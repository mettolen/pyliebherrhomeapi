# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Realtime control updates via Server-Sent Events: `stream_controls()` opens the SSE endpoint and yields parsed control lists as the appliance pushes updates _(beta)_
- `stream_controls_forever()` — auto-reconnecting wrapper around `stream_controls()` with exponential backoff and jitter, plus optional non-blocking `on_connect` / `on_disconnect` callbacks for availability tracking (e.g. in a Home Assistant integration)
- `SSE_RECONNECT_BASE_DELAY` and `SSE_RECONNECT_MAX_DELAY` constants controlling the reconnect backoff bounds

## [0.4.1] - 2026-03-22

### Added

- Added `DEFAULT_PRESENTATION_LIGHT_MAX_BRIGHTNESS` constant for presentation light default max brightness

### Fixed

- Moved `importlib.metadata.version()` call from `LiebherrClient.__init__()` to a module-level constant to prevent blocking I/O inside the event loop

## [0.4.0] - 2026-03-18

### Added

- Added `PresentationLightControl` model and `ControlType.PRESENTATION_LIGHT` enum value
- Added `DeviceState.get_presentation_light_controls()` method
- Exported `PresentationLightControl`, `ControlType`, and `parse_control` from the public API
- Added GitHub Copilot instructions for the project

### Changed

- **Breaking**: Bumped minimum Python version from 3.11 to 3.12
- **Breaking**: Changed `DeviceState.get_toggle_controls()` to return `dict[str, ToggleControl]` keyed by control name instead of `dict[int | None, ToggleControl]` keyed by zone_id
- Made all dataclasses frozen and slotted (`frozen=True, slots=True`)
- Replaced `TypeVar` with Python 3.12 type parameter syntax in `_coerce_enum()`
- Refactored error handling in `LiebherrClient._request()` to read the response body once instead of consuming the stream twice
- Moved `__all__` definitions from individual modules to `__init__.py`
- Added `__repr__` to `LiebherrClient`
- Updated README badges and documentation

## [0.3.0] - 2026-02-19

### Changed

- **Breaking**: Migrated all `(str, Enum)` classes to `StrEnum` (`DeviceType`, `TemperatureUnit`, `ZonePosition`, `IceMakerMode`, `HydroBreezeMode`, `BioFreshPlusMode`, `DoorState`, `ControlType`)
- **Breaking**: Renamed `set_superfrost()` to `set_super_frost()` and `set_supercool()` to `set_super_cool()` for naming consistency
- **Breaking**: Renamed constants `CONTROL_SUPERFROST` to `CONTROL_SUPER_FROST` and `CONTROL_SUPERCOOL` to `CONTROL_SUPER_COOL`
- Normalized all enum string values to lowercase for compatibility with Home Assistant translation keys
- Updated `_coerce_enum()` to handle case-insensitive matching from the API
- Client setter methods now send `.value.upper()` to the API to match the expected wire format

## [0.2.1] - 2026-01-23

### Fixed

- Fixed zone-based control getter methods to return dictionaries consistently
- Changed `get_auto_door_controls`, `get_ice_maker_controls`, `get_hydro_breeze_controls`, and `get_biofresh_plus_controls` to return `dict[int, Control]` instead of single controls
- All zone-based controls now consistently return dictionaries grouped by zone_id

## [0.2.0] - 2026-01-23

### Added

- Enhanced logging capabilities with NullHandler to prevent logging warnings
- Added tests for device retrieval methods
- Added Codecov integration for code coverage tracking
- Added Dependabot configuration for automated dependency updates
- Defined `__all__` for client, exceptions, and models modules

### Changed

- Enhanced control retrieval methods with improved error handling and logging
- Updated README with enhanced documentation and badges

### Fixed

- Fixed CI workflow and test execution
- Updated GitHub Actions dependencies (actions/setup-python from 5 to 6, actions/checkout from 4 to 6, codecov/codecov-action from 4 to 5)

## [0.1.0] - 2026-01-11

### Added

- Initial project structure
- Complete implementation of Liebherr SmartDevice Home API client
- Support for all device endpoints (get devices, get device by ID)
- Support for all control endpoints (get controls, get control by name)
- Temperature control for all zones
- SuperFrost and SuperCool control
- Party Mode and Night Mode control
- Presentation Light control
- Ice Maker control with Max Ice support
- HydroBreeze mode control
- BioFreshPlus mode control
- Auto Door control
- Comprehensive data models for all control types
- Full type hints support
- Async/await implementation with aiohttp
- Comprehensive error handling with specific exception types
- Unit tests with pytest
- Example usage script
- Documentation and README with usage examples

### Documentation

- Updated README with official SmartDevice HomeAPI documentation details
- Added detailed prerequisites section with step-by-step setup instructions
- Added "Important Notes" section covering:
  - Device zone numbering (zone 0 is top, ascending from top to bottom)
  - Distinction between base controls and zone controls
  - Recommended polling intervals (30 seconds for controls)
  - Beta version notes and rate limiting guidance
  - API key setup instructions (Beta features in SmartDevice app)
- Added efficient polling pattern example
- Enhanced code examples with zone and control type clarifications
- Updated client module docstring with official Liebherr terminology
- Added links to official Swagger UI and Release Notes
- Enhanced example.py with better comments and polling guidance
