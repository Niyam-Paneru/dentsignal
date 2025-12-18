# General/Family Practice Playbook

**Practice Profile:** 2-4 dentists, 5-15 staff, 1-2 locations, high call volume

---

## Configuration Settings

### Business Hours
```json
{
  "timezone": "America/Chicago",
  "hours": {
    "monday": {"open": "08:00", "close": "18:00"},
    "tuesday": {"open": "08:00", "close": "18:00"},
    "wednesday": {"open": "08:00", "close": "18:00"},
    "thursday": {"open": "08:00", "close": "18:00"},
    "friday": {"open": "08:00", "close": "16:00"},
    "saturday": {"open": "09:00", "close": "14:00"},
    "sunday": "closed"
  },
  "lunch_break": null
}
```
*Note: Larger practices often stagger lunches, so no universal break.*

### Agent Personality
```json
{
  "agent_name": "Alex",
  "voice": "aura-orion-en",
  "tone": "efficient_friendly",
  "personality_notes": "Professional but warm, handles volume efficiently"
}
```

---

## Greeting Scripts

### During Hours
```
"Thank you for calling [Practice Name], this is [Agent Name]. 
How may I help you today?"
```

### After Hours
```
"Thank you for calling [Practice Name]. Our office is currently closed.

Our hours are Monday through Thursday 8 AM to 6 PM, Friday 8 AM to 4 PM, 
and Saturday 9 AM to 2 PM.

If you're experiencing a dental emergency, please press 1.

Otherwise, I can help you schedule an appointment or leave a message."
```

### High Volume Mode
```
"Thank you for calling [Practice Name]. We're experiencing higher than 
usual call volume. I can help you right now - are you calling to 
schedule an appointment or something else?"
```

---

## Service Menu

General practices offer diverse services. Configure the AI to understand:

### Routine Services
- Cleanings / Prophylaxis (hygiene appointments)
- Exams / Check-ups
- X-rays
- Fillings / Restorations

### Cosmetic Services
- Whitening
- Veneers
- Bonding

### Major Services
- Crowns
- Root canals
- Extractions
- Dentures / Partials

### Specialty Services (if offered)
- Invisalign / Orthodontics
- Implants
- Sedation dentistry

**Script for service routing:**
```
"What type of appointment are you looking to schedule?

[If they're unsure]

Are you due for a cleaning and check-up, or is there something specific 
like a tooth that's bothering you?"
```

---

## Scheduling Logic

### Appointment Types & Durations
| Appointment Type | Duration | Book With |
|-----------------|----------|-----------|
| New Patient Exam | 60 min | Any dentist |
| Recall/Cleaning | 60 min | Hygienist |
| Limited Exam (problem) | 30 min | Any dentist |
| Filling (1-2 surfaces) | 45 min | Any dentist |
| Crown Prep | 90 min | Any dentist |
| Emergency | 30 min | Next available |

### Priority Rules
1. Emergencies → Same day, any available slot
2. New patients → Within 1 week (don't lose them)
3. Treatment → Within 2 weeks of diagnosis
4. Recall → Flexible, 6-month window

---

## Common Scenarios

### New Patient (High Value)
**Goal:** Book within 7 days, get complete info

**Script:**
```
"Wonderful! We'd love to welcome you to [Practice Name]. Let me get 
a few details and find you a great appointment time.

Can I get your full name and the best phone number?

[Collect info]

Do you have dental insurance? 

[If yes] What's the name on the card?
[If no] No problem, we have great options for uninsured patients.

Our next new patient appointment is [date/time]. Does that work for 
your schedule?"
```

### Insurance Question
**Goal:** Answer if possible, transfer if complex

**Script:**
```
"I'd be happy to help with insurance questions.

Are you asking whether we accept a specific insurance, or do you 
have a question about your coverage?

[If "do you accept X insurance"]
Yes, we accept [insurance] / Let me check on that - can I get your 
callback number and have our billing team confirm?

[If coverage question]
Our billing team can give you the most accurate information. Can I 
have them call you back? What's a good number?"
```

### Confirmation Call Inbound
**Trigger:** Patient calling to confirm their appointment

**Script:**
```
"I can help you confirm. Can I get your name and date of birth?

[Look up appointment]

I see your appointment on [date] at [time] with [provider]. Is that 
the one you're confirming?

[If yes] Perfect, you're all set! Please arrive 10 minutes early. 
Anything else I can help with?

[If wrong appointment] Let me pull up the right one..."
```

---

## Transfer Matrix

| Caller Need | During Hours | After Hours |
|-------------|--------------|-------------|
| Schedule appointment | Handle | Handle |
| Reschedule | Handle | Handle |
| Cancel | Handle | Handle |
| Emergency | Handle + Flag | Handle + Flag |
| Billing question | Transfer | Take message |
| Insurance verification | Transfer | Take message |
| Speak to doctor | Take message | Take message |
| Speak to specific person | Transfer | Take message |
| Complaint | Transfer to manager | Take detailed message |
| New patient inquiry | Handle | Handle |

---

## Multi-Provider Scheduling

### When Multiple Dentists Available
```
"Do you have a preference for which dentist you see, or would you 
like the next available appointment with any of our doctors?"
```

### When Requesting Specific Provider
```
"I can definitely schedule you with Dr. [Name]. Their next available 
[appointment type] is [date/time]. Does that work?

[If not]

The next option with Dr. [Name] would be [alternative date]. Or I 
could get you in sooner with Dr. [Other] if that helps?"
```

---

## SMS Templates

### Appointment Confirmation
```
[Practice Name]: Your appointment is confirmed for [Date] at [Time] 
with [Provider]. 

Please arrive 10 min early. Questions? Call [Phone]
```

### Recall Reminder
```
Hi [Name]! It's time to schedule your 6-month cleaning at [Practice Name].

Reply SCHEDULE and we'll call you, or call us at [Phone].
```

### Treatment Follow-Up
```
[Practice Name]: You have treatment recommendations pending. 

Call [Phone] to schedule before your insurance resets on [Date].
```

---

## Integration Notes

### Common PMS for Group Practices
- **Dentrix Enterprise** - Multi-location version
- **Eaglesoft** - Popular, good reporting
- **Open Dental** - Cost-effective, open source
- **Denticon** - Cloud-based, DSO-friendly

### Group Practice Considerations
- Multiple providers → must handle provider preferences
- Hygienist scheduling → separate from dentist scheduling  
- Insurance verification → often a dedicated person
- Call volume peaks → morning and lunch rushes
- Staff turnover → agent training is stable (advantage over humans)

---

## Metrics to Track

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| Answer rate | >98% | High volume = more missed opportunities |
| Hold time | <30 sec | Patients hate waiting |
| Calls handled vs transferred | >80% handled | Each transfer costs time |
| New patient conversion | >75% | Primary growth driver |
| Hygiene schedule fill rate | >90% | Revenue backbone |
| Same-day appointments booked | Track | Indicates effective urgency handling |

---

## Peak Time Handling

### Morning Rush (8-10 AM)
- Patients confirming appointments
- Calling to reschedule
- Emergencies from overnight

**Tactic:** Quick triage, efficient language, offer callback if complex

### Lunch Rush (12-1 PM)
- Patients calling on their lunch break
- Appointment requests

**Tactic:** Be efficient, acknowledge their time constraint

### End of Day (4-5 PM)
- Last-minute calls before closing
- "Can I get in tomorrow?"

**Tactic:** Check next-day availability, capture if urgent
