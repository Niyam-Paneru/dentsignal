'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertCircle, CreditCard, Mail, Clock, CheckCircle2, Zap, Phone, Star, Shield } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'
import { MarketingHeader } from '@/components/landing/marketing-header'
import { MarketingFooter } from '@/components/landing/marketing-footer'

interface ClinicSubscription {
  name: string
  subscription_status: 'trial' | 'active' | 'expired' | 'cancelled'
  subscription_expires_at: string | null
  plan_type: 'starter_149' | 'pro_199'
}

export default function SubscriptionRequiredPage() {
  const [clinic, setClinic] = useState<ClinicSubscription | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedPlan, setSelectedPlan] = useState<'starter_149' | 'pro_199'>('starter_149')
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
      if (data?.plan_type) {
        setSelectedPlan(data.plan_type as 'starter_149' | 'pro_199')
      }
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

  const getStatusMessage = () => {
    if (!clinic) return { title: 'Subscription Required', description: 'Please subscribe to access your dashboard.' }
    
    switch (clinic.subscription_status) {
      case 'trial':
        return {
          title: 'Your Free Trial Has Ended',
          description: `Your 9-day trial ended on ${formatDate(clinic.subscription_expires_at)}. Subscribe now to continue using DentSignal.`
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

  const plans = [
    {
      id: 'pro_199' as const,
      name: 'DentSignal',
      price: 199,
      popular: true,
      description: 'Everything included. One simple price.',
      features: [
        '24/7 AI Call Answering',
        'Unlimited calls',
        'Appointment Booking',
        'SMS Confirmations',
        'Proactive Recall Outbound',
        'Advanced Analytics & ROI',
        'Custom AI Voice & Script',
        'Priority Support',
        'English AI Voice',
      ]
    }
  ]

  const handlePaymentRequest = () => {
    const plan = plans.find(p => p.id === selectedPlan)
    const subject = encodeURIComponent(`DentSignal Subscription - ${plan?.name} Plan ($${plan?.price}/mo)`)
    const body = encodeURIComponent(`Hi DentSignal Team,

I would like to subscribe to the ${plan?.name} Plan at $${plan?.price}/month.

Clinic Name: ${clinic?.name || '[Your Clinic Name]'}
Plan: ${plan?.name} ($${plan?.price}/month)

Please send me the payment instructions.

Thank you!`)
    
    window.location.href = `mailto:hello@dentsignal.com?subject=${subject}&body=${body}`
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <MarketingHeader />
      
      <main className="flex-1 py-12 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Status Alert */}
          <Card className="mb-8">
            <CardHeader className="text-center pb-4">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-amber-100">
                <AlertCircle className="h-7 w-7 text-amber-600" />
              </div>
              <CardTitle className="text-2xl">{status.title}</CardTitle>
              <CardDescription className="text-base mt-2">
                {status.description}
              </CardDescription>
            </CardHeader>
            
            {clinic && (
              <CardContent className="pt-0">
                <div className="rounded-lg bg-gray-50 p-4 max-w-sm mx-auto">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">Clinic</span>
                    <span className="font-medium">{clinic.name}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Status</span>
                    <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800 capitalize">
                      {clinic.subscription_status === 'trial' ? 'Trial Expired' : clinic.subscription_status}
                    </span>
                  </div>
                </div>
              </CardContent>
            )}
          </Card>

          {/* Plan Selection */}
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900">Choose Your Plan</h2>
            <p className="text-gray-600 mt-2">Select a plan to continue using DentSignal</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-8">
            {plans.map((plan) => (
              <Card 
                key={plan.id}
                className={`cursor-pointer transition-shadow duration-150 hover:shadow-lg ${
                  selectedPlan === plan.id 
                    ? 'ring-2 ring-blue-600 border-blue-600' 
                    : 'hover:border-gray-300'
                } ${plan.popular ? 'relative' : ''}`}
                onClick={() => setSelectedPlan(plan.id)}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="bg-blue-600 text-white text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1">
                      <Star className="h-3 w-3" /> MOST POPULAR
                    </span>
                  </div>
                )}
                <CardHeader className={plan.popular ? 'pt-8' : ''}>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xl">{plan.name}</CardTitle>
                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                      selectedPlan === plan.id ? 'border-blue-600 bg-blue-600' : 'border-gray-300'
                    }`}>
                      {selectedPlan === plan.id && (
                        <CheckCircle2 className="h-4 w-4 text-white" />
                      )}
                    </div>
                  </div>
                  <CardDescription>{plan.description}</CardDescription>
                  <div className="mt-4">
                    <span className="text-4xl font-bold">${plan.price}</span>
                    <span className="text-gray-600">/month</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0 mt-0.5" />
                        <span className="text-sm text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Payment Instructions */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                How to Subscribe
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-blue-600 font-bold">1</span>
                  </div>
                  <h4 className="font-medium mb-1">Confirm Your Plan</h4>
                  <p className="text-sm text-gray-600">$199/month - everything included</p>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-blue-600 font-bold">2</span>
                  </div>
                  <h4 className="font-medium mb-1">Request Payment Link</h4>
                  <p className="text-sm text-gray-600">We&apos;ll send you a secure Payoneer link</p>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-blue-600 font-bold">3</span>
                  </div>
                  <h4 className="font-medium mb-1">Instant Activation</h4>
                  <p className="text-sm text-gray-600">Access restored within 2 hours</p>
                </div>
              </div>

              <div className="border-t pt-4">
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  <Button size="lg" onClick={handlePaymentRequest} className="gap-2">
                    <Mail className="h-4 w-4" />
                    Request Payment Link ({plans.find(p => p.id === selectedPlan)?.name} - ${plans.find(p => p.id === selectedPlan)?.price}/mo)
                  </Button>
                </div>
                <p className="text-center text-sm text-gray-500 mt-3">
                  Or email us directly at <a href="mailto:hello@dentsignal.com" className="text-blue-600 hover:underline">hello@dentsignal.com</a>
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Trust Signals */}
          <div className="grid grid-cols-3 gap-4 text-center mb-6">
            <div className="flex flex-col items-center">
              <Shield className="h-8 w-8 text-green-600 mb-2" />
              <span className="text-sm text-gray-600">HIPAA Compliant</span>
            </div>
            <div className="flex flex-col items-center">
              <Zap className="h-8 w-8 text-blue-600 mb-2" />
              <span className="text-sm text-gray-600">Instant Activation</span>
            </div>
            <div className="flex flex-col items-center">
              <Phone className="h-8 w-8 text-purple-600 mb-2" />
              <span className="text-sm text-gray-600">Cancel Anytime</span>
            </div>
          </div>

          {/* Data Preservation Notice */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
            <CheckCircle2 className="h-6 w-6 text-green-600 mx-auto mb-2" />
            <p className="text-green-800 font-medium">Your data is safe!</p>
            <p className="text-green-700 text-sm">All your call history, transcripts, and settings are preserved. They&apos;ll be waiting for you when you subscribe.</p>
          </div>

          {/* Sign Out Option */}
          <div className="text-center mt-6">
            <Button variant="ghost" asChild>
              <Link href="/logout">Sign Out</Link>
            </Button>
          </div>
        </div>
      </main>

      <MarketingFooter />
    </div>
  )
}
