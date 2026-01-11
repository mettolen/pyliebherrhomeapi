"""Tests for Liebherr models."""

from typing import Any

import pytest

from pyliebherrhomeapi import (
    AutoDoorControl,
    BioFreshPlusControl,
    BioFreshPlusMode,
    Device,
    DeviceControl,
    DeviceState,
    DeviceType,
    DoorState,
    HydroBreezeControl,
    HydroBreezeMode,
    IceMakerControl,
    IceMakerMode,
    TemperatureControl,
    TemperatureUnit,
    ToggleControl,
    ZonePosition,
)
from pyliebherrhomeapi.models import parse_control


class TestDevice:
    """Tests for Device model."""

    def test_device_from_dict(self) -> None:
        """Test creating Device from dict."""
        data = {
            "deviceId": "12345",
            "nickname": "Kitchen Fridge",
            "deviceType": "FRIDGE",
            "imageUrl": "http://example.com/image.png",
            "deviceName": "Test Device",
        }
        device = Device.from_dict(data)
        assert device.device_id == "12345"
        assert device.nickname == "Kitchen Fridge"
        assert device.device_type == DeviceType.FRIDGE
        assert device.image_url == "http://example.com/image.png"
        assert device.device_name == "Test Device"

    def test_device_from_dict_minimal(self) -> None:
        """Test creating Device from dict with minimal data."""
        data = {"deviceId": "12345"}
        device = Device.from_dict(data)
        assert device.device_id == "12345"
        assert device.nickname is None
        assert device.device_type is None
        assert device.image_url is None
        assert device.device_name is None

    @pytest.mark.parametrize(
        (
            "device_type",
            "expected_is_fridge",
            "expected_is_freezer",
            "expected_is_combi",
            "expected_is_wine",
        ),
        [
            (DeviceType.FRIDGE, True, False, False, False),
            (DeviceType.FREEZER, False, True, False, False),
            (DeviceType.COMBI, False, False, True, False),
            (DeviceType.WINE, False, False, False, True),
        ],
    )
    def test_device_type_methods(
        self,
        device_type: DeviceType,
        expected_is_fridge: bool,
        expected_is_freezer: bool,
        expected_is_combi: bool,
        expected_is_wine: bool,
    ) -> None:
        """Test device type checking methods."""
        device = Device(device_id="1", device_type=device_type)
        assert device.is_fridge() is expected_is_fridge
        assert device.is_freezer() is expected_is_freezer
        assert device.is_combi() is expected_is_combi
        assert device.is_wine() is expected_is_wine

    def test_is_methods_with_none_type(self) -> None:
        """Test is_* methods when device_type is None."""
        device = Device(device_id="1", device_type=None)
        assert device.is_fridge() is False
        assert device.is_freezer() is False
        assert device.is_combi() is False
        assert device.is_wine() is False

    def test_device_unknown_type_retains_raw_value(self) -> None:
        """Unknown device types are preserved as raw strings."""

        device = Device.from_dict({"deviceId": "1", "deviceType": "NEW_TYPE"})

        assert device.device_type == "NEW_TYPE"
        assert device.is_fridge() is False


