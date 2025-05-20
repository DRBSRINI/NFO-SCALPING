import os
import requests

print("🚀 Bot Started Successfully!")

# ✅ Load required environment variables
CLIENT_ID = os.environ.get("CLIENT_ID", "1103110998")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzQ4OTU3MzE1LCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMzExMDk5OCJ9.63JJ5I2xkyChgmHYg4Nl3zRkDz5SJl4AWmJljJ0rgUkGVxnQ6z3uUDZM47dQNSKaiimygNJz5jkVHBqyoDe1aw")

# ✅ Create DHAN object (you can later use this with a class/method)
DHAN = (CLIENT_ID, ACCESS_TOKEN)  # Placeholder structure for your use

# ✅ Print only important info
print("🆔 Client ID:", CLIENT_ID)
print("🔑 Access Token:", ACCESS_TOKEN[:6] + "..." + ACCESS_TOKEN[-6:])

# ✅ Correct headers for DhanHQ
headers = {
    "access-token": ACCESS_TOKEN,
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# ✅ API call to get profile
try:
    response = requests.get("https://api.dhan.co/v2/profile", headers=headers)
    print("📡 Status Code:", response.status_code)
    if response.status_code == 200:
        print("📬 Profile Data:", response.json())
    else:
        print("❌ Error:", response.text)
except Exception as e:
    print("❌ Exception occurred:", e) 
    
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
