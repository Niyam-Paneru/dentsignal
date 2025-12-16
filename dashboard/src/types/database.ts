// Database types for the dental dashboard
export interface Clinic {
  id: string
  name: string
  phone: string
  twilio_number: string
  address: string | null
  business_hours: BusinessHours
  created_at: string
  owner_id: string
}

export interface BusinessHours {
  monday: { open: string; close: string } | null
  tuesday: { open: string; close: string } | null
  wednesday: { open: string; close: string } | null
  thursday: { open: string; close: string } | null
  friday: { open: string; close: string } | null
  saturday: { open: string; close: string } | null
  sunday: { open: string; close: string } | null
}

export interface ClinicSettings {
  clinic_id: string
  agent_name: string
  agent_voice: string
  greeting_template: string
  services: string[]
  dentist_names: string[]
}

export interface Call {
  id: string
  clinic_id: string
  caller_phone: string
  started_at: string
  ended_at: string | null
  duration_seconds: number | null
  outcome: string
  call_reason?: string
  transcript: string | null
  recording_url: string | null
  sentiment: 'positive' | 'neutral' | 'negative' | null
  patient_id: string | null
  summary: string | null
}

export interface Appointment {
  id: string
  clinic_id: string
  patient_id: string | null
  call_id: string | null
  scheduled_date: string
  scheduled_time: string
  service_type: string
  status: 'scheduled' | 'confirmed' | 'completed' | 'cancelled' | 'no_show'
  google_event_id: string | null
  created_at: string
  patient_name: string | null
  patient_phone: string | null
}

export interface Patient {
  id: string
  clinic_id: string
  first_name: string
  last_name: string
  phone: string
  email: string | null
  date_of_birth: string | null
  insurance_provider: string | null
  notes: string | null
  created_at: string
}

// Dashboard stats types
export interface DashboardStats {
  totalCalls: number
  bookedAppointments: number
  successRate: number
  missedCalls: number
  callsTrend: number // percentage change from previous period
  bookingsTrend: number
}

export interface CallTrendData {
  date: string
  calls: number
  booked: number
}

export interface RecentCall {
  id: string
  time: string
  caller_phone: string
  reason: string
  outcome: string
  duration: string
}
