'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  ChevronLeft, 
  ChevronRight, 
  Calendar as CalendarIcon,
  Clock,
  User,
  Bot,
  AlertTriangle,
  Loader2
} from 'lucide-react'
import { getAppointmentsForDate, getWeekAppointmentCounts } from '@/lib/api/dental'
import type { Appointment } from '@/types/database'

const statusConfig: Record<string, { label: string; className: string }> = {
  scheduled: { label: 'Scheduled', className: 'bg-blue-100 border-blue-200 dark:bg-blue-900/30 dark:border-blue-800' },
  confirmed: { label: 'Confirmed', className: 'bg-green-100 border-green-200 dark:bg-green-900/30 dark:border-green-800' },
  completed: { label: 'Completed', className: 'bg-gray-100 border-gray-200 dark:bg-gray-900/30 dark:border-gray-800' },
  open: { label: 'Open', className: 'bg-gray-50 border-gray-200 border-dashed dark:bg-gray-900/30 dark:border-gray-800' },
  blocked: { label: 'Blocked', className: 'bg-gray-100 border-gray-300 dark:bg-gray-800 dark:border-gray-700' },
  cancelled: { label: 'Cancelled', className: 'bg-red-50 border-red-200 dark:bg-red-900/30 dark:border-red-800' },
  no_show: { label: 'No Show', className: 'bg-red-50 border-red-200 dark:bg-red-900/30 dark:border-red-800' },
}

const defaultStatus = { label: 'Unknown', className: 'bg-gray-50 border-gray-200 dark:bg-gray-900/30 dark:border-gray-800' }

interface WeekDay {
  day: string
  date: number
  fullDate: Date
  count: number
  capacity: number
  isToday: boolean
  warning: boolean
}

