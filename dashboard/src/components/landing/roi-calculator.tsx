'use client'

import { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Button } from '@/components/ui/button'
import { 
  DollarSign, 
  Phone, 
  ArrowRight,
  CheckCircle2,
  Percent,
  Calendar,
} from 'lucide-react'
import Link from 'next/link'

// =============================================================================
// ROI CALCULATOR - January 2026
// Based on dentsignal_roi_spec.md - honest, simple, 4 sliders only
// =============================================================================

// PRICING - Single source of truth
const DENTSIGNAL_MONTHLY_PRICE = 199  // $199/month - CORRECT PRICE

// DentSignal's conversion rate for missed calls (conservative estimate)
const DENTSIGNAL_CONVERSION_RATE = 0.50  // 50% of missed calls get booked

// Helper: round to nearest $100 for cleaner display
function roundToHundred(value: number): number {
  return Math.round(value / 100) * 100
}

// Helper: clamp payback days to reasonable range
function clampPaybackDays(days: number): number {
  if (days < 1) return 1
  if (days > 30) return 30
  return Math.round(days)
}

interface CalculatorInputs {
  // 4 sliders only - per spec
  monthlyCalls: number           // 500-3000, default 1000
  missedCallPercent: number      // 5-25%, default 15
  currentConversionRate: number  // 30-60%, default 45
  avgAppointmentValue: number    // 150-600, default 350
}

