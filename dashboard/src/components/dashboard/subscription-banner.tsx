'use client'

import { AlertTriangle, Clock, CreditCard } from 'lucide-react'
import { useSubscription, getPlanDisplayName } from '@/lib/hooks/use-subscription'

export function SubscriptionBanner() {
  const { subscription, loading } = useSubscription()

  if (loading || !subscription) return null

  // Don't show banner if subscription is healthy (more than 7 days remaining)
  if (subscription.isActive && !subscription.isExpiringSoon) return null

  const isTrial = subscription.status === 'trial'
  const isExpired = !subscription.isActive

  // Determine banner style and message
  let bgColor = 'bg-amber-50 border-amber-200'
  let textColor = 'text-amber-800'
  let Icon = Clock
  let message = ''
  let actionText = 'Renew Now'

  if (isExpired) {
    bgColor = 'bg-red-50 border-red-200'
    textColor = 'text-red-800'
    Icon = AlertTriangle
    message = 'Your subscription has expired. Renew now to restore full access.'
    actionText = 'Reactivate'
  } else if (isTrial && subscription.daysRemaining <= 3) {
    bgColor = 'bg-amber-50 border-amber-200'
    textColor = 'text-amber-800'
    Icon = Clock
    message = `Your trial ends in ${subscription.daysRemaining} day${subscription.daysRemaining !== 1 ? 's' : ''}. Subscribe to keep using DentSignal.`
    actionText = 'Subscribe Now'
  } else if (isTrial) {
    bgColor = 'bg-blue-50 border-blue-200'
    textColor = 'text-blue-800'
    Icon = Clock
    message = `${subscription.daysRemaining} days left in your trial. Enjoying DentSignal?`
    actionText = 'Subscribe Now'
  } else if (subscription.isExpiringSoon) {
    bgColor = 'bg-amber-50 border-amber-200'
    textColor = 'text-amber-800'
    Icon = AlertTriangle
    message = `Your ${getPlanDisplayName(subscription.planType)} plan renews in ${subscription.daysRemaining} day${subscription.daysRemaining !== 1 ? 's' : ''}.`
    actionText = 'Manage Billing'
  }

  return (
    <div className={`${bgColor} border rounded-lg px-4 py-3 mb-6`}>
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Icon className={`h-5 w-5 ${textColor} shrink-0`} />
          <p className={`text-sm font-medium ${textColor}`}>
            {message}
          </p>
        </div>
        <a
          href="mailto:hello@dentsignal.com?subject=Subscription%20Inquiry"
          className={`inline-flex items-center gap-1.5 rounded-md bg-white px-3 py-1.5 text-sm font-medium shadow-sm border hover:bg-gray-50 transition-colors shrink-0 ${textColor}`}
        >
          <CreditCard className="h-4 w-4" />
          {actionText}
        </a>
      </div>
    </div>
  )
}
