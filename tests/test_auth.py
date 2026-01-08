import pytest
import urllib.parse
from aioresponses import aioresponses
from bradford_white_wave_client.auth import BradfordWhiteAuth, BradfordWhiteAuthError
from bradford_white_wave_client.const import CLIENT_ID, REDIRECT_URI, TOKEN_URL


@pytest.fixture
def auth():
    return BradfordWhiteAuth()


def test_generate_auth_url(auth):
    state = "test_state"
    nonce = "test_nonce"
    url = auth.generate_auth_url(state, nonce)

    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    assert "https://consumer.bradfordwhiteapps.com" in url
    assert params["client_id"][0] == CLIENT_ID
    assert params["redirect_uri"][0] == REDIRECT_URI
    assert params["state"][0] == state
    assert params["nonce"][0] == nonce
    assert params["response_type"][0] == "code"
    assert "openid" in params["scope"][0]


def test_parse_redirect_url_success():
    code = "test_auth_code"
    url = (
        f"com.bradfordwhiteapps.bwconnect://oauth/redirect?code={code}&state=test_state"
    )
    parsed_code = BradfordWhiteAuth.parse_redirect_url(url)
    assert parsed_code == code


def test_parse_redirect_url_just_code():
    code = "test_auth_code_raw_string"
    parsed_code = BradfordWhiteAuth.parse_redirect_url(code)
    assert parsed_code == code


def test_parse_redirect_url_confirmed_error():
    url = "https://consumer.bradfordwhiteapps.com/confirmed"
    with pytest.raises(BradfordWhiteAuthError, match="intermediate 'confirmed' page"):
        BradfordWhiteAuth.parse_redirect_url(url)


def test_parse_redirect_url_no_code():
    url = "com.bradfordwhiteapps.bwconnect://oauth/redirect?error=access_denied"
    with pytest.raises(BradfordWhiteAuthError, match="No 'code' parameter"):
        BradfordWhiteAuth.parse_redirect_url(url)


@pytest.mark.asyncio
async def test_exchange_code_for_token_success(auth):
    code = "test_code"
    mock_response = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "expires_in": 3600,
    }

    with aioresponses() as m:
        m.post(TOKEN_URL, payload=mock_response)

        tokens = await auth.exchange_code_for_token(code)

        assert tokens == mock_response
        await auth.close()


@pytest.mark.asyncio
async def test_exchange_code_for_token_failure(auth):
    code = "bad_code"

    with aioresponses() as m:
        m.post(TOKEN_URL, status=400, body="Bad Request")

        with pytest.raises(BradfordWhiteAuthError, match="Token exchange failed"):
            await auth.exchange_code_for_token(code)
        await auth.close()


@pytest.mark.asyncio
async def test_refresh_tokens_success(auth):
    refresh_token = "valid_refresh_token"
    mock_response = {
        "access_token": "refreshed_access_token",
        "refresh_token": "refreshed_refresh_token",
        "expires_in": 3600,
    }

    with aioresponses() as m:
        m.post(TOKEN_URL, payload=mock_response)

        tokens = await auth.refresh_tokens(refresh_token)

        assert tokens == mock_response
        await auth.close()
