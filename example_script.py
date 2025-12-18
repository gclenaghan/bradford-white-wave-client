import asyncio
import json

from bradford_white_wave_client import BradfordWhiteClient

async def main():
    # Load Credentials
    try:
        with open(".credentials.json") as f:
            creds = json.load(f)
            refresh_token = creds.get("refresh_token")
    except FileNotFoundError:
        print("Please create '.credentials.json' with 'refresh_token' using get_tokens.py.")
        return

    # test with refresh token if available
    if refresh_token:
        print("Authenticating with Refresh Token...")
        client = BradfordWhiteClient(refresh_token=refresh_token)
    else:
        print("No refresh token found. Please create '.credentials.json' with 'refresh_token'.")
        return
    
    # Auto-authenticates on first request
    devices = await client.list_devices()
    
    for device in devices:
        print(f"\n--- Device: {device.friendly_name} ({device.mac_address}) ---")
        
        # Get full status
        try:
            full_status = await client.get_status(device.mac_address)
            print(f"Status: Mode={full_status.mode}, Setpoint={full_status.setpoint_fahrenheit}°F")
        except Exception as e:
            print(f"Failed to get status: {e}")

        # Get Energy Usage (hourly)
        try:
            energy = await client.get_energy_usage(device.mac_address)
            if not energy:
                print("Energy Usage: No data returned")
            for e in energy:
                print(f"Energy Usage: {e.total_energy} kWh at {e.timestamp}")
        except Exception as e:
            print(f"Failed to get energy usage: {e}")

if __name__ == "__main__":
    asyncio.run(main())
