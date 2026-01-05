-- Add transfer settings fields to dental_clinics
-- These support the new call transfer configuration in settings

ALTER TABLE dental_clinics 
ADD COLUMN IF NOT EXISTS emergency_phone VARCHAR(20),
ADD COLUMN IF NOT EXISTS transfer_fallback VARCHAR(20) DEFAULT 'voicemail';

-- Add comment for documentation
COMMENT ON COLUMN dental_clinics.emergency_phone IS 'Emergency contact number for urgent transfers';
COMMENT ON COLUMN dental_clinics.transfer_fallback IS 'Behavior when transfer fails: voicemail, callback_30m, callback_1h, callback_2h, retry';