class TestTemperatureControl:
    """Tests for TemperatureControl model."""

    def test_temperature_control_from_dict(self) -> None:
        """Test creating TemperatureControl from dict."""
        data = {
            "name": "temperature",
            "type": "TemperatureControl",
            "zoneId": 0,
            "zonePosition": "top",
            "value": 4,
            "target": 5,
            "min": 2,
            "max": 8,
            "unit": "°C",
        }
        control = TemperatureControl.from_dict(data)
        assert control.name == "temperature"
        assert control.type == "TemperatureControl"
        assert control.zone_id == 0
        assert control.zone_position == ZonePosition.TOP
        assert control.value == 4
        assert control.target == 5
        assert control.min == 2
        assert control.max == 8
        assert control.unit == TemperatureUnit.CELSIUS

    def test_temperature_control_from_dict_minimal(self) -> None:
        """Test creating TemperatureControl from dict with minimal data."""
        data = {"name": "temperature", "type": "TemperatureControl", "zoneId": 0}
        control = TemperatureControl.from_dict(data)
        assert control.name == "temperature"
        assert control.zone_id == 0
        assert control.value is None
        assert control.target is None

    def test_temperature_control_unknown_zone_position(self) -> None:
        """Unknown zone positions are preserved as raw strings."""

        data = {
            "name": "temperature",
            "type": "TemperatureControl",
            "zoneId": 0,
            "zonePosition": "mystery",
            "unit": "KELVIN",
        }

        control = TemperatureControl.from_dict(data)

        assert control.zone_position == "mystery"
        assert control.unit == "KELVIN"

    @pytest.mark.parametrize(
        ("min_temp", "max_temp", "test_value", "expected"),
        [
            # Within range
            (2, 8, 4, True),
            (2, 8, 2, True),
            (2, 8, 8, True),
            # Below min
            (2, 8, 1, False),
            (2, 8, 0, False),
            # Above max
            (2, 8, 9, False),
            (2, 8, 10, False),
            # No limits
            (None, None, -100, True),
            (None, None, 100, True),
            # Only min
            (2, None, 2, True),
            (2, None, 100, True),
            (2, None, 1, False),
            # Only max
            (None, 8, 8, True),
            (None, 8, -100, True),
            (None, 8, 9, False),
        ],
    )
    def test_validate_temperature(
        self,
        min_temp: int | None,
        max_temp: int | None,
        test_value: int,
        expected: bool,
    ) -> None:
        """Test validate_temperature with various min/max combinations."""
        control = TemperatureControl(
            name="temperature",
            type="TemperatureControl",
            zone_id=0,
            min=min_temp,
            max=max_temp,
        )
        assert control.validate_temperature(test_value) is expected


class TestToggleControl:
    """Tests for ToggleControl model."""

    def test_toggle_control_from_dict(self) -> None:
        """Test creating ToggleControl from dict."""
        data = {
            "name": "superfrost",
            "type": "ToggleControl",
            "zoneId": 0,
            "zonePosition": "bottom",
            "value": True,
        }
        control = ToggleControl.from_dict(data)
        assert control.name == "superfrost"
        assert control.type == "ToggleControl"
        assert control.zone_id == 0
        assert control.zone_position == ZonePosition.BOTTOM
        assert control.value is True

    def test_toggle_control_from_dict_minimal(self) -> None:
        """Test creating ToggleControl from dict with minimal data."""
        data = {"name": "superfrost", "type": "ToggleControl"}
        control = ToggleControl.from_dict(data)
        assert control.name == "superfrost"
        assert control.zone_id is None
        assert control.value is None


class TestAutoDoorControl:
    """Tests for AutoDoorControl model."""

    def test_auto_door_control_from_dict(self) -> None:
        """Test creating AutoDoorControl from dict."""
        data = {
            "name": "autodoor",
            "type": "AutoDoorControl",
            "zoneId": 0,
            "zonePosition": "middle",
            "value": "CLOSED",
        }
        control = AutoDoorControl.from_dict(data)
        assert control.name == "autodoor"
        assert control.type == "AutoDoorControl"
        assert control.zone_id == 0
        assert control.zone_position == ZonePosition.MIDDLE
        assert control.value == DoorState.CLOSED

    def test_auto_door_control_from_dict_minimal(self) -> None:
        """Test creating AutoDoorControl from dict with minimal data."""
        data = {"name": "autodoor", "type": "AutoDoorControl", "zoneId": 0}
        control = AutoDoorControl.from_dict(data)
        assert control.name == "autodoor"
        assert control.zone_id == 0
        assert control.value is None


class TestIceMakerControl:
    """Tests for IceMakerControl model."""

    def test_ice_maker_control_from_dict(self) -> None:
        """Test creating IceMakerControl from dict."""
        data = {
            "name": "icemaker",
            "type": "IceMakerControl",
            "zoneId": 0,
            "zonePosition": "top",
            "iceMakerMode": "MAX_ICE",
            "hasMaxIce": True,
        }
        control = IceMakerControl.from_dict(data)
        assert control.name == "icemaker"
        assert control.type == "IceMakerControl"
        assert control.zone_id == 0
        assert control.zone_position == ZonePosition.TOP
        assert control.ice_maker_mode == IceMakerMode.MAX_ICE
        assert control.has_max_ice is True

    def test_ice_maker_control_from_dict_minimal(self) -> None:
        """Test creating IceMakerControl from dict with minimal data."""
        data = {"name": "icemaker", "type": "IceMakerControl", "zoneId": 0}
        control = IceMakerControl.from_dict(data)
        assert control.name == "icemaker"
        assert control.zone_id == 0
        assert control.ice_maker_mode is None
        assert control.has_max_ice is None