export function ROICalculator() {
  const [inputs, setInputs] = useState<CalculatorInputs>({
    monthlyCalls: 1000,           // Default: 1000 calls/month
    missedCallPercent: 15,        // Default: 15% missed
    currentConversionRate: 45,    // Default: 45% current human conversion
    avgAppointmentValue: 350,     // Default: $350 per appointment
  })

  const calculations = useMemo(() => {
    // ========== FORMULA FROM SPEC ==========
    // monthlyLostRevenue = monthlyCalls × missedCallRate% × currentConversionRate% × avgAppointmentValue
    // This represents what you're currently losing because missed calls × your current conversion rate
    const monthlyLostRevenue = 
      inputs.monthlyCalls * 
      (inputs.missedCallPercent / 100) * 
      (inputs.currentConversionRate / 100) * 
      inputs.avgAppointmentValue

    // monthlyRecoveredRevenue = monthlyCalls × missedCallRate% × dentSignalConversionRate% × avgAppointmentValue
    // DentSignal converts 50% of missed calls (conservative estimate)
    const monthlyRecoveredRevenue = 
      inputs.monthlyCalls * 
      (inputs.missedCallPercent / 100) * 
      DENTSIGNAL_CONVERSION_RATE * 
      inputs.avgAppointmentValue

    // monthlyNetProfit = monthlyRecoveredRevenue - $199
    const monthlyNetProfit = monthlyRecoveredRevenue - DENTSIGNAL_MONTHLY_PRICE

    // paybackDays = 199 / (monthlyRecoveredRevenue / 30)
    // How many days until DentSignal pays for itself
    const paybackDays = monthlyRecoveredRevenue > 0 
      ? (DENTSIGNAL_MONTHLY_PRICE / (monthlyRecoveredRevenue / 30))
      : 999

    // Calculate extra appointments for display
    const missedCalls = Math.round(inputs.monthlyCalls * (inputs.missedCallPercent / 100))
    const extraAppointments = Math.round(missedCalls * DENTSIGNAL_CONVERSION_RATE)

    return {
      // What you're losing (rounded to nearest $100)
      monthlyLoss: roundToHundred(monthlyLostRevenue),
      
      // What DentSignal recovers (rounded to nearest $100)
      monthlyRecovered: roundToHundred(monthlyRecoveredRevenue),
      
      // Your profit after paying for DentSignal (rounded to nearest $100)
      monthlyProfit: roundToHundred(Math.max(0, monthlyNetProfit)),
      
      // Payback period in days (clamped 1-30 for display)
      paybackDays: clampPaybackDays(paybackDays),
      
      // Extra stats for "The Math" section
      missedCalls,
      extraAppointments,
      
      // Cost display
      monthlyCost: DENTSIGNAL_MONTHLY_PRICE,
    }
  }, [inputs])

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(value)
  }

  return (
    <div className="mx-auto max-w-5xl overflow-x-hidden px-4">
      <div className="grid gap-4 lg:gap-6 lg:grid-cols-[1fr_1.2fr] items-start">
        {/* Input Section - Compact */}
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg text-slate-900">
              Your Practice
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 pt-0">
            {/* Slider 1: Monthly Calls (500-3000, default 1000) */}
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-1.5 text-sm text-slate-700">
                  <Phone className="h-3.5 w-3.5 text-cyan-600" />
                  Monthly Calls
                </Label>
                <span className="text-sm font-semibold text-slate-900">{inputs.monthlyCalls.toLocaleString()}</span>
              </div>
              <Slider
                min={500}
                max={3000}
                step={100}
                value={[inputs.monthlyCalls]}
                onValueChange={([value]) => setInputs(prev => ({ ...prev, monthlyCalls: value }))}
                className="cursor-pointer"
              />
            </div>

            {/* Slider 2: Missed Call % (5-25%, default 15%) */}
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-1.5 text-sm text-slate-700">
                  <Percent className="h-3.5 w-3.5 text-cyan-600" />
                  Missed Calls
                </Label>
                <span className="text-sm font-semibold text-slate-900">{inputs.missedCallPercent}%</span>
              </div>
              <Slider
                min={5}
                max={25}
                step={1}
                value={[inputs.missedCallPercent]}
                onValueChange={([value]) => setInputs(prev => ({ ...prev, missedCallPercent: value }))}
                className="cursor-pointer"
              />
            </div>

            {/* Slider 3: Current Conversion Rate (30-60%, default 45%) */}
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-1.5 text-sm text-slate-700">
                  <Calendar className="h-3.5 w-3.5 text-cyan-600" />
                  Your Booking Rate
                </Label>
                <span className="text-sm font-semibold text-slate-900">{inputs.currentConversionRate}%</span>
              </div>
              <Slider
                min={30}
                max={60}
                step={1}
                value={[inputs.currentConversionRate]}
                onValueChange={([value]) => setInputs(prev => ({ ...prev, currentConversionRate: value }))}
                className="cursor-pointer"
              />
            </div>

            {/* Slider 4: Average Appointment Value (150-600, default 350) */}
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-1.5 text-sm text-slate-700">
                  <DollarSign className="h-3.5 w-3.5 text-cyan-600" />
                  Avg Appointment Value
                </Label>
                <span className="text-sm font-semibold text-slate-900">{formatCurrency(inputs.avgAppointmentValue)}</span>
              </div>
              <Slider
                min={150}
                max={600}
                step={25}
                value={[inputs.avgAppointmentValue]}
                onValueChange={([value]) => setInputs(prev => ({ ...prev, avgAppointmentValue: value }))}
                className="cursor-pointer"
              />
            </div>

            {/* Formula explanation - small gray text */}
            <p className="text-xs text-slate-400 pt-2 border-t border-slate-100">
              Based on: {inputs.monthlyCalls.toLocaleString()} calls × {inputs.missedCallPercent}% missed × {inputs.currentConversionRate}% conversion × {formatCurrency(inputs.avgAppointmentValue)}
            </p>
          </CardContent>
        </Card>

        {/* Results Section - Single focus on loss */}
        <div className="space-y-4" aria-live="polite">
          {/* Main Loss Card - Big scary number */}
          <Card className="border-2 border-[#EF4444] bg-red-50">
            <CardContent className="py-6 px-4 text-center">
              <p className="text-sm font-semibold text-[#EF4444] uppercase tracking-wide mb-2">You&apos;re Losing</p>
              <p className="text-4xl sm:text-5xl font-black text-[#EF4444]">
                {formatCurrency(calculations.monthlyLoss)}
              </p>
              <p className="text-base text-red-600 mt-1">/month from missed calls</p>
              <p className="text-sm text-slate-600 mt-3">
                DentSignal recovers ~50% of this on average.
              </p>
            </CardContent>
          </Card>
          
          {/* Payback line */}
          <p className="text-center text-sm text-slate-600">
            At $199/mo, pays for itself in <span className="font-bold text-slate-900">~{calculations.paybackDays} days</span>
          </p>
        </div>
      </div>

      {/* Trust indicators - Compact */}
      <div className="mt-6 flex flex-wrap justify-center gap-4 text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
          No contracts
        </span>
        <span className="flex items-center gap-1">
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
          HIPAA compliant
        </span>
        <span className="flex items-center gap-1">
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
          Cancel anytime
        </span>
      </div>

      {/* Disclaimer */}
      <p className="mt-4 text-center text-xs text-slate-400">
        Estimates based on industry benchmarks. Your results depend on call quality and practice type.
      </p>
    </div>
  )
}
