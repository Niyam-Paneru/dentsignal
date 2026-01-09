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
  TrendingUp
} from 'lucide-react'
import { MarketingHeader } from '@/components/landing/marketing-header'
import { MarketingFooter } from '@/components/landing/marketing-footer'
import { ROICalculator } from '@/components/landing/roi-calculator'

export default function FeaturesPage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#F8F9FA]">
      <MarketingHeader />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative overflow-hidden bg-[#1B3A7C] py-20 lg:py-28">
          {/* Background Decorations */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-30">
            <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] bg-blue-400 rounded-full blur-[100px]" />
            <div className="absolute top-[30%] -right-[10%] w-[40%] h-[60%] bg-cyan-300 rounded-full blur-[100px]" />
          </div>
          
          <div className="container relative mx-auto px-4 text-center">
            <h1 className="mx-auto max-w-4xl text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white mb-6">
              Every Feature Your <br className="hidden sm:block" /> Practice Needs
            </h1>
            <p className="mx-auto max-w-2xl text-xl text-[#0099CC] font-medium mb-10">
              24/7 AI coverage that never sleeps, ensuring you never miss a patient.
            </p>
            <div className="flex justify-center gap-4 flex-col sm:flex-row">
              <Link href="/signup">
                <Button size="lg" className="h-14 gap-2 bg-[#22C55E] hover:bg-[#16a34a] text-white text-base font-bold px-8 shadow-lg transition-transform hover:-translate-y-0.5">
                  Start Free Trial
                  <ArrowRight className="h-5 w-5" />
                </Button>
              </Link>
              <Button 
                size="lg" 
                variant="outline" 
                className="h-14 bg-white text-[#1B3A7C] border-white/20 hover:bg-white/90 text-base font-bold px-8"
              >
                <Phone className="h-5 w-5 mr-2" />
                Call Demo: (904) 867-9643
              </Button>
            </div>
          </div>
        </section>

        {/* Feature Grid Section */}
        <section className="py-20 bg-[#F8F9FA]" id="features">
          <div className="container mx-auto px-4">
            <div className="mb-16 text-center">
              <h2 className="text-3xl font-bold text-[#1B3A7C] sm:text-4xl">Smart Capabilities</h2>
              <p className="mt-4 text-lg text-[#718096]">Designed specifically for modern dental practices.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8 max-w-5xl mx-auto">
              {/* Feature 1: Smart Scheduling */}
              <FeatureCard
                icon={Calendar}
                title="Smart Scheduling"
                description="Seamless integration with your PMS (Dentrix, Eaglesoft, Open Dental) to book appointments instantly without human intervention."
              />

              {/* Feature 2: Emergency Triage */}
              <FeatureCard
                icon={AlertTriangle}
                title="Emergency Triage"
                description="AI intelligently prioritizes urgent cases for immediate attention, flagging severe pain or trauma directly to your on-call staff."
              />

              {/* Feature 3: Multi-language Support */}
              <FeatureCard
                icon={Globe}
                title="Multi-language Support"
                description="Communicate fluently with patients in over 30 languages, removing barriers and expanding your practice's reach."
              />

              {/* Feature 4: After-hours Receptionist */}
              <FeatureCard
                icon={Clock}
                title="24/7 After-hours Receptionist"
                description="Never miss a call, ensuring round-the-clock coverage even on weekends and holidays. Capture every lead while you rest."
              />

              {/* Feature 5: No-Show Reduction */}
              <FeatureCard
                icon={Bell}
                title="No-Show Reduction"
                description="4-touch SMS sequence with booking confirmations, 24-hour reminders, 2-hour final reminders, and easy reschedule links. Reduce no-shows by 60%."
              />

              {/* Feature 6: Live Dashboard */}
              <FeatureCard
                icon={BarChart3}
                title="Real-Time Dashboard"
                description="Monitor all calls, view transcripts, track appointments, and see revenue recovered in real-time. One-click transfer to join any live call."
              />
            </div>
          </div>
        </section>

        {/* ROI Calculator Section */}
        <section className="py-20 bg-[#1B3A7C]" id="roi">
          <div className="container mx-auto px-4">
            <div className="grid lg:grid-cols-2 gap-12 items-center mb-12">
              <div>
                <h2 className="text-3xl font-bold mb-6 text-white">Stop Leaving Money on the Table</h2>
                <p className="text-lg text-blue-100 mb-8 leading-relaxed">
                  A single missed call can cost your practice thousands over a patient&apos;s lifetime. 
                  See how much revenue DentSignal can recover for you by simply answering the phone 24/7.
                </p>
                <div className="flex gap-4 items-center">
                  <div className="h-12 w-12 rounded-full bg-[#0099CC]/20 flex items-center justify-center text-[#0099CC]">
                    <TrendingUp className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="font-bold text-lg text-white">Instant ROI</p>
                    <p className="text-sm text-blue-200">Most practices pay for the software with 1 recovered patient.</p>
                  </div>
                </div>
              </div>
              <div className="hidden lg:block" />
            </div>

            <ROICalculator />
          </div>
        </section>

        {/* How It Works Section */}
        <section className="py-24 bg-white" id="how-it-works">
          <div className="container mx-auto px-4">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-[#1B3A7C] sm:text-4xl">How It Works</h2>
              <p className="mt-4 text-[#718096]">Get started in minutes, not months.</p>
            </div>

            <div className="relative max-w-5xl mx-auto">
              {/* Connecting Line (Desktop) */}
              <div className="hidden lg:block absolute top-12 left-0 w-full h-0.5 bg-gray-200 -z-10 transform -translate-y-1/2" />
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 lg:gap-8">
                {/* Step 1 */}
                <StepCard
                  icon={Phone}
                  step="1"
                  title="Connect Phone"
                  description="Forward your missed calls to your dedicated DentSignal number."
                />

                {/* Step 2 */}
                <StepCard
                  icon={Zap}
                  step="2"
                  title="AI Training"
                  description="Our AI learns your practice's specific protocols and scheduling rules."
                />

                {/* Step 3 */}
                <StepCard
                  icon={CheckCircle}
                  step="3"
                  title="Go Live"
                  description="Activate the system. DentSignal starts answering immediately."
                />

                {/* Step 4 */}
                <StepCard
                  icon={BarChart3}
                  step="4"
                  title="See Results"
                  description="Watch your dashboard populate with booked appointments."
                />
              </div>
            </div>
          </div>
        </section>

        {/* You're in Control Section */}
        <section className="py-16 bg-[#F8F9FA]">
          <div className="container mx-auto px-4">
            <div className="mb-10 text-center">
              <h2 className="mb-3 text-2xl font-bold text-[#1B3A7C]">🎛️ You&apos;re Always in Control</h2>
              <p className="text-[#718096]">AI handles calls, but you decide when transfers happen.</p>
            </div>

            <div className="mx-auto max-w-4xl grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              <ControlCard
                icon={Headphones}
                title="You Click Transfer"
                description="Step in anytime from dashboard"
                color="text-[#EF4444]"
              />
              <ControlCard
                icon={MessageSquare}
                title="Patient Asks for Human"
                description="Instant transfer to your team"
                color="text-[#0099CC]"
              />
              <ControlCard
                icon={AlertTriangle}
                title="Emergency Detected"
                description="AI escalates urgent cases"
                color="text-[#EF4444]"
              />
              <ControlCard
                icon={Shield}
                title="AI Can't Answer"
                description="Complex cases go to you"
                color="text-[#1B3A7C]"
              />
            </div>

            <p className="mt-8 text-center text-sm text-[#718096]">
              <span className="font-semibold text-[#22C55E]">You configure who gets transfers:</span>{' '}
              Owner&apos;s cell, office manager, or receptionist line.
            </p>
          </div>
        </section>

        {/* Security Section */}
        <section className="py-16 bg-white border-t border-gray-200" id="security">
          <div className="container mx-auto px-4">
            <div className="flex flex-col lg:flex-row items-center justify-between gap-10">
              <div className="lg:w-1/3">
                <h2 className="text-2xl font-bold text-[#1B3A7C] mb-3">Enterprise Grade Security</h2>
                <p className="text-[#718096]">
                  Your patient data is protected with the highest standards of compliance and encryption.
                </p>
              </div>
              
              <div className="flex flex-wrap justify-center lg:justify-end gap-8 lg:gap-12 lg:w-2/3">
                {/* HIPAA Badge */}
                <SecurityBadge
                  icon={Shield}
                  label="Compliant"
                  title="HIPAA"
                />

                {/* Encryption Badge */}
                <SecurityBadge
                  icon={Lock}
                  label="256-Bit"
                  title="AES Encrypted"
                />

                {/* SOC2 Badge */}
                <SecurityBadge
                  icon={CheckCircle}
                  label="Certified"
                  title="SOC2 Type II"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Final CTA Section */}
        <section className="py-20 bg-white">
          <div className="container mx-auto px-4 text-center max-w-4xl">
            <h2 className="text-3xl font-bold text-[#1B3A7C] sm:text-4xl mb-6">
              Ready to transform your front desk?
            </h2>
            <p className="text-lg text-[#718096] mb-10 max-w-2xl mx-auto">
              Join hundreds of dental practices already using DentSignal to recover revenue and improve patient satisfaction.
            </p>
            <Link href="/signup">
              <Button 
                size="lg" 
                className="h-14 gap-2 bg-[#22C55E] hover:bg-[#16a34a] text-white text-lg font-bold px-10 shadow-xl transition-all hover:scale-105"
              >
                Start Your Free Trial
                <ArrowRight className="h-5 w-5" />
              </Button>
            </Link>
            <p className="mt-4 text-sm text-[#718096]">No credit card required • Cancel anytime</p>
          </div>
        </section>
      </main>

      <MarketingFooter />
    </div>
  )
}


