"""Python library for Liebherr Home API."""

import logging
from importlib.metadata import PackageNotFoundError, version

from .client import LiebherrClient
from .exceptions import (
    LiebherrAuthenticationError,
    LiebherrBadRequestError,
    LiebherrConnectionError,
    LiebherrError,
    LiebherrNotFoundError,
    LiebherrPreconditionFailedError,
    LiebherrServerError,
    LiebherrTimeoutError,
    LiebherrUnsupportedError,
)
from .models import (
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

# Add NullHandler to prevent "No handler found" warnings
logging.getLogger(__name__).addHandler(logging.NullHandler())

try:
    __version__ = version("pyliebherrhomeapi")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    # Client
    "LiebherrClient",
    # Exceptions
    "LiebherrAuthenticationError",
    "LiebherrBadRequestError",
    "LiebherrConnectionError",
    "LiebherrError",
    "LiebherrNotFoundError",
    "LiebherrPreconditionFailedError",
    "LiebherrServerError",
    "LiebherrTimeoutError",
    "LiebherrUnsupportedError",
    # Models
    "AutoDoorControl",
    "BioFreshPlusControl",
    "BioFreshPlusMode",
    "Device",
    "DeviceControl",
    "DeviceState",
    "DeviceType",
    "DoorState",
    "HydroBreezeControl",
    "HydroBreezeMode",
    "IceMakerControl",
    "IceMakerMode",
    "TemperatureControl",
    "TemperatureUnit",
    "ToggleControl",
    "ZonePosition",
]