class TestHydroBreezeControl:
    """Tests for HydroBreezeControl model."""

    def test_hydro_breeze_control_from_dict(self) -> None:
        """Test creating HydroBreezeControl from dict."""
        data = {
            "name": "hydrobreeze",
            "type": "HydroBreezeControl",
            "zoneId": 0,
            "currentMode": "HIGH",
        }
        control = HydroBreezeControl.from_dict(data)
        assert control.name == "hydrobreeze"
        assert control.type == "HydroBreezeControl"
        assert control.zone_id == 0
        assert control.current_mode == HydroBreezeMode.HIGH

    def test_hydro_breeze_control_from_dict_minimal(self) -> None:
        """Test creating HydroBreezeControl from dict with minimal data."""
        data = {"name": "hydrobreeze", "type": "HydroBreezeControl", "zoneId": 0}
        control = HydroBreezeControl.from_dict(data)
        assert control.name == "hydrobreeze"
        assert control.zone_id == 0
        assert control.current_mode is None


class TestBioFreshPlusControl:
    """Tests for BioFreshPlusControl model."""

    def test_biofresh_plus_control_from_dict(self) -> None:
        """Test creating BioFreshPlusControl from dict."""
        data = {
            "name": "biofreshplus",
            "type": "BioFreshPlusControl",
            "zoneId": 0,
            "currentMode": "ZERO_ZERO",
            "supportedModes": ["ZERO_ZERO", "ZERO_MINUS_TWO"],
            "temperatureUnit": "°C",
        }
        control = BioFreshPlusControl.from_dict(data)
        assert control.name == "biofreshplus"
        assert control.type == "BioFreshPlusControl"
        assert control.zone_id == 0
        assert control.current_mode == BioFreshPlusMode.ZERO_ZERO
        assert len(control.supported_modes) == 2
        assert BioFreshPlusMode.ZERO_ZERO in control.supported_modes
        assert control.temperature_unit == TemperatureUnit.CELSIUS

    def test_biofresh_plus_control_from_dict_minimal(self) -> None:
        """Test creating BioFreshPlusControl from dict with minimal data."""
        data = {"name": "biofreshplus", "type": "BioFreshPlusControl", "zoneId": 0}
        control = BioFreshPlusControl.from_dict(data)
        assert control.name == "biofreshplus"
        assert control.zone_id == 0
        assert control.current_mode is None
        assert len(control.supported_modes) == 0
        assert control.temperature_unit is None


class TestParseControl:
    """Tests for parse_control function."""

    @pytest.mark.parametrize(
        ("control_type", "expected_class"),
        [
            ("TemperatureControl", TemperatureControl),
            ("ToggleControl", ToggleControl),
            ("AutoDoorControl", AutoDoorControl),
            ("IceMakerControl", IceMakerControl),
            ("HydroBreezeControl", HydroBreezeControl),
            ("BioFreshPlusControl", BioFreshPlusControl),
            ("UnknownControl", ToggleControl),  # Fallback
        ],
    )
    def test_parse_control_types(
        self, control_type: str, expected_class: type[DeviceControl]
    ) -> None:
        """Test parsing various control types."""
        data: dict[str, Any] = {"name": "test", "type": control_type}
        if control_type != "ToggleControl":
            data["zoneId"] = 0
        control = parse_control(data)
        assert isinstance(control, expected_class)


