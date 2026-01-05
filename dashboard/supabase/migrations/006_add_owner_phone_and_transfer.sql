-- Migration: Add owner phone number and transfer settings
-- Purpose: Enable "Transfer to Me" feature for live call takeover

-- Add owner phone number to dental_clinics
ALTER TABLE dental_clinics 
ADD COLUMN IF NOT EXISTS owner_phone VARCHAR(20),
ADD COLUMN IF NOT EXISTS transfer_enabled BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS transfer_timeout_seconds INTEGER DEFAULT 20;

-- Add comment explaining the fields
COMMENT ON COLUMN dental_clinics.owner_phone IS 'Owner personal/cell phone for receiving transferred calls';
COMMENT ON COLUMN dental_clinics.transfer_enabled IS 'Whether transfer-to-owner feature is enabled';
COMMENT ON COLUMN dental_clinics.transfer_timeout_seconds IS 'Seconds to wait for owner to answer before fallback';

-- Create call_transfers table to track transfer events
CREATE TABLE IF NOT EXISTS call_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID REFERENCES dental_calls(id) ON DELETE CASCADE,
    clinic_id UUID REFERENCES dental_clinics(id) ON DELETE CASCADE,
    call_sid VARCHAR(64) NOT NULL,
    from_phone VARCHAR(20),
    to_phone VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'ringing', 'answered', 'no_answer', 'failed', 'completed')),
    initiated_at TIMESTAMPTZ DEFAULT NOW(),
    answered_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    initiated_by VARCHAR(100),
    failure_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_call_transfers_call_sid ON call_transfers(call_sid);
CREATE INDEX IF NOT EXISTS idx_call_transfers_clinic_id ON call_transfers(clinic_id);
CREATE INDEX IF NOT EXISTS idx_call_transfers_status ON call_transfers(status);

-- Add RLS policies for call_transfers
ALTER TABLE call_transfers ENABLE ROW LEVEL SECURITY;

-- Clinic owners can only see their own transfers
CREATE POLICY "Users can view own clinic transfers" ON call_transfers
    FOR SELECT
    USING (
        clinic_id IN (
            SELECT id FROM dental_clinics WHERE owner_id = auth.uid()
        )
    );

-- Allow insert from authenticated users for their clinic
CREATE POLICY "Users can insert transfers for own clinic" ON call_transfers
    FOR INSERT
    WITH CHECK (
        clinic_id IN (
            SELECT id FROM dental_clinics WHERE owner_id = auth.uid()
        )
    );

-- Allow update for own clinic transfers
CREATE POLICY "Users can update own clinic transfers" ON call_transfers
    FOR UPDATE
    USING (
        clinic_id IN (
            SELECT id FROM dental_clinics WHERE owner_id = auth.uid()
        )
    );
