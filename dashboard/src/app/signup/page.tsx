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

// Password validation helpers
function hasMinLength(password: string): boolean {
  return password.length >= 8
}

function hasSpecialChar(password: string): boolean {
  return /[!@#$%^&*(),.?":{}|<>\[\]\\;'`~_+=\-\/]/.test(password)
}

export default function SignupPage() {
  const [step, setStep] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Step 1 fields
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  
  // Step 2 fields
  const [clinicName, setClinicName] = useState('')
  const [phone, setPhone] = useState('')
  
  // Captcha
  const [captchaToken, setCaptchaToken] = useState<string | null>(null)
  
  const router = useRouter()
  const supabase = createClient()

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
    if (!lastName.trim()) {
      setError('Please enter your last name')
      return false
    }
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address')
      return false
    }
    if (!password || !hasMinLength(password)) {
      setError('Password must be at least 8 characters')
      return false
    }
    if (!hasSpecialChar(password)) {
      setError('Password must include at least one special character (!@#$%^&* etc.)')
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
    
    // Validation for step 2
    if (!clinicName || clinicName.length < 3) {
      setError('Clinic name must be at least 3 characters')
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
      setError(signUpError.message)
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
                step === 1 ? 'bg-[#0099CC]/10' : 'bg-[#27AE60]/10'
              }`}>
                {step === 1 ? (
                  <User className="h-6 w-6 text-[#0099CC]" />
                ) : (
                  <Building2 className="h-6 w-6 text-[#27AE60]" />
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
              <div className="mb-6 flex items-center gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-600">
                <AlertCircle className="h-4 w-4 shrink-0" />
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
                      onChange={(e) => setFirstName(e.target.value)}
                      className="h-11 border-[#E8EBF0] focus:border-[#0099CC] focus:ring-[#0099CC]"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName" className="text-[#2D3748]">Last name</Label>
                    <Input 
                      id="lastName" 
                      placeholder="Smith" 
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      className="h-11 border-[#E8EBF0] focus:border-[#0099CC] focus:ring-[#0099CC]"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-[#2D3748]">Work email</Label>
                  <Input 
                    id="email" 
                    type="email" 
                    placeholder="you@clinic.com" 
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email"
                    className="h-11 border-[#E8EBF0] focus:border-[#0099CC] focus:ring-[#0099CC]"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password" className="text-[#2D3748]">Password</Label>
                  <Input 
                    id="password" 
                    type="password" 
                    placeholder="Create a password" 
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="new-password"
                    className="h-11 border-[#E8EBF0] focus:border-[#0099CC] focus:ring-[#0099CC]"
                  />
                  <div className="space-y-1 pt-1">
                    <div className="flex items-center gap-2">
                      <div className={`h-1.5 w-1.5 rounded-full ${hasMinLength(password) ? 'bg-green-500' : 'bg-gray-300'}`} />
                      <p className={`text-xs ${hasMinLength(password) ? 'text-green-600' : 'text-[#718096]'}`}>
                        At least 8 characters
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className={`h-1.5 w-1.5 rounded-full ${hasSpecialChar(password) ? 'bg-green-500' : 'bg-gray-300'}`} />
                      <p className={`text-xs ${hasSpecialChar(password) ? 'text-green-600' : 'text-[#718096]'}`}>
                        Include a special character (!@#$%^&* etc.)
                      </p>
                    </div>
                  </div>
                </div>

                <Button 
                  type="button" 
                  onClick={handleNextStep}
                  className="h-11 w-full bg-[#0099CC] hover:bg-[#0077A3] text-white font-medium"
                >
                  Continue
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>

                <p className="text-center text-xs text-[#718096]">
                  By signing up, you agree to our{' '}
                  <Link href="#" className="text-[#0099CC] hover:underline">Terms</Link>
                  {' '}and{' '}
                  <Link href="#" className="text-[#0099CC] hover:underline">Privacy Policy</Link>
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
                    onChange={(e) => setClinicName(e.target.value)}
                    className="h-11 border-[#E8EBF0] focus:border-[#0099CC] focus:ring-[#0099CC]"
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
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-[#27AE60]" />
                      <span>Your AI receptionist will be ready in minutes</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-[#27AE60]" />
                      <span>Test it with a call before going live</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-[#27AE60]" />
                      <span>7 days free, cancel anytime</span>
                    </li>
                  </ul>
                </div>

                {/* Invisible Turnstile CAPTCHA */}
                <Turnstile 
                  onVerify={setCaptchaToken}
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
              <Check className="h-3 w-3 text-[#27AE60]" />
              No credit card required
            </span>
            <span className="flex items-center gap-1">
              <Check className="h-3 w-3 text-[#27AE60]" />
              HIPAA compliant
            </span>
          </div>
        </div>
      </main>

      <MarketingFooter />
    </div>
  )
}
