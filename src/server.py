#!/usr/bin/env python3
"""
MCP Server for Govee RGBIC Cylinder Floor Lamp Control

This server provides tools to control Govee smart lighting devices through the MCP protocol.
"""

import os
import asyncio
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from fastmcp import FastMCP
from govee_api_laggat import Govee, GoveeDevice

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("govee-controller")

# Govee API client (initialized on first use)
_govee_client: Optional[Govee] = None


async def get_govee_client() -> Govee:
    """Get or create the Govee API client."""
    global _govee_client

    if _govee_client is None:
        api_key = os.getenv("GOVEE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOVEE_API_KEY not found in environment variables. "
                "Please set it in your .env file or environment."
            )

        _govee_client = await Govee.create(api_key)

    return _govee_client


async def get_target_device() -> GoveeDevice:
    """
    Get the target Govee device based on environment configuration.

    If GOVEE_DEVICE_ADDRESS or GOVEE_DEVICE_MODEL is set, filters to that device.
    Otherwise, returns the first available device.
    """
    govee = await get_govee_client()
    devices, _ = await govee.get_devices()

    if not devices:
        raise ValueError("No Govee devices found on your account")

    target_address = os.getenv("GOVEE_DEVICE_ADDRESS", "").strip()
    target_model = os.getenv("GOVEE_DEVICE_MODEL", "").strip()

    # Filter devices if specific device is requested
    if target_address or target_model:
        for device in devices:
            address_match = not target_address or device.device == target_address
            model_match = not target_model or device.model == target_model

            if address_match and model_match:
                return device

        raise ValueError(
            f"Device not found with address={target_address}, model={target_model}"
        )

    # Return first device if no filter specified
    return devices[0]


@mcp.tool()
async def turn_on() -> str:
    """Turn on the Govee lamp."""
    try:
        device = await get_target_device()
        govee = await get_govee_client()
        success, _ = await govee.turn_on(device)

        if success:
            return f"✓ Lamp turned ON (Device: {device.device_name})"
        else:
            return f"✗ Failed to turn on lamp (Device: {device.device_name})"
    except Exception as e:
        return f"✗ Error: {str(e)}"


@mcp.tool()
async def turn_off() -> str:
    """Turn off the Govee lamp."""
    try:
        device = await get_target_device()
        govee = await get_govee_client()
        success, _ = await govee.turn_off(device)

        if success:
            return f"✓ Lamp turned OFF (Device: {device.device_name})"
        else:
            return f"✗ Failed to turn off lamp (Device: {device.device_name})"
    except Exception as e:
        return f"✗ Error: {str(e)}"


@mcp.tool()
async def set_brightness(brightness: int) -> str:
    """
    Set the brightness of the Govee lamp.

    Args:
        brightness: Brightness level from 0 to 100
    """
    try:
        if not 0 <= brightness <= 100:
            return "✗ Error: Brightness must be between 0 and 100"

        device = await get_target_device()
        govee = await get_govee_client()
        success, _ = await govee.set_brightness(device, brightness)

        if success:
            return f"✓ Brightness set to {brightness}% (Device: {device.device_name})"
        else:
            return f"✗ Failed to set brightness (Device: {device.device_name})"
    except Exception as e:
        return f"✗ Error: {str(e)}"


@mcp.tool()
async def set_color(red: int, green: int, blue: int) -> str:
    """
    Set the color of the Govee lamp using RGB values.

    Args:
        red: Red value from 0 to 255
        green: Green value from 0 to 255
        blue: Blue value from 0 to 255
    """
    try:
        # Validate RGB values
        if not all(0 <= val <= 255 for val in [red, green, blue]):
            return "✗ Error: RGB values must be between 0 and 255"

        device = await get_target_device()
        govee = await get_govee_client()

        # Govee API expects RGB as a tuple
        success, _ = await govee.set_color(device, (red, green, blue))

        if success:
            return f"✓ Color set to RGB({red}, {green}, {blue}) (Device: {device.device_name})"
        else:
            return f"✗ Failed to set color (Device: {device.device_name})"
    except Exception as e:
        return f"✗ Error: {str(e)}"


