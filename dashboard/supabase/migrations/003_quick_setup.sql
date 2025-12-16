-- =====================================================
-- QUICK CLINIC SETUP - Run this in Supabase SQL Editor
-- =====================================================
-- This script automatically finds your user ID and creates a clinic for you
-- Just run the whole thing - no manual ID replacement needed!

-- =====================================================
-- OPTION 1: Auto-detect user and create clinic
-- =====================================================
-- This finds the first user without a clinic and creates one for them

DO $$
DECLARE
    target_user_id UUID;
    new_clinic_id UUID;
BEGIN
    -- Find a user that doesn't have a clinic yet
    SELECT u.id INTO target_user_id
    FROM auth.users u
    LEFT JOIN dental_clinics c ON c.owner_id = u.id
    WHERE c.id IS NULL
    ORDER BY u.created_at DESC
    LIMIT 1;

    IF target_user_id IS NULL THEN
        RAISE NOTICE 'All users already have clinics!';
        RETURN;
    END IF;

    -- Create clinic for this user
    INSERT INTO dental_clinics (owner_id, name, phone, address, twilio_number)
    VALUES (
        target_user_id,
        'Bright Smile Dental',
        '(555) 123-4567',
        '123 Main Street, Suite 100, City, State 12345',
        '+15551234567'
    )
    RETURNING id INTO new_clinic_id;

    -- Create clinic settings
    INSERT INTO dental_clinic_settings (clinic_id, agent_name, agent_voice, services, dentist_names)
    VALUES (
        new_clinic_id,
        'Sarah',
        'aura-asteria-en',
        ARRAY['cleaning', 'checkup', 'filling', 'crown', 'whitening', 'extraction', 'root canal'],
        ARRAY['Dr. Smith', 'Dr. Johnson']
    );

    -- Add demo calls for the last 7 days
    INSERT INTO dental_calls (clinic_id, caller_phone, started_at, duration_seconds, outcome, call_reason, sentiment, quality_score, summary)
    VALUES
        (new_clinic_id, '+1 555-0101', NOW() - INTERVAL '1 hour', 185, 'booked', 'New Patient Inquiry', 'positive', 92, 'New patient called to schedule first cleaning. Booked for next week.'),
        (new_clinic_id, '+1 555-0102', NOW() - INTERVAL '3 hours', 120, 'info', 'Insurance Question', 'neutral', 78, 'Patient asked about Delta Dental coverage. Provided information.'),
        (new_clinic_id, '+1 555-0103', NOW() - INTERVAL '5 hours', 145, 'booked', 'Reschedule Appointment', 'positive', 85, 'Existing patient rescheduled cleaning from Monday to Thursday.'),
        (new_clinic_id, '+1 555-0104', NOW() - INTERVAL '8 hours', 45, 'transferred', 'Emergency - Tooth Pain', 'negative', 65, 'Patient with severe pain. Transferred to on-call dentist.'),
        (new_clinic_id, '+1 555-0105', NOW() - INTERVAL '1 day', 200, 'booked', 'Whitening Consultation', 'positive', 88, 'Patient interested in teeth whitening. Booked consultation.'),
        (new_clinic_id, '+1 555-0106', NOW() - INTERVAL '1 day 4 hours', 90, 'inquiry', 'Pricing Question', 'neutral', 72, 'Asked about cleaning costs. Will call back to book.'),
        (new_clinic_id, '+1 555-0107', NOW() - INTERVAL '2 days', 160, 'booked', 'Checkup Appointment', 'positive', 90, 'Regular checkup booked for returning patient.'),
        (new_clinic_id, '+1 555-0108', NOW() - INTERVAL '2 days 6 hours', 30, 'missed', NULL, NULL, NULL, NULL),
        (new_clinic_id, '+1 555-0109', NOW() - INTERVAL '3 days', 175, 'booked', 'Crown Replacement', 'positive', 82, 'Patient needs crown replaced. Booked procedure.'),
        (new_clinic_id, '+1 555-0110', NOW() - INTERVAL '3 days 8 hours', 110, 'info', 'Hours Question', 'positive', 75, 'Asked about Saturday hours. Confirmed we are open.'),
        (new_clinic_id, '+1 555-0111', NOW() - INTERVAL '4 days', 195, 'booked', 'Family Appointment', 'positive', 95, 'Booked appointments for entire family - 4 cleanings.'),
        (new_clinic_id, '+1 555-0112', NOW() - INTERVAL '5 days', 80, 'cancelled', 'Cancel Appointment', 'neutral', 70, 'Patient cancelled due to work conflict. Will reschedule.'),
        (new_clinic_id, '+1 555-0113', NOW() - INTERVAL '5 days 3 hours', 165, 'booked', 'New Patient', 'positive', 88, 'First-time patient scheduled for consultation.'),
        (new_clinic_id, '+1 555-0114', NOW() - INTERVAL '6 days', 140, 'booked', 'Cleaning', 'positive', 91, 'Regular cleaning appointment booked.'),
        (new_clinic_id, '+1 555-0115', NOW() - INTERVAL '6 days 5 hours', 55, 'info', 'Location Question', 'neutral', 80, 'Asked for directions and parking info.');

    -- Add demo appointments
    INSERT INTO dental_appointments (clinic_id, patient_name, patient_phone, scheduled_date, scheduled_time, service_type, status)
    VALUES
        (new_clinic_id, 'John Smith', '+1 555-0101', CURRENT_DATE + INTERVAL '1 day', '09:00', 'Cleaning', 'confirmed'),
        (new_clinic_id, 'Jane Doe', '+1 555-0102', CURRENT_DATE + INTERVAL '1 day', '10:30', 'Checkup', 'scheduled'),
        (new_clinic_id, 'Bob Johnson', '+1 555-0103', CURRENT_DATE + INTERVAL '1 day', '14:00', 'Filling', 'confirmed'),
        (new_clinic_id, 'Alice Brown', '+1 555-0104', CURRENT_DATE + INTERVAL '2 days', '09:00', 'Crown', 'scheduled'),
        (new_clinic_id, 'Charlie Wilson', '+1 555-0105', CURRENT_DATE + INTERVAL '2 days', '11:00', 'Whitening', 'confirmed'),
        (new_clinic_id, 'Diana Miller', '+1 555-0106', CURRENT_DATE + INTERVAL '2 days', '15:00', 'Cleaning', 'scheduled'),
        (new_clinic_id, 'Edward Davis', '+1 555-0107', CURRENT_DATE + INTERVAL '3 days', '10:00', 'Checkup', 'scheduled'),
        (new_clinic_id, 'Fiona Garcia', '+1 555-0108', CURRENT_DATE + INTERVAL '3 days', '13:00', 'Extraction', 'confirmed'),
        (new_clinic_id, 'George Lee', '+1 555-0109', CURRENT_DATE + INTERVAL '4 days', '09:00', 'Cleaning', 'scheduled'),
        (new_clinic_id, 'Helen Martinez', '+1 555-0110', CURRENT_DATE + INTERVAL '4 days', '14:30', 'Root Canal', 'confirmed');

    RAISE NOTICE 'SUCCESS! Created clinic "Bright Smile Dental" for user: %', target_user_id;
    RAISE NOTICE 'Clinic ID: %', new_clinic_id;
    RAISE NOTICE 'Added 15 demo calls and 10 appointments.';
