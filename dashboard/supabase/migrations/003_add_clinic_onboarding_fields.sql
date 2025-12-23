-- =====================================================
-- Migration: Add onboarding fields to dental_clinics
-- Date: 2024-12-23
-- Description: Adds fields collected during signup for better onboarding
-- =====================================================

-- Add new columns to dental_clinics table
ALTER TABLE dental_clinics ADD COLUMN IF NOT EXISTS owner_name TEXT;
ALTER TABLE dental_clinics ADD COLUMN IF NOT EXISTS monthly_call_volume INTEGER DEFAULT 500;
ALTER TABLE dental_clinics ADD COLUMN IF NOT EXISTS current_answer_rate INTEGER DEFAULT 50;
ALTER TABLE dental_clinics ADD COLUMN IF NOT EXISTS reminder_method VARCHAR(10) DEFAULT 'sms';

-- Add status column for calls (active tracking for live dashboard)
ALTER TABLE dental_calls ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'completed' 
    CHECK (status IN ('active', 'ringing', 'in_progress', 'transferring', 'completed', 'failed'));

-- Add caller_name to calls
ALTER TABLE dental_calls ADD COLUMN IF NOT EXISTS caller_name TEXT;

-- Add receptionist notes for handoff
ALTER TABLE dental_calls ADD COLUMN IF NOT EXISTS receptionist_notes TEXT;

-- Add AI handling metadata
ALTER TABLE dental_calls ADD COLUMN IF NOT EXISTS ai_handled BOOLEAN DEFAULT TRUE;
ALTER TABLE dental_calls ADD COLUMN IF NOT EXISTS transferred_to TEXT;
ALTER TABLE dental_calls ADD COLUMN IF NOT EXISTS transfer_reason TEXT;

-- Create index for active calls (for live dashboard)
CREATE INDEX IF NOT EXISTS idx_dental_calls_status ON dental_calls(status);
CREATE INDEX IF NOT EXISTS idx_dental_calls_active ON dental_calls(clinic_id, status) WHERE status = 'active';

-- =====================================================
-- Comments for documentation
-- =====================================================
COMMENT ON COLUMN dental_clinics.owner_name IS 'Name of the dentist/owner collected during signup';
COMMENT ON COLUMN dental_clinics.monthly_call_volume IS 'Estimated monthly call volume from signup';
COMMENT ON COLUMN dental_clinics.current_answer_rate IS 'Current answer rate percentage (0-100)';
COMMENT ON COLUMN dental_clinics.reminder_method IS 'Preferred reminder method: sms or email';
COMMENT ON COLUMN dental_calls.status IS 'Real-time call status for live dashboard';
COMMENT ON COLUMN dental_calls.receptionist_notes IS 'Notes added by receptionist after transfer';
