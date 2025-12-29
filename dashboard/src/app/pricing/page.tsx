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

      {/* Pricing Cards */}
      <section className="bg-white py-16">
        <div className="container mx-auto px-4">
          <div className="mx-auto grid max-w-3xl gap-8 md:grid-cols-2">
            {/* Starter */}
            <div className="rounded-xl border border-[#E8EBF0] bg-white p-6 shadow-sm">
              <h3 className="text-lg font-bold text-[#1B3A7C]">Starter</h3>
              <p className="mt-1 text-sm text-[#718096]">Perfect for solo & small practices</p>
              <div className="my-4">
                <span className="text-4xl font-bold text-[#2D3748]">$149</span>
                <span className="text-[#718096]">/month</span>
              </div>
              <ul className="mb-6 space-y-2 text-sm">
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#27AE60]" /> Up to 300 AI-handled calls/month
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#27AE60]" /> 24/7 call answering
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#27AE60]" /> Appointment scheduling via Google Calendar
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#27AE60]" /> Emergency call triage
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#27AE60]" /> Call recordings & transcripts
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#27AE60]" /> Basic analytics dashboard
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#27AE60]" /> Email support
                </li>
                <li className="flex items-center gap-2 text-[#718096]">
                  <X className="h-4 w-4" /> SMS reminders
                </li>
                <li className="flex items-center gap-2 text-[#718096]">
                  <X className="h-4 w-4" /> Custom AI voice
                </li>
              </ul>
              <Link href="/signup">
                <Button variant="outline" className="w-full border-[#1B3A7C] text-[#1B3A7C] hover:bg-[#1B3A7C] hover:text-white">
                  Start 7-Day Trial
                </Button>
              </Link>
            </div>

            {/* Professional - Most Popular */}
            <div className="relative rounded-xl border-2 border-[#0099CC] bg-white p-6 shadow-lg">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[#0099CC] px-4 py-1 text-xs font-bold text-white">
                RECOMMENDED
              </div>
              <h3 className="text-lg font-bold text-[#1B3A7C]">Professional</h3>
              <p className="mt-1 text-sm text-[#718096]">For growing practices</p>
              <div className="my-4">
                <span className="text-4xl font-bold text-[#2D3748]">$199</span>
                <span className="text-[#718096]">/month</span>
              </div>
              <ul className="mb-6 space-y-2 text-sm">
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#27AE60]" /> Unlimited AI-handled calls
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#27AE60]" /> 24/7 call answering
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#27AE60]" /> Appointment scheduling via Google Calendar
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#27AE60]" /> Emergency call triage
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#27AE60]" /> Call recordings & transcripts
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#27AE60]" /> Advanced analytics dashboard
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#27AE60]" /> SMS appointment reminders
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#27AE60]" /> Custom AI voice & greeting
                </li>
                <li className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-[#27AE60]" /> Priority email support (4h response)
                </li>
              </ul>
              <Link href="/signup">
                <Button className="w-full bg-[#0099CC] hover:bg-[#0077A3] text-white">
                  Start 7-Day Trial
                </Button>
              </Link>
            </div>
          </div>

          {/* Note about integrations */}
          <p className="mt-8 text-center text-sm text-[#718096]">
            Need PMS integration (Dentrix, Open Dental)? <Link href="mailto:founder@dentsignal.me" className="text-[#0099CC] hover:underline">Contact us</Link> for custom enterprise solutions.
          </p>
        </div>
      </section>

      {/* Competitor Comparison */}
      <section className="bg-[#E8EBF0]/50 py-16">
        <div className="container mx-auto px-4">
          <h2 className="mb-8 text-center text-2xl font-bold text-[#1B3A7C]">Compare to Competitors</h2>
          <div className="mx-auto max-w-3xl rounded-xl border border-[#E8EBF0] bg-white p-6 shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#E8EBF0]">
                    <th className="py-3 text-left text-[#718096]">Feature</th>
                    <th className="py-3 text-center text-[#718096]">Weave</th>
                    <th className="py-3 text-center text-[#718096]">RevenueWell</th>
                    <th className="py-3 text-center font-bold text-[#0099CC]">DentSignal</th>
                  </tr>
                </thead>
                <tbody className="text-[#2D3748]">
                  <tr className="border-b border-[#E8EBF0]">
                    <td className="py-3">Inbound Call AI</td>
                    <td className="py-3 text-center">❌</td>
                    <td className="py-3 text-center">❌</td>
                    <td className="py-3 text-center text-[#27AE60]">✅</td>
                  </tr>
                  <tr className="border-b border-[#E8EBF0]">
                    <td className="py-3">Auto Appointment Booking</td>
                    <td className="py-3 text-center">❌</td>
                    <td className="py-3 text-center">❌</td>
                    <td className="py-3 text-center text-[#27AE60]">✅</td>
                  </tr>
                  <tr className="border-b border-[#E8EBF0]">
                    <td className="py-3">24/7 Coverage</td>
                    <td className="py-3 text-center text-[#27AE60]">✅</td>
                    <td className="py-3 text-center">❌</td>
                    <td className="py-3 text-center text-[#27AE60]">✅</td>
                  </tr>
                  <tr className="border-b border-[#E8EBF0]">
                    <td className="py-3">Setup Time</td>
                    <td className="py-3 text-center">3-6 weeks</td>
                    <td className="py-3 text-center">2-4 weeks</td>
                    <td className="py-3 text-center font-bold text-[#27AE60]">48 hours</td>
                  </tr>
                  <tr className="border-b border-[#E8EBF0]">
                    <td className="py-3">Contract</td>
                    <td className="py-3 text-center">12 months</td>
                    <td className="py-3 text-center">Flexible</td>
                    <td className="py-3 text-center font-bold text-[#27AE60]">Month-to-month</td>
                  </tr>
                  <tr>
                    <td className="py-3 font-bold">Price</td>
                    <td className="py-3 text-center">$300+/mo</td>
                    <td className="py-3 text-center">$175/mo</td>
                    <td className="py-3 text-center font-bold text-[#27AE60]">From $149/mo</td>
                  </tr>
                </tbody>
              </table>
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
    <details className="group rounded-xl border border-[#E8EBF0] bg-white p-4 transition-all hover:border-[#0099CC]/30">
      <summary className="flex cursor-pointer items-center justify-between font-medium text-[#1B3A7C]">
        {question}
        <ChevronDown className="h-4 w-4 text-[#0099CC] transition-transform group-open:rotate-180" />
      </summary>
      <p className="mt-3 text-sm text-[#718096]">{answer}</p>
    </details>
  )
}
