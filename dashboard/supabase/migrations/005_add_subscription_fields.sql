-- =====================================================
-- Payment/Subscription Fields for dental_clinics
-- Minimal v0: Just 3 columns to gate dashboard access
-- =====================================================

-- Add subscription columns to dental_clinics
ALTER TABLE dental_clinics 
ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'trial' 
    CHECK (subscription_status IN ('trial', 'active', 'expired', 'cancelled')),
ADD COLUMN IF NOT EXISTS subscription_expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),
ADD COLUMN IF NOT EXISTS plan_type TEXT DEFAULT 'starter_149' 
    CHECK (plan_type IN ('starter_149', 'pro_199'));

-- Index for faster subscription checks
CREATE INDEX IF NOT EXISTS idx_dental_clinics_subscription 
ON dental_clinics(subscription_status, subscription_expires_at);

-- Comment for documentation
COMMENT ON COLUMN dental_clinics.subscription_status IS 'trial = 7-day trial, active = paid, expired = not renewed, cancelled = user cancelled';
COMMENT ON COLUMN dental_clinics.subscription_expires_at IS 'Dashboard access blocked after this date';
COMMENT ON COLUMN dental_clinics.plan_type IS 'starter_149 = $149/mo, pro_199 = $199/mo';
