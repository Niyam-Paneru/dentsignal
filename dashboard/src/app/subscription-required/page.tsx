'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertCircle, CreditCard, Mail, Clock, CheckCircle2 } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'
import { MarketingHeader } from '@/components/landing/marketing-header'
import { MarketingFooter } from '@/components/landing/marketing-footer'

interface ClinicSubscription {
  name: string
  subscription_status: 'trial' | 'active' | 'expired' | 'cancelled'
  subscription_expires_at: string | null
  plan_type: 'pro_199'
}

export default function SubscriptionRequiredPage() {
  const [clinic, setClinic] = useState<ClinicSubscription | null>(null)
  const [loading, setLoading] = useState(true)
  const supabase = createClient()

  useEffect(() => {
    async function fetchClinic() {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return

      const { data } = await supabase
        .from('dental_clinics')
        .select('name, subscription_status, subscription_expires_at, plan_type')
        .eq('owner_id', user.id)
        .single()

      setClinic(data as ClinicSubscription)
      setLoading(false)
    }
    fetchClinic()
  }, [supabase])

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const getPlanName = () => {
    return 'Professional Plan ($199/mo)'
  }

  const getStatusMessage = () => {
    if (!clinic) return { title: 'Subscription Required', description: 'Please subscribe to access your dashboard.' }
    
    switch (clinic.subscription_status) {
      case 'trial':
        return {
          title: 'Your Trial Has Expired',
          description: `Your 7-day trial ended on ${formatDate(clinic.subscription_expires_at)}. Subscribe now to continue using DentSignal.`
        }
      case 'expired':
        return {
          title: 'Your Subscription Has Expired',
          description: `Your subscription expired on ${formatDate(clinic.subscription_expires_at)}. Renew now to restore access.`
        }
      case 'cancelled':
        return {
          title: 'Your Subscription Was Cancelled',
          description: 'Your subscription has been cancelled. Reactivate to continue using DentSignal.'
        }
      default:
        return {
          title: 'Subscription Required',
          description: 'Please subscribe to access your dashboard.'
        }
    }
  }

  const status = getStatusMessage()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col">
      <MarketingHeader />
      
      <main className="flex-1 flex items-center justify-center px-4 py-16">
        <Card className="w-full max-w-lg">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-amber-100">
              <AlertCircle className="h-7 w-7 text-amber-600" />
            </div>
            <CardTitle className="text-2xl">{status.title}</CardTitle>
            <CardDescription className="text-base mt-2">
              {status.description}
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            {/* Current Plan Info */}
            {clinic && (
              <div className="rounded-lg bg-gray-50 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Clinic</span>
                  <span className="font-medium">{clinic.name}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Plan</span>
                  <span className="font-medium">{getPlanName()}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Status</span>
                  <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800 capitalize">
                    {clinic.subscription_status}
                  </span>
                </div>
              </div>
            )}

            {/* Payment Options */}
            <div className="space-y-3">
              <h3 className="font-medium text-gray-900">To reactivate your account:</h3>
              
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                  <span>Your call history and data are preserved</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                  <span>Instant reactivation upon payment</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                  <span>No setup fees or contracts</span>
                </div>
              </div>
            </div>

            {/* Contact to Pay */}
            <div className="rounded-lg border-2 border-dashed border-gray-200 p-4 text-center">
              <CreditCard className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-600 mb-3">
                Contact us to complete your payment and restore access immediately.
              </p>
              <a 
                href="mailto:hello@dentsignal.com?subject=Subscription%20Renewal%20Request"
                className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium"
              >
                <Mail className="h-4 w-4" />
                hello@dentsignal.com
              </a>
            </div>

            {/* Actions */}
            <div className="flex flex-col gap-3">
              <Button asChild className="w-full" size="lg">
                <a href="mailto:hello@dentsignal.com?subject=Subscription%20Renewal%20Request">
                  <CreditCard className="mr-2 h-4 w-4" />
                  Contact to Renew
                </a>
              </Button>
              
              <Button variant="outline" asChild className="w-full">
                <Link href="/logout">
                  Sign Out
                </Link>
              </Button>
            </div>

            {/* Support Note */}
            <p className="text-xs text-center text-gray-500">
              Questions? Email us at hello@dentsignal.com or call (555) 123-4567
            </p>
          </CardContent>
        </Card>
      </main>

      <MarketingFooter />
    </div>
  )
}
