#!/usr/bin/env python3
"""
Direct UDP communication with Govee devices for local control.

This module provides direct unicast UDP communication when multicast
discovery doesn't work in the network environment.
"""

import asyncio
import json
import socket
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class GoveeLocalDevice:
    """Represents a Govee device discovered on local network."""
    ip: str
    device_id: str
    sku: str
    ble_version_hard: str
    ble_version_soft: str
    wifi_version_hard: str
    wifi_version_soft: str


class GoveeLocalClient:
    """
    Direct UDP client for Govee local API.

    Uses unicast UDP instead of multicast for environments where
    multicast doesn't work properly.
    """

    BROADCAST_PORT = 4001  # Discovery port
    COMMAND_PORT = 4003    # Command port
    LISTENING_PORT = 4002  # Listening port
    TIMEOUT = 3.0          # Socket timeout in seconds

    def __init__(self, device_ip: Optional[str] = None):
        """
        Initialize the local client.

        Args:
            device_ip: Optional known device IP address. If provided,
                      discovery will use direct unicast to this IP.
        """
        self.device_ip = device_ip
        self._sock: Optional[socket.socket] = None

    def _create_socket(self) -> socket.socket:
        """Create and configure a UDP socket."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(self.TIMEOUT)
        return sock

    async def discover_device(self, target_ip: Optional[str] = None) -> Optional[GoveeLocalDevice]:
        """
        Discover a Govee device using direct unicast.

        Args:
            target_ip: IP address to query. Uses self.device_ip if not provided.

        Returns:
            GoveeLocalDevice if found, None otherwise.
        """
        ip = target_ip or self.device_ip
        if not ip:
            raise ValueError("No device IP provided for discovery")

        scan_message = {
            "msg": {
                "cmd": "scan",
                "data": {
                    "account_topic": "reserve"
                }
            }
        }

        sock = self._create_socket()
        try:
            sock.bind(('0.0.0.0', self.LISTENING_PORT))

            # Send discovery message
            message_bytes = json.dumps(scan_message).encode('utf-8')
            sock.sendto(message_bytes, (ip, self.BROADCAST_PORT))

            # Wait for response
            try:
                data, addr = sock.recvfrom(4096)
                response = json.loads(data.decode('utf-8'))

                # Parse response
                if response.get('msg', {}).get('cmd') == 'scan':
                    data = response['msg']['data']
                    return GoveeLocalDevice(
                        ip=data['ip'],
                        device_id=data['device'],
                        sku=data['sku'],
                        ble_version_hard=data.get('bleVersionHard', ''),
                        ble_version_soft=data.get('bleVersionSoft', ''),
                        wifi_version_hard=data.get('wifiVersionHard', ''),
                        wifi_version_soft=data.get('wifiVersionSoft', '')
                    )
            except socket.timeout:
                return None
        finally:
            sock.close()

        return None

    async def get_device_status(self, device_ip: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a device.

        Args:
            device_ip: IP address of device. Uses self.device_ip if not provided.

        Returns:
            Status dictionary with onOff, brightness, color, colorTemInKelvin
        """
        ip = device_ip or self.device_ip
        if not ip:
            raise ValueError("No device IP provided")

        status_msg = {
            "msg": {
                "cmd": "devStatus",
                "data": {}
            }
        }

        sock = self._create_socket()
        try:
            sock.bind(('0.0.0.0', self.LISTENING_PORT))

            # Send status request
            message_bytes = json.dumps(status_msg).encode('utf-8')
            sock.sendto(message_bytes, (ip, self.COMMAND_PORT))

            # Wait for response
            try:
                data, addr = sock.recvfrom(4096)
                response = json.loads(data.decode('utf-8'))

                if response.get('msg', {}).get('cmd') == 'devStatus':
                    return response['msg']['data']
            except socket.timeout:
                return None
        finally:
            sock.close()

        return None

    async def activate_scene(self, scene_code: int, device_ip: Optional[str] = None) -> bool:
        """
        Activate a scene on the device.

        Args:
            scene_code: Scene code (e.g., 10 for "Rings")
            device_ip: IP address of device. Uses self.device_ip if not provided.

        Returns:
            True if command sent successfully (note: device may not respond)
        """
        ip = device_ip or self.device_ip
        if not ip:
            raise ValueError("No device IP provided")

        scene_msg = {
            "msg": {
                "cmd": "ptReal",
                "data": {
                    "command": "pt",
                    "value": scene_code
                }
            }
        }

        sock = self._create_socket()
        try:
            sock.bind(('0.0.0.0', self.LISTENING_PORT))

            # Send scene command
            message_bytes = json.dumps(scene_msg).encode('utf-8')
            sock.sendto(message_bytes, (ip, self.COMMAND_PORT))

            # Command sent successfully
            # Note: Device may not send response for scene commands
            return True
        except Exception:
            return False
        finally:
            sock.close()

    async def set_brightness(self, brightness: int, device_ip: Optional[str] = None) -> bool:
        """
        Set device brightness.

        Args:
            brightness: Brightness value 0-100
            device_ip: IP address of device. Uses self.device_ip if not provided.

        Returns:
            True if command sent successfully
        """
        ip = device_ip or self.device_ip
        if not ip:
            raise ValueError("No device IP provided")

        if not 0 <= brightness <= 100:
            raise ValueError("Brightness must be between 0 and 100")

        brightness_msg = {
            "msg": {
                "cmd": "brightness",
                "data": {
                    "value": brightness
                }
            }
        }

        sock = self._create_socket()
        try:
            sock.bind(('0.0.0.0', self.LISTENING_PORT))

            message_bytes = json.dumps(brightness_msg).encode('utf-8')
            sock.sendto(message_bytes, (ip, self.COMMAND_PORT))

            return True
        except Exception:
            return False
        finally:
            sock.close()

    async def set_color(self, r: int, g: int, b: int, device_ip: Optional[str] = None) -> bool:
        """
        Set device color.

        Args:
            r: Red value 0-255
            g: Green value 0-255
            b: Blue value 0-255
            device_ip: IP address of device. Uses self.device_ip if not provided.

        Returns:
            True if command sent successfully
        """
        ip = device_ip or self.device_ip
        if not ip:
            raise ValueError("No device IP provided")

        if not all(0 <= v <= 255 for v in [r, g, b]):
            raise ValueError("RGB values must be between 0 and 255")

        color_msg = {
            "msg": {
                "cmd": "colorwc",
                "data": {
                    "color": {
                        "r": r,
                        "g": g,
                        "b": b
                    },
                    "colorTemInKelvin": 0
                }
            }
        }

        sock = self._create_socket()
        try:
            sock.bind(('0.0.0.0', self.LISTENING_PORT))

            message_bytes = json.dumps(color_msg).encode('utf-8')
            sock.sendto(message_bytes, (ip, self.COMMAND_PORT))

            return True
        except Exception:
            return False
        finally:
            sock.close()

    async def turn_on(self, device_ip: Optional[str] = None) -> bool:
        """
        Turn device on.

        Args:
            device_ip: IP address of device. Uses self.device_ip if not provided.

        Returns:
            True if command sent successfully
        """
        ip = device_ip or self.device_ip
        if not ip:
            raise ValueError("No device IP provided")

        on_msg = {
            "msg": {
                "cmd": "turn",
                "data": {
                    "value": 1
                }
            }
        }

        sock = self._create_socket()
        try:
            sock.bind(('0.0.0.0', self.LISTENING_PORT))

            message_bytes = json.dumps(on_msg).encode('utf-8')
            sock.sendto(message_bytes, (ip, self.COMMAND_PORT))

            return True
        except Exception:
            return False
        finally:
            sock.close()

    async def turn_off(self, device_ip: Optional[str] = None) -> bool:
        """
        Turn device off.

        Args:
            device_ip: IP address of device. Uses self.device_ip if not provided.

        Returns:
            True if command sent successfully
        """
        ip = device_ip or self.device_ip
        if not ip:
            raise ValueError("No device IP provided")

        off_msg = {
            "msg": {
                "cmd": "turn",
                "data": {
                    "value": 0
                }
            }
        }

        sock = self._create_socket()
        try:
            sock.bind(('0.0.0.0', self.LISTENING_PORT))

            message_bytes = json.dumps(off_msg).encode('utf-8')
            sock.sendto(message_bytes, (ip, self.COMMAND_PORT))

            return True
        except Exception:
            return False
        finally:
            sock.close()


# Common scene codes for Govee devices
COMMON_SCENES = {
    1: "Sunrise",
    2: "Sunset",
    3: "Movie",
    4: "Dating",
    5: "Romantic",
    6: "Blinking",
    7: "Candlelight",
    8: "Snowflake",
    9: "Energetic",
    10: "Rings",
    11: "Beautiful",
    12: "Night",
    13: "Reading",
    14: "Working",
    15: "Sleeping",
}


def get_scene_name(scene_code: int) -> str:
    """Get the name of a scene by its code."""
    return COMMON_SCENES.get(scene_code, f"Scene {scene_code}")
