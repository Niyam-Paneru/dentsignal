import { createClient } from '@/lib/supabase/client'
import type { 
  Call, 
  Appointment, 
  DashboardStats, 
  CallTrendData,
  RecentCall 
} from '@/types/database'

// Get the user's clinic ID dynamically
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

export async function getDashboardStats(days: number = 7): Promise<DashboardStats> {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    console.warn('No clinic found for user')
    return {
      totalCalls: 0,
      bookedAppointments: 0,
      successRate: 0,
      missedCalls: 0,
      callsTrend: 0,
      bookingsTrend: 0,
      revenueRecovered: 0,
      avgCallDuration: '0:00',
    }
  }

  const startDate = new Date()
  startDate.setDate(startDate.getDate() - days)

  const { data: calls, error } = await supabase
    .from('dental_calls')
    .select('outcome, duration_seconds')
    .eq('clinic_id', clinicId)
    .gte('started_at', startDate.toISOString())

  if (error) {
    console.error('Error fetching stats:', error)
    return {
      totalCalls: 0,
      bookedAppointments: 0,
      successRate: 0,
      missedCalls: 0,
      callsTrend: 0,
      bookingsTrend: 0,
      revenueRecovered: 0,
      avgCallDuration: '0:00',
    }
  }

  const totalCalls = calls?.length || 0
  const bookedAppointments = calls?.filter(c => c.outcome === 'booked').length || 0
  const missedCalls = calls?.filter(c => c.outcome === 'missed').length || 0
  const successRate = totalCalls > 0 ? Math.round((bookedAppointments / totalCalls) * 100) : 0
  
  // Calculate revenue recovered: avg dental appointment = $350
  const avgAppointmentValue = 350
  const revenueRecovered = bookedAppointments * avgAppointmentValue
  
  // Calculate average call duration
  const totalDuration = calls?.reduce((sum, c) => sum + (c.duration_seconds || 0), 0) || 0
  const avgDurationSeconds = totalCalls > 0 ? Math.round(totalDuration / totalCalls) : 0
  const avgMins = Math.floor(avgDurationSeconds / 60)
  const avgSecs = avgDurationSeconds % 60
  const avgCallDuration = `${avgMins}:${avgSecs.toString().padStart(2, '0')}`

  return {
    totalCalls,
    bookedAppointments,
    successRate,
    missedCalls,
    callsTrend: 15, // TODO: Calculate from previous period
    bookingsTrend: 12,
    revenueRecovered,
    avgCallDuration,
  }
}

export async function getRecentCalls(limit: number = 5): Promise<RecentCall[]> {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    return []
  }

  const { data, error } = await supabase
    .from('dental_calls')
    .select('id, started_at, caller_phone, call_reason, outcome, duration_seconds')
    .eq('clinic_id', clinicId)
    .order('started_at', { ascending: false })
    .limit(limit)

  if (error) {
    console.error('Error fetching recent calls:', error)
    return []
  }

  return (data || []).map(call => ({
    id: call.id,
    time: new Date(call.started_at).toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    }),
    caller_phone: call.caller_phone || 'Unknown',
    reason: call.call_reason || 'Unknown',
    outcome: call.outcome as RecentCall['outcome'],
    duration: formatDuration(call.duration_seconds || 0),
  }))
}

export interface ActiveCall {
  id: string
  caller_phone: string
  status: string
  started_at: string
  caller_name?: string
  call_type?: string
}

export async function getActiveCalls(): Promise<ActiveCall[]> {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    return []
  }

  const { data, error } = await supabase
    .from('dental_calls')
    .select('id, caller_phone, status, started_at, caller_name, call_reason')
    .eq('clinic_id', clinicId)
    .eq('status', 'in_progress')
    .order('started_at', { ascending: false })

  if (error) {
    console.error('Error fetching active calls:', error)
    return []
  }

  return (data || []).map(call => ({
    id: call.id,
    caller_phone: call.caller_phone || 'Unknown',
    status: call.status,
    started_at: call.started_at,
    caller_name: call.caller_name,
    call_type: call.call_reason,
  }))
}

