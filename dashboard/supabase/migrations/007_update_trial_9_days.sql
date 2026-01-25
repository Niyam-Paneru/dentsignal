-- =====================================================
-- Update Trial Period to 9 Days + Add Manual Activation Fields
-- Migration: 007_update_trial_9_days.sql
-- =====================================================

-- Update default trial period to 9 days for new clinics
ALTER TABLE dental_clinics 
ALTER COLUMN subscription_expires_at SET DEFAULT (NOW() + INTERVAL '9 days');

-- Add last_payment_date for tracking manual payments
ALTER TABLE dental_clinics 
ADD COLUMN IF NOT EXISTS last_payment_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS payment_notes TEXT,
ADD COLUMN IF NOT EXISTS activated_by TEXT;

-- Add index for easier payment tracking
CREATE INDEX IF NOT EXISTS idx_dental_clinics_last_payment 
ON dental_clinics(last_payment_date DESC);

-- Comment for documentation
COMMENT ON COLUMN dental_clinics.last_payment_date IS 'When the last payment was received (manual tracking for Payoneer)';
COMMENT ON COLUMN dental_clinics.payment_notes IS 'Admin notes about payment (e.g., "Payoneer transaction #12345")';
COMMENT ON COLUMN dental_clinics.activated_by IS 'Admin email who activated the subscription';

-- Update existing trial clinics that still have 7-day trial to 9 days
-- Only affects clinics still in trial with expiry in the future
UPDATE dental_clinics 
SET subscription_expires_at = created_at + INTERVAL '9 days'
WHERE subscription_status = 'trial' 
AND subscription_expires_at > NOW();
