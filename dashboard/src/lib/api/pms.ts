import { createClient } from '@/lib/supabase/client'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000' // DevSkim: ignore DS137138

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

// Helper to make authenticated requests to the backend
async function pmsRequest(path: string, options: RequestInit = {}) {
  const clinicId = await getUserClinicId()
  if (!clinicId) throw new Error('No clinic found')
  
  const url = `${API_URL}/api/pms${path}`
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-Clinic-ID': clinicId,
    ...((options.headers as Record<string, string>) || {}),
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

// Types
export interface PMSConfig {
  provider: string
  is_active: boolean
  od_api_mode: string
  od_base_url: string
  od_clinic_num: number | null
  od_permission_tier: string
  connection_status: string
  sync_appointments: boolean
  sync_patients: boolean
  auto_create_patients: boolean
  last_sync_at: string | null
  updated_at: string
}

export interface ConnectionTestResult {
  success: boolean
  message: string
  details: {
    api_mode: string
    server_version?: string
    provider_count?: number
    operatory_count?: number
    error?: string
  }
}

export interface PMSStatus {
  provider: string
  is_active: boolean
  connection_status: string
  last_sync_at: string | null
  sync_appointments: boolean
  sync_patients: boolean
  auto_create_patients: boolean
}

// API functions

export async function getPMSConfig(): Promise<PMSConfig | null> {
  try {
    return await pmsRequest('/config')
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error)
    if (message.includes('404') || message.includes('not configured')) return null
    throw error
  }
}

export async function savePMSConfig(config: {
  provider: string
  customer_key: string
  api_mode?: string
  base_url?: string
  clinic_num?: number
}): Promise<PMSConfig> {
  return pmsRequest('/config', {
    method: 'POST',
    body: JSON.stringify(config),
  })
}

export async function deletePMSConfig(): Promise<void> {
  await pmsRequest('/config', { method: 'DELETE' })
}

export async function testPMSConnection(): Promise<ConnectionTestResult> {
  return pmsRequest('/test-connection', { method: 'POST' })
}

export async function updatePMSSettings(settings: {
  sync_appointments?: boolean
  sync_patients?: boolean
  auto_create_patients?: boolean
}): Promise<PMSConfig> {
  return pmsRequest('/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  })
}

export async function getPMSStatus(): Promise<PMSStatus> {
  return pmsRequest('/status')
}

export async function getPMSProviders(): Promise<Array<{
  id: number
  name: string
  abbreviation: string
  is_hidden: boolean
}>> {
  return pmsRequest('/providers')
}

export async function getPMSOperatories(): Promise<Array<{
  id: number
  name: string
  abbreviation: string
  is_hidden: boolean
}>> {
  return pmsRequest('/operatories')
}
