# DentSignal API Documentation

> **API Base URL:** `https://api.dentsignal.me` (Production) | `http://localhost:8000` (Development)

## Overview

DentSignal provides a comprehensive API for managing dental clinic AI voice agents, appointments, SMS automation, and analytics.

## Authentication

All API endpoints require JWT authentication (except webhooks from Twilio).

```bash
# Login to get a token
curl -X POST /api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@clinic.com", "password": "your-password"}'

# Response
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "email": "admin@clinic.com"
}

# Use token in subsequent requests
curl -X GET /api/clinics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📞 Inbound Calls

Voice agent handling for incoming calls.

### Create Inbound Call Session

```
POST /inbound/incoming/{clinic_id}
```

Twilio webhook endpoint. Returns TwiML to start media stream.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| clinic_id | path | Clinic ID |
| From | body | Caller phone number |
| CallSid | body | Twilio Call SID |

**Response:** TwiML XML

---

### Voice WebSocket

```
WS /inbound/ws/{call_id}
```

Twilio Media Streams WebSocket endpoint. Bridges Twilio ↔ Deepgram Voice Agent.

**Events Received:**
- `connected` - Stream connected
- `start` - Stream started with metadata
- `media` - Audio data (base64 mulaw)
- `stop` - Stream ended

**Events Sent:**
- `media` - TTS audio (base64 mulaw)
- `mark` - Audio sync markers
- `clear` - Cancel pending audio (barge-in)

---

## 📅 Calendar & Appointments

### Get Available Slots

```
GET /api/calendar/availability/{clinic_id}
```

Get available appointment slots for a date.

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| clinic_id | path | Clinic ID |
| target_date | query | Date in YYYY-MM-DD format |
| appointment_type | query | Optional: cleaning, checkup, etc. |
| duration_minutes | query | Optional: Override slot duration |

**Response:**
```json
{
  "date": "2025-12-20",
  "slots": [
    {
      "start": "2025-12-20T09:00:00",
      "end": "2025-12-20T09:30:00",
      "duration_minutes": 30,
      "provider_name": "Dr. Smith"
    }
  ],
  "slots_count": 8,
  "voice_description": "We have 8 available slots on Friday, December 20th..."
}
```

---

### Create Appointment

```
POST /api/calendar/appointments/{clinic_id}
```

Book a new appointment.

**Request Body:**
```json
{
  "patient_name": "John Smith",
  "patient_phone": "+15551234567",
  "patient_email": "john@example.com",
  "is_new_patient": true,
  "scheduled_time": "2025-12-20T09:00:00",
  "appointment_type": "cleaning",
  "duration_minutes": 60,
  "provider_name": "Dr. Smith",
  "reason": "6-month cleaning",
  "source": "phone"
}
```

**Response:**
```json
{
  "id": 123,
  "patient_name": "John Smith",
  "scheduled_time": "2025-12-20T09:00:00",
  "appointment_type": "cleaning",
  "status": "scheduled",
  "calendar_event_id": "abc123",
  "confirmation_sent": false,
  "created_at": "2025-12-19T10:30:00"
}
```

---

### List Appointments

```
GET /api/calendar/appointments/{clinic_id}
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| start_date | query | Filter: YYYY-MM-DD |
| end_date | query | Filter: YYYY-MM-DD |
| status | query | Filter: scheduled, confirmed, completed, cancelled, no_show |
| limit | query | Max results (default 50) |

---

### Update Appointment

```
PATCH /api/calendar/appointments/{clinic_id}/{appointment_id}
```

**Request Body:**
```json
{
  "scheduled_time": "2025-12-21T10:00:00",
  "status": "confirmed",
  "notes": "Patient requested morning appointment"
}
```

---

### Cancel Appointment

```
DELETE /api/calendar/appointments/{clinic_id}/{appointment_id}
```

---

### Mark No-Show

```
POST /api/calendar/appointments/{clinic_id}/{appointment_id}/no-show
```

**Request Body:**
```json
{
  "notes": "Called twice, no answer",
  "send_followup_sms": true
}
```

---

### Get No-Show Statistics

```
GET /api/calendar/no-shows/{clinic_id}/stats
```

**Response:**
```json
{
  "total_no_shows": 45,
  "this_month": 5,
  "last_month": 8,
  "follow_up_pending": 3,
  "rescheduled_count": 30,
  "no_show_rate": 4.2
}
```

---

## 📱 SMS Automation

### Send SMS

```
POST /api/sms/send
```

