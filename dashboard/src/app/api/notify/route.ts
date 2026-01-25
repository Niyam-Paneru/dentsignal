import { NextResponse } from 'next/server'

const SLACK_BOT_TOKEN = process.env.SLACK_BOT_TOKEN
const SLACK_CHANNEL = process.env.SLACK_CHANNEL || '#dentsignal-alerts'

export async function POST(request: Request) {
  try {
    const { type, data } = await request.json()
    
    if (!SLACK_BOT_TOKEN) {
      console.warn('SLACK_BOT_TOKEN not configured')
      return NextResponse.json({ ok: true, skipped: true })
    }
    
    let message = ''
    let emoji = '🔔'
    
    switch (type) {
      case 'signup':
        emoji = '🎉'
        message = `*New Signup!*\n• Email: \`${data.email}\`\n• Name: ${data.name}\n• Clinic: ${data.clinic}\n• Time: ${new Date().toISOString()}`
        break
      case 'call_completed':
        emoji = '📞'
        message = `*Call Completed*\n• Duration: ${data.duration}s\n• Booked: ${data.booked ? 'Yes ✅' : 'No'}`
        break
      case 'error':
        emoji = '🚨'
        message = `*Error Alert*\n• Error: \`${data.error}\`\n• Context: ${data.context || 'N/A'}`
        break
      default:
        message = data.message || 'Notification'
    }
    
    const response = await fetch('https://slack.com/api/chat.postMessage', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${SLACK_BOT_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        channel: SLACK_CHANNEL,
        text: `${emoji} ${message}`,
        mrkdwn: true,
      }),
    })
    
    const result = await response.json()
    
    if (!result.ok) {
      console.error('Slack API error:', result.error)
      return NextResponse.json({ ok: false, error: result.error }, { status: 500 })
    }
    
    return NextResponse.json({ ok: true })
  } catch (error) {
    console.error('Slack notification error:', error)
    return NextResponse.json({ ok: false, error: 'Internal error' }, { status: 500 })
  }
}
