# Bradford White Wave Client

A Python client library for the Bradford White Wave API for water heaters. The "Wave"
platform is new and separate from the previous "Connect" platform. For instance the original Aerotherm uses an
optional "Connect" module add-on, while the Aerotherm G2 has built-in connectivity to the "Wave" platform.

This library is designed for use in a Home Assistant integration and general automation tasks.

To build this I took some inspiration from the [bradford-white-connect-client](https://github.com/ablyler/bradford_white_connect_client)
library and did some digging into how the new app works.

## Authentication

Some manual steps are required to authenticate with the API, since for the time being I have been unable to fully automate the process.

1. Run the example script:
   ```bash
   python example_script.py
   ```
2. The script will generate a login URL. Open it in your browser.
3. Log in with your Bradford White Wave credentials.
4. The browser will recieve a redirect, but (at least for Firefox) it will fail to follow this redirect and show an error page.
5. Open the network tab in your browser's development tools and refresh the page. You'll see the failed redirect response. Look for the location: header starting with `com.bradfordwhiteapps.bwconnect://` in the response.
6. Copy the full url and paste it back into the script terminal.
7. The script will save your credentials to `.credentials.json` so future runs of the script will skip the above steps (this file is in .gitignore).

## Usage

Once you have a `refresh_token`, you can initialize the client:

```python
client = BradfordWhiteClient(refresh_token="YOUR_REFRESH_TOKEN")
await client.authenticate()
```

From there, there are several methods available:

```python
# List devices
await client.list_devices()

# Get status
await client.get_status("MAC_ADDRESS")

# Get energy usage
await client.get_energy("MAC_ADDRESS", "hourly")

# Set temperature
await client.set_temperature("MAC_ADDRESS", 120)

# Set mode
from bradford_white_wave_client.models import BradfordWhiteMode
await client.set_mode("MAC_ADDRESS", BradfordWhiteMode.HEAT_PUMP)
```

## Installation

```bash
pip install bradford-white-wave-client
```

## Features
- Async/Await support using `aiohttp`
- Type-hinted with `Pydantic` models
- Auto-refresh of access tokens

## Disclaimers
- This is an unofficial library and is not affiliated with Bradford White.
- I have only tested with an Aerotherm G2.
- This is largely written in "collaboration" with Gemini, though I have manually reviewed the code and verified the flows.
