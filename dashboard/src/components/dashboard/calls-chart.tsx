'use client'

import { 
  DynamicBarChart, 
  DynamicResponsiveContainer, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend 
} from '@/components/charts/dynamic-charts'
import { BarChart3 } from 'lucide-react'

interface CallsChartProps {
  data: {
    date: string
    calls: number
    booked: number
  }[]
}

export function CallsChart({ data }: CallsChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex h-[300px] flex-col items-center justify-center text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted mb-3">
          <BarChart3 className="h-6 w-6 text-muted-foreground" />
        </div>
        <p className="text-sm font-medium text-muted-foreground">No call data yet</p>
        <p className="text-xs text-muted-foreground mt-1 max-w-[200px]">
          Call trends will appear here once your AI starts handling calls
        </p>
      </div>
    )
  }

  return (
    <div className="h-[300px] w-full">
      <DynamicResponsiveContainer width="100%" height="100%">
        <DynamicBarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis 
            dataKey="date" 
            className="text-xs"
            tick={{ fill: 'hsl(var(--muted-foreground))' }}
          />
          <YAxis 
            className="text-xs"
            tick={{ fill: 'hsl(var(--muted-foreground))' }}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#ffffff',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              color: '#1a202c',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            }}
            labelStyle={{ color: '#1a202c', fontWeight: 600 }}
            itemStyle={{ color: '#1a202c' }}
            cursor={{ fill: 'rgba(0, 0, 0, 0.05)' }}
          />
          <Legend />
          <Bar 
            dataKey="calls" 
            name="Total Calls"
            fill="hsl(var(--primary))" 
            radius={[4, 4, 0, 0]}
          />
          <Bar 
            dataKey="booked" 
            name="Booked"
            fill="hsl(142, 76%, 36%)" 
            radius={[4, 4, 0, 0]}
          />
        </DynamicBarChart>
      </DynamicResponsiveContainer>
    </div>
  )
}
