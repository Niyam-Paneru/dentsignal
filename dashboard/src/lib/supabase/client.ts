import { createBrowserClient } from '@supabase/ssr'

/**
 * Create a Supabase browser client.
 * Returns null if env vars are missing (so public pages degrade gracefully).
 */
export function createClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  if (!url || !key) {
    console.warn('[Supabase] Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY')
    return null
  }

  return createBrowserClient(url, key)
}

/** Convenience: returns a non-null client or throws (use in auth-required contexts). */
export function requireClient() {
  const client = createClient()
  if (!client) throw new Error('Supabase client is not configured')
  return client
}
