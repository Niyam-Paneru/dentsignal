import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000' // DevSkim: ignore DS137138

export async function POST(request: NextRequest) {
  try {
    // Auth check - verify the request is from an authenticated user
    const supabase = await createClient()
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    
    if (authError || !user) {
      return NextResponse.json(
        { detail: 'Authentication required' },
        { status: 401 }
      )
    }

    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/api/transfer/initiate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(process.env.BACKEND_API_KEY && { 'X-API-Key': process.env.BACKEND_API_KEY }),
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('Transfer API error:', error)
    return NextResponse.json(
      { detail: 'Failed to connect to transfer service' },
      { status: 503 }
    )
  }
}
