import { Check, X, Clock, Zap, ShieldCheck, LucideIcon } from 'lucide-react'

interface ComparisonItem {
  old: string
  new: string
  icon: LucideIcon
  highlight: string
}

// Reduced to 3 most impactful comparisons (per UX audit)
// Messaging: receptionist-friendly (backup, not replacement)
const comparisons: ComparisonItem[] = [
  {
    old: "Patient calls → voicemail → they call competitor instead",
    new: "Patient calls → AI books appointment instantly",
    icon: Zap,
    highlight: "Capture every lead",
  },
  {
    old: "After-hours calls go to voicemail and get forgotten",
    new: "24/7 backup catches nights, weekends, and lunch rushes",
    icon: Clock,
    highlight: "Always covered",
  },
  {
    old: "Sensitive patient data handled by random call centers",
    new: "HIPAA-compliant AI with encrypted, secure handling",
    icon: ShieldCheck,
    highlight: "Enterprise security",
  },
]

export function WhyChooseSection() {
  return (
    <section className="bg-gradient-to-b from-gray-50 to-white py-12 border-b border-gray-100">
      <div className="container mx-auto px-4">
        <div className="mb-8 text-center">
          <h2 className="mb-2 text-2xl font-bold text-[#1B3A7C]">
            The DentSignal Difference
          </h2>
          <p className="text-gray-600">
            Three changes that transform your practice
          </p>
        </div>

        <div className="mx-auto max-w-4xl grid md:grid-cols-3 gap-6">
          {comparisons.map((item, index) => (
            <div
              key={index}
              className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md hover:border-[#0099CC]/30 transition-all"
            >
              {/* Highlight Badge */}
              <div className="inline-flex items-center gap-1.5 bg-[#22C55E]/10 text-[#16a34a] text-xs font-semibold rounded-full px-3 py-1 mb-4">
                <item.icon className="h-3.5 w-3.5" />
                {item.highlight}
              </div>
              
              {/* Old Way */}
              <div className="flex items-start gap-2 mb-3">
                <div className="flex-shrink-0 mt-0.5">
                  <X className="h-4 w-4 text-error" />
                </div>
                <p className="text-gray-400 text-sm line-through">
                  {item.old}
                </p>
              </div>

              {/* New Way */}
              <div className="flex items-start gap-2">
                <div className="flex-shrink-0 mt-0.5">
                  <Check className="h-4 w-4 text-success" />
                </div>
                <p className="text-gray-800 text-sm font-medium">
                  {item.new}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
