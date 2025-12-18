# Bradford White Wave Client

A robust, asynchronous Python client library for the Bradford White WaveAPI.
Designed for Home Assistant integration and general automation tasks.

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