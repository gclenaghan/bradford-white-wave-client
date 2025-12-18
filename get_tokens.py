import asyncio
import urllib.parse
import aiohttp
from bradford_white_wave_client.const import (
    AUTH_URL, 
    TOKEN_URL, 
    CLIENT_ID, 
    REDIRECT_URI, 
    SCOPE
)

async def main():
    print("=== Manual Token Retrieval ===")
    print("1. Open the following URL in your browser (Chrome/Edge/Safari):")
    print("-" * 60)
    
    # Construct clean Auth URL
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPE),
        "state": "manual_flow",
        "nonce": "manual_flow",
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    print(url)
    print("-" * 60)
    
    print("\n2. Log in with your Bradford White credentials.")
    print("3. IMPORTANT: After login, the browser might show a white page or error.")
    print("   - Open Developer Tools (F12) -> Network Tab.")
    print("   - Look for the request to '.../confirmed'.")
    print("   - Click it and look at the 'Response Headers' section.")
    print("   - Find the 'Location' header. It should start with 'com.bradfordwhiteapps.bwconnect://'")
    print("   - Copy that FULL 'Location' URL.")
    print("4. Paste that FULL URL here:")
    
    redirect_resp = input("> ").strip()
    
    # Parse code
    try:
        if "confirmed" in redirect_resp:
             print("\nError: You pasted the 'confirmed' URL, but we need the *next* URL.")
             print("The 'confirmed' page redirects to the custom scheme url.")
             print("Please check your browser network tab for the redirect to 'com.bradfordwhiteapps.bwconnect://...'")
             return

        parsed = urllib.parse.urlparse(redirect_resp)
        query_params = urllib.parse.parse_qs(parsed.query)
        code = query_params.get("code", [None])[0]
        
        if not code:
            # Maybe they pasted just the code?
            if "://" not in redirect_resp:
                code = redirect_resp
            else:
                print("Error: Could not find 'code' parameter in the URL.")
                return
    except Exception as e:
        print(f"Error parsing URL: {e}")
        return

    print(f"\nExchanging code: {code[:10]}... for tokens...")
    
    # Exchange
    token_data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "scope": " ".join(SCOPE),
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(TOKEN_URL, data=token_data) as resp:
            if resp.status != 200:
                print(f"Error: {resp.status}")
                print(await resp.text())
                return
            
            tokens = await resp.json()
            
    print("\n=== SUCCESS! ===")
    print("Here are your tokens. Save the 'refresh_token' securely.")
    print("-" * 60)
    print(f"Refresh Token: {tokens.get('refresh_token')}")
    print("-" * 60)
    print("\nYou can now use this refresh_token to initialize the client:")
    print('client = BradfordWhiteClient(refresh_token="YOUR_TOKEN")')

if __name__ == "__main__":
    asyncio.run(main())
