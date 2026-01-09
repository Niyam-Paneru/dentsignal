import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { 
  Phone, 
  Calendar, 
  BarChart3, 
  ArrowRight,
  Clock,
  Bell,
  Shield,
  Globe,
  ChevronRight
} from 'lucide-react'
import { MarketingHeader } from '@/components/landing/marketing-header'
import { MarketingFooter } from '@/components/landing/marketing-footer'

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#F8F9FA]">
      <MarketingHeader />

      <main id="main-content" className="flex-1">

      {/* Trust Badge Bar */}
      <div className="bg-[#1f2937] py-2.5 text-center text-sm text-white">
        <div className="container mx-auto flex flex-wrap items-center justify-center gap-4 sm:gap-8 px-4">
          <span className="flex items-center gap-1.5">🛡️ HIPAA Compliant</span>
          <span className="hidden sm:inline text-white/30">|</span>
          <span className="flex items-center gap-1.5">⚡ Live in 48 Hours</span>
          <span className="hidden sm:inline text-white/30">|</span>
          <span className="flex items-center gap-1.5">🕐 24/7 Coverage</span>
        </div>
      </div>

      {/* Hero Section - Clean, Single Focus */}
      <section className="relative overflow-hidden bg-[#1f2937] py-20 sm:py-28">
        {/* Background Decorations */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-20">
          <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] bg-blue-400 rounded-full blur-[100px]" />
          <div className="absolute top-[30%] -right-[10%] w-[40%] h-[60%] bg-cyan-300 rounded-full blur-[100px]" />
        </div>

        <div className="container relative mx-auto px-4">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="mb-6 text-4xl sm:text-5xl lg:text-6xl font-black text-white leading-tight">
              Stop Losing Patients to <span className="text-[#EF4444]">Missed Calls</span>
            </h1>
            
            <p className="mb-8 text-lg sm:text-xl text-white/70 max-w-2xl mx-auto">
              AI answers every call 24/7, books appointments, and transfers emergencies to you.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-6">
              <Link href="/signup">
                <Button size="lg" className="h-14 gap-3 bg-[#22C55E] hover:bg-[#16a34a] text-lg font-bold shadow-xl shadow-[#22C55E]/20 transition-all hover:shadow-[#22C55E]/40 hover:-translate-y-1 rounded-xl px-8">
                  Start 7-Day Free Trial
                  <ArrowRight className="h-5 w-5" />
                </Button>
              </Link>
              <Link href="/features">
                <Button size="lg" variant="outline" className="h-14 gap-2 bg-transparent text-white border-white/30 hover:bg-white/10 font-semibold px-6">
                  See All Features
                  <ChevronRight className="h-5 w-5" />
                </Button>
              </Link>
            </div>
            
            <p className="text-sm text-white/50 mb-4">No credit card required. Cancel anytime.</p>
            
            <p className="text-sm text-white/60">
              🤖 Or call the AI demo: <a href="tel:+19048679643" className="font-mono text-[#0099CC] hover:underline">(904) 867-9643</a>
            </p>
          </div>
        </div>
      </section>

      {/* Social Proof Bar */}
      <section className="bg-[#1f2937] border-t border-white/10 py-4">
        <div className="container mx-auto px-4">
          <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-white/70">
            <span className="flex items-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-[#22C55E] animate-pulse" />
              Trusted by 50+ dental practices
            </span>
            <span className="hidden sm:inline text-white/30">|</span>
            <span className="text-[#EF4444] font-semibold">$7K–$10K/month lost to missed calls</span>
          </div>
        </div>
      </section>

      {/* Quick Features Overview - Links to /features */}
      <section className="bg-[#F8F9FA] py-16">
        <div className="container mx-auto px-4">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-3xl font-bold text-[#1B3A7C]">Everything You Need</h2>
            <p className="text-lg text-[#718096]">
              Built specifically for dental practices
            </p>
          </div>

          <div className="mx-auto grid max-w-4xl gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <QuickFeature icon={Phone} title="24/7 Call Handling" />
            <QuickFeature icon={Calendar} title="Instant Booking" />
            <QuickFeature icon={Bell} title="SMS Reminders" />
            <QuickFeature icon={Shield} title="Emergency Triage" />
            <QuickFeature icon={BarChart3} title="Live Dashboard" />
            <QuickFeature icon={Globe} title="30+ Languages" />
          </div>

          <div className="mt-10 text-center">
            <Link href="/features">
              <Button variant="outline" className="gap-2 text-[#1B3A7C] border-[#1B3A7C]/30 hover:bg-[#1B3A7C]/5">
                View All Features
                <ChevronRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Value Prop - Simple */}
      <section className="bg-white py-16">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="mb-6 text-3xl font-bold text-[#1B3A7C]">
              One Missed Call = One Lost Patient
            </h2>
            <p className="text-lg text-[#718096] mb-8">
              The average dental patient is worth $850+ in their first year alone. 
              DentSignal pays for itself after recovering just <strong className="text-[#2D3748]">one call per month</strong>.
            </p>
            <div className="flex flex-wrap justify-center gap-6 text-sm text-[#2D3748]">
              <span className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-[#0099CC]" />
                Live in 48 hours
              </span>
              <span className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-[#0099CC]" />
                HIPAA compliant
              </span>
              <span className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-[#0099CC]" />
                No setup fees
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Teaser */}
      <section className="bg-[#F8F9FA] py-16">
        <div className="container mx-auto px-4 text-center">
          <div className="mb-4 inline-flex items-center rounded-full bg-[#22C55E]/10 px-4 py-2 text-sm font-semibold text-[#22C55E]">
            FOUNDING MEMBER PRICING
          </div>
          <h2 className="mb-2 text-4xl font-bold text-[#2D3748]">
            $199<span className="text-lg font-normal text-[#718096]">/month</span>
          </h2>
          <p className="text-[#718096] mb-6">Unlimited calls • 24/7 • Everything included</p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/signup">
              <Button size="lg" className="gap-2 bg-[#22C55E] hover:bg-[#16a34a] text-white font-bold px-8">
                Start Free Trial
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/pricing">
              <Button variant="ghost" className="gap-2 text-[#718096] hover:text-[#2D3748]">
                See Full Pricing Details
                <ChevronRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-16 bg-[#1B3A7C]">
        <div className="container mx-auto px-4 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white">Ready to Stop Losing Patients?</h2>
          <p className="mb-8 text-white/80 max-w-xl mx-auto">
            Join 50+ dental practices already using DentSignal to answer every call and book more appointments.
          </p>
          <Link href="/signup">
            <Button size="lg" className="gap-2 bg-[#22C55E] hover:bg-[#16a34a] text-white font-bold px-8 shadow-lg">
              Start 7-Day Free Trial
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <p className="mt-4 text-sm text-white/50">No credit card required</p>
        </div>
      </section>

      </main>
      <MarketingFooter />
    </div>
  )
}


function QuickFeature({ 
  icon: Icon, 
  title 
}: { 
  icon: React.ElementType
  title: string 
}) {
  return (
    <div className="flex items-center gap-4 p-4 bg-white rounded-xl border border-[#E8EBF0] hover:shadow-sm hover:border-[#0099CC]/30 transition-all">
      <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-[#1B3A7C]/10">
        <Icon className="h-6 w-6 text-[#1B3A7C]" />
      </div>
      <span className="font-semibold text-[#2D3748]">{title}</span>
    </div>
  )
}
