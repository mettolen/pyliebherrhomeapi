"""Tests for Liebherr client."""
# pylint: disable=redefined-outer-name, protected-access
# pylint: disable=unused-argument, unreachable, too-few-public-methods
# pylint: disable=too-many-lines, too-many-positional-arguments, too-many-arguments

import asyncio
import importlib
from importlib.metadata import PackageNotFoundError
from types import ModuleType
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiohttp.client_exceptions import ContentTypeError

import pyliebherrhomeapi
import pyliebherrhomeapi.client as pyliebherrhomeapi_client
from pyliebherrhomeapi import (
    BioFreshPlusMode,
    HydroBreezeMode,
    IceMakerMode,
    LiebherrAuthenticationError,
    LiebherrBadRequestError,
    LiebherrClient,
    LiebherrConnectionError,
    LiebherrNotFoundError,
    LiebherrPreconditionFailedError,
    LiebherrServerError,
    LiebherrTimeoutError,
    LiebherrUnsupportedError,
    TemperatureUnit,
)
from pyliebherrhomeapi.client import _VERSION

API_KEY = "test-api-key"
DEVICE_ID = "12.345.678.9"


@pytest.fixture
def mock_response() -> MagicMock:
    """Create a mock response."""
    response = MagicMock()
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    return response


@pytest.fixture
def mock_session(mock_response: MagicMock) -> MagicMock:
    """Create a mock aiohttp session."""
    session = MagicMock(spec=aiohttp.ClientSession)
    session.request = MagicMock(return_value=mock_response)
    return session


@pytest.fixture
def client(mock_session: MagicMock) -> LiebherrClient:
    """Create a test client."""
    return LiebherrClient(api_key=API_KEY, session=mock_session)


class TestClientLifecycle:
    """Tests for client lifecycle and configuration."""

    async def test_initialization(self) -> None:
        """Test client initialization."""
        client = LiebherrClient(api_key=API_KEY)
        assert client is not None
        await client.close()

    async def test_context_manager(self) -> None:
        """Test client as context manager."""
        async with LiebherrClient(api_key=API_KEY) as client:
            assert client is not None

    async def test_custom_base_url(self) -> None:
        """Test client with custom base URL."""
        custom_url = "https://custom.api.com/"
        client = LiebherrClient(api_key=API_KEY, base_url=custom_url)
        assert client._base_url == "https://custom.api.com"
        await client.close()

    async def test_custom_timeout(self) -> None:
        """Test client with custom timeout."""
        custom_timeout = 30
        client = LiebherrClient(api_key=API_KEY, timeout=custom_timeout)
        assert client._timeout == custom_timeout
        await client.close()

    async def test_repr_redacts_api_key(self) -> None:
        """Test that repr does not expose the API key."""
        client = LiebherrClient(api_key="secret-key-12345")
        result = repr(client)
        assert "secret-key-12345" not in result
        assert "api_key='***'" in result
        await client.close()

    async def test_creates_own_session(self) -> None:
        """Test client creates its own session when none provided."""
        client = LiebherrClient(api_key=API_KEY)
        assert client._session is None
        assert client._own_session is True

        mock_response = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[])

        with patch.object(aiohttp.ClientSession, "request", return_value=mock_response):
            await client.get_devices()

        assert client._session is not None
        await client.close()
        assert client._session is None

    async def test_close_with_provided_session(self, mock_session: MagicMock) -> None:
        """Test that close doesn't close a session that was provided."""
        client = LiebherrClient(api_key=API_KEY, session=mock_session)
        assert client._own_session is False

        await client.close()
        mock_session.close.assert_not_called()

    async def test_close_when_no_session(self) -> None:
        """Test close when no session was created."""
        client = LiebherrClient(api_key=API_KEY)
        assert client._session is None
        await client.close()
        assert client._session is None


