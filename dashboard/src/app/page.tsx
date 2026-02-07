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
  ChevronRight,
  CheckCircle2
} from 'lucide-react'
import { MarketingHeader } from '@/components/landing/marketing-header'
import { MarketingFooter } from '@/components/landing/marketing-footer'
import { HeroCalculator } from '@/components/landing/hero-calculator'
import { WhyChooseSection } from '@/components/landing/why-choose-section'
import { ExitIntentPopup } from '@/components/landing/exit-intent-popup'
import { VideoModal } from '@/components/landing/video-modal'

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#F8F9FA]">
      <MarketingHeader />

      <main id="main-content" className="flex-1">

      {/* Trust Badge Bar */}
      <div className="bg-[#1f2937] py-2.5 text-center text-sm text-white">
        <div className="container mx-auto flex flex-wrap items-center justify-center gap-4 sm:gap-8 px-4">
          <span className="flex items-center gap-1.5">
            <Shield className="h-4 w-4 text-emerald-400" />
            HIPAA Ready
          </span>
          <span className="hidden sm:inline text-white/30">|</span>
          <span className="flex items-center gap-1.5">
            <Clock className="h-4 w-4 text-cyan-400" />
            Live in 48 Hours
          </span>
          <span className="hidden sm:inline text-white/30">|</span>
          <span className="flex items-center gap-1.5">
            <Globe className="h-4 w-4 text-blue-400" />
            24/7 Coverage
          </span>
        </div>
      </div>

      {/* Hero Section - Two Column with Calculator */}
      <section className="relative overflow-hidden bg-gradient-to-br from-[#4A90E2] via-[#1B3A7C] to-[#0F2347] py-12 sm:py-16">
        {/* Background Decorations - Softer */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-30">
          <div className="absolute -top-[20%] -left-[10%] w-[40%] h-[40%] bg-[#0099CC] rounded-full blur-[120px]" />
          <div className="absolute bottom-[10%] -right-[10%] w-[35%] h-[50%] bg-[#22C55E] rounded-full blur-[120px]" />
        </div>

        <div className="container relative mx-auto px-4">
          <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 items-center">
            {/* Left: Copy */}
            <div className="text-center lg:text-left">
              {/* Urgency Badge */}
              <div className="inline-flex items-center gap-2 bg-[#EF4444]/20 border border-[#EF4444]/30 rounded-full px-4 py-1.5 mb-6">
                <span className="flex h-2 w-2 rounded-full bg-[#EF4444] animate-pulse" />
                <span className="text-sm font-semibold text-white">25 missed new-patient calls = $21,250/month lost</span>
              </div>

              <h1 className="mb-4 text-3xl sm:text-4xl lg:text-5xl font-black text-white leading-tight">
                Stop Losing Patients to <span className="text-[#EF4444]">Missed Calls</span>
              </h1>
              
              <p className="mb-6 text-base sm:text-lg text-white/80 max-w-xl">
                AI answers every call 24/7, books appointments instantly, and transfers emergencies. See how much you&apos;re losing →
              </p>
              
              <div className="flex flex-col sm:flex-row items-center lg:items-start gap-3 mb-4">
                <Link href="/signup">
                  <Button size="lg" className="h-12 gap-2 bg-[#22C55E] hover:bg-[#16a34a] text-base font-bold shadow-lg shadow-[#22C55E]/25 transition-[transform,box-shadow] duration-150 hover:shadow-[#22C55E]/40 hover:-translate-y-0.5 rounded-lg px-6">
                    Start 9-Day Free Trial
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
                <VideoModal 
                  videoId="YOUR_DEMO_VIDEO"
                  buttonSize="lg"
                  buttonClassName="h-12 gap-2 bg-white/10 text-white border-white/20 hover:bg-white/20 font-semibold px-5"
                />
              </div>
              
              <div className="flex items-center gap-4 mt-2">
                <a href="tel:+19048679643">
                  <Button size="sm" variant="ghost" className="h-9 gap-2 text-white/70 hover:text-white hover:bg-white/10 text-sm">
                    <Phone className="h-3.5 w-3.5" />
                    Try It Now: (904) 867-9643
                  </Button>
                </a>
              </div>
              
              <p className="text-xs text-white/50">No credit card required • Cancel anytime • Live in 48 hours</p>
            </div>

            {/* Right: Calculator */}
            <div className="lg:pl-4">
              <HeroCalculator />
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof Bar - Cleaner */}
      <section className="bg-white border-b border-gray-100 py-3">
        <div className="container mx-auto px-4">
          <div className="flex flex-wrap items-center justify-center gap-6 text-sm">
            <span className="flex items-center gap-2 text-gray-600">
              <CheckCircle2 className="h-4 w-4 text-[#22C55E]" />
              Now Accepting 5 Founding Practices
            </span>
            <span className="hidden sm:inline text-gray-300">|</span>
            <span className="flex items-center gap-2 text-gray-600">
              <CheckCircle2 className="h-4 w-4 text-[#22C55E]" />
              HIPAA Ready
            </span>
            <span className="hidden sm:inline text-gray-300">|</span>
            <span className="flex items-center gap-2 text-gray-600">
              <CheckCircle2 className="h-4 w-4 text-[#22C55E]" />
              Google Calendar + Calendly Integration
            </span>
          </div>
        </div>
      </section>

      {/* ROI Action Bridge - Personalized Impact */}
      <section className="bg-[#1B3A7C] py-10 border-y-4 border-[#22C55E]">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-2xl font-bold text-white mb-3">
            Ready to Capture That Revenue?
          </h2>
          <p className="text-white/80 mb-6 max-w-xl mx-auto">
            Your custom ROI calculation shows real money on the table. Let us prove it works for your practice.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/signup">
              <Button size="lg" className="gap-2 bg-[#22C55E] hover:bg-[#16a34a] text-white font-bold px-8 shadow-lg">
                Start Free Trial - See It Work
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="gap-2 bg-white/10 text-white border-white/30 hover:bg-white/20 font-semibold">
              <Phone className="h-4 w-4" />
              Book a 15-Min Demo
            </Button>
          </div>
        </div>
      </section>

      {/* Why Choose DentSignal - Simplified */}
      <WhyChooseSection />

      {/* Quick Features Overview - Compact */}
      <section className="bg-[#F8F9FA] py-12">
        <div className="container mx-auto px-4">
          <div className="mb-8 text-center">
            <h2 className="mb-2 text-2xl font-bold text-[#1B3A7C]">Everything You Need</h2>
            <p className="text-gray-600">Built specifically for dental practices</p>
          </div>

          <div className="mx-auto grid max-w-5xl gap-3 grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
            <QuickFeature icon={Phone} title="24/7 Calls" desc="Never miss a patient" />
            <QuickFeature icon={Calendar} title="Instant Booking" desc="Books appointments live" />
            <QuickFeature icon={Bell} title="SMS Reminders" desc="Reduce no-shows" />
            <QuickFeature icon={Shield} title="Emergency Detection" desc="Routes urgent calls" />
            <QuickFeature icon={BarChart3} title="Dashboard" desc="Real-time analytics" />
            <QuickFeature icon={Globe} title="English" desc="More languages soon" />
          </div>

          <div className="mt-6 text-center">
            <Link href="/features" className="text-sm text-[#0099CC] hover:underline font-medium inline-flex items-center gap-1">
              See all features <ChevronRight className="h-3 w-3" />
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
                HIPAA ready
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
            Be one of 5 founding practices to get AI that answers every call and books appointments 24/7.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/signup">
              <Button size="lg" className="gap-2 bg-[#22C55E] hover:bg-[#16a34a] text-white font-bold px-8 shadow-lg">
                Start 9-Day Free Trial
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <a href="tel:+19048679643">
              <Button size="lg" variant="outline" className="gap-2 bg-white/10 text-white border-white/30 hover:bg-white/20 font-semibold">
                <Phone className="h-4 w-4" />
                Call AI Demo: (904) 867-9643
              </Button>
            </a>
          </div>
          <p className="mt-4 text-sm text-white/50">No credit card required</p>
        </div>
      </section>

      </main>
      <MarketingFooter />
      <ExitIntentPopup />
    </div>
  )
}


function QuickFeature({ 
  icon: Icon, 
  title,
  desc
}: { 
  icon: React.ElementType
  title: string
  desc: string
}) {
  return (
    <div className="flex flex-col items-center text-center p-3 bg-white rounded-lg border border-gray-100 hover:shadow-sm hover:border-[#0099CC]/30 transition-[border,box-shadow] duration-150">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#0099CC]/10 mb-2">
        <Icon className="h-5 w-5 text-[#0099CC]" />
      </div>
      <span className="font-semibold text-sm text-[#2D3748]">{title}</span>
      <span className="text-xs text-gray-500 mt-0.5">{desc}</span>
    </div>
  )
}
