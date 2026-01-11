"""Tests for Liebherr client."""
# pylint: disable=redefined-outer-name, protected-access

import importlib
from importlib.metadata import PackageNotFoundError
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiohttp.client_exceptions import ContentTypeError

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
from pyliebherrhomeapi.client import _get_version

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
        ("method_name", "kwargs"),
        [
            (
                "set_temperature",
                {"zone_id": 0, "target": 4, "unit": TemperatureUnit.CELSIUS},
            ),
            ("set_superfrost", {"zone_id": 0, "value": True}),
            ("set_supercool", {"zone_id": 0, "value": True}),
            ("set_presentation_light", {"target": 50}),
            ("set_ice_maker", {"zone_id": 0, "mode": IceMakerMode.MAX_ICE}),
            ("set_hydro_breeze", {"zone_id": 0, "mode": HydroBreezeMode.HIGH}),
            ("set_bio_fresh_plus", {"zone_id": 0, "mode": BioFreshPlusMode.ZERO_ZERO}),
            ("trigger_auto_door", {"zone_id": 0, "value": True}),
            ("set_party_mode", {"value": True}),
            ("set_night_mode", {"value": True}),
        ],
    )
    async def test_setter_methods(
        self,
        client: LiebherrClient,
        mock_response: MagicMock,
        method_name: str,
        kwargs: dict[str, Any],
    ) -> None:
        """Test all setter methods."""
        mock_response.status = 204

        method = getattr(client, method_name)
        await method(device_id=DEVICE_ID, **kwargs)
        # Should not raise


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
        """Fallback to response text when JSON parsing fails due to content type."""

        mock_response.status = 400
        mock_response.reason = "Bad Request"
        mock_response.text = AsyncMock(return_value="plain error")
        mock_response.json = AsyncMock(
            side_effect=ContentTypeError(MagicMock(), (), message="bad content")
        )

        with pytest.raises(LiebherrBadRequestError) as err:
            await client.get_devices()

        assert "plain error" in str(err.value)

    async def test_extract_message_returns_reason_when_not_dict(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Fallback to response reason when JSON is not a dict."""

        mock_response.status = 400
        mock_response.reason = "Bad Request"
        mock_response.json = AsyncMock(return_value=["oops"])

        with pytest.raises(LiebherrBadRequestError) as err:
            await client.get_devices()

        assert "Bad Request" in str(err.value)

    async def test_unexpected_json_format_raises_server_error(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Non-JSON 200 responses raise server error with context."""

        mock_response.status = 200
        mock_response.reason = "OK"
        mock_response.raise_for_status = MagicMock(return_value=None)
        mock_response.text = AsyncMock(return_value="not json")
        mock_response.json = AsyncMock(side_effect=ValueError("boom"))

        with pytest.raises(LiebherrServerError) as err:
            await client.get_devices()

        assert "Unexpected response format" in str(err.value)

    async def test_raise_for_status(
        self, client: LiebherrClient, mock_response: MagicMock
    ) -> None:
        """Test that unknown status codes call raise_for_status."""
        mock_response.status = 418
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

    def test_get_version_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Return fallback version when package metadata is missing."""

        monkeypatch.setattr(
            "pyliebherrhomeapi.client.version",
            MagicMock(side_effect=PackageNotFoundError()),
        )

        assert _get_version() == "0.0.0"

    def test_module_version_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Reload module to apply version fallback when metadata missing."""

        import pyliebherrhomeapi as module

        monkeypatch.setattr(
            "importlib.metadata.version",
            MagicMock(side_effect=PackageNotFoundError()),
        )

        reloaded = importlib.reload(module)

        assert reloaded.__version__ == "0.0.0"