class TestDeviceOperations:
    """Tests for device-related operations."""

    async def test_get_devices(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Test getting all devices."""
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value=[
                {
                    "deviceId": DEVICE_ID,
                    "nickname": "Kitchen Fridge",
                    "deviceType": "FRIDGE",
                    "deviceName": "Test Fridge",
                }
            ]
        )

        devices = await client.get_devices()
        assert len(devices) == 1
        assert devices[0].device_id == DEVICE_ID
        assert devices[0].nickname == "Kitchen Fridge"

    async def test_get_device(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Test getting a specific device."""
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "deviceId": DEVICE_ID,
                "nickname": "Kitchen Fridge",
                "deviceType": "FRIDGE",
            }
        )

        device = await client.get_device(DEVICE_ID)
        assert device.device_id == DEVICE_ID

    @pytest.mark.parametrize(
        ("response_data",),
        [
            ({"error": "not a list"},),
        ],
    )
    async def test_get_devices_edge_cases(
        self,
        client: LiebherrClient,
        mock_response: MagicMock,
        response_data: list[Any] | dict[str, Any],
    ) -> None:
        """Test get_devices with edge cases."""
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=response_data)

        with pytest.raises(LiebherrServerError):
            await client.get_devices()

    async def test_get_devices_none_response(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Test get_devices returns empty list when response is None (204 status)."""
        mock_response.status = 204

        devices = await client.get_devices()
        assert devices == []

    async def test_get_device_not_dict(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Test getting device with non-dict response."""
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=["not", "a", "dict"])

        with pytest.raises(LiebherrServerError):
            await client.get_device(DEVICE_ID)


