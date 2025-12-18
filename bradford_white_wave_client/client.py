import logging
import aiohttp
import json
from typing import List, Optional, Any, Dict
from .auth import BradfordWhiteAuth
from .models import DeviceStatus, EnergyUsage, WriteResponse
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

    def __init__(self, email: str = None, password: str = None, refresh_token: str = None):
        if not refresh_token and not (email and password):
            raise ValueError("Must provide either email/password or a refresh_token")
            
        self.auth = BradfordWhiteAuth(email or "", password or "")
        self._session: Optional[aiohttp.ClientSession] = None
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = refresh_token

    async def authenticate(self):
        """Authenticate with the API."""
        try:
             # If we have a refresh token but no access token, try refreshing first
             if self._refresh_token and not self._access_token:
                 _LOGGER.info("Using provided refresh token")
                 tokens = await self.auth.refresh_tokens(self._refresh_token)
                 # Some B2C flows return id_token instead of access_token
                 self._access_token = tokens.get("access_token", tokens.get("id_token"))
                 self._refresh_token = tokens.get("refresh_token", self._refresh_token)
                 
                 if not self._access_token:
                     raise BradfordWhiteConnectError("No access_token or id_token returned from refresh")
                 return

             # Otherwise full login
             if self.auth.email and self.auth.password:
                tokens = await self.auth.authenticate()
                self._access_token = tokens.get("access_token", tokens.get("id_token"))
                self._refresh_token = tokens.get("refresh_token")
             else:
                 raise BradfordWhiteConnectError("No credentials for full authentication")
                 
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
        # Need account ID (oid) from token usually, or email? 
        # The prompt says: Query: username=<ACCOUNT_ID> (Extracted from JWT 'oid')
        # We need to decode the JWT to get the OID.
        
        if not self._access_token:
            await self.authenticate()
            
        # Basic JWT decode without verifying signature (we trust the IDP we just authed with)
        try:
             import base64
             # Split token, get payload
             payload_part = self._access_token.split(".")[1]
             # Add padding
             payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
             payload = json.loads(base64.b64decode(payload_part))
             account_id = payload.get("oid")
        except Exception:
             # Fallback or fail? Prompt says "Extracted from JWT 'oid'"
             # If we can't extract, we might fail.
             raise BradfordWhiteConnectError("Could not extract 'oid' (Account ID) from access token.")

        params = {"username": account_id}
        data = await self._request("GET", ENDPOINT_LIST_DEVICES, params=params)
        
        # API returns a list or a dict with a list? 
        # Usually list based on prompts "Returns a list..."
        # Let's assume list of dicts.
        
        devices = []
        if isinstance(data, dict) and "appliances" in data:
            for item in data["appliances"]:
                devices.append(DeviceStatus(**item))
        elif isinstance(data, list):
             # Fallback if sometimes it returns a direct list
             for item in data:
                 devices.append(DeviceStatus(**item))
             # Or maybe it's just the dict if single device? Unlikely for "list".
        
        return devices

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

    async def set_mode(self, mac_address: str, mode: int) -> WriteResponse:
        """Set the operation mode."""
        # Modes: 0=Standard, 1=Vacation, 2=Only Heat Pump, 3=Heat Pump (Hybrid), 4=High Demand, 5=Electric
        params = {"mac_address": mac_address, "mode": mode}
        data = await self._request("GET", ENDPOINT_SET_MODE, params=params)
        return WriteResponse(**data)

        """Close the session."""
        if self._session:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
