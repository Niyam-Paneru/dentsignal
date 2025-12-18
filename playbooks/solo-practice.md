# Solo Practitioner Playbook

**Practice Profile:** 1 dentist, 1-3 staff, typically 1 location

---

## Configuration Settings

### Business Hours
```json
{
  "timezone": "America/New_York",
  "hours": {
    "monday": {"open": "09:00", "close": "17:00"},
    "tuesday": {"open": "09:00", "close": "17:00"},
    "wednesday": {"open": "09:00", "close": "17:00"},
    "thursday": {"open": "09:00", "close": "17:00"},
    "friday": {"open": "09:00", "close": "14:00"},
    "saturday": "closed",
    "sunday": "closed"
  },
  "lunch_break": {"start": "12:00", "end": "13:00"}
}
```

### Agent Personality
```json
{
  "agent_name": "Sarah",
  "voice": "aura-athena-en",
  "tone": "warm_professional",
  "personality_notes": "Personal, remember the doctor's name, small-town feel"
}
```

---

## Greeting Scripts

### During Hours
```
"Thank you for calling [Practice Name], this is [Agent Name]. 
Dr. [Doctor Name]'s office, how may I help you today?"
```

### After Hours
```
"Thank you for calling [Practice Name]. Our office is currently closed. 
Our regular hours are [hours]. 

If this is a dental emergency, press 1 and I'll take your information 
for Dr. [Doctor Name] to call you back as soon as possible.

For all other inquiries, I can help you schedule an appointment or 
leave a message."
```

### Lunch Break
```
"Thank you for calling [Practice Name]. Our team is on lunch break 
right now, but I'd be happy to help. Are you calling to schedule 
an appointment, or is this regarding something else?"
```

---

## Common Scenarios

### New Patient Inquiry
**Trigger phrases:** "new patient", "never been there", "first visit"

**Response flow:**
1. Welcome warmly: "Wonderful! We'd love to have you as a patient."
2. Ask how they heard about the practice (tracking)
3. Collect basic info: name, phone, insurance (optional)
4. Offer next available appointment
5. Mention new patient forms: "We'll email forms ahead of time"

**Script:**
```
"Wonderful! We always love meeting new patients. 

Just a few quick questions: Can I get your name and the best phone 
number to reach you?

[After collecting]

Perfect, [Name]. Do you have dental insurance, or will this be 
self-pay? 

[After insurance info]

Great. Our next available appointment for a new patient exam is 
[date/time]. Would that work for you?"
```

### Appointment Rescheduling
**Trigger phrases:** "reschedule", "change my appointment", "can't make it"

**Response flow:**
1. Pull up context (if available)
2. Express understanding
3. Offer alternatives
4. Confirm new time
5. Send updated confirmation

**Script:**
```
"No problem at all - things come up! Let me help you find a new time.

Do you have a preference for morning or afternoon? Any particular 
day of the week?

[After preferences]

I have [option 1] or [option 2]. Which works better for you?"
```

### Emergency Call
**Trigger phrases:** "emergency", "severe pain", "knocked out tooth", "swelling", "bleeding"

**Response flow:**
1. Express concern
2. Assess severity
3. Collect callback number
4. Promise urgent response
5. Flag for immediate notification

**Script:**
```
"I'm sorry you're dealing with this. Let me get your information 
so Dr. [Doctor Name] can call you right back.

Can you tell me briefly what's happening?

[Listen and note symptoms]

What's the best number to reach you right now?

[Collect number]

Thank you. I'm marking this as urgent and Dr. [Doctor Name] will 
call you back as soon as possible, usually within 15-30 minutes. 
Is there anything else I should note for the doctor?"
```

---

## Transfer Rules

| Scenario | Action |
|----------|--------|
| Patient asks for specific person | Transfer if available |
| Billing/Insurance question | Transfer to front desk |
| Medical emergency | Transfer immediately |
| Appointment request | Handle, don't transfer |
| New patient inquiry | Handle, don't transfer |
| Complaint | Transfer to manager/owner |

---

## SMS Templates

### Appointment Confirmation
```
Hi [Name]! Your appointment with Dr. [Doctor Name] at [Practice Name] 
is confirmed for [Date] at [Time]. 

Reply C to confirm or R to reschedule.
```

### Day-Before Reminder
```
Reminder: Your appointment at [Practice Name] is tomorrow, [Date] 
at [Time]. 

Please arrive 10 minutes early. If you need to reschedule, call 
us at [Phone].
```

### Post-Visit Follow-Up
```
Hi [Name], thanks for visiting [Practice Name] today! If you have 
any questions about your visit, we're here to help. 

- Dr. [Doctor Name] & Team
```

---

## Integration Notes

### Common PMS for Solo Practices
- **Dentrix** - Most common, calendar sync available
- **Eaglesoft** - Second most common
- **Open Dental** - Growing in popularity, open API
- **Curve Dental** - Cloud-based option

### Solo Practice Considerations
- Usually no IT staff → setup must be simple
- Doctor often checks own voicemail → morning summary email critical
- Personal relationships matter → agent should feel personal, not corporate
- Flexible hours → may need easy way to update availability

---

## Metrics to Track

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| Answer rate | >95% | Solo practices lose more per missed call |
| New patient booking rate | >70% | Critical for growth |
| Avg call duration | <3 min | Don't waste patient time |
| After-hours calls | Track | May indicate need for extended hours |
| Emergency flags | Track | Monitor for patterns |

---

## Common Customizations

1. **Personal greeting** - Use doctor's name, not just practice name
2. **Vacation mode** - Easy toggle for when doctor is out
3. **Morning summary** - Email to doctor's personal email
4. **VIP patient list** - Certain patients always transfer
5. **Referral tracking** - "How did you hear about us?"
