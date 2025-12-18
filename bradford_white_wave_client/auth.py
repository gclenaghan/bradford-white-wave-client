import logging
import urllib.parse
import aiohttp
from typing import Dict, Any, Optional
from .const import (
    AUTH_URL, 
    TOKEN_URL, 
    CLIENT_ID, 
    REDIRECT_URI, 
    SCOPE, 
    USER_AGENT
)
from .exceptions import BradfordWhiteAuthError

_LOGGER = logging.getLogger(__name__)

class BradfordWhiteAuth:
    """Handle Bradford White Authentication."""

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            # Debug Trace Config
            async def on_request_start(session, trace_config_ctx, params):
                _LOGGER.debug(f">> Request: {params.method} {params.url}")
                _LOGGER.debug(f">> Headers: {params.headers}")

            async def on_request_end(session, trace_config_ctx, params):
                _LOGGER.debug(f"<< Response: {params.response.status}")
                _LOGGER.debug(f"<< Headers: {params.response.headers}")

            trace_config = aiohttp.TraceConfig()
            trace_config.on_request_start.append(on_request_start)
            trace_config.on_request_end.append(on_request_end)

            self._session = aiohttp.ClientSession(
                headers={"User-Agent": USER_AGENT},
                cookie_jar=aiohttp.CookieJar(unsafe=True),
                trace_configs=[trace_config]
            )
        return self._session

    def generate_auth_url(self, state: str, nonce: str) -> str:
        """Generate the authorization URL for the user to visit."""
        params = {
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(SCOPE),
            "state": state,
            "nonce": nonce,
        }
        return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    @staticmethod
    def parse_redirect_url(url: str) -> str:
        """Extract the authorization code from the redirect URL."""
        if "confirmed" in url:
             raise BradfordWhiteAuthError("URL seems to be the intermediate 'confirmed' page. Please use the final 'com.bradfordwhiteapps.bwconnect://' URL.")
        
        try:
            parsed = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed.query)
            code = query_params.get("code", [None])[0]
            if not code:
                # Fallback: maybe the URL is just the code?
                if "://" not in url and len(url) > 20: 
                    return url
                raise BradfordWhiteAuthError("No 'code' parameter found in the URL.")
            return code
        except Exception as e:
            raise BradfordWhiteAuthError(f"Failed to parse redirect URL: {e}")

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange the authorization code for an access token."""
        session = await self._get_session()
        
        data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "scope": " ".join(SCOPE),
            "code": code,
            "redirect_uri": REDIRECT_URI,
        }

        async with session.post(TOKEN_URL, data=data) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise BradfordWhiteAuthError(f"Token exchange failed: {resp.status} - {text}")
            
            return await resp.json()

    async def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh the access token."""
        session = await self._get_session()
        
        data = {
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "refresh_token": refresh_token,
            "scope": " ".join(SCOPE),
        }
        
        async with session.post(TOKEN_URL, data=data) as resp:
             if resp.status != 200:
                _LOGGER.error(f"Failed to refresh token: {resp.status} - {await resp.text()}")
                raise BradfordWhiteAuthError("Failed to refresh token")
             
             data = await resp.json()
             _LOGGER.debug(f"Refresh response keys: {data.keys()}") 
             return data
    
    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()
