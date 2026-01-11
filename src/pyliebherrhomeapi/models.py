"""Data models for pyliebherrhomeapi."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

_EnumT = TypeVar("_EnumT", bound=Enum)


def _coerce_enum(enum_cls: type[_EnumT], value: str | None) -> _EnumT | str | None:
    """Return enum member when possible, else the raw value.

    This prevents hard failures when the upstream API introduces new values.
    """

    if value is None:
        return None
    try:
        return enum_cls(value)
    except ValueError:
        return value


class DeviceType(str, Enum):
    """Device type enumeration."""

    FRIDGE = "FRIDGE"
    FREEZER = "FREEZER"
    COMBI = "COMBI"
    WINE = "WINE"


class TemperatureUnit(str, Enum):
    """Temperature unit enumeration."""

    CELSIUS = "°C"
    FAHRENHEIT = "°F"


class ZonePosition(str, Enum):
    """Zone position enumeration."""

    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class IceMakerMode(str, Enum):
    """Ice maker mode enumeration."""

    OFF = "OFF"
    ON = "ON"
    MAX_ICE = "MAX_ICE"


class HydroBreezeMode(str, Enum):
    """HydroBreeze mode enumeration."""

    OFF = "OFF"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class BioFreshPlusMode(str, Enum):
    """BioFreshPlus mode enumeration."""

    ZERO_ZERO = "ZERO_ZERO"
    ZERO_MINUS_TWO = "ZERO_MINUS_TWO"
    MINUS_TWO_MINUS_TWO = "MINUS_TWO_MINUS_TWO"
    MINUS_TWO_ZERO = "MINUS_TWO_ZERO"


class DoorState(str, Enum):
    """Door state enumeration."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    MOVING = "MOVING"


class ControlType(str, Enum):
    """Control type enumeration."""

    TEMPERATURE = "TemperatureControl"
    TOGGLE = "ToggleControl"
    AUTO_DOOR = "AutoDoorControl"
    ICE_MAKER = "IceMakerControl"
    HYDRO_BREEZE = "HydroBreezeControl"
    BIO_FRESH_PLUS = "BioFreshPlusControl"


@dataclass
class Device:
    """Liebherr device information."""

    device_id: str
    nickname: str | None = None
    device_type: DeviceType | str | None = None
    image_url: str | None = None
    device_name: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Device:
        """Create Device from API response."""
        return cls(
            device_id=data["deviceId"],
            nickname=data.get("nickname"),
            device_type=_coerce_enum(DeviceType, data.get("deviceType")),
            image_url=data.get("imageUrl"),
            device_name=data.get("deviceName"),
        )

    def is_fridge(self) -> bool:
        """Check if device is a fridge."""
        return self.device_type == DeviceType.FRIDGE

    def is_freezer(self) -> bool:
        """Check if device is a freezer."""
        return self.device_type == DeviceType.FREEZER

    def is_combi(self) -> bool:
        """Check if device is a combination fridge/freezer."""
        return self.device_type == DeviceType.COMBI

    def is_wine(self) -> bool:
        """Check if device is a wine cooler."""
        return self.device_type == DeviceType.WINE


@dataclass
class TemperatureControl:
    """Temperature control information."""

    name: str
    type: str
    zone_id: int
    zone_position: ZonePosition | str | None = None
    value: int | None = None
    target: int | None = None
    min: int | None = None
    max: int | None = None
    unit: TemperatureUnit | str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TemperatureControl:
        """Create TemperatureControl from API response."""
        return cls(
            name=data["name"],
            type=data["type"],
            zone_id=data["zoneId"],
            zone_position=_coerce_enum(ZonePosition, data.get("zonePosition")),
            value=data.get("value"),
            target=data.get("target"),
            min=data.get("min"),
            max=data.get("max"),
            unit=_coerce_enum(TemperatureUnit, data.get("unit")),
        )

    def validate_temperature(self, temp: int) -> bool:
        """Validate if temperature is within allowed range.

        Args:
            temp: Temperature value to validate.

        Returns:
            True if temperature is within min/max range, False otherwise.

        """
        if self.min is not None and temp < self.min:
            return False
        if self.max is not None and temp > self.max:
            return False
        return True


@dataclass
class ToggleControl:
    """Toggle control (SuperCool, SuperFrost, etc.)."""

    name: str
    type: str
    zone_id: int | None = None
    zone_position: ZonePosition | str | None = None
    value: bool | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToggleControl:
        """Create ToggleControl from API response."""
        return cls(
            name=data["name"],
            type=data["type"],
            zone_id=data.get("zoneId"),
            zone_position=_coerce_enum(ZonePosition, data.get("zonePosition")),
            value=data.get("value"),
        )


@dataclass
class AutoDoorControl:
    """Auto door control information."""

    name: str
    type: str
    zone_id: int
    zone_position: ZonePosition | str | None = None
    value: DoorState | str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AutoDoorControl:
        """Create AutoDoorControl from API response."""
        return cls(
            name=data["name"],
            type=data["type"],
            zone_id=data["zoneId"],
            zone_position=_coerce_enum(ZonePosition, data.get("zonePosition")),
            value=_coerce_enum(DoorState, data.get("value")),
        )


@dataclass
class IceMakerControl:
    """Ice maker control information."""

    name: str
    type: str
    zone_id: int
    zone_position: ZonePosition | str | None = None
    ice_maker_mode: IceMakerMode | str | None = None
    has_max_ice: bool | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IceMakerControl:
        """Create IceMakerControl from API response."""
        return cls(
            name=data["name"],
            type=data["type"],
            zone_id=data["zoneId"],
            zone_position=_coerce_enum(ZonePosition, data.get("zonePosition")),
            ice_maker_mode=_coerce_enum(IceMakerMode, data.get("iceMakerMode")),
            has_max_ice=data.get("hasMaxIce"),
        )


