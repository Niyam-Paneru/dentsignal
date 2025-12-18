# Specialty Practice Playbook

**Practice Profile:** Oral Surgery, Periodontics, Endodontics, Orthodontics, Prosthodontics

---

## Key Characteristics of Specialty Practices

1. **Referral-based** - Most patients come from referring dentists
2. **Complex scheduling** - Longer appointments, specific requirements
3. **Higher anxiety** - Patients referred for serious issues
4. **Insurance complexity** - Medical vs dental, pre-authorizations
5. **Consultation first** - Usually consult before treatment

---

## Configuration by Specialty

### Oral Surgery
```json
{
  "specialty": "oral_surgery",
  "services": [
    "Wisdom teeth extraction",
    "Dental implants",
    "Bone grafting",
    "Biopsy",
    "TMJ treatment",
    "Corrective jaw surgery"
  ],
  "pre_appointment": "Nothing to eat or drink 6 hours before if sedation",
  "special_instructions": true
}
```

### Periodontics
```json
{
  "specialty": "periodontics",
  "services": [
    "Deep cleaning / Scaling and root planing",
    "Gum grafting",
    "Crown lengthening",
    "Implant placement",
    "Periodontal maintenance"
  ],
  "referral_required": false
}
```

### Endodontics
```json
{
  "specialty": "endodontics",
  "services": [
    "Root canal therapy",
    "Root canal retreatment",
    "Apicoectomy",
    "Emergency root canals"
  ],
  "emergency_priority": true
}
```

### Orthodontics
```json
{
  "specialty": "orthodontics",
  "services": [
    "Braces - traditional",
    "Braces - ceramic/clear",
    "Invisalign",
    "Retainers",
    "Phase I treatment (children)"
  ],
  "consultation_required": true,
  "treatment_length": "12-24 months typical"
}
```

---

## Greeting Scripts

### Standard Greeting
```
"Thank you for calling [Practice Name] [Specialty], this is [Agent Name]. 
How may I help you today?"
```

### Referral Patient (Most Common)
```
"Thank you for calling. Were you referred to us by your dentist?

[If yes] Perfect. Do you have the referral or X-rays they sent?

[If no] No problem - we accept patients who find us directly too. 
What brings you to a [specialist type] today?"
```

### Emergency (Endodontics)
```
"I'm sorry you're in pain. For root canal emergencies, we try to 
see patients the same day when possible.

Can you describe your pain? Is it constant throbbing, or sharp 
pain when you bite?

[Assess urgency and schedule]"
```

---

## Referral Handling

### When Referral Has Been Sent
```
"Perfect. Let me check if we've received that from [Referring Dentist Name].

[Check system]

Yes, I see it here. Dr. [Referring] has noted [brief description]. 
Let me schedule your consultation.

When would be best for you - we have openings on [dates]?"
```

### When Referral Not Yet Received
```
"No worries - sometimes referrals take a day or two to come through.

I can schedule your appointment now, and we'll follow up with 
[Referring Dentist] to get the records.

Can I get your name and the best phone number to reach you?"
```

### Self-Referred Patient
```
"Absolutely, we see self-referred patients too.

To help us prepare for your visit, can you tell me a bit about 
what's going on and what you're hoping to address?

[Listen and document]

We'll start with a consultation so Dr. [Name] can evaluate and 
recommend the best treatment."
```

---

## Specialty-Specific Scenarios

### Oral Surgery: Wisdom Teeth Consultation
```
"Wisdom teeth consultations are common! We'll start with an exam 
and 3D scan to see exactly what's going on.

A few things to know:
- The consultation is about [30-45] minutes
- We'll discuss sedation options
- If needed, extraction is usually a separate appointment

Do you have dental insurance? Wisdom teeth are sometimes covered 
under medical insurance too."
```

### Oral Surgery: Pre-Op Call
```
"I see you're scheduled for surgery on [Date] at [Time].

Just confirming a few things:
- Nothing to eat or drink after midnight the night before
- Wear comfortable, loose clothing
- Someone must drive you home - you cannot drive yourself
- Plan to rest for the remainder of the day

Do you have any questions about preparing for your procedure?"
```

### Periodontics: Deep Cleaning
```
"For your scaling and root planing appointment, the treatment takes 
about [1-2] hours depending on which areas we're treating.

We'll numb the area so you'll be comfortable. Some patients prefer 
to do one side at a time over two visits.

Would you like to do the full treatment in one visit, or split it up?"
```

### Endodontics: Root Canal Anxiety
```
"I completely understand the concern - root canals have an unfair 
reputation. The truth is, most patients say the procedure itself 
is no more uncomfortable than getting a filling.

The pain you're feeling now is actually worse than what you'll 
experience during treatment. We're here to get you out of pain.

Dr. [Name] has done thousands of these procedures. You're in 
excellent hands."
```

