'use client'

import { useState, useMemo } from 'react'
import { Slider } from '@/components/ui/slider'
import { Button } from '@/components/ui/button'
import { ArrowRight, TrendingDown } from 'lucide-react'
import Link from 'next/link'

// =============================================================================
// HERO CALCULATOR - CONSERVATIVE/HONEST VERSION
// =============================================================================
// Miss rate: 35% of calls go unanswered (industry avg)
// NOT all missed calls are new patients
// NOT all would have converted
// REALISTIC assumptions:
//   - 40% of missed calls would have converted (not 100%)
//   - DentSignal captures ~50% of those
//   - Shows a RANGE, not a single inflated number
// =============================================================================

export function HeroCalculator() {
  // Default: 60 missed new patient calls/month (industry avg for small practice)
  const [missedNewPatientCalls, setMissedNewPatientCalls] = useState(60)
  // First-year patient value: $850 (industry standard)
  const [patientValue, setPatientValue] = useState(850)

  const calculations = useMemo(() => {
    // CONSERVATIVE: Only 40% would have converted (not 100%)
    const conversionRate = 0.40
    const potentialPatients = missedNewPatientCalls * conversionRate
    
    // DentSignal captures ~50% of those (realistic, not 95%)
    const captureRate = 0.50
    const patientsCaptured = potentialPatients * captureRate
    
    // Monthly recovery = patients captured × patient value
    const monthlyRecoveryLow = Math.round(patientsCaptured * patientValue * 0.8) // Conservative
    const monthlyRecoveryHigh = Math.round(patientsCaptured * patientValue * 1.2) // Optimistic
    const yearlyRecoveryLow = monthlyRecoveryLow * 12
    const yearlyRecoveryHigh = monthlyRecoveryHigh * 12
    
    return {
      monthlyRecoveryLow,
      monthlyRecoveryHigh,
      yearlyRecoveryLow,
      yearlyRecoveryHigh,
      patientsCaptured: Math.round(patientsCaptured),
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
        <div className="h-8 w-8 rounded-full bg-[#22C55E]/10 flex items-center justify-center">
          <TrendingDown className="h-4 w-4 text-[#22C55E]" />
        </div>
        <span className="font-bold text-gray-900">Estimate Your Recovery</span>
      </div>
      <p className="text-xs text-gray-500 mb-4 ml-10">Based on conservative assumptions</p>

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

      {/* Results - Conservative RANGE */}
      <div className="bg-gradient-to-r from-[#22C55E]/10 to-[#22C55E]/5 border border-[#22C55E]/20 rounded-xl p-4 mb-4">
        <p className="text-xs font-semibold text-[#22C55E] uppercase tracking-wide mb-1">Estimated Recovery</p>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl sm:text-3xl font-black text-[#22C55E]">
            {formatCurrency(calculations.monthlyRecoveryLow)} - {formatCurrency(calculations.monthlyRecoveryHigh)}
          </span>
          <span className="text-sm text-[#22C55E]/70">/mo</span>
        </div>
        <p className="text-xs text-gray-600 mt-1">
          ~{calculations.patientsCaptured} additional patients/mo captured
        </p>
      </div>

      {/* Disclaimer */}
      <p className="text-xs text-center text-gray-500 mb-4">
        Assumes 40% conversion rate, 50% capture rate. <span className="font-medium">Your results may vary.</span>
      </p>

      {/* CTA */}
      <Link href="/signup" className="block">
        <Button className="w-full h-11 gap-2 bg-[#22C55E] hover:bg-[#16a34a] text-white font-bold shadow-lg">
          Start Free Trial
          <ArrowRight className="h-4 w-4" />
        </Button>
      </Link>

      <p className="text-xs text-center text-gray-400 mt-2">
        7-day free trial • No credit card • $199/mo after
      </p>
    </div>
  )
}