export default function CalendarPage() {
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [weekDays, setWeekDays] = useState<WeekDay[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      setLoading(true)
      try {
        const [dayAppointments, weekCounts] = await Promise.all([
          getAppointmentsForDate(selectedDate),
          getWeekAppointmentCounts()
        ])
        setAppointments(dayAppointments)
        
        const today = new Date()
        const todayDate = today.getDate()
        
        const startOfWeek = new Date(today)
        startOfWeek.setDate(today.getDate() - today.getDay() + 1) // Monday
        
        const days: WeekDay[] = weekCounts.map((w, i) => {
          const fullDate = new Date(startOfWeek)
          fullDate.setDate(startOfWeek.getDate() + i)
          return {
            day: w.day,
            date: w.date,
            fullDate,
            count: w.count,
            capacity: w.capacity,
            isToday: w.date === todayDate,
            warning: w.capacity > 90,
          }
        })
        setWeekDays(days)
      } catch (error) {
        console.error('Failed to load calendar data:', error)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [selectedDate])

  const currentMonth = selectedDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
  const selectedDayLabel = selectedDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
  
  const bookedByAI = appointments.filter(a => a.call_id).length
  const totalSlots = appointments.length
  const confirmedSlots = appointments.filter(a => a.status === 'confirmed' || a.status === 'scheduled').length

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
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Appointment Calendar</h1>
          <p className="text-muted-foreground">View and manage AI-booked appointments</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon">
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button variant="outline" className="min-w-[160px]">
            <CalendarIcon className="mr-2 h-4 w-4" />
            {currentMonth}
          </Button>
          <Button variant="outline" size="icon">
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Week View */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle>Week View</CardTitle>
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-1">
                <div className="h-3 w-3 rounded-full bg-green-500" />
                <span className="text-muted-foreground">AI Booked</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="h-3 w-3 rounded-full bg-blue-500" />
                <span className="text-muted-foreground">Manual</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="h-3 w-3 rounded-full bg-gray-300" />
                <span className="text-muted-foreground">Open</span>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-6 gap-2">
            {weekDays.map((day) => (
              <button
                key={day.date}
                onClick={() => setSelectedDate(day.fullDate)}
                className={`rounded-lg border p-3 text-center transition-colors hover:bg-muted ${
                  selectedDate.getDate() === day.date ? 'border-primary bg-primary/5' : ''
                } ${day.isToday ? 'ring-2 ring-primary ring-offset-2' : ''}`}
              >
                <p className="text-sm font-medium text-muted-foreground">{day.day}</p>
                <p className={`text-2xl font-bold ${day.isToday ? 'text-primary' : ''}`}>{day.date}</p>
                <div className="mt-1 flex items-center justify-center gap-1">
                  <span className="text-xs text-muted-foreground">{day.count} appts</span>
                  {day.warning && (
                    <AlertTriangle className="h-3 w-3 text-orange-500" />
                  )}
                </div>
                <div className="mt-1 h-1.5 w-full rounded-full bg-gray-200 dark:bg-gray-700">
                  <div 
                    className={`h-full rounded-full ${day.capacity > 90 ? 'bg-orange-500' : 'bg-green-500'}`}
                    style={{ width: `${Math.min(day.capacity, 100)}%` }}
                  />
                </div>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Capacity Warning */}
      <Card className="border-orange-200 bg-orange-50 dark:border-orange-900 dark:bg-orange-950">
        <CardContent className="flex items-center gap-3 py-4">
          <AlertTriangle className="h-5 w-5 text-orange-600" />
          <div>
            <p className="font-medium text-orange-800 dark:text-orange-200">
              Wednesday Dec 11: 95% Capacity
            </p>
            <p className="text-sm text-orange-700 dark:text-orange-300">
              Only 1 slot remaining. AI will inform callers of limited availability.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Day Schedule */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Schedule */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{selectedDayLabel}</CardTitle>
                <CardDescription>Scheduled Appointments</CardDescription>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold">{bookedByAI}</p>
                <p className="text-xs text-muted-foreground">Booked by AI</p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {appointments.length === 0 ? (
              <div className="flex h-32 items-center justify-center text-muted-foreground">
                No appointments scheduled for this day
              </div>
            ) : (
            <div className="space-y-2">
              {appointments.map((apt) => {
                const status = statusConfig[apt.status] || defaultStatus
                return (
                <div
                  key={apt.id}
                  className={`flex items-center justify-between rounded-lg border p-3 ${status.className}`}
                >
                  <div className="flex items-center gap-3">
                    <div className="text-center">
                      <Clock className="mx-auto h-4 w-4 text-muted-foreground" />
                      <p className="mt-1 text-sm font-medium">{apt.scheduled_time}</p>
                    </div>
                    <div className="h-10 w-px bg-border" />
                    <div>
                      <p className="font-medium">{apt.patient_name || 'Unknown Patient'}</p>
                      <p className="text-sm text-muted-foreground">
                        {apt.service_type}
                      </p>
                    </div>
                  </div>
                  <Badge 
                    variant="outline" 
                    className={apt.call_id ? 'border-green-500 text-green-700' : 'border-blue-500 text-blue-700'}
                  >
                    {apt.call_id ? (
                      <>
                        <Bot className="mr-1 h-3 w-3" />
                        AI Booked
                      </>
                    ) : (
                      <>
                        <User className="mr-1 h-3 w-3" />
                        Manual
                      </>
                    )}
                  </Badge>
                </div>
                )
              })}
            </div>
            )}
          </CardContent>
        </Card>

        {/* Stats Sidebar */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Day Stats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Total Appointments</span>
                <span className="font-medium">{totalSlots}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Confirmed</span>
                <span className="font-medium text-green-600">{confirmedSlots}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">AI Booked</span>
                <span className="font-medium text-primary">{bookedByAI}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Google Calendar</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm">
                <div className="h-2 w-2 rounded-full bg-green-500" />
                <span className="text-muted-foreground">Synced 2 min ago</span>
              </div>
              <Button variant="outline" size="sm" className="mt-3 w-full">
                Sync Now
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
