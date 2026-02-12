import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "DentSignal - AI Dental Receptionist | 24/7 Call Answering",
  description: "25 missed new-patient calls = $21,250/month lost. DentSignal AI receptionist answers 24/7, books appointments automatically. $199/month flat rate. Live in 48 hours.",
  keywords: ["dental AI", "dental receptionist", "AI phone answering", "dental practice software", "missed calls dental", "appointment booking AI", "HIPAA-ready AI"],
  authors: [{ name: "DentSignal" }],
  creator: "DentSignal",
  publisher: "DentSignal",
  metadataBase: new URL("https://dentsignal.me"),
  alternates: {
    canonical: "https://dentsignal.me",
  },
  icons: {
    icon: [
      { url: "/icon.svg", type: "image/svg+xml" },
      { url: "/favicon.ico", sizes: "any" },
    ],
    shortcut: "/icon.svg",
    apple: "/icon.svg",
  },
  openGraph: {
    title: "DentSignal - AI Dental Receptionist | Never Miss a Call",
    description: "AI answers every call 24/7, books appointments automatically. Starting at $199/month. HIPAA-ready with BAA available. Live in 48 hours.",
    url: "https://dentsignal.me",
    siteName: "DentSignal",
    locale: "en_US",
    type: "website",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "DentSignal AI Dental Receptionist",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "DentSignal - AI Dental Receptionist",
    description: "25 missed new-patient calls = $21,250/month lost. AI answers 24/7, books appointments. $199/month flat rate.",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <meta name="theme-color" content="#1B3A7C" media="(prefers-color-scheme: light)" />
        <meta name="theme-color" content="#0f172a" media="(prefers-color-scheme: dark)" />
        <link rel="preconnect" href="https://supabase.co" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="icon" href="/icon.svg" type="image/svg+xml" />
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="apple-touch-icon" href="/icon.svg" />
        <link rel="manifest" href="/manifest.json" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {/* Skip to main content link for accessibility */}
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        {children}
        <Toaster />
      </body>
    </html>
  );
}
