#!/usr/bin/env python3
"""
Test govee-local-api directly on host (not in Docker)
Run this on the actual server to test if local discovery works
"""

import asyncio
import sys

# Check if library is installed
try:
    from govee_local_api import GoveeController
    print("✓ govee-local-api is installed")
except ImportError:
    print("✗ govee-local-api NOT installed")
    print("\nInstall with: pip install govee-local-api")
    sys.exit(1)

async def test_on_host():
    """Test local discovery on the actual host machine."""

    print("=" * 70)
    print("GOVEE LOCAL DISCOVERY TEST (ON HOST)")
    print("=" * 70)
    print()

    loop = asyncio.get_event_loop()

    print("Step 1: Creating controller...")
    controller = GoveeController(
        loop=loop,
        discovery_enabled=True,
        discovery_interval=5,
        update_enabled=True
    )

    print("Step 2: Setting up UDP transport on 0.0.0.0:4002...")
    try:
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: controller,
            local_addr=('0.0.0.0', 4002),
            allow_broadcast=True
        )
        print("✓ UDP transport listening on port 4002")
        print("  (Make sure firewall allows UDP 4002)")
    except OSError as e:
        if "Address already in use" in str(e):
            print("✗ Port 4002 already in use!")
            print("  Stop any other processes using this port")
        else:
            print(f"✗ Error: {e}")
        return
    except Exception as e:
        print(f"✗ Failed: {e}")
        return

    print()
    print("Step 3: Broadcasting discovery (25 seconds)...")
    print("  Broadcast address: 239.255.255.250:4001")
    print("  Listening on: 0.0.0.0:4002")
    print()

    for i in range(5):
        await asyncio.sleep(5)
        devices = controller.devices
        print(f"  [{(i+1)*5}s] Devices found: {len(devices)}")

        if devices:
            print("\n  ✓ Device discovered!")
            break

    print()

    devices = controller.devices
    if not devices:
        print("✗ NO DEVICES FOUND")
        print("\nTroubleshooting:")
        print("  1. Verify lamp is powered ON and connected to WiFi")
        print("  2. Check you're on the same network as the lamp")
        print("  3. Check firewall: sudo firewall-cmd --list-all")
        print("  4. Try opening UDP ports:")
        print("     sudo firewall-cmd --add-port=4001/udp --add-port=4002/udp")
        print("  5. Check if lamp supports local API (some models don't)")
    else:
        print(f"✓ Found {len(devices)} device(s)!")
        print()

        for idx, device in enumerate(devices, 1):
            print(f"Device {idx}:")
            print(f"  SKU/Model: {device.sku}")
            print(f"  IP Address: {device.ip_address}")
            print(f"  Fingerprint: {device.fingerprint}")

            # Try to get more info
            if hasattr(device, 'state'):
                print(f"  State: {device.state}")

            if hasattr(device, 'device_name'):
                print(f"  Name: {device.device_name}")

            # Check capabilities
            attrs = dir(device)
            scene_methods = [a for a in attrs if 'scene' in a.lower()]
            if scene_methods:
                print(f"  Scene-related methods: {scene_methods}")

            print()

    # Cleanup
    transport.close()
    print("Transport closed.")
    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    try:
        asyncio.run(test_on_host())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
