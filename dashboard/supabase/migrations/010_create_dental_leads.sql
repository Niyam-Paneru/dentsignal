-- Migration: Create dental_leads table for email capture (exit-intent, landing page forms)
-- This stores marketing leads from the public website

CREATE TABLE IF NOT EXISTS dental_leads (
  id BIGSERIAL PRIMARY KEY,
  email TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'exit-intent',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Index for deduplication and lookup
CREATE UNIQUE INDEX IF NOT EXISTS idx_dental_leads_email_source ON dental_leads (email, source);
CREATE INDEX IF NOT EXISTS idx_dental_leads_created_at ON dental_leads (created_at DESC);

-- RLS: Allow anonymous inserts (public website), only authenticated super admins can read
ALTER TABLE dental_leads ENABLE ROW LEVEL SECURITY;

-- Anyone can insert (public lead capture from website)
CREATE POLICY "Allow anonymous lead inserts"
  ON dental_leads
  FOR INSERT
  TO anon, authenticated
  WITH CHECK (true);

-- Only authenticated users can read leads (super admin will check in app code)
CREATE POLICY "Allow authenticated users to read leads"
  ON dental_leads
  FOR SELECT
  TO authenticated
  USING (true);
