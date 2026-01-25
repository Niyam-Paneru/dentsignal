/**
 * Celebratory UX copy for dashboard notifications
 * Rotates randomly to create variable rewards
 * 
 * TONE DISTRIBUTION:
 * - Validation (60%): Make user feel seen + accomplished
 * - Data (25%): Reinforce ROI + competence without emotion
 * - Playful (15%): Break monotony with subtle wit
 */

export type CelebrationTone = 'validation' | 'data' | 'playful'
export type CelebrationCategory = 'booking' | 'emergency' | 'quality' | 'noshow' | 'recovered' | 'rescheduled' | 'positive_sentiment'

export interface CelebrationMessage {
  id: string
  tone: CelebrationTone
  text: string
}

// Tone weights for random selection
export const TONE_WEIGHTS = {
  validation: 0.60,
  data: 0.25,
  playful: 0.15,
}

export const BOOKING_CONFIRMED_MESSAGES: CelebrationMessage[] = [
  // Validation (60%)
  { id: 'bc_v1', tone: 'validation', text: "That call was going to voicemail. Now it's locked in your calendar. You're welcome. 🙌" },
  { id: 'bc_v2', tone: 'validation', text: "Patient saved from the void. One more person walking through your door. 📅" },
  { id: 'bc_v3', tone: 'validation', text: "Another win for your AI. Your team: undefeated today. ✅" },
  { id: 'bc_v4', tone: 'validation', text: "That patient was one second away from calling your competitor. Bullet dodged. 🎯" },
  { id: 'bc_v5', tone: 'validation', text: "Another human saved from the voicemail void. Your AI's track record: perfect. 🏆" },
  { id: 'bc_v6', tone: 'validation', text: "One more appointment means one less empty chair next week. 📈" },
  { id: 'bc_v7', tone: 'validation', text: "Appointment booked while you were doing literally anything else. Automation wins. 🎉" },
  { id: 'bc_v8', tone: 'validation', text: "One more patient means one more smile in that chair. 😊" },
  { id: 'bc_v9', tone: 'validation', text: "Call captured. Appointment locked. Revenue protected. ✨" },
  // Data (25%)
  { id: 'bc_d1', tone: 'data', text: "New appointment booked. That's $850+ walking through your door. 💰" },
  { id: 'bc_d2', tone: 'data', text: "Your AI just did in 30 seconds what would take your team 5 minutes. ⚡" },
  { id: 'bc_d3', tone: 'data', text: "Phone rings → patient books → everyone wins. Math checks out. ✅" },
  { id: 'bc_d4', tone: 'data', text: "Patient didn't hang up. Patient didn't call back later. Patient booked right now. 🔥" },
  // Playful (15%)
  { id: 'bc_p1', tone: 'playful', text: "Your AI now has an official seat at the staff table. Salary: $199/month. Vacation: none. 🤖" },
  { id: 'bc_p2', tone: 'playful', text: "Your receptionist just answered a call, booked an appointment, and took zero break. That's your AI. 🚀" },
]

export const EMERGENCY_HANDLED_MESSAGES: CelebrationMessage[] = [
  // Validation (60%)
  { id: 'eh_v1', tone: 'validation', text: "Emergency detected and routed. Patient is in good hands. Crisis averted. 🚑" },
  { id: 'eh_v2', tone: 'validation', text: "Patient needed urgent care. Your AI flagged it immediately. Safe outcome. ✅" },
  { id: 'eh_v3', tone: 'validation', text: "Emergency call handled with zero hesitation. Your AI and team moved as one. 💙" },
  { id: 'eh_v4', tone: 'validation', text: "Patient in pain got routed to care in seconds. Your system works when it matters most. 🏥" },
  { id: 'eh_v5', tone: 'validation', text: "Your AI recognized the severity and acted instantly. That's the safety net working. 👨‍⚕️" },
  { id: 'eh_v6', tone: 'validation', text: "Patient needed immediate help. Your system delivered it without delay. 🤝" },
  // Data (25%)
  { id: 'eh_d1', tone: 'data', text: "That was urgent. Your system didn't delay. Patient got help fast. 🎯" },
  { id: 'eh_d2', tone: 'data', text: "Urgent situation → AI detected → Doctor notified → Patient safe. Chain reaction complete. ⚡" },
  { id: 'eh_d3', tone: 'data', text: "Critical call came in. Your AI didn't miss a beat. ✔️" },
  // Playful (15%)
  { id: 'eh_p1', tone: 'playful', text: "Emergency routed. Doctor on it. Your system knows what matters. 🛡️" },
]

