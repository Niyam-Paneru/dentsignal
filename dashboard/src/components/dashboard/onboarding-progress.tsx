'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

import { 
  CheckCircle2, 
  Circle, 
  Phone, 
  Calendar,
  Bot,
  ChevronRight,
  X
} from 'lucide-react'
import Link from 'next/link'

interface OnboardingStep {
  id: string
  title: string
  description: string
  icon: React.ElementType
  completed: boolean
  href?: string
  action?: string
}

interface OnboardingProgressProps {
  clinicName?: string
  hasForwardingSetup?: boolean
  hasCustomGreeting?: boolean
  hasFirstCall?: boolean
  onDismiss?: () => void
}

export function OnboardingProgress({
  clinicName,
  hasForwardingSetup = false,
  hasCustomGreeting = false,
  hasFirstCall = false,
  onDismiss
}: OnboardingProgressProps) {
  // Check if already dismissed in localStorage on mount
  const [dismissed, setDismissed] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('onboarding-dismissed') === 'true'
    }
    return false
  })

  const steps: OnboardingStep[] = [
    {
      id: 'clinic-setup',
      title: 'Clinic Profile Created',
      description: 'Your clinic information is saved',
      icon: CheckCircle2,
      completed: !!clinicName,
    },
    {
      id: 'call-forwarding',
      title: 'Set Up Call Forwarding',
      description: 'Forward your office calls to DentSignal',
      icon: Phone,
      completed: hasForwardingSetup,
      href: '/settings?tab=forwarding',
      action: 'Set up forwarding',
    },
    {
      id: 'customize-ai',
      title: 'Customize Your AI Receptionist',
      description: 'Set the greeting, voice, and preferences',
      icon: Bot,
      completed: hasCustomGreeting,
      href: '/settings?tab=ai',
      action: 'Customize AI',
    },
    {
      id: 'first-call',
      title: 'Receive Your First Call',
      description: 'DentSignal will handle your incoming calls',
      icon: Calendar,
      completed: hasFirstCall,
    },
  ]

  const completedSteps = steps.filter(s => s.completed).length
  const progress = Math.round((completedSteps / steps.length) * 100)

  const handleDismiss = () => {
    setDismissed(true)
    localStorage.setItem('onboarding-dismissed', 'true')
    onDismiss?.()
  }

  // Hide if all steps complete or dismissed
  if (dismissed || completedSteps === steps.length) {
    return null
  }

  return (
    <Card className="relative border-primary/20 bg-gradient-to-r from-primary/5 to-transparent">
      <button
        onClick={handleDismiss}
        className="absolute right-3 top-3 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        aria-label="Dismiss onboarding"
      >
        <X className="h-4 w-4" />
      </button>
      
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">Get Started with DentSignal</CardTitle>
        <CardDescription>
          Complete these steps to start receiving AI-handled calls
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Progress bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">{completedSteps} of {steps.length} complete</span>
            <span className="font-medium">{progress}%</span>
          </div>
          <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
            <div 
              className="h-full bg-primary transition-all duration-300" 
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Steps list */}
        <div className="space-y-2">
          {steps.map((step) => (
            <div
              key={step.id}
              className={`flex items-center gap-3 rounded-lg border p-3 transition-colors ${
                step.completed 
                  ? 'bg-muted/30 border-muted' 
                  : 'bg-background hover:bg-muted/50'
              }`}
            >
              <div className={`flex-shrink-0 ${step.completed ? 'text-green-600' : 'text-muted-foreground'}`}>
                {step.completed ? (
                  <CheckCircle2 className="h-5 w-5" />
                ) : (
                  <Circle className="h-5 w-5" />
                )}
              </div>
              
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium ${step.completed ? 'text-muted-foreground line-through' : ''}`}>
                  {step.title}
                </p>
                <p className="text-xs text-muted-foreground truncate">
                  {step.description}
                </p>
              </div>

              {!step.completed && step.href && (
                <Link href={step.href}>
                  <Button size="sm" variant="outline" className="gap-1">
                    {step.action}
                    <ChevronRight className="h-3 w-3" />
                  </Button>
                </Link>
              )}
            </div>
          ))}
        </div>

        {/* Quick help */}
        <div className="rounded-lg bg-muted/50 p-3 text-sm">
          <p className="text-muted-foreground">
            Need help? Email us at{' '}
            <a href="mailto:niyampaneru79@gmail.com" className="text-primary hover:underline">
              niyampaneru79@gmail.com
            </a>
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
