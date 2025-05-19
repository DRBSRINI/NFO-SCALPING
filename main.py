import os
import requests
import os
from dhanhq import dhanhq

print("🚀 Bot Started Successfully!")

# Load environment variables
client_id = os.environ.get("CLIENT_ID")
access_token = os.environ.get("ACCESS_TOKEN")
app_name = os.environ.get("APP_NAME")

# Debug prints
print("🆔 Client ID:", client_id)
print("🔑 Access Token:", access_token[:6] + "..." + access_token[-6:])
print("📦 App Name:", app_name)

# Initialize SDK
dhan = dhanhq(client_id=client_id, access_token=access_token)

# ✅ Correct method to fetch user details
try:
    profile = dhan.get_client_master()
    print("📬 Profile Data:", profile)
except Exception as e:
    print("❌ Failed to fetch profile:", e)




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
