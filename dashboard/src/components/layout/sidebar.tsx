'use client'

import Link from 'next/link'
import Image from 'next/image'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  Phone,
  PhoneCall,
  Calendar,
  Settings,
  BarChart3,
  LogOut,
  Menu,
  Shield,
  CreditCard,
  Sparkles,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useState, useEffect, useCallback } from 'react'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { createClient } from '@/lib/supabase/client'
import { Badge } from '@/components/ui/badge'

// Super Admin emails - only platform owner(s)
const SUPER_ADMIN_EMAILS = [
  'founder@dentsignal.me',
]

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Live Calls', href: '/live-calls', icon: PhoneCall, showActiveCount: true },
  { name: 'Calls', href: '/calls', icon: Phone },
  { name: 'Recalls', href: '/recalls', icon: Sparkles },
  { name: 'Calendar', href: '/calendar', icon: Calendar },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
]

// Super Admin only (platform owner)
const adminNavigation = [
  { name: 'Super Admin', href: '/superadmin', icon: Shield },
]

function NavLinks({ onItemClick, isSuperAdmin, activeCallCount = 0 }: { onItemClick?: () => void; isSuperAdmin?: boolean; activeCallCount?: number }) {
  const pathname = usePathname()

  return (
    <nav className="flex flex-col gap-1">
      {navigation.map((item) => {
        const isActive = pathname.startsWith(item.href)
        const showBadge = item.showActiveCount && activeCallCount > 0
        
        return (
          <Link
            key={item.name}
            href={item.href}
            onClick={onItemClick}
            aria-current={isActive ? 'page' : undefined}
            className={cn(
              'flex items-center justify-between rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
              isActive
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            )}
          >
            <span className="flex items-center gap-3">
              <item.icon className="h-5 w-5" aria-hidden="true" />
              {item.name}
            </span>
            {showBadge && (
              <Badge
                className="bg-destructive text-destructive-foreground text-xs px-1.5 py-0 min-w-[20px] h-5 flex items-center justify-center animate-pulse"
                aria-label={`${activeCallCount} active calls`}
              >
                {activeCallCount}
              </Badge>
            )}
          </Link>
        )
      })}
      
      {/* Super Admin Section - Only show to admins */}
      {isSuperAdmin && (
        <div className="mt-4 pt-4 border-t">
          <p className="px-3 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Platform Admin
          </p>
          {adminNavigation.map((item) => {
            const isActive = pathname.startsWith(item.href)
            return (
              <Link
                  key={item.name}
                  href={item.href}
                  onClick={onItemClick}
                  aria-current={isActive ? 'page' : undefined}
                  className={cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                    isActive
                      ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  )}
                >
                  <item.icon className="h-5 w-5" aria-hidden="true" />
                  {item.name}
              </Link>
          )
        })}
        </div>
      )}
    </nav>
  )
}

interface UserInfo {
  email: string | null
  clinicName: string | null
  clinicId: string | null
  subscriptionStatus: string | null
  subscriptionExpiresAt: Date | null
  planType: string | null
}

