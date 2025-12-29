'use client'

import { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Button } from '@/components/ui/button'
import { 
  DollarSign, 
  TrendingUp, 
  Clock, 
  Phone, 
  ArrowRight,
  CheckCircle2,
  Building2,
} from 'lucide-react'
import Link from 'next/link'

// =============================================================================
// HONEST ROI CALCULATOR - December 2025
// Based on roi-calculator-honest.md - realistic, conservative, credible
// =============================================================================

// Practice size defaults (realistic starting values)
const PRACTICE_DEFAULTS = {
  small: {
    label: '1–2 dentists',
    monthlyCallVolume: 900,      // 700-1,100 typical
    currentAnswerRate: 70,       // 30% missed
    currentConversionRate: 45,   // within 40-60% range
    avgAppointmentValue: 350,    // between $250-500
  },
  medium: {
    label: '3–4 dentists',
    monthlyCallVolume: 1500,     // 1,300-1,800 typical
    currentAnswerRate: 68,
    currentConversionRate: 48,
    avgAppointmentValue: 375,
  },
  large: {
    label: '5+ dentists',
    monthlyCallVolume: 2200,
    currentAnswerRate: 65,
    currentConversionRate: 50,
    avgAppointmentValue: 400,
  },
}

// AI performance (sane ranges, don't oversell)
const AI_BENCHMARKS = {
  answerRate: 0.97,  // 97%, not 99% - don't promise perfection
  conversion: {
    conservative: 0.42,
    base: 0.50,
    optimistic: 0.55,
  },
  // Key insight: only SOME missed calls are real booking opportunities
  missedToBookedFactor: {
    conservative: 0.15,  // 15% of missed calls
    base: 0.25,          // 25%
    optimistic: 0.35,    // 35%
  },
}

// Pricing
const AI_MONTHLY_PRICE = 149

// Receptionist comparison
const RECEPTIONIST_ANNUAL_COST = 65000  // Conservative estimate

interface CalculatorInputs {
  practiceSize: 'small' | 'medium' | 'large'
  monthlyCallVolume: number
  currentAnswerRate: number
  avgAppointmentValue: number
  scenario: 'conservative' | 'base' | 'optimistic'
}

// Helper: clamp numbers to avoid cartoonish output
function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

