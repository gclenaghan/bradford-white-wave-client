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
        refresh_token = None

    client = BradfordWhiteClient(refresh_token=refresh_token)

    # test with refresh token if available
    if refresh_token:
        print("Authenticating with Saved Refresh Token...")
    else:
        print("No refresh token found. Starting interactive setup...")
        # Start OAuth Flow
        auth_url = client.get_authorization_url()
        print("\n1. Open this URL in your browser:")
        print("-" * 60)
        print(auth_url)
        print("-" * 60)
        print("\n2. Log in and paste the FULL redirected URL here (starting with com.bradfordwhiteapps.bwconnect://):")
        
        redirect_url = input("> ").strip()
        
        try:
            print("Exchanging code for tokens...")
            await client.authenticate_with_code(redirect_url)
            
            # Save new token
            new_refresh = client._refresh_token
            with open(".credentials.json", "w") as f:
                json.dump({"refresh_token": new_refresh}, f, indent=2)
            print("Successfully authenticated and saved to .credentials.json!")
            
        except Exception as e:
            print(f"Authentication failed: {e}")
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
