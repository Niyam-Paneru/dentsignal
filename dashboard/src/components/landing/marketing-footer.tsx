import Image from "next/image";
import Link from "next/link";

const quickLinks = [
  { label: "Product", href: "/" },
  { label: "Pricing", href: "/pricing" },
  { label: "Login", href: "/login" },
  { label: "Sign up", href: "/signup" },
];

const supportLinks = [
  { label: "Book a demo", href: "mailto:founder@dentsignal.me" },
  { label: "Support", href: "mailto:founder@dentsignal.me" },
  { label: "Privacy", href: "/privacy" },
  { label: "Terms", href: "/terms" },
];

export function MarketingFooter() {
  return (
    <footer className="border-t border-[#1B3A7C]/30 bg-[#1f2937] text-slate-100">
      <div className="container mx-auto px-4 py-12">
        <div className="grid gap-10 md:grid-cols-[1.1fr_1fr_1fr] md:items-start">
          <div className="space-y-4">
            <Link href="/" className="inline-flex items-center">
              <Image
                src="/logo.svg"
                alt="DentSignal"
                width={140}
                height={40}
                className="h-[36px] object-contain"
                style={{ width: 'auto' }}
              />
            </Link>
            <p className="text-sm text-slate-300">
              AI receptionist that answers every call, books appointments, and protects your patient experience 24/7.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-6 sm:grid-cols-2">
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Explore</p>
              <ul className="space-y-2 text-sm text-slate-200">
                {quickLinks.map((item) => (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className="transition-colors hover:text-white"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Contact</p>
              <ul className="space-y-2 text-sm text-slate-200">
                {supportLinks.map((item) => (
                  <li key={item.label}>
                    <Link
                      href={item.href}
                      className="transition-colors hover:text-white"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="space-y-3 rounded-2xl border border-white/10 bg-white/[0.04] p-4 text-sm text-slate-200">
            <p className="text-sm font-semibold text-white">Direct Founder Support</p>
            <p className="text-slate-300">
              Built by someone who gets it. Questions? I read every message and respond within 4 hours.
            </p>
            <div className="flex flex-col gap-2">
              <Link
                href="mailto:founder@dentsignal.me"
                className="inline-flex w-fit items-center gap-2 rounded-full bg-[#0099CC] px-4 py-2 text-xs font-semibold text-white transition hover:bg-[#0077A3]"
              >
                founder@dentsignal.me
              </Link>
              <Link
                href="tel:+19048679643"
                className="inline-flex w-fit items-center gap-2 rounded-full border border-white/20 px-4 py-2 text-xs font-semibold text-white transition hover:bg-white/10"
              >
                (904) 867-9643
              </Link>
            </div>
          </div>
        </div>

        <div className="mt-10 flex flex-col gap-4 text-sm text-slate-400 sm:flex-row sm:items-center sm:justify-between">
          <p>© 2025 DentSignal. Built for modern dental practices.</p>
          <div className="flex items-center gap-4">
            <Link href="mailto:founder@dentsignal.me" className="hover:text-white">
              founder@dentsignal.me
            </Link>
            <span className="hidden sm:inline">•</span>
            <Link href="tel:+19048679643" className="hover:text-white">
              (904) 867-9643
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
