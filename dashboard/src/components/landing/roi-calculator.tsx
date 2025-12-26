'use client'

import { useState, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Button } from '@/components/ui/button'
import { 
  DollarSign, 
  TrendingUp, 
  Clock, 
  Phone, 
  Users,
  ArrowRight,
  CheckCircle2,
  Building2,
  AlertTriangle
} from 'lucide-react'
import Link from 'next/link'

// Practice size presets based on research data
const PRACTICE_PRESETS = {
  small: {
    label: '1-2 Dentists',
    monthlyCallVolume: 1000,
    currentAnswerRate: 65,
    currentConversionRate: 45,
    avgAppointmentValue: 400,
    missedCallsPerMonth: 350,
  },
  medium: {
    label: '3-4 Dentists',
    monthlyCallVolume: 2000,
    currentAnswerRate: 60,
    currentConversionRate: 48,
    avgAppointmentValue: 425,
    missedCallsPerMonth: 800,
  },
  large: {
    label: '5+ Dentists',
    monthlyCallVolume: 3500,
    currentAnswerRate: 55,
    currentConversionRate: 50,
    avgAppointmentValue: 450,
    missedCallsPerMonth: 1575,
  },
}

// AI performance benchmarks from research
const AI_BENCHMARKS = {
  answerRate: 0.99,  // 99% answer rate
  conversionRates: {
    conservative: 0.40,
    base: 0.50,
    optimistic: 0.60,
  },
  afterHoursProportion: 0.25,  // 25% of calls after 5pm
  afterHoursConversion: 0.55,  // 55% conversion (high intent)
}

// Operating costs from research
const AI_COSTS = {
  perCall: 0.0303,  // Deepgram + LLM + hosting
  monthlyFixed: 10,  // Base infrastructure
}

// Pricing tiers
const AI_MONTHLY_PRICE = 99  // Entry price point (not cost)

interface CalculatorInputs {
  practiceSize: 'small' | 'medium' | 'large'
  monthlyCallVolume: number
  currentAnswerRate: number
  avgAppointmentValue: number
  scenario: 'conservative' | 'base' | 'optimistic'
}