export const HIGH_QUALITY_CALL_MESSAGES: CelebrationMessage[] = [
  // Validation (60%)
  { id: 'hq_v1', tone: 'validation', text: "That call scored 90+. Your patient left happy. Pure gold. 🌟" },
  { id: 'hq_v2', tone: 'validation', text: "Your AI handled that patient beautifully. The conversation flowed naturally. ✨" },
  { id: 'hq_v3', tone: 'validation', text: "That patient got exactly what they needed. Your call quality: exceptional. 💎" },
  { id: 'hq_v4', tone: 'validation', text: "Patient got heard, understood, and helped. That's what a 90+ call looks like. 🎯" },
  { id: 'hq_v5', tone: 'validation', text: "That patient's experience was excellent from ring to booking. ⭐" },
  { id: 'hq_v6', tone: 'validation', text: "The patient in that call felt respected and cared for. Quality call confirmed. 💙" },
  { id: 'hq_v7', tone: 'validation', text: "Your conversation hit every mark. Patient happy, call score high, everyone wins. ✅" },
  // Data (25%)
  { id: 'hq_d1', tone: 'data', text: "Your conversation with that patient was a masterclass. 90+ score. 👏" },
  { id: 'hq_d2', tone: 'data', text: "That call was a textbook example of how it's done right. 90+ earned. 🏆" },
  { id: 'hq_d3', tone: 'data', text: "Your patient got a smooth, confident, helpful conversation. That's why the score is high. 🚀" },
  // Playful (15%)
  { id: 'hq_p1', tone: 'playful', text: "That patient will probably tell friends about your practice. Great call. 👑" },
  { id: 'hq_p2', tone: 'playful', text: "Your AI conducted that conversation like a pro. Patient satisfaction: confirmed. 🔥" },
]

export const NO_SHOW_PREVENTED_MESSAGES: CelebrationMessage[] = [
  // Validation (60%)
  { id: 'ns_v1', tone: 'validation', text: "Patient confirmed via text. That's $400 showing up on time. ✅" },
  { id: 'ns_v2', tone: 'validation', text: "SMS reminder worked. Patient is locked in. No-show risk: eliminated. 💚" },
  { id: 'ns_v3', tone: 'validation', text: "Patient said yes. Your revenue is safe. Your schedule is solid. 🎯" },
  { id: 'ns_v4', tone: 'validation', text: "Appointment confirmed by patient. One less worry on your plate. 🙏" },
  { id: 'ns_v5', tone: 'validation', text: "Patient texted back. They're committed. That chair will be filled. 👤" },
  { id: 'ns_v6', tone: 'validation', text: "Your reminder landed. Patient responded. Appointment stands strong. 💪" },
  // Data (25%)
  { id: 'ns_d1', tone: 'data', text: "One confirmed appointment means one less missed opportunity. 📱" },
  { id: 'ns_d2', tone: 'data', text: "Patient response received. Commitment confirmed. Revenue protected. 💰" },
  { id: 'ns_d3', tone: 'data', text: "SMS did its job. Patient remembers. Patient will show. Victory. 🏆" },
  // Playful (15%)
  { id: 'ns_p1', tone: 'playful', text: "Patient confirmed loyalty with one text. Your system earned its worth. ⭐" },
]

export const MISSED_CALL_RECOVERED_MESSAGES: CelebrationMessage[] = [
  // Validation (60%)
  { id: 'mc_v1', tone: 'validation', text: "Call at 2am on Sunday. Human would have missed it. Your AI: on the job. 🌙" },
  { id: 'mc_v2', tone: 'validation', text: "That call came in when your team was sleeping. Your AI captured it anyway. 🚀" },
  { id: 'mc_v3', tone: 'validation', text: "Call during peak hours your staff couldn't cover. AI answered. Patient happy. 👏" },
  { id: 'mc_v4', tone: 'validation', text: "Your receptionist was busy. Your AI covered. Patient got through. ✅" },
  { id: 'mc_v5', tone: 'validation', text: "That patient called when they thought no one was listening. Your AI was. 👂" },
  { id: 'mc_v6', tone: 'validation', text: "Patient called late. They weren't sure you'd answer. Surprise: you did. 💙" },
  // Data (25%)
  { id: 'mc_d1', tone: 'data', text: "Call came after hours. Voicemail wouldn't have helped. Your AI did instead. 🎯" },
  { id: 'mc_d2', tone: 'data', text: "Weekend call at 6pm. Normal clinic would miss it. You didn't. 📞" },
  { id: 'mc_d3', tone: 'data', text: "Call landed outside business hours. Your AI didn't take a break. ⚡" },
  // Playful (15%)
  { id: 'mc_p1', tone: 'playful', text: "That call would have been lost to voicemail. Instead it's an appointment. 💎" },
]

