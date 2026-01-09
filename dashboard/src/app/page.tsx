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
  Headphones,
  PhoneForwarded,
  Eye,
  MousePointer,
  User
} from 'lucide-react'
import { ROICalculator } from '@/components/landing/roi-calculator'
import { MarketingHeader } from '@/components/landing/marketing-header'
import { MarketingFooter } from '@/components/landing/marketing-footer'

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#F8F9FA]">
      <MarketingHeader />

      <main id="main-content" className="flex-1">

      {/* Trust Badge Bar - Psychology: Trust signals visible first */}
      <div className="bg-[#1f2937] py-2.5 text-center text-sm text-white">
        <div className="container mx-auto flex flex-wrap items-center justify-center gap-4 sm:gap-8 px-4">
          <span className="flex items-center gap-1.5">🛡️ HIPAA BAA Compliant</span>
          <span className="hidden sm:inline text-white/30">|</span>
          <span className="flex items-center gap-1.5">⚡ Live in 48 Hours</span>
          <span className="hidden sm:inline text-white/30">|</span>
          <span className="flex items-center gap-1.5">🕐 24/7 Support</span>
          <span className="hidden sm:inline text-white/30">|</span>
          <span className="flex items-center gap-1.5">🔒 Enterprise Encryption</span>
        </div>
      </div>

      {/* Hero Section - Loss-Focused Dark Design */}
      <section className="relative overflow-hidden bg-[#1f2937] py-16 sm:py-24">
        <div className="container relative mx-auto px-4">
          <div className="mx-auto max-w-5xl">
            <div className="grid gap-12 lg:grid-cols-5 lg:gap-8 items-center">
              
              {/* Left Column (60%) - Problem Statement */}
              <div className="lg:col-span-3 text-center lg:text-left">
                {/* Social Proof Badge */}
                <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-[#22C55E]/10 px-4 py-2 text-sm font-semibold text-[#22C55E] border border-[#22C55E]/20">
                  <span className="flex h-2 w-2 rounded-full bg-[#22C55E] animate-pulse" />
                  ✨ Trusted by 50+ dental practices nationwide
                </div>
                
                {/* Big RED Loss Amount - Realistic range per spec */}
                <div className="mb-6">
                  <span className="text-5xl sm:text-6xl lg:text-7xl font-black text-[#EF4444] tracking-tight">
                    $7K–$10K
                  </span>
                  <span className="block text-2xl sm:text-3xl font-bold text-white/80 mt-2">
                    /month lost to missed calls
                  </span>
                </div>
                
                <h1 className="mb-6 text-2xl sm:text-3xl font-bold text-white/90 leading-relaxed">
                  Right now, patients are calling your practice and hanging up.<br className="hidden sm:block" />
                  <span className="text-[#EF4444]">They book with someone else.</span>
                </h1>
                
                <p className="mb-8 text-lg text-white/70">
                  DentSignal captures those calls. Every single one.<br />
                  AI answers 24/7, books appointments, transfers emergencies.
                </p>
                
                {/* Trust Line */}
                <div className="flex flex-wrap items-center justify-center lg:justify-start gap-4 text-sm text-white/60">
                  <span className="flex items-center gap-1.5">
                    <span className="text-[#22C55E]">✓</span> HIPAA compliant
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="text-[#22C55E]">✓</span> Setup in 48 hours
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="text-[#22C55E]">✓</span> Cancel anytime
                  </span>
                </div>
              </div>
              
              {/* Right Column (40%) - CTA Area */}
              <div className="lg:col-span-2">
                <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-8 text-center">
                  <p className="mb-2 text-sm font-bold uppercase tracking-widest text-[#22C55E]">
                    Start Capturing Missed Revenue
                  </p>
                  <p className="mb-6 text-white/70 text-sm">
                    7-day free trial. No credit card required.
                  </p>
                  
                  <Link href="/signup">
                    <Button size="lg" className="w-full h-14 gap-3 bg-[#22C55E] hover:bg-[#16a34a] text-lg font-bold shadow-xl shadow-[#22C55E]/20 transition-all hover:shadow-[#22C55E]/40 hover:-translate-y-1 rounded-xl mb-4">
                      Start 7-Day Free Trial
                      <ArrowRight className="h-5 w-5" />
                    </Button>
                  </Link>
                  
                  <div className="text-center mb-4">
                    <span className="text-white/40 text-sm">or hear it first</span>
                  </div>
                  
                  <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-[#0099CC]">
                    🤖 AI Demo Line (24/7 Robot)
                  </p>
                  <a 
                    href="tel:+19048679643" 
                    className="block mb-2 text-2xl font-bold tracking-wider text-white hover:text-[#0099CC] transition-colors font-mono"
                  >
                    (904) 867-9643
                  </a>
                  <p className="text-xs text-white/50">
                    Talk to our AI. Pretend you have a toothache.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ROI Calculator Section */}
      <section className="bg-[#1f2937] py-10 border-t border-white/10" id="calculator">
        <div className="container mx-auto px-4">
          <div className="mb-10 text-center">
            <div className="mb-4 inline-flex items-center rounded-full bg-[#EF4444]/10 px-4 py-2 text-sm font-semibold text-[#EF4444]">
              <Calculator className="mr-2 h-4 w-4" />
              See What You&apos;re Losing
            </div>
            <h2 className="mb-4 text-3xl font-bold text-white">Calculate Your Lost Revenue</h2>
            <p className="mx-auto max-w-2xl text-lg text-white/70">
              Adjust the sliders to match your practice and see how much you&apos;re losing to missed calls.
            </p>
          </div>

          <ROICalculator />
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-[#F8F9FA] py-12">
        <div className="container mx-auto px-4">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-3xl font-bold text-[#1B3A7C]">What You Get With DentSignal</h2>
            <p className="text-lg text-[#718096]">
              Everything a dental practice needs to capture more patients and reduce no-shows
            </p>
          </div>

          <div className="mx-auto grid max-w-5xl gap-6 md:grid-cols-2 lg:grid-cols-3">
            <FeatureCard
              icon={Phone}
              title="📞 Calls Answered While In Surgery"
              description="Your team is busy with patients. DentSignal answers every call 24/7, books appointments, and transfers urgent cases to you."
            />
            <FeatureCard
              icon={Calendar}
              title="📅 Appointments Booked Instantly"
              description="No more phone tag. Patients book themselves in real-time. Your calendar updates automatically. No manual entry needed."
            />
            <FeatureCard
              icon={BarChart3}
              title="💰 See Which Calls Became Money"
              description="Real-time dashboard shows call value, revenue per conversation, and which calls turned into booked appointments."
            />
            <FeatureCard
              icon={Clock}
              title="✅ No-Shows Drop 60%"
              description="Automatic SMS reminders 24 hours before appointments. Patients confirm or reschedule. More confirmed appointments = more revenue."
            />
            <FeatureCard
              icon={Users}
              title="🛡️ Insurance Verified in Seconds"
              description="AI verifies insurance coverage during the call. No more 'Do you take my insurance?' callbacks. Fewer payment surprises."
            />
            <FeatureCard
              icon={DollarSign}
              title="🚨 Emergency Calls Transferred"
              description="AI detects urgency keywords and transfers emergency calls to you in seconds. Urgent patients get you, not voicemail."
            />
          </div>
        </div>
      </section>

      {/* You're Always in Control Section - Compact */}
      <section className="bg-white py-10">
        <div className="container mx-auto px-4">
          <div className="mb-8 text-center">
            <h2 className="mb-2 text-2xl font-bold text-[#1B3A7C]">🎛️ You're Always in Control</h2>
            <p className="text-[#718096]">AI handles calls, but you decide when transfers happen.</p>
          </div>

          <div className="mx-auto max-w-4xl grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="flex items-center gap-3 p-4 rounded-xl bg-[#F8F9FA] border border-[#E8EBF0]">
              <MousePointer className="h-8 w-8 text-[#EF4444] flex-shrink-0" />
              <div>
                <p className="text-sm font-bold text-[#2D3748]">You Click Transfer</p>
                <p className="text-xs text-[#718096]">Step in anytime from dashboard</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 rounded-xl bg-[#F8F9FA] border border-[#E8EBF0]">
              <User className="h-8 w-8 text-[#0099CC] flex-shrink-0" />
              <div>
                <p className="text-sm font-bold text-[#2D3748]">Patient Asks for Human</p>
                <p className="text-xs text-[#718096]">Instant transfer to your team</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 rounded-xl bg-[#F8F9FA] border border-[#E8EBF0]">
              <Shield className="h-8 w-8 text-[#EF4444] flex-shrink-0" />
              <div>
                <p className="text-sm font-bold text-[#2D3748]">Emergency Detected</p>
                <p className="text-xs text-[#718096]">AI escalates urgent cases</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-4 rounded-xl bg-[#F8F9FA] border border-[#E8EBF0]">
              <Headphones className="h-8 w-8 text-[#1B3A7C] flex-shrink-0" />
              <div>
                <p className="text-sm font-bold text-[#2D3748]">AI Can't Answer</p>
                <p className="text-xs text-[#718096]">Complex cases go to you</p>
              </div>
            </div>
          </div>

          <p className="mt-6 text-center text-sm text-[#718096]">
            <span className="font-semibold text-[#22C55E]">You configure who gets transfers:</span> Owner's cell, office manager, or receptionist line.
          </p>
        </div>
      </section>

      {/* How It Works - Compact */}
      <section className="bg-white py-10">
        <div className="container mx-auto px-4">
          <div className="mb-8 text-center">
            <h2 className="mb-2 text-2xl font-bold text-[#1B3A7C]">How It Works</h2>
            <p className="text-[#718096]">Live in under 48 hours. No technical knowledge needed.</p>
          </div>

          <div className="mx-auto max-w-4xl grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="text-center p-4 rounded-xl bg-[#F8F9FA] border border-[#E8EBF0]">
              <div className="text-2xl mb-2">📞</div>
              <div className="text-xs text-[#22C55E] font-semibold mb-1">Today</div>
              <h3 className="text-sm font-bold text-[#2D3748]">Call AI Demo</h3>
              <p className="text-xs text-[#718096]">Hear it handle real calls</p>
            </div>
            <div className="text-center p-4 rounded-xl bg-[#F8F9FA] border border-[#E8EBF0]">
              <div className="text-2xl mb-2">✍️</div>
              <div className="text-xs text-[#0099CC] font-semibold mb-1">5 minutes</div>
              <h3 className="text-sm font-bold text-[#2D3748]">Start Free Trial</h3>
              <p className="text-xs text-[#718096]">Connect your calendar</p>
            </div>
            <div className="text-center p-4 rounded-xl bg-[#F8F9FA] border border-[#E8EBF0]">
              <div className="text-2xl mb-2">⚙️</div>
              <div className="text-xs text-[#0099CC] font-semibold mb-1">Same day</div>
              <h3 className="text-sm font-bold text-[#2D3748]">Connect Phone</h3>
              <p className="text-xs text-[#718096]">Forward or get new number</p>
            </div>
            <div className="text-center p-4 rounded-xl bg-[#F8F9FA] border border-[#E8EBF0]">
              <div className="text-2xl mb-2">📊</div>
              <div className="text-xs text-[#22C55E] font-semibold mb-1">Ongoing</div>
              <h3 className="text-sm font-bold text-[#2D3748]">Track Results</h3>
              <p className="text-xs text-[#718096]">See revenue in dashboard</p>
            </div>
          </div>

          <div className="mt-6 text-center">
            <Link href="/signup">
              <Button size="lg" className="gap-2 bg-[#22C55E] hover:bg-[#16a34a] text-white font-bold shadow-lg">
                Start 7-Day Free Trial
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <p className="mt-3 text-sm text-[#718096]">
              🤖 Or call our AI demo: <a href="tel:+19048679643" className="font-medium text-[#0099CC] hover:underline">(904) 867-9643</a>
            </p>
          </div>
        </div>
      </section>

      {/* What Sets Us Apart - Compact Horizontal */}
      <section className="bg-[#F8F9FA] py-8">
        <div className="container mx-auto px-4">
          <h2 className="mb-6 text-center text-xl font-bold text-[#1B3A7C]">Why DentSignal?</h2>
          <div className="mx-auto max-w-4xl flex flex-wrap justify-center gap-x-6 gap-y-2 text-sm text-[#2D3748]">
            <span>✓ Unlimited calls</span>
            <span>✓ No setup fees</span>
            <span>✓ Month-to-month</span>
            <span>✓ 48-hour setup</span>
            <span>✓ Founder support</span>
            <span>✓ Works out of the box</span>
          </div>
        </div>
      </section>

      {/* Pricing Section - Compact */}
      <section className="bg-white py-10" id="pricing">
        <div className="container mx-auto px-4">
          <div className="mb-6 text-center">
            <h2 className="mb-2 text-2xl font-bold text-[#1B3A7C]">Simple Pricing. Massive ROI.</h2>
            <p className="text-[#718096]">One plan. Everything included.</p>
          </div>

          <div className="mx-auto max-w-sm">
            <div className="relative rounded-xl border-2 border-[#0099CC] bg-white p-5 text-center shadow-lg">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[#22C55E] px-3 py-1 text-xs font-bold text-white">
                FOUNDING MEMBER PRICING
              </div>
              <div className="my-3">
                <span className="text-3xl font-bold text-[#2D3748]">$199</span>
                <span className="text-[#718096]">/mo</span>
              </div>
              <p className="text-sm text-[#718096] mb-4">Unlimited calls • 24/7 • SMS reminders</p>
              <Link href="/signup">
                <Button className="w-full bg-[#22C55E] hover:bg-[#16a34a] text-white font-bold">
                  Start 7-Day Free Trial
                </Button>
              </Link>
              <p className="mt-2 text-xs text-[#718096]">No credit card required</p>
            </div>
            <p className="mt-4 text-center text-sm text-[#718096]">
              Pays for itself after recovering just 1 missed call.
            </p>
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="py-10 bg-[#1B3A7C]">
        <div className="container mx-auto px-4 text-center">
          <h2 className="mb-3 text-2xl font-bold text-white">Ready to Stop Losing Patients?</h2>
          <p className="mb-4 text-white/80">7-day free trial. No credit card. Cancel anytime.</p>
          <div className="mb-4 flex flex-wrap items-center justify-center gap-4 text-sm text-white/70">
            <span>✓ HIPAA compliant</span>
            <span>✓ No contracts</span>
            <span>✓ Live in 48h</span>
          </div>
          <Link href="/signup">
            <Button size="lg" className="gap-2 bg-[#22C55E] hover:bg-[#16a34a] text-white font-bold">
              Start Free Trial
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <p className="mt-3 text-sm text-white/60">
            🤖 Demo: <a href="tel:+19048679643" className="text-white/80 hover:underline">(904) 867-9643</a> • 📧 <a href="mailto:founder@dentsignal.me" className="text-white/80 hover:underline">founder@dentsignal.me</a>
          </p>
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
