# pyliebherrhomeapi

Python library for the [Liebherr SmartDevice Home API](https://developer.liebherr.com/apis/smartdevice-homeapi/).

## Features

- 🔌 **Async/await support** using asyncio with comprehensive error handling
- 🌡️ **Temperature control** for all zones in your Liebherr appliances
- ❄️ **SuperFrost/SuperCool** control for quick cooling/freezing
- 🎉 **Special modes** (Party Mode, Night Mode, Presentation Light)
- 🧊 **Ice maker control** with Max Ice support
- 💧 **HydroBreeze and BioFreshPlus** mode management
- 🚪 **Auto door** control for supported appliances
- 📱 **Device management** - list and query all connected appliances
- 🛡️ **Type hints** for better IDE support and development experience
- ✅ **Input validation** with proper error handling
- 📊 **Comprehensive data models** for all control types
- 🧪 **100% test coverage** ensuring reliability and code quality

## Requirements

- Python 3.11+ (matches the typed codebase and test matrix)
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

### Polling Recommendations

⚠️ **Beta Version Notice**: The API currently doesn't push updates, so endpoints need to be polled regularly.

**Recommended polling intervals:**

- **Controls**: Poll every 30 seconds using `/v1/devices/{deviceId}/controls` to get all states in one call
- **Device list**: Poll manually only when appliances are added/removed or nicknames change
- **Rate limits**: Be mindful of API call limits. Avoid too many calls at once as there are restrictions for security and performance

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
await client.set_supercool(
    device_id="12.345.678.9",
    zone_id=0,
    value=True
)

# Enable SuperFrost for zone 1
await client.set_superfrost(
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

### Efficient Polling Pattern

```python
import asyncio
from pyliebherrhomeapi import LiebherrClient

async def poll_device_state(client: LiebherrClient, device_id: str):
    """Poll device state every 30 seconds (recommended interval)."""
    while True:
        try:
            # Get all controls in a single API call
            device_state = await client.get_device_state(device_id)

            # Process the controls
            for control in device_state.controls:
                print(f"{control.name}: {control}")

            # Wait 30 seconds before next poll (recommended by Liebherr)
            await asyncio.sleep(30)

        except Exception as e:
            print(f"Error polling device: {e}")
            await asyncio.sleep(30)

async def main():
    async with LiebherrClient(api_key="your-api-key") as client:
        devices = await client.get_devices()
        if devices:
            await poll_device_state(client, devices[0].device_id)
```

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

This client library is generated based on the official `openapi.json` specification downloaded from the Liebherr Developer Portal, which reflects the latest API state. When Liebherr updates their API and releases a new version of the OpenAPI specification, this client library will be updated accordingly to maintain compatibility and support new features.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.
