'use client'

import { useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loader2, AlertCircle, ArrowLeft } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'
import { Turnstile } from '@/components/turnstile'
import { MarketingHeader } from '@/components/landing/marketing-header'
import { MarketingFooter } from '@/components/landing/marketing-footer'

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [captchaToken, setCaptchaToken] = useState<string | null>(null)
  
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    
    // Rate limiting check
    if (isRateLimited()) {
      setIsLoading(false)
      return
    }
    
    // Track attempt
    setAttempts(prev => prev + 1)
    setLastAttemptTime(Date.now())
    
    const { error: signInError } = await supabase.auth.signInWithPassword({
      email,
      password,
      options: {
        captchaToken: captchaToken || undefined,
      },
    })
    
    if (signInError) {
      setError(signInError.message)
      setIsLoading(false)
      return
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
              
              {/* Invisible Turnstile CAPTCHA */}
              <Turnstile 
                onVerify={setCaptchaToken}
                onExpire={() => setCaptchaToken(null)}
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
