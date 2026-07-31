"""Client for Liebherr Home API.

Terminology (from Liebherr SmartDevice HomeAPI documentation):
- device: The Liebherr appliance
- deviceId: The serial number of the appliance
- zone: A cooling/freezing zone in the device (min. 1 zone per device)
    - Zone 0 is the top zone
    - Zone numbers ascend from top to bottom
- base controls: Controls that apply to the whole device (e.g., Party Mode)
- zone controls: Controls that apply to a specific zone (e.g., Temperature)

Important Notes:
- Only appliances connected via SmartDevice app are accessible
- Zone controls always require a zone_id, even if device has only one zone
- SSE publishes control updates only; device list changes require a REST request
- API key is obtained from SmartDevice app (Settings -> Beta features -> HomeAPI)
- API key can only be copied once from the app!
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from collections.abc import AsyncIterator, Callable
from importlib.metadata import PackageNotFoundError, version
from types import TracebackType
from typing import Any, Self

import aiohttp
from aiohttp import ContentTypeError

from .const import (
    API_BASE_URL,
    API_VERSION,
    CONTROL_AUTO_DOOR,
    CONTROL_BIO_FRESH_PLUS,
    CONTROL_HYDRO_BREEZE,
    CONTROL_ICE_MAKER,
    CONTROL_NIGHT_MODE,
    CONTROL_PARTY_MODE,
    CONTROL_PRESENTATION_LIGHT,
    CONTROL_SUPER_COOL,
    CONTROL_SUPER_FROST,
    CONTROL_TEMPERATURE,
    DEFAULT_TIMEOUT,
    SSE_RECONNECT_BASE_DELAY,
    SSE_RECONNECT_MAX_DELAY,
)
from .exceptions import (
    LiebherrAuthenticationError,
    LiebherrBadRequestError,
    LiebherrConnectionError,
    LiebherrNotFoundError,
    LiebherrPreconditionFailedError,
    LiebherrServerError,
    LiebherrTimeoutError,
    LiebherrUnsupportedError,
)
from .models import (
    BioFreshPlusMode,
    Device,
    DeviceControl,
    DeviceState,
    HydroBreezeMode,
    IceMakerMode,
    TemperatureControl,
    TemperatureUnit,
    parse_control,
)

_LOGGER = logging.getLogger(__name__)

try:
    _VERSION = version("pyliebherrhomeapi")
except PackageNotFoundError:
    _VERSION = "0.0.0"


def _parse_sse_event(payload: str) -> list[DeviceControl] | None:
    """Parse a single SSE ``data`` payload into a list of controls.

    The payload is expected to be JSON containing either a single control
    object or a list of control objects. Anything else is logged and dropped
    so a malformed event does not kill the stream.
    """
    try:
        data = json.loads(payload)
    except ValueError:
        _LOGGER.warning("Failed to decode SSE payload as JSON: %r", payload)
        return None

    if isinstance(data, dict):
        items: list[Any] = [data]
    elif isinstance(data, list):
        items = data
    else:
        _LOGGER.warning(
            "Unexpected SSE payload (expected list or dict, got %s)",
            type(data).__name__,
        )
        return None

    controls: list[DeviceControl] = []
    for item in items:
        if not isinstance(item, dict):
            _LOGGER.warning("Skipping non-dict SSE item: %r", item)
            continue
        try:
            controls.append(parse_control(item))
        except (KeyError, ValueError, TypeError) as err:
            _LOGGER.warning("Failed to parse SSE control %r: %s", item, err)
    return controls


class LiebherrClient:
    """Client for interacting with Liebherr Home API."""

    def __init__(
        self,
        api_key: str,
        session: aiohttp.ClientSession | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        base_url: str = API_BASE_URL,
    ) -> None:
        """Initialize the Liebherr client.

        Args:
            api_key: API key for authentication.
            session: Optional aiohttp session. If not provided, new one created.
            timeout: Request timeout in seconds.
            base_url: Base URL for the API (default: production URL).

        """
        self._api_key = api_key
        self._session = session
        self._timeout = timeout
        self._base_url = base_url.rstrip("/")
        self._own_session = session is None
        self._user_agent = f"pyliebherrhomeapi/{_VERSION}"
        _LOGGER.debug(
            "Initialized LiebherrClient "
            "(base_url=%s, timeout=%ds, external_session=%s)",
            self._base_url,
            self._timeout,
            session is not None,
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None:
            _LOGGER.debug("Creating new aiohttp ClientSession")
            self._session = aiohttp.ClientSession()
        return self._session

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """Make an API request.

        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path.
            json_data: JSON data for POST requests.
            params: Query parameters.

        Returns:
            Response data as dict, list, or None for 204 responses.

        Raises:
            LiebherrAuthenticationError: If authentication fails.
            LiebherrBadRequestError: If invalid data is provided.
            LiebherrNotFoundError: If device is not reachable.
            LiebherrPreconditionFailedError: If precondition fails.
            LiebherrUnsupportedError: If operation is not supported.
            LiebherrServerError: If server returns 500 error.
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        url = f"{self._base_url}/{API_VERSION}/{endpoint}"
        headers = {
            "api-key": self._api_key,
            "User-Agent": self._user_agent,
        }
        session = await self._get_session()

        _LOGGER.debug("Making %s request to %s", method, endpoint)

        try:
            async with session.request(
                method,
                url,
                json=json_data,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self._timeout),
            ) as response:
                _LOGGER.debug("Response %d from %s", response.status, endpoint)
                if response.status == 204:
                    return None

                # Read the body once to avoid consuming the stream twice
                body: Any = None
                body_error: Exception | None = None
                try:
                    body = await response.json()
                except (ContentTypeError, ValueError) as err:
                    body_error = err

                def _extract_message() -> str:
                    if body_error is not None:
                        return response.reason or ""
                    if isinstance(body, dict):
                        return str(body.get("message", "Unknown error"))
                    return str(body) if body is not None else response.reason or ""

                if response.status == 401:
                    _LOGGER.error("Authentication failed")
                    raise LiebherrAuthenticationError("Authentication failed")
                if response.status == 400:
                    msg = _extract_message()
                    _LOGGER.warning("Bad request: %s", msg)
                    raise LiebherrBadRequestError(f"Invalid data provided: {msg}")
                if response.status == 404:
                    msg = _extract_message()
                    _LOGGER.warning("Resource not found: %s", msg)
                    raise LiebherrNotFoundError(f"Device is not reachable: {msg}")
                if response.status == 412:
                    msg = _extract_message()
                    _LOGGER.warning("Precondition failed: %s", msg)
                    raise LiebherrPreconditionFailedError(f"Precondition failed: {msg}")
                if response.status == 422:
                    msg = _extract_message()
                    _LOGGER.warning("Unsupported operation: %s", msg)
                    raise LiebherrUnsupportedError(f"Operation not supported: {msg}")
                if response.status == 500:
                    msg = _extract_message()
                    _LOGGER.error("Server error: %s", msg)
                    raise LiebherrServerError(f"Internal server error: {msg}")
                if response.status == 503:
                    msg = _extract_message()
                    _LOGGER.error("Service unavailable: %s", msg)
                    raise LiebherrConnectionError(
                        f"Internal service not reachable: {msg}"
                    )

                try:
                    response.raise_for_status()
                except aiohttp.ClientResponseError as err:
                    msg = err.message or response.reason or ""
                    raise LiebherrConnectionError(
                        f"HTTP {response.status}: {msg}"
                    ) from err

                if body_error is not None:
                    raise LiebherrServerError(
                        f"Unexpected response format ({response.status}): "
                        f"{response.reason or ''}"
                    ) from body_error

                data: dict[str, Any] | list[Any] = body
                return data

        except (TimeoutError, aiohttp.ServerTimeoutError) as ex:
            _LOGGER.warning(
                "Request timeout after %d seconds for %s %s",
                self._timeout,
                method,
                endpoint,
            )
            raise LiebherrTimeoutError("Request timed out") from ex
        except aiohttp.ClientError as ex:
            _LOGGER.error("Connection error for %s %s: %s", method, endpoint, ex)
            raise LiebherrConnectionError(f"Connection error: {ex}") from ex

    async def close(self) -> None:
        """Close the client session."""
        if self._own_session and self._session:
            _LOGGER.debug("Closing aiohttp ClientSession")
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        await self.close()

    def __repr__(self) -> str:
        """Return a string representation with redacted API key."""
        return (
            f"LiebherrClient(base_url={self._base_url!r}, "
            f"timeout={self._timeout}, "
            f"api_key='***')"
        )

    # Device endpoints

    async def get_devices(self) -> list[Device]:
        """Get all connected devices.

        Call this method again to discover added or removed appliances and
        appliance nickname changes. The Server-Sent Events endpoints only
        publish control updates and do not publish device list changes.

        Returns:
            List of Device objects.

        Raises:
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        _LOGGER.debug("Fetching all devices")
        response = await self._request("GET", "devices")
        if response is None:
            return []

        if not isinstance(response, list):
            raise LiebherrServerError("Unexpected response format for devices")

        devices = [
            Device.from_dict(device) for device in response if isinstance(device, dict)
        ]
        _LOGGER.debug("Retrieved %d device(s)", len(devices))
        return devices

    async def get_device(self, device_id: str) -> Device:
        """Get a specific device by ID.

        Args:
            device_id: The device ID (serial number).

        Returns:
            Device object.

        Raises:
            LiebherrNotFoundError: If device is not found.
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        masked_id = f"***{device_id[-4:]}" if len(device_id) > 4 else "***"
        _LOGGER.debug("Fetching device %s", masked_id)
        response = await self._request("GET", f"devices/{device_id}")
        if not isinstance(response, dict):
            raise LiebherrServerError("Unexpected response format for device")
        return Device.from_dict(response)

    # Control endpoints

    async def get_controls(self, device_id: str) -> list[DeviceControl]:
        """Get all controls for a device.

        Args:
            device_id: The device ID (serial number).

        Returns:
            List of control objects.

        Raises:
            LiebherrNotFoundError: If device is not found.
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        response = await self._request("GET", f"devices/{device_id}/controls")
        if not isinstance(response, list):
            raise LiebherrServerError("Unexpected response format for controls")
        return [
            parse_control(control) for control in response if isinstance(control, dict)
        ]

    async def get_control(
        self,
        device_id: str,
        control_name: str,
        zone_id: int | None = None,
    ) -> list[DeviceControl]:
        """Get specific control by name.

        Args:
            device_id: The device ID (serial number).
            control_name: Name of the control.
            zone_id: Optional zone ID for filtering.

        Returns:
            List of control objects matching the criteria.

        Raises:
            LiebherrNotFoundError: If device or control is not found.
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        params = {"zoneId": zone_id} if zone_id is not None else None
        response = await self._request(
            "GET",
            f"devices/{device_id}/controls/{control_name}",
            params=params,
        )
        if not isinstance(response, list):
            raise LiebherrServerError("Unexpected response format for control")
        return [
            parse_control(control) for control in response if isinstance(control, dict)
        ]

    # Temperature control

    async def set_temperature(
        self,
        device_id: str,
        zone_id: int,
        target: int,
        unit: TemperatureUnit = TemperatureUnit.CELSIUS,
    ) -> None:
        """Set temperature for a zone.

        Args:
            device_id: The device ID (serial number).
            zone_id: The zone ID.
            target: Target temperature.
            unit: Temperature unit (default: Celsius).

        Raises:
            LiebherrBadRequestError: If invalid data is provided.
            LiebherrNotFoundError: If device is not reachable.
            LiebherrPreconditionFailedError: If device not onboarded.
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        await self._request(
            "POST",
            f"devices/{device_id}/controls/{CONTROL_TEMPERATURE}",
            json_data={
                "zoneId": zone_id,
                "target": target,
                "unit": unit.value,
            },
        )

    # Toggle controls (SuperFrost, SuperCool, etc.)

    async def set_super_frost(self, device_id: str, zone_id: int, value: bool) -> None:
        """Set SuperFrost mode.

        Args:
            device_id: The device ID (serial number).
            zone_id: The zone ID.
            value: True to enable, False to disable.

        Raises:
            LiebherrBadRequestError: If invalid data is provided.
            LiebherrNotFoundError: If device is not reachable.
            LiebherrPreconditionFailedError: If device not onboarded.
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        await self._request(
            "POST",
            f"devices/{device_id}/controls/{CONTROL_SUPER_FROST}",
            json_data={"zoneId": zone_id, "value": value},
        )

    async def set_super_cool(self, device_id: str, zone_id: int, value: bool) -> None:
        """Set SuperCool mode.

        Args:
            device_id: The device ID (serial number).
            zone_id: The zone ID.
            value: True to enable, False to disable.

        Raises:
            LiebherrBadRequestError: If invalid data is provided.
            LiebherrNotFoundError: If device is not reachable.
            LiebherrPreconditionFailedError: If device not onboarded.
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        await self._request(
            "POST",
            f"devices/{device_id}/controls/{CONTROL_SUPER_COOL}",
            json_data={"zoneId": zone_id, "value": value},
        )

    async def set_party_mode(self, device_id: str, value: bool) -> None:
        """Set PartyMode.

        Args:
            device_id: The device ID (serial number).
            value: True to enable, False to disable.

        Raises:
            LiebherrBadRequestError: If invalid data is provided.
            LiebherrNotFoundError: If device is not reachable.
            LiebherrPreconditionFailedError: If device not onboarded.
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        await self._request(
            "POST",
            f"devices/{device_id}/controls/{CONTROL_PARTY_MODE}",
            json_data={"value": value},
        )

    async def set_night_mode(self, device_id: str, value: bool) -> None:
        """Set NightMode.

        Args:
            device_id: The device ID (serial number).
            value: True to enable, False to disable.

        Raises:
            LiebherrBadRequestError: If invalid data is provided.
            LiebherrNotFoundError: If device is not reachable.
            LiebherrPreconditionFailedError: If device not onboarded.
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        await self._request(
            "POST",
            f"devices/{device_id}/controls/{CONTROL_NIGHT_MODE}",
            json_data={"value": value},
        )

    async def set_presentation_light(self, device_id: str, target: int) -> None:
        """Set presentation light intensity.

        Args:
            device_id: The device ID (serial number).
            target: Light intensity value.

        Raises:
            LiebherrBadRequestError: If invalid data is provided.
            LiebherrNotFoundError: If device is not reachable.
            LiebherrPreconditionFailedError: If device not onboarded.
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        await self._request(
            "POST",
            f"devices/{device_id}/controls/{CONTROL_PRESENTATION_LIGHT}",
            json_data={"target": target},
        )

    # Special controls

    async def set_ice_maker(
        self, device_id: str, zone_id: int, mode: IceMakerMode
    ) -> None:
        """Set ice maker mode.

        Args:
            device_id: The device ID (serial number).
            zone_id: The zone ID.
            mode: Ice maker mode (OFF, ON, MAX_ICE).

        Raises:
            LiebherrBadRequestError: If invalid data is provided.
            LiebherrNotFoundError: If device is not reachable.
            LiebherrPreconditionFailedError: If device not onboarded.
            LiebherrUnsupportedError: If MaxIce not supported.
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        await self._request(
            "POST",
            f"devices/{device_id}/controls/{CONTROL_ICE_MAKER}",
            json_data={"zoneId": zone_id, "iceMakerMode": mode.value.upper()},
        )

    async def set_hydro_breeze(
        self, device_id: str, zone_id: int, mode: HydroBreezeMode
    ) -> None:
        """Set HydroBreeze mode.

        Args:
            device_id: The device ID (serial number).
            zone_id: The zone ID.
            mode: HydroBreeze mode (OFF, LOW, MEDIUM, HIGH).

        Raises:
            LiebherrBadRequestError: If invalid data is provided.
            LiebherrNotFoundError: If device is not reachable.
            LiebherrPreconditionFailedError: If device not onboarded.
            LiebherrUnsupportedError: If BioFreshPlus not enabled.
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        await self._request(
            "POST",
            f"devices/{device_id}/controls/{CONTROL_HYDRO_BREEZE}",
            json_data={"zoneId": zone_id, "hydroBreezeMode": mode.value.upper()},
        )

    async def set_bio_fresh_plus(
        self, device_id: str, zone_id: int, mode: BioFreshPlusMode
    ) -> None:
        """Set BioFreshPlus mode.

        Args:
            device_id: The device ID (serial number).
            zone_id: The zone ID.
            mode: BioFreshPlus mode.

        Raises:
            LiebherrBadRequestError: If invalid data is provided.
            LiebherrNotFoundError: If device is not reachable.
            LiebherrPreconditionFailedError: If device not onboarded.
            LiebherrUnsupportedError: If BioFreshPlus not enabled.
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        await self._request(
            "POST",
            f"devices/{device_id}/controls/{CONTROL_BIO_FRESH_PLUS}",
            json_data={"zoneId": zone_id, "bioFreshPlusMode": mode.value.upper()},
        )

    async def trigger_auto_door(
        self, device_id: str, zone_id: int, value: bool
    ) -> None:
        """Open or close auto door.

        Args:
            device_id: The device ID (serial number).
            zone_id: The zone ID.
            value: True to open, False to close.

        Raises:
            LiebherrBadRequestError: If invalid data is provided.
            LiebherrNotFoundError: If device is not reachable.
            LiebherrPreconditionFailedError: If device not onboarded.
            LiebherrUnsupportedError: If Auto Door not enabled.
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        await self._request(
            "POST",
            f"devices/{device_id}/controls/{CONTROL_AUTO_DOOR}",
            json_data={"zoneId": zone_id, "value": value},
        )

    # Convenience methods

    async def get_device_state(self, device_id: str) -> DeviceState:
        """Get complete device state (device info + all controls).

        Args:
            device_id: The device ID (serial number).

        Returns:
            DeviceState object containing device info and all controls.

        Raises:
            LiebherrNotFoundError: If device is not found.
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        device = await self.get_device(device_id)
        controls = await self.get_controls(device_id)
        return DeviceState(device=device, controls=controls)

    async def stream_controls(
        self, device_id: str
    ) -> AsyncIterator[list[DeviceControl]]:
        """Stream realtime control updates for a device via Server-Sent Events.

        Opens a long-lived connection to the SSE endpoint and yields a list of
        parsed controls each time the server pushes an update. The connection
        stays open until the consumer stops iterating, an error occurs, or the
        server closes the stream.

        This stream only publishes appliance control updates. Call
        :meth:`get_devices` explicitly to discover added or removed appliances
        and appliance nickname changes.

        The Liebherr OpenAPI spec defines each event payload as a JSON list of
        control objects matching the regular ``/controls`` response. Consumers
        maintaining cached state should merge the controls in each event by
        name and zone. A single control object (rather than a list) is also
        accepted defensively. Events whose payload cannot be parsed are skipped
        with a warning so a single bad event does not terminate the stream.

        The server keeps the connection open by sending an empty keep-alive
        roughly every 30 seconds. These arrive as bare empty lines rather than
        SSE ``:`` comments and do not terminate the stream; the connection is
        only considered closed when the underlying HTTP response ends.

        Args:
            device_id: The device ID (serial number).

        Yields:
            List of :class:`DeviceControl` objects parsed from each SSE event.

        Raises:
            LiebherrAuthenticationError: If authentication fails.
            LiebherrNotFoundError: If device is not reachable.
            LiebherrPreconditionFailedError: If device is not onboarded.
            LiebherrServerError: If the server returns a 5xx response.
            LiebherrConnectionError: If the connection fails or drops.
            LiebherrTimeoutError: If the initial connection times out.

        """
        url = f"{self._base_url}/{API_VERSION}/sse/devices/{device_id}/controls"
        headers = {
            "api-key": self._api_key,
            "User-Agent": self._user_agent,
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
        }
        session = await self._get_session()

        _LOGGER.debug("Opening SSE stream for device %s", device_id)

        # Disable read/total timeouts so the stream can stay open indefinitely;
        # keep a connect timeout so a stuck handshake still fails fast.
        stream_timeout = aiohttp.ClientTimeout(
            total=None, sock_read=None, sock_connect=self._timeout
        )

        try:
            response_cm = session.get(url, headers=headers, timeout=stream_timeout)
        except aiohttp.ClientError as ex:
            raise LiebherrConnectionError(f"Connection error: {ex}") from ex

        try:
            async with response_cm as response:
                self._raise_for_sse_status(response, device_id)

                data_lines: list[str] = []
                try:
                    async for raw_line in response.content:
                        line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
                        if line == "":
                            # Dispatch the buffered event on empty line.
                            if data_lines:
                                controls = _parse_sse_event("\n".join(data_lines))
                                data_lines = []
                                if controls is not None:
                                    yield controls
                            continue
                        if line.startswith(":"):
                            # SSE comment / keep-alive
                            continue
                        if line.startswith("data:"):
                            value = line[5:]
                            # Per spec, a single leading space is stripped.
                            if value.startswith(" "):
                                value = value[1:]
                            data_lines.append(value)
                        # Other fields (e.g. event, id, retry) are ignored.

                    # Flush a final event if the server closed without a
                    # terminating blank line.
                    if data_lines:
                        controls = _parse_sse_event("\n".join(data_lines))
                        if controls is not None:
                            yield controls
                except (TimeoutError, aiohttp.ServerTimeoutError) as ex:
                    raise LiebherrTimeoutError("SSE stream timed out") from ex
                except aiohttp.ClientError as ex:
                    raise LiebherrConnectionError(f"SSE stream error: {ex}") from ex
        except (TimeoutError, aiohttp.ServerTimeoutError) as ex:
            raise LiebherrTimeoutError("Timeout connecting to SSE stream") from ex
        except aiohttp.ClientError as ex:
            raise LiebherrConnectionError(f"Connection error: {ex}") from ex

    @staticmethod
    def _raise_for_sse_status(response: aiohttp.ClientResponse, device_id: str) -> None:
        """Translate non-success SSE status codes to library exceptions."""
        status = response.status
        if status == 200:
            return
        if status == 401:
            raise LiebherrAuthenticationError("Authentication failed")
        if status == 404:
            raise LiebherrNotFoundError(f"Device {device_id} is not reachable")
        if status == 412:
            raise LiebherrPreconditionFailedError(
                f"Device {device_id} is not onboarded"
            )
        if 500 <= status < 600:
            raise LiebherrServerError(f"Server error opening SSE stream: {status}")
        raise LiebherrConnectionError(f"Unexpected status {status} opening SSE stream")

    def _sse_reconnect_delay(
        self, attempt: int, base_delay: float, max_delay: float
    ) -> float:
        """Compute the reconnect delay for an SSE stream.

        Uses exponential backoff capped at ``max_delay`` with "equal jitter"
        (half fixed, half random) to avoid a reconnect stampede.
        """
        delay = min(base_delay * 2**attempt, max_delay)
        jitter = random.uniform(0, delay / 2)
        return float(delay / 2 + jitter)

    async def stream_controls_forever(
        self,
        device_id: str,
        *,
        base_delay: float = SSE_RECONNECT_BASE_DELAY,
        max_delay: float = SSE_RECONNECT_MAX_DELAY,
        on_connect: Callable[[], None] | None = None,
        on_disconnect: Callable[[], None] | None = None,
    ) -> AsyncIterator[list[DeviceControl]]:
        """Stream control updates, reconnecting automatically on failure.

        Wraps :meth:`stream_controls` in a resilient loop: recoverable errors
        (connection drops, timeouts, and 5xx server errors) and clean stream
        closures trigger a reconnect after an exponential backoff delay with
        jitter. The backoff resets after any successfully received event.

        This stream only publishes appliance control updates. Call
        :meth:`get_devices` explicitly to discover added or removed appliances
        and appliance nickname changes.

        Non-recoverable errors are re-raised without retrying, since retrying
        cannot succeed without caller intervention:

        - :class:`LiebherrAuthenticationError` (bad API key)
        - :class:`LiebherrNotFoundError` (device not reachable)
        - :class:`LiebherrPreconditionFailedError` (device not onboarded)

        This generator only stops when the consumer stops iterating or a
        non-recoverable error is raised; otherwise it reconnects indefinitely.

        The optional ``on_connect`` / ``on_disconnect`` callbacks let a consumer
        (e.g. a Home Assistant coordinator) track availability. ``on_connect``
        fires when the first event arrives after (re)connecting; ``on_disconnect``
        fires when a recoverable drop or clean close schedules a reconnect. They
        are not called for non-recoverable errors or when the consumer stops
        iterating, since those terminate the generator and are observable
        directly. Callbacks must be non-blocking (HA ``@callback`` style); an
        exception raised by a callback is logged and does not break the stream.

        Args:
            device_id: The device ID (serial number).
            base_delay: Initial reconnect delay in seconds.
            max_delay: Maximum reconnect delay in seconds.
            on_connect: Called once each time the stream (re)connects.
            on_disconnect: Called each time the stream drops and a reconnect
                is scheduled.

        Yields:
            List of :class:`DeviceControl` objects parsed from each SSE event.

        Raises:
            LiebherrAuthenticationError: If authentication fails.
            LiebherrNotFoundError: If the device is not reachable.
            LiebherrPreconditionFailedError: If the device is not onboarded.

        """
        attempt = 0
        connected = False
        while True:
            try:
                async for controls in self.stream_controls(device_id):
                    attempt = 0
                    if not connected:
                        connected = True
                        self._run_stream_callback(on_connect, device_id, "on_connect")
                    yield controls
            except (
                LiebherrConnectionError,
                LiebherrTimeoutError,
                LiebherrServerError,
            ) as err:
                # Recoverable: reconnect after a backoff delay.
                # Non-recoverable errors (auth, not-found, precondition) are
                # not caught here and propagate to the caller.
                delay = self._sse_reconnect_delay(attempt, base_delay, max_delay)
                _LOGGER.debug(
                    "SSE stream for %s dropped (%s); reconnecting in %.1fs",
                    device_id,
                    err,
                    delay,
                )
            else:
                delay = self._sse_reconnect_delay(attempt, base_delay, max_delay)
                _LOGGER.debug(
                    "SSE stream for %s ended; reconnecting in %.1fs",
                    device_id,
                    delay,
                )
            if connected:
                connected = False
                self._run_stream_callback(on_disconnect, device_id, "on_disconnect")
            attempt += 1
            await asyncio.sleep(delay)

    @staticmethod
    def _run_stream_callback(
        callback: Callable[[], None] | None, device_id: str, name: str
    ) -> None:
        """Invoke a stream state callback, swallowing and logging errors.

        A consumer-provided callback must never break the reconnect loop, so
        any exception it raises is logged instead of propagated.
        """
        if callback is None:
            return
        try:
            callback()
        except Exception:  # pylint: disable=broad-exception-caught
            _LOGGER.exception("SSE %s callback for %s raised", name, device_id)

    async def refresh_device(self, device_id: str) -> DeviceState:
        """Refresh and return current device state.

        This is an alias for get_device_state for better naming consistency.

        Args:
            device_id: The device ID (serial number).

        Returns:
            DeviceState object containing device info and all controls.

        Raises:
            LiebherrNotFoundError: If device is not found.
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        return await self.get_device_state(device_id)

    async def get_temperature_controls(
        self, device_id: str
    ) -> list[TemperatureControl]:
        """Get only temperature controls for a device.

        Args:
            device_id: The device ID (serial number).

        Returns:
            List of temperature controls.

        Raises:
            LiebherrNotFoundError: If device is not found.
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        controls = await self.get_controls(device_id)
        return [
            control for control in controls if isinstance(control, TemperatureControl)
        ]
