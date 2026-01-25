'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { 
  Phone, 
  Calendar, 
  Clock,
  Shield,
  ArrowRight,
  Globe,
  Bell,
  MessageSquare,
  BarChart3,
  Headphones,
  AlertTriangle,
  Lock,
  CheckCircle,
  Zap,
  TrendingUp,
  Check
} from 'lucide-react'
import { MarketingHeader } from '@/components/landing/marketing-header'
import { MarketingFooter } from '@/components/landing/marketing-footer'
import { ROICalculator } from '@/components/landing/roi-calculator'

export default function FeaturesPage() {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <MarketingHeader />

      <main className="flex-1">
        {/* Hero Section - Compact */}
        <section className="relative overflow-hidden bg-gradient-to-br from-[#0099CC] via-[#1B3A7C] to-[#0F2347] py-14 lg:py-20">
          <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-20">
            <div className="absolute -top-[20%] -left-[10%] w-[40%] h-[40%] bg-cyan-300 rounded-full blur-[100px]" />
            <div className="absolute bottom-[10%] -right-[10%] w-[30%] h-[40%] bg-emerald-400 rounded-full blur-[100px]" />
          </div>
          
          <div className="container relative mx-auto px-4 text-center">
            <div className="inline-flex items-center gap-2 bg-white/10 border border-white/20 rounded-full px-4 py-1.5 mb-5">
              <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-sm font-medium text-white">Up to 35% of dental calls go unanswered*</span>
            </div>
            <h1 className="mx-auto max-w-3xl text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight text-white mb-4">
              Features That Actually <span className="text-cyan-300">Make You Money</span>
            </h1>
            <p className="mx-auto max-w-xl text-base lg:text-lg text-white/80 mb-8">
              Every feature designed to recover lost revenue. 24/7 AI that books appointments while you sleep.
            </p>
            <div className="flex justify-center gap-3 flex-col sm:flex-row">
              <Link href="/signup">
                <Button size="lg" className="h-12 gap-2 bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-6 shadow-lg">
                  Start Free Trial <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <a href="tel:+19048679643">
                <Button size="lg" variant="outline" className="h-12 bg-white/10 text-white border-white/30 hover:bg-white/20 font-semibold px-6">
                  <Phone className="h-4 w-4 mr-2" /> Call Demo
                </Button>
              </a>
            </div>
          </div>
        </section>

        {/* Feature Grid - Compact Cards */}
        <section className="py-14 bg-slate-50" id="features">
          <div className="container mx-auto px-4">
            <div className="mb-10 text-center">
              <h2 className="text-2xl lg:text-3xl font-bold text-slate-900">Core Features</h2>
              <p className="mt-2 text-slate-600">Everything you need to capture every patient call</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 max-w-5xl mx-auto">
              <FeatureCard
                icon={Clock}
                iconColor="text-cyan-500"
                bgColor="bg-cyan-500/10"
                title="24/7 AI Receptionist"
                points={["Never miss a call", "Weekends & holidays", "After-hours capture"]}
              />
              <FeatureCard
                icon={Calendar}
                iconColor="text-emerald-500"
                bgColor="bg-emerald-500/10"
                title="Instant Booking"
                points={["Books appointments live", "Google Calendar sync", "No double-booking"]}
              />
              <FeatureCard
                icon={AlertTriangle}
                iconColor="text-red-500"
                bgColor="bg-red-500/10"
                title="Emergency Detection"
                points={["Detects urgent cases", "Instant staff alerts", "Transfers with context"]}
              />
              <FeatureCard
                icon={Bell}
                iconColor="text-amber-500"
                bgColor="bg-amber-500/10"
                title="No-Show Reduction"
                points={["4-touch SMS sequence", "60% fewer no-shows", "Easy reschedule links"]}
              />
              <FeatureCard
                icon={Globe}
                iconColor="text-purple-500"
                bgColor="bg-purple-500/10"
                title="English + Spanish"
                points={["Native English AI", "Spanish support", "More languages coming"]}
              />
              <FeatureCard
                icon={BarChart3}
                iconColor="text-blue-500"
                bgColor="bg-blue-500/10"
                title="Live Dashboard"
                points={["Real-time call tracking", "Revenue recovered", "One-click transfer"]}
              />
            </div>
          </div>
        </section>

        {/* ROI Calculator Section */}
        <section className="py-14 bg-gradient-to-b from-slate-900 to-slate-800" id="roi">
          <div className="container mx-auto px-4">
            <div className="text-center mb-8">
              <h2 className="text-2xl lg:text-3xl font-bold text-white mb-2">See Your Revenue Loss</h2>
              <p className="text-slate-400">Based on 2025-2026 industry research</p>
            </div>
            <ROICalculator />
          </div>
        </section>

        {/* How It Works - Horizontal */}
        <section className="py-14 bg-white" id="how-it-works">
          <div className="container mx-auto px-4">
            <div className="text-center mb-10">
              <h2 className="text-2xl lg:text-3xl font-bold text-slate-900">Live in 48 Hours</h2>
              <p className="mt-2 text-slate-600">No IT team needed. No contracts.</p>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 max-w-4xl mx-auto">
              <StepCard step="1" icon={Phone} title="Forward Calls" desc="Point missed calls to your DentSignal number" />
              <StepCard step="2" icon={Zap} title="AI Learns" desc="We configure your hours, services, and rules" />
              <StepCard step="3" icon={CheckCircle} title="Go Live" desc="AI starts answering calls immediately" />
              <StepCard step="4" icon={TrendingUp} title="See ROI" desc="Watch appointments book in real-time" />
            </div>
          </div>
        </section>

        {/* Transfer Control - Compact */}
        <section className="py-12 bg-slate-50">
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto">
              <div className="text-center mb-6">
                <h2 className="text-xl lg:text-2xl font-bold text-slate-900">🎛️ You&apos;re Always in Control</h2>
                <p className="text-sm text-slate-600">AI handles calls, you decide when to step in</p>
              </div>

              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <ControlBadge icon={Headphones} text="Click to join any call" color="bg-cyan-500" />
                <ControlBadge icon={MessageSquare} text="Patient asks for human" color="bg-blue-500" />
                <ControlBadge icon={AlertTriangle} text="Emergency detected" color="bg-red-500" />
                <ControlBadge icon={Shield} text="Complex case escalation" color="bg-purple-500" />
              </div>
            </div>
          </div>
        </section>

        {/* Security Badges - Inline */}
        <section className="py-10 bg-white border-t border-slate-100">
          <div className="container mx-auto px-4">
            <div className="flex flex-wrap items-center justify-center gap-6 lg:gap-10">
              <SecurityBadge icon={Shield} title="HIPAA" label="Ready" />
              <SecurityBadge icon={Lock} title="256-Bit" label="Encrypted" />
              <SecurityBadge icon={CheckCircle} title="BAA" label="Available" />
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-14 bg-gradient-to-r from-emerald-500 to-cyan-500">
          <div className="container mx-auto px-4 text-center">
            <h2 className="text-2xl lg:text-3xl font-bold text-white mb-3">
              Stop Losing $21K/Month to Missed Calls
            </h2>
            <p className="text-white/90 mb-6 max-w-xl mx-auto">
              25 missed new-patient calls × $850 each = $21,250/month. DentSignal captures them 24/7.
            </p>
            <Link href="/signup">
              <Button size="lg" className="h-12 gap-2 bg-white text-emerald-600 hover:bg-slate-100 font-bold px-8 shadow-lg">
                Start 7-Day Free Trial <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <p className="mt-3 text-sm text-white/70">No credit card • Cancel anytime • $199/mo after trial</p>
          </div>
        </section>
      </main>

      <MarketingFooter />
    </div>
  )
}

