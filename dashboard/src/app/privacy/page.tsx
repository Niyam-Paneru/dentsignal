import { MarketingHeader } from "@/components/landing/marketing-header";
import { MarketingFooter } from "@/components/landing/marketing-footer";

const sections = [
  {
    title: "What We Collect",
    items: [
      "Account data (name, email, clinic details) to create and manage your workspace.",
      "Telephony data (call metadata, recordings/transcripts when enabled) to deliver call handling and analytics.",
      "Usage and device data (logs, diagnostics, IP, browser) to secure and improve the service.",
    ],
  },
  {
    title: "How We Use Data",
    items: [
      "Provide AI call answering, scheduling, and messaging services for your clinic.",
      "Maintain security, prevent abuse, and troubleshoot reliability issues.",
      "Improve product quality (e.g., model prompts, detection) without using your PHI to train shared models.",
    ],
  },
  {
    title: "Sharing & Vendors",
    items: [
      "Telephony and AI vendors (e.g., Twilio, Deepgram, Supabase) under Business Associate Agreements where applicable.",
      "Analytics and error monitoring providers limited to operational data, not PHI where feasible.",
      "We do not sell or rent your data to third parties.",
    ],
  },
  {
    title: "HIPAA & Security",
    items: [
      "Encryption in transit and at rest for call media, transcripts, and account data.",
      "Role-based access controls; restrict PHI access to authorized clinic staff.",
      "Configurable retention; request deletion of recordings/transcripts where legally permissible.",
    ],
  },
  {
    title: "Retention",
    items: [
      "Account data is retained while your subscription is active and as required by law.",
      "Call recordings/transcripts are retained only as needed for service delivery and can be deleted upon request, subject to legal obligations.",
    ],
  },
  {
    title: "Your Choices",
    items: [
      "Request access, correction, or deletion of your data (subject to legal/contractual limits).",
      "Disable call recording or transcript storage in your account if you prefer to minimize retained PHI.",
      "Opt out of non-essential communications by using unsubscribe links or contacting support.",
    ],
  },
  {
    title: "Children",
    items: [
      "The service is intended for use by dental practices and their staff, not by children under 13.",
    ],
  },
  {
    title: "International Transfers",
    items: [
      "Data may be processed in the United States. By using the service, you consent to cross-border processing as applicable.",
    ],
  },
  {
    title: "Changes",
    items: [
      "We may update this Privacy Notice to reflect operational, legal, or regulatory changes. Material updates will be shared via the dashboard or email.",
    ],
  },
  {
    title: "Contact",
    items: [
      "Privacy questions or requests: founder@dentsignal.me or (904) 867-9643.",
    ],
  },
];

export default function PrivacyPage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#F8F9FA] text-slate-900">
      <MarketingHeader />
      <main className="container mx-auto flex-1 px-4 py-12">
        <div className="mx-auto max-w-4xl rounded-2xl bg-white p-8 shadow-sm">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Legal</p>
          <h1 className="mb-4 text-3xl font-bold text-slate-900">Privacy Notice</h1>
          <p className="mb-8 text-slate-600">Effective date: December 26, 2025</p>

          <div className="space-y-6">
            {sections.map((section) => (
              <section key={section.title} className="space-y-2">
                <h2 className="text-lg font-semibold text-slate-900">{section.title}</h2>
                <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                  {section.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
        </div>
      </main>
      <MarketingFooter />
    </div>
  );
}
