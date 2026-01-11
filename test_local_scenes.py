#!/usr/bin/env python3
"""
Test local API scene discovery
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

async def test_local_api():
    """Test the local API for scene support."""

    print("=" * 70)
    print("TESTING GOVEE LOCAL API")
    print("=" * 70)
    print()

    # Check if library is available
    try:
        from govee_local_api import GoveeController
        print("✓ govee-local-api library is installed")
    except ImportError as e:
        print(f"✗ govee-local-api library NOT installed: {e}")
        print("\nInstall with: pip install govee-local-api")
        return

    print()
    print("Step 1: Creating controller and discovering devices...")

    try:
        controller = GoveeController()
        print(f"✓ Controller created: {controller}")

        # Discover devices on local network
        print("\nStep 2: Discovering devices on local network...")
        print("(This may take 5-10 seconds...)")

        await controller.discover()

        devices = controller.devices
        print(f"\n✓ Discovery complete. Found {len(devices)} device(s)")

        if not devices:
            print("\n✗ No devices found on local network!")
            print("\nPossible reasons:")
            print("  1. Lamp is not on the same network")
            print("  2. Lamp is turned off")
            print("  3. Firewall blocking UDP discovery")
            print("  4. Docker container network mode not set to 'host'")
            return

        # List discovered devices
        print("\nDiscovered devices:")
        for idx, device in enumerate(devices, 1):
            print(f"\n  Device {idx}:")
            print(f"    Type: {type(device)}")
            print(f"    Attributes: {dir(device)}")

            # Try to get device info
            if hasattr(device, 'device_id'):
                print(f"    ID: {device.device_id}")
            if hasattr(device, 'ip'):
                print(f"    IP: {device.ip}")
            if hasattr(device, 'model'):
                print(f"    Model: {device.model}")
            if hasattr(device, 'device_name'):
                print(f"    Name: {device.device_name}")

            # Check for scene support
            print(f"\n    Scene-related attributes:")
            if hasattr(device, 'scenes'):
                print(f"      scenes: {device.scenes}")
            if hasattr(device, 'set_scene'):
                print(f"      ✓ Has set_scene method")
            if hasattr(device, 'set_light_option'):
                print(f"      ✓ Has set_light_option method")

            # Try to get state
            if hasattr(device, 'get_state'):
                try:
                    state = await device.get_state()
                    print(f"    State: {state}")
                except Exception as e:
                    print(f"    State error: {e}")

    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_local_api())