export async function getCallTrends(days: number = 7): Promise<CallTrendData[]> {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    return []
  }

  const startDate = new Date()
  startDate.setDate(startDate.getDate() - days)

  const { data, error } = await supabase
    .from('dental_calls')
    .select('started_at, outcome')
    .eq('clinic_id', clinicId)
    .gte('started_at', startDate.toISOString())
    .order('started_at', { ascending: true })

  if (error) {
    console.error('Error fetching call trends:', error)
    return []
  }

  // Group by day
  const grouped = (data || []).reduce((acc, call) => {
    const date = new Date(call.started_at).toLocaleDateString('en-US', { weekday: 'short' })
    if (!acc[date]) {
      acc[date] = { calls: 0, booked: 0 }
    }
    acc[date].calls++
    if (call.outcome === 'booked') {
      acc[date].booked++
    }
    return acc
  }, {} as Record<string, { calls: number; booked: number }>)

  return Object.entries(grouped).map(([date, stats]) => ({
    date,
    calls: stats.calls,
    booked: stats.booked,
  }))
}

export async function getAllCalls(): Promise<Call[]> {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    return []
  }

  const { data, error } = await supabase
    .from('dental_calls')
    .select('*')
    .eq('clinic_id', clinicId)
    .order('started_at', { ascending: false })

  if (error) {
    console.error('Error fetching calls:', error)
    return []
  }

  return data || []
}

export async function getAppointments(startDate?: Date, endDate?: Date): Promise<Appointment[]> {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    return []
  }

  let query = supabase
    .from('dental_appointments')
    .select('*')
    .eq('clinic_id', clinicId)
    .order('scheduled_date', { ascending: true })
    .order('scheduled_time', { ascending: true })

  if (startDate) {
    query = query.gte('scheduled_date', startDate.toISOString().split('T')[0])
  }
  if (endDate) {
    query = query.lte('scheduled_date', endDate.toISOString().split('T')[0])
  }

  const { data, error } = await query

  if (error) {
    console.error('Error fetching appointments:', error)
    return []
  }

  return data || []
}

export async function getAppointmentsForDate(date: Date): Promise<Appointment[]> {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    return []
  }

  const dateStr = date.toISOString().split('T')[0]
  
  const { data, error } = await supabase
    .from('dental_appointments')
    .select('*')
    .eq('clinic_id', clinicId)
    .eq('scheduled_date', dateStr)
    .order('scheduled_time', { ascending: true })

  if (error) {
    console.error('Error fetching appointments:', error)
    return []
  }

  return data || []
}

export async function getWeekAppointmentCounts(): Promise<{ date: number; day: string; count: number; capacity: number }[]> {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    return []
  }

  const today = new Date()
  const startOfWeek = new Date(today)
  startOfWeek.setDate(today.getDate() - today.getDay() + 1) // Monday
  
  const results = []
  
  for (let i = 0; i < 6; i++) { // Mon-Sat
    const date = new Date(startOfWeek)
    date.setDate(startOfWeek.getDate() + i)
    const dateStr = date.toISOString().split('T')[0]
    
    const { count } = await supabase
      .from('dental_appointments')
      .select('*', { count: 'exact', head: true })
      .eq('clinic_id', clinicId)
      .eq('scheduled_date', dateStr)
    
    const maxSlots = i === 5 ? 6 : 10 // Saturday has fewer slots
    results.push({
      date: date.getDate(),
      day: date.toLocaleDateString('en-US', { weekday: 'short' }),
      count: count || 0,
      capacity: Math.round(((count || 0) / maxSlots) * 100),
    })
  }
  
  return results
}

