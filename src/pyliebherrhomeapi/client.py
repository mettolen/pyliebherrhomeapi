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
- Recommended polling interval: 30 seconds for controls
- API key is obtained from SmartDevice app (Settings -> Beta features -> HomeAPI)
- API key can only be copied once from the app!
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Any

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
    CONTROL_SUPERCOOL,
    CONTROL_SUPERFROST,
    CONTROL_TEMPERATURE,
    DEFAULT_TIMEOUT,
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


def _get_version() -> str:
    """Return installed package version with a safe fallback."""

    try:
        return version("pyliebherrhomeapi")
    except PackageNotFoundError:
        return "0.0.0"


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
        self._user_agent = f"pyliebherrhomeapi/{_get_version()}"

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None:
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

        try:
            async with session.request(
                method,
                url,
                json=json_data,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self._timeout),
            ) as response:
                if response.status == 204:
                    return None

                async def _safe_json() -> Any:
                    return await response.json()

                async def _extract_message() -> str:
                    try:
                        error_data = await _safe_json()
                        if isinstance(error_data, dict):
                            return str(error_data.get("message", "Unknown error"))
                    except (ContentTypeError, ValueError):
                        text = await response.text()
                        return text.strip() or response.reason or ""
                    return response.reason or ""

                if response.status == 401:
                    raise LiebherrAuthenticationError("Authentication failed")
                if response.status == 400:
                    msg = await _extract_message()
                    raise LiebherrBadRequestError(f"Invalid data provided: {msg}")
                if response.status == 404:
                    msg = await _extract_message()
                    raise LiebherrNotFoundError(f"Device is not reachable: {msg}")
                if response.status == 412:
                    msg = await _extract_message()
                    raise LiebherrPreconditionFailedError(f"Precondition failed: {msg}")
                if response.status == 422:
                    msg = await _extract_message()
                    raise LiebherrUnsupportedError(f"Operation not supported: {msg}")
                if response.status == 500:
                    msg = await _extract_message()
                    raise LiebherrServerError(f"Internal server error: {msg}")
                if response.status == 503:
                    msg = await _extract_message()
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
                try:
                    data: dict[str, Any] | list[Any] = await _safe_json()
                except (ContentTypeError, ValueError) as err:
                    msg = await _extract_message()
                    raise LiebherrServerError(
                        f"Unexpected response format ({response.status}): {msg}"
                    ) from err
                return data

        except (TimeoutError, aiohttp.ServerTimeoutError) as ex:
            raise LiebherrTimeoutError("Request timed out") from ex
        except aiohttp.ClientError as ex:
            raise LiebherrConnectionError(f"Connection error: {ex}") from ex

    async def close(self) -> None:
        """Close the client session."""
        if self._own_session and self._session:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> LiebherrClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    # Device endpoints

    async def get_devices(self) -> list[Device]:
        """Get all connected devices.

        Returns:
            List of Device objects.

        Raises:
            LiebherrConnectionError: If connection fails.
            LiebherrTimeoutError: If request times out.

        """
        response = await self._request("GET", "devices")
        if not isinstance(response, list):
            raise LiebherrServerError("Unexpected response format for devices")
        return [Device.from_dict(device) for device in response]

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
        return [parse_control(control) for control in response]

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
        return [parse_control(control) for control in response]

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

    async def set_superfrost(self, device_id: str, zone_id: int, value: bool) -> None:
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
            f"devices/{device_id}/controls/{CONTROL_SUPERFROST}",
            json_data={"zoneId": zone_id, "value": value},
        )

    async def set_supercool(self, device_id: str, zone_id: int, value: bool) -> None:
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
            f"devices/{device_id}/controls/{CONTROL_SUPERCOOL}",
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
            json_data={"zoneId": zone_id, "iceMakerMode": mode.value},
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
            json_data={"zoneId": zone_id, "hydroBreezeMode": mode.value},
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
            json_data={"zoneId": zone_id, "bioFreshPlusMode": mode.value},
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
