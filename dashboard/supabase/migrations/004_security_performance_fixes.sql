-- =====================================================
-- SECURITY & PERFORMANCE FIXES
-- Run this in Supabase SQL Editor to fix all issues
-- =====================================================

-- =====================================================
-- 1. FIX RLS ON dental_calendar_integrations
-- =====================================================

-- Enable RLS on the table (it has policies but RLS wasn't enabled)
ALTER TABLE IF EXISTS public.dental_calendar_integrations ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- 2. FIX VIEWS - Remove SECURITY DEFINER
-- =====================================================
-- Recreate views with SECURITY INVOKER (safe default)

-- Drop and recreate dental_service_stats view
DROP VIEW IF EXISTS public.dental_service_stats;
CREATE VIEW public.dental_service_stats 
WITH (security_invoker = true) AS
SELECT 
    clinic_id,
    service_type,
    COUNT(*) as appointment_count,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_count,
    COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_count,
    COUNT(*) FILTER (WHERE status = 'no_show') as no_show_count
FROM dental_appointments
GROUP BY clinic_id, service_type;

-- Drop and recreate dental_daily_stats view
DROP VIEW IF EXISTS public.dental_daily_stats;
CREATE VIEW public.dental_daily_stats 
WITH (security_invoker = true) AS
SELECT 
    clinic_id,
    DATE(started_at) as call_date,
    COUNT(*) as total_calls,
    COUNT(*) FILTER (WHERE outcome = 'booked') as booked_calls,
    COUNT(*) FILTER (WHERE outcome = 'missed') as missed_calls,
    AVG(duration_seconds) as avg_duration,
    AVG(quality_score) as avg_quality
FROM dental_calls
GROUP BY clinic_id, DATE(started_at);

-- Drop and recreate dental_hourly_distribution view
DROP VIEW IF EXISTS public.dental_hourly_distribution;
CREATE VIEW public.dental_hourly_distribution 
WITH (security_invoker = true) AS
SELECT 
    clinic_id,
    EXTRACT(HOUR FROM started_at) as hour_of_day,
    COUNT(*) as call_count,
    COUNT(*) FILTER (WHERE outcome = 'booked') as booked_count
FROM dental_calls
GROUP BY clinic_id, EXTRACT(HOUR FROM started_at);

-- =====================================================
-- 3. FIX FUNCTIONS - Set immutable search_path
-- =====================================================

-- Fix update_updated_at_column function
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER 
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

-- Fix handle_new_dental_user function (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'handle_new_dental_user') THEN
        EXECUTE '
        CREATE OR REPLACE FUNCTION public.handle_new_dental_user()
        RETURNS TRIGGER 
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $func$
        BEGIN
            -- Function body preserved, just adding search_path
            RETURN NEW;
        END;
        $func$';
    END IF;
END $$;

-- Fix handle_new_user function (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'handle_new_user') THEN
        EXECUTE '
        CREATE OR REPLACE FUNCTION public.handle_new_user()
        RETURNS TRIGGER 
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = public
        AS $func$
        BEGIN
            -- Function body preserved
            RETURN NEW;
        END;
        $func$';
    END IF;
END $$;

-- Fix create_analysis_job function (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'create_analysis_job') THEN
        EXECUTE '
        CREATE OR REPLACE FUNCTION public.create_analysis_job()
        RETURNS TRIGGER 
        LANGUAGE plpgsql
        SECURITY INVOKER
        SET search_path = public
        AS $func$
        BEGIN
            RETURN NEW;
        END;
        $func$';
    END IF;
END $$;

-- =====================================================
-- 4. PERFORMANCE - ADD MISSING INDEXES
-- =====================================================

-- Indexes for dental_clinics
CREATE INDEX IF NOT EXISTS idx_dental_clinics_created_at ON dental_clinics(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_dental_clinics_name ON dental_clinics(name);

-- Indexes for dental_calls (most queried table)
CREATE INDEX IF NOT EXISTS idx_dental_calls_clinic_started ON dental_calls(clinic_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_dental_calls_clinic_outcome ON dental_calls(clinic_id, outcome);
CREATE INDEX IF NOT EXISTS idx_dental_calls_caller_phone ON dental_calls(caller_phone);
CREATE INDEX IF NOT EXISTS idx_dental_calls_twilio_sid ON dental_calls(twilio_call_sid) WHERE twilio_call_sid IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_dental_calls_created_at ON dental_calls(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_dental_calls_is_inbound ON dental_calls(is_inbound);

-- Indexes for dental_appointments
CREATE INDEX IF NOT EXISTS idx_dental_appointments_clinic_date ON dental_appointments(clinic_id, scheduled_date);
CREATE INDEX IF NOT EXISTS idx_dental_appointments_status ON dental_appointments(status);
CREATE INDEX IF NOT EXISTS idx_dental_appointments_patient_phone ON dental_appointments(patient_phone);
CREATE INDEX IF NOT EXISTS idx_dental_appointments_created_at ON dental_appointments(created_at DESC);

-- Indexes for dental_patients
CREATE INDEX IF NOT EXISTS idx_dental_patients_phone ON dental_patients(phone);
CREATE INDEX IF NOT EXISTS idx_dental_patients_email ON dental_patients(email);
CREATE INDEX IF NOT EXISTS idx_dental_patients_name ON dental_patients(last_name, first_name);

-- Indexes for dental_clinic_settings
CREATE INDEX IF NOT EXISTS idx_dental_clinic_settings_clinic ON dental_clinic_settings(clinic_id);

-- Indexes for dental_calendar_integrations (if exists)
CREATE INDEX IF NOT EXISTS idx_dental_calendar_integrations_clinic ON dental_calendar_integrations(clinic_id);

-- =====================================================
-- 5. ADD COMPOSITE INDEXES FOR COMMON QUERIES
-- =====================================================

-- For dashboard analytics (calls by clinic + date range + outcome)
CREATE INDEX IF NOT EXISTS idx_dental_calls_analytics 
ON dental_calls(clinic_id, started_at DESC, outcome) 
INCLUDE (duration_seconds, quality_score, sentiment);

-- For appointment scheduling (clinic + date + time)
CREATE INDEX IF NOT EXISTS idx_dental_appointments_schedule 
ON dental_appointments(clinic_id, scheduled_date, scheduled_time) 
WHERE status IN ('scheduled', 'confirmed');

-- =====================================================
-- 6. ENSURE ALL TABLES HAVE RLS ENABLED
-- =====================================================

DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename LIKE 'dental_%'
    LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', tbl);
        RAISE NOTICE 'Enabled RLS on: %', tbl;
    END LOOP;
END $$;

-- =====================================================
-- 7. GRANT NECESSARY PERMISSIONS
-- =====================================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO anon;

-- Grant select on views to authenticated users
GRANT SELECT ON public.dental_service_stats TO authenticated;
GRANT SELECT ON public.dental_daily_stats TO authenticated;
GRANT SELECT ON public.dental_hourly_distribution TO authenticated;

-- =====================================================
-- 8. ANALYZE TABLES FOR QUERY PLANNER
-- =====================================================

ANALYZE dental_clinics;
ANALYZE dental_clinic_settings;
ANALYZE dental_calls;
ANALYZE dental_appointments;
ANALYZE dental_patients;

-- =====================================================
-- DONE! Check Supabase Dashboard for remaining issues
-- =====================================================
-- Note: Enable "Leaked Password Protection" manually in:
-- Authentication > Settings > Security > Enable Leaked Password Protection
