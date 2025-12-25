import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

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
  description: "Stop losing $21,000/month to missed calls. DentSignal AI receptionist answers 24/7, books appointments automatically. 60% cheaper than Weave. Live in 48 hours.",
  keywords: ["dental AI", "dental receptionist", "AI phone answering", "dental practice software", "missed calls dental", "appointment booking AI", "HIPAA compliant AI"],
  authors: [{ name: "DentSignal" }],
  creator: "DentSignal",
  publisher: "DentSignal",
  metadataBase: new URL("https://dentsignal.me"),
  alternates: {
    canonical: "https://dentsignal.me",
  },
  openGraph: {
    title: "DentSignal - AI Dental Receptionist | Never Miss a Call",
    description: "AI answers every call 24/7, books appointments automatically. 60% cheaper than Weave. HIPAA compliant. Live in 48 hours.",
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
    description: "Stop losing $21,000/month to missed calls. AI answers 24/7, books appointments. 60% cheaper than Weave.",
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
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon.png", type: "image/png" },
    ],
    apple: "/apple-touch-icon.png",
  },
  verification: {
    google: "your-google-verification-code",
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
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="icon" href="/favicon.png" type="image/png" />
        <link rel="apple-touch-icon" href="/favicon.png" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
