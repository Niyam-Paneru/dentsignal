'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Phone, 
  ChevronDown, 
  ChevronRight, 
  Copy, 
  Check,
  Smartphone,
  Building,
  HelpCircle
} from 'lucide-react'

interface ForwardingGuideProps {
  twilioNumber?: string
}

type CarrierType = 'att' | 'verizon' | 'tmobile' | 'sprint' | 'landline' | 'voip'

const carrierInstructions: Record<CarrierType, { name: string; icon: React.ElementType; steps: string[] }> = {
  att: {
    name: 'AT&T',
    icon: Smartphone,
    steps: [
      'Dial *21* followed by your DentSignal number, then #',
      'Example: *21*9048679643#',
      'Press Send/Call to activate',
      'You\'ll hear a confirmation tone',
      'To deactivate: Dial #21# and press Send'
    ]
  },
  verizon: {
    name: 'Verizon',
    icon: Smartphone,
    steps: [
      'Dial *72 followed by your DentSignal number',
      'Example: *729048679643',
      'Press Send/Call and wait for confirmation',
      'You\'ll hear two beeps when active',
      'To deactivate: Dial *73 and press Send'
    ]
  },
  tmobile: {
    name: 'T-Mobile',
    icon: Smartphone,
    steps: [
      'Dial **21* followed by your DentSignal number, then #',
      'Example: **21*9048679643#',
      'Press Send/Call to activate',
      'Wait for confirmation message',
      'To deactivate: Dial ##21# and press Send'
    ]
  },
  sprint: {
    name: 'Sprint',
    icon: Smartphone,
    steps: [
      'Dial *72 followed by your DentSignal number',
      'Example: *729048679643',
      'Press Send/Call',
      'Wait for the second dial tone, then hang up',
      'To deactivate: Dial *720 and press Send'
    ]
  },
  landline: {
    name: 'Landline / Office Phone',
    icon: Building,
    steps: [
      'Contact your phone provider (e.g., Comcast, Spectrum, AT&T Business)',
      'Request "Unconditional Call Forwarding" to your DentSignal number',
      'Or dial *72, wait for dial tone, then dial your DentSignal number',
      'For VoIP systems (RingCentral, Vonage): Configure in admin portal',
      'Most providers can set up forwarding within 24 hours'
    ]
  },
  voip: {
    name: 'VoIP / Cloud Phone',
    icon: Building,
    steps: [
      'Log into your VoIP provider dashboard (RingCentral, Vonage, Dialpad, etc.)',
      'Go to Call Handling or Forwarding Settings',
      'Add your DentSignal number as a forwarding destination',
      'Set to "Always Forward" or during specific hours',
      'Save and test with a call to your office number'
    ]
  }
}

export function CallForwardingGuide({ twilioNumber = '(904) 867-9643' }: ForwardingGuideProps) {
  const [expandedCarrier, setExpandedCarrier] = useState<CarrierType | null>(null)
  const [copied, setCopied] = useState(false)

  const formattedNumber = twilioNumber.replace(/\D/g, '')
  
  const copyNumber = async () => {
    await navigator.clipboard.writeText(formattedNumber)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Phone className="h-5 w-5" />
          Call Forwarding Setup
        </CardTitle>
        <CardDescription>
          Forward your office calls to DentSignal so our AI can answer them
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Your DentSignal number */}
        <div className="rounded-lg border bg-muted/50 p-4">
          <p className="text-sm text-muted-foreground mb-2">Your DentSignal Number</p>
          <div className="flex items-center gap-3">
            <span className="text-2xl font-bold tracking-wider">{twilioNumber}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={copyNumber}
              className="gap-1"
            >
              {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              {copied ? 'Copied!' : 'Copy'}
            </Button>
          </div>
        </div>

        {/* Carrier selection */}
        <div className="space-y-2">
          <p className="text-sm font-medium">Select your phone provider:</p>
          
          {(Object.entries(carrierInstructions) as [CarrierType, typeof carrierInstructions[CarrierType]][]).map(([key, carrier]) => {
            const Icon = carrier.icon
            const isExpanded = expandedCarrier === key
            
            return (
              <div key={key} className="border rounded-lg overflow-hidden">
                <button
                  onClick={() => setExpandedCarrier(isExpanded ? null : key)}
                  className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Icon className="h-5 w-5 text-muted-foreground" />
                    <span className="font-medium">{carrier.name}</span>
                  </div>
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  )}
                </button>
                
                {isExpanded && (
                  <div className="px-4 pb-4 pt-2 border-t bg-muted/30">
                    <ol className="space-y-2 text-sm">
                      {carrier.steps.map((step, i) => (
                        <li key={i} className="flex gap-2">
                          <Badge variant="outline" className="h-5 w-5 shrink-0 rounded-full p-0 justify-center">
                            {i + 1}
                          </Badge>
                          <span>{step}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Need help */}
        <div className="rounded-lg bg-primary/5 border-primary/20 border p-4 flex items-start gap-3">
          <HelpCircle className="h-5 w-5 text-primary shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium mb-1">Need help setting up?</p>
            <p className="text-muted-foreground">
              Email us at{' '}
              <a href="mailto:niyampaneru79@gmail.com" className="text-primary hover:underline">
                niyampaneru79@gmail.com
              </a>
              {' '}and we&apos;ll help you set up call forwarding for free.
            </p>
          </div>
        </div>

        {/* Test your setup */}
        <div className="pt-2">
          <Button className="w-full" variant="outline">
            <Phone className="mr-2 h-4 w-4" />
            Test Your Forwarding Setup
          </Button>
          <p className="text-xs text-muted-foreground text-center mt-2">
            We&apos;ll call your office number and verify it reaches DentSignal
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
