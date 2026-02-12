'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { requireClient } from '@/lib/supabase/client'
import { Loader2 } from 'lucide-react'

export default function LogoutPage() {
  const router = useRouter()
  const supabase = requireClient()

  useEffect(() => {
    const handleLogout = async () => {
      await supabase.auth.signOut()
      router.push('/login')
      router.refresh()
    }
    handleLogout()
  }, [router, supabase.auth])

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-white dark:from-gray-900 dark:to-gray-950">
      <div className="text-center">
        <Loader2 className="mx-auto h-8 w-8 animate-spin text-primary" />
        <p className="mt-4 text-muted-foreground">Signing out...</p>
      </div>
    </div>
  )
}