### Orthodontics: Initial Consultation
```
"Great! Our complimentary consultation includes:
- Full exam with Dr. [Name]
- Digital photos and X-rays
- Discussion of treatment options
- Cost and payment plan information

The visit takes about [45-60] minutes. 

Is this for yourself or for your child?"
```

### Orthodontics: Treatment Update
```
"Are you calling about your current treatment with us?

[If yes] I can help with that. What's going on?

[Common issues: broken bracket, discomfort, lost retainer]

[If broken bracket] Is the bracket still attached to the wire, 
or has it come completely off? If it's not causing pain, you can 
wait until your next regular appointment. If it's poking or 
uncomfortable, let's get you in to fix it."
```

---

## Consultation Flow

Most specialty visits start with consultation:

### Standard Consultation Script
```
"Since this is your first visit with us, we'll start with a 
consultation. Dr. [Name] will:

1. Review your records and any X-rays
2. Do a thorough examination
3. Explain what's going on
4. Recommend treatment options
5. Discuss costs and scheduling

The consultation takes about [time]. Do you have any questions 
before we schedule?"
```

### After Consultation - Treatment Scheduling
```
"Following your consultation with Dr. [Name], you've been 
recommended [treatment].

I can schedule that for you now. The procedure takes approximately 
[duration] and we have availability on [dates].

[If sedation involved]
This procedure requires [type of sedation], so you'll need someone 
to drive you home.

Which option works best for you?"
```

---

## Insurance Handling (Complex Cases)

### Medical vs Dental Insurance
```
"Some [specialty procedures] may be covered by medical insurance 
rather than dental insurance. For example:
- Wisdom teeth with medical complications
- Jaw surgery
- Implants after cancer treatment

We'll verify both your dental and medical coverage before treatment. 
Can I get both insurance cards' information?"
```

### Pre-Authorization
```
"For this procedure, your insurance requires pre-authorization. 
Our billing team will submit that request.

This typically takes [3-5] business days. Once approved, we'll 
call you to schedule the treatment.

If there are any coverage questions, we'll reach out to discuss 
options before proceeding."
```

---

## Emergency Handling by Specialty

### Oral Surgery Emergencies
- Post-operative bleeding
- Severe swelling
- Signs of infection
- Dry socket

```
"If you're experiencing bleeding that won't stop after biting on 
gauze for 20 minutes, severe swelling, or fever, that's urgent.

I'm going to page Dr. [Name] right now. What's your callback number?"
```

### Endodontic Emergencies
- Severe toothache
- Dental abscess
- Referred pain

```
"Severe tooth pain, especially if it's keeping you awake, suggests 
the nerve is involved. We try to see emergency root canal patients 
the same day.

Can you come in at [time]? Dr. [Name] will evaluate and, if needed, 
start treatment to get you out of pain."
```

---

## Transfer Matrix

| Caller Need | Action |
|-------------|--------|
| Schedule consultation | Handle |
| Referral follow-up | Handle |
| Emergency | Handle + Flag (high priority) |
| Treatment scheduling | Handle |
| Pre-op questions | Handle or transfer to clinical |
| Post-op complications | Transfer to clinical |
| Complex insurance | Transfer to billing |
| Referring dentist calling | Transfer immediately |

---

## SMS Templates

### Consultation Confirmation
```
[Practice Name]: Your consultation with Dr. [Name] is confirmed 
for [Date] at [Time].

Please bring: Insurance cards, referral form, list of medications.

Questions? Call [Phone]
```

### Surgery Prep Reminder
```
[Practice Name] REMINDER: Your surgery is [Date] at [Time].

⚠️ NOTHING to eat or drink after midnight
⚠️ You MUST have a driver
⚠️ Wear comfortable clothing

Reply with questions or call [Phone]
```

### Orthodontic Check-In
```
Time for your braces check! Schedule your next adjustment at 
[Practice Name]:

Call [Phone] or reply SCHEDULE

Keep brushing and flossing! 🦷
```

---

## Metrics to Track

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| Referral-to-consult rate | >80% | Capture referred patients quickly |
| Consult-to-treatment rate | >70% | Conversion after consultation |
| Emergency same-day | 100% | Specialty = complex problems |
| Referring doctor satisfaction | Track | They send more patients |
| Pre-auth success rate | >90% | Ensures patients can proceed |

---

## Communication with Referring Dentists

### When Referring Dentist Calls
```
"[Priority handling - always helpful to referring doctors]

Dr. [Name]'s office? Of course, let me help you right away.

[Transfer to staff or take detailed message]"
```

### Referral Follow-Up
```
"I'm following up on [Patient Name] that was referred to us by 
Dr. [Referring Dentist].

Dr. [Specialist] has completed the [procedure] and recommends 
[next steps]. We're sending a report to your office today.

Is there anything else Dr. [Referring Dentist] needs from us?"
```
