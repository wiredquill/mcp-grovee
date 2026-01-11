#!/usr/bin/env python3
"""
Govee Undocumented API Client

This module provides access to Govee's undocumented APIs for features not
available in the official Platform API, such as tap-to-run/one-click scenes.

Based on research from: https://github.com/wez/govee2mqtt

WARNING: This API is undocumented and may change or break at any time.
"""

import asyncio
import httpx
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class GoveeAccount:
    """Represents a logged-in Govee account."""
    email: str
    token: str
    account_id: str
    topic: str
    expires_at: datetime


@dataclass
class CommunityAuth:
    """Represents community API authentication."""
    token: str
    expires_at: datetime


@dataclass
class OneClickShortcut:
    """Represents a one-click/tap-to-run shortcut."""
    name: str
    shortcut_id: str
    iot_rules: List[Dict[str, Any]]
    devices: List[str]


class GoveeUndocumentedAPI:
    """
    Client for Govee's undocumented APIs.

    Provides access to:
    - Account authentication
    - One-click/tap-to-run shortcuts
    - IoT credentials for AWS MQTT
    """

    BASE_URL = "https://app2.govee.com"
    COMMUNITY_BASE_URL = "https://community-api.govee.com"

    # Standard headers mimicking Govee mobile app
    USER_AGENT = "GoveeHome/5.6.01 (com.ihoment.GoVeeSensor; build:2; iOS 16.5.0)"

    def __init__(self, email: str, password: str):
        """
        Initialize the undocumented API client.

        Args:
            email: Govee account email
            password: Govee account password
        """
        self.email = email
        self.password = password
        self._account: Optional[GoveeAccount] = None
        self._community_auth: Optional[CommunityAuth] = None
        self._client_id = "1234567890abcdef"  # Simulated device ID

    async def _get_headers(self, include_auth: bool = False) -> Dict[str, str]:
        """
        Get standard headers for API requests.

        Args:
            include_auth: Whether to include Authorization header

        Returns:
            Dictionary of headers
        """
        headers = {
            "User-Agent": self.USER_AGENT,
            "Content-Type": "application/json",
            "appVersion": "5.6.01",
            "clientId": self._client_id,
            "clientType": "1",  # iOS
            "iotVersion": "0",
            "timestamp": str(int(time.time() * 1000))
        }

        if include_auth and self._account:
            headers["Authorization"] = f"Bearer {self._account.token}"

        return headers

    async def login(self, force_refresh: bool = False) -> GoveeAccount:
        """
        Login to Govee account and get authentication token.

        Args:
            force_refresh: Force new login even if cached token is valid

        Returns:
            GoveeAccount with authentication details
        """
        # Check if we have a valid cached token
        if self._account and not force_refresh:
            if datetime.now() < self._account.expires_at:
                return self._account

        url = f"{self.BASE_URL}/account/rest/account/v1/login"

        payload = {
            "email": self.email,
            "password": self.password,
            "client": "ios"
        }

        headers = await self._get_headers()

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != 200:
                raise ValueError(f"Login failed: {data.get('message', 'Unknown error')}")

            result = data.get("data", {})

            # Token expires in 12 hours (from govee2mqtt research)
            expires_at = datetime.now() + timedelta(hours=12)

            self._account = GoveeAccount(
                email=self.email,
                token=result.get("token", ""),
                account_id=result.get("accountId", ""),
                topic=result.get("topic", ""),
                expires_at=expires_at
            )

            return self._account

    async def login_community(self, force_refresh: bool = False) -> CommunityAuth:
        """
        Login to community API for one-click shortcuts.

        Args:
            force_refresh: Force new login even if cached token is valid

        Returns:
            CommunityAuth with bearer token
        """
        # Check if we have a valid cached token
        if self._community_auth and not force_refresh:
            if datetime.now() < self._community_auth.expires_at:
                return self._community_auth

        url = f"{self.COMMUNITY_BASE_URL}/os/v1/login"

        payload = {
            "email": self.email,
            "password": self.password
        }

        headers = {
            "User-Agent": self.USER_AGENT,
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != 200:
                raise ValueError(f"Community login failed: {data.get('message', 'Unknown error')}")

            result = data.get("data", {})
            token = result.get("token", "")
            expires_ms = result.get("tokenExpiredTime", 0)

            # Convert milliseconds timestamp to datetime
            if expires_ms:
                expires_at = datetime.fromtimestamp(expires_ms / 1000)
            else:
                # Default to 1 day if not provided
                expires_at = datetime.now() + timedelta(days=1)

            self._community_auth = CommunityAuth(
                token=token,
                expires_at=expires_at
            )

            return self._community_auth

    async def get_iot_credentials(self) -> Dict[str, Any]:
        """
        Get IoT credentials for AWS MQTT connection.

        This is needed for real-time device control via AWS IoT.

        Returns:
            Dictionary with endpoint, p12 certificate, and password
        """
        # Ensure we're logged in
        await self.login()

        url = f"{self.BASE_URL}/app/v1/account/iot/key"

        headers = await self._get_headers(include_auth=True)

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != 200:
                raise ValueError(f"Failed to get IoT credentials: {data.get('message', 'Unknown error')}")

            result = data.get("data", {})

            return {
                "endpoint": result.get("endpoint", ""),
                "p12": result.get("p12", ""),  # Base64-encoded certificate
                "p12_pass": result.get("p12_pass", ""),
                "log": result.get("log", "")
            }

    async def get_one_click_shortcuts(self) -> List[OneClickShortcut]:
        """
        Get all one-click/tap-to-run shortcuts configured in Govee app.

        Returns:
            List of OneClickShortcut objects
        """
        # Login to community API
        auth = await self.login_community()

        url = f"{self.BASE_URL}/bff-app/v1/exec-plat/home"

        headers = {
            "User-Agent": self.USER_AGENT,
            "Authorization": f"Bearer {auth.token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != 200:
                raise ValueError(f"Failed to get shortcuts: {data.get('message', 'Unknown error')}")

            result = data.get("data", {})
            shortcuts = []

            # Parse shortcuts from home data
            # The structure contains groups with shortcuts inside
            groups = result.get("groups", [])

            for group in groups:
                items = group.get("items", [])

                for item in items:
                    # Check if this is a one-click shortcut
                    if item.get("type") == "oneClick":
                        shortcut_data = item.get("data", {})

                        shortcut = OneClickShortcut(
                            name=shortcut_data.get("name", "Unnamed"),
                            shortcut_id=shortcut_data.get("id", ""),
                            iot_rules=shortcut_data.get("iotRules", []),
                            devices=shortcut_data.get("devices", [])
                        )

                        shortcuts.append(shortcut)

            return shortcuts

    async def get_light_effect_library(self, sku: str) -> List[Dict[str, Any]]:
        """
        Get light effect library for a specific device SKU.

        This provides additional scene information beyond the platform API.

        Args:
            sku: Device SKU (e.g., "H6078")

        Returns:
            List of scene categories with scenes
        """
        # Ensure we're logged in
        await self.login()

        url = f"{self.BASE_URL}/appsku/v1/light-effect-libraries?sku={sku}"

        headers = await self._get_headers(include_auth=True)

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != 200:
                raise ValueError(f"Failed to get light effects: {data.get('message', 'Unknown error')}")

            result = data.get("data", {})

            # Return scene categories
            return result.get("sceneCategories", [])

    async def execute_one_click_shortcut(self, shortcut: OneClickShortcut) -> bool:
        """
        Execute a one-click shortcut.

        Note: This requires AWS IoT MQTT connection, which is not yet implemented.
        For now, this returns the IoT rules that would need to be published.

        Args:
            shortcut: The OneClickShortcut to execute

        Returns:
            True if command prepared successfully
        """
        # This would need AWS IoT MQTT implementation
        # For now, we just validate the shortcut has IoT rules

        if not shortcut.iot_rules:
            raise ValueError(f"Shortcut '{shortcut.name}' has no IoT rules")

        # TODO: Implement AWS IoT MQTT publishing
        # For each rule in shortcut.iot_rules:
        #   - Connect to AWS IoT endpoint
        #   - Publish to device topic
        #   - Send the command payload

        return True
