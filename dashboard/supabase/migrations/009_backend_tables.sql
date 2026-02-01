-- =====================================================
-- Backend Tables Migration for DentSignal
-- Migrates SQLite backend tables to Supabase PostgreSQL
-- =====================================================

-- =====================================================
-- 1. USERS TABLE (Backend Authentication)
-- =====================================================
CREATE TABLE IF NOT EXISTS backend_users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_backend_users_email ON backend_users(email);

-- =====================================================
-- 2. UPLOAD BATCHES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS upload_batches (
    id SERIAL PRIMARY KEY,
    clinic_id UUID NOT NULL REFERENCES dental_clinics(id) ON DELETE CASCADE,
    source TEXT DEFAULT 'csv',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_upload_batches_clinic ON upload_batches(clinic_id);

-- =====================================================
-- 3. LEADS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES upload_batches(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    source_url TEXT,
    notes TEXT,
    consent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leads_batch ON leads(batch_id);
CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone);

-- =====================================================
-- 4. OUTBOUND CALLS TABLE
-- =====================================================
CREATE TYPE call_status AS ENUM ('queued', 'in-progress', 'completed', 'failed');
CREATE TYPE call_result_type AS ENUM ('booked', 'no-answer', 'failed', 'reschedule', 'voicemail');

CREATE TABLE IF NOT EXISTS outbound_calls (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    batch_id INTEGER NOT NULL REFERENCES upload_batches(id) ON DELETE CASCADE,
    clinic_id UUID NOT NULL REFERENCES dental_clinics(id) ON DELETE CASCADE,
    status call_status DEFAULT 'queued',
    attempt INTEGER DEFAULT 1,
    twilio_sid TEXT,
    recording_url TEXT,
    recording_sid TEXT,
    duration INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outbound_calls_lead ON outbound_calls(lead_id);
CREATE INDEX IF NOT EXISTS idx_outbound_calls_clinic ON outbound_calls(clinic_id);
CREATE INDEX IF NOT EXISTS idx_outbound_calls_twilio ON outbound_calls(twilio_sid);

-- =====================================================
-- 5. CALL RESULTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS call_results (
    id SERIAL PRIMARY KEY,
    call_id INTEGER UNIQUE NOT NULL REFERENCES outbound_calls(id) ON DELETE CASCADE,
    result call_result_type NOT NULL,
    transcript TEXT,
    booked_slot TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_call_results_call ON call_results(call_id);

-- =====================================================
-- 6. INBOUND CALLS TABLE (Enhanced)
-- =====================================================
CREATE TYPE inbound_call_status AS ENUM ('ringing', 'in-progress', 'completed', 'failed', 'no-answer');
CREATE TYPE inbound_call_outcome AS ENUM ('booked', 'inquiry', 'callback', 'transferred', 'hangup', 'voicemail', 'no_resolution');

CREATE TABLE IF NOT EXISTS inbound_calls (
    id SERIAL PRIMARY KEY,
    clinic_id UUID NOT NULL REFERENCES dental_clinics(id) ON DELETE CASCADE,
    from_number TEXT NOT NULL,
    to_number TEXT NOT NULL,
    twilio_call_sid TEXT UNIQUE NOT NULL,
    stream_sid TEXT,
    status inbound_call_status DEFAULT 'ringing',
    outcome inbound_call_outcome,
    duration_seconds INTEGER,
    transcript TEXT,
    summary TEXT,
    caller_name TEXT,
    is_new_patient BOOLEAN,
    reason_for_call TEXT,
    booked_appointment TIMESTAMPTZ,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    extra_data JSONB
);

CREATE INDEX IF NOT EXISTS idx_inbound_calls_clinic ON inbound_calls(clinic_id);
CREATE INDEX IF NOT EXISTS idx_inbound_calls_from ON inbound_calls(from_number);
CREATE INDEX IF NOT EXISTS idx_inbound_calls_twilio ON inbound_calls(twilio_call_sid);

-- =====================================================
-- 7. NO SHOW RECORDS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS no_show_records (
    id SERIAL PRIMARY KEY,
    appointment_id UUID NOT NULL REFERENCES dental_appointments(id) ON DELETE CASCADE,
    patient_id UUID REFERENCES dental_patients(id) ON DELETE SET NULL,
    clinic_id UUID NOT NULL REFERENCES dental_clinics(id) ON DELETE CASCADE,
    scheduled_time TIMESTAMPTZ NOT NULL,
    appointment_type TEXT,
    followed_up BOOLEAN DEFAULT FALSE,
    followup_call_made BOOLEAN DEFAULT FALSE,
    followup_sms_sent BOOLEAN DEFAULT FALSE,
    followup_notes TEXT,
    rescheduled_appointment_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    followed_up_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_no_show_records_clinic ON no_show_records(clinic_id);
CREATE INDEX IF NOT EXISTS idx_no_show_records_appointment ON no_show_records(appointment_id);

-- =====================================================
-- 8. CALENDAR INTEGRATIONS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS calendar_integrations (
    id SERIAL PRIMARY KEY,
    clinic_id UUID UNIQUE NOT NULL REFERENCES dental_clinics(id) ON DELETE CASCADE,
    provider TEXT DEFAULT 'manual',
    is_active BOOLEAN DEFAULT TRUE,
    google_calendar_id TEXT,
    google_credentials_json TEXT,
    calendly_api_key TEXT,
    calendly_user_uri TEXT,
    calendly_event_type_uri TEXT,
    slot_duration_minutes INTEGER DEFAULT 60,
    buffer_minutes INTEGER DEFAULT 15,
    business_hours_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_sync TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_calendar_integrations_clinic ON calendar_integrations(clinic_id);

-- =====================================================
-- 9. RECALL STATUS & TYPE ENUMS
-- =====================================================
CREATE TYPE recall_status AS ENUM ('pending', 'sms_sent', 'call_scheduled', 'call_completed', 'booked', 'declined', 'no_response', 'cancelled');
CREATE TYPE recall_type AS ENUM ('cleaning', 'checkup', 'followup', 'periodontal', 'custom');

-- =====================================================
-- 10. PATIENT RECALLS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS patient_recalls (
    id SERIAL PRIMARY KEY,
    clinic_id UUID NOT NULL REFERENCES dental_clinics(id) ON DELETE CASCADE,
    patient_id UUID REFERENCES dental_patients(id) ON DELETE SET NULL,
    patient_name TEXT NOT NULL,
    patient_phone TEXT NOT NULL,
    patient_email TEXT,
    recall_type recall_type DEFAULT 'cleaning',
    last_visit_date TIMESTAMPTZ,
    due_date TIMESTAMPTZ NOT NULL,
    status recall_status DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    sms_sent_at TIMESTAMPTZ,
    sms_message_sid TEXT,
    call_scheduled_at TIMESTAMPTZ,
    call_completed_at TIMESTAMPTZ,
    call_id INTEGER,
    outbound_call_sid TEXT,
    patient_response TEXT,
    booked_appointment_id UUID REFERENCES dental_appointments(id) ON DELETE SET NULL,
    declined_reason TEXT,
    sms_attempts INTEGER DEFAULT 0,
    call_attempts INTEGER DEFAULT 0,
    max_sms_attempts INTEGER DEFAULT 2,
    max_call_attempts INTEGER DEFAULT 2,
    campaign_id TEXT,
    batch_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    next_outreach_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_patient_recalls_clinic ON patient_recalls(clinic_id);
CREATE INDEX IF NOT EXISTS idx_patient_recalls_phone ON patient_recalls(patient_phone);
CREATE INDEX IF NOT EXISTS idx_patient_recalls_due ON patient_recalls(due_date);
CREATE INDEX IF NOT EXISTS idx_patient_recalls_status ON patient_recalls(status);

-- =====================================================
-- 11. RECALL CAMPAIGNS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS recall_campaigns (
    id SERIAL PRIMARY KEY,
    clinic_id UUID NOT NULL REFERENCES dental_clinics(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    recall_type recall_type NOT NULL,
    description TEXT,
    target_overdue_days INTEGER DEFAULT 30,
    target_count INTEGER DEFAULT 0,
    total_recalls INTEGER DEFAULT 0,
    sms_sent INTEGER DEFAULT 0,
    calls_made INTEGER DEFAULT 0,
    appointments_booked INTEGER DEFAULT 0,
    declined INTEGER DEFAULT 0,
    no_response INTEGER DEFAULT 0,
    estimated_revenue DECIMAL(10,2) DEFAULT 0,
    actual_revenue DECIMAL(10,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_recall_campaigns_clinic ON recall_campaigns(clinic_id);

-- =====================================================
-- 12. USAGE TYPE ENUM
-- =====================================================
CREATE TYPE usage_type AS ENUM ('inbound_call', 'outbound_call', 'sms_sent', 'sms_received', 'ai_tokens', 'tts_characters', 'stt_seconds');

-- =====================================================
-- 13. USAGE RECORDS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS usage_records (
    id SERIAL PRIMARY KEY,
    clinic_id UUID NOT NULL REFERENCES dental_clinics(id) ON DELETE CASCADE,
    usage_type usage_type NOT NULL,
    quantity DECIMAL(12,4) DEFAULT 0,
    reference_id TEXT,
    reference_type TEXT,
    billing_month TEXT NOT NULL,
    unit_cost DECIMAL(10,6) DEFAULT 0,
    total_cost DECIMAL(10,4) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_records_clinic ON usage_records(clinic_id);
CREATE INDEX IF NOT EXISTS idx_usage_records_month ON usage_records(billing_month);
CREATE INDEX IF NOT EXISTS idx_usage_records_type ON usage_records(usage_type);

-- =====================================================
-- 14. MONTHLY USAGE SUMMARIES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS monthly_usage_summaries (
    id SERIAL PRIMARY KEY,
    clinic_id UUID NOT NULL REFERENCES dental_clinics(id) ON DELETE CASCADE,
    billing_month TEXT NOT NULL,
    total_voice_seconds INTEGER DEFAULT 0,
    inbound_seconds INTEGER DEFAULT 0,
    outbound_seconds INTEGER DEFAULT 0,
    sms_sent_count INTEGER DEFAULT 0,
    sms_received_count INTEGER DEFAULT 0,
    ai_tokens_used INTEGER DEFAULT 0,
    tts_characters INTEGER DEFAULT 0,
    stt_seconds INTEGER DEFAULT 0,
    included_minutes INTEGER DEFAULT 2000,
    overage_minutes INTEGER DEFAULT 0,
    overage_rate DECIMAL(10,4) DEFAULT 0.05,
    base_cost DECIMAL(10,2) DEFAULT 0,
    overage_cost DECIMAL(10,2) DEFAULT 0,
    total_cost DECIMAL(10,2) DEFAULT 0,
    is_finalized BOOLEAN DEFAULT FALSE,
    finalized_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(clinic_id, billing_month)
);

CREATE INDEX IF NOT EXISTS idx_monthly_usage_clinic ON monthly_usage_summaries(clinic_id);
CREATE INDEX IF NOT EXISTS idx_monthly_usage_month ON monthly_usage_summaries(billing_month);

-- =====================================================
-- 15. ROW LEVEL SECURITY FOR NEW TABLES
-- =====================================================

-- Enable RLS
ALTER TABLE upload_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE outbound_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE inbound_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE no_show_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_recalls ENABLE ROW LEVEL SECURITY;
ALTER TABLE recall_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE monthly_usage_summaries ENABLE ROW LEVEL SECURITY;

-- Helper function to check clinic ownership
CREATE OR REPLACE FUNCTION user_owns_clinic(clinic_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM dental_clinics 
        WHERE id = clinic_uuid AND owner_id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Policies for upload_batches
CREATE POLICY "Users can view own upload batches" ON upload_batches
    FOR SELECT USING (user_owns_clinic(clinic_id));
CREATE POLICY "Users can insert own upload batches" ON upload_batches
    FOR INSERT WITH CHECK (user_owns_clinic(clinic_id));

-- Policies for leads (via batch)
CREATE POLICY "Users can view own leads" ON leads
    FOR SELECT USING (
        batch_id IN (SELECT id FROM upload_batches WHERE user_owns_clinic(clinic_id))
    );
CREATE POLICY "Users can insert own leads" ON leads
    FOR INSERT WITH CHECK (
        batch_id IN (SELECT id FROM upload_batches WHERE user_owns_clinic(clinic_id))
    );

-- Policies for outbound_calls
CREATE POLICY "Users can view own outbound calls" ON outbound_calls
    FOR SELECT USING (user_owns_clinic(clinic_id));
CREATE POLICY "Users can insert own outbound calls" ON outbound_calls
    FOR INSERT WITH CHECK (user_owns_clinic(clinic_id));
CREATE POLICY "Users can update own outbound calls" ON outbound_calls
    FOR UPDATE USING (user_owns_clinic(clinic_id));

-- Policies for call_results
CREATE POLICY "Users can view own call results" ON call_results
    FOR SELECT USING (
        call_id IN (SELECT id FROM outbound_calls WHERE user_owns_clinic(clinic_id))
    );
CREATE POLICY "Users can insert own call results" ON call_results
    FOR INSERT WITH CHECK (
        call_id IN (SELECT id FROM outbound_calls WHERE user_owns_clinic(clinic_id))
    );

-- Policies for inbound_calls
CREATE POLICY "Users can view own inbound calls" ON inbound_calls
    FOR SELECT USING (user_owns_clinic(clinic_id));
CREATE POLICY "Users can insert own inbound calls" ON inbound_calls
    FOR INSERT WITH CHECK (user_owns_clinic(clinic_id));
CREATE POLICY "Users can update own inbound calls" ON inbound_calls
    FOR UPDATE USING (user_owns_clinic(clinic_id));

-- Policies for no_show_records
CREATE POLICY "Users can view own no show records" ON no_show_records
    FOR SELECT USING (user_owns_clinic(clinic_id));
CREATE POLICY "Users can insert own no show records" ON no_show_records
    FOR INSERT WITH CHECK (user_owns_clinic(clinic_id));
CREATE POLICY "Users can update own no show records" ON no_show_records
    FOR UPDATE USING (user_owns_clinic(clinic_id));

-- Policies for calendar_integrations
CREATE POLICY "Users can view own calendar integrations" ON calendar_integrations
    FOR SELECT USING (user_owns_clinic(clinic_id));
CREATE POLICY "Users can insert own calendar integrations" ON calendar_integrations
    FOR INSERT WITH CHECK (user_owns_clinic(clinic_id));
CREATE POLICY "Users can update own calendar integrations" ON calendar_integrations
    FOR UPDATE USING (user_owns_clinic(clinic_id));

-- Policies for patient_recalls
CREATE POLICY "Users can view own patient recalls" ON patient_recalls
    FOR SELECT USING (user_owns_clinic(clinic_id));
CREATE POLICY "Users can insert own patient recalls" ON patient_recalls
    FOR INSERT WITH CHECK (user_owns_clinic(clinic_id));
CREATE POLICY "Users can update own patient recalls" ON patient_recalls
    FOR UPDATE USING (user_owns_clinic(clinic_id));

-- Policies for recall_campaigns
CREATE POLICY "Users can view own recall campaigns" ON recall_campaigns
    FOR SELECT USING (user_owns_clinic(clinic_id));
CREATE POLICY "Users can insert own recall campaigns" ON recall_campaigns
    FOR INSERT WITH CHECK (user_owns_clinic(clinic_id));
CREATE POLICY "Users can update own recall campaigns" ON recall_campaigns
    FOR UPDATE USING (user_owns_clinic(clinic_id));

-- Policies for usage_records
CREATE POLICY "Users can view own usage records" ON usage_records
    FOR SELECT USING (user_owns_clinic(clinic_id));

-- Policies for monthly_usage_summaries
CREATE POLICY "Users can view own usage summaries" ON monthly_usage_summaries
    FOR SELECT USING (user_owns_clinic(clinic_id));

-- =====================================================
-- 16. SERVICE ROLE POLICIES (for backend API)
-- Backend uses service role key which bypasses RLS
-- These policies allow the backend to manage all data
-- =====================================================

-- Grant service role full access (service role bypasses RLS by default)
-- No additional policies needed - service_role has full access

-- =====================================================
-- 17. UPDATE TRIGGERS
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_outbound_calls_updated_at
    BEFORE UPDATE ON outbound_calls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_patient_recalls_updated_at
    BEFORE UPDATE ON patient_recalls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_recall_campaigns_updated_at
    BEFORE UPDATE ON recall_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_monthly_usage_updated_at
    BEFORE UPDATE ON monthly_usage_summaries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_calendar_integrations_updated_at
    BEFORE UPDATE ON calendar_integrations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================
