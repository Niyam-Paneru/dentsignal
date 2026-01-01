'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'

export interface SubscriptionInfo {
  status: 'trial' | 'active' | 'expired' | 'cancelled'
  expiresAt: Date | null
  planType: 'starter_149' | 'pro_199'
  daysRemaining: number
  isExpiringSoon: boolean // Within 7 days
  isActive: boolean
}

export function useSubscription() {
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchSubscription() {
      const supabase = createClient()
      const { data: { user } } = await supabase.auth.getUser()

      if (!user) {
        setLoading(false)
        return
      }

      const { data: clinic } = await supabase
        .from('dental_clinics')
        .select('subscription_status, subscription_expires_at, plan_type')
        .eq('owner_id', user.id)
        .single()

      if (clinic) {
        const expiresAt = clinic.subscription_expires_at 
          ? new Date(clinic.subscription_expires_at) 
          : null
        const now = new Date()
        const daysRemaining = expiresAt 
          ? Math.max(0, Math.ceil((expiresAt.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)))
          : 0
        const isActive = expiresAt ? expiresAt > now : false
        const isExpiringSoon = isActive && daysRemaining <= 7

        setSubscription({
          status: clinic.subscription_status || 'trial',
          expiresAt,
          planType: clinic.plan_type || 'starter_149',
          daysRemaining,
          isExpiringSoon,
          isActive,
        })
      }

      setLoading(false)
    }

    fetchSubscription()
  }, [])

  return { subscription, loading }
}

// Helper to format plan names
export function getPlanDisplayName(planType: string): string {
  switch (planType) {
    case 'pro_199':
      return 'Pro'
    case 'starter_149':
    default:
      return 'Starter'
  }
}

export function getPlanPrice(planType: string): number {
  return planType === 'pro_199' ? 199 : 149
}
