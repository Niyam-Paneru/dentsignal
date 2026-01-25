'use client'

import { useCallback } from 'react'
import { toast } from 'sonner'
import { getRandomMessage, CelebrationCategory } from '@/lib/celebratory-messages'

/**
 * Hook to show celebratory toast notifications
 * Uses random messages with weighted tone distribution from celebratory-messages
 */
export function useCelebration() {
  const celebrate = useCallback((category: CelebrationCategory, customTitle?: string) => {
    const message = getRandomMessage(category)
    
    const titles: Record<CelebrationCategory, string> = {
      booking: '🎉 Appointment Booked!',
      emergency: '🚨 Emergency Handled',
      quality: '⭐ High Quality Call',
      noshow: '✅ Patient Confirmed',
      recovered: '📞 Call Recovered',
      rescheduled: '🔄 Patient Rescheduled',
      positive_sentiment: '💚 Happy Patient',
    }
    
    toast.success(customTitle || titles[category], {
      description: message,
      duration: 5000,
    })
  }, [])

  const celebrateBooking = useCallback(() => celebrate('booking'), [celebrate])
  const celebrateEmergency = useCallback(() => celebrate('emergency'), [celebrate])
  const celebrateQuality = useCallback(() => celebrate('quality'), [celebrate])
  const celebrateNoShow = useCallback(() => celebrate('noshow'), [celebrate])
  const celebrateRecovered = useCallback(() => celebrate('recovered'), [celebrate])
  const celebrateRescheduled = useCallback(() => celebrate('rescheduled'), [celebrate])
  const celebratePositiveSentiment = useCallback(() => celebrate('positive_sentiment'), [celebrate])

  return {
    celebrate,
    celebrateBooking,
    celebrateEmergency,
    celebrateQuality,
    celebrateNoShow,
    celebrateRecovered,
    celebrateRescheduled,
    celebratePositiveSentiment,
  }
}