// =============================================================================
// COMPONENTS
// =============================================================================

function FeatureCard({ 
  icon: Icon, 
  title, 
  description 
}: { 
  icon: React.ElementType
  title: string
  description: string 
}) {
  return (
    <div className="flex flex-col sm:flex-row gap-6 p-8 bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-md hover:border-[#0099CC]/30 transition-all">
      <div className="flex-shrink-0">
        <div className="flex h-14 w-14 items-center justify-center rounded-lg bg-[#1B3A7C]/10 text-[#1B3A7C]">
          <Icon className="h-8 w-8" />
        </div>
      </div>
      <div>
        <h3 className="text-xl font-bold text-[#2D3748] mb-2">{title}</h3>
        <p className="text-[#718096] leading-relaxed">{description}</p>
      </div>
    </div>
  )
}

function StepCard({ 
  icon: Icon, 
  step,
  title, 
  description 
}: { 
  icon: React.ElementType
  step: string
  title: string
  description: string 
}) {
  return (
    <div className="flex flex-col items-center text-center group">
      <div className="w-24 h-24 bg-white border-2 border-gray-100 rounded-full flex items-center justify-center mb-6 shadow-sm group-hover:border-[#0099CC] transition-colors">
        <Icon className="h-10 w-10 text-[#1B3A7C] group-hover:text-[#0099CC] transition-colors" />
      </div>
      <h3 className="text-lg font-bold text-[#1B3A7C] mb-2">{step}. {title}</h3>
      <p className="text-sm text-[#718096]">{description}</p>
    </div>
  )
}

function ControlCard({
  icon: Icon,
  title,
  description,
  color
}: {
  icon: React.ElementType
  title: string
  description: string
  color: string
}) {
  return (
    <div className="flex items-center gap-3 p-4 rounded-xl bg-white border border-[#E8EBF0] hover:shadow-sm transition-shadow">
      <Icon className={`h-8 w-8 ${color} flex-shrink-0`} />
      <div>
        <p className="text-sm font-bold text-[#2D3748]">{title}</p>
        <p className="text-xs text-[#718096]">{description}</p>
      </div>
    </div>
  )
}

function SecurityBadge({
  icon: Icon,
  label,
  title
}: {
  icon: React.ElementType
  label: string
  title: string
}) {
  return (
    <div className="flex items-center gap-3 border border-gray-300 rounded-lg px-4 py-3 bg-white hover:shadow-sm transition-shadow">
      <Icon className="h-8 w-8 text-[#1B3A7C]" />
      <div className="flex flex-col">
        <span className="text-xs font-bold text-[#718096] uppercase">{label}</span>
        <span className="text-lg font-bold text-[#1B3A7C] leading-none">{title}</span>
      </div>
    </div>
  )
}
