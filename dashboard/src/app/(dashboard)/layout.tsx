import { Sidebar } from '@/components/layout/sidebar'
import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import { SubscriptionBannerWrapper } from '@/components/dashboard/subscription-banner-wrapper'
import { DashboardClientWrapper } from '@/components/dashboard/dashboard-client-wrapper'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Server-side auth check (backup to middleware)
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  
  if (!user) {
    redirect('/login')
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="lg:pl-64">
        <DashboardClientWrapper>
          <div className="container mx-auto p-6 lg:p-8">
            <SubscriptionBannerWrapper />
            {children}
          </div>
        </DashboardClientWrapper>
      </main>
    </div>
  )
}
