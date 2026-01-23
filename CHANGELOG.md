# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
