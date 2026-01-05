'use client'

import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Phone, CalendarCheck, TrendingUp, PhoneMissed, ArrowUpRight, ArrowDownRight, Loader2, Building2, DollarSign, Clock, PhoneCall, PhoneForwarded } from 'lucide-react'
import { RecentCallsTable } from '@/components/dashboard/recent-calls-table'
import { CallsChart } from '@/components/dashboard/calls-chart'
import { OnboardingProgress } from '@/components/dashboard/onboarding-progress'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { getDashboardStats, getRecentCalls, getCallTrends, getClinic, getClinicSettings, getActiveCalls } from '@/lib/api/dental'
import type { DashboardStats, RecentCall, CallTrendData, Clinic } from '@/types/database'
import { createClient } from '@/lib/supabase/client'

interface ActiveCall {
  id: string
  caller_phone: string
  status: string
  started_at: string
  caller_name?: string
  call_type?: string
}

function StatCard({ 
  title, 
  value, 
  trend, 
  icon: Icon,
  trendLabel = 'vs last week'
}: { 
  title: string
  value: string | number
  trend?: number
  icon: React.ElementType
  trendLabel?: string
}) {
  const isPositive = trend && trend > 0
  const isNegative = trend && trend < 0

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {trend !== undefined && (
          <p className={`flex items-center text-xs ${isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-muted-foreground'}`}>
            {isPositive ? <ArrowUpRight className="mr-1 h-3 w-3" /> : isNegative ? <ArrowDownRight className="mr-1 h-3 w-3" /> : null}
            {isPositive ? '+' : ''}{trend}% {trendLabel}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentCalls, setRecentCalls] = useState<RecentCall[]>([])
  const [chartData, setChartData] = useState<CallTrendData[]>([])
  const [clinic, setClinic] = useState<Clinic | null>(null)
  const [activeCalls, setActiveCalls] = useState<ActiveCall[]>([])
  const [loading, setLoading] = useState(true)
  const [noClinic, setNoClinic] = useState(false)
  const [dateRange, setDateRange] = useState(7)
  const [hasCustomGreeting, setHasCustomGreeting] = useState(false)
  const [hasForwarding, setHasForwarding] = useState(false)

  // Fetch active calls
  const fetchActiveCalls = useCallback(async () => {
    try {
      const calls = await getActiveCalls()
      setActiveCalls(calls || [])
    } catch (error) {
      console.error('Failed to fetch active calls:', error)
    }
  }, [])

  // Format call duration
  const formatDuration = (startedAt: string) => {
    const start = new Date(startedAt)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - start.getTime()) / 1000)
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Real-time subscription for active calls
  useEffect(() => {
    if (!clinic?.id) return

    const supabase = createClient()
    
    // Subscribe to call status changes
    const channel = supabase
      .channel('dashboard-active-calls')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'dental_calls',
          filter: `clinic_id=eq.${clinic.id}`,
        },
        () => {
          fetchActiveCalls()
        }
      )
      .subscribe()

    // Initial fetch
    fetchActiveCalls()

    // Poll every 5 seconds for duration updates
    const interval = setInterval(fetchActiveCalls, 5000)

    return () => {
      supabase.removeChannel(channel)
      clearInterval(interval)
    }
  }, [clinic?.id, fetchActiveCalls])

  useEffect(() => {
    async function loadData() {
      setLoading(true)
      try {
        // First check if user has a clinic
        const clinicData = await getClinic()
        if (!clinicData) {
          setNoClinic(true)
          setLoading(false)
          return
        }
        setClinic(clinicData)
        
        const [statsData, callsData, trendsData, settingsData] = await Promise.all([
          getDashboardStats(dateRange),
          getRecentCalls(5),
          getCallTrends(dateRange),
          getClinicSettings()
        ])
        setStats(statsData)
        setRecentCalls(callsData)
        setChartData(trendsData)
        
        // Check onboarding status
        setHasCustomGreeting(!!settingsData?.greeting_template)
        setHasForwarding(!!clinicData?.twilio_number)
      } catch (error) {
        console.error('Failed to load dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [dateRange])

  const currentDate = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })

  if (loading || !stats) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  // Show setup message if no clinic assigned
  if (noClinic) {
    return (
      <div className="flex h-[calc(100vh-200px)] items-center justify-center">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
              <Building2 className="h-8 w-8 text-primary" />
            </div>
            <CardTitle className="text-2xl">Welcome to Dental AI!</CardTitle>
            <CardDescription>
              Your account is set up, but you don&apos;t have a clinic configured yet.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center space-y-4">
            <p className="text-sm text-muted-foreground">
              To get started, a clinic needs to be linked to your account. This is typically done by the platform administrator.
            </p>
            <div className="rounded-lg bg-muted p-4 text-left">
              <p className="text-sm font-medium mb-2">Next steps:</p>
              <ol className="text-sm text-muted-foreground space-y-1 list-decimal list-inside">
                <li>Contact your administrator</li>
                <li>They will create your clinic in the database</li>
                <li>Once linked, refresh this page</li>
              </ol>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Onboarding Progress - shows until complete */}
      <OnboardingProgress
        clinicName={clinic?.name}
        hasForwardingSetup={hasForwarding}
        hasCustomGreeting={hasCustomGreeting}
        hasFirstCall={stats.totalCalls > 0}
      />

      {/* Header */}
      <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">
              {clinic?.name ? `Welcome, ${clinic.name}!` : 'Dashboard'}
            </h1>
            {/* Live Status Indicator */}
            {hasForwarding && stats.totalCalls > 0 && (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-100 dark:bg-green-900 border border-green-200 dark:border-green-800">
                <span className="flex h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-xs font-medium text-green-700 dark:text-green-300">You're Live</span>
              </div>
            )}
            {hasForwarding && stats.totalCalls === 0 && (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-100 dark:bg-amber-900 border border-amber-200 dark:border-amber-800">
                <span className="flex h-2 w-2 rounded-full bg-amber-500" />
                <span className="text-xs font-medium text-amber-700 dark:text-amber-300">Waiting for first call</span>
              </div>
            )}
            {!hasForwarding && (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
                <span className="flex h-2 w-2 rounded-full bg-gray-400" />
                <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Setup Required</span>
              </div>
            )}
          </div>
          <p className="text-muted-foreground">{currentDate}</p>
        </div>
        <Tabs value={dateRange.toString()} onValueChange={(v) => setDateRange(parseInt(v))} className="w-auto">
          <TabsList>
            <TabsTrigger value="1">Today</TabsTrigger>
            <TabsTrigger value="7">7 Days</TabsTrigger>
            <TabsTrigger value="30">30 Days</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <StatCard
          title="Total Calls"
          value={stats.totalCalls}
          trend={stats.callsTrend}
          icon={Phone}
        />
        <StatCard
          title="Appointments Booked"
          value={stats.bookedAppointments}
          trend={stats.bookingsTrend}
          icon={CalendarCheck}
        />
        <StatCard
          title="Success Rate"
          value={`${stats.successRate}%`}
          trend={5}
          icon={TrendingUp}
        />
        <StatCard
          title="Revenue Recovered"
          value={`$${stats.revenueRecovered.toLocaleString()}`}
          icon={DollarSign}
        />
        <StatCard
          title="Avg Call Duration"
          value={stats.avgCallDuration}
          icon={Clock}
        />
        <StatCard
          title="Missed Calls"
          value={stats.missedCalls}
          trend={-20}
          icon={PhoneMissed}
          trendLabel="fewer than avg"
        />
      </div>

      {/* Active Calls Widget */}
      {activeCalls.length > 0 && (
        <Card className="border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <PhoneCall className="h-5 w-5 text-green-600 animate-pulse" />
                <CardTitle className="text-green-800 dark:text-green-200">
                  Live Calls ({activeCalls.length})
                </CardTitle>
              </div>
              <Button asChild size="sm" variant="outline" className="border-green-300 hover:bg-green-100">
                <Link href="/live-calls">View All</Link>
              </Button>
            </div>
            <CardDescription className="text-green-700 dark:text-green-300">
              Currently active calls being handled by AI
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {activeCalls.slice(0, 3).map((call) => (
                <div 
                  key={call.id} 
                  className="flex items-center justify-between rounded-lg bg-white dark:bg-green-900/50 p-3 shadow-sm"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 dark:bg-green-800">
                      <Phone className="h-5 w-5 text-green-600 dark:text-green-300" />
                    </div>
                    <div>
                      <p className="font-medium text-sm">
                        {call.caller_name || call.caller_phone || 'Unknown Caller'}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {call.call_type || 'General Inquiry'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant="outline" className="bg-green-100 text-green-700 border-green-200">
                      {formatDuration(call.started_at)}
                    </Badge>
                    <Button 
                      size="sm" 
                      variant="ghost"
                      className="text-green-700 hover:text-green-900 hover:bg-green-100"
                      asChild
                    >
                      <Link href={`/live-calls?call=${call.id}`}>
                        <PhoneForwarded className="h-4 w-4 mr-1" />
                        Monitor
                      </Link>
                    </Button>
                  </div>
                </div>
              ))}
              {activeCalls.length > 3 && (
                <p className="text-center text-sm text-green-600 pt-2">
                  +{activeCalls.length - 3} more active {activeCalls.length - 3 === 1 ? 'call' : 'calls'}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Charts and Recent Calls */}
      <div className="grid gap-6 lg:grid-cols-7">
        {/* Chart */}
        <Card className="lg:col-span-4">
          <CardHeader>
            <CardTitle>Call Trends</CardTitle>
            <CardDescription>
              Calls vs appointments booked this week
            </CardDescription>
          </CardHeader>
          <CardContent>
            <CallsChart data={chartData} />
          </CardContent>
        </Card>

        {/* Recent Calls */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Recent Calls</CardTitle>
            <CardDescription>
              Latest calls handled by AI
            </CardDescription>
          </CardHeader>
          <CardContent>
            <RecentCallsTable calls={recentCalls} />
          </CardContent>
        </Card>
      </div>

      {/* Alerts Section */}
      <Card className="border-orange-200 bg-orange-50 dark:border-orange-900 dark:bg-orange-950">
        <CardHeader className="pb-2">
          <CardTitle className="text-orange-800 dark:text-orange-200">⚠️ Alerts</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-orange-700 dark:text-orange-300">
          <ul className="list-disc space-y-1 pl-4">
            <li>Wednesday capacity: 95% full (3 open slots remaining)</li>
            <li>&quot;Insurance not covered&quot; asked 5x this week - consider updating prompt</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