export function ROICalculator() {
  const [inputs, setInputs] = useState<CalculatorInputs>({
    practiceSize: 'small',
    monthlyCallVolume: PRACTICE_DEFAULTS.small.monthlyCallVolume,
    currentAnswerRate: PRACTICE_DEFAULTS.small.currentAnswerRate,
    avgAppointmentValue: PRACTICE_DEFAULTS.small.avgAppointmentValue,
    scenario: 'base',
  })

  const handlePracticeSizeChange = (size: 'small' | 'medium' | 'large') => {
    const preset = PRACTICE_DEFAULTS[size]
    setInputs({
      practiceSize: size,
      monthlyCallVolume: preset.monthlyCallVolume,
      currentAnswerRate: preset.currentAnswerRate,
      avgAppointmentValue: preset.avgAppointmentValue,
      scenario: inputs.scenario,
    })
  }

  const calculations = useMemo(() => {
    const preset = PRACTICE_DEFAULTS[inputs.practiceSize]
    const answerRate = inputs.currentAnswerRate / 100
    const conversionRate = preset.currentConversionRate / 100
    
    // ========== CURRENT STATE ==========
    const totalCalls = inputs.monthlyCallVolume
    const answeredNow = totalCalls * answerRate
    const apptsNow = answeredNow * conversionRate
    const missedCalls = totalCalls - answeredNow
    
    // ========== WITH AI ==========
    // Key: only a PORTION of missed calls are real appointment opportunities
    // Not all missed calls = lost bookings (many are existing patients, questions, etc.)
    const missedToBookedFactor = AI_BENCHMARKS.missedToBookedFactor[inputs.scenario]
    const extraApptsFromMissed = missedCalls * missedToBookedFactor
    
    // Total appointments with AI = current + recovered from missed
    const extraAppts = extraApptsFromMissed
    const extraRevenue = extraAppts * inputs.avgAppointmentValue
    
    // ========== NET GAIN ==========
    const netMonthlyGain = extraRevenue - AI_MONTHLY_PRICE
    const netAnnualGain = netMonthlyGain * 12
    
    // ========== ROI & PAYBACK ==========
    const roiPercent = AI_MONTHLY_PRICE > 0 ? (netMonthlyGain / AI_MONTHLY_PRICE) * 100 : 0
    const paybackDays = netMonthlyGain > 0 ? (AI_MONTHLY_PRICE / netMonthlyGain) * 30 : 999
    
    // ========== APPLY HARD CAPS (credibility) ==========
    const safeNetMonthlyGain = clamp(netMonthlyGain, 0, 3500)    // Max $3,500/month
    const safeNetAnnualGain = clamp(netAnnualGain, 0, 42000)     // Max $42k/year
    const safeRoiPercent = clamp(roiPercent, 0, 900)             // Max 900% ROI
    const safePaybackDays = clamp(paybackDays, 7, 60)            // 1-8 weeks
    const safeExtraAppts = clamp(Math.round(extraAppts), 0, 25)  // Max 25/month
    
    // Payback display
    const paybackDisplay = safePaybackDays <= 14 ? '1–2 weeks' :
                           safePaybackDays <= 30 ? '2–4 weeks' :
                           safePaybackDays <= 45 ? '4–6 weeks' :
                           '6–8 weeks'
    
    // Receptionist comparison
    const aiAnnualCost = AI_MONTHLY_PRICE * 12
    const savingsVsHiring = RECEPTIONIST_ANNUAL_COST - aiAnnualCost
    
    return {
      // Current state
      missedCalls: Math.round(missedCalls),
      currentAppts: Math.round(apptsNow),
      
      // With AI (capped for credibility)
      extraAppts: safeExtraAppts,
      
      // Financial (HONEST numbers)
      monthlySavings: Math.round(safeNetMonthlyGain),
      annualSavings: Math.round(safeNetAnnualGain),
      roiPercent: Math.round(safeRoiPercent),
      paybackDisplay,
      
      // Comparison
      aiMonthlyCost: AI_MONTHLY_PRICE,
      aiAnnualCost,
      savingsVsHiring: Math.round(savingsVsHiring),
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
    <div className="mx-auto max-w-5xl">
      <div className="grid gap-8 lg:grid-cols-2">
        {/* Input Section */}
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-slate-900">
              <Building2 className="h-5 w-5 text-cyan-600" />
              Your Practice Details
            </CardTitle>
            <p className="text-sm text-slate-500">
              Adjust these to match your practice. We&apos;ll show a conservative estimate.
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Practice Size Selection */}
            <div className="space-y-3">
              <Label className="text-sm font-medium text-slate-700">Practice Size</Label>
              <div className="grid grid-cols-3 gap-2">
                {(['small', 'medium', 'large'] as const).map((size) => (
                  <button
                    key={size}
                    onClick={() => handlePracticeSizeChange(size)}
                    className={`rounded-lg border-2 p-3 text-center transition-all ${
                      inputs.practiceSize === size
                        ? 'border-cyan-600 bg-cyan-50'
                        : 'border-slate-200 hover:border-cyan-300'
                    }`}
                  >
                    <div className="text-sm font-medium text-slate-800">{PRACTICE_DEFAULTS[size].label}</div>
                    <div className="text-xs text-slate-500">
                      ~{PRACTICE_DEFAULTS[size].monthlyCallVolume.toLocaleString()} calls/mo
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Monthly Call Volume */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-2 text-slate-700">
                  <Phone className="h-4 w-4 text-cyan-600" />
                  Monthly Call Volume
                </Label>
                <span className="text-sm font-medium text-slate-900">{inputs.monthlyCallVolume.toLocaleString()} calls</span>
              </div>
              <Slider
                min={500}
                max={3000}
                step={50}
                value={[inputs.monthlyCallVolume]}
                onValueChange={([value]) => setInputs(prev => ({ ...prev, monthlyCallVolume: value }))}
                className="cursor-pointer"
              />
              <div className="flex justify-between text-xs text-slate-500">
                <span>500</span>
                <span>3,000</span>
              </div>
            </div>

            {/* Current Answer Rate */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-2 text-slate-700">
                  <Clock className="h-4 w-4 text-cyan-600" />
                  Current Answer Rate
                </Label>
                <span className="text-sm font-medium text-slate-900">{inputs.currentAnswerRate}%</span>
              </div>
              <Slider
                min={50}
                max={85}
                step={1}
                value={[inputs.currentAnswerRate]}
                onValueChange={([value]) => setInputs(prev => ({ ...prev, currentAnswerRate: value }))}
                className="cursor-pointer"
              />
              <div className="flex justify-between text-xs text-slate-500">
                <span>50% (Struggling)</span>
                <span>85% (Excellent)</span>
              </div>
            </div>

            {/* Average Appointment Value */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="flex items-center gap-2 text-slate-700">
                  <DollarSign className="h-4 w-4 text-cyan-600" />
                  Avg Revenue Per Appointment
                </Label>
                <span className="text-sm font-medium text-slate-900">{formatCurrency(inputs.avgAppointmentValue)}</span>
              </div>
              <Slider
                min={200}
                max={600}
                step={25}
                value={[inputs.avgAppointmentValue]}
                onValueChange={([value]) => setInputs(prev => ({ ...prev, avgAppointmentValue: value }))}
                className="cursor-pointer"
              />
              <div className="flex justify-between text-xs text-slate-500">
                <span>$200</span>
                <span>$600</span>
              </div>
            </div>

            {/* Scenario Selection */}
            <div className="space-y-3">
              <Label className="text-sm font-medium text-slate-700">Projection Scenario</Label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => setInputs(prev => ({ ...prev, scenario: 'conservative' }))}
                  className={`rounded-lg border-2 p-2 text-center transition-all ${
                    inputs.scenario === 'conservative'
                      ? 'border-amber-500 bg-amber-50'
                      : 'border-slate-200 hover:border-amber-300'
                  }`}
                >
                  <div className="text-xs font-medium text-slate-800">Conservative</div>
                  <div className="text-xs text-slate-500">15% recovery</div>
                </button>
                <button
                  onClick={() => setInputs(prev => ({ ...prev, scenario: 'base' }))}
                  className={`rounded-lg border-2 p-2 text-center transition-all ${
                    inputs.scenario === 'base'
                      ? 'border-cyan-600 bg-cyan-50'
                      : 'border-slate-200 hover:border-cyan-300'
                  }`}
                >
                  <div className="text-xs font-medium text-slate-800">Base Case</div>
                  <div className="text-xs text-slate-500">25% recovery</div>
                </button>
                <button
                  onClick={() => setInputs(prev => ({ ...prev, scenario: 'optimistic' }))}
                  className={`rounded-lg border-2 p-2 text-center transition-all ${
                    inputs.scenario === 'optimistic'
                      ? 'border-emerald-500 bg-emerald-50'
                      : 'border-slate-200 hover:border-emerald-300'
                  }`}
                >
                  <div className="text-xs font-medium text-slate-800">Optimistic</div>
                  <div className="text-xs text-slate-500">35% recovery</div>
                </button>
              </div>
              <p className="text-xs text-slate-500">
                % of missed calls that become actual bookings with AI
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Results Section */}
        <div className="space-y-6">
          {/* Main Savings Card */}
          <Card className="border-2 border-emerald-200 bg-emerald-50/50">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-slate-900">
                <TrendingUp className="h-5 w-5 text-emerald-600" />
                Estimated Revenue Recovery
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-6 text-center">
                <p className="mb-1 text-sm text-slate-600">Monthly Gain</p>
                <p className="text-4xl font-bold text-emerald-600">
                  +{formatCurrency(calculations.monthlySavings)}
                </p>
                <p className="mt-1 text-sm text-slate-500">
                  {formatCurrency(calculations.annualSavings)}/year
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg bg-white p-4 border border-slate-200">
                  <p className="text-sm text-slate-600">ROI</p>
                  <p className="text-2xl font-bold text-slate-900">{calculations.roiPercent}%</p>
                </div>
                <div className="rounded-lg bg-white p-4 border border-slate-200">
                  <p className="text-sm text-slate-600">Payback Period</p>
                  <p className="text-2xl font-bold text-slate-900">{calculations.paybackDisplay}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* What This Means */}
          <Card className="border-slate-200">
            <CardHeader className="pb-2">
              <CardTitle className="text-base text-slate-900">What This Means</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between rounded-lg border border-slate-200 p-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-cyan-100">
                      <Phone className="h-4 w-4 text-cyan-600" />
                    </div>
                    <span className="text-sm text-slate-700">Missed calls currently</span>
                  </div>
                  <span className="font-semibold text-slate-900">{calculations.missedCalls}/mo</span>
                </div>

                <div className="flex items-center justify-between rounded-lg border border-slate-200 p-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    </div>
                    <span className="text-sm text-slate-700">Extra appointments recovered</span>
                  </div>
                  <span className="font-semibold text-emerald-600">+{calculations.extraAppts}/mo</span>
                </div>

                <div className="flex items-center justify-between rounded-lg border border-slate-200 p-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100">
                      <DollarSign className="h-4 w-4 text-slate-600" />
                    </div>
                    <span className="text-sm text-slate-700">AI receptionist cost</span>
                  </div>
                  <span className="font-semibold text-slate-900">{formatCurrency(calculations.aiMonthlyCost)}/mo</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* vs Hiring Comparison */}
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <div className="mb-3 text-center text-sm font-medium text-slate-600">vs. Hiring a Receptionist</div>
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg bg-white p-3 text-center border border-slate-200">
                <p className="text-xs text-slate-500">Full-Time Receptionist</p>
                <p className="text-lg font-bold text-slate-700">{formatCurrency(RECEPTIONIST_ANNUAL_COST)}/yr</p>
              </div>
              <div className="rounded-lg bg-cyan-50 p-3 text-center border border-cyan-200">
                <p className="text-xs text-slate-500">AI Receptionist</p>
                <p className="text-lg font-bold text-cyan-700">{formatCurrency(calculations.aiAnnualCost)}/yr</p>
              </div>
            </div>
            <p className="mt-3 text-center text-sm text-slate-600">
              Save {formatCurrency(calculations.savingsVsHiring)}/year vs. hiring
            </p>
          </div>

          {/* CTA */}
          <div className="rounded-xl bg-slate-900 p-6 text-center text-white">
            <h3 className="mb-2 text-xl font-semibold">Ready to recover those missed calls?</h3>
            <p className="mb-4 text-sm text-slate-300">
              Free trial. No credit card required. Cancel anytime.
            </p>
            <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
              <Link href="/signup">
                <Button className="w-full gap-2 sm:w-auto bg-cyan-600 hover:bg-cyan-700 text-white font-semibold">
                  Start Free Trial
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <a href="tel:+19048679643">
                <Button variant="outline" className="w-full border-slate-600 bg-transparent text-white hover:bg-slate-800 sm:w-auto">
                  📞 Try Demo Line
                </Button>
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Trust indicators */}
      <div className="mt-10 grid gap-4 text-center sm:grid-cols-4">
        <div className="flex items-center justify-center gap-2 text-sm text-slate-600">
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          No contracts
        </div>
        <div className="flex items-center justify-center gap-2 text-sm text-slate-600">
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          Free trial included
        </div>
        <div className="flex items-center justify-center gap-2 text-sm text-slate-600">
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          Cancel anytime
        </div>
        <div className="flex items-center justify-center gap-2 text-sm text-slate-600">
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          HIPAA compliant
        </div>
      </div>

      {/* Disclaimer */}
      <p className="mt-6 text-center text-xs text-slate-400">
        Estimates are based on typical practices (60–75% answer rate, 40–60% conversion).
        Your actual results will depend on your existing systems, staff, and call quality.
      </p>
    </div>
  )
}
