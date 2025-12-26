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
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useState, useEffect } from 'react'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { createClient } from '@/lib/supabase/client'

// Super Admin emails - only platform owner(s)
const SUPER_ADMIN_EMAILS = [
  'niyampaneru79@gmail.com',
]

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Live Calls', href: '/live-calls', icon: PhoneCall },
  { name: 'Calls', href: '/calls', icon: Phone },
  { name: 'Calendar', href: '/calendar', icon: Calendar },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
]

// Super Admin only (platform owner)
const adminNavigation = [
  { name: 'Super Admin', href: '/superadmin', icon: Shield },
]

function NavLinks({ onItemClick, isSuperAdmin }: { onItemClick?: () => void; isSuperAdmin?: boolean }) {
  const pathname = usePathname()

  return (
    <nav className="flex flex-col gap-1">
      {navigation.map((item) => {
        const isActive = pathname.startsWith(item.href)
        return (
          <Link
            key={item.name}
            href={item.href}
            onClick={onItemClick}
            className={cn(
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              isActive
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            )}
          >
            <item.icon className="h-5 w-5" />
            {item.name}
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
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-[#1B3A7C] text-white'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )}
              >
                <item.icon className="h-5 w-5" />
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
}

export function Sidebar() {
  const [open, setOpen] = useState(false)
  const [isSuperAdmin, setIsSuperAdmin] = useState(false)
  const [userInfo, setUserInfo] = useState<UserInfo>({ email: null, clinicName: null, clinicId: null })
  const [loading, setLoading] = useState(true)
  
  // Check if user is a super admin and get user/clinic info
  useEffect(() => {
    const loadUserData = async () => {
      const supabase = createClient()
      const { data: { user } } = await supabase.auth.getUser()
      
      if (user?.email) {
        const isAdmin = SUPER_ADMIN_EMAILS.map(e => e.toLowerCase()).includes(user.email.toLowerCase())
        setIsSuperAdmin(isAdmin)
        
        // Get user's clinic from database
        const { data: clinicData } = await supabase
          .from('dental_clinics')
          .select('id, name')
          .eq('owner_id', user.id)
          .single()
        
        setUserInfo({
          email: user.email,
          clinicName: clinicData?.name || null,
          clinicId: clinicData?.id || null,
        })
      }
      setLoading(false)
    }
    
    loadUserData()
  }, [])

  return (
    <>
      {/* Mobile menu button */}
      <div className="fixed left-4 top-4 z-50 lg:hidden">
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild>
            <Button variant="outline" size="icon">
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0">
            <div className="flex h-full flex-col">
              <div className="flex h-16 items-center gap-2 border-b px-6">
                <Image src="/favicon.png" alt="DentSignal" width={32} height={32} className="rounded" />
                <span className="font-semibold">DentSignal</span>
              </div>
              <div className="flex-1 overflow-auto p-4">
                <NavLinks onItemClick={() => setOpen(false)} isSuperAdmin={isSuperAdmin} />
              </div>
              <div className="border-t p-4">
                <Button variant="ghost" className="w-full justify-start gap-3" asChild>
                  <Link href="/logout">
                    <LogOut className="h-5 w-5" />
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
            <Image src="/favicon.png" alt="DentSignal" width={32} height={32} className="rounded" />
            <span className="text-lg font-semibold">DentSignal</span>
          </div>
          <div className="flex-1 overflow-auto p-4">
            <NavLinks isSuperAdmin={isSuperAdmin} />
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
            </div>
            <Button variant="ghost" className="w-full justify-start gap-3" asChild>
              <Link href="/logout">
                <LogOut className="h-5 w-5" />
                Sign Out
              </Link>
            </Button>
          </div>
        </div>
      </aside>
    </>
  )
}
