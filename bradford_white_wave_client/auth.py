import logging
import re
import json
import urllib.parse
import aiohttp
import secrets
from bs4 import BeautifulSoup
from typing import Dict, Optional
from .const import (
    AUTH_URL, 
    TOKEN_URL, 
    CLIENT_ID, 
    REDIRECT_URI, 
    SCOPE, 
    USER_AGENT,
    SELF_ASSERTED_URL,
    CONFIRMED_URL
)
from .exceptions import BradfordWhiteAuthError

_LOGGER = logging.getLogger(__name__)

class BradfordWhiteAuth:
    """Handle Bradford White Authentication."""

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            # Debug Trace Config
            async def on_request_start(session, trace_config_ctx, params):
                _LOGGER.debug(f">> Request: {params.method} {params.url}")
                _LOGGER.debug(f">> Headers: {params.headers}")
                # Body isn't easily available in params here without reading it, preventing stream consumption issues
                # But we can verify headers/url

            async def on_request_end(session, trace_config_ctx, params):
                _LOGGER.debug(f"<< Response: {params.response.status}")
                _LOGGER.debug(f"<< Headers: {params.response.headers}")

            trace_config = aiohttp.TraceConfig()
            trace_config.on_request_start.append(on_request_start)
            trace_config.on_request_end.append(on_request_end)

            self._session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36"
                },
                cookie_jar=aiohttp.CookieJar(unsafe=True),
                trace_configs=[trace_config] 
            )
        return self._session

    async def authenticate(self) -> str:
        """Authenticate using Azure B2C scraping and return access token."""
        session = await self._get_session()
        _LOGGER.info("Starting authentication flow for %s", self.email)

        # 1. Start Auth Flow - GET Authorize URL
        params = {
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(SCOPE),
            "scope": " ".join(SCOPE),
            "state": secrets.token_urlsafe(16),
            "nonce": secrets.token_urlsafe(16),
        }
        
        async with session.get(AUTH_URL, params=params) as resp:
            _LOGGER.debug("Fetching auth page: %s", resp.url)
            if resp.status != 200:
                raise BradfordWhiteAuthError(f"Failed to load login page: {resp.status}")
            html = await resp.text()

        # 2. Parse HTML for CSRF and State
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract SETTINGS json from script
        # Pattern looks for: var SETTINGS = { ... };
        script_pattern = re.compile(r"var SETTINGS = ({.*?});", re.DOTALL)
        match = script_pattern.search(html)
        
        if not match:
             raise BradfordWhiteAuthError("Could not find SETTINGS in login page.")
        
        try:
            settings_str = match.group(1)
            # JSON in JS might not be strict JSON (keys might not be quoted), 
            # but usually in these B2C templates they are. 
            # If not, we might need a more robust parser or regex for specific keys.
            settings = json.loads(settings_str)
            
            csrf = settings.get("csrf")
            trans_id = settings.get("transId")
            _LOGGER.debug("Parsed CSRF: %s, transId: %s", csrf, trans_id)
            
        except json.JSONDecodeError:
            # Fallback regex if json.loads fails (e.g. trailing commas etc)
            csrf = re.search(r'"csrf":\s*"([^"]+)"', settings_str).group(1)
            trans_id = re.search(r'"transId":\s*"([^"]+)"', settings_str).group(1)

        if not csrf or not trans_id:
            raise BradfordWhiteAuthError("Could not extract CSRF or transId.")

        # 3. Submit Credentials - POST SelfAsserted
        # Parse trans_id to get actual 'tx' value if it's in format "StateProperties=..."
        # In the provided example: "StateProperties=eyJ..."
        # But the endpoint usually expects just the value of transId or tx in query params.
        # Let's check typical B2C requests. Usually query param is `tx`.
        
        # Careful: transId often contains "StateProperties=" prefix which might need stripped 
        # OR passed as is. In the example provided by user:
        # "transId": "StateProperties=eyJ..."
        # We will pass it as query param `tx` AND `p` (policy).
        
        form_data = {
            "request_type": "RESPONSE",
            "email": self.email,
            "password": self.password,
        }
        
        headers = {
            "X-CSRF-TOKEN": csrf,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": f"https://{urllib.parse.urlparse(AUTH_URL).netloc}",
            "Referer": str(resp.url), 
            # Client Hints
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
        }
        
        # Extract just the token part if needed, but B2C often takes the whole string as 'tx'
        tx_val = trans_id
        
        post_params = {
            "tx": tx_val,
            "p": "B2C_1_Wave_SignIn" # Policy
        }

        _LOGGER.debug("Submitting credentials to %s with params %s", SELF_ASSERTED_URL, post_params)

        # Manually encode data to ensure it matches the application/x-www-form-urlencoded content type exactly
        encoded_data = urllib.parse.urlencode(form_data)

        async with session.post(
            SELF_ASSERTED_URL, 
            data=encoded_data, 
            headers=headers, 
            params=post_params
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                _LOGGER.error("Login submission failed: %s - %s", resp.status, text)
                raise BradfordWhiteAuthError(f"Login submission failed: {resp.status} - {text}")
            
            resp_json = await resp.json()
            # B2C usually returns: {"status":"200", "statusMessage":"..."}
            if resp_json.get("status") != "200":
                 _LOGGER.error("Login logic failure: %s", resp_json)
                 raise BradfordWhiteAuthError(f"Login failed: {resp_json}")

        # 4. Confirm/Polling phase (often required to trigger the redirect)
        # Sometimes sending credentials returns 200 OK but we need to hit the "CombinedSigninAndSignup/confirmed" endpoint
        # OR just hitting the Authorize URL again with the same cookies will now redirect us.
        # Let's try hitting the Authorize URL again (standard B2C behavior).
        # But first, check if there was a "confirmed" endpoint call in the logs? 
        # The prompt mentioned "Handle Redirect: If successful, the server redirects...". 
        # The response to SelfAsserted is usually JSON 200.
        # Then the client JS triggers a redirect/navigation.
        # We simulate this by hitting the 'CombinedSigninAndSignup/confirmed' or just 'authorize' again.
        
        # Let's try calling the `confirmed` endpoint as it mimics the "next" step
        async with session.get(
            CONFIRMED_URL,
            params={
                "csrf": csrf,
                "tx": tx_val,
                "p": "B2C_1_Wave_SignIn"
            },
            allow_redirects=False 
        ) as resp:
            _LOGGER.debug("Checking confirmation URL: %s", resp.url)
            # We expect a 302 redirect to the app's redirect_uri
            location = resp.headers.get("Location")
            
            if not location:
                # Fallback: try hitting the AUTH_URL again
                 async with session.get(AUTH_URL, params=params, allow_redirects=False) as auth_resp:
                    location = auth_resp.headers.get("Location")

            if not location or REDIRECT_URI not in location:
                 raise BradfordWhiteAuthError("Failed to get redirect with authorization code.")

        # 5. Extract Code
        parsed = urllib.parse.urlparse(location)
        query_params = urllib.parse.parse_qs(parsed.query)
        code = query_params.get("code", [None])[0]

        if not code:
            raise BradfordWhiteAuthError("No code found in redirect URL.")

        # 6. Exchange Code for Token
        token_data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "scope": " ".join(SCOPE),
            "code": code,
            "redirect_uri": REDIRECT_URI,
        }



        _LOGGER.debug("Exchanging code for tokens")
        async with session.post(TOKEN_URL, data=token_data) as resp:
            if resp.status != 200:
                raise BradfordWhiteAuthError(f"Token exchange failed: {await resp.text()}")
            
            tokens = await resp.json()
            _LOGGER.info("Successfully authenticated")
            return tokens

    async def refresh_tokens(self, refresh_token: str) -> dict:
        """Refresh the access token."""
        session = await self._get_session()
        data = {
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "refresh_token": refresh_token,
            "scope": " ".join(SCOPE) 
        }
        
        async with session.post(TOKEN_URL, data=data) as resp:
             if resp.status != 200:
                raise BradfordWhiteAuthError("Failed to refresh token")
             
             data = await resp.json()
             _LOGGER.debug(f"Refresh response: {data.keys()}") 
             return data
