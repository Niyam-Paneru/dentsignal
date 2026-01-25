import { Check, X } from 'lucide-react'

const comparisons = [
  {
    old: "Your receptionist answers phones during lunch break",
    new: "Your AI answers calls 24/7, even at lunch",
    emoji: "🍽️",
  },
  {
    old: "Patient calls → voicemail → they call competitor instead",
    new: "Patient calls → AI books appointment instantly",
    emoji: "⚡",
  },
  {
    old: "Industry data: 20-35% of calls missed, thousands lost monthly",
    new: "95%+ of calls answered, revenue captured daily",
    emoji: "💰",
  },
  {
    old: "Hiring receptionist costs $65k/year + training + benefits",
    new: "AI costs $199/month, zero overhead",
    emoji: "🤖",
  },
  {
    old: "No-show rates average 15-30%, losing $400+ per patient",
    new: "SMS reminders can reduce no-shows by up to 50%",
    emoji: "📱",
  },
  {
    old: "Staffing shortage? Hope someone covers phones",
    new: "Staff shortage? Your AI doesn't call in sick",
    emoji: "✅",
  },
  {
    old: "Patient books during business hours only, limited slots",
    new: "Patient books 3am Tuesday. Appointment locked in.",
    emoji: "🔒",
  },
  {
    old: "Other AI receptionists charge $300-500/month + setup fees",
    new: "DentSignal: $199/month, no setup fees, all features included",
    emoji: "💎",
  },
]

export function WhyChooseSection() {
  return (
    <section className="bg-white py-16 border-b border-gray-100">
      <div className="container mx-auto px-4">
        <div className="mb-10 text-center">
          <h2 className="mb-3 text-3xl font-bold text-[#1B3A7C]">
            Why Choose DentSignal?
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            See what changes when you stop losing patients to missed calls
          </p>
        </div>

        <div className="mx-auto max-w-4xl space-y-4">
          {comparisons.map((item, index) => (
            <div
              key={index}
              className="grid md:grid-cols-2 gap-3 md:gap-6 p-4 rounded-xl bg-gray-50 hover:bg-gray-100/80 transition-colors"
            >
              {/* Old Way */}
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-red-100">
                    <X className="h-3.5 w-3.5 text-red-500" />
                  </div>
                </div>
                <p className="text-gray-500 text-sm md:text-base leading-relaxed">
                  {item.old}
                </p>
              </div>

              {/* New Way */}
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-green-100">
                    <Check className="h-3.5 w-3.5 text-green-600" />
                  </div>
                </div>
                <p className="text-gray-800 text-sm md:text-base leading-relaxed font-medium">
                  {item.new} <span className="ml-1">{item.emoji}</span>
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