class TestDeviceState:
    """Tests for DeviceState model."""

    @pytest.fixture
    def sample_device(self) -> Device:
        """Create a sample device."""
        return Device(device_id="12345", device_type=DeviceType.FRIDGE)

    @pytest.fixture
    def sample_controls(self) -> list[DeviceControl]:
        """Create sample controls."""
        return [
            TemperatureControl(name="temp1", type="TemperatureControl", zone_id=0),
            TemperatureControl(name="temp2", type="TemperatureControl", zone_id=1),
            ToggleControl(name="toggle1", type="ToggleControl", zone_id=0),
            ToggleControl(name="toggle2", type="ToggleControl", zone_id=1),
            AutoDoorControl(name="door1", type="AutoDoorControl", zone_id=0),
            IceMakerControl(name="ice1", type="IceMakerControl", zone_id=0),
            HydroBreezeControl(name="hydro1", type="HydroBreezeControl", zone_id=1),
            BioFreshPlusControl(name="bio1", type="BioFreshPlusControl", zone_id=1),
        ]

    def test_device_state_creation(
        self, sample_device: Device, sample_controls: list[DeviceControl]
    ) -> None:
        """Test creating DeviceState."""
        state = DeviceState(device=sample_device, controls=sample_controls)
        assert state.device == sample_device
        assert len(state.controls) == 8

    def test_device_state_default_controls(self, sample_device: Device) -> None:
        """Test DeviceState with default empty controls."""
        state = DeviceState(device=sample_device)
        assert state.device == sample_device
        assert len(state.controls) == 0

    @pytest.mark.parametrize(
        ("method_name", "expected_type", "expected_count"),
        [
            ("get_temperature_controls", TemperatureControl, 2),
            ("get_toggle_controls", ToggleControl, 2),
            ("get_auto_door_controls", AutoDoorControl, 1),
            ("get_ice_maker_controls", IceMakerControl, 1),
            ("get_hydro_breeze_controls", HydroBreezeControl, 1),
            ("get_biofresh_plus_controls", BioFreshPlusControl, 1),
        ],
    )
    def test_get_control_type_methods(
        self,
        sample_device: Device,
        sample_controls: list[DeviceControl],
        method_name: str,
        expected_type: type[DeviceControl],
        expected_count: int,
    ) -> None:
        """Test various get_*_controls methods."""
        state = DeviceState(device=sample_device, controls=sample_controls)
        method = getattr(state, method_name)
        controls = method()
        assert len(controls) == expected_count
        assert all(isinstance(c, expected_type) for c in controls)

    def test_get_control_by_name_found(
        self, sample_device: Device, sample_controls: list[DeviceControl]
    ) -> None:
        """Test get_control_by_name when control exists."""
        state = DeviceState(device=sample_device, controls=sample_controls)
        control = state.get_control_by_name("temp1")
        assert control is not None
        assert control.name == "temp1"

    def test_get_control_by_name_not_found(
        self, sample_device: Device, sample_controls: list[DeviceControl]
    ) -> None:
        """Test get_control_by_name when control doesn't exist."""
        state = DeviceState(device=sample_device, controls=sample_controls)
        control = state.get_control_by_name("nonexistent")
        assert control is None

    @pytest.mark.parametrize(
        ("zone_id", "expected_count"),
        [
            (0, 4),  # temp1, toggle1, door1, ice1
            (1, 4),  # temp2, toggle2, hydro1, bio1
        ],
    )
    def test_get_controls_by_zone(
        self,
        sample_device: Device,
        sample_controls: list[DeviceControl],
        zone_id: int,
        expected_count: int,
    ) -> None:
        """Test get_controls_by_zone method."""
        state = DeviceState(device=sample_device, controls=sample_controls)
        zone_controls = state.get_controls_by_zone(zone_id)
        assert len(zone_controls) == expected_count

    def test_get_controls_by_zone_empty(self, sample_device: Device) -> None:
        """Test get_controls_by_zone with no controls."""
        state = DeviceState(device=sample_device, controls=[])
        zone_controls = state.get_controls_by_zone(0)
        assert len(zone_controls) == 0

    def test_filter_methods_with_empty_controls(self, sample_device: Device) -> None:
        """Test all filter methods with empty controls."""
        state = DeviceState(device=sample_device, controls=[])
        assert len(state.get_temperature_controls()) == 0
        assert len(state.get_toggle_controls()) == 0
        assert len(state.get_auto_door_controls()) == 0
        assert len(state.get_ice_maker_controls()) == 0
        assert len(state.get_hydro_breeze_controls()) == 0
        assert len(state.get_biofresh_plus_controls()) == 0
