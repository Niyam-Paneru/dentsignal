'use client'

import { useState, useMemo } from 'react'
import { Slider } from '@/components/ui/slider'
import { Button } from '@/components/ui/button'
import { ArrowRight, TrendingDown } from 'lucide-react'
import Link from 'next/link'

// =============================================================================
// HERO CALCULATOR - Based on 2025-2026 Industry Research
// =============================================================================
// Miss rate: 35% of calls go unanswered (industry avg)
// New patient calls: ~20% of missed calls are new patients
// Conversion: 30-40% would have converted
// First-year value: $850 per new patient
// Lifetime value: $8,000-$25,000 per patient
// Per missed call: $200-$300 immediate lost revenue
// =============================================================================

export function HeroCalculator() {
  // Default: 60 missed new patient calls/month (industry avg for small practice)
  const [missedNewPatientCalls, setMissedNewPatientCalls] = useState(60)
  // First-year patient value: $850 (industry standard)
  const [patientValue, setPatientValue] = useState(850)

  const calculations = useMemo(() => {
    // 30-40% of new patient calls convert → use 35% as middle ground
    const conversionRate = 0.35
    const patientsLost = missedNewPatientCalls * conversionRate
    
    // Monthly loss = patients lost × first-year value
    const monthlyLoss = patientsLost * patientValue
    const yearlyLoss = monthlyLoss * 12
    
    // DentSignal recovers ~50% of missed calls
    const recoverable = monthlyLoss * 0.5
    
    return {
      monthlyLoss: Math.round(monthlyLoss),
      yearlyLoss: Math.round(yearlyLoss),
      recoverable: Math.round(recoverable),
      patientsLost: Math.round(patientsLost),
    }
  }, [missedNewPatientCalls, patientValue])

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(value)
  }

  return (
    <div className="bg-white rounded-2xl shadow-2xl p-5 sm:p-6 max-w-md mx-auto lg:mx-0">
      {/* Header with stat */}
      <div className="flex items-center gap-2 mb-1">
        <div className="h-8 w-8 rounded-full bg-[#EF4444]/10 flex items-center justify-center">
          <TrendingDown className="h-4 w-4 text-[#EF4444]" />
        </div>
        <span className="font-bold text-gray-900">How much are you losing?</span>
      </div>
      <p className="text-xs text-gray-500 mb-4 ml-10">35% of calls go unanswered. 75% never call back.</p>

      {/* Sliders */}
      <div className="space-y-4 mb-5">
        <div>
          <div className="flex justify-between text-sm mb-1.5">
            <span className="text-gray-600">Missed new patient calls/mo</span>
            <span className="font-bold text-gray-900">{missedNewPatientCalls}</span>
          </div>
          <Slider
            min={10}
            max={100}
            step={5}
            value={[missedNewPatientCalls]}
            onValueChange={([value]) => setMissedNewPatientCalls(value)}
            className="cursor-pointer"
          />
          <p className="text-xs text-gray-400 mt-1">Industry avg: 50-100/month</p>
        </div>

        <div>
          <div className="flex justify-between text-sm mb-1.5">
            <span className="text-gray-600">First-year patient value</span>
            <span className="font-bold text-gray-900">{formatCurrency(patientValue)}</span>
          </div>
          <Slider
            min={500}
            max={1500}
            step={50}
            value={[patientValue]}
            onValueChange={([value]) => setPatientValue(value)}
            className="cursor-pointer"
          />
          <p className="text-xs text-gray-400 mt-1">Industry avg: $850</p>
        </div>
      </div>

      {/* Results - Big scary number */}
      <div className="bg-gradient-to-r from-[#EF4444]/10 to-[#EF4444]/5 border border-[#EF4444]/20 rounded-xl p-4 mb-4">
        <p className="text-xs font-semibold text-[#EF4444] uppercase tracking-wide mb-1">You&apos;re losing</p>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl sm:text-4xl font-black text-[#EF4444]">
            {formatCurrency(calculations.yearlyLoss)}
          </span>
          <span className="text-sm text-[#EF4444]/70">/year</span>
        </div>
        <p className="text-xs text-gray-600 mt-1">
          {formatCurrency(calculations.monthlyLoss)}/mo • ~{calculations.patientsLost} patients lost/mo
        </p>
      </div>

      {/* Recovery line */}
      <p className="text-sm text-center text-gray-600 mb-4">
        DentSignal can recover ~<span className="font-bold text-[#22C55E]">{formatCurrency(calculations.recoverable)}/mo</span> for just $199/mo
      </p>

      {/* CTA */}
      <Link href="/signup" className="block">
        <Button className="w-full h-11 gap-2 bg-[#22C55E] hover:bg-[#16a34a] text-white font-bold shadow-lg">
          Stop Losing Money
          <ArrowRight className="h-4 w-4" />
        </Button>
      </Link>

      <p className="text-xs text-center text-gray-400 mt-2">
        7-day free trial • No credit card
      </p>
    </div>
  )
}
