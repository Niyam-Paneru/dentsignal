# 📋 Dental AI Voice Agent - Master TODO List

> Last Updated: December 18, 2025

---

## 🚨 IMMEDIATE: Deployment (In Progress)

### Deployment Status
- [x] GitHub repo created: `Niyam-Paneru/dentsignal` ✅ (Dec 16)
- [x] Vercel deployment live: `dentsignal.vercel.app` ✅ (Dec 16)
- [x] Domain configured: `dentsignal.me` ✅ (Dec 16)
- [ ] **DigitalOcean App Platform** - Deploy backend API
- [ ] Update `NEXT_PUBLIC_API_URL` in Vercel to production URL
- [ ] Configure Twilio webhooks to production API

### API Keys (All Active)
- [x] Deepgram API key ✅
- [x] OpenAI API key ✅
- [x] Twilio account (funded) ✅
- [x] Gemini API key ✅
- [x] HuggingFace API key ✅

---

## 🔥 HIGH PRIORITY: Automation to Reduce Manual Work

**Goal: Customers paying $199/month should NOT do manual work**

### Phase 1: Immediate Automations (Week 1-2)
- [ ] **Auto-Onboarding (CRITICAL)**
  - Supabase Edge Function for account provisioning
  - Auto-create clinic, AI config, dashboard access
  - Welcome email with setup instructions
  - 2-min Loom video: "How to forward calls"
  - **Result: Customer live in 15 minutes, not 2 days**

- [ ] **Auto Call Forwarding Setup**
  - Auto-generate forwarding instructions per phone carrier
  - Include: *72 + DentSignal number
  - Test call option built into onboarding
  - **Result: Eliminates 90% of "how do I set this up?" tickets**

### Phase 2: Advanced Automations (Month 2-3)
- [ ] **Auto Appointment Reminders (SMS)**
  - Booking confirmation (same day)
  - 2 days before reminder
  - 24 hours before (anxiety check)
  - 3 hours before
  - **Result: Reduces no-shows from 25% → 10%**

- [ ] **Auto Insurance Verification**
  - Real-time insurance database lookup
  - Cache common insurances (Delta Dental, Blue Cross, etc.)
  - Fallback to human for unknown plans
  - **Result: Reduces staff interruptions by 40%**

- [ ] **Auto Call Quality Scoring**
  - Post-call GPT-4o-mini analysis
  - Score: greeting, questions asked, booking success
  - Tag: "great_call", "needs_improvement", "missed_booking"
  - Weekly email digest to customer
  - **Result: Proves ROI, reduces churn**

### Phase 3: Enterprise Automations (Month 4-6)
- [ ] **Auto Revenue Recovery Reports**
  - Monthly automated email with ROI metrics
  - Calls answered, appointments booked, revenue recovered
  - Charts and top-performing calls
  - **Result: Reduces churn from 15% → 5%**

- [ ] **Self-Service AI Customization**
  - Customer dashboard → Settings → AI Personality
  - Greeting style (formal/warm/casual)
  - Custom greetings per location
  - A/B testing framework
  - **Result: Eliminates 80% of "can you change this?" tickets**

---

## ✅ COMPLETED: Recent Updates (Dec 18, 2025)

### AI Training Enhancements
- [x] Added 8 advanced objection handling scripts ✅
- [x] Added emergency triage decision tree (1-10 pain scale) ✅
- [x] Added transfer decision tree (when to/not to transfer) ✅
- [x] Added 7-Second Rule for first impressions ✅
- [x] Added conversion data by demographics ✅
- [x] Integrated all research into prompt_builder.py ✅

### Landing Page Updates
- [x] Added visible pricing section ($149/$199/$399 tiers) ✅
- [x] Added competitor comparison table (vs Weave, RevenueWell) ✅
- [x] Professional tier marked as "Most Popular" ✅

### Branding
- [x] Rebranded from "Dental AI" to "DentSignal" ✅ (Dec 16)
- [x] Domain: dentsignal.me ✅
- [x] Updated all code references ✅

