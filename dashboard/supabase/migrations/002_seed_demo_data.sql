-- =====================================================
-- Dental AI Dashboard - Demo Data
-- Run this AFTER you sign up with your email
-- =====================================================

-- IMPORTANT: First, find your user ID from Supabase Auth
-- Go to Authentication > Users in Supabase dashboard
-- Copy your user's UUID

-- Replace 'YOUR_USER_ID_HERE' with your actual user UUID
-- Example: '12345678-1234-1234-1234-123456789012'

-- =====================================================
-- STEP 1: Insert your clinic (REQUIRED)
-- =====================================================
-- Run this query to insert a clinic for yourself
-- Replace YOUR_USER_ID_HERE with your UUID from Supabase Auth > Users

INSERT INTO dental_clinics (owner_id, name, phone, address, twilio_number)
VALUES (
    'YOUR_USER_ID_HERE',  -- Replace with your actual user UUID
    'My Dental Clinic',   -- Change to your clinic name
    '(555) 123-4567',
    '123 Main Street, City, State 12345',
    '+15551234567'
)
RETURNING id;

-- Copy the returned clinic ID and use it below

-- =====================================================
-- STEP 2: Insert clinic settings
-- =====================================================
-- Replace CLINIC_ID_HERE with the ID returned above

INSERT INTO dental_clinic_settings (clinic_id, agent_name, agent_voice, services, dentist_names)
VALUES (
    'CLINIC_ID_HERE',  -- Replace with clinic ID from step 1
    'Sarah',
    'aura-asteria-en',
    ARRAY['cleaning', 'checkup', 'filling', 'crown', 'whitening', 'extraction', 'root canal'],
    ARRAY['Dr. Smith', 'Dr. Johnson']
);

-- =====================================================
-- STEP 3: Insert demo calls (optional - for testing)
-- =====================================================
-- Replace CLINIC_ID_HERE with your clinic ID

INSERT INTO dental_calls (clinic_id, caller_phone, started_at, duration_seconds, outcome, call_reason, sentiment, quality_score, summary)
VALUES
    ('CLINIC_ID_HERE', '+1 555-0101', NOW() - INTERVAL '1 hour', 185, 'booked', 'New Patient Inquiry', 'positive', 92, 'New patient called to schedule first cleaning. Booked for next week.'),
    ('CLINIC_ID_HERE', '+1 555-0102', NOW() - INTERVAL '2 hours', 120, 'info', 'Insurance Question', 'neutral', 78, 'Patient asked about Delta Dental coverage. Provided information.'),
    ('CLINIC_ID_HERE', '+1 555-0103', NOW() - INTERVAL '3 hours', 145, 'booked', 'Reschedule Appointment', 'positive', 85, 'Existing patient rescheduled cleaning from Monday to Thursday.'),
    ('CLINIC_ID_HERE', '+1 555-0104', NOW() - INTERVAL '4 hours', 45, 'transferred', 'Emergency - Tooth Pain', 'negative', 65, 'Patient with severe pain. Transferred to on-call dentist.'),
    ('CLINIC_ID_HERE', '+1 555-0105', NOW() - INTERVAL '5 hours', 200, 'booked', 'Whitening Consultation', 'positive', 88, 'Patient interested in teeth whitening. Booked consultation.'),
    ('CLINIC_ID_HERE', '+1 555-0106', NOW() - INTERVAL '1 day', 90, 'inquiry', 'Pricing Question', 'neutral', 72, 'Asked about cleaning costs. Will call back to book.'),
    ('CLINIC_ID_HERE', '+1 555-0107', NOW() - INTERVAL '1 day 2 hours', 160, 'booked', 'Checkup Appointment', 'positive', 90, 'Regular checkup booked for returning patient.'),
    ('CLINIC_ID_HERE', '+1 555-0108', NOW() - INTERVAL '2 days', 30, 'missed', NULL, NULL, NULL, NULL),
    ('CLINIC_ID_HERE', '+1 555-0109', NOW() - INTERVAL '2 days 3 hours', 175, 'booked', 'Crown Replacement', 'positive', 82, 'Patient needs crown replaced. Booked procedure.'),
    ('CLINIC_ID_HERE', '+1 555-0110', NOW() - INTERVAL '3 days', 110, 'info', 'Hours Question', 'positive', 75, 'Asked about Saturday hours. Confirmed we are open.'),
    ('CLINIC_ID_HERE', '+1 555-0111', NOW() - INTERVAL '4 days', 195, 'booked', 'Family Appointment', 'positive', 95, 'Booked appointments for entire family - 4 cleanings.'),
    ('CLINIC_ID_HERE', '+1 555-0112', NOW() - INTERVAL '5 days', 80, 'cancelled', 'Cancel Appointment', 'neutral', 70, 'Patient cancelled due to work conflict. Will reschedule.');