export function ROICalculator() {
  const [inputs, setInputs] = useState<CalculatorInputs>({
    practiceSize: 'small',
    monthlyCallVolume: PRACTICE_PRESETS.small.monthlyCallVolume,
    currentAnswerRate: PRACTICE_PRESETS.small.currentAnswerRate,
    avgAppointmentValue: PRACTICE_PRESETS.small.avgAppointmentValue,
    scenario: 'base',
  })
  const [showResults, setShowResults] = useState(false)

  // Update inputs when practice size changes
  const handlePracticeSizeChange = (size: 'small' | 'medium' | 'large') => {
    const preset = PRACTICE_PRESETS[size]
    setInputs({
      practiceSize: size,
      monthlyCallVolume: preset.monthlyCallVolume,
      currentAnswerRate: preset.currentAnswerRate,
      avgAppointmentValue: preset.avgAppointmentValue,
      scenario: inputs.scenario,
    })
  }

  const calculations = useMemo(() => {
    const preset = PRACTICE_PRESETS[inputs.practiceSize]
    const conversionRate = preset.currentConversionRate / 100
    const answerRate = inputs.currentAnswerRate / 100
    
    // Current state calculations
    const currentAppointments = inputs.monthlyCallVolume * answerRate * conversionRate
    const missedCalls = inputs.monthlyCallVolume * (1 - answerRate)
    
    // Missed call revenue loss (50% of missed would have booked)
    const missedCallRevenueLoss = missedCalls * inputs.avgAppointmentValue * 0.5
    
    // With AI
    const aiConversionRate = AI_BENCHMARKS.conversionRates[inputs.scenario]
    const aiAppointments = inputs.monthlyCallVolume * AI_BENCHMARKS.answerRate * aiConversionRate
    const additionalAppointments = Math.max(0, aiAppointments - currentAppointments)
    const additionalRevenue = additionalAppointments * inputs.avgAppointmentValue
    
    // After-hours capture (major differentiator)
    const afterHoursCalls = inputs.monthlyCallVolume * AI_BENCHMARKS.afterHoursProportion
    const afterHoursAppointments = afterHoursCalls * AI_BENCHMARKS.afterHoursConversion
    const afterHoursRevenue = afterHoursAppointments * inputs.avgAppointmentValue
    
    // AI operating cost (not price)
    const aiOperatingCost = (inputs.monthlyCallVolume * AI_COSTS.perCall) + AI_COSTS.monthlyFixed
    
    // Total monthly revenue increase
    const monthlyRevenueIncrease = additionalRevenue + afterHoursRevenue
    
    // Net savings (revenue - AI price)
    const monthlySavings = monthlyRevenueIncrease - AI_MONTHLY_PRICE
    const annualSavings = monthlySavings * 12
    
    // ROI calculations
    const roiPercent = (monthlySavings / AI_MONTHLY_PRICE) * 100
    const paybackDays = AI_MONTHLY_PRICE / (monthlySavings / 30)
    
    // Comparison to hiring receptionist
    const annualReceptionistCost = 65000  // Fully loaded from research
    const savingsVsHiring = annualReceptionistCost - (AI_MONTHLY_PRICE * 12)
    
    // Total appointments recovered
    const totalNewAppointments = Math.round(additionalAppointments + afterHoursAppointments)
    const missedCallsRecovered = Math.round(missedCalls * AI_BENCHMARKS.answerRate)
    
    return {
      // Current state
      currentMissedCalls: Math.round(missedCalls),
      currentAppointments: Math.round(currentAppointments),
      missedCallRevenueLoss: Math.round(missedCallRevenueLoss),
      
      // With AI
      additionalAppointments: Math.round(additionalAppointments),
      afterHoursAppointments: Math.round(afterHoursAppointments),
      totalNewAppointments,
      missedCallsRecovered,
      
      // Financial
      monthlyRevenueIncrease: Math.round(monthlyRevenueIncrease),
      monthlySavings: Math.round(monthlySavings),
      annualSavings: Math.round(annualSavings),
      aiMonthlyCost: AI_MONTHLY_PRICE,
      aiOperatingCost: Math.round(aiOperatingCost),
      
      // ROI
      roiPercent: Math.round(roiPercent),
      paybackDays: paybackDays < 1 ? 'Less than 1 day' : `${Math.round(paybackDays)} days`,
      
      // Comparison
      annualReceptionistCost,
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
        <Card className="border-[#E8EBF0] bg-white shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-[#1B3A7C]">
              <Building2 className="h-5 w-5 text-[#0099CC]" />
              Your Practice Details
            </CardTitle>
            <CardDescription className="text-[#718096]">
              Select your practice size to see accurate projections
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Practice Size Selection */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">Practice Size</Label>
              <div className="grid grid-cols-3 gap-2">
                {(['small', 'medium', 'large'] as const).map((size) => (
                  <button
                    key={size}
                    onClick={() => handlePracticeSizeChange(size)}
                    className={`rounded-lg border-2 p-3 text-center transition-all ${
                      inputs.practiceSize === size
                        ? 'border-[#0099CC] bg-[#0099CC]/10'
                        : 'border-[#E8EBF0] hover:border-[#0099CC]/50'
                    }`}
                  >
                    <div className="text-sm font-medium text-[#2D3748]">{PRACTICE_PRESETS[size].label}</div>
                    <div className="text-xs text-[#718096]">
                      ~{PRACTICE_PRESETS[size].monthlyCallVolume.toLocaleString()} calls/mo
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Monthly Call Volume */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="calls" className="flex items-center gap-2 text-[#2D3748]">
                  <Phone className="h-4 w-4 text-[#0099CC]" />
                  Monthly Call Volume
                </Label>
                <span className="text-sm font-medium text-[#1B3A7C]">{inputs.monthlyCallVolume.toLocaleString()} calls</span>
              </div>
              <Slider
                id="calls"
                min={500}
                max={5000}
                step={100}
                value={[inputs.monthlyCallVolume]}
                onValueChange={([value]) => setInputs(prev => ({ ...prev, monthlyCallVolume: value }))}
                className="cursor-pointer"
              />
              <div className="flex justify-between text-xs text-[#718096]">
                <span>500</span>
                <span>5,000</span>
              </div>
            </div>

            {/* Current Answer Rate */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="answer" className="flex items-center gap-2 text-[#2D3748]">
                  <Clock className="h-4 w-4 text-[#0099CC]" />
                  Current Answer Rate
                </Label>
                <span className="text-sm font-medium text-[#1B3A7C]">{inputs.currentAnswerRate}%</span>
              </div>
              <Slider
                id="answer"
                min={40}
                max={90}
                step={1}
                value={[inputs.currentAnswerRate]}
                onValueChange={([value]) => setInputs(prev => ({ ...prev, currentAnswerRate: value }))}
                className="cursor-pointer"
              />
              <div className="flex justify-between text-xs text-[#718096]">
                <span>40% (Poor)</span>
                <span>90% (Excellent)</span>
              </div>
            </div>

            {/* Average Appointment Value */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="revenue" className="flex items-center gap-2 text-[#2D3748]">
                  <DollarSign className="h-4 w-4 text-[#0099CC]" />
                  Avg Revenue Per Appointment
                </Label>
                <span className="text-sm font-medium text-[#1B3A7C]">{formatCurrency(inputs.avgAppointmentValue)}</span>
              </div>
              <Slider
                id="revenue"
                min={200}
                max={800}
                step={25}
                value={[inputs.avgAppointmentValue]}
                onValueChange={([value]) => setInputs(prev => ({ ...prev, avgAppointmentValue: value }))}
                className="cursor-pointer"
              />
              <div className="flex justify-between text-xs text-[#718096]">
                <span>$200</span>
                <span>$800</span>
              </div>
            </div>

            {/* Scenario Selection */}
            <div className="space-y-3">
              <Label className="text-sm font-medium text-[#2D3748]">Projection Scenario</Label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => setInputs(prev => ({ ...prev, scenario: 'conservative' }))}
                  className={`rounded-lg border-2 p-2 text-center transition-all ${
                    inputs.scenario === 'conservative'
                      ? 'border-[#F59E0B] bg-[#F59E0B]/10'
                      : 'border-[#E8EBF0] hover:border-[#F59E0B]/50'
                  }`}
                >
                  <div className="text-xs font-medium text-[#2D3748]">Conservative</div>
                  <div className="text-xs text-[#718096]">40% conv.</div>
                </button>
                <button
                  onClick={() => setInputs(prev => ({ ...prev, scenario: 'base' }))}
                  className={`rounded-lg border-2 p-2 text-center transition-all ${
                    inputs.scenario === 'base'
                      ? 'border-[#0099CC] bg-[#0099CC]/10'
                      : 'border-[#E8EBF0] hover:border-[#0099CC]/50'
                  }`}
                >
                  <div className="text-xs font-medium text-[#2D3748]">Base Case</div>
                  <div className="text-xs text-[#718096]">50% conv.</div>
                </button>
                <button
                  onClick={() => setInputs(prev => ({ ...prev, scenario: 'optimistic' }))}
                  className={`rounded-lg border-2 p-2 text-center transition-all ${
                    inputs.scenario === 'optimistic'
                      ? 'border-[#27AE60] bg-[#27AE60]/10'
                      : 'border-[#E8EBF0] hover:border-[#27AE60]/50'
                  }`}
                >
                  <div className="text-xs font-medium text-[#2D3748]">Optimistic</div>
                  <div className="text-xs text-[#718096]">60% conv.</div>
                </button>
              </div>
            </div>

            <Button 
              className="w-full bg-[#0099CC] hover:bg-[#0077A3] text-white font-semibold" 
              size="lg"
              onClick={() => setShowResults(true)}
            >
              Calculate My Savings
              <TrendingUp className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* Results Section */}
        <div className="space-y-6">
          {/* Main Savings Card */}
          <Card className={`border-2 transition-all ${showResults ? 'border-[#27AE60] bg-[#27AE60]/5' : 'border-[#E8EBF0]'}`}>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-[#1B3A7C]">
                <TrendingUp className="h-5 w-5 text-[#27AE60]" />
                Your Potential Savings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-6 text-center">
                <p className="mb-1 text-sm text-[#718096]">Annual Savings</p>
                <p className="text-5xl font-bold text-[#27AE60]">
                  {formatCurrency(calculations.annualSavings)}
                </p>
                <p className="mt-2 text-lg text-[#718096]">
                  {formatCurrency(calculations.monthlySavings)}/month
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg bg-[#F8F9FA] p-4 border border-[#E8EBF0]">
                  <p className="text-sm text-[#718096]">ROI</p>
                  <p className="text-2xl font-bold text-[#1B3A7C]">{calculations.roiPercent.toLocaleString()}%</p>
                </div>
                <div className="rounded-lg bg-[#F8F9FA] p-4 border border-[#E8EBF0]">
                  <p className="text-sm text-[#718096]">Payback Period</p>
                  <p className="text-2xl font-bold text-[#1B3A7C]">{calculations.paybackDays}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* What You're Losing Now */}
          <Card className="border-[#DC3545]/30 bg-[#DC3545]/5">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base text-[#DC3545]">
                <AlertTriangle className="h-4 w-4" />
                Currently Losing
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg bg-white p-3 border border-[#E8EBF0]">
                  <p className="text-xs text-[#718096]">Missed Calls/Month</p>
                  <p className="text-xl font-bold text-[#DC3545]">{calculations.currentMissedCalls}</p>
                </div>
                <div className="rounded-lg bg-white p-3 border border-[#E8EBF0]">
                  <p className="text-xs text-[#718096]">Lost Revenue/Month</p>
                  <p className="text-xl font-bold text-[#DC3545]">{formatCurrency(calculations.missedCallRevenueLoss)}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* With AI Benefits */}
          <Card className="border-[#E8EBF0]">
            <CardHeader className="pb-2">
              <CardTitle className="text-base text-[#1B3A7C]">With AI Receptionist</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between rounded-lg border border-[#E8EBF0] p-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#0099CC]/10">
                      <Phone className="h-4 w-4 text-[#0099CC]" />
                    </div>
                    <span className="text-sm text-[#2D3748]">Missed calls recovered/month</span>
                  </div>
                  <span className="font-bold text-[#0099CC]">+{calculations.missedCallsRecovered}</span>
                </div>

                <div className="flex items-center justify-between rounded-lg border border-[#E8EBF0] p-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#27AE60]/10">
                      <DollarSign className="h-4 w-4 text-[#27AE60]" />
                    </div>
                    <span className="text-sm text-[#2D3748]">Additional appointments/month</span>
                  </div>
                  <span className="font-bold text-[#27AE60]">+{calculations.totalNewAppointments}</span>
                </div>

                <div className="flex items-center justify-between rounded-lg border border-[#E8EBF0] p-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#1B3A7C]/10">
                      <Clock className="h-4 w-4 text-[#1B3A7C]" />
                    </div>
                    <span className="text-sm text-[#2D3748]">After-hours calls captured</span>
                  </div>
                  <span className="font-bold text-[#1B3A7C]">+{calculations.afterHoursAppointments}</span>
                </div>

                <div className="flex items-center justify-between rounded-lg border border-[#E8EBF0] p-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#F59E0B]/10">
                      <Users className="h-4 w-4 text-[#F59E0B]" />
                    </div>
                    <span className="text-sm text-[#2D3748]">vs. Hiring Receptionist</span>
                  </div>
                  <span className="font-bold text-[#F59E0B]">Save {formatCurrency(calculations.savingsVsHiring)}/yr</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Pricing Comparison */}
          <div className="rounded-xl border border-[#E8EBF0] bg-[#F8F9FA] p-4">
            <div className="mb-3 text-center text-sm font-medium text-[#718096]">Cost Comparison</div>
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg bg-white p-3 text-center border border-[#E8EBF0]">
                <p className="text-xs text-[#718096]">Full-Time Receptionist</p>
                <p className="text-lg font-bold text-[#DC3545]">{formatCurrency(calculations.annualReceptionistCost)}/yr</p>
              </div>
              <div className="rounded-lg bg-[#0099CC]/10 p-3 text-center border border-[#0099CC]/30">
                <p className="text-xs text-[#718096]">AI Receptionist</p>
                <p className="text-lg font-bold text-[#0099CC]">{formatCurrency(calculations.aiMonthlyCost * 12)}/yr</p>
              </div>
            </div>
          </div>

          {/* CTA */}
          <div className="rounded-xl bg-[#1B3A7C] p-6 text-center text-white shadow-lg">
            <h3 className="mb-2 text-xl font-bold">Save {formatCurrency(calculations.monthlySavings)}/month</h3>
            <p className="mb-4 text-sm text-white/90">
              5 founding practices get free 7-day trial
            </p>
            <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
              <Link href="/signup">
                <Button className="w-full gap-2 sm:w-auto bg-[#0099CC] hover:bg-[#0077A3] text-white font-semibold">
                  Start Free Trial
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <a href="tel:+15551234567">
                <Button variant="outline" className="w-full border-white/30 bg-white/10 text-white hover:bg-white/20 sm:w-auto">
                  📞 Try Demo Line
                </Button>
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Trust indicators */}
      <div className="mt-12 grid gap-4 text-center sm:grid-cols-4">
        <div className="flex items-center justify-center gap-2 text-sm text-[#718096]">
          <CheckCircle2 className="h-4 w-4 text-[#27AE60]" />
          No contracts
        </div>
        <div className="flex items-center justify-center gap-2 text-sm text-[#718096]">
          <CheckCircle2 className="h-4 w-4 text-[#27AE60]" />
          7-day free trial
        </div>
        <div className="flex items-center justify-center gap-2 text-sm text-[#718096]">
          <CheckCircle2 className="h-4 w-4 text-[#27AE60]" />
          Cancel anytime
        </div>
        <div className="flex items-center justify-center gap-2 text-sm text-[#718096]">
          <CheckCircle2 className="h-4 w-4 text-[#27AE60]" />
          24/7 availability
        </div>
      </div>

      {/* Data source disclaimer */}
      <p className="mt-8 text-center text-xs text-[#A0AEC0]">
        *Based on industry data from 2,000+ dental practices. Your actual results depend on call volume, conversion rates, and implementation.
      </p>
    </div>
  )
}