---

## ✅ COMPLETED: Technical Fixes

- [x] **Fix routes_inbound.py** - Ensure Twilio webhooks work correctly ✅ (Dec 14)
- [x] **Fix consent flow** - PSTN mode requires consent enforcement ✅ (Dec 14)
- [x] **PII masking** - Ensure no PHI leaks in logs ✅ (Already in utils.py)
- [x] **Add integration tests** - Test full call flow end-to-end ✅ (Dec 14)
- [x] **Add rate limiting** - Protect API from abuse ✅ (Dec 14 - rate_limiter.py)

---

## ✅ COMPLETED: Week 1 Foundation

### Day 1-2: Technical Hardening
- [x] Abstract Deepgram provider interface (switch-ready) ✅ (Dec 14 - providers/deepgram_provider.py)
- [x] Abstract Twilio provider interface (switch-ready) ✅ (Dec 14 - providers/twilio_provider.py)
- [x] Abstract LLM provider interface (OpenAI/Claude swap) ✅ (Dec 14 - providers/llm_providers.py)
- [x] Implement usage tracking per clinic (minutes used) ✅ (Dec 14 - routes_usage.py, db.py)
- [x] Add overage billing logic (>2,000 min/mo) ✅ (Dec 14 - integrated in record_usage())

### Day 3-4: Dashboard Completion
- [ ] Verify all pages use real Supabase data
- [ ] Test auth flow in incognito (must redirect to login)
- [ ] Test super admin access (only niyampaneru79@gmail.com)
- [ ] Add "Appointments Booked" metric to dashboard (primary KPI)
- [ ] Add "Revenue Recovered" calculation to analytics

### Day 5-7: Landing Page
- [x] Create landing page with dental color palette ✅ (Already exists - page.tsx)
- [x] Hero: "Stop Losing $370k/Year to Missed Calls" ✅ (Shows $255K based on research)
- [x] ROI calculator embed ✅ (roi-calculator.tsx with practice size presets)
- [x] One CTA: "Book a 15-minute Demo" ✅ ("Start Free Trial" button)
- [x] Link to Calendly ✅ (Links to /signup)
- [x] Mobile responsive ✅ (Tailwind responsive classes)

---

## 🎯 WEEK 2: Sales Infrastructure

### Outreach Prep
- [ ] Write 5 LinkedIn connection request templates
- [ ] Write 5 LinkedIn follow-up message templates
- [ ] Write 3 cold email templates (subject + body)
- [ ] Create 1-page ROI calculator (Google Sheets)
- [ ] Prepare 10-minute demo script

### Target List Building
- [ ] Join 10 dental Facebook groups (list in research)
- [ ] Identify 50 solo/2-doc practices in target region
- [ ] Export dental directory leads (ADA, local associations)
- [ ] Build outreach spreadsheet (name, email, phone, status)

### Collateral
- [ ] 1-pager PDF: "How Dental AI Recovers $370k/Year"
- [ ] Case study template (for first 3 customers)
- [ ] Pricing page (3 tiers: $149, $199, $399)
- [ ] FAQ document for common objections

---

## 🎯 WEEK 3-4: First Customers

### Outreach Execution
- [ ] Post in 2 Facebook groups (value-add, not spam)
- [ ] Send 20 LinkedIn connection requests
- [ ] Send 10 cold emails
- [ ] Follow up on all non-responders after 3 days

### Demo & Close
- [ ] Book 3 demo calls minimum
- [ ] Conduct demos with ROI calculator
- [ ] Offer free 30-day pilot (no credit card)
- [ ] Close 1 paying customer

### Onboarding
- [ ] Create onboarding checklist (15-30-15 minute format)
- [ ] Build 4 pre-configured playbooks:
  - [ ] General Family Practice
  - [ ] Cosmetic/Fee-for-Service
  - [ ] Pediatric
  - [ ] Emergency-heavy
- [ ] Create staff training video (5 min max)

---

## 🎯 MONTH 2-3: Scale to 10 Customers

