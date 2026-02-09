/**
 * Site-wide configuration constants.
 * Single source of truth for business details used across marketing pages,
 * dashboard, legal pages, and email templates.
 * 
 * Update values here instead of hunting through 20+ files.
 */

export const SITE_CONFIG = {
  // Business info
  companyName: 'DentSignal',
  founderEmail: 'founder@dentsignal.me',
  supportEmail: 'founder@dentsignal.me',
  phoneNumber: '(904) 867-9643',
  phoneNumberE164: '+19048679643',
  domain: 'dentsignal.me',

  // Pricing
  monthlyPrice: 199,
  monthlyPriceFormatted: '$199',
  annualCost: 2388, // 199 * 12
  trialDays: 9,

  // ROI defaults
  missedCallsPerMonth: 25,
  patientValueYear1: 850,
  monthlyLoss: 21250, // 25 * 850

  // Demo video (replace with real YouTube ID when ready)
  demoVideoId: null as string | null,

  // Social / legal
  privacyUrl: '/privacy',
  termsUrl: '/terms',
} as const

export type SiteConfig = typeof SITE_CONFIG