export function Sidebar() {
  const [open, setOpen] = useState(false)
  const [isSuperAdmin, setIsSuperAdmin] = useState(false)
  const [activeCallCount, setActiveCallCount] = useState(0)
  const [userInfo, setUserInfo] = useState<UserInfo>({ 
    email: null, 
    clinicName: null, 
    clinicId: null,
    subscriptionStatus: null,
    subscriptionExpiresAt: null,
    planType: null
  })
  const [loading, setLoading] = useState(true)

  // Fetch active call count
  const fetchActiveCallCount = useCallback(async (clinicId: string) => {
    const supabase = createClient()
    const { count } = await supabase
      .from('dental_calls')
      .select('*', { count: 'exact', head: true })
      .eq('clinic_id', clinicId)
      .eq('status', 'in_progress')
    
    setActiveCallCount(count || 0)
  }, [])
  
  // Check if user is a super admin and get user/clinic info
  useEffect(() => {
    const loadUserData = async () => {
      const supabase = createClient()
      const { data: { user } } = await supabase.auth.getUser()
      
      if (user?.email) {
        const isAdmin = SUPER_ADMIN_EMAILS.map(e => e.toLowerCase()).includes(user.email.toLowerCase())
        setIsSuperAdmin(isAdmin)
        
        // Get user's clinic from database with subscription info
        const { data: clinicData } = await supabase
          .from('dental_clinics')
          .select('id, name, subscription_status, subscription_expires_at, plan_type')
          .eq('owner_id', user.id)
          .single()
        
        setUserInfo({
          email: user.email,
          clinicName: clinicData?.name || null,
          clinicId: clinicData?.id || null,
          subscriptionStatus: clinicData?.subscription_status || null,
          subscriptionExpiresAt: clinicData?.subscription_expires_at ? new Date(clinicData.subscription_expires_at) : null,
          planType: clinicData?.plan_type || null,
        })

        // Fetch initial active call count
        if (clinicData?.id) {
          fetchActiveCallCount(clinicData.id)
        }
      }
      setLoading(false)
    }
    
    loadUserData()
  }, [fetchActiveCallCount])

  // Real-time subscription for active calls
  useEffect(() => {
    if (!userInfo.clinicId) return

    const supabase = createClient()
    
    // Subscribe to call status changes
    const channel = supabase
      .channel('active-calls-count')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'dental_calls',
          filter: `clinic_id=eq.${userInfo.clinicId}`,
        },
        () => {
          // Refetch count on any change
          fetchActiveCallCount(userInfo.clinicId!)
        }
      )
      .subscribe()

    // Also poll every 5 seconds as a fallback
    const interval = setInterval(() => {
      fetchActiveCallCount(userInfo.clinicId!)
    }, 5000)

    return () => {
      supabase.removeChannel(channel)
      clearInterval(interval)
    }
  }, [userInfo.clinicId, fetchActiveCallCount])

  return (
    <>
      {/* Mobile menu button */}
      <div className="fixed left-4 top-4 z-50 lg:hidden">
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild>
            <Button variant="outline" size="icon" aria-label="Open navigation menu">
              <Menu className="h-5 w-5" aria-hidden="true" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0">
            <div className="flex h-full flex-col">
              <div className="flex h-16 items-center gap-2 border-b px-6">
                <Image src="/icon.svg" alt="DentSignal" width={32} height={32} className="rounded" />
                <span className="font-semibold">DentSignal</span>
              </div>
              <div className="flex-1 overflow-auto p-4">
                <NavLinks onItemClick={() => setOpen(false)} isSuperAdmin={isSuperAdmin} activeCallCount={activeCallCount} />
              </div>
              <div className="border-t p-4">
                <Button variant="ghost" className="w-full justify-start gap-3" asChild>
                  <Link href="/logout">
                    <LogOut className="h-5 w-5" aria-hidden="true" />
                    Sign Out
                  </Link>
                </Button>
              </div>
            </div>
          </SheetContent>
        </Sheet>
      </div>

      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 border-r bg-card lg:block">
        <div className="flex h-full flex-col">
          <div className="flex h-16 items-center gap-2 border-b px-6">
            <Image src="/icon.svg" alt="DentSignal" width={32} height={32} className="rounded" />
            <span className="text-lg font-semibold">DentSignal</span>
          </div>
          <div className="flex-1 overflow-auto p-4">
            <NavLinks isSuperAdmin={isSuperAdmin} activeCallCount={activeCallCount} />
          </div>
          <div className="border-t p-4">
            <div className="mb-4 rounded-lg bg-muted p-3">
              <p className="text-xs font-medium text-muted-foreground">Current Clinic</p>
              <p className="text-sm font-medium truncate">
                {loading ? 'Loading...' : (userInfo.clinicName || 'No clinic assigned')}
              </p>
              {userInfo.email && (
                <p className="text-xs text-muted-foreground truncate mt-1">
                  {userInfo.email}
                </p>
              )}
              {/* Subscription Status */}
              {userInfo.subscriptionStatus && (
                <div className="mt-2 pt-2 border-t border-border/50">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">Plan</span>
                      <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                        userInfo.subscriptionStatus === 'active'
                          ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                          : userInfo.subscriptionStatus === 'trial'
                          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                          : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                      }`}>
                        {userInfo.subscriptionStatus === 'trial' ? 'Trial' :
                         userInfo.subscriptionStatus === 'active' ? 'Active' :
                         'Expired'}
                      </span>
                    </div>
                  {userInfo.subscriptionExpiresAt && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {userInfo.subscriptionStatus === 'active' || userInfo.subscriptionStatus === 'trial' 
                        ? 'Renews' 
                        : 'Expired'}: {userInfo.subscriptionExpiresAt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </p>
                  )}
                </div>
              )}
            </div>
            <Link
              href="/settings?tab=billing"
              className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground mb-3 px-1"
            >
              <CreditCard className="h-3.5 w-3.5" aria-hidden="true" />
              Manage Billing
            </Link>
            <Button variant="ghost" className="w-full justify-start gap-3" asChild>
              <Link href="/logout">
                <LogOut className="h-5 w-5" aria-hidden="true" />
                Sign Out
              </Link>
            </Button>
          </div>
        </div>
      </aside>
    </>
  )
}
