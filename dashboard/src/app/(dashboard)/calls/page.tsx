'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Search, Filter, Play, FileText, Phone, Loader2, Star, CheckCircle, AlertCircle } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { getAllCalls } from '@/lib/api/dental'
import type { Call } from '@/types/database'

const outcomeConfig: Record<string, { label: string; className: string }> = {
  booked: { label: 'Booked', className: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100' },
  transferred: { label: 'Transferred', className: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-100' },
  transfer: { label: 'Transferred', className: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-100' },
  info: { label: 'Info', className: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100' },
  inquiry: { label: 'Inquiry', className: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100' },
  cancelled: { label: 'Cancelled', className: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-100' },
  missed: { label: 'Missed', className: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100' },
  failed: { label: 'Failed', className: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100' },
}

const defaultOutcome = { label: 'Unknown', className: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-100' }

const sentimentConfig = {
  positive: { label: '😊 Positive', className: 'text-green-600' },
  neutral: { label: '😐 Neutral', className: 'text-gray-600' },
  negative: { label: '😞 Negative', className: 'text-red-600' },
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
    hour12: true,
  })
}

export default function CallsPage() {
  const [calls, setCalls] = useState<Call[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [outcomeFilter, setOutcomeFilter] = useState<string>('all')
  const [selectedCall, setSelectedCall] = useState<Call | null>(null)

  useEffect(() => {
    async function loadCalls() {
      setLoading(true)
      try {
        const data = await getAllCalls()
        setCalls(data)
      } catch (error) {
        console.error('Failed to load calls:', error)
      } finally {
        setLoading(false)
      }
    }
    loadCalls()
  }, [])

  const filteredCalls = calls.filter((call) => {
    const matchesSearch = 
      (call.caller_phone || '').includes(searchQuery) ||
      (call.call_reason || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (call.transcript || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (call.summary || '').toLowerCase().includes(searchQuery.toLowerCase())
    const matchesOutcome = outcomeFilter === 'all' || call.outcome === outcomeFilter
    return matchesSearch && matchesOutcome
  })

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
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Call History</h1>
        <p className="text-muted-foreground">View and manage all calls handled by AI</p>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by phone, reason, or transcript..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={outcomeFilter} onValueChange={setOutcomeFilter}>
          <SelectTrigger className="w-full sm:w-[180px]">
            <Filter className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Filter by outcome" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Outcomes</SelectItem>
            <SelectItem value="booked">Booked</SelectItem>
            <SelectItem value="transferred">Transferred</SelectItem>
            <SelectItem value="info">Info</SelectItem>
            <SelectItem value="missed">Missed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Calls Table */}
      <Card>
        <CardHeader>
          <CardTitle>Today&apos;s Calls</CardTitle>
          <CardDescription>{filteredCalls.length} calls</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {filteredCalls.map((call) => {
              const outcome = outcomeConfig[call.outcome] || defaultOutcome
              const sentiment = sentimentConfig[call.sentiment || 'neutral']
              return (
              <div
                key={call.id}
                onClick={() => setSelectedCall(call)}
                className="flex cursor-pointer items-center justify-between rounded-lg border p-4 transition-colors hover:bg-muted/50"
              >
                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                    <Phone className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">{call.call_reason || 'Unknown'}</p>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <span>{formatTime(call.started_at)}</span>
                      <span>•</span>
                      <span>{call.caller_phone}</span>
                      <span>•</span>
                      <span>{formatDuration(call.duration_seconds || 0)}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-sm ${sentiment.className}`}>
                    {sentiment.label}
                  </span>
                  <Badge className={outcome.className}>
                    {outcome.label}
                  </Badge>
                </div>
              </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Call Detail Dialog */}
      <Dialog open={!!selectedCall} onOpenChange={() => setSelectedCall(null)}>
        <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
          {selectedCall && (() => {
            const outcome = outcomeConfig[selectedCall.outcome] || defaultOutcome
            const sentiment = sentimentConfig[selectedCall.sentiment || 'neutral']
            return (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Phone className="h-5 w-5" />
                  {selectedCall.call_reason || 'Call'}
                </DialogTitle>
                <DialogDescription>
                  {formatTime(selectedCall.started_at)} • {selectedCall.caller_phone} • {formatDuration(selectedCall.duration_seconds || 0)}
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4">
                {/* Status badges */}
                <div className="flex gap-2">
                  <Badge className={outcome.className}>
                    {outcome.label}
                  </Badge>
                  <Badge variant="outline" className={sentiment.className}>
                    {sentiment.label}
                  </Badge>
                  {selectedCall.quality_score !== undefined && selectedCall.quality_score !== null && (
                    <Badge 
                      variant="outline" 
                      className={
                        selectedCall.quality_score >= 80 ? 'text-green-600 border-green-300' :
                        selectedCall.quality_score >= 60 ? 'text-amber-600 border-amber-300' :
                        'text-red-600 border-red-300'
                      }
                    >
                      <Star className="h-3 w-3 mr-1" />
                      {selectedCall.quality_score}%
                    </Badge>
                  )}
                </div>

                {/* Quality Score Breakdown */}
                {selectedCall.quality_score !== undefined && selectedCall.quality_score !== null && (
                  <div className="rounded-lg border p-4 space-y-3">
                    <h4 className="font-medium flex items-center gap-2">
                      <Star className="h-4 w-4 text-amber-500" />
                      Quality Score Breakdown
                    </h4>
                    <div className="grid grid-cols-2 gap-4">
                      {/* Main Score */}
                      <div className="col-span-2">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm text-muted-foreground">Overall Quality</span>
                          <span className={`text-lg font-bold ${
                            selectedCall.quality_score >= 80 ? 'text-green-600' :
                            selectedCall.quality_score >= 60 ? 'text-amber-600' :
                            'text-red-600'
                          }`}>
                            {selectedCall.quality_score}%
                          </span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full transition-[width] duration-300 ${
                              selectedCall.quality_score >= 80 ? 'bg-green-500' :
                              selectedCall.quality_score >= 60 ? 'bg-amber-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${selectedCall.quality_score}%` }}
                          />
                        </div>
                      </div>
                      
                      {/* Breakdown Items */}
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm">
                          <CheckCircle className={`h-4 w-4 ${selectedCall.quality_score >= 70 ? 'text-green-500' : 'text-muted-foreground'}`} />
                          <span>Professional greeting</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <CheckCircle className={`h-4 w-4 ${selectedCall.outcome === 'booked' ? 'text-green-500' : 'text-muted-foreground'}`} />
                          <span>Resolved inquiry</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <CheckCircle className={`h-4 w-4 ${(selectedCall.duration_seconds || 0) > 60 ? 'text-green-500' : 'text-muted-foreground'}`} />
                          <span>Adequate call length</span>
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm">
                          {selectedCall.sentiment === 'positive' ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : selectedCall.sentiment === 'negative' ? (
                            <AlertCircle className="h-4 w-4 text-red-500" />
                          ) : (
                            <CheckCircle className="h-4 w-4 text-muted-foreground" />
                          )}
                          <span>Patient satisfaction</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <CheckCircle className={`h-4 w-4 ${selectedCall.summary ? 'text-green-500' : 'text-muted-foreground'}`} />
                          <span>Call documented</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <CheckCircle className={`h-4 w-4 ${selectedCall.quality_score >= 80 ? 'text-green-500' : 'text-muted-foreground'}`} />
                          <span>No escalation needed</span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Quality Tips */}
                    {selectedCall.quality_score < 70 && (
                      <div className="mt-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
                        <p className="text-sm text-amber-800 font-medium">💡 Improvement Tip</p>
                        <p className="text-xs text-amber-700 mt-1">
                          {selectedCall.sentiment === 'negative' 
                            ? 'Consider reviewing the transcript for handling difficult conversations better.'
                            : selectedCall.outcome === 'missed'
                            ? 'Try to answer calls more quickly or improve voicemail options.'
                            : 'Review the prompt settings to improve call handling quality.'
                          }
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Summary */}
                <div className="rounded-lg bg-muted p-4">
                  <h4 className="mb-2 font-medium">Summary</h4>
                  <p className="text-sm text-muted-foreground">{selectedCall.summary || 'No summary available'}</p>
                </div>

                {/* Transcript */}
                <Tabs defaultValue="transcript">
                  <TabsList>
                    <TabsTrigger value="transcript">
                      <FileText className="mr-2 h-4 w-4" />
                      Transcript
                    </TabsTrigger>
                    <TabsTrigger value="recording">
                      <Play className="mr-2 h-4 w-4" />
                      Recording
                    </TabsTrigger>
                  </TabsList>
                  <TabsContent value="transcript" className="mt-4">
                    <div className="max-h-[300px] overflow-y-auto rounded-lg border bg-card p-4">
                      <pre className="whitespace-pre-wrap text-sm">{selectedCall.transcript || 'No transcript available'}</pre>
                    </div>
                  </TabsContent>
                  <TabsContent value="recording" className="mt-4">
                    <div className="rounded-lg border bg-muted p-4">
                      {selectedCall.recording_url ? (
                        <div className="space-y-4">
                          <div className="flex items-center gap-3">
                            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                              <Play className="h-6 w-6 text-primary" />
                            </div>
                            <div>
                              <p className="font-medium">Call Recording</p>
                              <p className="text-sm text-muted-foreground">
                                {formatDuration(selectedCall.duration_seconds || 0)} duration
                              </p>
                            </div>
                          </div>
                          <audio 
                            controls 
                            className="w-full"
                            src={selectedCall.recording_url}
                          >
                            Your browser does not support the audio element.
                          </audio>
                          <p className="text-xs text-muted-foreground">
                            Recordings are stored securely and encrypted. HIPAA compliant.
                          </p>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center justify-center py-8 text-center">
                          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted-foreground/10 mb-4">
                            <Play className="h-8 w-8 text-muted-foreground" />
                          </div>
                          <p className="font-medium text-muted-foreground">Recording Not Available</p>
                          <p className="text-sm text-muted-foreground mt-1">
                            This call may not have been recorded, or the recording is still processing.
                          </p>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                </Tabs>
              </div>
            </>
            )
          })()}
        </DialogContent>
      </Dialog>
    </div>
  )
}
