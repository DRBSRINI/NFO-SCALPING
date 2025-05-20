import os
import requests

print("🚀 Bot Started Successfully!")

# Load credentials
CLIENT_ID = os.getenv("CLIENT_ID", "1103110998")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "paste_your_access_token_here")  # Replace this token or set it in environment

print("🆔 Client ID:", CLIENT_ID)
print("🔑 Access Token:", ACCESS_TOKEN[:6] + "..." + ACCESS_TOKEN[-6:])

# Set headers
headers = {
    "access-token": ACCESS_TOKEN,
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# ✅ Only use valid endpoint from API docs
url = "https://api.dhan.co/v2/profile"

# Call the endpoint
try:
    response = requests.get(url, headers=headers)
    print("📡 Status Code:", response.status_code)

    if response.status_code == 200:
        print("📬 Profile Data:", response.json())
    else:
        print("❌ Error:", response.text)

except Exception as e:
    print("❌ Exception occurred:", e)
