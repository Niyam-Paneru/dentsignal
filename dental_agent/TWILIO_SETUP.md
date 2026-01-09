# Twilio Phone Number Setup Guide

## ⚡ TL;DR - It's Automated!

Just call the API endpoint - everything is configured automatically:

```bash
POST /api/admin/provision-number
{
    "clinic_id": 123,
    "area_code": "512"
}
```

Done! Voice + SMS webhooks are set up. No manual steps needed.

---

## Quick Reference: Webhook URLs (For Troubleshooting Only)

If you ever need to check or fix webhooks manually:

| Webhook Type | URL | Method |
|--------------|-----|--------|
| **Voice** | `{API_BASE_URL}/inbound/voice` | POST |
| **SMS** | `{API_BASE_URL}/api/sms/inbound` | POST |
| **Status Callback** | `{API_BASE_URL}/twilio/status` | POST |

---

## API Endpoints for Phone Management

| Endpoint | Purpose |
|----------|---------|
| `GET /api/admin/available-numbers?area_code=512` | Find numbers to buy |
| `POST /api/admin/provision-number` | **Buy + auto-configure** ✨ |
| `GET /api/admin/clinic-numbers` | List all your numbers |
| `POST /api/admin/fix-webhooks/{sid}` | Fix broken webhooks |
| `DELETE /api/admin/release-number/{sid}` | Release when clinic cancels |

---

## Checklist for New Clinic Onboarding

- [ ] Call `POST /api/admin/provision-number` with clinic_id and area_code
- [ ] Number is automatically saved to database
- [ ] Test inbound call → should trigger AI agent
- [ ] Test inbound SMS → should process patient replies
- [ ] Give clinic their new number for website/Google

---

## Troubleshooting

### "Webhook not receiving requests"
- Check API_BASE_URL is publicly accessible (not localhost)
- Verify ngrok tunnel is running (for dev)
- Check Twilio error logs in console

### "SMS not being processed"
- Run `POST /api/admin/fix-webhooks/{phone_sid}` to reset webhooks
- Verify phone has SMS capability

### "Voice calls failing"  
- Run `POST /api/admin/fix-webhooks/{phone_sid}` to reset webhooks
- Check TwiML response is valid
