# Pediatric Dental Practice Playbook

**Practice Profile:** Specialized in children (infants to teens), parent-focused communication

---

## Configuration Settings

### Business Hours
```json
{
  "timezone": "America/Denver",
  "hours": {
    "monday": {"open": "08:00", "close": "17:00"},
    "tuesday": {"open": "08:00", "close": "17:00"},
    "wednesday": {"open": "08:00", "close": "17:00"},
    "thursday": {"open": "08:00", "close": "17:00"},
    "friday": {"open": "08:00", "close": "14:00"},
    "saturday": "closed",
    "sunday": "closed"
  },
  "lunch_break": {"start": "12:00", "end": "13:00"},
  "notes": "Often busiest after school hours and during summer"
}
```

### Agent Personality
```json
{
  "agent_name": "Jamie",
  "voice": "aura-luna-en",
  "tone": "friendly_reassuring",
  "personality_notes": "Warm, patient, understanding of parent concerns"
}
```

---

## Key Differences from General Practice

1. **Caller is parent, patient is child** - Always collect both names
2. **Multiple children** - Often scheduling siblings together
3. **Anxiety concerns** - Parents worried about child's fear
4. **Age-specific care** - Infant, toddler, child, teen have different needs
5. **Insurance complexity** - Child may be on different plan than parent

---

## Greeting Scripts

### During Hours
```
"Thank you for calling [Practice Name] Pediatric Dentistry, this is 
[Agent Name]. How may I help you today?"
```

### After Hours
```
"Thank you for calling [Practice Name] Pediatric Dentistry. We're 
currently closed, but I can still help.

If your child is experiencing a dental emergency - like a knocked-out 
tooth, severe pain, or significant swelling - please press 1 and I'll 
get Dr. [Name]'s team right to you.

For appointment scheduling or other questions, I can help right now."
```

### First-Time Caller Welcome
```
"Is this your first time calling [Practice Name]? 

[If yes]

Wonderful! We specialize in making dental visits fun and comfortable 
for kids. I can help you schedule your child's first visit. What's 
your little one's name?"
```

---

## New Patient Flow

### Infant/First Visit (Under 2)
**Trigger:** "first tooth", "baby", "1 year old", "infant"

**Script:**
```
"How exciting - it's time for their first dental visit! We love 
introducing little ones to the dentist.

This first visit is usually short and sweet - Dr. [Name] will check 
their teeth and gums, and give you tips on caring for their smile 
as they grow.

Can I get your baby's name and their date of birth?"
```

### School-Age Child (3-12)
**Script:**
```
"Perfect. And how old is [Child Name]?

[After age]

Great! At [age], we'll do [age-appropriate services]. Has [Child Name] 
been to a dentist before?

[If first time]
No worries - our team is amazing at making first visits comfortable. 
We take things slow and make it fun.

[If previous experience]
Wonderful! We'll review any records you can send over."
```

### Teen Patient
**Script:**
```
"Got it. At [age], we focus on [teen-specific services like orthodontic 
evaluation, wisdom teeth monitoring].

Does [Teen Name] have any dental concerns we should know about? 
Sometimes teens are nervous about certain things."
```

---

## Common Parent Questions

### "Will my child be scared?"
```
"That's such a common concern, and I completely understand. Our entire 
office is designed for kids - from the waiting room to the way our 
team talks to them.

Dr. [Name] and the team are experts at putting kids at ease. For very 
anxious children, we also offer [nitrous oxide / sedation options] 
if needed.

Most kids leave asking when they can come back!"
```

### "Can I go back with my child?"
```
"Absolutely! Parents are always welcome in the treatment area. For 
some procedures, we might ask you to wait in a special viewing area, 
but you'll never be far away.

Is there anything specific that would help [Child Name] feel more 
comfortable?"
```

### "Do you take [insurance]?"
```
"Let me check on that for you. What's the insurance company name?

[Check or note]

[If accepted] Yes, we do accept [Insurance]. Keep in mind that children 
sometimes have different coverage than the rest of the family.

[If not sure] Our billing team can verify that for you. Can I get 
your callback number?"
```

### "My child is in pain"
```
"I'm sorry [Child Name] is uncomfortable. Let me get some details 
so we can help quickly.

Can you describe the pain? Is it constant or does it come and go? 
Any swelling or fever?

[Assess severity]

Based on what you're describing, I want to get [Child Name] seen 
[today / as soon as possible]. We have [availability]. Can you 
come in?"
```

