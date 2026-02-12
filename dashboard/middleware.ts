import { type NextRequest } from 'next/server'
import { updateSession } from '@/lib/supabase/middleware'

/**
 * Nonce-based CSP middleware.
 *
 * Generates a per-request cryptographic nonce so Next.js can whitelist its
 * own inline <script> tags without resorting to 'unsafe-inline'.
 *
 * Next.js automatically reads the nonce from the CSP header at
 * `Content-Security-Policy` (via `get-script-nonce-from-header.js`).
 */
export async function middleware(request: NextRequest) {
  // 1. Generate a cryptographic nonce for this request
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')

  // 2. Build a strict Content-Security-Policy with the nonce
  const csp = [
    "default-src 'self'",
    // 'strict-dynamic' trusts scripts injected by nonce-authorised scripts,
    // which covers Next.js chunk loading.  'unsafe-inline' is ignored by
    // browsers that understand 'nonce-…', so it only serves as a fallback
    // for very old user agents.
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic' https://challenges.cloudflare.com`,
    // Tailwind / Next.js both inject inline <style> elements at runtime.
    // Until Next.js supports style nonces this must remain 'unsafe-inline'.
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https: blob:",
    "font-src 'self' data:",
    "connect-src 'self' https://*.supabase.co https://challenges.cloudflare.com wss://*.supabase.co",
    "frame-src https://challenges.cloudflare.com",
    "frame-ancestors 'none'",
    "worker-src 'self' blob:",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; ')

  // 3. Forward the nonce to the server-rendered page via request headers
  //    so Next.js can pick it up for inline scripts.
  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('x-nonce', nonce)
  requestHeaders.set('Content-Security-Policy', csp)

  // 4. Run Supabase session management (auth, redirects, cookies)
  const response = await updateSession(request)

  // 5. Stamp the CSP + nonce onto the outgoing response
  response.headers.set('Content-Security-Policy', csp)
  response.headers.set('x-nonce', nonce)

  return response
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
