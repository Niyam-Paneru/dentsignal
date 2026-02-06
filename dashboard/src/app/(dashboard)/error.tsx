'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { AlertCircle, RefreshCw, LogIn } from 'lucide-react'

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const router = useRouter()

  // Check if this is an auth-related error
  const isAuthError = 
    error.message?.includes('Refresh Token') ||
    error.message?.includes('refresh_token') ||
    error.message?.includes('AuthApiError') ||
    error.message?.includes('session') ||
    error.message?.includes('JWT') ||
    error.message?.includes('token')

  useEffect(() => {
    // Log error for debugging (without PII)
    console.error('Dashboard error:', error.message)
    
    // Auto-redirect to login for auth errors after a brief delay
    if (isAuthError) {
      const timeout = setTimeout(() => {
        router.push('/login')
      }, 3000)
      return () => clearTimeout(timeout)
    }
  }, [error, isAuthError, router])

  const handleLogin = () => {
    // Clear any stale auth state
    router.push('/logout')
  }

  const handleRetry = () => {
    reset()
  }

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md text-center space-y-6">
        <div className="flex justify-center">
          <div className="rounded-full bg-red-100 p-4">
            <AlertCircle className="h-8 w-8 text-red-600" />
          </div>
        </div>
        
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-foreground">
            {isAuthError ? 'Session Expired' : 'Something went wrong'}
          </h1>
          <p className="text-muted-foreground text-sm sm:text-base">
            {isAuthError 
              ? 'Your session has expired. Please sign in again to continue.'
              : 'An unexpected error occurred. Please try again.'}
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          {isAuthError ? (
            <>
              <Button 
                onClick={handleLogin}
                className="w-full sm:w-auto"
              >
                <LogIn className="mr-2 h-4 w-4" />
                Sign In Again
              </Button>
              <p className="text-xs text-muted-foreground">
                Redirecting automatically in 3 seconds...
              </p>
            </>
          ) : (
            <>
              <Button 
                onClick={handleRetry}
                className="w-full sm:w-auto"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Try Again
              </Button>
              <Button 
                variant="outline" 
                onClick={() => router.push('/dashboard')}
                className="w-full sm:w-auto"
              >
                Go to Dashboard
              </Button>
            </>
          )}
        </div>

        {process.env.NODE_ENV === 'development' && (
          <details className="mt-6 text-left">
            <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
              Technical Details
            </summary>
            <pre className="mt-2 p-4 bg-muted rounded-lg text-xs overflow-auto max-h-40">
              {error.message}
              {error.digest && `\nDigest: ${error.digest}`}
            </pre>
          </details>
        )}
      </div>
    </div>
  )
}