export const RESCHEDULED_MESSAGES: CelebrationMessage[] = [
  // Validation (60%)
  { id: 'rs_v1', tone: 'validation', text: "Patient rescheduled. You kept the relationship. That's a win. 💙" },
  { id: 'rs_v2', tone: 'validation', text: "Call didn't result in booking, but you handled it with care. That's good practice. 👍" },
  { id: 'rs_v3', tone: 'validation', text: "Patient needed to reschedule. You made it easy. They'll book again. ✅" },
  { id: 'rs_v4', tone: 'validation', text: "Patient changed plans. You were flexible. Trust built. ⚖️" },
  { id: 'rs_v5', tone: 'validation', text: "Reschedule isn't a loss. It's a patient who still chooses you. 🙏" },
  { id: 'rs_v6', tone: 'validation', text: "Patient rescheduled for later. You stayed helpful. That's how you build loyalty. 🌱" },
  // Data (25%)
  { id: 'rs_d1', tone: 'data', text: "Not every call books first try. But this one stayed engaged. Growth. 📈" },
  { id: 'rs_d2', tone: 'data', text: "Patient said no today. But they didn't say never. Relationship intact. 🤝" },
  { id: 'rs_d3', tone: 'data', text: "Not a booking, but a conversation that mattered. Sometimes that's the win. 💬" },
  // Playful (15%)
  { id: 'rs_p1', tone: 'playful', text: "Call handled smoothly even when plans changed. That's professionalism. 👏" },
]

export const POSITIVE_SENTIMENT_MESSAGES: CelebrationMessage[] = [
  // Validation (60%)
  { id: 'ps_v1', tone: 'validation', text: "Patient left that call happy. That's the tone you want. 😊" },
  { id: 'ps_v2', tone: 'validation', text: "That patient felt heard and cared for. You made their day better. 💚" },
  { id: 'ps_v3', tone: 'validation', text: "Patient sounded relieved by the end. Your AI gave them what they needed. ✨" },
  { id: 'ps_v4', tone: 'validation', text: "Patient confidence went up during the call. That's excellent. 🌟" },
  { id: 'ps_v5', tone: 'validation', text: "That was a good experience for the patient. They'll be back. 🔄" },
  { id: 'ps_v6', tone: 'validation', text: "Patient ended the call satisfied. That's the goal. Nailed it. ✅" },
  // Data (25%)
  { id: 'ps_d1', tone: 'data', text: "Positive energy from patient. They trust your practice now. 💙" },
  { id: 'ps_d2', tone: 'data', text: "Patient feeling good = patient showing up = patient staying loyal. Perfect chain. 🔗" },
  { id: 'ps_d3', tone: 'data', text: "This patient is probably telling friends about you right now. Great interaction. 👏" },
  // Playful (15%)
  { id: 'ps_p1', tone: 'playful', text: "That patient is now a brand advocate for your clinic. Well done. 👑" },
]

const ALL_MESSAGES: Record<CelebrationCategory, CelebrationMessage[]> = {
  booking: BOOKING_CONFIRMED_MESSAGES,
  emergency: EMERGENCY_HANDLED_MESSAGES,
  quality: HIGH_QUALITY_CALL_MESSAGES,
  noshow: NO_SHOW_PREVENTED_MESSAGES,
  recovered: MISSED_CALL_RECOVERED_MESSAGES,
  rescheduled: RESCHEDULED_MESSAGES,
  positive_sentiment: POSITIVE_SENTIMENT_MESSAGES,
}

/**
 * Get a random message from a category, weighted by tone
 */
export function getRandomMessage(category: CelebrationCategory): string {
  const messages = ALL_MESSAGES[category]
  if (!messages || messages.length === 0) return ''
  
  // Weight messages by tone
  const weighted: CelebrationMessage[] = []
  messages.forEach(m => {
    const weight = TONE_WEIGHTS[m.tone]
    const copies = Math.round(weight * 10)
    for (let i = 0; i < copies; i++) {
      weighted.push(m)
    }
  })
  
  return weighted[Math.floor(Math.random() * weighted.length)].text
}

/**
 * Weekly email subject/closing pairs
 */
export const WEEKLY_EMAIL_PAIRS = [
  {
    subject: "Your team just saved $12,400 this week 💰",
    closing: "Go check your dashboard. You've earned the victory lap. 🏆",
  },
  {
    subject: "Your AI handled 47 calls. You handled zero stress. 🎯",
    closing: "See the full breakdown. Your practice is crushing it. 🚀",
  },
  {
    subject: "Week summary: More patients, more revenue, same schedule. ⚡",
    closing: "Check the dashboard. Your numbers are worth celebrating. 🎉",
  },
  {
    subject: "Your AI worked 168 hours. Never called in sick. 🤖",
    closing: "Review what your team accomplished. The data is beautiful. ✨",
  },
  {
    subject: "53 calls answered. 12 appointments booked. Zero burnout. 👑",
    closing: "See your weekly wins in the dashboard. You deserve this. 💎",
  },
  {
    subject: "Your practice just recovered $8,900 in missed revenue. 📈",
    closing: "View the full report. Numbers don't lie. They celebrate. ✅",
  },
  {
    subject: "Your team's weekly performance: Legendary. (Your AI agrees.) 🌟",
    closing: "Check out what you built. Take a moment to breathe. 💙",
  },
  {
    subject: "Weekly reality check: Your AI is earning its keep. 💪",
    closing: "Dashboard has all the proof. Go take a look. 🔥",
  },
]
