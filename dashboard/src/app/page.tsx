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
                
                {/* Big RED Loss Amount */}
                <div className="mb-6">
                  <span className="text-6xl sm:text-7xl lg:text-8xl font-black text-[#EF4444] tracking-tight">
                    $21,000
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
                    See Your Lost Revenue
                  </p>
                  <p className="mb-6 text-white/70 text-sm">
                    Calculate how much you&apos;re losing to missed calls
                  </p>
                  
                  <Link href="#calculator">
                    <Button size="lg" className="w-full h-14 gap-3 bg-[#22C55E] hover:bg-[#16a34a] text-lg font-bold shadow-xl shadow-[#22C55E]/20 transition-all hover:shadow-[#22C55E]/40 hover:-translate-y-1 rounded-xl mb-4">
                      Calculate My Loss
                      <ArrowRight className="h-5 w-5" />
                    </Button>
                  </Link>
                  
                  <div className="text-center mb-6">
                    <span className="text-white/40 text-sm">or</span>
                  </div>
                  
                  <p className="mb-2 text-sm font-bold uppercase tracking-widest text-[#0099CC]">
                    🎧 Try It Yourself
                  </p>
                  <a 
                    href="tel:+19048679643" 
                    className="block mb-3 text-3xl font-black tracking-wider text-white hover:text-[#0099CC] transition-colors font-mono"
                  >
                    (904) 867-9643
                  </a>
                  <p className="text-xs text-white/50">
                    Call our demo line. Pretend you have a toothache.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ROI Calculator Section - Moved Above Fold */}
      <section className="bg-[#1f2937] py-16 border-t border-white/10" id="calculator">
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

      {/* Features Section - Pain to Solution Reframe */}
      <section className="bg-[#F8F9FA] py-20">
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

      {/* How It Works - 5 Steps with Timeline */}
      <section className="bg-white py-20">
        <div className="container mx-auto px-4">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-3xl font-bold text-[#1B3A7C]">How It Works</h2>
            <p className="text-lg text-[#718096]">
              From your first call to live calls in 48 hours. No technical knowledge needed.
            </p>
          </div>

          <div className="mx-auto max-w-5xl">
            <div className="grid gap-6 md:grid-cols-5">
              {/* Step 1 */}
              <div className="text-center relative">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-[#22C55E] text-2xl shadow-lg">
                  📞
                </div>
                <div className="text-xs text-[#22C55E] font-semibold mb-1">Today</div>
                <h3 className="mb-2 text-sm font-bold text-[#2D3748]">Schedule Setup Call</h3>
                <p className="text-xs text-[#718096]">
                  15-min call to discuss your practice needs
                </p>
                <div className="hidden md:block absolute top-6 left-[60%] w-[80%] h-0.5 bg-[#E8EBF0]" />
              </div>
              
              {/* Step 2 */}
              <div className="text-center relative">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-[#0099CC] text-2xl shadow-lg">
                  ⚙️
                </div>
                <div className="text-xs text-[#0099CC] font-semibold mb-1">24 hours</div>
                <h3 className="mb-2 text-sm font-bold text-[#2D3748]">Phone Number Setup</h3>
                <p className="text-xs text-[#718096]">
                  We configure your AI + calendar integration
                </p>
                <div className="hidden md:block absolute top-6 left-[60%] w-[80%] h-0.5 bg-[#E8EBF0]" />
              </div>
              
              {/* Step 3 */}
              <div className="text-center relative">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-[#0099CC] text-2xl shadow-lg">
                  ✅
                </div>
                <div className="text-xs text-[#0099CC] font-semibold mb-1">2 hours</div>
                <h3 className="mb-2 text-sm font-bold text-[#2D3748]">Test With Team</h3>
                <p className="text-xs text-[#718096]">
                  Call the AI, verify bookings, give feedback
                </p>
                <div className="hidden md:block absolute top-6 left-[60%] w-[80%] h-0.5 bg-[#E8EBF0]" />
              </div>
              
              {/* Step 4 */}
              <div className="text-center relative">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-[#1B3A7C] text-2xl shadow-lg">
                  🚀
                </div>
                <div className="text-xs text-[#1B3A7C] font-semibold mb-1">48 hours</div>
                <h3 className="mb-2 text-sm font-bold text-[#2D3748]">Go Live</h3>
                <p className="text-xs text-[#718096]">
                  AI answers calls with live founder support
                </p>
                <div className="hidden md:block absolute top-6 left-[60%] w-[80%] h-0.5 bg-[#E8EBF0]" />
              </div>
              
              {/* Step 5 */}
              <div className="text-center">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-[#27AE60] text-2xl shadow-lg">
                  📊
                </div>
                <div className="text-xs text-[#27AE60] font-semibold mb-1">Ongoing</div>
                <h3 className="mb-2 text-sm font-bold text-[#2D3748]">Track Results</h3>
                <p className="text-xs text-[#718096]">
                  See calls, appointments, and revenue in dashboard
                </p>
              </div>
            </div>
            
            {/* CTA for Step 1 */}
            <div className="mt-10 text-center">
              <Link href="/signup">
                <Button size="lg" className="gap-2 bg-[#22C55E] hover:bg-[#16a34a] text-white font-bold shadow-lg">
                  Schedule My 15-Min Call
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
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
