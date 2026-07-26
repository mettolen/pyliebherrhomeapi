"""Example usage of pyliebherrhomeapi."""

import asyncio
import logging
import os

import aiohttp

from pyliebherrhomeapi import (
    AutoDoorControl,
    BioFreshPlusControl,
    HydroBreezeControl,
    IceMakerControl,
    LiebherrClient,
    TemperatureControl,
    ToggleControl,
)
from pyliebherrhomeapi.const import API_BASE_URL, API_VERSION


async def dump_raw_sse(api_key: str, device_id: str, *, timeout: float = 60) -> None:
    """Open the SSE endpoint directly and log raw headers and content.

    This bypasses the parsed ``stream_controls()`` helper so you can inspect
    the exact response status, response headers, and raw event bytes the
    server sends. Useful when debugging connection or parsing issues.

    Args:
        api_key: API key for authentication.
        device_id: The device ID (serial number) to subscribe to.
        timeout: How long (seconds) to keep reading the raw stream.

    """
    url = f"{API_BASE_URL}/{API_VERSION}/sse/devices/{device_id}/controls"
    headers = {
        "api-key": api_key,
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache",
    }
    print(f"\n[RAW SSE] GET {url}")
    print("[RAW SSE] Request headers:")
    for key, value in headers.items():
        # Redact the API key so it does not leak into logs.
        shown = "***" if key.lower() == "api-key" else value
        print(f"    {key}: {shown}")

    stream_timeout = aiohttp.ClientTimeout(total=None, sock_read=None, sock_connect=10)
    async with (
        aiohttp.ClientSession() as session,
        session.get(url, headers=headers, timeout=stream_timeout) as response,
    ):
        print(f"[RAW SSE] Status: {response.status} {response.reason}")
        print("[RAW SSE] Response headers:")
        for key, value in response.headers.items():
            print(f"    {key}: {value}")

        print("[RAW SSE] Raw stream content (repr per line):")
        try:
            async with asyncio.timeout(timeout):
                async for raw_line in response.content:
                    decoded = raw_line.decode("utf-8", errors="replace")
                    print(f"    {decoded!r}")
        except TimeoutError:
            print("[RAW SSE] Raw stream window elapsed.")


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
            # await client.set_super_cool(
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

        # Realtime updates via Server-Sent Events.
        #
        # This server closes the SSE connection after delivering a snapshot
        # (observed: one ``event:device-update`` then EOF after ~15s), so a
        # single stream_controls() call yields one event and then ends. Use
        # stream_controls_forever(), which transparently reconnects with
        # backoff so you keep receiving updates. Each event contains the full
        # set of controls for this server; if a server sends deltas instead,
        # merge each update into your cached state rather than replacing it.
        #
        # The example below subscribes to the first device for up to 600
        # seconds, printing each update as it arrives. Use asyncio.timeout()
        # or break out of the loop based on your own condition to stop.
        #
        if devices:
            target = devices[0]

            # Raw SSE diagnostics: print the exact response status, headers,
            # and raw stream bytes before consuming the parsed stream. Handy
            # when the parsed stream misbehaves and you need to see what the
            # server actually sent.
            print(f"\n[RAW SSE] Inspecting raw stream for {target.nickname}...")
            await dump_raw_sse(api_key, target.device_id, timeout=600)

            print(f"\nSubscribing to realtime updates for {target.nickname}...")
            try:
                async with asyncio.timeout(600):
                    async for controls in client.stream_controls_forever(
                        target.device_id
                    ):
                        print(f"  Update: {len(controls)} control(s)")
                        for control in controls:
                            print(f"    - {control.name}: {control!r}")
            except TimeoutError:
                print("  Stream window elapsed.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(main())
