'use client'

import dynamic from 'next/dynamic'
import { Loader2 } from 'lucide-react'

// Loading placeholder for charts
function ChartLoadingFallback() {
  return (
    <div className="flex h-full min-h-[200px] items-center justify-center">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
    </div>
  )
}

// Dynamically import recharts components to reduce initial bundle size
export const DynamicBarChart = dynamic(
  () => import('recharts').then((mod) => mod.BarChart),
  { ssr: false, loading: ChartLoadingFallback }
)

export const DynamicLineChart = dynamic(
  () => import('recharts').then((mod) => mod.LineChart),
  { ssr: false, loading: ChartLoadingFallback }
)

export const DynamicAreaChart = dynamic(
  () => import('recharts').then((mod) => mod.AreaChart),
  { ssr: false, loading: ChartLoadingFallback }
)

export const DynamicPieChart = dynamic(
  () => import('recharts').then((mod) => mod.PieChart),
  { ssr: false, loading: ChartLoadingFallback }
)

export const DynamicResponsiveContainer = dynamic(
  () => import('recharts').then((mod) => mod.ResponsiveContainer),
  { ssr: false }
)

// Re-export static components that don't need dynamic loading
export { 
  Bar, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  Pie, 
  Cell,
  Area
} from 'recharts'
