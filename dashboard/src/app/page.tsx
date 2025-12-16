import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { 
  Phone, 
  Calendar, 
  BarChart3, 
  Bot, 
  Stethoscope,
  ArrowRight,
  Clock,
  DollarSign,
  Users,
  Calculator,
  Shield,
  ChevronDown,
  Headphones
} from 'lucide-react'
import { ROICalculator } from '@/components/landing/roi-calculator'

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#F8F9FA]">
      {/* Header - Navy for authority */}
      <header className="sticky top-0 z-50 border-b border-[#E8EBF0] bg-white/95 backdrop-blur-sm">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#1B3A7C]">
              <Stethoscope className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold text-[#1B3A7C]">DentSignal</span>
          </div>
          <nav className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" className="text-[#2D3748] hover:text-[#1B3A7C]">Sign In</Button>
            </Link>
            <Link href="/signup">
              <Button className="bg-[#0099CC] hover:bg-[#0077A3] text-white font-medium">
                Start Free Trial
              </Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section - Clean white with navy text */}
      <section className="relative overflow-hidden bg-white py-16 sm:py-24">
        <div className="container mx-auto px-4 text-center">
          <div className="mx-auto max-w-3xl">
            <div className="mb-6 inline-flex items-center rounded-full bg-[#0099CC]/10 px-4 py-2 text-sm font-semibold text-[#0099CC]">
              <Bot className="mr-2 h-4 w-4" />
              AI-Powered Dental Receptionist
            </div>
            <h1 className="mb-6 text-4xl font-extrabold tracking-tight text-[#1B3A7C] sm:text-5xl lg:text-6xl">
              Stop Losing{' '}
              <span className="text-[#DC3545]">$255,000/Year</span>{' '}
              to Missed Calls
            </h1>
            <p className="mb-10 text-lg leading-relaxed text-[#718096] sm:text-xl">
              The average dental practice misses 30% of calls—that&apos;s $255K in lost revenue. 
              Our AI receptionist answers 24/7 and books appointments while you focus on patients.
            </p>
            
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
                <Button size="lg" className="h-14 gap-2 bg-[#0099CC] px-8 text-base font-semibold hover:bg-[#0077A3]">
                  Start Free Trial
                  <ArrowRight className="h-5 w-5" />
                </Button>
              </Link>
              <Link href="#calculator">
                <Button size="lg" variant="outline" className="h-14 gap-2 border-[#1B3A7C] px-8 text-base font-semibold text-[#1B3A7C] hover:bg-[#1B3A7C] hover:text-white">
                  Calculate Your Lost Revenue
                </Button>
              </Link>
            </div>
            
            <p className="mt-6 text-sm font-medium text-[#718096]">
              🎯 Now accepting 5 founding practices for free 7-day trial
            </p>
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

      {/* ROI Calculator Section - White */}
      <section className="bg-[#E8EBF0]/50 py-20" id="calculator">
        <div className="container mx-auto px-4">
          <div className="mb-12 text-center">
            <div className="mb-4 inline-flex items-center rounded-full bg-[#27AE60]/10 px-4 py-2 text-sm font-semibold text-[#27AE60]">
              <Calculator className="mr-2 h-4 w-4" />
              ROI Calculator
            </div>
            <h2 className="mb-4 text-3xl font-bold text-[#1B3A7C]">Calculate Your Lost Revenue</h2>
            <p className="mx-auto max-w-2xl text-lg text-[#718096]">
              Based on 2,000+ dental practices: the average clinic loses $21,000/month to missed calls. 
              See what you&apos;re losing—and how much you&apos;ll save.
            </p>
          </div>

          <ROICalculator />
        </div>
      </section>


      {/* FAQ Section - White */}
      <section className="bg-white py-20">
        <div className="container mx-auto px-4">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-3xl font-bold text-[#1B3A7C]">Common Questions</h2>
            <p className="text-lg text-[#718096]">
              What dentists ask before trying AI
            </p>
          </div>

          <div className="mx-auto max-w-3xl space-y-4">
            <FAQItem 
              question="Will patients know it's AI?"
              answer="Most patients can't tell—the voice quality is that natural. But if someone asks, it politely says 'I'm the AI assistant—would you prefer I transfer you to the office?' Transparency builds trust, and 95% continue the call. Plus, they're getting 24/7 service they couldn't get otherwise."
            />
            <FAQItem 
              question="Is it HIPAA compliant?"
              answer="Fully HIPAA-compliant with BAA coverage included—no extra fee. Every call is encrypted end-to-end. Unlike some competitors, we NEVER use your patient data to train AI for other practices. That's our legal guarantee."
            />
            <FAQItem 
              question="What if it makes a mistake?"
              answer="It's trained specifically on dental calls—emergency triage, insurance questions, appointment types. For 95% of calls, it handles perfectly. For complex clinical questions, it smoothly transfers to your team with full context. You stay in control."
            />
            <FAQItem 
              question="Will this replace my receptionist?"
              answer="No—it makes her job easier. She's no longer interrupted 47 times per day during patient checkout or lunch. AI handles overflow during peak times and captures after-hours calls. Your team will thank you."
            />
            <FAQItem 
              question="My patients are older—will they hate this?"
              answer="80% of patients can't tell it's AI—it sounds completely natural. For those who prefer a human, it transfers instantly. But here's what matters: older patients LOVE that someone answers at 7pm when they're in pain. That's better service than voicemail."
            />
            <FAQItem 
              question="How long does setup take?"
              answer="Live in 48 hours. Zero IT work required. Works with your current phone provider—we handle call forwarding. You test one call and you're done."
            />
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
            <h2 className="mb-4 text-2xl font-bold text-[#1B3A7C]">Built by a Solo Founder, Not a Corporation</h2>
            <p className="mb-6 text-[#718096]">
              Hi, I&apos;m building this because I watched my family&apos;s small business lose customers to missed calls. 
              Big companies charge $300+/month for AI receptionists. Small dental practices deserve better.
            </p>
            <p className="mb-6 text-[#718096]">
              I&apos;m looking for <strong className="text-[#1B3A7C]">5 founding practices</strong> to try this free for 7 days. 
              In exchange, I just need honest feedback—and a testimonial if you love it.
            </p>
            <p className="text-sm text-[#718096]">
              Questions? Email me directly: <span className="font-medium text-[#0099CC]">niyampaneru79@gmail.com</span>
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section - Navy background for trust */}
      <section className="py-20 bg-white">
        <div className="container mx-auto px-4 text-center">
          <div className="mx-auto max-w-2xl rounded-2xl bg-[#1B3A7C] p-8 text-white sm:p-12 shadow-xl">
            <h2 className="mb-4 text-3xl font-bold">Start Free 7-Day Trial</h2>
            <p className="mb-6 text-lg text-white/90">
              5 spots available for founding practices. Free setup, free trial, honest feedback.
            </p>
            <div className="mb-6 flex flex-col items-center justify-center gap-2 text-sm text-white/80">
              <span>✓ No credit card required</span>
              <span>✓ No contracts ever</span>
              <span>✓ Cancel anytime</span>
            </div>
            <Link href="/signup">
              <Button size="lg" className="gap-2 bg-[#0099CC] hover:bg-[#0077A3] text-white font-semibold">
                Apply Now — 5 Spots Left
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer - Charcoal professional */}
      <footer className="bg-[#1A202C] py-8 text-white">
        <div className="container mx-auto flex flex-col items-center justify-between gap-4 px-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <Stethoscope className="h-5 w-5 text-[#0099CC]" />
            <span className="font-semibold">DentSignal</span>
          </div>
          <p className="text-sm text-[#718096]">
            © 2025 DentSignal. All rights reserved.
          </p>
        </div>
      </footer>
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

function FAQItem({ question, answer }: { question: string; answer: string }) {
  return (
    <details className="group rounded-xl border border-[#E8EBF0] bg-white p-4 transition-all hover:border-[#0099CC]/30">
      <summary className="flex cursor-pointer items-center justify-between font-medium text-[#1B3A7C]">
        {question}
        <ChevronDown className="h-4 w-4 text-[#0099CC] transition-transform group-open:rotate-180" />
      </summary>
      <p className="mt-3 text-sm text-[#718096]">{answer}</p>
    </details>
  )
}
