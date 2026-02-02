'use client'

import { SessionTimeout } from '@/components/auth/session-timeout'

/**
 * Dashboard Client Wrapper
 * 
 * Contains client-side functionality for the dashboard:
 * - Session timeout (HIPAA auto-logoff requirement)
 * - Future: Activity tracking, real-time notifications
 */
export function DashboardClientWrapper({ children }: { children: React.ReactNode }) {
  return (
    <>
      {/* HIPAA-required session timeout */}
      <SessionTimeout />
      
      {/* Dashboard content */}
      {children}
    </>
  )
}
