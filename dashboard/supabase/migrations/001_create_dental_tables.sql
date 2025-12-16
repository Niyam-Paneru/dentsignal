-- =====================================================
-- Dental AI Dashboard - Supabase Schema
-- Run this in your Supabase SQL Editor
-- =====================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. DENTAL CLINICS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS dental_clinics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone TEXT,
    twilio_number TEXT,
    address TEXT,
    business_hours JSONB DEFAULT '{
        "monday": {"open": "09:00", "close": "17:00"},
        "tuesday": {"open": "09:00", "close": "17:00"},
        "wednesday": {"open": "09:00", "close": "17:00"},
        "thursday": {"open": "09:00", "close": "17:00"},
        "friday": {"open": "09:00", "close": "17:00"},
        "saturday": {"open": "09:00", "close": "13:00"},
        "sunday": null
    }'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster lookups by owner
CREATE INDEX IF NOT EXISTS idx_dental_clinics_owner ON dental_clinics(owner_id);

-- =====================================================
-- 2. DENTAL CLINIC SETTINGS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS dental_clinic_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id UUID NOT NULL REFERENCES dental_clinics(id) ON DELETE CASCADE,
    agent_name TEXT DEFAULT 'Sarah',
    agent_voice TEXT DEFAULT 'aura-asteria-en',
    greeting_template TEXT DEFAULT 'Thank you for calling {clinic_name}. This is {agent_name}, how may I help you today?',
    services TEXT[] DEFAULT ARRAY['cleaning', 'checkup', 'filling', 'crown', 'whitening', 'extraction'],
    dentist_names TEXT[] DEFAULT ARRAY['Dr. Smith'],
    max_call_duration INTEGER DEFAULT 300,
    transfer_keywords TEXT[] DEFAULT ARRAY['speak to human', 'real person', 'manager'],
    personality_traits TEXT[] DEFAULT ARRAY['friendly', 'professional', 'helpful'],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(clinic_id)
);

-- =====================================================
-- 3. DENTAL CALLS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS dental_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id UUID NOT NULL REFERENCES dental_clinics(id) ON DELETE CASCADE,
    caller_phone TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    outcome TEXT CHECK (outcome IN ('booked', 'inquiry', 'info', 'transferred', 'missed', 'cancelled', 'voicemail', 'failed')),
    call_reason TEXT,
    transcript TEXT,
    recording_url TEXT,
    sentiment TEXT CHECK (sentiment IN ('positive', 'neutral', 'negative')),
    quality_score INTEGER CHECK (quality_score >= 0 AND quality_score <= 100),
    patient_id UUID,
    summary TEXT,
    twilio_call_sid TEXT,
    is_inbound BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_dental_calls_clinic ON dental_calls(clinic_id);
CREATE INDEX IF NOT EXISTS idx_dental_calls_started ON dental_calls(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_dental_calls_outcome ON dental_calls(outcome);

-- =====================================================
-- 4. DENTAL APPOINTMENTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS dental_appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id UUID NOT NULL REFERENCES dental_clinics(id) ON DELETE CASCADE,
    patient_id UUID,
    call_id UUID REFERENCES dental_calls(id) ON DELETE SET NULL,
    patient_name TEXT,
    patient_phone TEXT,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME NOT NULL,
    service_type TEXT NOT NULL,
    status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'confirmed', 'completed', 'cancelled', 'no_show')),
    notes TEXT,
    google_event_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_dental_appointments_clinic ON dental_appointments(clinic_id);
CREATE INDEX IF NOT EXISTS idx_dental_appointments_date ON dental_appointments(scheduled_date);

-- =====================================================
-- 5. DENTAL PATIENTS TABLE (Optional)
-- =====================================================
CREATE TABLE IF NOT EXISTS dental_patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_id UUID NOT NULL REFERENCES dental_clinics(id) ON DELETE CASCADE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    date_of_birth DATE,
    insurance_provider TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dental_patients_clinic ON dental_patients(clinic_id);

-- =====================================================
-- 6. ROW LEVEL SECURITY (RLS)
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE dental_clinics ENABLE ROW LEVEL SECURITY;
ALTER TABLE dental_clinic_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE dental_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE dental_appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE dental_patients ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own clinic
CREATE POLICY "Users can view own clinic" ON dental_clinics
    FOR SELECT USING (auth.uid() = owner_id);

CREATE POLICY "Users can update own clinic" ON dental_clinics
    FOR UPDATE USING (auth.uid() = owner_id);

CREATE POLICY "Users can insert own clinic" ON dental_clinics
    FOR INSERT WITH CHECK (auth.uid() = owner_id);

-- Policy: Users can only see settings for their clinic
CREATE POLICY "Users can view own clinic settings" ON dental_clinic_settings
    FOR SELECT USING (
        clinic_id IN (SELECT id FROM dental_clinics WHERE owner_id = auth.uid())
    );

CREATE POLICY "Users can update own clinic settings" ON dental_clinic_settings
    FOR UPDATE USING (
        clinic_id IN (SELECT id FROM dental_clinics WHERE owner_id = auth.uid())
    );

CREATE POLICY "Users can insert own clinic settings" ON dental_clinic_settings
    FOR INSERT WITH CHECK (
        clinic_id IN (SELECT id FROM dental_clinics WHERE owner_id = auth.uid())
    );

-- Policy: Users can only see calls for their clinic
CREATE POLICY "Users can view own clinic calls" ON dental_calls
    FOR SELECT USING (
        clinic_id IN (SELECT id FROM dental_clinics WHERE owner_id = auth.uid())
    );

CREATE POLICY "Users can insert own clinic calls" ON dental_calls
    FOR INSERT WITH CHECK (
        clinic_id IN (SELECT id FROM dental_clinics WHERE owner_id = auth.uid())
    );

-- Policy: Users can only see appointments for their clinic
CREATE POLICY "Users can view own clinic appointments" ON dental_appointments
    FOR SELECT USING (
        clinic_id IN (SELECT id FROM dental_clinics WHERE owner_id = auth.uid())
    );

CREATE POLICY "Users can manage own clinic appointments" ON dental_appointments
    FOR ALL USING (
        clinic_id IN (SELECT id FROM dental_clinics WHERE owner_id = auth.uid())
    );

-- Policy: Users can only see patients for their clinic
CREATE POLICY "Users can view own clinic patients" ON dental_patients
    FOR SELECT USING (
        clinic_id IN (SELECT id FROM dental_clinics WHERE owner_id = auth.uid())
    );

CREATE POLICY "Users can manage own clinic patients" ON dental_patients
    FOR ALL USING (
        clinic_id IN (SELECT id FROM dental_clinics WHERE owner_id = auth.uid())
    );

-- =====================================================
-- 7. FUNCTIONS FOR AUTO-UPDATING TIMESTAMPS
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_dental_clinics_updated_at
    BEFORE UPDATE ON dental_clinics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dental_clinic_settings_updated_at
    BEFORE UPDATE ON dental_clinic_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dental_appointments_updated_at
    BEFORE UPDATE ON dental_appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dental_patients_updated_at
    BEFORE UPDATE ON dental_patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
