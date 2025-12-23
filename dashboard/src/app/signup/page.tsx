'use client'

import { useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Loader2, Check, AlertCircle, ArrowLeft, ArrowRight } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'

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
  const [ownerName, setOwnerName] = useState('')
  const [phone, setPhone] = useState('')
  const [monthlyCallVolume, setMonthlyCallVolume] = useState('500')
  const [answerRate, setAnswerRate] = useState([50])
  const [reminderMethod, setReminderMethod] = useState('sms')
  
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
    if (!password || password.length < 8) {
      setError('Password must be at least 8 characters')
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
    
    const callVolume = parseInt(monthlyCallVolume) || 500
    
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
    
    if (callVolume <= 0) {
      setError('Monthly call volume must be greater than 0')
      setIsLoading(false)
      return
    }
    
    // Sign up user
    const { data: authData, error: signUpError } = await supabase.auth.signUp({
      email,
      password,
      options: {
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
          owner_name: ownerName || `${firstName} ${lastName}`,
          phone: stripPhoneFormatting(phone),
          monthly_call_volume: callVolume,
          current_answer_rate: answerRate[0],
          reminder_method: reminderMethod,
        })
      
      if (clinicError) {
        console.error('Failed to create clinic:', clinicError)
        // Don't block signup, they can add clinic info later
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
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-white p-4 dark:from-gray-900 dark:to-gray-950">
      <Card className="w-full max-w-lg">
        <div className="p-4 pb-0">
          {step === 1 ? (
            <Link href="/" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary transition-colors">
              <ArrowLeft className="h-4 w-4" />
              Back to Home
            </Link>
          ) : (
            <button 
              type="button"
              onClick={handlePrevStep}
              className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Account Info
            </button>
          )}
        </div>
        <CardHeader className="text-center pt-2">
          <div className="mx-auto mb-4">
            <Image src="/favicon.png" alt="DentSignal" width={48} height={48} className="rounded-lg" />
          </div>
          <CardTitle className="text-2xl">
            {step === 1 ? 'Create Your Account' : 'Set Up Your Clinic'}
          </CardTitle>
          <CardDescription>
            {step === 1 ? 'Step 1 of 2 – Account Information' : 'Step 2 of 2 – Clinic Details'}
          </CardDescription>
          {/* Progress indicator */}
          <div className="flex justify-center gap-2 pt-3">
            <div className={`h-2 w-16 rounded-full transition-colors ${step >= 1 ? 'bg-primary' : 'bg-muted'}`} />
            <div className={`h-2 w-16 rounded-full transition-colors ${step >= 2 ? 'bg-primary' : 'bg-muted'}`} />
          </div>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="flex items-center gap-2 rounded-lg bg-red-50 p-3 text-sm text-red-600 dark:bg-red-900/20 dark:text-red-400 mb-4">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          {step === 1 ? (
            /* Step 1: Account Information */
            <div className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="firstName">First Name</Label>
                  <Input 
                    id="firstName" 
                    placeholder="John" 
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    required 
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName">Last Name</Label>
                  <Input 
                    id="lastName" 
                    placeholder="Smith" 
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    required 
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input 
                  id="email" 
                  type="email" 
                  placeholder="you@clinic.com" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required 
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input 
                  id="password" 
                  type="password" 
                  placeholder="••••••••" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required 
                  minLength={8} 
                />
                <p className="text-xs text-muted-foreground">Must be at least 8 characters</p>
              </div>

              {/* Benefits preview */}
              <div className="rounded-lg bg-muted p-3 mt-4">
                <p className="mb-2 text-sm font-medium">What you&apos;ll get:</p>
                <ul className="space-y-1 text-xs text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <Check className="h-3 w-3 text-green-500" />
                    AI-powered call handling 24/7
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-3 w-3 text-green-500" />
                    Automatic appointment booking
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-3 w-3 text-green-500" />
                    Call analytics & insights
                  </li>
                </ul>
              </div>

              <Button type="button" className="w-full" onClick={handleNextStep}>
                Continue
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          ) : (
            /* Step 2: Clinic Information */
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="clinicName">Clinic Name</Label>
                <Input 
                  id="clinicName" 
                  placeholder="Sunshine Dental Care" 
                  value={clinicName}
                  onChange={(e) => setClinicName(e.target.value)}
                  required 
                  minLength={3} 
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ownerName">Owner / Lead Dentist Name</Label>
                <Input 
                  id="ownerName" 
                  placeholder="Dr. John Smith" 
                  value={ownerName}
                  onChange={(e) => setOwnerName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Practice Phone Number</Label>
                <Input 
                  id="phone" 
                  type="tel" 
                  placeholder="(555) 123-4567"
                  value={phone}
                  onChange={handlePhoneChange}
                  required 
                />
                <p className="text-xs text-muted-foreground">Your current clinic phone number</p>
              </div>
              
              <div className="space-y-4 pt-2 border-t">
                <div className="text-sm font-medium text-muted-foreground pt-2">Personalize Your Experience</div>
                <div className="space-y-2">
                  <Label htmlFor="monthlyCallVolume">Estimated Monthly Call Volume</Label>
                  <Input 
                    id="monthlyCallVolume" 
                    type="number" 
                    min={1}
                    max={10000}
                    value={monthlyCallVolume}
                    onChange={(e) => setMonthlyCallVolume(e.target.value)}
                    required 
                  />
                  <p className="text-xs text-muted-foreground">How many calls does your clinic receive per month?</p>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Current Answer Rate</Label>
                    <span className="text-sm font-medium">{answerRate[0]}%</span>
                  </div>
                  <Slider
                    value={answerRate}
                    onValueChange={setAnswerRate}
                    max={100}
                    min={0}
                    step={5}
                    className="w-full"
                  />
                  <p className="text-xs text-muted-foreground">What percentage of calls do you currently answer?</p>
                </div>
                <div className="space-y-3">
                  <Label>Preferred Reminder Method</Label>
                  <RadioGroup value={reminderMethod} onValueChange={setReminderMethod} className="flex gap-6">
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="sms" id="sms" />
                      <Label htmlFor="sms" className="font-normal cursor-pointer">SMS</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="email" id="email-reminder" />
                      <Label htmlFor="email-reminder" className="font-normal cursor-pointer">Email</Label>
                    </div>
                  </RadioGroup>
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  'Create Account'
                )}
              </Button>
            </form>
          )}

          <div className="mt-6 text-center text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link href="/login" className="text-primary hover:underline">
              Sign in
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
