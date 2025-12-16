"""Update Twilio webhook to ngrok URL."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Use API_BASE_URL from .env (updated with current ngrok URL)
public_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
webhook_url = f'{public_url}/inbound/voice'

sid = os.getenv('TWILIO_SID')
token = os.getenv('TWILIO_TOKEN')
phone = os.getenv('TWILIO_NUMBER')

print(f"Updating Twilio webhook...")
print(f"Phone: {phone}")
print(f"Webhook: {webhook_url}")

# Get phone number SID
r = requests.get(
    f'https://api.twilio.com/2010-04-01/Accounts/{sid}/IncomingPhoneNumbers.json',
    auth=(sid, token),
    params={'PhoneNumber': phone}
)
phone_sid = r.json()['incoming_phone_numbers'][0]['sid']
print(f"Phone SID: {phone_sid}")

# Update webhook
r = requests.post(
    f'https://api.twilio.com/2010-04-01/Accounts/{sid}/IncomingPhoneNumbers/{phone_sid}.json',
    auth=(sid, token),
    data={'VoiceUrl': webhook_url, 'VoiceMethod': 'POST'}
)

if r.status_code == 200:
    print(f"✓ Webhook updated successfully!")
else:
    print(f"✗ Error: {r.status_code} - {r.text}")
