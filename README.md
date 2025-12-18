# Bradford White Wave Client

A robust, asynchronous Python client library for the Bradford White WaveAPI.
Designed for Home Assistant integration and general automation tasks.


## Authentication

Since the automatic authentication flow mimics a browser and can be fragile, you may prefer to manually retrieve a Refresh Token once and use that. Refresh tokens typically last for a long time (weeks/months).

### Manual Token Retrieval

1. Run the included helper script:
   ```bash
   python3 get_tokens.py
   ```
2. Follow the on-screen instructions to open the login URL in your browser.
3. Login. If the browser stalls on a white page, open Developer Tools -> Network Tab.
4. Find the request to `/confirmed`, check its **Response Headers**, and copy the `Location` header URL (starting with `com.bradfordwhiteapps.bwconnect://`).
5. Paste that URL back into the script.
6. The script will output your **Refresh Token**.

### Usage with Refresh Token

```python
from bradford_white_wave_client import BradfordWhiteClient

# Initialize with just the refresh token
client = BradfordWhiteClient(refresh_token="YOUR_REFRESH_TOKEN")

async def main():
    # It will automatically fetch a fresh access token using the refresh token
    devices = await client.list_devices()
    print(devices)
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
    client = BradfordWhiteClient("your_email", "your_password")
    
    # Login
    await client.authenticate()
    
    # List devices
    devices = await client.list_devices()
    for device in devices:
        print(f"Found device: {device.friendly_name} ({device.mac_address})")
        
        # Get status
        status = await client.get_status(device.mac_address)
        print(f"Current Temp: {status.setpoint_fahrenheit}°F")
        
        # Set temperature
        # await client.set_temperature(device.mac_address, 125)

asyncio.run(main())
```

## Features
- Async/Await support using `aiohttp`
- Type-hinted with `Pydantic` models
- Handles complex Azure B2C authentication automatically
- Auto-refresh of access tokens

## Disclaimer
This is an unofficial library and is not affiliated with Bradford White.