-- =====================================================
-- STEP 4: Insert demo appointments (optional)
-- =====================================================
-- Replace CLINIC_ID_HERE with your clinic ID

INSERT INTO dental_appointments (clinic_id, patient_name, patient_phone, scheduled_date, scheduled_time, service_type, status)
VALUES
    ('CLINIC_ID_HERE', 'John Smith', '+1 555-0101', CURRENT_DATE + INTERVAL '1 day', '09:00', 'Cleaning', 'confirmed'),
    ('CLINIC_ID_HERE', 'Jane Doe', '+1 555-0102', CURRENT_DATE + INTERVAL '1 day', '10:30', 'Checkup', 'scheduled'),
    ('CLINIC_ID_HERE', 'Bob Johnson', '+1 555-0103', CURRENT_DATE + INTERVAL '1 day', '14:00', 'Filling', 'confirmed'),
    ('CLINIC_ID_HERE', 'Alice Brown', '+1 555-0104', CURRENT_DATE + INTERVAL '2 days', '09:00', 'Crown', 'scheduled'),
    ('CLINIC_ID_HERE', 'Charlie Wilson', '+1 555-0105', CURRENT_DATE + INTERVAL '2 days', '11:00', 'Whitening', 'confirmed'),
    ('CLINIC_ID_HERE', 'Diana Miller', '+1 555-0106', CURRENT_DATE + INTERVAL '2 days', '15:00', 'Cleaning', 'scheduled'),
    ('CLINIC_ID_HERE', 'Edward Davis', '+1 555-0107', CURRENT_DATE + INTERVAL '3 days', '10:00', 'Checkup', 'scheduled'),
    ('CLINIC_ID_HERE', 'Fiona Garcia', '+1 555-0108', CURRENT_DATE + INTERVAL '3 days', '13:00', 'Extraction', 'confirmed');

-- =====================================================
-- QUICK SETUP SCRIPT (Run this all at once after replacing IDs)
-- =====================================================
-- After you sign up and get your user UUID, you can run this:
--
-- DO $$
-- DECLARE
--     new_clinic_id UUID;
--     my_user_id UUID := 'YOUR_USER_ID_HERE';  -- Replace this
-- BEGIN
--     -- Create clinic
--     INSERT INTO dental_clinics (owner_id, name, phone, address)
--     VALUES (my_user_id, 'My Dental Clinic', '(555) 123-4567', '123 Main St')
--     RETURNING id INTO new_clinic_id;
--     
--     -- Create settings
--     INSERT INTO dental_clinic_settings (clinic_id, agent_name)
--     VALUES (new_clinic_id, 'Sarah');
--     
--     -- Add demo calls
--     INSERT INTO dental_calls (clinic_id, caller_phone, started_at, duration_seconds, outcome, call_reason, sentiment, quality_score)
--     VALUES
--         (new_clinic_id, '+1 555-0101', NOW() - INTERVAL '1 hour', 185, 'booked', 'New Patient', 'positive', 92),
--         (new_clinic_id, '+1 555-0102', NOW() - INTERVAL '2 hours', 120, 'info', 'Insurance Question', 'neutral', 78),
--         (new_clinic_id, '+1 555-0103', NOW() - INTERVAL '3 hours', 145, 'booked', 'Reschedule', 'positive', 85);
--     
--     RAISE NOTICE 'Created clinic with ID: %', new_clinic_id;
-- END $$;
