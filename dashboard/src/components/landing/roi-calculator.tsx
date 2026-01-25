'use client'

import { useState, useMemo } from 'react'
import { Slider } from '@/components/ui/slider'
import { Button } from '@/components/ui/button'
import { 
  DollarSign, 
  Phone, 
  ArrowRight,
  Calculator,
  Info,
} from 'lucide-react'
import Link from 'next/link'

// =============================================================================
// ROI CALCULATOR - UNIFIED WITH HERO CALCULATOR
// =============================================================================
// Uses same formula as hero-calculator.tsx for consistency:
//   - Input: Missed new patient calls (already filtered)
//   - 40% would have converted (conservative)
//   - DentSignal captures ~50% of those
//   - Shows a RANGE (low/high) for credibility
// =============================================================================

const DENTSIGNAL_MONTHLY_PRICE = 199

export function ROICalculator() {
  // Same defaults as hero calculator
  const [missedNewPatientCalls, setMissedNewPatientCalls] = useState(60)
  const [patientValue, setPatientValue] = useState(850)

  const calc = useMemo(() => {
    // Step 1: Only 40% would have actually converted (not 100%)
    const conversionRate = 0.40
    const wouldHaveConverted = missedNewPatientCalls * conversionRate
    
    // Step 2: DentSignal captures ~50% of those (realistic)
    const captureRate = 0.50
    const patientsCaptured = wouldHaveConverted * captureRate
    
    // Step 3: Calculate recovery range (±20% for low/high)
    const monthlyRecoveryMid = patientsCaptured * patientValue
    const monthlyRecoveryLow = Math.round(monthlyRecoveryMid * 0.8)
    const monthlyRecoveryHigh = Math.round(monthlyRecoveryMid * 1.2)
    
    return {
      missedCalls: missedNewPatientCalls,
      wouldHaveConverted: Math.round(wouldHaveConverted),
      patientsCaptured: Math.round(patientsCaptured),
      monthlyRecoveryLow,
      monthlyRecoveryHigh,
      annualRecoveryLow: monthlyRecoveryLow * 12,
      annualRecoveryHigh: monthlyRecoveryHigh * 12,
    }
  }, [missedNewPatientCalls, patientValue])

  const fmt = (n: number) => new Intl.NumberFormat('en-US', { 
    style: 'currency', 
    currency: 'USD', 
    maximumFractionDigits: 0 
  }).format(n)

  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-6 lg:p-8 shadow-2xl max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center gap-2 mb-2">
          <Calculator className="h-5 w-5 text-emerald-400" />
          <h3 className="text-2xl font-bold text-white">Estimate Your Recovery</h3>
        </div>
        <p className="text-slate-400 text-sm">Conservative estimates based on realistic assumptions</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Left: Sliders */}
        <div className="space-y-5">
          {/* Monthly Calls */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-slate-300 flex items-center gap-1.5">
                <Phone className="h-4 w-4 text-cyan-400" /> Missed new patient calls/mo
              </span>
              <span className="font-bold text-white">{missedNewPatientCalls}</span>
            </div>
            <Slider
              min={10} max={100} step={5}
              value={[missedNewPatientCalls]}
              onValueChange={([v]) => setMissedNewPatientCalls(v)}
              className="cursor-pointer"
            />
            <p className="text-xs text-slate-500 mt-1">Industry avg: 50-100/month</p>
          </div>

          {/* Patient Value */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-slate-300 flex items-center gap-1.5">
                <DollarSign className="h-4 w-4 text-emerald-400" /> First-year patient value
              </span>
              <span className="font-bold text-white">{fmt(patientValue)}</span>
            </div>
            <Slider
              min={500} max={1500} step={50}
              value={[patientValue]}
              onValueChange={([v]) => setPatientValue(v)}
              className="cursor-pointer"
            />
            <p className="text-xs text-slate-500 mt-1">Industry avg: $850</p>
          </div>

          {/* Math breakdown - TRANSPARENT */}
          <div className="bg-slate-800/50 rounded-lg p-3 text-xs text-slate-400 border border-slate-700">
            <p className="text-slate-500 mb-1 font-medium">How we calculate:</p>
            <p>{calc.missedCalls} missed new patient calls</p>
            <p>→ {calc.wouldHaveConverted} would convert (40%)</p>
            <p>→ <span className="text-emerald-400 font-semibold">{calc.patientsCaptured} captured by AI (50%)</span></p>
          </div>
        </div>

        {/* Right: Results */}
        <div className="flex flex-col justify-between">
          {/* Recovery Display - GREEN, not scary red */}
          <div className="bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 border border-emerald-500/30 rounded-xl p-5 text-center mb-4">
            <p className="text-emerald-400 text-xs font-bold uppercase tracking-wider mb-1">Estimated Recovery</p>
            <p className="text-3xl lg:text-4xl font-black text-emerald-400">
              {fmt(calc.monthlyRecoveryLow)} - {fmt(calc.monthlyRecoveryHigh)}
            </p>
            <p className="text-emerald-300/80 text-sm mt-1">/month</p>
            <p className="text-slate-400 text-xs mt-2">
              {fmt(calc.annualRecoveryLow)} - {fmt(calc.annualRecoveryHigh)}/year
            </p>
          </div>

          {/* ROI Display */}
          <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 text-center mb-4">
            <p className="text-slate-400 text-xs font-medium mb-1">DentSignal costs</p>
            <p className="text-xl font-bold text-white">{fmt(DENTSIGNAL_MONTHLY_PRICE)}<span className="text-sm text-slate-400">/mo</span></p>
            <p className="text-emerald-400 text-sm mt-2 font-medium">
              {calc.monthlyRecoveryLow > DENTSIGNAL_MONTHLY_PRICE 
                ? `${Math.round(calc.monthlyRecoveryLow / DENTSIGNAL_MONTHLY_PRICE)}x-${Math.round(calc.monthlyRecoveryHigh / DENTSIGNAL_MONTHLY_PRICE)}x return on investment`
                : 'Adjust sliders to see ROI'
              }
            </p>
          </div>

          {/* Disclaimer */}
          <div className="flex items-start gap-2 text-xs text-slate-500 mb-4 bg-slate-800/30 rounded-lg p-3">
            <Info className="h-4 w-4 flex-shrink-0 mt-0.5" />
            <p>
              Estimates based on 40% conversion, 50% capture rate. 
              <span className="font-medium text-slate-400"> Your results may vary</span> based on practice size, location, and call patterns.
            </p>
          </div>

          {/* CTA */}
          <Link href="/signup" className="block">
            <Button className="w-full h-12 gap-2 bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-base shadow-lg shadow-emerald-500/25">
              Start Free Trial
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <p className="text-center text-xs text-slate-500 mt-2">7-day free trial • No credit card • $199/mo</p>
        </div>
      </div>
    </div>
  )
}
