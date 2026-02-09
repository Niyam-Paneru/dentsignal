import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({
            request,
          })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  // Refresh session if expired - handle auth errors gracefully
  let user = null
  try {
    const { data } = await supabase.auth.getUser()
    user = data?.user
  } catch (error) {
    // Auth error (invalid refresh token, etc.) - clear cookies and redirect to login
    console.error('[Middleware] Auth error:', error instanceof Error ? error.message : 'Unknown error')
    
    // Clear auth cookies
    const response = NextResponse.redirect(new URL('/login', request.url))
    response.cookies.delete('sb-access-token')
    response.cookies.delete('sb-refresh-token')
    
    // Clear all Supabase auth cookies (they start with sb-)
    request.cookies.getAll().forEach(cookie => {
      if (cookie.name.startsWith('sb-')) {
        response.cookies.delete(cookie.name)
      }
    })
    
    return response
  }

  // Protected routes - redirect to login if not authenticated
  const protectedRoutes = ['/dashboard', '/live-calls', '/calls', '/calendar', '/settings', '/analytics', '/superadmin', '/recalls']
  const isProtectedRoute = protectedRoutes.some(route => 
    request.nextUrl.pathname.startsWith(route)
  )

  if (isProtectedRoute && !user) {
    const url = request.nextUrl.clone()
    url.pathname = '/login'
    return NextResponse.redirect(url)
  }

  // Subscription check for protected routes (except superadmin)
  const subscriptionRequiredRoutes = ['/dashboard', '/live-calls', '/calls', '/calendar', '/settings', '/analytics', '/recalls']
  const needsSubscription = subscriptionRequiredRoutes.some(route => 
    request.nextUrl.pathname.startsWith(route)
  )

  // Skip subscription check for /subscription-required page
  if (needsSubscription && user && !request.nextUrl.pathname.startsWith('/subscription-required')) {
    // Check if user has active subscription
    try {
      const { data: clinic } = await supabase
        .from('dental_clinics')
        .select('subscription_status, subscription_expires_at')
        .eq('owner_id', user.id)
        .single()

      // No clinic record yet (signup may still be processing) — allow access
      if (!clinic) {
        return supabaseResponse
      }

      const now = new Date()
      const expiresAt = clinic.subscription_expires_at ? new Date(clinic.subscription_expires_at) : null
      const isTrial = clinic.subscription_status === 'trial'
      const isCancelled = clinic.subscription_status === 'cancelled'

      // Trial/active with valid expiry — allow access
      // Expired or cancelled — block
      const isExpired = expiresAt ? expiresAt < now : false

      if (isCancelled || isExpired) {
        const url = request.nextUrl.clone()
        url.pathname = '/subscription-required'
        return NextResponse.redirect(url)
      }
    } catch (error) {
      // Database error - allow access but log
      console.error('[Middleware] Subscription check error:', error instanceof Error ? error.message : 'Unknown error')
    }
  }

  // Redirect logged in users away from auth pages
  const authRoutes = ['/login', '/signup']
  const isAuthRoute = authRoutes.some(route => 
    request.nextUrl.pathname.startsWith(route)
  )

  if (isAuthRoute && user) {
    const url = request.nextUrl.clone()
    url.pathname = '/dashboard'
    return NextResponse.redirect(url)
  }

  return supabaseResponse
}
