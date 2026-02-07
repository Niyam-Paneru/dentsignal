'use client'

import { useEffect, useRef, useCallback, useState } from 'react'

interface TurnstileProps {
  onVerify: (token: string) => void
  onError?: () => void
  onExpire?: () => void
  mode?: 'normal' | 'invisible'
}

declare global {
  interface Window {
    turnstile: {
      render: (container: HTMLElement, options: {
        sitekey: string
        callback: (token: string) => void
        'error-callback'?: () => void
        'expired-callback'?: () => void
        theme?: 'light' | 'dark' | 'auto'
        size?: 'normal' | 'compact' | 'invisible'
        retry?: 'auto' | 'never'
        'retry-interval'?: number
      }) => string
      reset: (widgetId: string) => void
      remove: (widgetId: string) => void
    }
    onTurnstileLoad?: () => void
  }
}

const TURNSTILE_SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || '0x4AAAAAACJCGDiUek-rJNYJ'

export function Turnstile({ onVerify, onError, onExpire, mode = 'normal' }: TurnstileProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const widgetIdRef = useRef<string | null>(null)
  const [loadFailed, setLoadFailed] = useState(false)
  const retryCountRef = useRef(0)
  const MAX_RETRIES = 2

  const handleError = useCallback(() => {
    retryCountRef.current += 1
    if (retryCountRef.current <= MAX_RETRIES && widgetIdRef.current && window.turnstile) {
      // Auto-retry by resetting the widget
      console.warn(`[Turnstile] Error occurred, retrying (${retryCountRef.current}/${MAX_RETRIES})...`)
      try {
        window.turnstile.reset(widgetIdRef.current)
      } catch {
        // Reset failed, fall through to error handler
        setLoadFailed(true)
        onError?.()
      }
    } else {
      console.warn('[Turnstile] CAPTCHA failed after retries - allowing form submission without it')
      setLoadFailed(true)
      onError?.()
    }
  }, [onError])

  useEffect(() => {
    const loadTurnstile = () => {
      if (containerRef.current && window.turnstile && !widgetIdRef.current) {
        try {
          widgetIdRef.current = window.turnstile.render(containerRef.current, {
            sitekey: TURNSTILE_SITE_KEY,
            callback: (token: string) => {
              retryCountRef.current = 0
              onVerify(token)
            },
            'error-callback': handleError,
            'expired-callback': onExpire,
            theme: 'light',
            size: mode,
            retry: 'auto',
            'retry-interval': 3000,
          })
        } catch (err) {
          console.warn('[Turnstile] Failed to render widget:', err)
          setLoadFailed(true)
          onError?.()
        }
      }
    }

    // Check if script already loaded
    if (window.turnstile) {
      loadTurnstile()
    } else {
      // Load the script
      const existingScript = document.querySelector('script[src*="turnstile"]')
      if (!existingScript) {
        const script = document.createElement('script')
        script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?onload=onTurnstileLoad'
        script.async = true
        script.defer = true
        script.onerror = () => {
          console.warn('[Turnstile] Failed to load Cloudflare script - ad blocker or network issue')
          setLoadFailed(true)
          onError?.()
        }
        window.onTurnstileLoad = loadTurnstile
        document.head.appendChild(script)
      } else {
        window.onTurnstileLoad = loadTurnstile
      }
    }

    // Timeout fallback: if widget hasn't loaded after 10s, don't block the user
    const timeout = setTimeout(() => {
      if (!widgetIdRef.current) {
        console.warn('[Turnstile] Widget load timeout - allowing form submission without CAPTCHA')
        setLoadFailed(true)
        onError?.()
      }
    }, 10000)

    return () => {
      clearTimeout(timeout)
      if (widgetIdRef.current && window.turnstile) {
        try {
          window.turnstile.remove(widgetIdRef.current)
        } catch {
          // Widget may already be removed
        }
        widgetIdRef.current = null
      }
    }
  }, [onVerify, onExpire, handleError, onError, mode])

  if (loadFailed && mode === 'normal') {
    return (
      <div className="text-xs text-amber-600 text-center py-1">
        Security check unavailable. You can still sign in.
      </div>
    )
  }

  return <div ref={containerRef} />
}

export function resetTurnstile(widgetId: string) {
  if (window.turnstile && widgetId) {
    try {
      window.turnstile.reset(widgetId)
    } catch {
      // Widget may have been removed
    }
  }
}
