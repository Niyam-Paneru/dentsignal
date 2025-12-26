import { MarketingHeader } from "@/components/landing/marketing-header";
import { MarketingFooter } from "@/components/landing/marketing-footer";

const sections = [
  {
    title: "Service Overview",
    items: [
      "DentSignal provides an AI-assisted voice and messaging receptionist for dental practices, including call answering, appointment booking, reminders, and related analytics.",
      "The service is intended for business use by dental practices and their authorized staff; patients should contact their provider directly for care questions.",
    ],
  },
  {
    title: "Accounts & Eligibility",
    items: [
      "You must be at least 18 years old and authorized to act on behalf of the dental practice to create an account.",
      "You are responsible for maintaining the confidentiality of login credentials and for all activity under your account.",
    ],
  },
  {
    title: "Acceptable Use",
    items: [
      "Do not use the service to send unlawful, harassing, or misleading content, or to collect or store sensitive data beyond what is necessary for patient scheduling and communications.",
      "You agree not to probe, scan, or test the vulnerability of the platform, or attempt to bypass security or rate limits.",
    ],
  },
  {
    title: "Data & HIPAA",
    items: [
      "Calls, transcripts, and related data may include protected health information (PHI). We implement access controls, encryption in transit and at rest, and vendor BAAs where applicable.",
      "You are responsible for obtaining any required patient consents for call recording and for configuring your account to align with your practice policies.",
      "We do not use customer data to train models for other clients. Data retention defaults to operational needs; request deletion to remove stored data where legally permissible.",
    ],
  },
  {
    title: "Reliability & Telephony",
    items: [
      "Telephony quality may depend on carrier networks (e.g., Twilio) and third-party AI vendors. We aim for high availability but do not guarantee uninterrupted service.",
      "You remain responsible for maintaining a working practice phone number and forwarding configuration to route calls to DentSignal.",
    ],
  },
  {
    title: "Fees & Billing",
    items: [
      "Subscription fees are billed in advance per your selected plan; usage-based telephony or SMS fees may apply where specified.",
      "Late or failed payments may result in suspension. Taxes are additional where applicable.",
    ],
  },
  {
    title: "Disclaimers & Liability",
    items: [
      "The service is provided on an \"as is\" and \"as available\" basis without warranties of any kind, to the fullest extent permitted by law.",
      "DentSignal is not a medical provider and does not offer medical advice. Clinical decisions remain with licensed professionals.",
      "Liability is limited to the amount paid to DentSignal in the prior three (3) months, to the extent permitted by law.",
    ],
  },
  {
    title: "Termination",
    items: [
      "You may cancel at any time; fees already paid are non-refundable unless required by law.",
      "We may suspend or terminate accounts for violation of these terms, abuse, or non-payment.",
    ],
  },
  {
    title: "Changes",
    items: [
      "We may update these Terms to reflect operational, legal, or regulatory changes. Material updates will be communicated via the dashboard or email.",
    ],
  },
  {
    title: "Contact",
    items: [
      "Questions about these Terms: niyampaneru79@gmail.com or (904) 867-9643.",
    ],
  },
];

export default function TermsPage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#F8F9FA] text-slate-900">
      <MarketingHeader />
      <main className="container mx-auto flex-1 px-4 py-12">
        <div className="mx-auto max-w-4xl rounded-2xl bg-white p-8 shadow-sm">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Legal</p>
          <h1 className="mb-4 text-3xl font-bold text-slate-900">Terms of Service</h1>
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