---

## Sibling Scheduling

**Trigger:** "both kids", "my children", "siblings", multiple names mentioned

**Script:**
```
"I can schedule both [Child 1] and [Child 2] together - that's often 
easiest for parents.

Would you prefer back-to-back appointments, or at the same time in 
different rooms?

[Note preference]

Our next opening for two kids is [date/time]. Does that work for 
your family?"
```

---

## Emergency Handling (Pediatric-Specific)

### Knocked Out Tooth
**CRITICAL - Permanent teeth may be saved**

```
"I'm sorry that happened! Stay calm - I'll help you.

First question: Is this a baby tooth or a permanent tooth?

[If permanent tooth in child over 6]
This is time-sensitive. If you have the tooth:
1. Pick it up by the crown, not the root
2. Rinse it gently with milk or water
3. If you can, put it back in the socket
4. If not, put it in milk and come immediately

We're getting Dr. [Name] ready for you now.

[If baby tooth]
Baby teeth don't get reimplanted, but we should still see [Child Name] 
to check for other injuries. Can you come in today?"
```

### Toothache / Pain
```
"Poor [Child Name]. Let me help you get them comfortable.

On a scale of 1-10, how would you describe their pain?

[If 7+] Let's get them in right away. Can you come in within the hour?

[If moderate] Does [Child Name] have any fever or facial swelling?

[Assess and schedule appropriately]

In the meantime, children's ibuprofen can help with pain. Avoid hot 
or cold foods on that side."
```

### Dental Trauma (Fall, Sports Injury)
```
"Is [Child Name] otherwise okay - no head injury or other concerns?

[If head/injury concern → recommend ER first]

Okay, let me ask about the dental part:
- Are any teeth loose, cracked, or knocked out?
- Is there bleeding from the mouth?
- Can they open and close their jaw normally?

[Assess and schedule urgently if needed]"
```

---

## SMS Templates

### Appointment Reminder (Parent)
```
Hi! [Child Name]'s dental appointment at [Practice Name] is tomorrow, 
[Date] at [Time].

Need to reschedule? Call [Phone] or reply R.

See you soon! 🦷
```

### First Visit Prep
```
[Practice Name]: [Child Name]'s first visit is [Date] at [Time]! 

Tips to prepare:
- Read them a fun book about the dentist
- Keep it positive
- Bring their favorite toy

We can't wait to meet them!
```

### 6-Month Recall
```
Time for [Child Name]'s checkup! 

Schedule their 6-month visit at [Practice Name]: 
Reply SCHEDULE or call [Phone]

Healthy smiles start with regular visits! 😊
```

---

## Transfer Matrix

| Caller Need | Action |
|-------------|--------|
| Schedule appointment | Handle |
| Emergency (pain, trauma) | Handle + Flag |
| Insurance question | Handle basic, transfer complex |
| Billing | Transfer |
| Sedation questions | Transfer to clinical staff |
| Special needs patient inquiry | Transfer to clinical staff |
| Complaint | Transfer to manager |

---

## Special Situations

### Special Needs Patients
```
"We love caring for children with special needs. Can you tell me a 
little about [Child Name]'s specific needs so I can make sure our 
team is prepared to make them comfortable?

[Listen and note carefully]

I'm going to flag this appointment so Dr. [Name] and the team can 
review and prepare. We want this to be a great experience for 
[Child Name]."
```

### Extremely Anxious Child
```
"I completely understand - some kids really struggle with dental visits.

A few options we offer:
1. A 'meet and greet' visit first - no treatment, just exploring
2. Nitrous oxide (laughing gas) to help them relax
3. For very anxious children, we also offer sedation options

Would any of those be helpful for [Child Name]?"
```

---

## Metrics to Track

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| New patient families | Track | Usually brings 1.8 kids on average |
| Sibling booking rate | >40% | Efficiency + family loyalty |
| Recall compliance | >75% | Critical for pediatric preventive care |
| Emergency same-day rate | 100% | Kids in pain can't wait |
| Parent satisfaction | Track | They refer other parents |

---

## Integration Notes

### Pediatric Practice Considerations
- **School schedules** → Summer and after-school are peak
- **Multiple children per family** → Link family records
- **Parent contact** → May have different last names than child
- **Insurance quirks** → Child's plan may differ from parent's
- **Growth tracking** → Age-appropriate treatment recommendations
