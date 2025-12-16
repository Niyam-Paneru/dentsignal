'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Phone, CalendarCheck, TrendingUp, PhoneMissed, ArrowUpRight, ArrowDownRight, Loader2, Building2 } from 'lucide-react'
import { RecentCallsTable } from '@/components/dashboard/recent-calls-table'
import { CallsChart } from '@/components/dashboard/calls-chart'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { getDashboardStats, getRecentCalls, getCallTrends, getClinic } from '@/lib/api/dental'
import type { DashboardStats, RecentCall, CallTrendData, Clinic } from '@/types/database'

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
  const [loading, setLoading] = useState(true)
  const [noClinic, setNoClinic] = useState(false)
  const [dateRange, setDateRange] = useState(7)

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
        
        const [statsData, callsData, trendsData] = await Promise.all([
          getDashboardStats(dateRange),
          getRecentCalls(5),
          getCallTrends(dateRange)
        ])
        setStats(statsData)
        setRecentCalls(callsData)
        setChartData(trendsData)
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
      {/* Header */}
      <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
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
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
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
          title="Missed Calls"
          value={stats.missedCalls}
          trend={-20}
          icon={PhoneMissed}
          trendLabel="fewer than avg"
        />
      </div>

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
