'use client'

import { useEffect, useCallback, useRef, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'

/**
 * HIPAA Session Timeout Component
 * 
 * Automatically logs out users after period of inactivity.
 * Required by HIPAA Security Rule (45 CFR § 164.312(a)(2)(iii))
 * 
 * Configuration:
 * - IDLE_TIMEOUT: Time before warning appears (15 minutes)
 * - WARNING_TIMEOUT: Time to respond to warning before logout (60 seconds)
 */

// Configuration (in milliseconds)
const IDLE_TIMEOUT = 15 * 60 * 1000 // 15 minutes of inactivity
const WARNING_TIMEOUT = 60 * 1000    // 60 seconds to respond to warning

// Events that reset the idle timer
const ACTIVITY_EVENTS = [
  'mousedown',
  'mousemove',
  'keydown',
  'scroll',
  'touchstart',
  'click',
]

export function SessionTimeout() {
  const router = useRouter()
  const [showWarning, setShowWarning] = useState(false)
  const [countdown, setCountdown] = useState(60)
  
  const idleTimerRef = useRef<NodeJS.Timeout | null>(null)
  const warningTimerRef = useRef<NodeJS.Timeout | null>(null)
  const countdownIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Logout function
  const handleLogout = useCallback(async () => {
    const supabase = createClient()
    await supabase.auth.signOut()
    
    // Clear any stored data
    if (typeof window !== 'undefined') {
      localStorage.removeItem('sb-session')
      sessionStorage.clear()
    }
    
    router.push('/login?reason=session_timeout')
  }, [router])

  // Reset the idle timer on user activity
  const resetIdleTimer = useCallback(() => {
    // Don't reset if warning is showing
    if (showWarning) return

    // Clear existing timer
    if (idleTimerRef.current) {
      clearTimeout(idleTimerRef.current)
    }

    // Set new timer
    idleTimerRef.current = setTimeout(() => {
      // Show warning dialog
      setShowWarning(true)
      setCountdown(60)

      // Start countdown
      countdownIntervalRef.current = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            handleLogout()
            return 0
          }
          return prev - 1
        })
      }, 1000)

      // Set final logout timer
      warningTimerRef.current = setTimeout(() => {
        handleLogout()
      }, WARNING_TIMEOUT)
    }, IDLE_TIMEOUT)
  }, [showWarning, handleLogout])

  // Handle "Stay Logged In" click
  const handleStayLoggedIn = useCallback(() => {
    // Clear warning timers
    if (warningTimerRef.current) {
      clearTimeout(warningTimerRef.current)
    }
    if (countdownIntervalRef.current) {
      clearInterval(countdownIntervalRef.current)
    }

    // Hide warning and reset
    setShowWarning(false)
    setCountdown(60)
    
    // Restart idle timer
    resetIdleTimer()
  }, [resetIdleTimer])

  // Set up activity listeners
  useEffect(() => {
    // Initial timer start
    resetIdleTimer()

    // Add activity listeners
    ACTIVITY_EVENTS.forEach((event) => {
      document.addEventListener(event, resetIdleTimer, { passive: true })
    })

    // Cleanup
    return () => {
      ACTIVITY_EVENTS.forEach((event) => {
        document.removeEventListener(event, resetIdleTimer)
      })
      
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current)
      if (warningTimerRef.current) clearTimeout(warningTimerRef.current)
      if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current)
    }
  }, [resetIdleTimer])

  return (
    <AlertDialog open={showWarning} onOpenChange={setShowWarning}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="text-amber-600">
            ⚠️ Session Expiring
          </AlertDialogTitle>
          <AlertDialogDescription className="space-y-2">
            <p>
              Your session will expire in <strong className="text-red-600">{countdown} seconds</strong> due to inactivity.
            </p>
            <p className="text-sm text-muted-foreground">
              For security purposes (HIPAA compliance), sessions automatically end after 15 minutes of inactivity.
            </p>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={handleLogout}>
            Log Out Now
          </AlertDialogCancel>
          <AlertDialogAction onClick={handleStayLoggedIn}>
            Stay Logged In
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
