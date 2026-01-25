'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { 
  ArrowLeft,
  ChevronDown,
  Check,
  X
} from 'lucide-react'
import { MarketingHeader } from '@/components/landing/marketing-header'
import { MarketingFooter } from '@/components/landing/marketing-footer'

export default function PricingPage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#F8F9FA]">
      <MarketingHeader />

      <main className="flex-1">
        {/* Back Link */}
        <div className="container mx-auto px-4 pt-6">
          <Link href="/" className="inline-flex items-center gap-1 text-sm text-[#718096] hover:text-[#1B3A7C] transition-colors">
            <ArrowLeft className="h-4 w-4" />
            Back to Home
          </Link>
        </div>

      {/* Pricing Header */}
      <section className="bg-[#F8F9FA] py-12">
        <div className="container mx-auto px-4 text-center">
          <h1 className="mb-4 text-4xl font-bold text-[#1B3A7C]">Simple, Transparent Pricing</h1>
          <p className="text-lg text-[#718096]">
            No hidden fees. No long contracts. Cancel anytime.
          </p>
        </div>
      </section>

      {/* Pricing Card - Single Plan */}
      <section className="bg-white py-16">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-lg">
            {/* Professional Plan - The Only Plan */}
            <div className="relative rounded-xl border-2 border-[#0099CC] bg-white p-8 shadow-lg">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[#22C55E] px-4 py-1 text-xs font-bold text-white">
                FOUNDING MEMBER PRICING
              </div>
              <h3 className="text-xl font-bold text-[#1B3A7C] text-center">Professional Plan</h3>
              <p className="mt-1 text-sm text-[#718096] text-center">Everything you need. No upsells.</p>
              <div className="my-6 text-center">
                <span className="text-5xl font-bold text-[#2D3748]">$199</span>
                <span className="text-[#718096]">/month</span>
              </div>
              <ul className="mb-8 space-y-3 text-sm">
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#22C55E]" /> <strong>Unlimited</strong> AI-handled calls (24/7)
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#22C55E]" /> Appointment scheduling & booking
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#22C55E]" /> Emergency call triage
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#22C55E]" /> Call recordings & transcripts
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#22C55E]" /> SMS appointment reminders
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#22C55E]" /> Custom AI voice & greeting
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#22C55E]" /> Priority email support (4h response)
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#22C55E]" /> Google Calendar integration
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#22C55E]" /> Advanced analytics dashboard
                </li>
              </ul>
              <Link href="/signup">
                <Button className="w-full h-12 bg-[#22C55E] hover:bg-[#16a34a] text-white text-lg font-bold">
                  Start 7-Day Free Trial
                </Button>
              </Link>
              <p className="mt-3 text-center text-xs text-[#718096]">
                No credit card required • No setup fees • Cancel anytime
              </p>
            </div>

            {/* The Math */}
            <div className="mt-8 rounded-xl border border-[#E8EBF0] bg-[#F8F9FA] p-6">
              <h4 className="font-bold text-[#1B3A7C] mb-3">The Math (Conservative)</h4>
              <p className="text-sm text-[#718096] mb-2">
                Your practice misses ~300 calls/month. About <strong className="text-[#EF4444]">25 are new patients</strong> worth $850 each in Year 1.
              </p>
              <p className="text-sm text-[#718096] mb-2">
                That&apos;s <strong className="text-[#EF4444]">$21,250/month</strong> or <strong className="text-[#EF4444]">$255,000/year</strong> in lost revenue.
              </p>
              <p className="text-sm text-[#718096]">
                DentSignal costs $199/month ($2,388/year) and captures those calls 24/7.
              </p>
              <p className="text-sm font-bold text-[#22C55E] mt-3">
                ROI: Pays for itself after recovering just 1 missed call.
              </p>
            </div>

            {/* Founding Customer Guarantee */}
            <div className="mt-6 text-center p-4 border border-dashed border-[#0099CC] rounded-lg bg-[#0099CC]/5">
              <p className="text-sm text-[#718096]">
                <strong className="text-[#1B3A7C]">Founding Customer Guarantee:</strong> Lock in $199/month forever. Price may increase for new customers after we reach 50 practices.
              </p>
            </div>
          </div>

          {/* Note about integrations */}
          <p className="mt-8 text-center text-sm text-[#718096]">
            Need PMS integration (Dentrix, Open Dental)? <Link href="mailto:founder@dentsignal.me" className="text-[#0099CC] hover:underline">Contact us</Link> for custom solutions.
          </p>
        </div>
      </section>

      {/* What Sets Us Apart */}
      <section className="bg-[#E8EBF0]/50 py-16">
        <div className="container mx-auto px-4">
          <h2 className="mb-8 text-center text-2xl font-bold text-[#1B3A7C]">What Sets Us Apart</h2>
          <div className="mx-auto max-w-2xl">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex items-start gap-3 rounded-lg bg-white p-4 border border-[#E8EBF0]">
                <Check className="h-5 w-5 text-[#22C55E] mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-[#2D3748]">Unlimited calls</p>
                  <p className="text-sm text-[#718096]">No caps, no overages</p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-lg bg-white p-4 border border-[#E8EBF0]">
                <Check className="h-5 w-5 text-[#22C55E] mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-[#2D3748]">No setup fees</p>
                  <p className="text-sm text-[#718096]">Others charge $500-2,000</p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-lg bg-white p-4 border border-[#E8EBF0]">
                <Check className="h-5 w-5 text-[#22C55E] mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-[#2D3748]">Month-to-month</p>
                  <p className="text-sm text-[#718096]">No 12+ month lock-in</p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-lg bg-white p-4 border border-[#E8EBF0]">
                <Check className="h-5 w-5 text-[#22C55E] mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-[#2D3748]">1-week setup</p>
                  <p className="text-sm text-[#718096]">Test, optimize, then go live</p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-lg bg-white p-4 border border-[#E8EBF0]">
                <Check className="h-5 w-5 text-[#22C55E] mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-[#2D3748]">Direct founder support</p>
                  <p className="text-sm text-[#718096]">4h response time</p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-lg bg-white p-4 border border-[#E8EBF0]">
                <Check className="h-5 w-5 text-[#22C55E] mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-[#2D3748]">Works out of the box</p>
                  <p className="text-sm text-[#718096]">No complex integrations</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="bg-white py-16">
        <div className="container mx-auto px-4">
          <div className="mb-10 text-center">
            <h2 className="mb-4 text-2xl font-bold text-[#1B3A7C]">Common Questions</h2>
            <p className="text-[#718096]">
              What dentists actually ask before signing up
            </p>
          </div>

          <div className="mx-auto max-w-3xl space-y-4">
            <FAQItem 
              question="What if the AI makes a booking mistake?"
              answer="Every appointment is recorded and reviewed. If there's an error, we fix it and refund you for that day. Plus, your team can always verify appointments before they're locked in. You stay in control."
            />
            <FAQItem 
              question="Can I customize what the AI says?"
              answer="Completely. We customize greetings, services offered, appointment types, hours, and tone to match your practice. Takes about 30 minutes during setup. Want it to mention your $99 cleaning special? Done."
            />
            <FAQItem 
              question="What happens if the AI can't handle a call?"
              answer="It transfers to your team with full context—the caller's name, what they called about, and any information collected. Smooth handoff, no repetition. Your staff gets a summary before picking up."
            />
            <FAQItem 
              question="How many calls can it handle at once?"
              answer="Unlimited. If you get 50 calls in an hour, all 50 are answered. If some need human review, they're queued for your team in priority order. No more busy signals."
            />
            <FAQItem 
              question="Can I cancel anytime?"
              answer="Yes. Month-to-month, no lock-in. Cancel anytime with 30 days notice. But most practices see ROI in the first 2 weeks—you'll want to keep it."
            />
            <FAQItem 
              question="Do you use my patient data?"
              answer="Never. Your data stays yours. We offer BAAs (Business Associate Agreements) for HIPAA compliance. We never train our AI on your patient information, and we don't share your data with anyone."
            />
            <FAQItem 
              question="How long does setup take?"
              answer="Live in 48 hours. Day 1: We set up your AI and configure your practice details. Day 2: You test scenarios, we optimize, and you go live. No IT work required—we handle everything."
            />
          </div>
        </div>
      </section>

        {/* CTA */}
        <section className="py-16 bg-[#E8EBF0]/50">
          <div className="container mx-auto px-4 text-center">
            <div className="mx-auto max-w-2xl rounded-2xl bg-[#1B3A7C] p-8 text-white sm:p-12 shadow-xl">
              <h2 className="mb-4 text-2xl font-bold">Ready to Get Started?</h2>
              <p className="mb-6 text-white/90">
                Start your free 7-day trial today. No credit card required.
              </p>
              <Link href="/signup">
                <Button size="lg" className="gap-2 bg-[#0099CC] hover:bg-[#0077A3] text-white font-semibold">
                  Start Free Trial
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <MarketingFooter />
    </div>
  )
}

function FAQItem({ question, answer }: { question: string; answer: string }) {
  return (
    <details className="group rounded-xl border border-[#E8EBF0] bg-white p-4 transition-colors duration-150 hover:border-[#0099CC]/30">
      <summary className="flex cursor-pointer items-center justify-between font-medium text-[#1B3A7C]">
        {question}
        <ChevronDown className="h-4 w-4 text-[#0099CC] transition-transform group-open:rotate-180" />
      </summary>
      <p className="mt-3 text-sm text-[#718096]">{answer}</p>
    </details>
  )
}
