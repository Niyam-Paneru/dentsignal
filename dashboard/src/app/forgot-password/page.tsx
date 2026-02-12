'use client'

import { useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loader2, AlertCircle, ArrowLeft, Mail } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'
import { MarketingHeader } from '@/components/landing/marketing-header'
import { MarketingFooter } from '@/components/landing/marketing-footer'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sent, setSent] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    try {
      const supabase = createClient()
      if (!supabase) {
        setError('Service temporarily unavailable. Please try again later.')
        setIsLoading(false)
        return
      }

      const { error: resetError } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/callback?next=/reset-password`,
      })

      if (resetError) {
        // Don't reveal whether email exists (security best practice)
        if (resetError.message.includes('rate') || resetError.message.includes('limit')) {
          setError('Too many requests. Please wait a few minutes and try again.')
        } else {
          // Always show success to prevent email enumeration
          setSent(true)
        }
      } else {
        setSent(true)
      }
    } catch {
      setError('Something went wrong. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-blue-50 to-white text-slate-900">
      <MarketingHeader />

      <main className="flex flex-1 items-center justify-center px-4 py-10">
        <Card className="w-full max-w-md shadow-lg">
          <div className="p-4 pb-0">
            <Link href="/login" className="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-primary">
              <ArrowLeft className="h-4 w-4" />
              Back to Sign In
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
            <CardTitle className="text-2xl">Reset Your Password</CardTitle>
            <CardDescription>
              {sent
                ? 'Check your email for a reset link'
                : "Enter your email and we'll send you a reset link"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {sent ? (
              <div className="space-y-4">
                <div className="flex flex-col items-center gap-3 rounded-lg bg-green-50 p-6 text-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
                    <Mail className="h-6 w-6 text-green-600" />
                  </div>
                  <p className="text-sm text-green-700">
                    If an account exists for <strong>{email}</strong>, you&apos;ll receive a password reset link shortly.
                  </p>
                  <p className="text-xs text-green-600">
                    Check your spam folder if you don&apos;t see it within a few minutes.
                  </p>
                </div>
                <Button asChild variant="outline" className="w-full">
                  <Link href="/login">Return to Sign In</Link>
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="flex items-center gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-600" role="alert" aria-live="polite">
                    <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
                    {error}
                  </div>
                )}
                <div className="space-y-2">
                  <Label htmlFor="email">Email address</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@clinic.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email"
                    autoFocus
                    required
                  />
                </div>
                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    'Send Reset Link'
                  )}
                </Button>
              </form>
            )}

            <div className="mt-6 text-center text-sm text-muted-foreground">
              Remember your password?{' '}
              <Link href="/login" className="text-primary hover:underline">
                Sign in
              </Link>
            </div>
          </CardContent>
        </Card>
      </main>

      <MarketingFooter />
    </div>
  )
}
