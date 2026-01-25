'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  DynamicBarChart,
  DynamicLineChart,
  DynamicPieChart,
  DynamicResponsiveContainer,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Pie,
  Cell,
  Legend,
} from '@/components/charts/dynamic-charts'
import { TrendingUp, DollarSign, Clock, Phone, Loader2, Building2 } from 'lucide-react'
import { 
  getWeeklyCallStats, 
  getMonthlyTrend, 
  getPeakHours, 
  getOutcomeDistribution,
  getServiceTypeStats,
  getAnalyticsSummary,
  getClinic,
  getRevenueAttribution,
  type RevenueAttribution
} from '@/lib/api/dental'

const tooltipStyle = {
  contentStyle: { 
    backgroundColor: '#ffffff',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    color: '#1a202c',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  },
  labelStyle: { color: '#1a202c', fontWeight: 600 },
  itemStyle: { color: '#1a202c' },
  cursor: { fill: 'rgba(0, 0, 0, 0.05)' },
}

function StatCard({ 
  title, 
  value, 
  subtitle,
  icon: Icon,
  trend,
}: { 
  title: string
  value: string | number
  subtitle: string
  icon: React.ElementType
  trend?: { value: number; label: string }
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
        {trend && (
          <p className={`mt-1 text-xs ${trend.value > 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend.value > 0 ? '↑' : '↓'} {Math.abs(trend.value)}% {trend.label}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

export default function AnalyticsPage() {
  const [loading, setLoading] = useState(true)
  const [noClinic, setNoClinic] = useState(false)
  const [weeklyData, setWeeklyData] = useState<{ day: string; calls: number; booked: number; transferred: number; missed: number }[]>([])
  const [monthlyTrend, setMonthlyTrend] = useState<{ week: string; calls: number; bookingRate: number }[]>([])
  const [peakHoursData, setPeakHoursData] = useState<{ hour: string; calls: number }[]>([])
  const [outcomeData, setOutcomeData] = useState<{ name: string; value: number; color: string }[]>([])
  const [serviceData, setServiceData] = useState<{ name: string; count: number; percentage: number }[]>([])
  const [summary, setSummary] = useState({ totalCalls: 0, bookingRate: 0, avgDuration: '0:00', estimatedRevenue: 0, callsTrend: 0, bookingTrend: 0 })
  const [revenueData, setRevenueData] = useState<RevenueAttribution | null>(null)

  useEffect(() => {
    async function loadData() {
      setLoading(true)
      try {
        const clinic = await getClinic()
        if (!clinic) {
          setNoClinic(true)
          setLoading(false)
          return
        }

        const [weekly, monthly, peak, outcomes, services, stats, revenue] = await Promise.all([
          getWeeklyCallStats(),
          getMonthlyTrend(),
          getPeakHours(),
          getOutcomeDistribution(),
          getServiceTypeStats(),
          getAnalyticsSummary(),
          getRevenueAttribution(30),
        ])

        setWeeklyData(weekly)
        setMonthlyTrend(monthly)
        setPeakHoursData(peak)
        setOutcomeData(outcomes)
        setServiceData(services)
        setSummary(stats)
        setRevenueData(revenue)
      } catch (error) {
        console.error('Failed to load analytics:', error)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (noClinic) {
    return (
      <div className="flex h-[calc(100vh-200px)] items-center justify-center">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
              <Building2 className="h-8 w-8 text-primary" />
            </div>
            <CardTitle className="text-2xl">No Clinic Found</CardTitle>
            <CardDescription>
              Your account doesn&apos;t have a clinic linked yet. Contact your administrator to set up your clinic.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  const hasData = weeklyData.some(d => d.calls > 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground">Performance insights for your AI receptionist</p>
        </div>
        <Tabs defaultValue="week">
          <TabsList>
            <TabsTrigger value="week">This Week</TabsTrigger>
            <TabsTrigger value="month">This Month</TabsTrigger>
            <TabsTrigger value="year">This Year</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Top Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Calls"
          value={summary.totalCalls}
          subtitle="This week"
          icon={Phone}
          trend={{ value: summary.callsTrend, label: 'vs last week' }}
        />
        <StatCard
          title="Booking Rate"
          value={`${summary.bookingRate}%`}
          subtitle={`appointments booked`}
          icon={TrendingUp}
          trend={{ value: summary.bookingTrend, label: 'vs last week' }}
        />
        <StatCard
          title="Avg Call Duration"
          value={summary.avgDuration}
          subtitle="minutes per call"
          icon={Clock}
        />
        <StatCard
          title="Estimated Revenue"
          value={`$${summary.estimatedRevenue.toLocaleString()}`}
          subtitle="from AI bookings"
          icon={DollarSign}
          trend={{ value: 22, label: 'vs last week' }}
        />
      </div>

      {!hasData ? (
        <Card className="p-12 text-center">
          <div className="mx-auto w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
            <Phone className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold mb-2">No Call Data Yet</h3>
          <p className="text-muted-foreground max-w-md mx-auto">
            Once your AI receptionist starts handling calls, you&apos;ll see detailed analytics and insights here.
          </p>
        </Card>
      ) : (
        <>
          {/* Charts Row 1 */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Weekly Calls Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Weekly Call Volume</CardTitle>
                <CardDescription>Calls and bookings by day</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  <DynamicResponsiveContainer width="100%" height="100%">
                    <DynamicBarChart data={weeklyData}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis dataKey="day" tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                      <YAxis tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                      <Tooltip {...tooltipStyle} />
                      <Legend />
                      <Bar dataKey="calls" name="Total Calls" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="booked" name="Booked" fill="#22c55e" radius={[4, 4, 0, 0]} />
                    </DynamicBarChart>
                  </DynamicResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Outcome Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Call Outcomes</CardTitle>
                <CardDescription>Distribution of call results</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  {outcomeData.length > 0 ? (
                    <DynamicResponsiveContainer width="100%" height="100%">
                      <DynamicPieChart>
                        <Pie
                          data={outcomeData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={2}
                          dataKey="value"
                          label={({ name, percent }) => `${name ?? ''} ${((percent ?? 0) * 100).toFixed(0)}%`}
                        >
                          {outcomeData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={tooltipStyle.contentStyle} />
                      </DynamicPieChart>
                    </DynamicResponsiveContainer>
                  ) : (
                    <div className="flex h-full items-center justify-center text-muted-foreground">
                      No outcome data available
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts Row 2 */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Peak Hours */}
            <Card>
              <CardHeader>
                <CardTitle>Peak Calling Hours</CardTitle>
                <CardDescription>When most calls come in</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  {peakHoursData.length > 0 ? (
                    <DynamicResponsiveContainer width="100%" height="100%">
                      <DynamicBarChart data={peakHoursData} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis type="number" tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                        <YAxis dataKey="hour" type="category" tick={{ fill: 'hsl(var(--muted-foreground))' }} width={50} />
                        <Tooltip {...tooltipStyle} />
                        <Bar dataKey="calls" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} />
                      </DynamicBarChart>
                    </DynamicResponsiveContainer>
                  ) : (
                    <div className="flex h-full items-center justify-center text-muted-foreground">
                      No hourly data available
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Booking Trend */}
            <Card>
              <CardHeader>
                <CardTitle>Booking Rate Trend</CardTitle>
                <CardDescription>Weekly booking rate progression</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  {monthlyTrend.length > 0 ? (
                    <DynamicResponsiveContainer width="100%" height="100%">
                      <DynamicLineChart data={monthlyTrend}>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                        <XAxis dataKey="week" tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                        <YAxis tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                        <Tooltip {...tooltipStyle} />
                        <Legend />
                        <Line 
                          type="monotone" 
                          dataKey="bookingRate" 
                          name="Booking Rate %" 
                          stroke="#22c55e" 
                          strokeWidth={2}
                          dot={{ fill: '#22c55e' }}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="calls" 
                          name="Total Calls" 
                          stroke="hsl(var(--primary))" 
                          strokeWidth={2}
                          dot={{ fill: 'hsl(var(--primary))' }}
                        />
                      </DynamicLineChart>
                    </DynamicResponsiveContainer>
                  ) : (
                    <div className="flex h-full items-center justify-center text-muted-foreground">
                      No trend data available
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Service Types */}
          {serviceData.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Top Services Requested</CardTitle>
                <CardDescription>Most common appointment types</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {serviceData.slice(0, 6).map((service) => (
                    <div key={service.name} className="flex items-center gap-4">
                      <div className="w-32 text-sm font-medium">{service.name}</div>
                      <div className="flex-1">
                        <div className="h-4 w-full rounded-full bg-muted">
                          <div 
                            className="h-full rounded-full bg-primary"
                            style={{ width: `${service.percentage}%` }}
                          />
                        </div>
                      </div>
                      <div className="w-20 text-right text-sm text-muted-foreground">
                        {service.count} ({service.percentage}%)
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* ROI Calculator */}
          <Card className="border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950">
            <CardHeader>
              <CardTitle className="text-green-800 dark:text-green-200">💰 ROI Summary</CardTitle>
              <CardDescription className="text-green-700 dark:text-green-300">
                Value generated by your AI receptionist this week
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-3">
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-700 dark:text-green-300">${summary.estimatedRevenue.toLocaleString()}</p>
                  <p className="text-sm text-green-600 dark:text-green-400">Revenue from AI bookings</p>
                  <p className="text-xs text-green-500">($150 avg per appointment)</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-700 dark:text-green-300">{Math.round(summary.totalCalls * 3 / 60)} hrs</p>
                  <p className="text-sm text-green-600 dark:text-green-400">Staff time saved</p>
                  <p className="text-xs text-green-500">({summary.totalCalls} calls × 3 min avg)</p>
                </div>
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-700 dark:text-green-300">${Math.round(summary.totalCalls * 3 / 60 * 25)}</p>
                  <p className="text-sm text-green-600 dark:text-green-400">Labor cost savings</p>
                  <p className="text-xs text-green-500">($25/hr staff rate)</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Revenue Attribution Dashboard */}
          {revenueData && revenueData.totalRevenue > 0 && (
            <>
              {/* Revenue Attribution Header */}
              <Card className="border-indigo-200 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-950 dark:to-purple-950">
                <CardHeader>
                  <CardTitle className="text-indigo-800 dark:text-indigo-200 flex items-center gap-2">
                    📊 Revenue Attribution
                  </CardTitle>
                  <CardDescription className="text-indigo-600 dark:text-indigo-300">
                    Detailed breakdown of AI-generated revenue (last 30 days)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-6 md:grid-cols-4">
                    <div className="text-center p-4 bg-white dark:bg-indigo-900/50 rounded-lg">
                      <p className="text-3xl font-bold text-indigo-700 dark:text-indigo-300">
                        ${revenueData.totalRevenue.toLocaleString()}
                      </p>
                      <p className="text-sm text-indigo-600 dark:text-indigo-400">Total Revenue</p>
                    </div>
                    <div className="text-center p-4 bg-white dark:bg-indigo-900/50 rounded-lg">
                      <p className="text-3xl font-bold text-indigo-700 dark:text-indigo-300">
                        ${revenueData.avgRevenuePerCall.toLocaleString()}
                      </p>
                      <p className="text-sm text-indigo-600 dark:text-indigo-400">Avg Revenue/Booking</p>
                    </div>
                    <div className="text-center p-4 bg-white dark:bg-indigo-900/50 rounded-lg">
                      <p className="text-3xl font-bold text-indigo-700 dark:text-indigo-300">
                        ${revenueData.conversionValue.toLocaleString()}
                      </p>
                      <p className="text-sm text-indigo-600 dark:text-indigo-400">Value per Call</p>
                    </div>
                    <div className="text-center p-4 bg-white dark:bg-indigo-900/50 rounded-lg">
                      <p className="text-3xl font-bold text-indigo-700 dark:text-indigo-300">
                        {revenueData.byService.reduce((sum, s) => sum + s.appointments, 0)}
                      </p>
                      <p className="text-sm text-indigo-600 dark:text-indigo-400">Total Bookings</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Revenue Charts Row */}
              <div className="grid gap-6 lg:grid-cols-2">
                {/* Revenue by Service Type */}
                <Card>
                  <CardHeader>
                    <CardTitle>Revenue by Service</CardTitle>
                    <CardDescription>Which procedures generate the most revenue</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {revenueData.byService.slice(0, 6).map((service) => (
                        <div key={service.serviceType} className="flex items-center gap-4">
                          <div className="w-28 text-sm font-medium truncate">{service.serviceType}</div>
                          <div className="flex-1">
                            <div className="h-6 w-full rounded-full bg-muted overflow-hidden">
                              <div 
                                className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 flex items-center justify-end pr-2"
                                style={{ width: `${Math.max(service.percentage, 10)}%` }}
                              >
                                <span className="text-xs text-white font-medium">{service.percentage}%</span>
                              </div>
                            </div>
                          </div>
                          <div className="w-24 text-right">
                            <span className="text-sm font-semibold">${service.revenue.toLocaleString()}</span>
                            <span className="text-xs text-muted-foreground block">{service.appointments} appts</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Revenue by Day of Week */}
                <Card>
                  <CardHeader>
                    <CardTitle>Revenue by Day</CardTitle>
                    <CardDescription>Best performing days of the week</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[250px]">
                      <DynamicResponsiveContainer width="100%" height="100%">
                        <DynamicBarChart data={revenueData.byDayOfWeek}>
                          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                          <XAxis dataKey="day" tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                          <YAxis tick={{ fill: 'hsl(var(--muted-foreground))' }} tickFormatter={(v) => `$${v}`} />
                          <Tooltip 
                            {...tooltipStyle}
                            formatter={(value) => [`$${Number(value).toLocaleString()}`, 'Revenue']}
                          />
                          <Bar dataKey="revenue" fill="#6366f1" radius={[4, 4, 0, 0]} />
                        </DynamicBarChart>
                      </DynamicResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* New vs Returning Patients */}
              <div className="grid gap-6 lg:grid-cols-3">
                <Card className="lg:col-span-1">
                  <CardHeader>
                    <CardTitle>Patient Mix</CardTitle>
                    <CardDescription>New vs returning patient revenue</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[200px]">
                      <DynamicResponsiveContainer width="100%" height="100%">
                        <DynamicPieChart>
                          <Pie
                            data={revenueData.newVsReturning}
                            cx="50%"
                            cy="50%"
                            innerRadius={50}
                            outerRadius={80}
                            dataKey="revenue"
                            nameKey="type"
                            label={({ name, percent }) => `${name?.split(' ')[0]} ${((percent ?? 0) * 100).toFixed(0)}%`}
                          >
                            <Cell fill="#22c55e" />
                            <Cell fill="#3b82f6" />
                          </Pie>
                          <Tooltip 
                            formatter={(value) => [`$${Number(value).toLocaleString()}`, '']}
                          />
                        </DynamicPieChart>
                      </DynamicResponsiveContainer>
                    </div>
                    <div className="flex justify-center gap-6 mt-4">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-green-500" />
                        <span className="text-sm">New</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-blue-500" />
                        <span className="text-sm">Returning</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Revenue by Hour */}
                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle>Revenue by Appointment Time</CardTitle>
                    <CardDescription>When high-value appointments are scheduled</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[200px]">
                      <DynamicResponsiveContainer width="100%" height="100%">
                        <DynamicLineChart data={revenueData.byHour}>
                          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                          <XAxis dataKey="hour" tick={{ fill: 'hsl(var(--muted-foreground))' }} />
                          <YAxis tick={{ fill: 'hsl(var(--muted-foreground))' }} tickFormatter={(v) => `$${v}`} />
                          <Tooltip 
                            {...tooltipStyle}
                            formatter={(value) => [`$${Number(value).toLocaleString()}`, 'Revenue']}
                          />
                          <Line 
                            type="monotone" 
                            dataKey="revenue" 
                            stroke="#6366f1" 
                            strokeWidth={2}
                            dot={{ fill: '#6366f1' }}
                          />
                        </DynamicLineChart>
                      </DynamicResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
