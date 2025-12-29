import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { 
  Phone, 
  Calendar, 
  BarChart3, 
  ArrowRight,
  Clock,
  DollarSign,
  Users,
  Calculator,
  Shield,
  Headphones
} from 'lucide-react'
import { ROICalculator } from '@/components/landing/roi-calculator'
import { MarketingHeader } from '@/components/landing/marketing-header'
import { MarketingFooter } from '@/components/landing/marketing-footer'

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#F8F9FA]">
      <MarketingHeader />

      <main className="flex-1">

      {/* Social Proof Banner */}
      <div className="bg-[#1B3A7C] py-2 text-center text-sm text-white">
        <span className="font-medium">� Try our live demo: (904) 867-9643 — See the AI in action</span>
      </div>

      {/* Hero Section - Clean white with navy text */}
      <section className="relative overflow-hidden bg-white py-16 sm:py-24">
        <div className="container mx-auto px-4 text-center">
          <div className="mx-auto max-w-3xl">
            {/* 48-Hour Setup Badge - Teal for trust + modernity */}
            <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-[#0099CC]/10 px-4 py-2 text-sm font-semibold text-[#0099CC] border border-[#0099CC]/20">
              <span className="flex h-2 w-2 rounded-full bg-[#0099CC] animate-pulse" />
              Live in 48 Hours — No IT Required
            </div>
            
            <h1 className="mb-6 text-4xl font-extrabold tracking-tight text-[#1B3A7C] sm:text-5xl lg:text-6xl">
              Never Miss Another{' '}
              <span className="text-[#0099CC]">Patient Call</span>{' '}
              Again
            </h1>
            <p className="mb-6 text-lg leading-relaxed text-[#718096] sm:text-xl">
              AI answers every call, books appointments 24/7, and integrates with your existing systems.
              No contracts. Setup in 48 hours.
            </p>
            
            {/* Trust Strip */}
            <div className="mb-8 flex flex-wrap items-center justify-center gap-6 text-sm text-[#718096]">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-[#27AE60]">✓</span>
                <span>HIPAA compliant</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-[#27AE60]">✓</span>
                <span>No long-term contracts</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-[#27AE60]">✓</span>
                <span>Free trial included</span>
              </div>
            </div>
            
            {/* Demo Phone CTA - Teal accent */}
            <div className="mb-10 rounded-2xl border-2 border-[#0099CC]/30 bg-[#0099CC]/5 p-6 sm:p-8">
              <p className="mb-2 text-sm font-semibold uppercase tracking-wide text-[#0099CC]">
                🎧 Try It Yourself — Call Our Demo Line
              </p>
              <p className="mb-3 text-3xl font-bold tracking-wider text-[#1B3A7C] sm:text-4xl">(904) 867-9643</p>
              <p className="text-sm text-[#718096]">Pretend you&apos;re a patient with a toothache. See how natural it sounds.</p>
            </div>
            
            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link href="/signup">
                <Button size="lg" className="h-14 gap-2 bg-[#0099CC] px-8 text-base font-semibold hover:bg-[#0077A3] shadow-lg shadow-[#0099CC]/25">
                  Start Free Trial
                  <ArrowRight className="h-5 w-5" />
                </Button>
              </Link>
              <Link href="#calculator">
                <Button size="lg" variant="outline" className="h-14 gap-2 border-[#1B3A7C] px-8 text-base font-semibold text-[#1B3A7C] hover:bg-[#1B3A7C] hover:text-white">
                  See ROI Calculator
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Trust Signals - Light gray section */}
        <div className="container mx-auto mt-16 px-4">
          <div className="mx-auto grid max-w-4xl gap-4 sm:grid-cols-3">
            <div className="rounded-xl border border-[#E8EBF0] bg-white p-6 text-center shadow-sm">
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-[#27AE60]/10">
                <Shield className="h-6 w-6 text-[#27AE60]" />
              </div>
              <p className="font-bold text-[#2D3748]">HIPAA Compliant</p>
              <p className="mt-1 text-sm text-[#718096]">BAA included, end-to-end encrypted</p>
            </div>
            <div className="rounded-xl border border-[#E8EBF0] bg-white p-6 text-center shadow-sm">
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-[#0099CC]/10">
                <Clock className="h-6 w-6 text-[#0099CC]" />
              </div>
              <p className="font-bold text-[#2D3748]">24/7 Availability</p>
              <p className="mt-1 text-sm text-[#718096]">Captures after-hours emergencies</p>
            </div>
            <div className="rounded-xl border border-[#E8EBF0] bg-white p-6 text-center shadow-sm">
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-[#1B3A7C]/10">
                <Headphones className="h-6 w-6 text-[#1B3A7C]" />
              </div>
              <p className="font-bold text-[#2D3748]">Live in 48 Hours</p>
              <p className="mt-1 text-sm text-[#718096]">Zero IT work required</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section - Light gray background */}
      <section className="bg-[#E8EBF0]/50 py-20">
        <div className="container mx-auto px-4">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-3xl font-bold text-[#1B3A7C]">Everything You Need</h2>
            <p className="text-lg text-[#718096]">
              Powerful features designed specifically for dental practices
            </p>
          </div>

          <div className="mx-auto grid max-w-5xl gap-6 md:grid-cols-2 lg:grid-cols-3">
            <FeatureCard
              icon={Phone}
              title="Smart Call Handling"
              description="AI answers every call with professional, natural conversation. Handles common questions and routes complex issues appropriately."
            />
            <FeatureCard
              icon={Calendar}
              title="Automatic Booking"
              description="Books appointments directly to your calendar. Checks availability, prevents double-booking, and sends confirmations."
            />
            <FeatureCard
              icon={BarChart3}
              title="Real-Time Analytics"
              description="Track call volume, booking rates, and ROI. See what's working and identify opportunities for improvement."
            />
            <FeatureCard
              icon={Clock}
              title="24/7 Availability"
              description="Never miss an after-hours call again. AI handles calls when your office is closed and schedules callbacks."
            />
            <FeatureCard
              icon={Users}
              title="Patient Management"
              description="Recognizes returning patients, tracks preferences, and provides personalized service every time."
            />
            <FeatureCard
              icon={DollarSign}
              title="Insurance Verification"
              description="Answers common insurance questions and collects information for verification before appointments."
            />
          </div>
        </div>
      </section>

      {/* How It Works - White background */}
      <section className="bg-white py-20">
        <div className="container mx-auto px-4">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-3xl font-bold text-[#1B3A7C]">How It Works</h2>
            <p className="text-lg text-[#718096]">
              Get started in minutes, not months
            </p>
          </div>

          <div className="mx-auto grid max-w-4xl gap-8 md:grid-cols-3">
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-[#1B3A7C] text-xl font-bold text-white shadow-lg">
                1
              </div>
              <h3 className="mb-2 text-lg font-bold text-[#2D3748]">Connect Your Phone</h3>
              <p className="text-sm text-[#718096]">
                Forward your existing number or get a new AI-powered line
              </p>
            </div>
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-[#1B3A7C] text-xl font-bold text-white shadow-lg">
                2
              </div>
              <h3 className="mb-2 text-lg font-bold text-[#2D3748]">Configure Your AI</h3>
              <p className="text-sm text-[#718096]">
                Customize greetings, services, and booking preferences
              </p>
            </div>
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-[#1B3A7C] text-xl font-bold text-white shadow-lg">
                3
              </div>
              <h3 className="mb-2 text-lg font-bold text-[#2D3748]">Start Booking</h3>
              <p className="text-sm text-[#718096]">
                AI handles calls while you track everything in your dashboard
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Comparison Section - Focus on our features, not competitor bashing */}
      <section className="bg-[#E8EBF0]/50 py-20">
        <div className="container mx-auto px-4">
          <div className="mb-12 text-center">
            <div className="mb-4 inline-flex items-center rounded-full bg-[#0099CC]/10 px-4 py-2 text-sm font-semibold text-[#0099CC]">
              💡 What You Get
            </div>
            <h2 className="mb-4 text-3xl font-bold text-[#1B3A7C]">Built Different</h2>
            <p className="text-lg text-[#718096]">
              AI-first from day one. Simple pricing. No enterprise bloat.
            </p>
          </div>

          <div className="mx-auto max-w-3xl overflow-x-auto rounded-2xl border border-[#E8EBF0] bg-white shadow-lg">
            <table className="w-full min-w-[500px]">
              <thead>
                <tr className="border-b border-[#E8EBF0] bg-[#F8F9FA]">
                  <th className="px-4 sm:px-6 py-4 text-left text-sm font-semibold text-[#718096]">Feature</th>
                  <th className="px-4 sm:px-6 py-4 text-center text-sm font-semibold text-[#1B3A7C]">DentSignal</th>
                  <th className="px-4 sm:px-6 py-4 text-center text-sm font-semibold text-[#718096]">Traditional Solutions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E8EBF0]">
                <tr>
                  <td className="px-4 sm:px-6 py-4 text-[#2D3748] font-medium">Monthly Price</td>
                  <td className="px-4 sm:px-6 py-4 text-center"><span className="text-[#27AE60] font-bold">From $149/mo</span></td>
                  <td className="px-4 sm:px-6 py-4 text-center text-[#718096]">$200-500/mo</td>
                </tr>
                <tr className="bg-[#F8F9FA]/50">
                  <td className="px-4 sm:px-6 py-4 text-[#2D3748] font-medium">Setup Time</td>
                  <td className="px-4 sm:px-6 py-4 text-center"><span className="text-[#27AE60] font-bold">48 hours</span></td>
                  <td className="px-4 sm:px-6 py-4 text-center text-[#718096]">Weeks to months</td>
                </tr>
                <tr>
                  <td className="px-4 sm:px-6 py-4 text-[#2D3748] font-medium">Contract</td>
                  <td className="px-4 sm:px-6 py-4 text-center"><span className="text-[#27AE60] font-bold">Month-to-month</span></td>
                  <td className="px-4 sm:px-6 py-4 text-center text-[#718096]">Often 12+ months</td>
                </tr>
                <tr className="bg-[#F8F9FA]/50">
                  <td className="px-4 sm:px-6 py-4 text-[#2D3748] font-medium">AI Call Answering</td>
                  <td className="px-4 sm:px-6 py-4 text-center"><span className="text-[#27AE60] font-bold">24/7 included</span></td>
                  <td className="px-4 sm:px-6 py-4 text-center text-[#718096]">Often extra or limited</td>
                </tr>
                <tr>
                  <td className="px-4 sm:px-6 py-4 text-[#2D3748] font-medium">Auto Booking</td>
                  <td className="px-4 sm:px-6 py-4 text-center"><span className="text-[#27AE60] font-bold">Built-in</span></td>
                  <td className="px-4 sm:px-6 py-4 text-center text-[#718096]">Varies by provider</td>
                </tr>
                <tr className="bg-[#F8F9FA]/50">
                  <td className="px-4 sm:px-6 py-4 text-[#2D3748] font-medium">IT Requirements</td>
                  <td className="px-4 sm:px-6 py-4 text-center"><span className="text-[#27AE60] font-bold">None</span></td>
                  <td className="px-4 sm:px-6 py-4 text-center text-[#718096]">May need integrations</td>
                </tr>
                <tr>
                  <td className="px-4 sm:px-6 py-4 text-[#2D3748] font-medium">Support</td>
                  <td className="px-4 sm:px-6 py-4 text-center"><span className="text-[#27AE60] font-bold">Direct founder access</span></td>
                  <td className="px-4 sm:px-6 py-4 text-center text-[#718096]">Ticket systems</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ROI Calculator Section - White */}
      <section className="bg-[#E8EBF0]/50 py-20" id="calculator">
        <div className="container mx-auto px-4">
          <div className="mb-12 text-center">
            <div className="mb-4 inline-flex items-center rounded-full bg-[#27AE60]/10 px-4 py-2 text-sm font-semibold text-[#27AE60]">
              <Calculator className="mr-2 h-4 w-4" />
              ROI Calculator
            </div>
            <h2 className="mb-4 text-3xl font-bold text-[#1B3A7C]">See Your Potential Savings</h2>
            <p className="mx-auto max-w-2xl text-lg text-[#718096]">
              Adjust the sliders to match your practice. We show conservative estimates—your actual results depend on your call volume and conversion rates.
            </p>
          </div>

          <ROICalculator />
        </div>
      </section>

      {/* Pricing Preview Section */}
      <section className="bg-white py-20" id="pricing">
        <div className="container mx-auto px-4">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-3xl font-bold text-[#1B3A7C]">Simple, Transparent Pricing</h2>
            <p className="text-lg text-[#718096]">
              Plans starting at $149/month. No hidden fees. Cancel anytime.
            </p>
          </div>

          <div className="mx-auto grid max-w-2xl gap-6 md:grid-cols-2">
            {/* Starter Preview */}
            <div className="rounded-xl border border-[#E8EBF0] bg-white p-6 text-center shadow-sm">
              <h3 className="text-lg font-bold text-[#1B3A7C]">Starter</h3>
              <p className="mt-1 text-sm text-[#718096]">Solo & small practices</p>
              <div className="my-4">
                <span className="text-3xl font-bold text-[#2D3748]">$149</span>
                <span className="text-[#718096]">/mo</span>
              </div>
              <p className="text-sm text-[#718096]">300 calls/mo, 24/7 coverage</p>
            </div>

            {/* Professional Preview */}
            <div className="relative rounded-xl border-2 border-[#0099CC] bg-white p-6 text-center shadow-lg">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[#0099CC] px-3 py-1 text-xs font-bold text-white">
                RECOMMENDED
              </div>
              <h3 className="text-lg font-bold text-[#1B3A7C]">Professional</h3>
              <p className="mt-1 text-sm text-[#718096]">Growing practices</p>
              <div className="my-4">
                <span className="text-3xl font-bold text-[#2D3748]">$199</span>
                <span className="text-[#718096]">/mo</span>
              </div>
              <p className="text-sm text-[#718096]">Unlimited calls + SMS reminders</p>
            </div>
          </div>

          <div className="mt-10 text-center">
            <Link href="/pricing">
              <Button size="lg" variant="outline" className="gap-2 border-[#1B3A7C] text-[#1B3A7C] hover:bg-[#1B3A7C] hover:text-white">
                View Full Pricing Details
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Founder Section - Light gray background */}
      <section className="py-20 bg-[#E8EBF0]/50">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-2xl text-center">
            <div className="mb-6 inline-flex h-20 w-20 items-center justify-center rounded-full bg-[#0099CC]/10 text-3xl">
              👋
            </div>
            <h2 className="mb-4 text-2xl font-bold text-[#1B3A7C]">Built by a Solo Founder</h2>
            <p className="mb-6 text-[#718096]">
              I built DentSignal because I saw how small practices struggle with enterprise-priced tools. 
              My goal is simple: make AI call answering accessible and affordable.
            </p>
            <p className="mb-6 text-[#718096]">
              Every feature is based on real feedback from dental offices. If something doesn&apos;t work for you, 
              tell me—I read every email and ship fixes fast.
            </p>
            <p className="text-sm text-[#718096]">
              Questions? <a href="mailto:founder@dentsignal.me" className="font-medium text-[#0099CC] hover:underline">founder@dentsignal.me</a>
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section - Navy background for trust */}
      <section className="py-20 bg-white">
        <div className="container mx-auto px-4 text-center">
          <div className="mx-auto max-w-2xl rounded-2xl bg-[#1B3A7C] p-8 text-white sm:p-12 shadow-xl relative overflow-hidden">
            <h2 className="mb-4 text-3xl font-bold">Ready to Get Started?</h2>
            <p className="mb-6 text-lg text-white/90">
              Free trial included. No credit card required. Cancel anytime.
            </p>
            <div className="mb-6 flex flex-wrap items-center justify-center gap-4 text-sm text-white/80">
              <span>✓ HIPAA compliant</span>
              <span>✓ No contracts</span>
              <span>✓ Live in 48 hours</span>
            </div>
            <Link href="/signup">
              <Button size="lg" className="gap-2 bg-[#0099CC] hover:bg-[#0077A3] text-white font-semibold shadow-lg shadow-[#0099CC]/25 px-8 py-6 text-lg">
                Start Free Trial
                <ArrowRight className="h-5 w-5" />
              </Button>
            </Link>
            <p className="mt-4 text-xs text-white/60">
              🔒 BAA included • Cancel anytime
            </p>
          </div>
        </div>
      </section>

      </main>
      <MarketingFooter />
    </div>
  )
}


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
    <div className="rounded-xl border border-[#E8EBF0] bg-white p-6 transition-all hover:shadow-lg hover:border-[#0099CC]/30">
      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-[#0099CC]/10">
        <Icon className="h-5 w-5 text-[#0099CC]" />
      </div>
      <h3 className="mb-2 font-semibold text-[#1B3A7C]">{title}</h3>
      <p className="text-sm text-[#718096]">{description}</p>
    </div>
  )
}