END $$;

-- =====================================================
-- OPTION 2: Create clinic for a SPECIFIC email
-- =====================================================
-- Uncomment and modify this if you want to target a specific user

/*
DO $$
DECLARE
    target_email TEXT := 'thelyricboy@gmail.com';  -- Change this to your email
    target_user_id UUID;
    new_clinic_id UUID;
BEGIN
    -- Find user by email
    SELECT id INTO target_user_id
    FROM auth.users
    WHERE email = target_email;

    IF target_user_id IS NULL THEN
        RAISE EXCEPTION 'User with email % not found!', target_email;
    END IF;

    -- Check if user already has a clinic
    IF EXISTS (SELECT 1 FROM dental_clinics WHERE owner_id = target_user_id) THEN
        RAISE NOTICE 'User % already has a clinic!', target_email;
        RETURN;
    END IF;

    -- Create clinic
    INSERT INTO dental_clinics (owner_id, name, phone, address, twilio_number)
    VALUES (
        target_user_id,
        'Bright Smile Dental',
        '(555) 123-4567',
        '123 Main Street, Suite 100, City, State 12345',
        '+15551234567'
    )
    RETURNING id INTO new_clinic_id;

    -- Create settings
    INSERT INTO dental_clinic_settings (clinic_id, agent_name, agent_voice, services, dentist_names)
    VALUES (
        new_clinic_id,
        'Sarah',
        'aura-asteria-en',
        ARRAY['cleaning', 'checkup', 'filling', 'crown', 'whitening'],
        ARRAY['Dr. Smith', 'Dr. Johnson']
    );

    RAISE NOTICE 'Created clinic for %: ID = %', target_email, new_clinic_id;
END $$;
*/

-- =====================================================
-- VERIFY YOUR SETUP
-- =====================================================
-- Run this to see all users and their clinics:

SELECT 
    u.email,
    u.id as user_id,
    c.name as clinic_name,
    c.id as clinic_id,
    (SELECT COUNT(*) FROM dental_calls WHERE clinic_id = c.id) as call_count
FROM auth.users u
LEFT JOIN dental_clinics c ON c.owner_id = u.id
ORDER BY u.created_at DESC;
