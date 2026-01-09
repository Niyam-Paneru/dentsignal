'use client'

import { useState, useMemo } from 'react'
import { Slider } from '@/components/ui/slider'
import { Button } from '@/components/ui/button'
import { 
  DollarSign, 
  Phone, 
  ArrowRight,
  TrendingDown,
  TrendingUp,
} from 'lucide-react'
import Link from 'next/link'

// =============================================================================
// ROI CALCULATOR - Based on 2025-2026 Industry Research
// =============================================================================
// Miss rate: 35% of calls go unanswered (industry avg, up to 68% peak times)
// New patient calls: ~20% of missed calls are new patients  
// Conversion: 30-40% would convert → use 35%
// First-year value: $850 per new patient
// Annual loss: $100K-$150K (industry standard)
// =============================================================================

const DENTSIGNAL_MONTHLY_PRICE = 199
const NEW_PATIENT_RATE = 0.20
const CONVERSION_RATE = 0.35

function roundToHundred(value: number): number {
  return Math.round(value / 100) * 100
}

export function ROICalculator() {
  const [monthlyCalls, setMonthlyCalls] = useState(1000)
  const [missedPercent, setMissedPercent] = useState(35)
  const [patientValue, setPatientValue] = useState(850)

  const calc = useMemo(() => {
    const missed = monthlyCalls * (missedPercent / 100)
    const newPatientMissed = missed * NEW_PATIENT_RATE
    const lostPatients = newPatientMissed * CONVERSION_RATE
    const monthlyLoss = lostPatients * patientValue
    const yearlyLoss = monthlyLoss * 12
    const recovered = monthlyLoss * 0.5
    const paybackDays = recovered > 0 ? Math.min(30, Math.max(1, Math.round(DENTSIGNAL_MONTHLY_PRICE / (recovered / 30)))) : 30

    return {
      monthlyLoss: roundToHundred(monthlyLoss),
      yearlyLoss: roundToHundred(yearlyLoss),
      recovered: roundToHundred(recovered),
      lostPatients: Math.round(lostPatients),
      paybackDays,
    }
  }, [monthlyCalls, missedPercent, patientValue])

  const fmt = (n: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)

  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-6 lg:p-8 shadow-2xl max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center mb-6">
        <h3 className="text-2xl font-bold text-white mb-1">Calculate Your Loss</h3>
        <p className="text-slate-400 text-sm">Based on 2025-2026 industry research • 35% avg miss rate</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Left: Sliders */}
        <div className="space-y-5">
          {/* Monthly Calls */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-slate-300 flex items-center gap-1.5">
                <Phone className="h-4 w-4 text-cyan-400" /> Monthly calls
              </span>
              <span className="font-bold text-white">{monthlyCalls.toLocaleString()}</span>
            </div>
            <Slider
              min={500} max={3000} step={100}
              value={[monthlyCalls]}
              onValueChange={([v]) => setMonthlyCalls(v)}
              className="cursor-pointer"
            />
          </div>

          {/* Miss Rate */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-slate-300 flex items-center gap-1.5">
                <TrendingDown className="h-4 w-4 text-red-400" /> Miss rate
              </span>
              <span className="font-bold text-white">{missedPercent}%</span>
            </div>
            <Slider
              min={20} max={50} step={1}
              value={[missedPercent]}
              onValueChange={([v]) => setMissedPercent(v)}
              className="cursor-pointer"
            />
            <p className="text-xs text-slate-500 mt-1">Industry avg: 35% (68% at peak)</p>
          </div>

          {/* Patient Value */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-slate-300 flex items-center gap-1.5">
                <DollarSign className="h-4 w-4 text-emerald-400" /> First-year value
              </span>
              <span className="font-bold text-white">{fmt(patientValue)}</span>
            </div>
            <Slider
              min={500} max={1500} step={50}
              value={[patientValue]}
              onValueChange={([v]) => setPatientValue(v)}
              className="cursor-pointer"
            />
            <p className="text-xs text-slate-500 mt-1">Lifetime value: $8K-$25K</p>
          </div>

          {/* Math breakdown */}
          <div className="bg-slate-800/50 rounded-lg p-3 text-xs text-slate-400 border border-slate-700">
            <span className="text-slate-500">The math:</span> {Math.round(monthlyCalls * missedPercent / 100)} missed × 20% new patients × 35% convert = <span className="text-white font-semibold">{calc.lostPatients} patients lost/mo</span>
          </div>
        </div>

        {/* Right: Results */}
        <div className="flex flex-col justify-between">
          {/* Loss Display */}
          <div className="bg-gradient-to-br from-red-500/20 to-red-600/10 border border-red-500/30 rounded-xl p-5 text-center mb-4">
            <p className="text-red-400 text-xs font-bold uppercase tracking-wider mb-1">You&apos;re Losing</p>
            <p className="text-4xl lg:text-5xl font-black text-red-400">{fmt(calc.yearlyLoss)}</p>
            <p className="text-red-300/80 text-sm mt-1">/year • {fmt(calc.monthlyLoss)}/month</p>
          </div>

          {/* Recovery Display */}
          <div className="bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 border border-emerald-500/30 rounded-xl p-4 text-center mb-4">
            <p className="text-emerald-400 text-xs font-bold uppercase tracking-wider mb-1">DentSignal Recovers</p>
            <p className="text-2xl lg:text-3xl font-bold text-emerald-400">~{fmt(calc.recovered)}<span className="text-lg">/mo</span></p>
            <p className="text-emerald-300/70 text-xs mt-1">Pays for itself in ~{calc.paybackDays} days</p>
          </div>

          {/* CTA */}
          <Link href="/signup" className="block">
            <Button className="w-full h-12 gap-2 bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-base shadow-lg shadow-emerald-500/25">
              Stop Losing {fmt(calc.monthlyLoss)}/mo
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <p className="text-center text-xs text-slate-500 mt-2">7-day free trial • No credit card • $199/mo</p>
        </div>
      </div>
    </div>
  )
}
