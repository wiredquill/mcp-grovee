#!/usr/bin/env python3
"""
Test govee-local-api with the correct API
"""

import asyncio
import json
from govee_local_api import GoveeController

async def test_correct_api():
    """Test with the actual govee-local-api methods."""

    print("=" * 70)
    print("TESTING GOVEE LOCAL API (CORRECT METHOD)")
    print("=" * 70)
    print()

    # Create controller with discovery ENABLED
    print("Step 1: Creating controller with discovery enabled...")
    controller = GoveeController(
        discovery_enabled=True,  # Enable automatic discovery
        discovery_interval=10,   # Discover every 10 seconds
        update_enabled=True      # Get device updates
    )

    print("✓ Controller created with discovery enabled")
    print()

    # Wait for discovery to happen
    print("Step 2: Waiting for device discovery (15 seconds)...")
    await asyncio.sleep(15)

    # Check discovered devices
    devices = controller.devices
    print(f"\n✓ Discovery complete. Found {len(devices)} device(s)")
    print()

    if not devices:
        print("✗ No devices discovered!")
        print("\nTroubleshooting:")
        print("  - Is the lamp powered on?")
        print("  - Is it on the same network?")
        print("  - Is Docker using --network host?")
        await controller.cleanup()
        return

    # List all discovered devices
    for idx, device in enumerate(devices, 1):
        print(f"Device {idx}:")
        print(f"  SKU: {device.sku}")
        print(f"  IP: {device.ip_address}")
        print(f"  Fingerprint: {device.fingerprint}")

        # Get device state
        if hasattr(device, 'state'):
            print(f"  State: {device.state}")

        # Check if it's our H6078
        if device.sku == "H6078":
            print(f"  ✓ This is the Torch Floor Lamp!")

            # Try to get capabilities
            if hasattr(device, 'capabilities'):
                print(f"  Capabilities: {device.capabilities}")

            # Try to send a scene command
            print(f"\n  Testing scene command...")
            try:
                # Govee local API uses JSON commands
                # Scene command format (based on Govee protocol)
                scene_command = {
                    "msg": {
                        "cmd": "ptReal",
                        "data": {
                            "command": "pt",
                            "value": 10  # Scene code 10 = "Rings"
                        }
                    }
                }

                command_str = json.dumps(scene_command)
                print(f"  Sending command: {command_str}")

                controller.send_raw_command(device, command_str)
                print(f"  ✓ Scene command sent!")

                # Wait a moment
                await asyncio.sleep(2)

            except Exception as e:
                print(f"  ✗ Error sending scene: {e}")

        print()

    # Cleanup
    await controller.cleanup()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_correct_api())
