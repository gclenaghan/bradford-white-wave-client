import logging
import aiohttp
import json
import base64
from typing import List, Optional, Any, Dict
from .auth import BradfordWhiteAuth
from .models import DeviceStatus, EnergyUsage, WriteResponse, BradfordWhiteMode
from .const import (
    BASE_URL, 
    ENDPOINT_LIST_DEVICES, 
    ENDPOINT_GET_STATUS, 
    ENDPOINT_GET_ENERGY,
    ENDPOINT_SET_TEMP,
    ENDPOINT_SET_MODE,
    USER_AGENT
)
from .exceptions import BradfordWhiteConnectError

_LOGGER = logging.getLogger(__name__)

class BradfordWhiteClient:
    """Async client for Bradford White WaveAPI."""

    def __init__(self, refresh_token: str = None):
        """Initialize the client."""
        self.auth = BradfordWhiteAuth()
        self._session: Optional[aiohttp.ClientSession] = None
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = refresh_token
        self._account_id: Optional[str] = None

    def _parse_account_id(self) -> None:
        """Extract account ID (oid) from the current access token."""
        if not self._access_token:
            return
            
        try:
             # Split token, get payload
             payload_part = self._access_token.split(".")[1]
             # Add padding
             payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
             payload = json.loads(base64.b64decode(payload_part))
             self._account_id = payload.get("oid")
        except Exception as e:
             _LOGGER.error(f"Failed to parse account ID from token: {e}")
             raise BradfordWhiteConnectError("Could not extract 'oid' (Account ID) from access token.")

    def get_authorization_url(self, state: str = "init", nonce: str = "init") -> str:
        """Generate the authorization URL for the user."""
        return self.auth.generate_auth_url(state, nonce)
        
    async def authenticate_with_code(self, url: str) -> None:
        """Authenticate using a redirect URL."""
        code = self.auth.parse_redirect_url(url)
        tokens = await self.auth.exchange_code_for_token(code)
        
        self._access_token = tokens.get("access_token", tokens.get("id_token"))
        self._refresh_token = tokens.get("refresh_token")
        self._parse_account_id()
        
        if not self._refresh_token:
            raise BradfordWhiteConnectError("No refresh_token returned from exchange.")
            
    async def authenticate(self):
        """Ensure valid access token."""
        try:
             # If we have a refresh token, verify/refresh it
             if self._refresh_token:
                 _LOGGER.info("Using provided refresh token")
                 tokens = await self.auth.refresh_tokens(self._refresh_token)
                 
                 self._access_token = tokens.get("access_token", tokens.get("id_token"))
                 self._refresh_token = tokens.get("refresh_token", self._refresh_token)
                 self._parse_account_id()
                 
                 if not self._access_token:
                     raise BradfordWhiteConnectError("No access_token or id_token returned from refresh")
                 return
             else:
                 raise BradfordWhiteConnectError("No refresh token provided. Please use get_authorization_url() and authenticate_with_code() first.")
                 
        except Exception as e:
            raise BradfordWhiteConnectError(f"Authentication failed: {e}")

    async def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated request."""
        if not self._access_token:
            await self.authenticate()

        session = await self.auth._get_session()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._access_token}"
        
        full_url = f"{BASE_URL}{url}"
        
        async with session.request(method, full_url, headers=headers, **kwargs) as resp:
            if resp.status == 401:
                # Token expired, try refresh
                try:
                    _LOGGER.info("Token expired, refreshing...")
                    tokens = await self.auth.refresh_tokens(self._refresh_token)
                    self._access_token = tokens.get("access_token", tokens.get("id_token"))
                    self._refresh_token = tokens.get("refresh_token", self._refresh_token)
                    self._parse_account_id()
                    
                    if not self._access_token:
                        raise BradfordWhiteConnectError("No access_token or id_token returned from refresh")
                    
                    # Retry request
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with session.request(method, full_url, headers=headers, **kwargs) as resp2:
                         if resp2.status != 200:
                             text = await resp2.text()
                             raise BradfordWhiteConnectError(f"API request failed after refresh: {resp2.status} - {text}")
                         return await resp2.json()
                except Exception as e:
                     raise BradfordWhiteConnectError(f"Token refresh failed: {e}")

            if resp.status != 200:
                text = await resp.text()
                raise BradfordWhiteConnectError(f"API request failed: {resp.status} - {text}")
            
            return await resp.json()

    async def list_devices(self) -> List[DeviceStatus]:
        """List all devices on the account."""
        if not self._account_id:
            raise BradfordWhiteConnectError("Account ID not available.")

        params = {"username": self._account_id}
        data = await self._request("GET", ENDPOINT_LIST_DEVICES, params=params)
        
        return [DeviceStatus(**item) for item in data["appliances"]]

    async def get_status(self, mac_address: str) -> DeviceStatus:
        """Get the status of a specific device."""
        params = {"macAddress": mac_address} # Note camelCase from prompt
        data = await self._request("GET", ENDPOINT_GET_STATUS, params=params)
        return DeviceStatus(**data)
    
    # view_type: "hourly", "daily", "weekly", "monthly"
    async def get_energy_usage(self, mac_address: str, view_type: str = "hourly") -> List[EnergyUsage]:
        """Get energy usage statistics."""
        payload = {"mac_address": mac_address, "view_type": view_type}
        data = await self._request("POST", ENDPOINT_GET_ENERGY, json=payload)
        
        # Prompt: Returns a list of hourly stats.
        usage_list = []
        if isinstance(data, list):
             for item in data:
                 usage_list.append(EnergyUsage(**item))
        return usage_list

    async def set_temperature(self, mac_address: str, temperature: int) -> WriteResponse:
        """Set the water heater temperature (Fahrenheit)."""
        params = {"mac_address": mac_address, "temperature": temperature} # snake_case
        data = await self._request("GET", ENDPOINT_SET_TEMP, params=params)
        return WriteResponse(**data)

    async def set_mode(self, mac_address: str, mode: BradfordWhiteMode) -> WriteResponse:
        """Set the operation mode."""
        params = {"mac_address": mac_address, "mode": mode.value}
        data = await self._request("GET", ENDPOINT_SET_MODE, params=params)
        return WriteResponse(**data)

    """Close the session."""
    async def close(self):
        if self._session:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
