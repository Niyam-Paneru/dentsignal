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

      {/* You're Always in Control Section - Moved Up for Trust */}
      <section className="bg-white py-20">
        <div className="container mx-auto px-4">
          <div className="mb-12 text-center">
            <div className="mb-4 inline-flex items-center rounded-full bg-[#22C55E]/10 px-4 py-2 text-sm font-semibold text-[#22C55E]">
              🎛️ Full Control
            </div>
            <h2 className="mb-4 text-3xl font-bold text-[#1B3A7C]">You're Always in Control</h2>
            <p className="text-lg text-[#718096] max-w-2xl mx-auto">
              AI handles the calls, but transfers happen when you want them — or when patients need them.
            </p>
          </div>

          {/* Visual Flow Diagram */}
          <div className="mx-auto max-w-5xl">
            <div className="rounded-2xl border-2 border-[#E8EBF0] bg-gradient-to-b from-[#F8F9FA] to-white p-6 sm:p-8 shadow-lg">
              {/* Main Flow: Patient → AI → Decision Point */}
              <div className="flex flex-col md:flex-row items-center justify-center gap-4 md:gap-6">
                
                {/* Step 1: Patient Calls */}
                <div className="flex flex-col items-center text-center">
                  <div className="h-14 w-14 rounded-full bg-[#1B3A7C] flex items-center justify-center mb-2 shadow-lg">
                    <Phone className="h-7 w-7 text-white" />
                  </div>
                  <p className="text-sm font-bold text-[#2D3748]">Patient Calls</p>
                </div>
                
                {/* Arrow */}
                <div className="hidden md:flex items-center text-[#0099CC]">
                  <div className="w-6 h-0.5 bg-[#0099CC]" />
                  <ArrowRight className="h-4 w-4 -ml-1" />
                </div>
                <div className="md:hidden text-[#0099CC] py-1">↓</div>
                
                {/* Step 2: AI Answers */}
                <div className="flex flex-col items-center text-center">
                  <div className="h-14 w-14 rounded-full bg-[#22C55E] flex items-center justify-center mb-2 shadow-lg animate-pulse">
                    <Headphones className="h-7 w-7 text-white" />
                  </div>
                  <p className="text-sm font-bold text-[#2D3748]">AI Answers</p>
                </div>
                
                {/* Arrow */}
                <div className="hidden md:flex items-center text-[#0099CC]">
                  <div className="w-6 h-0.5 bg-[#0099CC]" />
                  <ArrowRight className="h-4 w-4 -ml-1" />
                </div>
                <div className="md:hidden text-[#0099CC] py-1">↓</div>
                
                {/* Step 3: You See It Live */}
                <div className="flex flex-col items-center text-center">
                  <div className="h-14 w-14 rounded-full bg-[#0099CC] flex items-center justify-center mb-2 shadow-lg">
                    <Eye className="h-7 w-7 text-white" />
                  </div>
                  <p className="text-sm font-bold text-[#2D3748]">You See It Live</p>
                </div>
              </div>

              {/* Transfer Triggers Section */}
              <div className="mt-8 pt-6 border-t border-[#E8EBF0]">
                <p className="text-center text-sm font-semibold text-[#718096] mb-6">TRANSFER TRIGGERS — Call goes to your designated person:</p>
                
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  {/* Trigger 1: You Take Over */}
                  <div className="flex items-center gap-3 p-3 rounded-xl bg-[#EF4444]/5 border border-[#EF4444]/20">
                    <div className="h-10 w-10 rounded-full bg-[#EF4444] flex items-center justify-center flex-shrink-0">
                      <MousePointer className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-[#2D3748]">You Click Transfer</p>
                      <p className="text-xs text-[#718096]">Watch live, step in anytime</p>
                    </div>
                  </div>
                  
                  {/* Trigger 2: Patient Requests Human */}
                  <div className="flex items-center gap-3 p-3 rounded-xl bg-[#0099CC]/5 border border-[#0099CC]/20">
                    <div className="h-10 w-10 rounded-full bg-[#0099CC] flex items-center justify-center flex-shrink-0">
                      <User className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-[#2D3748]">Patient Asks for Human</p>
                      <p className="text-xs text-[#718096]">"Can I talk to a real person?"</p>
                    </div>
                  </div>
                  
                  {/* Trigger 3: Emergency Detected */}
                  <div className="flex items-center gap-3 p-3 rounded-xl bg-[#EF4444]/5 border border-[#EF4444]/20">
                    <div className="h-10 w-10 rounded-full bg-[#EF4444] flex items-center justify-center flex-shrink-0">
                      <Shield className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-[#2D3748]">Emergency Detected</p>
                      <p className="text-xs text-[#718096]">"I'm in severe pain"</p>
                    </div>
                  </div>
                  
                  {/* Trigger 4: Complex Question */}
                  <div className="flex items-center gap-3 p-3 rounded-xl bg-[#1B3A7C]/5 border border-[#1B3A7C]/20">
                    <div className="h-10 w-10 rounded-full bg-[#1B3A7C] flex items-center justify-center flex-shrink-0">
                      <Headphones className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-[#2D3748]">AI Can't Answer</p>
                      <p className="text-xs text-[#718096]">Complex billing, specific cases</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Where Does the Call Go? */}
              <div className="mt-6 p-4 rounded-xl bg-[#22C55E]/5 border border-[#22C55E]/20">
                <p className="text-center text-[#2D3748]">
                  <span className="font-bold text-[#22C55E]">Where does the call go?</span>{' '}
                  You decide. Owner's cell, office manager, receptionist's direct line — whoever you configure in settings. The AI says{' '}
                  <span className="italic text-[#0099CC]">"Let me connect you with someone who can help"</span>{' '}
                  and rings your chosen number.
                </p>
              </div>
            </div>

            {/* Use Cases Row */}
            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-xl bg-[#F8F9FA] border border-[#E8EBF0] p-4 text-center">
                <span className="text-2xl">🌙</span>
                <p className="mt-2 text-sm font-bold text-[#2D3748]">After Hours</p>
                <p className="text-xs text-[#718096]">AI handles, urgent → your cell</p>
              </div>
              <div className="rounded-xl bg-[#F8F9FA] border border-[#E8EBF0] p-4 text-center">
                <span className="text-2xl">🦷</span>
                <p className="mt-2 text-sm font-bold text-[#2D3748]">During Surgery</p>
                <p className="text-xs text-[#718096]">AI answers, you focus</p>
              </div>
              <div className="rounded-xl bg-[#F8F9FA] border border-[#E8EBF0] p-4 text-center">
                <span className="text-2xl">📞</span>
                <p className="mt-2 text-sm font-bold text-[#2D3748]">Lines Busy</p>
                <p className="text-xs text-[#718096]">AI catches overflow</p>
              </div>
              <div className="rounded-xl bg-[#F8F9FA] border border-[#E8EBF0] p-4 text-center">
                <span className="text-2xl">💰</span>
                <p className="mt-2 text-sm font-bold text-[#2D3748]">High-Value Leads</p>
                <p className="text-xs text-[#718096]">Jump in personally</p>
              </div>
            </div>

            {/* Bottom Line */}
            <div className="mt-8 text-center">
              <p className="text-lg font-bold text-[#1B3A7C]">
                AI handles 80% of calls. Humans step in for the 20% that need a personal touch.
              </p>
              <p className="mt-2 text-[#718096]">
                You choose who gets transferred calls — owner, manager, or front desk.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works - 5 Steps Self-Serve First */}
      <section className="bg-white py-20">
        <div className="container mx-auto px-4">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-3xl font-bold text-[#1B3A7C]">How It Works</h2>
            <p className="text-lg text-[#718096]">
              Go from curious to fully live in under 48 hours. No technical knowledge needed.
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
                <h3 className="mb-2 text-sm font-bold text-[#2D3748]">Call the AI Demo</h3>
                <p className="text-xs text-[#718096]">
                  Dial our AI and hear exactly how it handles real patient calls
                </p>
                <div className="hidden md:block absolute top-6 left-[60%] w-[80%] h-0.5 bg-[#E8EBF0]" />
              </div>
              
              {/* Step 2 */}
              <div className="text-center relative">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-[#0099CC] text-2xl shadow-lg">
                  ✍️
                </div>
                <div className="text-xs text-[#0099CC] font-semibold mb-1">5 minutes</div>
                <h3 className="mb-2 text-sm font-bold text-[#2D3748]">Start Free Trial</h3>
                <p className="text-xs text-[#718096]">
                  Create your account and connect your calendar. No setup call required.
                </p>
                <div className="hidden md:block absolute top-6 left-[60%] w-[80%] h-0.5 bg-[#E8EBF0]" />
              </div>
              
              {/* Step 3 */}
              <div className="text-center relative">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-[#0099CC] text-2xl shadow-lg">
                  ⚙️
                </div>
                <div className="text-xs text-[#0099CC] font-semibold mb-1">Same day</div>
                <h3 className="mb-2 text-sm font-bold text-[#2D3748]">Connect Your Phone</h3>
                <p className="text-xs text-[#718096]">
                  Forward your existing line or get a new AI number in minutes
                </p>
                <div className="hidden md:block absolute top-6 left-[60%] w-[80%] h-0.5 bg-[#E8EBF0]" />
              </div>
              
              {/* Step 4 */}
              <div className="text-center relative">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-[#1B3A7C] text-2xl shadow-lg">
                  ✅
                </div>
                <div className="text-xs text-[#1B3A7C] font-semibold mb-1">24-48 hours</div>
                <h3 className="mb-2 text-sm font-bold text-[#2D3748]">Refine (Optional)</h3>
                <p className="text-xs text-[#718096]">
                  Test with your team, tweak scripts. Email us for white-glove setup.
                </p>
                <div className="hidden md:block absolute top-6 left-[60%] w-[80%] h-0.5 bg-[#E8EBF0]" />
              </div>
              
              {/* Step 5 */}
              <div className="text-center">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-[#22C55E] text-2xl shadow-lg">
                  📊
                </div>
                <div className="text-xs text-[#22C55E] font-semibold mb-1">Ongoing</div>
                <h3 className="mb-2 text-sm font-bold text-[#2D3748]">Track Results</h3>
                <p className="text-xs text-[#718096]">
                  See calls, booked appointments, and recovered revenue in your dashboard
                </p>
              </div>
            </div>
            
            {/* CTA */}
            <div className="mt-10 text-center">
              <Link href="/signup">
                <Button size="lg" className="gap-2 bg-[#22C55E] hover:bg-[#16a34a] text-white font-bold shadow-lg">
                  Start 7-Day Free Trial
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <p className="mt-4 text-sm text-[#718096]">
                🤖 Or call our AI demo: <a href="tel:+19048679643" className="font-medium text-[#0099CC] hover:underline">(904) 867-9643</a> — it's a robot, not a human
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* What Sets Us Apart */}
      <section className="bg-[#E8EBF0]/50 py-20">
        <div className="container mx-auto px-4">
          <div className="mb-12 text-center">
            <div className="mb-4 inline-flex items-center rounded-full bg-[#0099CC]/10 px-4 py-2 text-sm font-semibold text-[#0099CC]">
              💡 What You Get
            </div>
            <h2 className="mb-4 text-3xl font-bold text-[#1B3A7C]">What Sets Us Apart</h2>
            <p className="text-lg text-[#718096]">
              AI-first from day one. Simple pricing. No enterprise bloat.
            </p>
          </div>

          <div className="mx-auto max-w-3xl">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div className="flex items-start gap-3 rounded-xl bg-white p-5 border border-[#E8EBF0] shadow-sm">
                <span className="text-[#22C55E] text-xl">✓</span>
                <div>
                  <p className="font-bold text-[#2D3748]">Unlimited calls</p>
                  <p className="text-sm text-[#718096]">No caps, no overages</p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-xl bg-white p-5 border border-[#E8EBF0] shadow-sm">
                <span className="text-[#22C55E] text-xl">✓</span>
                <div>
                  <p className="font-bold text-[#2D3748]">No setup fees</p>
                  <p className="text-sm text-[#718096]">Others charge $500-2,000</p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-xl bg-white p-5 border border-[#E8EBF0] shadow-sm">
                <span className="text-[#22C55E] text-xl">✓</span>
                <div>
                  <p className="font-bold text-[#2D3748]">Month-to-month</p>
                  <p className="text-sm text-[#718096]">No 12+ month lock-in</p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-xl bg-white p-5 border border-[#E8EBF0] shadow-sm">
                <span className="text-[#22C55E] text-xl">✓</span>
                <div>
                  <p className="font-bold text-[#2D3748]">48-hour setup</p>
                  <p className="text-sm text-[#718096]">Not weeks or months</p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-xl bg-white p-5 border border-[#E8EBF0] shadow-sm">
                <span className="text-[#22C55E] text-xl">✓</span>
                <div>
                  <p className="font-bold text-[#2D3748]">Direct founder support</p>
                  <p className="text-sm text-[#718096]">4h response time</p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-xl bg-white p-5 border border-[#E8EBF0] shadow-sm">
                <span className="text-[#22C55E] text-xl">✓</span>
                <div>
                  <p className="font-bold text-[#2D3748]">Works out of the box</p>
                  <p className="text-sm text-[#718096]">No complex integrations</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Preview Section */}
      <section className="bg-white py-20" id="pricing">
        <div className="container mx-auto px-4">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-3xl font-bold text-[#1B3A7C]">Simple Pricing. Massive ROI.</h2>
            <p className="text-lg text-[#718096]">
              One plan. Everything included. No hidden fees.
            </p>
          </div>

          <div className="mx-auto max-w-md">
            {/* Single Plan Preview */}
            <div className="relative rounded-xl border-2 border-[#0099CC] bg-white p-6 text-center shadow-lg">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[#22C55E] px-3 py-1 text-xs font-bold text-white">
                FOUNDING MEMBER PRICING
              </div>
              <h3 className="text-lg font-bold text-[#1B3A7C]">Professional Plan</h3>
              <p className="mt-1 text-sm text-[#718096]">Everything you need</p>
              <div className="my-4">
                <span className="text-4xl font-bold text-[#2D3748]">$199</span>
                <span className="text-[#718096]">/mo</span>
              </div>
              <p className="text-sm text-[#718096] mb-4">Unlimited calls • 24/7 coverage • SMS reminders</p>
              <Link href="/signup">
                <Button className="w-full bg-[#22C55E] hover:bg-[#16a34a] text-white font-bold">
                  Start 7-Day Free Trial
                </Button>
              </Link>
              <p className="mt-2 text-xs text-[#718096]">No credit card required</p>
            </div>

            {/* ROI Note */}
            <p className="mt-6 text-center text-sm text-[#718096]">
              <strong className="text-[#22C55E]">ROI:</strong> Pays for itself after recovering just 1 missed call at $400/appointment.
            </p>
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

      {/* Direct Founder Support Section */}
      <section className="py-10 bg-[#E8EBF0]/50">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-[#718096]">
              <span className="font-semibold text-[#1B3A7C]">Questions or custom needs?</span> Email <a href="mailto:founder@dentsignal.me" className="font-medium text-[#0099CC] hover:underline">founder@dentsignal.me</a> — replies within 4 hours.
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
              <Button size="lg" className="gap-2 bg-[#22C55E] hover:bg-[#16a34a] text-white font-bold shadow-lg shadow-[#22C55E]/25 px-8 py-6 text-lg">
                Start 7-Day Free Trial
                <ArrowRight className="h-5 w-5" />
              </Button>
            </Link>
            <p className="mt-3 text-sm text-white/70">
              🤖 Or call AI demo: <a href="tel:+19048679643" className="text-white hover:underline">(904) 867-9643</a> — 24/7 robot
            </p>
            <p className="mt-2 text-xs text-white/60">
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
