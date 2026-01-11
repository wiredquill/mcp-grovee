#!/usr/bin/env python3
"""
Test script to find the correct Govee API v2 format for scenes
"""

import asyncio
import os
import httpx
from dotenv import load_dotenv
from govee_api_laggat import Govee

load_dotenv()

async def test_api_formats():
    """Test different API formats to find the correct one."""

    api_key = os.getenv("GOVEE_API_KEY")
    if not api_key:
        print("ERROR: GOVEE_API_KEY not found")
        return

    print("=" * 70)
    print("TESTING DIFFERENT GOVEE API FORMATS")
    print("=" * 70)
    print()

    # Get device info
    govee = await Govee.create(api_key)
    devices, _ = await govee.get_devices()
    device = devices[0]

    print(f"Device: {device.device_name}")
    print(f"Model: {device.model}")
    print(f"Address: {device.device}")
    print()

    # Test different formats
    test_cases = [
        {
            "name": "Format 1: Original (router API)",
            "url": "https://openapi.api.govee.com/router/api/v1/device/scenes",
            "headers": {
                "Govee-API-Key": api_key,
                "Content-Type": "application/json"
            },
            "payload": {
                "device": device.device.replace(":", ""),
                "sku": device.model
            }
        },
        {
            "name": "Format 2: Direct API v1 (old format)",
            "url": "https://developer-api.govee.com/v1/devices/scenes",
            "headers": {
                "Govee-API-Key": api_key,
                "Content-Type": "application/json"
            },
            "payload": {
                "device": device.device,
                "model": device.model
            }
        },
        {
            "name": "Format 3: OpenAPI scenes",
            "url": "https://openapi.api.govee.com/v1/appliance/scenes",
            "headers": {
                "Govee-API-Key": api_key,
                "Content-Type": "application/json"
            },
            "payload": {
                "device": device.device.replace(":", ""),
                "model": device.model
            }
        },
        {
            "name": "Format 4: Device state (to verify API key works)",
            "url": "https://developer-api.govee.com/v1/devices/state",
            "headers": {
                "Govee-API-Key": api_key
            },
            "payload": {
                "device": device.device,
                "model": device.model
            },
            "method": "GET",
            "use_params": True
        }
    ]

    async with httpx.AsyncClient() as client:
        for idx, test in enumerate(test_cases, 1):
            print(f"\n{'='*70}")
            print(f"TEST {idx}: {test['name']}")
            print(f"{'='*70}")
            print(f"URL: {test['url']}")
            print(f"Headers: {test['headers']}")
            print(f"Payload: {test['payload']}")
            print()

            try:
                method = test.get('method', 'POST')

                if method == 'GET' and test.get('use_params'):
                    response = await client.get(
                        test['url'],
                        headers=test['headers'],
                        params=test['payload'],
                        timeout=30.0
                    )
                else:
                    response = await client.post(
                        test['url'],
                        headers=test['headers'],
                        json=test['payload'],
                        timeout=30.0
                    )

                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    print("✓ SUCCESS!")
                    try:
                        data = response.json()
                        import json
                        print(json.dumps(data, indent=2))
                    except:
                        print(response.text)
                else:
                    print(f"✗ FAILED: {response.status_code}")
                    print(f"Response: {response.text}")

            except httpx.HTTPStatusError as e:
                print(f"✗ HTTP Error: {e.response.status_code}")
                print(f"Response: {e.response.text}")
            except Exception as e:
                print(f"✗ Exception: {type(e).__name__}: {str(e)}")

    print(f"\n{'='*70}")
    print("TESTING COMPLETE")
    print(f"{'='*70}")

if __name__ == "__main__":
    asyncio.run(test_api_formats())
