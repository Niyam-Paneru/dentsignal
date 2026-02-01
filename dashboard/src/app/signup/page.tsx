'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loader2, Check, AlertCircle, ArrowLeft, ArrowRight, Phone, Building2, User } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'
import { Turnstile } from '@/components/turnstile'
import { MarketingHeader } from '@/components/landing/marketing-header'
import { MarketingFooter } from '@/components/landing/marketing-footer'

// Format phone number as (555) 123-4567
function formatPhoneNumber(value: string): string {
  const cleaned = value.replace(/\D/g, '')
  const match = cleaned.match(/^(\d{0,3})(\d{0,3})(\d{0,4})$/)
  if (!match) return value
  
  let formatted = ''
  if (match[1]) {
    formatted = `(${match[1]}`
    if (match[1].length === 3) {
      formatted += ') '
      if (match[2]) {
        formatted += match[2]
        if (match[2].length === 3) {
          formatted += '-'
          if (match[3]) {
            formatted += match[3]
          }
        }
      }
    }
  }
  return formatted
}

// Validate phone format (555) 123-4567
function isValidPhone(phone: string): boolean {
  return /^\(\d{3}\) \d{3}-\d{4}$/.test(phone)
}

// Strip phone formatting for storage
function stripPhoneFormatting(phone: string): string {
  return phone.replace(/\D/g, '')
}

// XSS Protection - sanitize input to prevent script injection
function containsXSS(value: string): boolean {
  const xssPatterns = [
    /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
    /<[^>]+on\w+\s*=/gi,  // onclick, onerror, onload, etc.
    /javascript:/gi,
    /<iframe/gi,
    /<object/gi,
    /<embed/gi,
    /<svg[^>]*onload/gi,
    /<img[^>]*onerror/gi,
    /&#x?[0-9a-f]+;/gi,  // HTML entities that could be used for XSS
  ]
  return xssPatterns.some(pattern => pattern.test(value))
}

// Sanitize name fields - only allow letters, spaces, hyphens, apostrophes
function isValidName(name: string): boolean {
  // Allow letters (including unicode), spaces, hyphens, apostrophes
  return /^[\p{L}\s'-]+$/u.test(name) && !containsXSS(name)
}

// Proper email validation
function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email) && !containsXSS(email)
}

