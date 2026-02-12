'use client'

import { useState, useEffect, useCallback } from 'react'
import { X, Gift, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { createClient } from '@/lib/supabase/client'

export function ExitIntentPopup() {
  const [isVisible, setIsVisible] = useState(false)
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [hasShown, setHasShown] = useState(false)

  const handleMouseLeave = useCallback((e: MouseEvent) => {
    // Only trigger when mouse moves toward top of viewport (closing tab)
    if (e.clientY <= 5 && !hasShown) {
      // Check if already dismissed this session
      const dismissed = sessionStorage.getItem('exit-intent-dismissed')
      if (!dismissed) {
        setIsVisible(true)
        setHasShown(true)
      }
    }
  }, [hasShown])

  useEffect(() => {
    // Delay adding listener so it doesn't fire on page load
    const timer = setTimeout(() => {
      document.addEventListener('mouseleave', handleMouseLeave)
    }, 5000) // Wait 5s before arming

    return () => {
      clearTimeout(timer)
      document.removeEventListener('mouseleave', handleMouseLeave)
    }
  }, [handleMouseLeave])

  const handleDismiss = () => {
    setIsVisible(false)
    sessionStorage.setItem('exit-intent-dismissed', 'true')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email) return

    // Save lead to Supabase (fail silently if unavailable)
    try {
      const supabase = createClient()
      if (supabase) {
        await supabase
          .from('dental_leads')
          .upsert(
            { email, source: 'exit-intent' },
            { onConflict: 'email,source' }
          )
      }
    } catch {
      // Silently fail — don't block the user experience
    }

    setSubmitted(true)
    sessionStorage.setItem('exit-intent-dismissed', 'true')
    
    // Auto-close after 3 seconds
    setTimeout(() => setIsVisible(false), 3000)
  }

  if (!isVisible) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="relative mx-4 w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl animate-in zoom-in-95 duration-300">
        {/* Close button */}
        <button
          onClick={handleDismiss}
          className="absolute right-4 top-4 rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
          aria-label="Close popup"
        >
          <X className="h-5 w-5" />
        </button>

        {!submitted ? (
          <>
            {/* Icon */}
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-[#0099CC]/10">
              <Gift className="h-7 w-7 text-[#0099CC]" />
            </div>

            {/* Headline */}
            <h3 className="mb-2 text-center text-xl font-bold text-[#2D3748]">
              Wait — Get Your Free ROI Report
            </h3>
            <p className="mb-6 text-center text-sm text-gray-600">
              See exactly how much revenue your practice is losing to missed calls. 
              Personalized report delivered in 24 hours.
            </p>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-3">
              <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full rounded-lg border border-gray-200 px-4 py-3 text-sm outline-none focus:border-[#0099CC] focus:ring-2 focus:ring-[#0099CC]/20 transition-all"
              />
              <Button
                type="submit"
                className="w-full gap-2 bg-[#22C55E] hover:bg-[#16a34a] text-white font-semibold py-3"
                size="lg"
              >
                Send My Free Report
                <ArrowRight className="h-4 w-4" />
              </Button>
            </form>

            <p className="mt-3 text-center text-xs text-gray-400">
              No spam. Unsubscribe anytime.
            </p>
          </>
        ) : (
          /* Success state */
          <div className="py-4 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-green-100">
              <svg className="h-7 w-7 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="mb-2 text-xl font-bold text-[#2D3748]">Check Your Inbox!</h3>
            <p className="text-sm text-gray-600">
              We&apos;ll send your personalized ROI report within 24 hours.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
