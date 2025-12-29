"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowRight, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useState } from "react";

const navLinks = [
  { href: "/", label: "Product" },
  { href: "/pricing", label: "Pricing" },
  { href: "/login", label: "Sign in" },
];

export function MarketingHeader({ className }: { className?: string }) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header
      className={cn(
        "sticky top-0 z-40 border-b border-[#1B3A7C]/30 bg-[#1B3A7C]/95 text-white backdrop-blur-xl supports-[backdrop-filter]:bg-[#1B3A7C]/90",
        className
      )}
    >
      <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-6">
        {/* Logo - Clean, professional, responsive */}
        <Link href="/" className="group flex items-center gap-3">
          <Image
            src="/logo.svg"
            alt="DentSignal"
            width={120}
            height={40}
            priority
            className="h-[40px] w-auto max-w-full object-contain transition-transform duration-150 group-hover:scale-[1.02]"
          />
          {/* Hide text on mobile, show on md+ */}
          <span className="hidden text-lg font-semibold text-white md:block">
            DentSignal
          </span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden items-center gap-1 sm:flex sm:gap-2">
          {navLinks.map((item) => {
            const isActive =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-full px-3 py-2 text-sm font-semibold transition-colors",
                  isActive
                    ? "bg-white/15 text-white shadow-[0_4px_12px_rgba(0,0,0,0.08)]"
                    : "text-slate-100 hover:bg-white/10 hover:text-white"
                )}
                aria-current={isActive ? "page" : undefined}
              >
                {item.label}
              </Link>
            );
          })}
          <Button
            asChild
            className="ml-2 gap-2 bg-[#0099CC] px-4 text-sm font-semibold text-white shadow-md shadow-[#0099CC]/25 hover:bg-[#0077A3]"
          >
            <Link href="/signup">
              Start free trial
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </nav>

        {/* Mobile Menu Button */}
        <div className="flex items-center gap-2 sm:hidden">
          <Button
            asChild
            size="sm"
            className="gap-1 bg-[#0099CC] px-3 text-xs font-semibold text-white hover:bg-[#0077A3]"
          >
            <Link href="/signup">Start trial</Link>
          </Button>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="rounded-lg p-2 text-white hover:bg-white/10"
            aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="border-t border-white/10 bg-[#1B3A7C] px-4 py-4 sm:hidden">
          <nav className="flex flex-col gap-2">
            {navLinks.map((item) => {
              const isActive =
                item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "rounded-lg px-4 py-3 text-sm font-semibold transition-colors",
                    isActive
                      ? "bg-white/15 text-white"
                      : "text-slate-100 hover:bg-white/10"
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      )}
    </header>
  );
}
