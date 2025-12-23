'use client'

import { useEffect, useState, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { 
  Phone, 
  PhoneForwarded, 
  PhoneIncoming, 
  Loader2, 
  Volume2, 
  Clock, 
  User,
  FileText,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  ArrowUpRight
} from 'lucide-react'
import { createClient } from '@/lib/supabase/client'
import type { Call } from '@/types/database'

interface LiveCall extends Call {
  live_duration?: string
}

// Get user's clinic ID
async function getUserClinicId(): Promise<string | null> {
  const supabase = createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return null
  
  const { data: clinic } = await supabase
    .from('dental_clinics')
    .select('id')
    .eq('owner_id', user.id)
    .single()
  
  return clinic?.id || null
}

// Status badge config
const statusConfig: Record<string, { 
  label: string
  className: string
  icon: typeof Phone
}> = {
  active: { 
    label: 'Active', 
    className: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100 animate-pulse',
    icon: Phone
  },
  ringing: { 
    label: 'Ringing', 
    className: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100 animate-pulse',
    icon: PhoneIncoming
  },
  in_progress: { 
    label: 'In Progress', 
    className: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100',
    icon: Phone
  },
  transferring: { 
    label: 'Transferring', 
    className: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-100 animate-pulse',
    icon: PhoneForwarded
  },
  completed: { 
    label: 'Completed', 
    className: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-100',
    icon: CheckCircle
  },
  failed: { 
    label: 'Failed', 
    className: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100',
    icon: AlertCircle
  },
}

const outcomeConfig: Record<string, { 
  label: string
  className: string
}> = {
  booked: { label: '✓ BOOKED', className: 'text-green-600 dark:text-green-400' },
  transferred: { label: '→ TRANSFERRED', className: 'text-orange-600 dark:text-orange-400' },
  info: { label: '✓ RESOLVED', className: 'text-blue-600 dark:text-blue-400' },
  inquiry: { label: '✓ RESOLVED', className: 'text-blue-600 dark:text-blue-400' },
  missed: { label: '✗ MISSED', className: 'text-red-600 dark:text-red-400' },
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatTime(dateString: string): string {
  return new Date(dateString).toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  })
}