### Product
- [ ] Add Dentrix integration
- [ ] Add Open Dental integration
- [ ] Add Eaglesoft integration
- [ ] Build recall campaign feature (outbound)
- [ ] Add no-show reduction automation

### Sales
- [ ] Collect 3 customer testimonials
- [ ] Create video case study
- [ ] Hire part-time appointment setter (optional)
- [ ] Implement referral program ($50 credit per referral)

### Operations
- [ ] Set up help desk (email-based for <$199, chat for $399+)
- [ ] Create knowledge base (top 20 FAQs)
- [ ] Automate monthly ROI reports per clinic

---

## 🎯 MONTH 4-6: Scale to 50 Customers

### Growth
- [ ] Expand to neighboring regions
- [ ] Partner with dental consultants/coaches
- [ ] Explore dental association sponsorships
- [ ] Launch affiliate program (10% recurring commission)

### Product
- [ ] Add more PMS integrations (Curve, CareStack)
- [ ] Multi-location support for small DSOs
- [ ] White-label option for Enterprise tier
- [ ] Custom AI personality tuning

### Compliance
- [ ] Complete HIPAA documentation
- [ ] Obtain BAAs from all vendors
- [ ] Implement 90-day data retention limit
- [ ] SOC2 Type 1 preparation (if scaling fast)

---

## 🎯 6-MONTH CHECKPOINT

### Success Criteria (Continue)
- [ ] 50+ paying customers
- [ ] $10,000+ MRR
- [ ] <5% monthly churn
- [ ] Positive unit economics (LTV > 3x CAC)

### Failure Criteria (Pivot or Kill)
- [ ] <10 paying customers
- [ ] >10% monthly churn
- [ ] Negative gross margins
- [ ] Unable to close demos

---

## 📊 KEY METRICS TO TRACK

### Weekly
- [ ] Demo calls booked
- [ ] Demos completed
- [ ] Customers closed
- [ ] Churn events

### Monthly
- [ ] MRR
- [ ] Customer count
- [ ] Churn rate
- [ ] Average revenue per user (ARPU)
- [ ] Customer acquisition cost (CAC)
- [ ] Lifetime value (LTV)

### Per Customer
- [ ] Calls answered
- [ ] Appointments booked
- [ ] Revenue recovered (calculated)
- [ ] No-show rate (before vs after)

---

## 🔧 TECHNICAL DEBT (Address by Month 3)

- [ ] Replace simulated telephony with production Twilio
- [ ] Add comprehensive error handling in websocket_bridge
- [ ] Implement call recording with proper encryption
- [ ] Add transcript search functionality
- [ ] Performance testing for 100+ concurrent calls
- [ ] Disaster recovery plan
- [ ] Automated backups for Supabase

---

## 📚 RESOURCES TO CREATE

- [ ] Onboarding video series (3-5 videos, 5 min each)
- [ ] Integration guides per PMS
- [ ] Troubleshooting guide
- [ ] Best practices for dental AI receptionist
- [ ] Monthly newsletter template
- [ ] Quarterly business review template (for Enterprise)

---

## 💡 FUTURE FEATURES (Backlog)

### Phase 2 (After 50 customers)
- [ ] Outbound recall campaigns
- [ ] Patient reactivation automation
- [ ] Insurance verification automation
- [ ] Treatment plan follow-ups
- [ ] Review request automation (post-appointment)

### Phase 3 (After 200 customers)
- [ ] Analytics benchmarking (compare to similar practices)
- [ ] Predictive no-show scoring
- [ ] Revenue forecasting
- [ ] Staff performance insights
- [ ] Multi-language support (Spanish priority)

---

## ⏰ IMMEDIATE NEXT ACTIONS (Today)

1. [ ] Run `003_quick_setup.sql` in Supabase to create demo clinic
2. [ ] Test dashboard with real data
3. [ ] Verify auth protection works in incognito
4. [ ] Fix any remaining chart tooltip issues
5. [ ] Start writing first cold email template