// =============================================================================
// COMPACT COMPONENTS
// =============================================================================

function FeatureCard({ 
  icon: Icon, 
  iconColor,
  bgColor,
  title, 
  points 
}: { 
  icon: React.ElementType
  iconColor: string
  bgColor: string
  title: string
  points: string[]
}) {
  return (
    <div className="bg-white rounded-xl p-5 border border-slate-200 hover:border-cyan-300 hover:shadow-lg transition-[border,box-shadow] duration-150">
      <div className={`inline-flex h-10 w-10 items-center justify-center rounded-lg ${bgColor} mb-3`}>
        <Icon className={`h-5 w-5 ${iconColor}`} />
      </div>
      <h3 className="text-lg font-bold text-slate-900 mb-2">{title}</h3>
      <ul className="space-y-1">
        {points.map((point, i) => (
          <li key={i} className="flex items-center gap-2 text-sm text-slate-600">
            <Check className="h-3.5 w-3.5 text-emerald-500 flex-shrink-0" />
            {point}
          </li>
        ))}
      </ul>
    </div>
  )
}

function StepCard({ 
  step,
  icon: Icon, 
  title, 
  desc 
}: { 
  step: string
  icon: React.ElementType
  title: string
  desc: string
}) {
  return (
    <div className="text-center p-4 bg-slate-50 rounded-xl border border-slate-200">
      <div className="w-12 h-12 bg-cyan-500 rounded-full flex items-center justify-center mx-auto mb-3 text-white font-bold text-lg shadow-lg shadow-cyan-500/30">
        {step}
      </div>
      <h3 className="font-bold text-slate-900 mb-1">{title}</h3>
      <p className="text-xs text-slate-500">{desc}</p>
    </div>
  )
}

function ControlBadge({ icon: Icon, text, color }: { icon: React.ElementType, text: string, color: string }) {
  return (
    <div className="flex items-center gap-2 p-3 bg-white rounded-lg border border-slate-200">
      <div className={`h-8 w-8 rounded-full ${color} flex items-center justify-center flex-shrink-0`}>
        <Icon className="h-4 w-4 text-white" />
      </div>
      <span className="text-xs font-medium text-slate-700">{text}</span>
    </div>
  )
}

function SecurityBadge({ icon: Icon, title, label }: { icon: React.ElementType, title: string, label: string }) {
  return (
    <div className="flex items-center gap-2">
      <Icon className="h-6 w-6 text-slate-400" />
      <div>
        <p className="text-sm font-bold text-slate-900 leading-none">{title}</p>
        <p className="text-xs text-slate-500">{label}</p>
      </div>
    </div>
  )
}
