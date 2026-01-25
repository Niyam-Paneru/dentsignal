-- Migration: Add SMS templates to dental_clinics
-- Purpose: Support customizable SMS templates for appointment reminders and recalls

-- Add SMS template columns to dental_clinics
ALTER TABLE dental_clinics 
ADD COLUMN IF NOT EXISTS sms_templates TEXT DEFAULT NULL;

ALTER TABLE dental_clinics 
ADD COLUMN IF NOT EXISTS sms_confirmation_enabled BOOLEAN DEFAULT TRUE;

ALTER TABLE dental_clinics 
ADD COLUMN IF NOT EXISTS sms_reminder_24h_enabled BOOLEAN DEFAULT TRUE;

ALTER TABLE dental_clinics 
ADD COLUMN IF NOT EXISTS sms_reminder_2h_enabled BOOLEAN DEFAULT TRUE;

ALTER TABLE dental_clinics 
ADD COLUMN IF NOT EXISTS sms_recall_enabled BOOLEAN DEFAULT TRUE;

-- Add comments for documentation
COMMENT ON COLUMN dental_clinics.sms_templates IS 'JSON object containing custom SMS templates: {confirmation, reminder_24h, reminder_2h, recall, recall_followup}';
COMMENT ON COLUMN dental_clinics.sms_confirmation_enabled IS 'Enable/disable appointment confirmation SMS';
COMMENT ON COLUMN dental_clinics.sms_reminder_24h_enabled IS 'Enable/disable 24-hour reminder SMS';
COMMENT ON COLUMN dental_clinics.sms_reminder_2h_enabled IS 'Enable/disable 2-hour reminder SMS';
COMMENT ON COLUMN dental_clinics.sms_recall_enabled IS 'Enable/disable recall/reactivation SMS';

-- Grant permissions (RLS already handles per-clinic access)
-- The existing policies on dental_clinics will apply to these new columns
