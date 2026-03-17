"""Data models for pyliebherrhomeapi."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any


def _coerce_enum[EnumT: Enum](
    enum_cls: type[EnumT], value: str | None
) -> EnumT | str | None:
    """Return enum member when possible, else the raw value.

    This prevents hard failures when the upstream API introduces new values.
    The API may return values in any case, so we try both the original
    and lowercase variants.
    """
    if value is None:
        return None
    for variant in (value, value.lower()):
        try:
            return enum_cls(variant)
        except ValueError:
            pass
    return value


class DeviceType(StrEnum):
    """Device type enumeration."""

    FRIDGE = "fridge"
    FREEZER = "freezer"
    COMBI = "combi"
    WINE = "wine"


class TemperatureUnit(StrEnum):
    """Temperature unit enumeration."""

    CELSIUS = "°C"
    FAHRENHEIT = "°F"


class ZonePosition(StrEnum):
    """Zone position enumeration."""

    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class IceMakerMode(StrEnum):
    """Ice maker mode enumeration."""

    OFF = "off"
    ON = "on"
    MAX_ICE = "max_ice"


class HydroBreezeMode(StrEnum):
    """HydroBreeze mode enumeration."""

    OFF = "off"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BioFreshPlusMode(StrEnum):
    """BioFreshPlus mode enumeration."""

    ZERO_ZERO = "zero_zero"
    ZERO_MINUS_TWO = "zero_minus_two"
    MINUS_TWO_MINUS_TWO = "minus_two_minus_two"
    MINUS_TWO_ZERO = "minus_two_zero"


class DoorState(StrEnum):
    """Door state enumeration."""

    CLOSED = "closed"
    OPEN = "open"
    MOVING = "moving"


class ControlType(StrEnum):
    """Control type enumeration."""

    TEMPERATURE = "TemperatureControl"
    TOGGLE = "ToggleControl"
    AUTO_DOOR = "AutoDoorControl"
    ICE_MAKER = "IceMakerControl"
    HYDRO_BREEZE = "HydroBreezeControl"
    BIO_FRESH_PLUS = "BioFreshPlusControl"
    PRESENTATION_LIGHT = "PresentationLightControl"


@dataclass(frozen=True, slots=True)
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


@dataclass(frozen=True, slots=True)
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


@dataclass(frozen=True, slots=True)
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


@dataclass(frozen=True, slots=True)
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


@dataclass(frozen=True, slots=True)
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


@dataclass(frozen=True, slots=True)
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


@dataclass(frozen=True, slots=True)
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


@dataclass(frozen=True, slots=True)
class PresentationLightControl:
    """Presentation light control information."""

    name: str
    type: str
    value: int | None = None
    max: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PresentationLightControl:
        """Create PresentationLightControl from API response."""
        return cls(
            name=data["name"],
            type=data["type"],
            value=data.get("value"),
            max=data.get("max"),
        )


DeviceControl = (
    TemperatureControl
    | ToggleControl
    | AutoDoorControl
    | IceMakerControl
    | HydroBreezeControl
    | BioFreshPlusControl
    | PresentationLightControl
)


@dataclass(frozen=True, slots=True)
class DeviceState:
    """Complete device state including info and all controls."""

    device: Device
    controls: list[DeviceControl] = field(default_factory=list)

    def get_temperature_controls(self) -> dict[int, TemperatureControl]:
        """Get all temperature controls grouped by zone.

        Returns:
            Dictionary mapping zone_id to temperature control.

        """
        result: dict[int, TemperatureControl] = {}
        for control in self.controls:
            if isinstance(control, TemperatureControl):
                result[control.zone_id] = control
        return result

    def get_toggle_controls(self) -> dict[str, ToggleControl]:
        """Get all toggle controls keyed by control name.

        Returns:
            Dictionary mapping control name to toggle control.

        """
        result: dict[str, ToggleControl] = {}
        for control in self.controls:
            if isinstance(control, ToggleControl):
                result[control.name] = control
        return result

    def get_auto_door_controls(self) -> dict[int, AutoDoorControl]:
        """Get all auto door controls grouped by zone.

        Returns:
            Dictionary mapping zone_id to auto door control.

        """
        result: dict[int, AutoDoorControl] = {}
        for control in self.controls:
            if isinstance(control, AutoDoorControl):
                result[control.zone_id] = control
        return result

    def get_ice_maker_controls(self) -> dict[int, IceMakerControl]:
        """Get all ice maker controls grouped by zone.

        Returns:
            Dictionary mapping zone_id to ice maker control.

        """
        result: dict[int, IceMakerControl] = {}
        for control in self.controls:
            if isinstance(control, IceMakerControl):
                result[control.zone_id] = control
        return result

    def get_hydro_breeze_controls(self) -> dict[int, HydroBreezeControl]:
        """Get all HydroBreeze controls grouped by zone.

        Returns:
            Dictionary mapping zone_id to HydroBreeze control.

        """
        result: dict[int, HydroBreezeControl] = {}
        for control in self.controls:
            if isinstance(control, HydroBreezeControl):
                result[control.zone_id] = control
        return result

    def get_biofresh_plus_controls(self) -> dict[int, BioFreshPlusControl]:
        """Get all BioFreshPlus controls grouped by zone.

        Returns:
            Dictionary mapping zone_id to BioFreshPlus control.

        """
        result: dict[int, BioFreshPlusControl] = {}
        for control in self.controls:
            if isinstance(control, BioFreshPlusControl):
                result[control.zone_id] = control
        return result

    def get_presentation_light_controls(
        self,
    ) -> dict[str, PresentationLightControl]:
        """Get all presentation light controls keyed by control name.

        Returns:
            Dictionary mapping control name to presentation light control.

        """
        result: dict[str, PresentationLightControl] = {}
        for control in self.controls:
            if isinstance(control, PresentationLightControl):
                result[control.name] = control
        return result

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
    if control_type == ControlType.PRESENTATION_LIGHT.value:
        return PresentationLightControl.from_dict(data)

    # Fallback to ToggleControl for unknown types
    return ToggleControl.from_dict(data)
