'use client'

import { Phone, Calendar, Users, TrendingUp, Sparkles, ArrowRight, Copy, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useState } from 'react'

interface EmptyStateProps {
  clinicName?: string
  aiName?: string
  phoneNumber?: string
}

export function EmptyCallsState({ clinicName, aiName = 'Sarah', phoneNumber }: EmptyStateProps) {
  const [copied, setCopied] = useState(false)
  
  const handleCopy = () => {
    if (phoneNumber) {
      navigator.clipboard.writeText(phoneNumber)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }
  
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="relative">
        <div className="w-24 h-24 rounded-full bg-blue-50 flex items-center justify-center mb-6">
          <Phone className="w-12 h-12 text-[#0099CC]" />
        </div>
        <div className="absolute -top-1 -right-1 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
        </div>
      </div>
      
      <h3 className="text-xl font-semibold text-[#1B3A7C] mb-2">
        {aiName} is live and ready
      </h3>
      
      <p className="text-gray-600 max-w-md mb-6">
        Your AI receptionist is standing by. Share your number or forward your existing line to start receiving calls.
      </p>
      
      {phoneNumber && (
        <div className="flex flex-col sm:flex-row gap-3 mb-8">
          <div className="px-4 py-2 bg-gray-100 rounded-lg font-mono text-lg">
            {phoneNumber}
          </div>
          <Button onClick={handleCopy} variant="outline" className="gap-2">
            {copied ? (
              <>
                <CheckCircle className="w-4 h-4 text-green-500" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                Copy number
              </>
            )}
          </Button>
        </div>
      )}
      
      <div className="flex items-center gap-6 text-sm text-gray-500">
        <span className="flex items-center gap-1">
          <CheckCircle className="w-4 h-4 text-green-500" />
          AI trained on {clinicName || 'your clinic'}
        </span>
        <span className="flex items-center gap-1">
          <CheckCircle className="w-4 h-4 text-green-500" />
          Calendar connected
        </span>
      </div>
      
      <div className="mt-8 p-4 bg-amber-50 border border-amber-200 rounded-lg max-w-md">
        <p className="text-sm text-amber-800">
          <strong>Pro tip:</strong> Forward your existing clinic number to {phoneNumber || 'your AI number'} and {aiName} will start answering immediately.
        </p>
      </div>
    </div>
  )
}

export function EmptyCalendarState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="w-20 h-20 rounded-full bg-purple-50 flex items-center justify-center mb-6">
        <Calendar className="w-10 h-10 text-purple-500" />
      </div>
      
      <h3 className="text-xl font-semibold text-[#1B3A7C] mb-2">
        No upcoming appointments
      </h3>
      
      <p className="text-gray-600 max-w-md mb-6">
        When patients book appointments through your AI receptionist, they'll appear here automatically.
      </p>
      
      <Button variant="outline" className="gap-2">
        Connect calendar
        <ArrowRight className="w-4 h-4" />
      </Button>
    </div>
  )
}

export function EmptyAnalyticsState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="w-20 h-20 rounded-full bg-green-50 flex items-center justify-center mb-6">
        <TrendingUp className="w-10 h-10 text-green-500" />
      </div>
      
      <h3 className="text-xl font-semibold text-[#1B3A7C] mb-2">
        Analytics will appear here
      </h3>
      
      <p className="text-gray-600 max-w-md mb-6">
        Once you start receiving calls, you'll see insights like call volume, conversion rates, and revenue impact.
      </p>
      
      <div className="grid grid-cols-2 gap-4 w-full max-w-sm opacity-50">
        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-gray-400">--</div>
          <div className="text-xs text-gray-400">Calls today</div>
        </div>
        <div className="p-4 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-gray-400">--</div>
          <div className="text-xs text-gray-400">Conversion rate</div>
        </div>
      </div>
    </div>
  )
}

export function FirstCallCelebration({ 
  clinicName, 
  aiName = 'Sarah',
  onListen 
}: { 
  clinicName?: string
  aiName?: string
  onListen?: () => void 
}) {
  return (
    <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-6">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center shrink-0">
          <Sparkles className="w-6 h-6 text-green-600" />
        </div>
        
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-green-800 mb-1">
            First call answered! 🎉
          </h3>
          
          <p className="text-green-700 mb-4">
            {aiName} just handled a call for {clinicName || 'your clinic'}. That's one less missed opportunity!
          </p>
          
          {onListen && (
            <Button 
              variant="outline" 
              size="sm" 
              onClick={onListen}
              className="bg-white border-green-300 text-green-700 hover:bg-green-50"
            >
              Listen to recording
            </Button>
          )}
        </div>
      </div>
      
      <div className="mt-4 pt-4 border-t border-green-200 flex items-center justify-between">
        <span className="text-sm text-green-600">
          Impact so far
        </span>
        <span className="text-lg font-bold text-green-800">
          1 patient helped
        </span>
      </div>
    </div>
  )
}

export function EmptyRecallsState() {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="w-16 h-16 rounded-full bg-orange-50 flex items-center justify-center mb-4">
        <Users className="w-8 h-8 text-orange-500" />
      </div>
      
      <h3 className="text-lg font-semibold text-[#1B3A7C] mb-2">
        No recall campaigns yet
      </h3>
      
      <p className="text-sm text-gray-600 max-w-md mb-4">
        Set up automated recall campaigns to bring patients back for their regular checkups.
      </p>
      
      <Button size="sm" className="gap-2">
        Create first campaign
        <ArrowRight className="w-4 h-4" />
      </Button>
    </div>
  )
}
