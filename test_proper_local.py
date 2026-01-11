#!/usr/bin/env python3
"""
Test govee-local-api with proper protocol setup
"""

import asyncio
from govee_local_api import GoveeController

async def test_proper_setup():
    """Test with proper asyncio protocol setup."""

    print("=" * 70)
    print("TESTING GOVEE LOCAL API (PROPER SETUP)")
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

    print("✓ Controller created")
    print()

    # Create the datagram endpoint (this is what's missing!)
    print("Step 2: Setting up UDP transport...")
    try:
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: controller,
            local_addr=('0.0.0.0', 4002),  # Listening port from help
            allow_broadcast=True
        )
        print("✓ UDP transport created and listening on port 4002")
    except Exception as e:
        print(f"✗ Failed to create transport: {e}")
        print("\nThis might be a permission or network issue.")
        return

    print()
    print("Step 3: Waiting for device discovery (20 seconds)...")
    print("(Controller will broadcast discovery messages...)")
    await asyncio.sleep(20)

    # Check discovered devices
    devices = controller.devices
    print(f"\n✓ Discovery complete. Found {len(devices)} device(s)")
    print()

    if not devices:
        print("✗ No devices discovered!")
        print("\nPossible issues:")
        print("  1. Lamp is not powered on")
        print("  2. Lamp is on a different network/VLAN")
        print("  3. Firewall blocking UDP port 4002")
        print("  4. Multicast not working in Docker")
    else:
        # List all discovered devices
        for idx, device in enumerate(devices, 1):
            print(f"Device {idx}:")
            print(f"  SKU: {device.sku}")
            print(f"  IP: {device.ip_address}")
            print(f"  Fingerprint: {device.fingerprint}")

            if hasattr(device, 'state'):
                print(f"  State: {device.state}")

            if device.sku == "H6078":
                print(f"  ✓ This is your Torch Floor Lamp!")

                # Test scene activation
                print(f"\n  Testing scene activation...")
                try:
                    # According to govee-local-api, scenes might be set differently
                    # Let's try setting brightness first to test the connection
                    print(f"  Testing connection with brightness change...")
                    controller.set_brightness(device, 100)
                    await asyncio.sleep(1)

                    print(f"  ✓ Brightness command sent")

                except Exception as e:
                    print(f"  ✗ Error: {e}")

            print()

    # Cleanup
    print("Step 4: Cleaning up...")
    transport.close()
    print("✓ Transport closed")

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_proper_setup())