@mcp.tool()
async def set_color_temperature(temperature: int) -> str:
    """
    Set the color temperature of the Govee lamp.

    Args:
        temperature: Color temperature in Kelvin, typically 2000-9000
    """
    try:
        if not 2000 <= temperature <= 9000:
            return "✗ Error: Color temperature must be between 2000K and 9000K"

        device = await get_target_device()
        govee = await get_govee_client()
        success, _ = await govee.set_color_temp(device, temperature)

        if success:
            return f"✓ Color temperature set to {temperature}K (Device: {device.device_name})"
        else:
            return f"✗ Failed to set color temperature (Device: {device.device_name})"
    except Exception as e:
        return f"✗ Error: {str(e)}"


@mcp.tool()
async def get_device_state() -> str:
    """Get the current state of the Govee lamp."""
    try:
        device = await get_target_device()
        govee = await get_govee_client()

        # Get fresh device state
        success, _ = await govee.get_states()

        if not success:
            return f"✗ Failed to get device state (Device: {device.device_name})"

        # Format device state
        state_info = [
            f"Device: {device.device_name}",
            f"Model: {device.model}",
            f"Address: {device.device}",
            f"Power: {'ON' if device.power_state else 'OFF'}",
            f"Brightness: {device.brightness}%",
        ]

        if device.color:
            r, g, b = device.color
            state_info.append(f"Color: RGB({r}, {g}, {b})")

        if device.color_temp:
            state_info.append(f"Color Temperature: {device.color_temp}K")

        if device.online is not None:
            state_info.append(f"Online: {device.online}")

        return "\n".join(state_info)
    except Exception as e:
        return f"✗ Error: {str(e)}"


@mcp.tool()
async def list_devices() -> str:
    """List all available Govee devices on the account."""
    try:
        govee = await get_govee_client()
        devices, _ = await govee.get_devices()

        if not devices:
            return "No Govee devices found on your account"

        device_list = ["Available Govee Devices:", ""]

        for idx, device in enumerate(devices, 1):
            device_list.append(f"{idx}. {device.device_name}")
            device_list.append(f"   Model: {device.model}")
            device_list.append(f"   Address: {device.device}")
            device_list.append(f"   Controllable: {device.controllable}")
            device_list.append(f"   Retrievable: {device.retrievable}")
            device_list.append("")

        return "\n".join(device_list)
    except Exception as e:
        return f"✗ Error: {str(e)}"


@mcp.tool()
async def set_preset_color(color_name: str) -> str:
    """
    Set the lamp to a preset color by name.

    Args:
        color_name: Color name (red, green, blue, yellow, cyan, magenta, white, warm_white, orange, purple, pink)
    """
    # Preset color mappings
    preset_colors = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "cyan": (0, 255, 255),
        "magenta": (255, 0, 255),
        "white": (255, 255, 255),
        "warm_white": (255, 230, 180),
        "orange": (255, 165, 0),
        "purple": (128, 0, 128),
        "pink": (255, 192, 203),
    }

    color_name_lower = color_name.lower()

    if color_name_lower not in preset_colors:
        available = ", ".join(preset_colors.keys())
        return f"✗ Unknown color: {color_name}. Available: {available}"

    r, g, b = preset_colors[color_name_lower]
    return await set_color(r, g, b)


if __name__ == "__main__":
    import sys

    # Determine transport mode from environment or command line
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

    # Check for command line argument
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--sse", "--http"]:
            transport = "sse"
        elif sys.argv[1] == "--stdio":
            transport = "stdio"

    # Run the MCP server with appropriate transport
    if transport == "sse":
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "8080"))
        print(f"Starting MCP server with SSE transport on {host}:{port}", file=sys.stderr)
        mcp.run(transport="sse", host=host, port=port)
    else:
        print("Starting MCP server with stdio transport", file=sys.stderr)
        mcp.run()