export async function getOutcomeDistribution(): Promise<{ name: string; value: number; color: string }[]> {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    return []
  }

  const { data, error } = await supabase
    .from('dental_calls')
    .select('outcome')
    .eq('clinic_id', clinicId)

  if (error || !data) {
    console.error('Error fetching outcome distribution:', error)
    return []
  }

  const colors: Record<string, string> = {
    booked: '#22c55e',
    inquiry: '#3b82f6',
    info: '#3b82f6',
    transfer: '#f97316',
    transferred: '#f97316',
    cancelled: '#9ca3af',
    missed: '#ef4444',
    failed: '#ef4444',
  }

  const counts = data.reduce((acc, call) => {
    const outcome = call.outcome || 'unknown'
    acc[outcome] = (acc[outcome] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return Object.entries(counts).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
    color: colors[name] || '#9ca3af',
  }))
}

export async function getServiceTypeStats(): Promise<{ name: string; count: number; percentage: number }[]> {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    return []
  }

  const { data, error } = await supabase
    .from('dental_appointments')
    .select('service_type')
    .eq('clinic_id', clinicId)

  if (error || !data) {
    console.error('Error fetching service stats:', error)
    return []
  }

  const counts = data.reduce((acc, apt) => {
    const service = apt.service_type || 'Other'
    acc[service] = (acc[service] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const total = data.length || 1
  return Object.entries(counts)
    .map(([name, count]) => ({
      name,
      count,
      percentage: Math.round((count / total) * 100),
    }))
    .sort((a, b) => b.count - a.count)
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// Settings functions
export async function getClinicSettings() {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    return null
  }

  const { data, error } = await supabase
    .from('dental_clinic_settings')
    .select('*')
    .eq('clinic_id', clinicId)
    .single()

  if (error) {
    console.error('Error fetching settings:', error)
    return null
  }

  return data
}

export async function getClinic() {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    return null
  }

  const { data, error } = await supabase
    .from('dental_clinics')
    .select('*')
    .eq('id', clinicId)
    .single()

  if (error) {
    console.error('Error fetching clinic:', error)
    return null
  }

  return data
}

export async function updateClinicSettings(settings: {
  agent_name?: string
  agent_voice?: string
  greeting_template?: string
  services_offered?: string[]
  personality_traits?: string[]
  max_call_duration?: number
  transfer_keywords?: string[]
}) {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    return false
  }

  const { error } = await supabase
    .from('dental_clinic_settings')
    .update(settings)
    .eq('clinic_id', clinicId)

  if (error) {
    console.error('Error updating settings:', error)
    return false
  }

  return true
}

export async function updateClinicInfo(info: {
  name?: string
  phone?: string
  address?: string
  owner_phone?: string
  transfer_enabled?: boolean
  transfer_timeout_seconds?: number
}) {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    return false
  }

  const { error } = await supabase
    .from('dental_clinics')
    .update(info)
    .eq('id', clinicId)

  if (error) {
    console.error('Error updating clinic info:', error)
    return false
  }

  return true
}

// Analytics functions
export async function getWeeklyCallStats(): Promise<{ day: string; calls: number; booked: number; transferred: number; missed: number }[]> {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    return []
  }

  const startDate = new Date()
  startDate.setDate(startDate.getDate() - 7)

  const { data, error } = await supabase
    .from('dental_calls')
    .select('started_at, outcome')
    .eq('clinic_id', clinicId)
    .gte('started_at', startDate.toISOString())

  if (error || !data) {
    return []
  }

  const dayOrder = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  const grouped = dayOrder.reduce((acc, day) => {
    acc[day] = { calls: 0, booked: 0, transferred: 0, missed: 0 }
    return acc
  }, {} as Record<string, { calls: number; booked: number; transferred: number; missed: number }>)

  data.forEach(call => {
    const day = new Date(call.started_at).toLocaleDateString('en-US', { weekday: 'short' })
    if (grouped[day]) {
      grouped[day].calls++
      if (call.outcome === 'booked') grouped[day].booked++
      if (call.outcome === 'transferred' || call.outcome === 'transfer') grouped[day].transferred++
      if (call.outcome === 'missed' || call.outcome === 'failed') grouped[day].missed++
    }
  })

  return dayOrder.map(day => ({ day, ...grouped[day] }))
}

