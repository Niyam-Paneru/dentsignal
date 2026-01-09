# Twilio Phone Number Setup Guide

## Quick Reference: Webhook URLs

When a new clinic number is purchased, it needs these webhooks:

| Webhook Type | URL | Method |
|--------------|-----|--------|
| **Voice** | `{API_BASE_URL}/inbound/voice` | POST |
| **SMS** | `{API_BASE_URL}/api/sms/inbound` | POST |
| **Status Callback** | `{API_BASE_URL}/twilio/status` | POST |

Replace `{API_BASE_URL}` with your actual domain (e.g., `https://api.dentsignal.com`)

---

## Option A: Automated (Recommended)

Use the `provision_clinic_number()` function - it does everything automatically!

```python
from twilio_service import provision_clinic_number

# Buy a number with area code
result = provision_clinic_number(
    clinic_id=123,
    area_code="512",  # Austin, TX
    friendly_name="Austin Dental Clinic"
)

print(result)
# {
#     'success': True,
#     'phone_number': '+15125551234',
#     'sid': 'PNxxxxx',
#     'webhooks': {
#         'voice': 'https://api.dentsignal.com/inbound/voice',
#         'sms': 'https://api.dentsignal.com/api/sms/inbound'
#     }
# }
```

Or via API:
```bash
POST /api/admin/provision-number
{
    "clinic_id": 123,
    "area_code": "512",
    "friendly_name": "Austin Dental"
}
```

---

## Option B: Manual (Twilio Console)

If you need to set up manually:

1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. Click on the phone number
3. Scroll to **Voice Configuration**:
   - Webhook URL: `https://your-api.com/inbound/voice`
   - Method: POST
4. Scroll to **Messaging Configuration**:
   - Webhook URL: `https://your-api.com/api/sms/inbound`
   - Method: POST
5. Click **Save**

---

## Useful Functions in twilio_service.py

| Function | Purpose |
|----------|---------|
| `list_available_numbers(area_code)` | Find numbers to buy |
| `provision_clinic_number(clinic_id, area_code)` | Buy + auto-configure |
| `update_number_webhooks(phone_sid)` | Fix existing number |
| `list_clinic_numbers()` | Audit all your numbers |
| `release_number(phone_sid)` | Delete when clinic cancels |

---

## Checklist for New Clinic Onboarding

- [ ] Buy Twilio number with `provision_clinic_number()`
- [ ] Save phone number to `clients.twilio_number` in database
- [ ] Save SID to clinic record (for future updates/release)
- [ ] Test inbound call → should trigger AI agent
- [ ] Test inbound SMS → should process patient replies
- [ ] Update clinic's Google/website with new number

---

## Common Issues

### "Webhook not receiving requests"
- Check API_BASE_URL is publicly accessible (not localhost)
- Verify ngrok tunnel is running (for dev)
- Check Twilio error logs in console

### "SMS not being processed"
- Verify SMS webhook is `/api/sms/inbound` (not `/sms/inbound`)
- Check phone has SMS capability enabled

### "Voice calls failing"
- Verify voice webhook is `/inbound/voice`
- Check TwiML is valid in response
