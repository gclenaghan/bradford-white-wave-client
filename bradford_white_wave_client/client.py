import logging
import aiohttp
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

    def __init__(self, email: str, password: str):
        self.auth = BradfordWhiteAuth(email=email, password=password)
        self._session: Optional[aiohttp.ClientSession] = None
        self._access_token: Optional[str] = None

    async def authenticate(self):
        """Authenticate with the API."""
        try:
             tokens = await self.auth.authenticate()
             # self._access_token = tokens["access_token"]
        except Exception as e:
            raise BradfordWhiteConnectError(f"Authentication failed: {e}")

    async def list_devices(self) -> List[DeviceStatus]:
        """List all devices on the account."""
        # Implementation needed
        return []

    async def get_status(self, mac_address: str) -> DeviceStatus:
        """Get the status of a specific device."""
        # Implementation needed
        raise NotImplementedError

    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
