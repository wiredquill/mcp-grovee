#!/usr/bin/env python3
"""
Test script to debug Govee API v2 scenes functionality
"""

import asyncio
import os
import httpx
from dotenv import load_dotenv
from govee_api_laggat import Govee

load_dotenv()

async def test_scenes():
    """Test the Govee API v2 scenes endpoints."""

    api_key = os.getenv("GOVEE_API_KEY")
    if not api_key:
        print("ERROR: GOVEE_API_KEY not found in .env file")
        return

    print("=" * 70)
    print("GOVEE API V2 SCENES TEST")
    print("=" * 70)
    print()

    # First, get device info using the old API
    print("Step 1: Getting device information...")
    govee = await Govee.create(api_key)
    devices, _ = await govee.get_devices()

    if not devices:
        print("ERROR: No devices found")
        return

    device = devices[0]
    print(f"✓ Found device: {device.device_name}")
    print(f"  Model: {device.model}")
    print(f"  Address: {device.device}")
    print()

    # Prepare device info for API v2
    device_info = {
        "device": device.device.replace(":", ""),
        "sku": device.model
    }

    print("Step 2: Device info for API v2:")
    print(f"  Device: {device_info['device']}")
    print(f"  SKU: {device_info['sku']}")
    print()

    # Test dynamic scenes endpoint
    print("Step 3: Testing dynamic scenes endpoint...")
    print(f"  URL: https://openapi.api.govee.com/router/api/v1/device/scenes")
    print(f"  Payload: {device_info}")

    headers = {
        "Govee-API-Key": api_key,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://openapi.api.govee.com/router/api/v1/device/scenes",
                headers=headers,
                json=device_info,
                timeout=30.0
            )

            print(f"  Status Code: {response.status_code}")
            print(f"  Response Headers: {dict(response.headers)}")
            print()

            if response.status_code == 200:
                data = response.json()
                print("  Response Data:")
                import json
                print(json.dumps(data, indent=2))
            else:
                print(f"  ERROR Response:")
                print(f"  {response.text}")

        except Exception as e:
            print(f"  EXCEPTION: {type(e).__name__}: {str(e)}")

        print()

    # Test DIY scenes endpoint
    print("Step 4: Testing DIY scenes endpoint...")
    print(f"  URL: https://openapi.api.govee.com/router/api/v1/device/diy-scenes")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://openapi.api.govee.com/router/api/v1/device/diy-scenes",
                headers=headers,
                json=device_info,
                timeout=30.0
            )

            print(f"  Status Code: {response.status_code}")
            print()

            if response.status_code == 200:
                data = response.json()
                print("  Response Data:")
                import json
                print(json.dumps(data, indent=2))
            else:
                print(f"  ERROR Response:")
                print(f"  {response.text}")

        except Exception as e:
            print(f"  EXCEPTION: {type(e).__name__}: {str(e)}")

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_scenes())
