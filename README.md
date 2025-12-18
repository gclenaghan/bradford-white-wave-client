# Bradford White Wave Client

A robust, asynchronous Python client library for the Bradford White WaveAPI.
Designed for Home Assistant integration and general automation tasks.


## Authentication

Bradford White uses Azure AD B2C which requires a manual step to obtain the initial credentials due to security protections.

### Initial Setup

1. Run the example script:
   ```bash
   python example_script.py
   ```
2. The script will generate a login URL. Open it in your browser.
3. Log in with your Bradford White credentials.
4. You will be redirected to a page that starts with `com.bradfordwhiteapps.bwconnect://`. **Copy this full URL**.
5. Paste the URL back into the script terminal.
6. The script will save your credentials to `.credentials.json` for future use.

### Usage in Code

Once you have a `refresh_token`, you can initialize the client:

```python
client = BradfordWhiteClient(refresh_token="YOUR_REFRESH_TOKEN")
await client.authenticate()
```

## Installation

```bash
pip install bradford-white-wave-client
```

## Usage

```python
import asyncio
from bradford_white_wave_client import BradfordWhiteClient

async def main():
    # Initialize with refresh token
    client = BradfordWhiteClient(refresh_token="YOUR_REFRESH_TOKEN")
    
    # List devices (auto-authenticates)
    devices = await client.list_devices()
    for device in devices:
        print(f"Found device: {device.friendly_name} ({device.mac_address})")
        
        # Get status
        status = await client.get_status(device.mac_address)
        print(f"Current Temp: {status.setpoint_fahrenheit}°F")

asyncio.run(main())
```

## Features
- Async/Await support using `aiohttp`
- Type-hinted with `Pydantic` models
- Handles complex Azure B2C authentication automatically
- Auto-refresh of access tokens

## Disclaimer
This is an unofficial library and is not affiliated with Bradford White.