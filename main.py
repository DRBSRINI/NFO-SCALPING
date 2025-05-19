import os
import requests

print("🚀 Bot Started Successfully!")
from dhanhq import dhanhq

# Your credentials
client_id = "1103110998"
access_token = "eyJ0eX...bDLTsQ"

# Initialize SDK
dhan = dhanhq(client_id, access_token)

# Fetch Profile - CORRECT METHOD
try:
    profile = dhan.get_profile()
    print("✅ Profile:")
    print(profile)
except Exception as e:
    print("❌ Error fetching profile:", e)

# Read credentials from Render environment variables
CLIENT_ID = os.environ.get("CLIENT_ID")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
APP_NAME = os.environ.get("APP_NAME")

# Print for debug
print("\U0001F194 Client ID:", CLIENT_ID)
print("\U0001F511 Access Token:", ACCESS_TOKEN[:6] + "..." + ACCESS_TOKEN[-6:])
print("\U0001F4E6 App Name:", APP_NAME)

# Make a test API call to Dhan Profile endpoint
try:
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    url = f"https://api.dhan.co/accounts/{CLIENT_ID}/profile"
    response = requests.get(url, headers=headers)

    print("\U0001F4E1 Status Code:", response.status_code)
    print("\U0001F4EC Response:", response.json())

except Exception as e:
    print("❌ API call failed:", e)
