"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navLinks = [
  { href: "/", label: "Product" },
  { href: "/pricing", label: "Pricing" },
  { href: "/login", label: "Sign in" },
];

export function MarketingHeader({ className }: { className?: string }) {
  const pathname = usePathname();

  return (
    <header
      className={cn(
        "sticky top-0 z-40 border-b border-[#1B3A7C]/30 bg-[#1B3A7C]/95 text-white backdrop-blur-xl supports-[backdrop-filter]:bg-[#1B3A7C]/90",
        className
      )}
    >
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link href="/" className="group flex items-center gap-3">
          <Image
            src="/logo.svg"
            alt="DentSignal"
            width={160}
            height={40}
            priority
            className="transition-transform duration-150 group-hover:scale-[1.03]"
          />
          <div className="hidden flex-col leading-tight sm:flex">
            <span className="text-sm font-semibold text-white">DentSignal</span>
            <span className="text-xs text-slate-200">24/7 AI dental receptionist</span>
          </div>
        </Link>

        <nav className="flex items-center gap-1 sm:gap-2">
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
            className="hidden sm:inline-flex gap-2 bg-[#0099CC] px-4 text-sm font-semibold text-white shadow-md shadow-[#0099CC]/25 hover:bg-[#0077A3]"
          >
            <Link href="/signup">
              Start free trial
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button
            asChild
            variant="outline"
            className="sm:hidden border-white/60 text-white hover:bg-white hover:text-[#1B3A7C]"
          >
            <Link href="/signup">Start trial</Link>
          </Button>
        </nav>
      </div>
    </header>
  );
}
