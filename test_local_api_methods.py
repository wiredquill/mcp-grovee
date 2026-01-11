#!/usr/bin/env python3
"""
Explore the govee-local-api library to find the correct methods
"""

import asyncio
from govee_local_api import GoveeController

async def explore_api():
    """Explore the actual API of govee-local-api."""

    print("=" * 70)
    print("EXPLORING GOVEE-LOCAL-API LIBRARY")
    print("=" * 70)
    print()

    # Create controller
    controller = GoveeController()

    print("GoveeController attributes and methods:")
    print()

    for attr in dir(controller):
        if not attr.startswith('_'):
            attr_value = getattr(controller, attr, None)
            print(f"  {attr}: {type(attr_value).__name__}")
            if callable(attr_value):
                # Try to get the signature
                import inspect
                try:
                    sig = inspect.signature(attr_value)
                    print(f"    Signature: {sig}")
                except:
                    pass

    print()
    print("=" * 70)
    print("Checking documentation...")
    print("=" * 70)
    print()

    if hasattr(controller, '__doc__') and controller.__doc__:
        print("Controller docstring:")
        print(controller.__doc__)

    print()
    print("Class help:")
    help(GoveeController)

if __name__ == "__main__":
    asyncio.run(explore_api())
