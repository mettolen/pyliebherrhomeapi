# pyliebherrhomeapi

[![CI](https://github.com/mettolen/pyliebherrhomeapi/actions/workflows/ci.yml/badge.svg)](https://github.com/mettolen/pyliebherrhomeapi/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/mettolen/pyliebherrhomeapi/branch/main/graph/badge.svg)](https://codecov.io/gh/mettolen/pyliebherrhomeapi)
[![PyPI version](https://badge.fury.io/py/pyliebherrhomeapi.svg)](https://badge.fury.io/py/pyliebherrhomeapi)
[![PyPI Downloads](https://img.shields.io/pypi/dm/pyliebherrhomeapi.svg)](https://pypi.org/project/pyliebherrhomeapi/)
[![Python versions](https://img.shields.io/pypi/pyversions/pyliebherrhomeapi.svg)](https://pypi.org/project/pyliebherrhomeapi/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python library for the [Liebherr SmartDevice Home API](https://developer.liebherr.com/apis/smartdevice-homeapi/).

---

This library is used by the [Liebherr](https://www.home-assistant.io/integrations/liebherr) Home Assistant integration.

<a href="https://www.home-assistant.io/integrations/liebherr/" target="_blank"><img alt="Dynamic Regex Badge" src="https://img.shields.io/badge/dynamic/regex?url=https%3A%2F%2Fwww.home-assistant.io%2Fintegrations%2Fliebherr%2F&search=(%5B%5Cd%2C%5D%2B)%5Cs*%3C%2Fa%3E%5Cs*active%20installations&replace=%241&style=for-the-badge&logo=homeassistant&label=Active%20installations&labelColor=%23f2f4f9&color=%2346bdf4"></a> <a href="https://www.home-assistant.io/docs/quality_scale/" target="_blank"><img alt="Dynamic Regex Badge" src="https://img.shields.io/badge/dynamic/regex?url=https%3A%2F%2Fwww.home-assistant.io%2Fintegrations%2Fliebherr%2F&search=%3Ca%20href%3D'%5B%5E'%5D*quality_scale%5B%5E'%5D*'%3E(%5B%5E%3C%5D%2B%3F)%20quality%3C%2Fa%3E&replace=%241&style=for-the-badge&logo=homeassistant&label=Quality%20scale&labelColor=%23f2f4f9&color=%2346bdf4"></a> <a href="https://my.home-assistant.io/redirect/config_flow_start?domain=liebherr" target="_blank"><img alt="Static Badge" src="https://img.shields.io/badge/Liebherr-i?style=for-the-badge&logo=homeassistant&label=Add%20integration&labelColor=%23f2f4f9&color=%2346bdf4"></a>

## Features

- 🔌 **Async/await support** using asyncio with comprehensive error handling
- 🌡️ **Temperature control** for all zones in your Liebherr appliances
- ❄️ **SuperFrost/SuperCool** control for quick cooling/freezing
- 🎉 **Special modes** (Party Mode, Night Mode, Presentation Light)
- 🧊 **Ice maker control** with Max Ice support
- 💧 **HydroBreeze and BioFreshPlus** mode management
- 🚪 **Auto door** control for supported appliances
- 📱 **Device management** - list and query all connected appliances
- 📡 **Realtime updates via Server-Sent Events (SSE)** _(beta)_ - subscribe to live control state changes
- 🛡️ **Type hints** for better IDE support and development experience
- ✅ **Input validation** with proper error handling
- 📊 **Comprehensive data models** for all control types
- 📝 **Configurable logging** with privacy-focused debug output
- 🧪 **100% test coverage** ensuring reliability and code quality

## Requirements

- Python 3.12+ (matches the typed codebase and test matrix)
- Asyncio environment with `aiohttp` (installed automatically)
- Network access to `https://home-api.smartdevice.liebherr.com`

## Installation

- From PyPI (when published):

  ```bash
  pip install pyliebherrhomeapi
  ```

- From source (current repository):

  ```bash
  pip install .
  ```

## Prerequisites

Before using this library, you need:

1. **Connect your appliance**: Connect your Liebherr appliance via the [SmartDevice app](https://smartdevice.onelink.me/OrY5/8neax8lp) to your home WiFi network
   - [Download the SmartDevice app](https://smartdevice.onelink.me/OrY5/8neax8lp)
   - [Instructions for connecting your appliance](https://go.liebherr.com/cb2ct1)

2. **Get your API Key** (via the SmartDevice app):
   - Go to **Settings** in the SmartDevice app
   - Select **"Beta features"**
   - Activate the **HomeAPI**
   - Copy the API Key (⚠️ **Important**: The API key can only be copied once. Once you leave the screen, it cannot be copied again. If you forget your key, you'll need to create a new one via the app)

3. **Connected appliances only**: Only appliances that are connected to the internet via the SmartDevice app can be accessed through the HomeAPI. Appliances that are only registered but not connected will not appear

## Quick Start

```python
import asyncio
from pyliebherrhomeapi import (
    LiebherrClient,
    TemperatureUnit,
    IceMakerMode,
)

async def main():
    # Create client with your API key
    async with LiebherrClient(api_key="your-api-key-here") as client:
        # Get all devices (only connected devices are returned)
        devices = await client.get_devices()
        print(f"Found {len(devices)} device(s)")

        for device in devices:
            # device_id is the serial number of the appliance
            print(f"Device: {device.nickname} ({device.device_id})")
            print(f"  Type: {device.device_type}")
            print(f"  Model: {device.device_name}")

            # Get all controls for this device
            controls = await client.get_controls(device.device_id)
            print(f"  Controls: {len(controls)}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Important Notes

### Device Zones

- Each device has at least one zone (cooling zone, freezing zone, etc.)
- **Zone numbering**: The top zone is zone 0, zone numbers ascend from top to bottom
- Zone controls (like temperature, SuperFrost, SuperCool) always require a `zone_id`
- Base controls (like Party Mode, Night Mode) apply to the whole device and don't need a zone

### Polling and Device Refresh

The REST endpoints do not push updates. Control updates can be received through [Realtime Updates (SSE)](#realtime-updates-sse-beta), but device list and metadata changes still require an explicit REST request.

- **Controls**: Prefer SSE for realtime updates. If polling is required, use `/v1/devices/{deviceId}/controls` to get all control states in one call
- **Device list**: Call `get_devices()` (`GET /v1/devices`) again to discover added or removed appliances and appliance nickname changes. These changes are not included in SSE events
- **Rate limits**: Avoid excessive polling. The API restricts the number of calls for security and performance reasons

### Control Types

**Base Controls** (apply to entire device, no `zone_id` needed):

- Party Mode
- Night Mode

**Zone Controls** (require `zone_id`, even if device has only one zone):

- Temperature
- SuperFrost
- SuperCool
- Ice Maker
- HydroBreeze
- BioFreshPlus
- Auto Door

## Usage Examples

### Temperature Control

```python
from pyliebherrhomeapi import LiebherrClient, TemperatureUnit

async with LiebherrClient(api_key="your-api-key") as client:
    # Set temperature for zone 0 (top zone) to 4°C
    await client.set_temperature(
        device_id="12.345.678.9",
        zone_id=0,  # Zone 0 is the top zone
        target=4,
        unit=TemperatureUnit.CELSIUS
    )

    # Get temperature control info
    controls = await client.get_control(
        device_id="12.345.678.9",
        control_name="temperature",
        zone_id=0
    )
```

### SuperCool and SuperFrost

```python
# Enable SuperCool for zone 0
await client.set_super_cool(
    device_id="12.345.678.9",
    zone_id=0,
    value=True
)

# Enable SuperFrost for zone 1
await client.set_super_frost(
    device_id="12.345.678.9",
    zone_id=1,
    value=True
)
```

### Special Modes

```python
# Enable Party Mode
await client.set_party_mode(
    device_id="12.345.678.9",
    value=True
)

# Enable Night Mode
await client.set_night_mode(
    device_id="12.345.678.9",
    value=True
)

# Set presentation light intensity (0-5)
await client.set_presentation_light(
    device_id="12.345.678.9",
    target=3
)
```

### Ice Maker Control

```python
from pyliebherrhomeapi import IceMakerMode

# Turn on ice maker
await client.set_ice_maker(
    device_id="12.345.678.9",
    zone_id=0,
    mode=IceMakerMode.ON
)

# Enable Max Ice mode
await client.set_ice_maker(
    device_id="12.345.678.9",
    zone_id=0,
    mode=IceMakerMode.MAX_ICE
)
```

### HydroBreeze Control

```python
from pyliebherrhomeapi import HydroBreezeMode

# Set HydroBreeze to medium
await client.set_hydro_breeze(
    device_id="12.345.678.9",
    zone_id=0,
    mode=HydroBreezeMode.MEDIUM
)
```

### BioFreshPlus Control

```python
from pyliebherrhomeapi import BioFreshPlusMode

# Set BioFreshPlus mode
await client.set_bio_fresh_plus(
    device_id="12.345.678.9",
    zone_id=0,
    mode=BioFreshPlusMode.ZERO_ZERO
)
```

### Auto Door Control

```python
# Open the door
await client.trigger_auto_door(
    device_id="12.345.678.9",
    zone_id=0,
    value=True  # True to open, False to close
)
```

### Query Device Controls

```python
# Get all controls (recommended for polling - gets all states in one call)
all_controls = await client.get_controls(device_id="12.345.678.9")

# Get specific control by name
temp_controls = await client.get_control(
    device_id="12.345.678.9",
    control_name="temperature"
)

# Get control for specific zone
zone_temp = await client.get_control(
    device_id="12.345.678.9",
    control_name="temperature",
    zone_id=0  # Top zone
)
```

### Polling Fallback Pattern

```python
import asyncio
from pyliebherrhomeapi import LiebherrClient

async def poll_controls(
    client: LiebherrClient, device_id: str, interval: float
) -> None:
    """Poll all device controls at a caller-selected interval."""
    while True:
        try:
            # Get all controls in a single API call
            controls = await client.get_controls(device_id)

            # Process the controls
            for control in controls:
                print(f"{control.name}: {control}")

            await asyncio.sleep(interval)

        except Exception as e:
            print(f"Error polling device: {e}")
            await asyncio.sleep(interval)

async def main():
    async with LiebherrClient(api_key="your-api-key") as client:
        devices = await client.get_devices()
        if devices:
            # This is an example interval, not an API recommendation.
            await poll_controls(client, devices[0].device_id, interval=60)
```

### Realtime Updates (SSE) _(beta)_

⚠️ **Beta**: SSE support in this library is beta. The endpoint and its control-list payload are documented in the official HomeAPI documentation and OpenAPI specification.

The client subscribes to `/v1/sse/devices/{deviceId}/controls` and yields a list of parsed controls on each update. The server keeps the connection open and sends an empty keep-alive about every 30 seconds. SSE events only contain appliance control updates; they do not report added or removed appliances or appliance nickname changes. Call `get_devices()` (`GET /v1/devices`) explicitly to refresh that information. Malformed events are logged and skipped.

#### Recommended: `stream_controls_forever()`

Reconnects automatically with exponential backoff + jitter on recoverable errors (drops, timeouts, 5xx) and clean closures. Non-recoverable errors (`LiebherrAuthenticationError`, `LiebherrNotFoundError`, `LiebherrPreconditionFailedError`) are re-raised. Optional non-blocking `on_connect` / `on_disconnect` callbacks let you track availability (e.g. in a Home Assistant integration); an exception in a callback is logged and does not break the stream.

```python
import asyncio
from pyliebherrhomeapi import LiebherrClient

async def main() -> None:
    async with LiebherrClient(api_key="your-api-key") as client:
        devices = await client.get_devices()
        if not devices:
            return

        async for controls in client.stream_controls_forever(
            devices[0].device_id,
            on_connect=lambda: print("SSE connected"),
            on_disconnect=lambda: print("SSE disconnected, reconnecting..."),
        ):
            for control in controls:
                zone_id = getattr(control, "zone_id", None)
                print(f"Update: {control.name} (zone={zone_id}) -> {control}")

asyncio.run(main())
```

#### Low-level: `stream_controls()`

Opens a single connection and yields events until it ends. Use it only if you want to manage reconnection yourself; otherwise prefer `stream_controls_forever()`.

**SSE vs. polling:** prefer SSE for low-latency, self-healing subscriptions (e.g. a long-running Home Assistant integration); prefer polling for simple scripts or environments where long-lived connections are problematic.

## Logging

The library uses Python's standard `logging` module for diagnostics. By default, it uses a `NullHandler`, so no logs are emitted unless you configure logging in your application.

### Enable Debug Logging

```python
import logging

# Enable debug logging for the library
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Or configure just for pyliebherrhomeapi
logger = logging.getLogger('pyliebherrhomeapi')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
```

### Log Levels

- **DEBUG**: Detailed information about API requests, responses, and session lifecycle
- **INFO**: General information about operations (currently not used)
- **WARNING**: HTTP errors and connection issues
- **ERROR**: Severe errors like server failures

### Privacy

Device IDs are automatically masked in debug logs (showing only last 4 characters) to protect sensitive information.

## Error Handling

```python
from pyliebherrhomeapi import (
    LiebherrClient,
    LiebherrAuthenticationError,
    LiebherrBadRequestError,
    LiebherrNotFoundError,
    LiebherrPreconditionFailedError,
    LiebherrUnsupportedError,
    LiebherrConnectionError,
    LiebherrTimeoutError,
)

async with LiebherrClient(api_key="your-api-key") as client:
    try:
        await client.set_temperature(
            device_id="12.345.678.9",
            zone_id=0,
            target=4
        )
    except LiebherrAuthenticationError:
        print("Invalid API key")
    except LiebherrBadRequestError as e:
        print(f"Invalid request: {e}")
    except LiebherrNotFoundError:
        print("Device not reachable")
    except LiebherrPreconditionFailedError:
        print("Device not onboarded to your household")
    except LiebherrUnsupportedError:
        print("Feature not supported on this device")
    except (LiebherrConnectionError, LiebherrTimeoutError) as e:
        print(f"Connection error: {e}")
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/mettolen/pyliebherrhomeapi.git
cd pyliebherrhomeapi

# Install development dependencies
pip install -e ".[dev]"
```

### Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=pyliebherrhomeapi --cov-report=html
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy src
```

## API Documentation

For detailed API documentation, visit:

- [SmartDevice HomeAPI Overview](https://developer.liebherr.com/apis/smartdevice-homeapi/)
- [Swagger UI Documentation](https://developer.liebherr.com/apis/smartdevice-homeapi/swagger-ui/)
- [Release Notes](https://developer.liebherr.com/apis/smartdevice-homeapi/releasenotes/)

**API Base URL**: `https://home-api.smartdevice.liebherr.com`

## Implementation Notes

This handwritten client is implemented against the checked-in official `openapi.json` specification and the HomeAPI documentation from the Liebherr Developer Portal.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.
