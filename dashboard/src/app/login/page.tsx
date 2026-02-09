'use client'

import { useState, useEffect, Suspense, useRef } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loader2, AlertCircle, ArrowLeft, CheckCircle } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'
import { Turnstile } from '@/components/turnstile'
import { MarketingHeader } from '@/components/landing/marketing-header'
import { MarketingFooter } from '@/components/landing/marketing-footer'

function LoginForm() {
  const [isLoading, setIsLoading] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [captchaToken, setCaptchaToken] = useState<string | null>(null)
  const [captchaError, setCaptchaError] = useState(false)
  const [slowAuth, setSlowAuth] = useState(false)
  const timeoutRef = useRef(false)
  const warnTimerRef = useRef<number | null>(null)
  const hardTimerRef = useRef<number | null>(null)
  const searchParams = useSearchParams()
  
  // Check for messages from signup
  useEffect(() => {
    const message = searchParams.get('message')
    if (message === 'check-email') {
      setSuccessMessage('Account created! Please check your email to confirm your account, then sign in.')
    }
  }, [searchParams])
  
  // Rate limiting state
  const [attempts, setAttempts] = useState(0)
  const [lastAttemptTime, setLastAttemptTime] = useState<number | null>(null)
  const MAX_ATTEMPTS = 5
  const RATE_LIMIT_WINDOW = 15 * 60 * 1000 // 15 minutes
  
  const router = useRouter()
  const supabase = createClient()
  
  // Check rate limiting
  const isRateLimited = () => {
    if (lastAttemptTime && attempts >= MAX_ATTEMPTS) {
      const timeSinceLastAttempt = Date.now() - lastAttemptTime
      if (timeSinceLastAttempt < RATE_LIMIT_WINDOW) {
        const minutesRemaining = Math.ceil((RATE_LIMIT_WINDOW - timeSinceLastAttempt) / 60000)
        setError(`Too many login attempts. Please try again in ${minutesRemaining} minutes.`)
        return true
      } else {
        // Reset rate limit
        setAttempts(0)
        setLastAttemptTime(null)
      }
    }
    return false
  }

  const handleCaptchaError = () => {
    setCaptchaError(true)
    // Log but don't block - invisible CAPTCHA can fail due to ad blockers, VPNs, etc.
    // Login will still work if Supabase doesn't require captcha, or will show
    // a helpful message if Supabase rejects the request
    console.warn('[Login] CAPTCHA failed to load - login blocked until CAPTCHA is available')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    setSlowAuth(false)
    timeoutRef.current = false
    
    // Rate limiting check
    if (isRateLimited()) {
      setIsLoading(false)
      return
    }
    
    // CAPTCHA: include token if available, but don't block login
    // If Supabase requires captcha and token is missing, it will return an error
    // that we handle below with a helpful message
    const authOptions: { captchaToken?: string } = {}
    if (captchaToken) {
      authOptions.captchaToken = captchaToken
    }

    // Track attempt
    setAttempts(prev => prev + 1)
    setLastAttemptTime(Date.now())
    
    warnTimerRef.current = window.setTimeout(() => {
      setSlowAuth(true)
    }, 8000)

    hardTimerRef.current = window.setTimeout(() => {
      timeoutRef.current = true
      setIsLoading(false)
      setError('Sign-in is taking longer than expected (usually under 10 seconds). Please try again.')
    }, 20000)

    const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
      email,
      password,
      options: authOptions,
    })

    if (warnTimerRef.current) {
      clearTimeout(warnTimerRef.current)
      warnTimerRef.current = null
    }
    if (hardTimerRef.current) {
      clearTimeout(hardTimerRef.current)
      hardTimerRef.current = null
    }

    if (timeoutRef.current) {
      return
    }
    
    if (signInError) {
      // Provide more helpful error messages
      if (signInError.message.includes('captcha') || captchaError) {
        setError('Security check failed to load. Please allow challenges.cloudflare.com and try again.')
      } else if (signInError.message.includes('Invalid login')) {
        setError('Invalid email or password. Please check your credentials.')
      } else if (signInError.message.includes('Email not confirmed') || signInError.message.includes('email_not_confirmed')) {
        setError('Please check your email and click the confirmation link to verify your account.')
      } else {
        setError(signInError.message)
      }
      setIsLoading(false)
      return
    }

    const user = signInData?.user

    if (user) {
      try {
        const { data: existingClinic } = await supabase
          .from('dental_clinics')
          .select('id')
          .eq('owner_id', user.id)
          .maybeSingle()

        if (!existingClinic?.id) {
          const trialExpiresAt = new Date()
          trialExpiresAt.setDate(trialExpiresAt.getDate() + 9)

          const clinicName = (user.user_metadata?.clinic_name as string | undefined) || 'Your Dental Practice'
          const ownerName = `${user.user_metadata?.first_name || ''} ${user.user_metadata?.last_name || ''}`.trim()

          const { data: newClinic, error: clinicCreateError } = await supabase
            .from('dental_clinics')
            .insert({
              owner_id: user.id,
              name: clinicName,
              owner_name: ownerName || null,
              subscription_status: 'trial',
              subscription_expires_at: trialExpiresAt.toISOString(),
            })
            .select('id')
            .single()

          if (!clinicCreateError && newClinic?.id) {
            await supabase
              .from('dental_clinic_settings')
              .insert({
                clinic_id: newClinic.id,
                agent_name: 'Sarah',
                agent_voice: 'aura-asteria-en',
                greeting_template: `Thank you for calling ${clinicName}. This is Sarah, how may I help you today?`,
              })
          }
        }
      } catch (error) {
        console.error('[Login] Failed to create clinic on first login:', error)
      }
    }
    
    router.push('/dashboard')
    router.refresh()
  }

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-blue-50 to-white text-slate-900">
      <MarketingHeader />

      <main className="flex flex-1 items-center justify-center px-4 py-10">
        <Card className="w-full max-w-md shadow-lg">
          <div className="p-4 pb-0">
            <Link href="/" className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-primary">
              <ArrowLeft className="h-4 w-4" />
              Back to Home
            </Link>
          </div>
          <CardHeader className="text-center pt-2">
            <div className="mx-auto mb-4">
              <Image
                src="/logo.svg"
                alt="DentSignal"
                width={120}
                height={40}
                priority
                className="h-[40px] object-contain"
                style={{ width: 'auto' }}
              />
            </div>
            <CardTitle className="text-2xl">Welcome Back</CardTitle>
            <CardDescription>
              Sign in to your DentSignal Dashboard
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {successMessage && (
                <div className="flex items-center gap-2 rounded-lg bg-green-50 p-3 text-sm text-green-700" role="status" aria-live="polite">
                  <CheckCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
                  {successMessage}
                </div>
              )}
              {error && (
                <div className="flex items-center gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-600" role="alert" aria-live="polite">
                  <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
                  {error}
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@clinic.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">Password</Label>
                  <Link href="/forgot-password" className="text-xs text-primary hover:underline">
                    Forgot password?
                  </Link>
                </div>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />
              </div>
              
              {/* Visible Turnstile CAPTCHA with graceful degradation */}
              <Turnstile 
                onVerify={setCaptchaToken}
                onError={handleCaptchaError}
                onExpire={() => setCaptchaToken(null)}
                mode="normal"
              />
              
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  'Sign In'
                )}
              </Button>
              {slowAuth && (
                <p className="text-xs text-muted-foreground" role="status" aria-live="polite">
                  Still working... this usually takes under 10 seconds.
                </p>
              )}
            </form>

            <div className="mt-6 text-center text-sm text-muted-foreground">
              Don&apos;t have an account?{' '}
              <Link href="/signup" className="text-primary hover:underline">
                Sign up
              </Link>
            </div>
          </CardContent>
        </Card>
      </main>

      <MarketingFooter />
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    }>
      <LoginForm />
    </Suspense>
  )
}
