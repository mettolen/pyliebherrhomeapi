"""Example usage of pyliebherrhomeapi."""

import asyncio
import os

from pyliebherrhomeapi import (
    AutoDoorControl,
    BioFreshPlusControl,
    HydroBreezeControl,
    IceMakerControl,
    LiebherrClient,
    TemperatureControl,
    ToggleControl,
)


async def main() -> None:
    """Run example.

    Prerequisites:
    1. Connect your appliance via the SmartDevice app
    2. Get API key from app Settings -> Beta features -> HomeAPI
    3. Set LIEBHERR_API_KEY environment variable with your API key

    Note: The API key can only be copied once from the app!
    """
    # Get API key from environment variable
    api_key = os.getenv("LIEBHERR_API_KEY")
    if not api_key:
        print("Please set LIEBHERR_API_KEY environment variable")
        print("\nTo get your API key:")
        print("1. Open SmartDevice app")
        print("2. Go to Settings -> Beta features")
        print("3. Activate HomeAPI")
        print("4. Copy the API key (can only be copied once!)")
        return

    async with LiebherrClient(api_key=api_key) as client:
        # Get all devices (only connected devices are returned)
        print("Fetching devices...")
        print("Note: Only appliances connected to WiFi will appear\n")
        devices = await client.get_devices()
        print(f"Found {len(devices)} device(s):")

        for device in devices:
            print(f"\n{'=' * 60}")
            print(f"Device: {device.nickname or 'Unnamed'}")
            print(f"  ID (Serial Number): {device.device_id}")
            print(f"  Type: {device.device_type}")
            print(f"  Model: {device.device_name}")

            # Get all controls for this device
            # Recommended: Use this single call for polling (every ~30 seconds)
            print("\n  Controls:")
            controls = await client.get_controls(device.device_id)

            for control in controls:
                print(f"    - {control.name} (type: {control.type})")

                # Type-specific handling
                match control:
                    case TemperatureControl():
                        print(f"      Zone: {control.zone_id} (0=top, ascending)")
                        print(f"      Current: {control.value} {control.unit}")
                        print(f"      Target: {control.target} {control.unit}")
                        print(f"      Range: {control.min} to {control.max}")
                    case ToggleControl():
                        if control.zone_id is not None:
                            print(f"      Zone: {control.zone_id} (zone control)")
                        else:
                            print("      Type: Base control (applies to whole device)")
                        print(f"      Value: {control.value}")
                    case AutoDoorControl():
                        print(f"      Zone: {control.zone_id}")
                        print(f"      State: {control.value}")
                    case IceMakerControl():
                        print(f"      Zone: {control.zone_id}")
                        print(f"      Mode: {control.ice_maker_mode}")
                        print(f"      Has Max Ice: {control.has_max_ice}")
                    case HydroBreezeControl():
                        print(f"      Zone: {control.zone_id}")
                        print(f"      Current Mode: {control.current_mode}")
                    case BioFreshPlusControl():
                        print(f"      Zone: {control.zone_id}")
                        print(f"      Current Mode: {control.current_mode}")
                        print(f"      Supported Modes: {control.supported_modes}")

            # Examples (commented out to prevent accidental changes):

            # Set temperature for zone 0 (top zone)
            # print("\n  Setting temperature to 4°C for zone 0 (top zone)...")
            # await client.set_temperature(
            #     device_id=device.device_id,
            #     zone_id=0,  # Top zone
            #     target=4,
            #     unit=TemperatureUnit.CELSIUS
            # )

            # Enable SuperCool for zone 0 (zone control - requires zone_id)
            # print("  Enabling SuperCool for zone 0...")
            # await client.set_supercool(
            #     device_id=device.device_id,
            #     zone_id=0,
            #     value=True
            # )

            # Enable Party Mode (base control - no zone_id needed)
            # print("  Enabling Party Mode (applies to whole device)...")
            # await client.set_party_mode(
            #     device_id=device.device_id,
            #     value=True
            # )

            print(f"{'=' * 60}\n")

        # Polling example (commented out)
        # print("\nRecommended polling pattern:")
        # print("Poll every 30 seconds using get_device_state() for efficiency")
        # while True:
        #     for device in devices:
        #         state = await client.get_device_state(device.device_id)
        #         print(f"{device.nickname}: {len(state.controls)} controls")
        #     await asyncio.sleep(30)  # Wait 30 seconds (recommended interval)


if __name__ == "__main__":
    asyncio.run(main())