// Sanitize business name - allow alphanumeric, spaces, common punctuation
function isValidBusinessName(name: string): boolean {
  return /^[\p{L}\p{N}\s\-&.,'"()]+$/u.test(name) && !containsXSS(name)
}

// Password validation helpers
function hasMinLength(password: string): boolean {
  return password.length >= 12
}

function hasSpecialChar(password: string): boolean {
  // Check for common special characters
  return /[!@#$%^&*()\-_=+{};:'",.<>/?\\|`~]/.test(password)
}

function hasNumber(password: string): boolean {
  return /[0-9]/.test(password)
}

function hasUpperAndLower(password: string): boolean {
  return /[a-z]/.test(password) && /[A-Z]/.test(password)
}

// Calculate password strength (0-4)
function getPasswordStrength(password: string): number {
  let score = 0
  if (password.length >= 8) score++
  if (password.length >= 12) score++
  if (hasSpecialChar(password)) score++
  if (hasNumber(password)) score++
  if (hasUpperAndLower(password)) score++
  return Math.min(4, score)
}

export default function SignupPage() {
  const [step, setStep] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [success, setSuccess] = useState<string | null>(null)
  
  // Step 1 fields
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  
  // Step 2 fields
  const [clinicName, setClinicName] = useState('')
  const [phone, setPhone] = useState('')
  
  // Rate limiting state
  const [attempts, setAttempts] = useState(0)
  const [lastAttemptTime, setLastAttemptTime] = useState<number | null>(null)
  const MAX_ATTEMPTS = 5
  const RATE_LIMIT_WINDOW = 15 * 60 * 1000 // 15 minutes
  
  // Honeypot field for catching bots
  const [honeypot, setHoneypot] = useState('')
  
  // Captcha
  const [captchaToken, setCaptchaToken] = useState<string | null>(null)
  const [captchaError, setCaptchaError] = useState(false)
  
  const router = useRouter()
  const supabase = createClient()
  
  // Handle CAPTCHA errors - SECURITY: block signup to prevent automated attacks
  const handleCaptchaError = () => {
    setCaptchaError(true)
    console.error('[Signup] CAPTCHA failed to load')
    setError('Security verification failed. Please refresh the page and try again.')
  }

  // Check rate limiting
  const isRateLimited = () => {
    if (lastAttemptTime && attempts >= MAX_ATTEMPTS) {
      const timeSinceLastAttempt = Date.now() - lastAttemptTime
      if (timeSinceLastAttempt < RATE_LIMIT_WINDOW) {
        const minutesRemaining = Math.ceil((RATE_LIMIT_WINDOW - timeSinceLastAttempt) / 60000)
        setError(`Too many signup attempts. Please try again in ${minutesRemaining} minutes.`)
        return true
      } else {
        // Reset rate limit
        setAttempts(0)
        setLastAttemptTime(null)
      }
    }
    return false
  }

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhoneNumber(e.target.value)
    if (formatted.length <= 14) {
      setPhone(formatted)
    }
  }

  const validateStep1 = () => {
    if (!firstName.trim()) {
      setError('Please enter your first name')
      return false
    }
    if (!isValidName(firstName)) {
      setError('First name contains invalid characters')
      return false
    }
    if (!lastName.trim()) {
      setError('Please enter your last name')
      return false
    }
    if (!isValidName(lastName)) {
      setError('Last name contains invalid characters')
      return false
    }
    if (!email || !isValidEmail(email)) {
      setError('Please enter a valid email address')
      return false
    }
    if (!password || !hasMinLength(password)) {
      setError('Password must be at least 12 characters')
      return false
    }
    if (!hasSpecialChar(password)) {
      setError('Password must include at least one special character (!@#$%^&* etc.)')
      return false
    }
    if (!hasNumber(password)) {
      setError('Password must include at least one number')
      return false
    }
    if (!hasUpperAndLower(password)) {
      setError('Password must include both uppercase and lowercase letters')
      return false
    }
    return true
  }

  const handleNextStep = () => {
    setError(null)
    if (validateStep1()) {
      setStep(2)
    }
  }

  const handlePrevStep = () => {
    setError(null)
    setStep(1)
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    setSuccess(null)
    
    // Honeypot check - if filled, it's a bot
    if (honeypot) {
      console.log('Honeypot triggered - bot detected')
      setIsLoading(false)
      // Silently fail for bots, don't give them feedback
      return
    }
    
    // Rate limiting check
    if (isRateLimited()) {
      setIsLoading(false)
      return
    }
    
    // SECURITY: Enforce CAPTCHA verification
    if (!captchaToken && !captchaError) {
      setError('Please complete the security verification.')
      setIsLoading(false)
      return
    }
    
    // Track attempt
    setAttempts(prev => prev + 1)
    setLastAttemptTime(Date.now())
    
    // Validation for step 2
    if (!clinicName || clinicName.length < 3) {
      setError('Clinic name must be at least 3 characters')
      setIsLoading(false)
      return
    }
    
    if (!isValidBusinessName(clinicName)) {
      setError('Clinic name contains invalid characters')
      setIsLoading(false)
      return
    }
    
    if (!isValidPhone(phone)) {
      setError('Please enter a valid phone number: (555) 123-4567')
      setIsLoading(false)
      return
    }
    
    // Sign up user
    const { data: authData, error: signUpError } = await supabase.auth.signUp({
      email,
      password,
      options: {
        captchaToken: captchaToken || undefined,
        data: {
          first_name: firstName,
          last_name: lastName,
          clinic_name: clinicName,
        }
      }
    })
    
    if (signUpError) {
      // Handle captcha-related errors more gracefully
      if (signUpError.message.toLowerCase().includes('captcha') || captchaError) {
        setError('Sign up failed. Please try again.')
      } else {
        setError(signUpError.message)
      }
      setIsLoading(false)
      return
    }
    
    // Create clinic record
    if (authData.user) {
      const { error: clinicError } = await supabase
        .from('dental_clinics')
        .insert({
          owner_id: authData.user.id,
          name: clinicName,
          owner_name: `${firstName} ${lastName}`,
          phone: stripPhoneFormatting(phone),
        })
      
      if (clinicError) {
        console.error('Failed to create clinic:', clinicError)
      }
      
      // Also create default clinic settings
      const { data: newClinic } = await supabase
        .from('dental_clinics')
        .select('id')
        .eq('owner_id', authData.user.id)
        .single()
      
      if (newClinic) {
        await supabase
          .from('dental_clinic_settings')
          .insert({
            clinic_id: newClinic.id,
            agent_name: 'Sarah',
            agent_voice: 'aura-asteria-en',
            greeting_template: `Thank you for calling ${clinicName}. This is Sarah, how may I help you today?`,
          })
      }
      
      // Send Slack notification (fire and forget - don't block signup)
      fetch('/api/notify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'signup',
          data: {
            email,
            name: `${firstName} ${lastName}`,
            clinic: clinicName,
          }
        })
      }).catch(() => {}) // Silently ignore errors
    }
    
    router.push('/dashboard')
    router.refresh()
  }

  return (
    <div className="flex min-h-screen flex-col bg-[#F8F9FA]">
      <MarketingHeader />

      <main className="container mx-auto flex-1 px-4 py-12">
        <div className="mx-auto max-w-md">
          {/* Progress Steps */}
          <div className="mb-8">
            <div className="flex items-center justify-center gap-4">
              <div className="flex items-center gap-2">
                <div className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold ${
                  step >= 1 ? 'bg-[#0099CC] text-white' : 'bg-[#E8EBF0] text-[#718096]'
                }`}>
                  {step > 1 ? <Check className="h-4 w-4" /> : '1'}
                </div>
                <span className={`text-sm font-medium ${step >= 1 ? 'text-[#1B3A7C]' : 'text-[#718096]'}`}>
                  Account
                </span>
              </div>
              <div className={`h-px w-12 ${step >= 2 ? 'bg-[#0099CC]' : 'bg-[#E8EBF0]'}`} />
              <div className="flex items-center gap-2">
                <div className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold ${
                  step >= 2 ? 'bg-[#0099CC] text-white' : 'bg-[#E8EBF0] text-[#718096]'
                }`}>
                  2
                </div>
                <span className={`text-sm font-medium ${step >= 2 ? 'text-[#1B3A7C]' : 'text-[#718096]'}`}>
                  Clinic
                </span>
              </div>
            </div>
          </div>

          {/* Card */}
          <div className="rounded-2xl border border-[#E8EBF0] bg-white p-8 shadow-sm">
            {/* Back button */}
            {step === 2 && (
              <button 
                type="button"
                onClick={handlePrevStep}
                className="mb-6 inline-flex items-center gap-1 text-sm text-[#718096] hover:text-[#1B3A7C] transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </button>
            )}

            {/* Title */}
            <div className="mb-6 text-center">
              <div className={`mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full ${
                step === 1 ? 'bg-[#0099CC]/10' : 'bg-[#22C55E]/10'
              }`}>
                {step === 1 ? (
                  <User className="h-6 w-6 text-[#0099CC]" />
                ) : (
                  <Building2 className="h-6 w-6 text-[#22C55E]" />
                )}
              </div>
              <h1 className="text-2xl font-bold text-[#1B3A7C]">
                {step === 1 ? 'Create your account' : 'Tell us about your practice'}
              </h1>
              <p className="mt-2 text-sm text-[#718096]">
                {step === 1 ? 'Start your 7-day free trial' : 'We\'ll customize your AI receptionist'}
              </p>
            </div>

            {/* Error */}
            {error && (
              <div className="mb-6 flex items-center gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-600" role="alert" aria-live="polite">
                <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
                {error}
              </div>
            )}

            {step === 1 ? (
              /* Step 1: Account Information */
              <div className="space-y-5">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="firstName" className="text-[#2D3748]">First name</Label>
                    <Input 
                      id="firstName" 
                      placeholder="John" 
                      value={firstName}
                      maxLength={50}
                      onChange={(e) => {
                        setFirstName(e.target.value)
                        // Clear error when user types valid name
                        if (error && error.includes('first name') && isValidName(e.target.value)) {
                          setError(null)
                        }
                      }}
                      className={`h-11 border-[#E8EBF0] focus:border-[#0099CC] focus:ring-[#0099CC] ${
                        firstName && isValidName(firstName) ? 'border-green-500 focus:border-green-500 focus:ring-green-500' : ''
                      }`}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName" className="text-[#2D3748]">Last name</Label>
                    <Input 
                      id="lastName" 
                      placeholder="Smith" 
                      value={lastName}
                      maxLength={50}
                      onChange={(e) => {
                        setLastName(e.target.value)
                        // Clear error when user types valid name
                        if (error && error.includes('last name') && isValidName(e.target.value)) {
                          setError(null)
                        }
                      }}
                      className={`h-11 border-[#E8EBF0] focus:border-[#0099CC] focus:ring-[#0099CC] ${
                        lastName && isValidName(lastName) ? 'border-green-500 focus:border-green-500 focus:ring-green-500' : ''
                      }`}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-[#2D3748]">Work email</Label>
                  <div className="relative">
                    <Input 
                      id="email" 
                      type="email" 
                      placeholder="you@clinic.com" 
                      value={email}
                      maxLength={100}
                      onChange={(e) => {
                        setEmail(e.target.value)
                        // Clear error when user types valid email
                        if (error && error.includes('email') && isValidEmail(e.target.value)) {
                          setError(null)
                        }
                      }}
                      autoComplete="email"
                      className={`h-11 pr-10 border-[#E8EBF0] focus:border-[#0099CC] focus:ring-[#0099CC] ${
                        email && isValidEmail(email) 
                          ? 'border-green-500 focus:border-green-500 focus:ring-green-500' 
                          : email && !isValidEmail(email) 
                            ? 'border-red-400 focus:border-red-400 focus:ring-red-400' 
                            : ''
                      }`}
                    />
                    {email && (
                      <div className="absolute right-3 top-1/2 -translate-y-1/2">
                        {isValidEmail(email) ? (
                          <Check className="h-4 w-4 text-green-500" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-red-400" />
                        )}
                      </div>
                    )}
                  </div>
                  {email && !isValidEmail(email) && (
                    <p className="text-xs text-red-500">Please enter a valid email address</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password" className="text-[#2D3748]">Password</Label>
                  <Input 
                    id="password" 
                    type="password" 
                    placeholder="Create a strong password" 
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value)
                      // Clear error when user starts typing valid password
                      if (error && error.includes('Password')) {
                        setError(null)
                      }
                    }}
                    autoComplete="new-password"
                    className={`h-11 border-[#E8EBF0] focus:border-[#0099CC] focus:ring-[#0099CC] ${
                      password && hasMinLength(password) && hasSpecialChar(password) && hasNumber(password) && hasUpperAndLower(password)
                        ? 'border-green-500 focus:border-green-500 focus:ring-green-500'
                        : ''
                    }`}
                  />
                  
                  {/* Password Strength Meter */}
                  {password && (
                    <div className="pt-2">
                      <div className="flex gap-1 mb-2">
                        {[1, 2, 3, 4].map((level) => (
                          <div
                            key={level}
                            className={`h-1.5 flex-1 rounded-full transition-colors ${
                              getPasswordStrength(password) >= level
                                ? getPasswordStrength(password) <= 1
                                  ? 'bg-red-500'
                                  : getPasswordStrength(password) <= 2
                                  ? 'bg-orange-500'
                                  : getPasswordStrength(password) <= 3
                                  ? 'bg-yellow-500'
                                  : 'bg-green-500'
                                : 'bg-gray-200'
                            }`}
                          />
                        ))}
                      </div>
                      <p className={`text-xs font-medium ${
                        getPasswordStrength(password) <= 1 ? 'text-red-600' :
                        getPasswordStrength(password) <= 2 ? 'text-orange-600' :
                        getPasswordStrength(password) <= 3 ? 'text-yellow-600' :
                        'text-green-600'
                      }`}>
                        {getPasswordStrength(password) <= 1 ? 'Weak' :
                         getPasswordStrength(password) <= 2 ? 'Fair' :
                         getPasswordStrength(password) <= 3 ? 'Good' :
                         'Strong'}
                      </p>
                    </div>
                  )}

                  {/* Password Requirements with Checkmarks */}
                  <div className="space-y-1.5 pt-2 rounded-lg bg-slate-50 p-3">
                    <p className="text-xs font-medium text-slate-600 mb-2">Password requirements:</p>
                    <div className="flex items-center gap-2">
                      {hasMinLength(password) ? (
                        <Check className="h-4 w-4 text-green-500" />
                      ) : (
                        <div className="h-4 w-4 rounded-full border-2 border-gray-300" />
                      )}
                      <p className={`text-xs ${hasMinLength(password) ? 'text-green-600 font-medium' : 'text-[#718096]'}`}>
                        At least 12 characters
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {hasSpecialChar(password) ? (
                        <Check className="h-4 w-4 text-green-500" />
                      ) : (
                        <div className="h-4 w-4 rounded-full border-2 border-gray-300" />
                      )}
                      <p className={`text-xs ${hasSpecialChar(password) ? 'text-green-600 font-medium' : 'text-[#718096]'}`}>
                        Include a special character (!@#$%^&* etc.)
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {hasNumber(password) ? (
                        <Check className="h-4 w-4 text-green-500" />
                      ) : (
                        <div className="h-4 w-4 rounded-full border-2 border-gray-300" />
                      )}
                      <p className={`text-xs ${hasNumber(password) ? 'text-green-600 font-medium' : 'text-[#718096]'}`}>
                        Include a number
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {hasUpperAndLower(password) ? (
                        <Check className="h-4 w-4 text-green-500" />
                      ) : (
                        <div className="h-4 w-4 rounded-full border-2 border-gray-300" />
                      )}
                      <p className={`text-xs ${hasUpperAndLower(password) ? 'text-green-600 font-medium' : 'text-[#718096]'}`}>
                        Include uppercase and lowercase letters
                      </p>
                    </div>
                  </div>
                </div>

                <Button 
                  type="button" 
                  onClick={handleNextStep}
                  disabled={!hasMinLength(password) || !hasSpecialChar(password) || !hasNumber(password) || !hasUpperAndLower(password)}
                  className="h-11 w-full bg-[#0099CC] hover:bg-[#0077A3] text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Continue
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>

                <p className="text-center text-xs text-[#718096]">
                  By signing up, you agree to our{' '}
                  <Link href="/terms" className="text-[#0099CC] hover:underline">Terms</Link>
                  {' '}and{' '}
                  <Link href="/privacy" className="text-[#0099CC] hover:underline">Privacy Policy</Link>
                </p>
              </div>
            ) : (
              /* Step 2: Clinic Information */
              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="clinicName" className="text-[#2D3748]">Practice name</Label>
                  <Input 
                    id="clinicName" 
                    placeholder="Sunshine Dental Care" 
                    value={clinicName}
                    maxLength={100}
                    onChange={(e) => setClinicName(e.target.value)}
                    className={`h-11 border-[#E8EBF0] focus:border-[#0099CC] focus:ring-[#0099CC] ${
                      clinicName.length >= 3 && isValidBusinessName(clinicName) ? 'border-green-500 focus:border-green-500 focus:ring-green-500' : ''
                    }`}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone" className="text-[#2D3748]">Practice phone number</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#718096]" />
                    <Input 
                      id="phone" 
                      type="tel" 
                      placeholder="(555) 123-4567"
                      value={phone}
                      onChange={handlePhoneChange}
                      className="h-11 pl-10 border-[#E8EBF0] focus:border-[#0099CC] focus:ring-[#0099CC]"
                    />
                  </div>
                  <p className="text-xs text-[#718096]">We&apos;ll use this to set up call forwarding</p>
                </div>

                {/* What happens next */}
                <div className="rounded-xl bg-[#F8F9FA] p-4">
                  <p className="mb-3 text-sm font-medium text-[#1B3A7C]">What happens next:</p>
                  <ul className="space-y-2 text-sm text-[#718096]">
                    <li className="flex items-start gap-2">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-[#22C55E]" />
                      <span>Your AI receptionist will be ready in minutes</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-[#22C55E]" />
                      <span>Test it with a call before going live</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-[#22C55E]" />
                      <span>7 days free, cancel anytime</span>
                    </li>
                  </ul>
                </div>

                {/* Honeypot field - hidden from users, catches bots */}
                <div className="absolute left-[-9999px] opacity-0 h-0 overflow-hidden" aria-hidden="true">
                  <label htmlFor="website">Website (leave blank)</label>
                  <input
                    type="text"
                    id="website"
                    name="website"
                    value={honeypot}
                    onChange={(e) => setHoneypot(e.target.value)}
                    tabIndex={-1}
                    autoComplete="off"
                  />
                </div>

                {/* Invisible Turnstile CAPTCHA - optional, won't block signup */}
                <Turnstile 
                  onVerify={setCaptchaToken}
                  onError={handleCaptchaError}
                  onExpire={() => setCaptchaToken(null)}
                />

                <Button 
                  type="submit" 
                  disabled={isLoading}
                  className="h-11 w-full bg-[#0099CC] hover:bg-[#0077A3] text-white font-medium"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Setting up your account...
                    </>
                  ) : (
                    'Start Free Trial'
                  )}
                </Button>
              </form>
            )}
          </div>

          {/* Trust badges */}
          <div className="mt-6 flex items-center justify-center gap-6 text-xs text-[#718096]">
            <span className="flex items-center gap-1">
              <Check className="h-3 w-3 text-[#22C55E]" />
              No credit card required
            </span>
            <span className="flex items-center gap-1">
              <Check className="h-3 w-3 text-[#22C55E]" />
              HIPAA ready
            </span>
          </div>
        </div>
      </main>

      <MarketingFooter />
    </div>
  )
}