export default function LiveCallsPage() {
  const [activeCalls, setActiveCalls] = useState<LiveCall[]>([])
  const [recentCalls, setRecentCalls] = useState<Call[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCall, setSelectedCall] = useState<Call | null>(null)
  const [notes, setNotes] = useState('')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  
  const supabase = createClient()

  const fetchCalls = useCallback(async () => {
    const clinicId = await getUserClinicId()
    if (!clinicId) return
    
    // Fetch active calls
    const { data: active } = await supabase
      .from('dental_calls')
      .select('*')
      .eq('clinic_id', clinicId)
      .in('status', ['active', 'ringing', 'in_progress', 'transferring'])
      .order('started_at', { ascending: false })
    
    // Fetch recent completed calls (last 10)
    const { data: recent } = await supabase
      .from('dental_calls')
      .select('*')
      .eq('clinic_id', clinicId)
      .not('status', 'in', '("active","ringing","in_progress","transferring")')
      .order('started_at', { ascending: false })
      .limit(10)
    
    // Calculate live duration for active calls
    const activeWithDuration = (active || []).map(call => ({
      ...call,
      live_duration: call.started_at 
        ? formatDuration(Math.floor((Date.now() - new Date(call.started_at).getTime()) / 1000))
        : '0:00'
    }))
    
    setActiveCalls(activeWithDuration)
    setRecentCalls(recent || [])
    setLastUpdate(new Date())
    setLoading(false)
  }, [supabase])

  useEffect(() => {
    fetchCalls()
    
    // Auto-refresh every 2 seconds
    const interval = setInterval(() => {
      if (autoRefresh) {
        fetchCalls()
      }
    }, 2000)
    
    return () => clearInterval(interval)
  }, [autoRefresh, fetchCalls])

  // Subscribe to realtime updates
  useEffect(() => {
    const channel = supabase
      .channel('live-calls')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'dental_calls' },
        () => {
          fetchCalls()
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [supabase, fetchCalls])

  const handleSaveNotes = async () => {
    if (!selectedCall) return
    
    await supabase
      .from('dental_calls')
      .update({ receptionist_notes: notes })
      .eq('id', selectedCall.id)
    
    setSelectedCall(null)
    setNotes('')
    fetchCalls()
  }

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">Live Calls</h1>
            {activeCalls.length > 0 && (
              <Badge className="bg-red-500 text-white animate-pulse px-3 py-1">
                {activeCalls.length} Active
              </Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Auto-refresh ON
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-2" />
                Auto-refresh OFF
              </>
            )}
          </Button>
          <Button variant="outline" size="sm" onClick={fetchCalls}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Active Calls Section */}
      <Card className="border-2 border-primary/20">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Volume2 className="h-5 w-5 text-primary" />
            <CardTitle>Active Calls ({activeCalls.length})</CardTitle>
          </div>
          <CardDescription>Real-time view of ongoing calls</CardDescription>
        </CardHeader>
        <CardContent>
          {activeCalls.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Phone className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No active calls right now</p>
              <p className="text-sm">Calls will appear here when patients dial in</p>
            </div>
          ) : (
            <div className="space-y-3">
              {activeCalls.map((call) => {
                const statusInfo = statusConfig[call.status || 'active'] || statusConfig.active
                const StatusIcon = statusInfo.icon
                
                return (
                  <div
                    key={call.id}
                    className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                        <StatusIcon className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">
                            {call.caller_name || call.caller_phone || 'Unknown Caller'}
                          </span>
                          <Badge className={statusInfo.className}>
                            {statusInfo.label}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {call.live_duration}
                          </span>
                          <span className="flex items-center gap-1">
                            <User className="h-3 w-3" />
                            {call.caller_phone}
                          </span>
                          {call.call_reason && (
                            <span className="flex items-center gap-1">
                              <FileText className="h-3 w-3" />
                              {call.call_reason}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button size="sm" variant="outline">
                        View Transcript
                      </Button>
                      <Button size="sm" className="bg-green-600 hover:bg-green-700">
                        Join Call
                      </Button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Calls Section */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Calls</CardTitle>
          <CardDescription>Last 10 completed calls</CardDescription>
        </CardHeader>
        <CardContent>
          {recentCalls.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No recent calls</p>
            </div>
          ) : (
            <div className="space-y-2">
              {recentCalls.map((call) => {
                const outcomeInfo = outcomeConfig[call.outcome] || { label: call.outcome, className: '' }
                
                return (
                  <Dialog key={call.id}>
                    <DialogTrigger asChild>
                      <div
                        className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent/50 transition-colors cursor-pointer"
                        onClick={() => {
                          setSelectedCall(call)
                          setNotes(call.receptionist_notes || '')
                        }}
                      >
                        <div className="flex items-center gap-4">
                          <div className="text-sm text-muted-foreground w-20">
                            {formatTime(call.started_at)}
                          </div>
                          <div>
                            <span className="font-medium">
                              {call.caller_name || call.caller_phone || 'Unknown'}
                            </span>
                            {call.call_reason && (
                              <span className="text-sm text-muted-foreground ml-2">
                                - {call.call_reason}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-sm text-muted-foreground">
                            {call.duration_seconds ? formatDuration(call.duration_seconds) : '-'}
                          </span>
                          <span className={`text-sm font-medium ${outcomeInfo.className}`}>
                            {outcomeInfo.label}
                          </span>
                          {call.quality_score && (
                            <Badge variant="outline" className="ml-2">
                              Score: {call.quality_score}
                            </Badge>
                          )}
                          <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
                        </div>
                      </div>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle>Call Details</DialogTitle>
                        <DialogDescription>
                          {formatTime(call.started_at)} • {call.caller_phone}
                        </DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4">
                        {/* Call Info */}
                        <div className="grid grid-cols-2 gap-4 p-4 rounded-lg bg-muted">
                          <div>
                            <div className="text-sm text-muted-foreground">Caller</div>
                            <div className="font-medium">{call.caller_name || 'Unknown'}</div>
                          </div>
                          <div>
                            <div className="text-sm text-muted-foreground">Phone</div>
                            <div className="font-medium">{call.caller_phone}</div>
                          </div>
                          <div>
                            <div className="text-sm text-muted-foreground">Duration</div>
                            <div className="font-medium">
                              {call.duration_seconds ? formatDuration(call.duration_seconds) : '-'}
                            </div>
                          </div>
                          <div>
                            <div className="text-sm text-muted-foreground">Outcome</div>
                            <div className={`font-medium ${outcomeInfo.className}`}>
                              {outcomeInfo.label}
                            </div>
                          </div>
                          {call.quality_score && (
                            <div>
                              <div className="text-sm text-muted-foreground">Quality Score</div>
                              <div className="font-medium">{call.quality_score}/100</div>
                            </div>
                          )}
                          {call.transferred_to && (
                            <div>
                              <div className="text-sm text-muted-foreground">Transferred To</div>
                              <div className="font-medium">{call.transferred_to}</div>
                            </div>
                          )}
                        </div>
                        
                        {/* Transcript */}
                        {call.transcript && (
                          <div>
                            <div className="text-sm font-medium mb-2">Transcript</div>
                            <div className="p-4 rounded-lg bg-muted text-sm whitespace-pre-wrap max-h-60 overflow-y-auto">
                              {call.transcript}
                            </div>
                          </div>
                        )}
                        
                        {/* Summary */}
                        {call.summary && (
                          <div>
                            <div className="text-sm font-medium mb-2">AI Summary</div>
                            <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-sm">
                              {call.summary}
                            </div>
                          </div>
                        )}
                        
                        {/* Receptionist Notes */}
                        <div>
                          <div className="text-sm font-medium mb-2">Receptionist Notes</div>
                          <Textarea
                            placeholder="Add notes about this call..."
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            rows={3}
                          />
                          <Button 
                            className="mt-2" 
                            size="sm"
                            onClick={handleSaveNotes}
                          >
                            Save Notes
                          </Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