**Request Body:**
```json
{
  "clinic_id": 1,
  "to_phone": "+15551234567",
  "message": "Your appointment is confirmed for tomorrow at 9am."
}
```

---

### Send Appointment Reminder

```
POST /api/sms/reminder/{appointment_id}
```

Sends appointment reminder SMS to patient.

---

### Send Bulk Recall

```
POST /api/sms/recall/{clinic_id}
```

Send 6-month recall reminders to patients who haven't visited.

**Request Body:**
```json
{
  "months_since_visit": 6,
  "limit": 100
}
```

---

## 📊 Analytics

### Get Call Analytics

```
GET /api/analytics/calls/{clinic_id}
```

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| start_date | query | YYYY-MM-DD |
| end_date | query | YYYY-MM-DD |

**Response:**
```json
{
  "total_calls": 156,
  "answered": 152,
  "missed": 4,
  "avg_duration_seconds": 185,
  "appointments_booked": 48,
  "conversion_rate": 31.5,
  "sentiment_breakdown": {
    "positive": 120,
    "neutral": 28,
    "negative": 4
  },
  "peak_hours": ["10:00", "14:00", "16:00"],
  "common_intents": [
    {"intent": "book_appointment", "count": 89},
    {"intent": "reschedule", "count": 23},
    {"intent": "insurance_question", "count": 15}
  ]
}
```

---

### Get Daily Summary

```
GET /api/analytics/summary/{clinic_id}
```

Daily summary for dashboard display.

---

### Get Peak Hours

```
GET /api/analytics/peak-hours/{clinic_id}
```

Call volume by hour of day.

---

## 🏥 Clinic Management

### List Clinics

```
GET /api/clinics
```

List all clinics (admin only).

---

### Create Clinic

```
POST /api/clinics
```

**Request Body:**
```json
{
  "name": "Sunny Smiles Dental",
  "phone": "+15551234567",
  "address": "123 Main St, City, ST 12345",
  "owner_email": "owner@sunnysmiles.com",
  "timezone": "America/New_York",
  "business_hours": {
    "monday": {"start": "09:00", "end": "17:00"},
    "tuesday": {"start": "09:00", "end": "17:00"}
  }
}
```

---

### Update Clinic Settings

```
PATCH /api/clinics/{clinic_id}
```

Update clinic configuration including AI voice settings.

**Request Body:**
```json
{
  "agent_name": "Sophie",
  "agent_voice": "aura-asteria-en",
  "custom_instructions": "Always mention our new patient special: $99 cleaning",
  "forwarding_enabled": true,
  "forwarding_number": "+15559876543"
}
```

---

## 🔒 Webhooks

### Twilio Call Status

```
POST /inbound/status/{call_id}
```

Twilio status callback webhook. Automatically handled.

### Twilio SMS Webhook

```
POST /twilio/sms/webhook
```

Handle incoming SMS replies from patients.

---

## ⚠️ Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message here",
  "code": "ERROR_CODE"
}
```

**Common Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `NOT_FOUND` | 404 | Resource not found |
| `UNAUTHORIZED` | 401 | Invalid or missing token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `VALIDATION_ERROR` | 422 | Invalid request data |
| `CONFLICT` | 409 | Resource conflict (e.g., time slot taken) |
| `RATE_LIMITED` | 429 | Too many requests |

---

## 🔧 Rate Limits

| Endpoint Type | Limit |
|--------------|-------|
| API Calls | 100/minute per clinic |
| SMS Sending | 10/minute per clinic |
| Bulk Operations | 5/minute per clinic |

---

## 📞 WebSocket Error Codes

| Code | Description |
|------|-------------|
| 1000 | Normal closure |
| 1001 | Going away (server shutdown) |
| 1008 | Policy violation |
| 1011 | Server error |
| 4000 | Clinic not found |
| 4001 | Call not found |
| 4002 | Deepgram connection failed |

---

## Environment Variables

```bash
# Required
DATABASE_URL=sqlite:///./dev.db
JWT_SECRET=your-secret-key
DEEPGRAM_API_KEY=dg_xxx
TWILIO_SID=ACxxx
TWILIO_TOKEN=xxx
TWILIO_NUMBER=+15551234567

# Optional
OPENAI_API_KEY=sk-xxx          # For AI summaries
GOOGLE_API_KEY=xxx             # For Gemini analytics
TELEPHONY_MODE=SIMULATED       # or TWILIO for production
API_BASE_URL=https://api.dentsignal.me
WS_BASE_URL=wss://api.dentsignal.me
```

---

## Interactive Docs

When running locally, access interactive API docs at:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
