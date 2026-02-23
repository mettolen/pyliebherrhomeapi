# GitHub Copilot Instructions for pyliebherrhomeapi

This repository contains `pyliebherrhomeapi`, a Python library for the [Liebherr SmartDevice Home API](https://developer.liebherr.com/apis/smartdevice-homeapi/). It is used by the [Liebherr Home Assistant integration](https://www.home-assistant.io/integrations/liebherr).

## Project Overview

- **Purpose**: Async Python client for Liebherr smart appliances
- **Protocol**: REST API over HTTPS (via aiohttp library)
- **Python**: 3.11+
- **Structure**: src layout (`src/pyliebherrhomeapi/`)

## Code Standards

### Python Requirements

- **Compatibility**: Python 3.11+
- **Type hints**: Required for all functions, methods, and variables (strict mypy)
- **Async/await**: All I/O operations must be async
- **Docstrings**: Required for all public classes and methods

### Code Style

- **Formatter**: Ruff (line length 88)
- **Linter**: Ruff + mypy (strict mode)
- **Language**: American English for all code, comments, and documentation

### Type Hints

```python
# ✅ Good - comprehensive type hints
async def set_temperature(
    self, device_id: str, zone_id: int, target: int, unit: TemperatureUnit
) -> None:
    """Set target temperature for a zone."""

# ✅ Good - Optional fields use | None
device_type: DeviceType | str | None
```

### Docstrings

```python
# ✅ Good - concise module header
"""Python library for Liebherr Home API."""

# ✅ Good - method docstring with raises
async def get_devices(self) -> list[Device]:
    """Get all devices associated with the account.

    Raises:
        LiebherrConnectionError: If connection fails.
        LiebherrAuthenticationError: If API key is invalid.
    """
```

## Architecture

### File Structure

```
src/pyliebherrhomeapi/
├── __init__.py      # Public API exports
├── client.py        # LiebherrClient - main async REST client
├── const.py         # Constants (API URLs, control names, mode values)
├── exceptions.py    # Exception hierarchy
├── models.py        # Enums, dataclasses, and control models
└── py.typed         # PEP-561 marker
```

### Exception Hierarchy

All exceptions inherit from `LiebherrError`:

- `LiebherrConnectionError` - Connection failures
- `LiebherrTimeoutError` - Request timeouts
- `LiebherrAuthenticationError` - Invalid API key (401)
- `LiebherrBadRequestError` - Invalid request data (400)
- `LiebherrNotFoundError` - Device not reachable (404)
- `LiebherrPreconditionFailedError` - Device not onboarded (412)
- `LiebherrUnsupportedError` - Feature not supported (422)
- `LiebherrServerError` - Server error (500)

### Client Patterns

```python
# ✅ Preferred - context manager
async with LiebherrClient(api_key="your-api-key") as client:
    devices = await client.get_devices()

# ✅ Also supported - external session (for Home Assistant)
client = LiebherrClient(api_key="key", session=existing_session)

# Also supported - manual lifecycle
client = LiebherrClient(api_key="key")
devices = await client.get_devices()
await client.close()
```

### Session Management

- The client can accept an external `aiohttp.ClientSession` (for Home Assistant integration)
- If no session is provided, the client creates and manages its own
- The `_own_session` flag tracks whether the client owns the session
- `close()` only closes sessions the client created

### Data Models

**Enums** (all use `StrEnum` with lowercase values):

- `DeviceType` - `fridge`, `freezer`, `combi`, `wine`
- `IceMakerMode` - `off`, `on`, `max_ice`
- `HydroBreezeMode` - `off`, `low`, `medium`, `high`
- `BioFreshPlusMode` - `zero_zero`, `zero_minus_two`, `minus_two_minus_two`, `minus_two_zero`
- `DoorState` - `closed`, `open`, `moving`
- `TemperatureUnit` - `°C`, `°F`
- `ControlType` - control type discriminators

**Controls** (dataclasses):

- `TemperatureControl` - temperature with target, min, max, unit
- `ToggleControl` - on/off controls (SuperFrost, SuperCool, Party Mode, etc.)
- `IceMakerControl` - ice maker with mode and max ice support
- `HydroBreezeControl` - HydroBreeze with mode selection
- `BioFreshPlusControl` - BioFreshPlus with supported modes
- `AutoDoorControl` - automatic door with door state

**Important**: Enum values are lowercase for Home Assistant translation key compatibility. The `_coerce_enum()` helper handles case-insensitive matching from the API (which returns UPPERCASE).

### API Wire Format

The Liebherr API sends and expects UPPERCASE enum values. The library:

- **Receiving**: `_coerce_enum()` tries both original and `.lower()` variants
- **Sending**: Client setter methods use `.value.upper()` before sending to the API

### Device Zones

- Each device has at least one zone (cooling, freezing, etc.)
- Zone 0 is the top zone; numbers ascend from top to bottom
- Zone controls (temperature, SuperFrost, etc.) require a `zone_id`
- Base controls (Party Mode, Night Mode) apply to the whole device

## Development Commands

### Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pyliebherrhomeapi --cov-report=term-missing

# Run specific test file
pytest tests/test_client.py -v
```

### Linting

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Ruff linting
ruff check src/pyliebherrhomeapi

# Ruff formatting
ruff format src/pyliebherrhomeapi

# Type checking
mypy src/pyliebherrhomeapi --strict
```

## Best Practices

### ✅ Do

- Use async/await for all HTTP operations
- Wrap aiohttp exceptions in pyliebherrhomeapi exceptions
- Use constants from `const.py` for API paths, control names, and limits
- Use `StrEnum` for all string enumerations
- Add type hints to all function signatures
- Validate inputs before sending to the API
- Write pytest tests for new functionality
- Use `pytest-asyncio` for async test functions
- Process data outside try blocks
- Keep enum values lowercase (for HA translation key compatibility)

### ❌ Don't

- Block the event loop with synchronous I/O
- Expose aiohttp types in the public API
- Use bare `except:` clauses
- Hardcode API paths or control names outside `const.py`
- Skip type annotations
- Close sessions that were provided externally
- Use `(str, Enum)` — use `StrEnum` instead

### Error Handling Pattern

```python
# ✅ Good - wrap library exceptions
try:
    async with session.request(method, url, headers=headers) as response:
        ...
except TimeoutError as err:
    raise LiebherrTimeoutError(f"Timeout connecting to API") from err
except aiohttp.ClientError as err:
    raise LiebherrConnectionError(f"Error connecting to API") from err

# Process data outside try block
data = await response.json()
return Device.from_dict(data)
```

### Enum Handling Pattern

```python
# ✅ Good - case-insensitive enum parsing
def _coerce_enum(enum_cls: type[_EnumT], value: str | None) -> _EnumT | str | None:
    if value is None:
        return None
    for variant in (value, value.lower()):
        try:
            return enum_cls(variant)
        except ValueError:
            pass
    return value  # Return raw value for unknown API values

# ✅ Good - uppercase for API wire format
await self._request(
    "POST",
    f"devices/{device_id}/controls/{CONTROL_ICE_MAKER}",
    json_data={"zoneId": zone_id, "iceMakerMode": mode.value.upper()},
)
```

### Async Context Manager

```python
# ✅ Good - proper cleanup
async def __aenter__(self) -> LiebherrClient:
    """Enter async context."""
    return self

async def __aexit__(self, *args: object) -> None:
    """Exit async context."""
    await self.close()
```

## Testing Guidelines

- Use `pytest-asyncio` with `asyncio_mode = "auto"`
- Mock `aiohttp.ClientSession` for unit tests
- Test both success and error paths
- Use fixtures for common test setup
- Timeout: 10 seconds per test
- Coverage: minimum 100%

### Test Example

```python
@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    return AsyncMock(spec=aiohttp.ClientSession)

async def test_get_devices_success(client, mock_response, sample_devices_data):
    """Test successful device retrieval."""
    mock_response.status = 200
    mock_response.json.return_value = sample_devices_data

    devices = await client.get_devices()

    assert len(devices) == 1
    assert devices[0].device_type == DeviceType.COMBI
```

## Constants Reference

Key constants from `const.py`:

| Constant                     | Value               | Description                |
| ---------------------------- | ------------------- | -------------------------- |
| `API_BASE_URL`               | `https://...`       | Liebherr Home API base URL |
| `DEFAULT_TIMEOUT`            | 10                  | Request timeout (seconds)  |
| `CONTROL_TEMPERATURE`        | `temperature`       | Temperature control name   |
| `CONTROL_SUPER_FROST`        | `superfrost`        | SuperFrost control name    |
| `CONTROL_SUPER_COOL`         | `supercool`         | SuperCool control name     |
| `CONTROL_ICE_MAKER`          | `icemaker`          | Ice maker control name     |
| `CONTROL_HYDRO_BREEZE`       | `hydrobreeze`       | HydroBreeze control name   |
| `CONTROL_BIO_FRESH_PLUS`     | `biofreshplus`      | BioFreshPlus control name  |
| `CONTROL_AUTO_DOOR`          | `autodoor`          | Auto door control name     |
| `CONTROL_PARTY_MODE`         | `partymode`         | Party mode control name    |
| `CONTROL_NIGHT_MODE`         | `nightmode`         | Night mode control name    |
| `CONTROL_PRESENTATION_LIGHT` | `presentationlight` | Presentation light name    |
