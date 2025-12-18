# Project Context: Bradford White Wave Client

## Overview
This is an asynchronous Python client library for the Bradford White Wave API (Azure AD B2C authenticaton). It allows control and monitoring of smart water heaters (specifically tested with Aerotherm G2).

## Authentication Flow (CRITICAL)
**We DO NOT use email/password automation.**
A previous attempt to scrape the B2C login page failed due to inability to successfully navigate the web login flow.

**Current "Robust" Flow:**
1.  **Manual Initial Login**: The user runs `example_script.py`.
2.  **Browser Interaction**: The script outputs a URL. The user logs in via their browser.
3.  **Code Extraction**: The user copies the final redirect URL (starting with `com.bradfordwhiteapps.bwconnect://`) back into the script.
4.  **Token Exchange**: The script swaps the auth code for a `refresh_token` and saves it to `.credentials.json`.
5.  **Automated Refresh**: The `BradfordWhiteClient` takes this `refresh_token` and automatically maintains a valid `access_token` during runtime.

### Key Auth Files
-   `auth.py`: Contains **pure OAuth logic** (`generate_auth_url`, `exchange_code_for_token`, `refresh_tokens`). No scraping.
-   `client.py`: Uses `auth.py` to transparently handle token lifecycle.

## API Details & Quirks
-   **Base URL**: `https://gw.prdapi.bradfordwhiteapps.com`
-   **Auth URL**: `https://consumer.bradfordwhiteapps.com/...`
-   **Client ID**: `7899415d-1c23-46d8-8a79-4c15ed5f7f22`
-   **Redirect URI**: `com.bradfordwhiteapps.bwconnect://oauth/redirect`
-   **Policy**: `B2C_1_Wave_SignIn`
-   **Device List**: The `/wave/getApplianceList` endpoint returns a dict wrapping a list: `{ "appliances": [...] }`.
-   **Energy Usage**: `get_energy_usage` supports view types: `hourly`, `daily`, `weekly`, `monthly`. Returns detailed lists including `total_energy` and `heat_pump_energy`.

## Useful Commands
-   **Run Interactive Setup / Test**:
    ```bash
    python example_script.py
    ```
    (This script checks for `.credentials.json` and guides the user if missing, then dumps device data).

## Future Tasks
-   **Publishing**: The `pyproject.toml` is set up for `hatch`. Ready to build and publish to PyPI.
-   **Home Assistant**: The library design (async, separation of config flow logic in `auth.py`) is tailored for easy integration into a Home Assistant Config Flow.