export async function getMonthlyTrend(): Promise<{ week: string; calls: number; bookingRate: number }[]> {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    return []
  }

  const startDate = new Date()
  startDate.setDate(startDate.getDate() - 28)

  const { data, error } = await supabase
    .from('dental_calls')
    .select('started_at, outcome')
    .eq('clinic_id', clinicId)
    .gte('started_at', startDate.toISOString())

  if (error || !data) {
    return []
  }

  const weeks: { week: string; calls: number; booked: number }[] = [
    { week: 'Week 1', calls: 0, booked: 0 },
    { week: 'Week 2', calls: 0, booked: 0 },
    { week: 'Week 3', calls: 0, booked: 0 },
    { week: 'Week 4', calls: 0, booked: 0 },
  ]

  const now = new Date()
  data.forEach(call => {
    const callDate = new Date(call.started_at)
    const daysAgo = Math.floor((now.getTime() - callDate.getTime()) / (1000 * 60 * 60 * 24))
    const weekIndex = Math.min(3, Math.floor(daysAgo / 7))
    weeks[3 - weekIndex].calls++
    if (call.outcome === 'booked') weeks[3 - weekIndex].booked++
  })

  return weeks.map(w => ({
    week: w.week,
    calls: w.calls,
    bookingRate: w.calls > 0 ? Math.round((w.booked / w.calls) * 100) : 0,
  }))
}

export async function getPeakHours(): Promise<{ hour: string; calls: number }[]> {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    return []
  }

  const startDate = new Date()
  startDate.setDate(startDate.getDate() - 30)

  const { data, error } = await supabase
    .from('dental_calls')
    .select('started_at')
    .eq('clinic_id', clinicId)
    .gte('started_at', startDate.toISOString())

  if (error || !data) {
    return []
  }

  const hours: Record<number, number> = {}
  for (let i = 8; i <= 17; i++) {
    hours[i] = 0
  }

  data.forEach(call => {
    const hour = new Date(call.started_at).getHours()
    if (hour >= 8 && hour <= 17) {
      hours[hour]++
    }
  })

  return Object.entries(hours).map(([h, calls]) => ({
    hour: `${parseInt(h) > 12 ? parseInt(h) - 12 : h} ${parseInt(h) >= 12 ? 'PM' : 'AM'}`,
    calls,
  }))
}

export async function getAnalyticsSummary(): Promise<{
  totalCalls: number
  bookingRate: number
  avgDuration: string
  estimatedRevenue: number
  callsTrend: number
  bookingTrend: number
}> {
  const supabase = createClient()
  const clinicId = await getUserClinicId()
  
  if (!clinicId) {
    return { totalCalls: 0, bookingRate: 0, avgDuration: '0:00', estimatedRevenue: 0, callsTrend: 0, bookingTrend: 0 }
  }

  const startDate = new Date()
  startDate.setDate(startDate.getDate() - 7)

  const { data, error } = await supabase
    .from('dental_calls')
    .select('outcome, duration_seconds')
    .eq('clinic_id', clinicId)
    .gte('started_at', startDate.toISOString())

  if (error || !data) {
    return { totalCalls: 0, bookingRate: 0, avgDuration: '0:00', estimatedRevenue: 0, callsTrend: 0, bookingTrend: 0 }
  }

  const totalCalls = data.length
  const bookedCalls = data.filter(c => c.outcome === 'booked').length
  const bookingRate = totalCalls > 0 ? Math.round((bookedCalls / totalCalls) * 100) : 0
  const totalDuration = data.reduce((sum, c) => sum + (c.duration_seconds || 0), 0)
  const avgSeconds = totalCalls > 0 ? Math.round(totalDuration / totalCalls) : 0
  const avgDuration = `${Math.floor(avgSeconds / 60)}:${(avgSeconds % 60).toString().padStart(2, '0')}`
  const estimatedRevenue = bookedCalls * 150 // $150 per appointment average

  return {
    totalCalls,
    bookingRate,
    avgDuration,
    estimatedRevenue,
    callsTrend: 15, // TODO: Calculate from previous period
    bookingTrend: 8,
  }
}
