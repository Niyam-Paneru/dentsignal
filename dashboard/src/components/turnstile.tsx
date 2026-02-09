'use client'

import { useState, useCallback } from 'react'
import { Turnstile as TurnstileWidget } from '@marsidev/react-turnstile'

interface TurnstileProps {
  onVerify: (token: string) => void
  onError?: () => void
  onExpire?: () => void
  mode?: 'normal' | 'invisible'
}

const TURNSTILE_SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || ''

export function Turnstile({ onVerify, onError, onExpire, mode = 'normal' }: TurnstileProps) {
  const [loadFailed, setLoadFailed] = useState(false)
  const [retryKey, setRetryKey] = useState(0)

  const handleError = useCallback(() => {
    console.warn('[Turnstile] CAPTCHA challenge failed')
    setLoadFailed(true)
    onError?.()
  }, [onError])

  if (!TURNSTILE_SITE_KEY) {
    console.warn('[Turnstile] Missing NEXT_PUBLIC_TURNSTILE_SITE_KEY')
    return (
      <div className="text-xs text-amber-600 text-center py-1">
        Security check unavailable — site key not configured.
      </div>
    )
  }

  if (loadFailed && mode === 'normal') {
    return (
      <div className="text-xs text-amber-600 text-center py-1">
        Security check unavailable. Please refresh or contact support.
        <button
          type="button"
          className="ml-2 underline"
          onClick={() => {
            setLoadFailed(false)
            setRetryKey((k) => k + 1)
          }}
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <TurnstileWidget
      key={retryKey}
      siteKey={TURNSTILE_SITE_KEY}
      onSuccess={onVerify}
      onError={handleError}
      onExpire={() => {
        onExpire?.()
      }}
      options={{
        theme: 'light',
        size: mode === 'normal' ? 'normal' : 'invisible',
        retry: 'auto',
        retryInterval: 3000,
      }}
    />
  )
}
