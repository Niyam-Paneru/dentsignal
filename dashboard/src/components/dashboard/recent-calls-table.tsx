'use client'

import { Badge } from '@/components/ui/badge'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Phone, PhoneForwarded, Info, PhoneMissed, CheckCircle } from 'lucide-react'

interface RecentCall {
  id: string
  time: string
  caller_phone: string
  reason: string
  outcome: string
  duration: string
}

interface RecentCallsTableProps {
  calls: RecentCall[]
}

const outcomeConfig: Record<string, { 
  label: string
  description: string
  variant: 'default' | 'secondary' | 'outline' | 'destructive'
  icon: typeof CheckCircle
  className: string
}> = {
  booked: { 
    label: 'Booked', 
    description: 'Appointment successfully scheduled',
    variant: 'default' as const,
    icon: CheckCircle,
    className: 'bg-green-100 text-green-800 hover:bg-green-100 dark:bg-green-900 dark:text-green-100'
  },
  transferred: { 
    label: 'Transferred', 
    description: 'Call transferred to staff member',
    variant: 'secondary' as const,
    icon: PhoneForwarded,
    className: 'bg-orange-100 text-orange-800 hover:bg-orange-100 dark:bg-orange-900 dark:text-orange-100'
  },
  transfer: { 
    label: 'Transferred', 
    description: 'Call transferred to staff member',
    variant: 'secondary' as const,
    icon: PhoneForwarded,
    className: 'bg-orange-100 text-orange-800 hover:bg-orange-100 dark:bg-orange-900 dark:text-orange-100'
  },
  info: { 
    label: 'Info', 
    description: 'Caller received information only',
    variant: 'outline' as const,
    icon: Info,
    className: 'bg-blue-100 text-blue-800 hover:bg-blue-100 dark:bg-blue-900 dark:text-blue-100'
  },
  inquiry: { 
    label: 'Inquiry', 
    description: 'General question answered',
    variant: 'outline' as const,
    icon: Info,
    className: 'bg-blue-100 text-blue-800 hover:bg-blue-100 dark:bg-blue-900 dark:text-blue-100'
  },
  cancelled: { 
    label: 'Cancelled', 
    description: 'Caller ended call before completion',
    variant: 'secondary' as const,
    icon: PhoneMissed,
    className: 'bg-gray-100 text-gray-800 hover:bg-gray-100 dark:bg-gray-700 dark:text-gray-100'
  },
  missed: { 
    label: 'Missed', 
    description: 'Call was not answered',
    variant: 'destructive' as const,
    icon: PhoneMissed,
    className: 'bg-red-100 text-red-800 hover:bg-red-100 dark:bg-red-900 dark:text-red-100'
  },
  failed: { 
    label: 'Failed', 
    description: 'Technical issue prevented call handling',
    variant: 'destructive' as const,
    icon: PhoneMissed,
    className: 'bg-red-100 text-red-800 hover:bg-red-100 dark:bg-red-900 dark:text-red-100'
  },
}

export function RecentCallsTable({ calls }: RecentCallsTableProps) {
  const defaultConfig = {
    label: 'Unknown',
    description: 'Call outcome not determined',
    variant: 'outline' as const,
    icon: Phone,
    className: 'bg-gray-100 text-gray-800 hover:bg-gray-100 dark:bg-gray-700 dark:text-gray-100'
  }

  if (calls.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted mb-3">
          <Phone className="h-6 w-6 text-muted-foreground" />
        </div>
        <p className="text-sm font-medium text-muted-foreground">No calls yet</p>
        <p className="text-xs text-muted-foreground mt-1">
          Calls will appear here once your AI agent starts taking calls
        </p>
      </div>
    )
  }

  return (
    <TooltipProvider>
      <div className="space-y-4">
        {calls.map((call) => {
          const config = outcomeConfig[call.outcome] || defaultConfig
          const Icon = config.icon
          
          return (
            <div
              key={call.id}
              className="flex items-center justify-between rounded-lg border p-3 transition-colors hover:bg-muted/50"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10">
                  <Phone className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium">{call.reason}</p>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <p className="text-xs text-muted-foreground cursor-help">
                        {call.time} • {call.caller_phone}
                      </p>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Phone: {call.caller_phone}</p>
                      <p>Duration: {call.duration}</p>
                    </TooltipContent>
                  </Tooltip>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">{call.duration}</span>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Badge className={config.className}>
                      <Icon className="mr-1 h-3 w-3" />
                      {config.label}
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{config.description}</p>
                  </TooltipContent>
                </Tooltip>
              </div>
            </div>
          )
        })}
      </div>
    </TooltipProvider>
  )
}