class TestControlOperations:
    """Tests for control-related operations."""

    async def test_get_controls(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Test getting device controls."""
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value=[
                {
                    "name": "temperature",
                    "type": "TemperatureControl",
                    "zoneId": 0,
                    "value": 4,
                    "target": 4,
                    "min": 2,
                    "max": 8,
                    "unit": "°C",
                }
            ]
        )

        controls = await client.get_controls(DEVICE_ID)
        assert len(controls) == 1

    async def test_get_control(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Test getting specific control by name."""
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value=[
                {
                    "name": "temperature",
                    "type": "TemperatureControl",
                    "zoneId": 0,
                    "value": 4,
                    "target": 4,
                }
            ]
        )

        controls = await client.get_control(DEVICE_ID, "temperature")
        assert len(controls) == 1
        assert controls[0].name == "temperature"

    async def test_get_control_with_zone(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Test getting specific control by name with zone filter."""
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value=[
                {
                    "name": "temperature",
                    "type": "TemperatureControl",
                    "zoneId": 1,
                    "value": 4,
                }
            ]
        )

        controls = await client.get_control(DEVICE_ID, "temperature", zone_id=1)
        assert len(controls) == 1

    @pytest.mark.parametrize(
        ("response_data",),
        [
            ({"error": "not a list"},),
        ],
    )
    async def test_get_controls_edge_cases(
        self,
        client: LiebherrClient,
        mock_response: MagicMock,
        response_data: list[Any] | dict[str, Any],
    ) -> None:
        """Test get_controls with edge cases."""
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=response_data)

        with pytest.raises(LiebherrServerError):
            await client.get_controls(DEVICE_ID)

    @pytest.mark.parametrize(
        ("response_data",),
        [
            ({"error": "not a list"},),
        ],
    )
    async def test_get_control_edge_cases(
        self,
        client: LiebherrClient,
        mock_response: MagicMock,
        response_data: list[Any] | dict[str, Any],
    ) -> None:
        """Test get_control with edge cases."""
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=response_data)

        with pytest.raises(LiebherrServerError):
            await client.get_control(DEVICE_ID, "temperature")


class TestSetterMethods:
    """Tests for all setter methods using parametrization."""

    @pytest.mark.parametrize(
        ("method_name", "kwargs", "control", "expected_json"),
        [
            (
                "set_temperature",
                {"zone_id": 0, "target": 4, "unit": TemperatureUnit.CELSIUS},
                "temperature",
                {"zoneId": 0, "target": 4, "unit": "\u00b0C"},
            ),
            (
                "set_super_frost",
                {"zone_id": 0, "value": True},
                "superfrost",
                {"zoneId": 0, "value": True},
            ),
            (
                "set_super_cool",
                {"zone_id": 0, "value": True},
                "supercool",
                {"zoneId": 0, "value": True},
            ),
            (
                "set_presentation_light",
                {"target": 50},
                "presentationlight",
                {"target": 50},
            ),
            (
                "set_ice_maker",
                {"zone_id": 0, "mode": IceMakerMode.MAX_ICE},
                "icemaker",
                {"zoneId": 0, "iceMakerMode": "MAX_ICE"},
            ),
            (
                "set_hydro_breeze",
                {"zone_id": 0, "mode": HydroBreezeMode.HIGH},
                "hydrobreeze",
                {"zoneId": 0, "hydroBreezeMode": "HIGH"},
            ),
            (
                "set_bio_fresh_plus",
                {"zone_id": 0, "mode": BioFreshPlusMode.ZERO_ZERO},
                "biofreshplus",
                {"zoneId": 0, "bioFreshPlusMode": "ZERO_ZERO"},
            ),
            (
                "trigger_auto_door",
                {"zone_id": 0, "value": True},
                "autodoor",
                {"zoneId": 0, "value": True},
            ),
            (
                "set_party_mode",
                {"value": True},
                "partymode",
                {"value": True},
            ),
            (
                "set_night_mode",
                {"value": True},
                "nightmode",
                {"value": True},
            ),
        ],
    )
    async def test_setter_methods(
        self,
        client: LiebherrClient,
        mock_session: MagicMock,
        mock_response: MagicMock,
        method_name: str,
        kwargs: dict[str, Any],
        control: str,
        expected_json: dict[str, Any],
    ) -> None:
        """Each setter POSTs the expected control endpoint and payload."""
        mock_response.status = 204

        method = getattr(client, method_name)
        await method(device_id=DEVICE_ID, **kwargs)

        args, call_kwargs = mock_session.request.call_args
        assert args[0] == "POST"
        assert args[1].endswith(f"/v1/devices/{DEVICE_ID}/controls/{control}")
        assert call_kwargs["json"] == expected_json


class TestConvenienceMethods:
    """Tests for convenience methods."""

    async def test_get_device_state(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Test getting complete device state."""
        mock_response.status = 200
        device_response = {
            "deviceId": DEVICE_ID,
            "nickname": "Kitchen Fridge",
            "deviceType": "FRIDGE",
        }
        controls_response = [
            {
                "name": "temperature",
                "type": "TemperatureControl",
                "zoneId": 0,
                "value": 4,
            }
        ]
        mock_response.json = AsyncMock(side_effect=[device_response, controls_response])

        state = await client.get_device_state(DEVICE_ID)
        assert state.device.device_id == DEVICE_ID
        assert len(state.controls) == 1

    async def test_refresh_device(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Test refresh_device (alias for get_device_state)."""
        mock_response.status = 200
        device_response = {"deviceId": DEVICE_ID, "deviceType": "FRIDGE"}
        controls_response: list[dict[str, Any]] = []
        mock_response.json = AsyncMock(side_effect=[device_response, controls_response])

        state = await client.refresh_device(DEVICE_ID)
        assert state.device.device_id == DEVICE_ID
        assert len(state.controls) == 0

    async def test_get_temperature_controls(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Test getting only temperature controls."""
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value=[
                {
                    "name": "temperature",
                    "type": "TemperatureControl",
                    "zoneId": 0,
                    "value": 4,
                },
                {
                    "name": "superfrost",
                    "type": "ToggleControl",
                    "zoneId": 0,
                    "value": True,
                },
            ]
        )

        temp_controls = await client.get_temperature_controls(DEVICE_ID)
        assert len(temp_controls) == 1
        assert temp_controls[0].name == "temperature"


class TestErrorHandling:
    """Tests for error handling using parametrization."""

    @pytest.mark.parametrize(
        ("status", "response_data", "exception_class"),
        [
            (401, {"message": "Unauthorized"}, LiebherrAuthenticationError),
            (400, {"message": "Invalid data"}, LiebherrBadRequestError),
            (404, {"message": "Device not found"}, LiebherrNotFoundError),
            (412, {"message": "Device not onboarded"}, LiebherrPreconditionFailedError),
            (422, {"message": "Not supported"}, LiebherrUnsupportedError),
            (500, {"message": "Internal error"}, LiebherrServerError),
            (503, {"message": "Service unavailable"}, LiebherrConnectionError),
        ],
    )
    async def test_http_errors(
        self,
        client: LiebherrClient,
        mock_response: MagicMock,
        status: int,
        response_data: dict[str, str],
        exception_class: type[Exception],
    ) -> None:
        """Test HTTP error handling."""
        mock_response.status = status
        mock_response.json = AsyncMock(return_value=response_data)

        with pytest.raises(exception_class):
            await client.get_devices()

    async def test_timeout_error(self, mock_session: MagicMock) -> None:
        """Test timeout error."""
        mock_session.request.side_effect = TimeoutError("Request timed out")
        client = LiebherrClient(api_key=API_KEY, session=mock_session)

        with pytest.raises(LiebherrTimeoutError):
            await client.get_devices()

    async def test_connection_error(self, mock_session: MagicMock) -> None:
        """Test connection error."""
        mock_session.request.side_effect = aiohttp.ClientError("Connection failed")
        client = LiebherrClient(api_key=API_KEY, session=mock_session)

        with pytest.raises(LiebherrConnectionError):
            await client.get_devices()

    async def test_http_status_204(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Test handling of 204 No Content response."""
        mock_response.status = 204

        result = await client._request("POST", "test")
        assert result is None

    async def test_extract_message_content_type_error(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Fallback to response reason when JSON parsing fails."""

        mock_response.status = 400
        mock_response.reason = "Bad Request"
        mock_response.json = AsyncMock(
            side_effect=ContentTypeError(MagicMock(), (), message="bad content")
        )

        with pytest.raises(LiebherrBadRequestError) as err:
            await client.get_devices()

        assert "Bad Request" in str(err.value)

    async def test_extract_message_returns_body_when_not_dict(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Include raw body content when JSON is not a dict."""

        mock_response.status = 400
        mock_response.reason = "Bad Request"
        mock_response.json = AsyncMock(return_value=["oops"])

        with pytest.raises(LiebherrBadRequestError) as err:
            await client.get_devices()

        assert "oops" in str(err.value)

    async def test_unexpected_json_format_raises_server_error(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Non-JSON 200 responses raise server error with context."""

        mock_response.status = 200
        mock_response.reason = "OK"
        mock_response.raise_for_status = MagicMock(return_value=None)
        mock_response.json = AsyncMock(side_effect=ValueError("boom"))

        with pytest.raises(LiebherrServerError) as err:
            await client.get_devices()

        assert "Unexpected response format" in str(err.value)

    async def test_raise_for_status(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Test that unknown status codes call raise_for_status."""
        mock_response.status = 418
        mock_response.json = AsyncMock(return_value={"message": "I'm a teapot"})
        mock_response.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=418,
            message="I'm a teapot",
        )

        with pytest.raises(LiebherrConnectionError):
            await client.get_devices()


class TestVersionFallback:
    """Tests for version fallback handling."""

    def test_get_version_fallback(self) -> None:
        """Module-level _VERSION is resolved at import time."""
        assert isinstance(_VERSION, str)
        assert _VERSION != ""

    @pytest.mark.parametrize(
        ("module", "attr"),
        [
            (pyliebherrhomeapi, "__version__"),
            (pyliebherrhomeapi_client, "_VERSION"),
        ],
        ids=["package", "client"],
    )
    def test_version_fallback_on_missing_metadata(
        self,
        monkeypatch: pytest.MonkeyPatch,
        module: ModuleType,
        attr: str,
    ) -> None:
        """Reloading a module applies the '0.0.0' fallback when metadata missing."""
        monkeypatch.setattr(
            "importlib.metadata.version",
            MagicMock(side_effect=PackageNotFoundError()),
        )

        reloaded = importlib.reload(module)

        assert getattr(reloaded, attr) == "0.0.0"


class _FakeContent:
    """Async-iterable stand-in for aiohttp's ``response.content``.

    Yields the supplied byte lines one at a time, mirroring how
    ``async for raw_line in response.content`` behaves over a real
    ``StreamReader``. If ``raise_after`` is given, that exception is raised
    once all lines are exhausted (instead of ``StopAsyncIteration``) to
    simulate a mid-stream failure.
    """

    def __init__(
        self, lines: list[bytes], raise_after: BaseException | None = None
    ) -> None:
        self._lines = list(lines)
        self._raise_after = raise_after

    def __aiter__(self) -> "_FakeContent":
        return self

    async def __anext__(self) -> bytes:
        if not self._lines:
            if self._raise_after is not None:
                raise self._raise_after
            raise StopAsyncIteration
        return self._lines.pop(0)


def _make_sse_response(
    lines: list[bytes],
    status: int = 200,
    raise_after: BaseException | None = None,
) -> MagicMock:
    """Build a mock response usable as an async context manager."""
    response = MagicMock()
    response.status = status
    response.content = _FakeContent(lines, raise_after=raise_after)
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    return response


def _set_sse_response(session: MagicMock, response: MagicMock) -> None:
    """Wire session.get to return the given response."""
    session.get = MagicMock(return_value=response)


class TestStreamControls:
    """Tests for the SSE-based realtime controls stream."""

    async def test_yields_parsed_control_lists(
        self, client: LiebherrClient, mock_session: MagicMock
    ) -> None:
        """Two well-formed events are parsed into two lists of controls."""
        payload_one = (
            '[{"name":"temperature","type":"TemperatureControl",'
            '"zoneId":0,"value":4,"target":4,"unit":"\u00b0C"}]'
        )
        payload_two = '[{"name":"superfrost","type":"ToggleControl","value":true}]'
        lines = [
            f"data: {payload_one}\n".encode(),
            b"\n",
            b": keep-alive\n",
            f"data: {payload_two}\n".encode(),
            b"\n",
        ]
        _set_sse_response(mock_session, _make_sse_response(lines))

        received: list[list[Any]] = []
        async for controls in client.stream_controls(DEVICE_ID):
            received.append(controls)

        assert len(received) == 2
        assert received[0][0].name == "temperature"
        assert received[0][0].value == 4
        assert received[1][0].name == "superfrost"
        assert received[1][0].value is True

    async def test_single_dict_payload_is_wrapped_in_list(
        self, client: LiebherrClient, mock_session: MagicMock
    ) -> None:
        """A dict (rather than a list) payload yields a one-item list."""
        payload = '{"name":"partymode","type":"ToggleControl","value":false}'
        lines = [f"data: {payload}\n".encode(), b"\n"]
        _set_sse_response(mock_session, _make_sse_response(lines))

        received: list[list[Any]] = []
        async for controls in client.stream_controls(DEVICE_ID):
            received.append(controls)

        assert len(received) == 1
        assert len(received[0]) == 1
        assert received[0][0].name == "partymode"

    async def test_final_event_flushed_without_trailing_blank_line(
        self, client: LiebherrClient, mock_session: MagicMock
    ) -> None:
        """A buffered event is emitted when the server closes the stream."""
        payload = '[{"name":"nightmode","type":"ToggleControl","value":true}]'
        lines = [f"data: {payload}\n".encode()]
        _set_sse_response(mock_session, _make_sse_response(lines))

        received = [c async for c in client.stream_controls(DEVICE_ID)]

        assert len(received) == 1
        assert received[0][0].name == "nightmode"

    async def test_bare_newline_keepalives_are_ignored(
        self, client: LiebherrClient, mock_session: MagicMock
    ) -> None:
        """Bare ``\\n`` lines between events are treated as keep-alive.

        The Liebherr Home API keeps the SSE connection open by periodically
        sending bare empty lines (roughly every 30 seconds) rather than SSE
        comments. Reproduces the exact wire pattern captured against the
        production server: an ``event:``/``data:`` pair, the standard blank
        line terminator, then several bare ``\\n`` keep-alive lines, followed
        by further events.
        """
        payload_one = (
            '[{"type":"TemperatureControl","name":"temperature",'
            '"zoneId":0,"zonePosition":"top","value":4,"target":4,'
            '"min":3,"max":9,"unit":"\u00b0C",'
            '"setTemperatureSteps":[],"setTemperatureStepsEnabled":false}]'
        )
        payload_two = (
            '[{"type":"ToggleControl","name":"supercool",'
            '"zoneId":0,"zonePosition":"top","value":false}]'
        )
        lines = [
            b"event:device-update\n",
            f"data:{payload_one}\n".encode(),
            b"\n",
            b"\n",
            b"\n",
            b"\n",
            b"event:device-update\n",
            f"data:{payload_two}\n".encode(),
            b"\n",
            b"\n",
            b"\n",
            b"\n",
        ]
        _set_sse_response(mock_session, _make_sse_response(lines))

        received = [c async for c in client.stream_controls(DEVICE_ID)]

        assert len(received) == 2
        assert received[0][0].name == "temperature"
        assert received[1][0].name == "supercool"

    async def test_malformed_json_is_skipped(
        self, client: LiebherrClient, mock_session: MagicMock
    ) -> None:
        """A bad JSON event is dropped; subsequent good events still arrive."""
        good = '[{"name":"partymode","type":"ToggleControl","value":true}]'
        lines = [
            b"data: not-json\n",
            b"\n",
            f"data: {good}\n".encode(),
            b"\n",
        ]
        _set_sse_response(mock_session, _make_sse_response(lines))

        received = [c async for c in client.stream_controls(DEVICE_ID)]

        assert len(received) == 1
        assert received[0][0].name == "partymode"

    async def test_non_object_payload_is_skipped(
        self, client: LiebherrClient, mock_session: MagicMock
    ) -> None:
        """A JSON scalar payload is ignored."""
        lines = [b"data: 42\n", b"\n"]
        _set_sse_response(mock_session, _make_sse_response(lines))

        received = [c async for c in client.stream_controls(DEVICE_ID)]

        assert received == []

    async def test_non_dict_list_items_are_skipped(
        self, client: LiebherrClient, mock_session: MagicMock
    ) -> None:
        """List items that aren't objects are dropped, others are kept."""
        good = '{"name":"partymode","type":"ToggleControl","value":true}'
        lines = [f"data: [42, {good}]\n".encode(), b"\n"]
        _set_sse_response(mock_session, _make_sse_response(lines))

        received = [c async for c in client.stream_controls(DEVICE_ID)]

        assert len(received) == 1
        assert len(received[0]) == 1
        assert received[0][0].name == "partymode"

    async def test_invalid_control_object_is_skipped(
        self, client: LiebherrClient, mock_session: MagicMock
    ) -> None:
        """A control object missing required keys is dropped with a warning."""
        # Missing the required 'name' key triggers a KeyError in parse_control.
        lines = [b'data: [{"type":"ToggleControl"}]\n', b"\n"]
        _set_sse_response(mock_session, _make_sse_response(lines))

        received = [c async for c in client.stream_controls(DEVICE_ID)]

        assert len(received) == 1
        assert received[0] == []

    async def test_unauthorized_status_raises(
        self, client: LiebherrClient, mock_session: MagicMock
    ) -> None:
        """HTTP 401 on the SSE handshake raises an auth error."""
        _set_sse_response(mock_session, _make_sse_response([], status=401))

        with pytest.raises(LiebherrAuthenticationError):
            async for _ in client.stream_controls(DEVICE_ID):
                pass

    async def test_not_found_status_raises(
        self, client: LiebherrClient, mock_session: MagicMock
    ) -> None:
        """HTTP 404 on the SSE handshake raises a not-found error."""
        _set_sse_response(mock_session, _make_sse_response([], status=404))

        with pytest.raises(LiebherrNotFoundError):
            async for _ in client.stream_controls(DEVICE_ID):
                pass

    async def test_precondition_failed_status_raises(
        self, client: LiebherrClient, mock_session: MagicMock
    ) -> None:
        """HTTP 412 on the SSE handshake raises a precondition error."""
        _set_sse_response(mock_session, _make_sse_response([], status=412))

        with pytest.raises(LiebherrPreconditionFailedError):
            async for _ in client.stream_controls(DEVICE_ID):
                pass

    async def test_server_error_status_raises(
        self, client: LiebherrClient, mock_session: MagicMock
    ) -> None:
        """HTTP 5xx on the SSE handshake raises a server error."""
        _set_sse_response(mock_session, _make_sse_response([], status=503))

        with pytest.raises(LiebherrServerError):
            async for _ in client.stream_controls(DEVICE_ID):
                pass

    async def test_unexpected_status_raises_connection_error(
        self, client: LiebherrClient, mock_session: MagicMock
    ) -> None:
        """Any other non-200 status surfaces as a connection error."""
        _set_sse_response(mock_session, _make_sse_response([], status=418))

        with pytest.raises(LiebherrConnectionError):
            async for _ in client.stream_controls(DEVICE_ID):
                pass

    @pytest.mark.parametrize(
        ("raise_after", "expected"),
        [
            (aiohttp.ClientError("connection reset"), LiebherrConnectionError),
            (aiohttp.ServerTimeoutError("read timed out"), LiebherrTimeoutError),
            (TimeoutError("read timed out"), LiebherrTimeoutError),
        ],
    )
    async def test_mid_stream_error_is_wrapped(
        self,
        client: LiebherrClient,
        mock_session: MagicMock,
        raise_after: BaseException,
        expected: type[Exception],
    ) -> None:
        """An error raised while iterating the stream is wrapped."""
        _set_sse_response(mock_session, _make_sse_response([], raise_after=raise_after))

        with pytest.raises(expected):
            async for _ in client.stream_controls(DEVICE_ID):
                pass

    async def test_connect_timeout_raises_timeout_error(
        self, client: LiebherrClient, mock_session: MagicMock
    ) -> None:
        """A timeout while establishing the SSE connection is wrapped."""
        response_cm = MagicMock()
        response_cm.__aenter__ = AsyncMock(side_effect=TimeoutError())
        response_cm.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=response_cm)

        with pytest.raises(LiebherrTimeoutError):
            async for _ in client.stream_controls(DEVICE_ID):
                pass

    async def test_get_raising_client_error_is_wrapped(
        self, client: LiebherrClient, mock_session: MagicMock
    ) -> None:
        """A synchronous ClientError from session.get is wrapped."""
        mock_session.get = MagicMock(side_effect=aiohttp.ClientError("dns failure"))

        with pytest.raises(LiebherrConnectionError):
            async for _ in client.stream_controls(DEVICE_ID):
                pass

    async def test_aenter_client_error_is_wrapped(
        self, client: LiebherrClient, mock_session: MagicMock
    ) -> None:
        """A ClientError from response.__aenter__ surfaces as ConnectionError."""
        response_cm = MagicMock()
        response_cm.__aenter__ = AsyncMock(
            side_effect=aiohttp.ClientError("handshake failed")
        )
        response_cm.__aexit__ = AsyncMock(return_value=None)
        mock_session.get = MagicMock(return_value=response_cm)

        with pytest.raises(LiebherrConnectionError):
            async for _ in client.stream_controls(DEVICE_ID):
                pass


class TestStreamReconnectDelay:
    """Tests for the SSE reconnect backoff calculation."""

    def test_reconnect_delay_grows_with_attempts(self, client: LiebherrClient) -> None:
        """The base delay is used on the first attempt."""
        delay = client._sse_reconnect_delay(0, 4.0, 60.0)
        assert 2.0 <= delay <= 4.0

    def test_reconnect_delay_is_capped_at_max(self, client: LiebherrClient) -> None:
        """Exponential growth is capped at max_delay."""
        delay = client._sse_reconnect_delay(20, 1.0, 10.0)
        assert 5.0 <= delay <= 10.0


class TestStreamControlsForever:
    """Tests for the auto-reconnecting stream wrapper."""

    async def test_reconnects_after_recoverable_error(
        self,
        client: LiebherrClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A recoverable error triggers a reconnect; events are relayed."""
        calls: list[str] = []

        async def fake_stream(device_id: str) -> Any:
            calls.append(device_id)
            if len(calls) == 1:
                yield ["a"]
                yield ["b"]
                raise LiebherrConnectionError("drop")
            raise LiebherrAuthenticationError("stop")

        sleeps: list[float] = []

        async def fake_sleep(delay: float) -> None:
            sleeps.append(delay)

        monkeypatch.setattr(client, "stream_controls", fake_stream)
        monkeypatch.setattr(asyncio, "sleep", fake_sleep)

        received: list[Any] = []
        with pytest.raises(LiebherrAuthenticationError):
            async for controls in client.stream_controls_forever(DEVICE_ID):
                received.append(controls)

        assert received == [["a"], ["b"]]
        assert len(calls) == 2
        assert len(sleeps) == 1

    async def test_backoff_resets_after_successful_event(
        self,
        client: LiebherrClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The backoff attempt counter resets after a yielded event."""
        calls: list[str] = []

        async def fake_stream(device_id: str) -> Any:
            calls.append(device_id)
            if len(calls) == 1:
                yield ["a"]
                raise LiebherrConnectionError("drop")
            if len(calls) == 2:
                raise LiebherrConnectionError("drop again")
            raise LiebherrAuthenticationError("stop")

        attempts: list[int] = []

        def spy_delay(attempt: int, base_delay: float, max_delay: float) -> float:
            attempts.append(attempt)
            return 0.0

        async def fake_sleep(delay: float) -> None:
            return None

        monkeypatch.setattr(client, "stream_controls", fake_stream)
        monkeypatch.setattr(client, "_sse_reconnect_delay", spy_delay)
        monkeypatch.setattr(asyncio, "sleep", fake_sleep)

        with pytest.raises(LiebherrAuthenticationError):
            async for _ in client.stream_controls_forever(DEVICE_ID):
                pass

        # First drop happens after a yield (attempt reset to 0); second drop
        # occurs with no event received, so the attempt counter has advanced.
        assert attempts == [0, 1]

    async def test_reconnects_after_clean_stream_close(
        self,
        client: LiebherrClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A stream that ends without error still reconnects."""
        calls: list[str] = []

        async def fake_stream(device_id: str) -> Any:
            calls.append(device_id)
            if len(calls) == 1:
                yield ["a"]
                return
            raise LiebherrAuthenticationError("stop")

        async def fake_sleep(delay: float) -> None:
            return None

        monkeypatch.setattr(client, "stream_controls", fake_stream)
        monkeypatch.setattr(asyncio, "sleep", fake_sleep)

        received: list[Any] = []
        with pytest.raises(LiebherrAuthenticationError):
            async for controls in client.stream_controls_forever(DEVICE_ID):
                received.append(controls)

        assert received == [["a"]]
        assert len(calls) == 2

    async def test_non_recoverable_error_is_not_retried(
        self,
        client: LiebherrClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A non-recoverable error propagates without reconnecting."""
        calls: list[str] = []

        async def fake_stream(device_id: str) -> Any:
            calls.append(device_id)
            raise LiebherrNotFoundError("gone")
            yield  # pragma: no cover - marks this as an async generator

        sleeps: list[float] = []

        async def fake_sleep(delay: float) -> None:
            sleeps.append(delay)

        monkeypatch.setattr(client, "stream_controls", fake_stream)
        monkeypatch.setattr(asyncio, "sleep", fake_sleep)

        with pytest.raises(LiebherrNotFoundError):
            async for _ in client.stream_controls_forever(DEVICE_ID):
                pass

        assert len(calls) == 1
        assert not sleeps

    async def test_connect_and_disconnect_callbacks_fire(
        self,
        client: LiebherrClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """on_connect fires on first event; on_disconnect on a drop."""
        calls: list[str] = []

        async def fake_stream(device_id: str) -> Any:
            calls.append(device_id)
            if len(calls) == 1:
                yield ["a"]
                raise LiebherrConnectionError("drop")
            raise LiebherrAuthenticationError("stop")

        async def fake_sleep(delay: float) -> None:
            return None

        monkeypatch.setattr(client, "stream_controls", fake_stream)
        monkeypatch.setattr(asyncio, "sleep", fake_sleep)

        events: list[str] = []
        with pytest.raises(LiebherrAuthenticationError):
            async for _ in client.stream_controls_forever(
                DEVICE_ID,
                on_connect=lambda: events.append("connect"),
                on_disconnect=lambda: events.append("disconnect"),
            ):
                pass

        assert events == ["connect", "disconnect"]

    async def test_disconnect_callback_skipped_without_prior_connect(
        self,
        client: LiebherrClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """on_disconnect is not called if no event was ever received."""

        async def fake_stream(device_id: str) -> Any:
            raise LiebherrConnectionError("drop")
            yield  # pragma: no cover - marks this as an async generator

        recovered = {"count": 0}

        async def fake_sleep(delay: float) -> None:
            recovered["count"] += 1
            if recovered["count"] >= 2:
                raise LiebherrAuthenticationError("stop")

        monkeypatch.setattr(client, "stream_controls", fake_stream)
        monkeypatch.setattr(asyncio, "sleep", fake_sleep)

        events: list[str] = []
        with pytest.raises(LiebherrAuthenticationError):
            async for _ in client.stream_controls_forever(
                DEVICE_ID,
                on_connect=lambda: events.append("connect"),
                on_disconnect=lambda: events.append("disconnect"),
            ):
                pass

        assert not events

    async def test_raising_callback_does_not_break_stream(
        self,
        client: LiebherrClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """An exception from a callback is swallowed and logged."""
        calls: list[str] = []

        async def fake_stream(device_id: str) -> Any:
            calls.append(device_id)
            if len(calls) == 1:
                yield ["a"]
                raise LiebherrConnectionError("drop")
            raise LiebherrAuthenticationError("stop")

        async def fake_sleep(delay: float) -> None:
            return None

        def boom() -> None:
            raise ValueError("callback boom")

        monkeypatch.setattr(client, "stream_controls", fake_stream)
        monkeypatch.setattr(asyncio, "sleep", fake_sleep)

        received: list[Any] = []
        with pytest.raises(LiebherrAuthenticationError):
            async for controls in client.stream_controls_forever(
                DEVICE_ID, on_connect=boom, on_disconnect=boom
            ):
                received.append(controls)

        # Despite the callbacks raising, the event was still delivered and the
        # loop continued until the non-recoverable error.
        assert received == [["a"]]
        assert len(calls) == 2