@dataclass
class HydroBreezeControl:
    """HydroBreeze control information."""

    name: str
    type: str
    zone_id: int
    current_mode: HydroBreezeMode | str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HydroBreezeControl:
        """Create HydroBreezeControl from API response."""
        return cls(
            name=data["name"],
            type=data["type"],
            zone_id=data["zoneId"],
            current_mode=_coerce_enum(HydroBreezeMode, data.get("currentMode")),
        )


@dataclass
class BioFreshPlusControl:
    """BioFreshPlus control information."""

    name: str
    type: str
    zone_id: int
    current_mode: BioFreshPlusMode | str | None = None
    supported_modes: list[BioFreshPlusMode | str] = field(default_factory=list)
    temperature_unit: TemperatureUnit | str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BioFreshPlusControl:
        """Create BioFreshPlusControl from API response."""
        supported: list[BioFreshPlusMode | str] = []
        for mode in data.get("supportedModes", []):
            coerced = _coerce_enum(BioFreshPlusMode, mode)
            if coerced is not None:
                supported.append(coerced)
        return cls(
            name=data["name"],
            type=data["type"],
            zone_id=data["zoneId"],
            current_mode=_coerce_enum(BioFreshPlusMode, data.get("currentMode")),
            supported_modes=supported,
            temperature_unit=_coerce_enum(TemperatureUnit, data.get("temperatureUnit")),
        )


DeviceControl = (
    TemperatureControl
    | ToggleControl
    | AutoDoorControl
    | IceMakerControl
    | HydroBreezeControl
    | BioFreshPlusControl
)


@dataclass
class DeviceState:
    """Complete device state including info and all controls."""

    device: Device
    controls: list[DeviceControl] = field(default_factory=list)

    def get_temperature_controls(self) -> list[TemperatureControl]:
        """Get all temperature controls.

        Returns:
            List of temperature controls.

        """
        return [
            control
            for control in self.controls
            if isinstance(control, TemperatureControl)
        ]

    def get_toggle_controls(self) -> list[ToggleControl]:
        """Get all toggle controls.

        Returns:
            List of toggle controls.

        """
        return [
            control for control in self.controls if isinstance(control, ToggleControl)
        ]

    def get_auto_door_controls(self) -> list[AutoDoorControl]:
        """Get all auto door controls.

        Returns:
            List of auto door controls.

        """
        return [
            control for control in self.controls if isinstance(control, AutoDoorControl)
        ]

    def get_ice_maker_controls(self) -> list[IceMakerControl]:
        """Get all ice maker controls.

        Returns:
            List of ice maker controls.

        """
        return [
            control for control in self.controls if isinstance(control, IceMakerControl)
        ]

    def get_hydro_breeze_controls(self) -> list[HydroBreezeControl]:
        """Get all HydroBreeze controls.

        Returns:
            List of HydroBreeze controls.

        """
        return [
            control
            for control in self.controls
            if isinstance(control, HydroBreezeControl)
        ]

    def get_biofresh_plus_controls(self) -> list[BioFreshPlusControl]:
        """Get all BioFreshPlus controls.

        Returns:
            List of BioFreshPlus controls.

        """
        return [
            control
            for control in self.controls
            if isinstance(control, BioFreshPlusControl)
        ]

    def get_control_by_name(self, name: str) -> DeviceControl | None:
        """Get control by name.

        Args:
            name: Control name to search for.

        Returns:
            Control with matching name, or None if not found.

        """
        for control in self.controls:
            if control.name == name:
                return control
        return None

    def get_controls_by_zone(self, zone_id: int) -> list[DeviceControl]:
        """Get all controls for a specific zone.

        Args:
            zone_id: Zone ID to filter by.

        Returns:
            List of controls for the specified zone.

        """
        zone_controls: list[DeviceControl] = []
        for control in self.controls:
            if isinstance(control, TemperatureControl) and control.zone_id == zone_id:
                zone_controls.append(control)
            elif isinstance(control, ToggleControl) and control.zone_id == zone_id:
                zone_controls.append(control)
            elif isinstance(control, AutoDoorControl) and control.zone_id == zone_id:
                zone_controls.append(control)
            elif isinstance(control, IceMakerControl) and control.zone_id == zone_id:
                zone_controls.append(control)
            elif isinstance(control, HydroBreezeControl) and control.zone_id == zone_id:
                zone_controls.append(control)
            elif (
                isinstance(control, BioFreshPlusControl) and control.zone_id == zone_id
            ):
                zone_controls.append(control)
        return zone_controls


def parse_control(data: dict[str, Any]) -> DeviceControl:
    """Parse device control from API response."""
    control_type = data.get("type")

    if control_type == ControlType.TEMPERATURE.value:
        return TemperatureControl.from_dict(data)
    if control_type == ControlType.TOGGLE.value:
        return ToggleControl.from_dict(data)
    if control_type == ControlType.AUTO_DOOR.value:
        return AutoDoorControl.from_dict(data)
    if control_type == ControlType.ICE_MAKER.value:
        return IceMakerControl.from_dict(data)
    if control_type == ControlType.HYDRO_BREEZE.value:
        return HydroBreezeControl.from_dict(data)
    if control_type == ControlType.BIO_FRESH_PLUS.value:
        return BioFreshPlusControl.from_dict(data)

    # Fallback to ToggleControl for unknown types
    return ToggleControl.from_dict(data)
