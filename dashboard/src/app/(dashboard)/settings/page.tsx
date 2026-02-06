'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Building2, 
  Bot, 
  Calendar, 
  Bell, 
  Shield,
  Save,
  Play,
  Loader2,
  Phone,
  CreditCard,
  CheckCircle2,
  AlertCircle,
  PhoneForwarded,
  Info,
  Clock,
  MessageSquare,
  Copy
} from 'lucide-react'
import { getClinicSettings, getClinic, updateClinicSettings, updateClinicInfo, getSmsSettings, updateSmsSettings, SmsTemplates } from '@/lib/api/dental'
import { CallForwardingGuide } from '@/components/dashboard/call-forwarding-guide'
import { useSubscription, getPlanDisplayName, getPlanPrice } from '@/lib/hooks/use-subscription'
import { useToast } from '@/hooks/use-toast'

interface ClinicData {
  name: string
  phone: string
  twilio_number: string
  address: string | null
  business_hours: Record<string, { open: string; close: string } | null>
  owner_phone?: string
  emergency_phone?: string
  transfer_enabled?: boolean
  transfer_timeout_seconds?: number
  transfer_fallback?: string
}

interface SettingsData {
  agent_name: string
  agent_voice: string
  greeting_template: string
  services: string[]
  dentist_names: string[]
  insurance_accepted: string
  insurance_verification: boolean
  emergency_transfers: boolean
  appointment_confirmations: boolean
  after_hours_messages: boolean
  max_transfer_attempts: number
}

export default function SettingsPage() {
  const [isSaving, setIsSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const [clinic, setClinic] = useState<ClinicData | null>(null)
  const [settings, setSettings] = useState<SettingsData | null>(null)
  const { toast } = useToast()
  
  // Auto-save state
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)
  const isInitialLoadRef = useRef(true)
  
  // Clinic info state (FIX-02: controlled inputs)
  const [clinicName, setClinicName] = useState('')
  const [clinicPhone, setClinicPhone] = useState('')
  const [clinicAddress, setClinicAddress] = useState('')
  const [clinicTimezone, setClinicTimezone] = useState('america_new_york')
  
  // Agent settings state
  const [agentName, setAgentName] = useState('')
  const [agentVoice, setAgentVoice] = useState('alloy')
  const [greeting, setGreeting] = useState('')
  const [transferPhone, setTransferPhone] = useState('')
  const [emergencyPhone, setEmergencyPhone] = useState('')
  const [transferEnabled, setTransferEnabled] = useState(true)
  const [transferTimeout, setTransferTimeout] = useState('20')
  const [transferFallback, setTransferFallback] = useState('voicemail')
  const { subscription } = useSubscription()
  
  // SMS Template state
  const [smsTemplates, setSmsTemplates] = useState<SmsTemplates>({
    confirmation: '',
    reminder_24h: '',
    reminder_2h: '',
    recall: '',
    recall_followup: '',
  })
  const [smsConfirmationEnabled, setSmsConfirmationEnabled] = useState(true)
  const [smsReminder24hEnabled, setSmsReminder24hEnabled] = useState(true)
  const [smsReminder2hEnabled, setSmsReminder2hEnabled] = useState(true)
  const [smsRecallEnabled, setSmsRecallEnabled] = useState(true)
  
  // FIX-03: Business hours state
  type DayHours = { isOpen: boolean; open: string; close: string }
  const defaultBusinessHours: Record<string, DayHours> = {
    Monday: { isOpen: true, open: '8:00 AM', close: '5:00 PM' },
    Tuesday: { isOpen: true, open: '8:00 AM', close: '5:00 PM' },
    Wednesday: { isOpen: true, open: '8:00 AM', close: '5:00 PM' },
    Thursday: { isOpen: true, open: '8:00 AM', close: '5:00 PM' },
    Friday: { isOpen: true, open: '8:00 AM', close: '5:00 PM' },
    Saturday: { isOpen: true, open: '8:00 AM', close: '2:00 PM' },
    Sunday: { isOpen: false, open: '9:00 AM', close: '1:00 PM' },
  }
  const [businessHours, setBusinessHours] = useState<Record<string, DayHours>>(defaultBusinessHours)
  
  const updateBusinessHour = (day: string, field: keyof DayHours, value: string | boolean) => {
    setBusinessHours(prev => ({
      ...prev,
      [day]: { ...prev[day], [field]: value }
    }))
  }

  // Copy Monday hours to all weekdays (Tue-Fri)
  const copyMondayToWeekdays = () => {
    const mondayHours = businessHours['Monday']
    setBusinessHours(prev => ({
      ...prev,
      Tuesday: { ...mondayHours },
      Wednesday: { ...mondayHours },
      Thursday: { ...mondayHours },
      Friday: { ...mondayHours },
    }))
  }

  useEffect(() => {
    async function loadData() {
      setLoading(true)
      try {
        const [clinicData, settingsData, smsData] = await Promise.all([
          getClinic(),
          getClinicSettings(),
          getSmsSettings()
        ])
        if (clinicData) {
          setClinic(clinicData)
          // FIX-02: Initialize clinic info state
          setClinicName(clinicData.name || '')
          setClinicPhone(clinicData.phone || '')
          setClinicAddress(clinicData.address || '')
          // Transfer settings
          setTransferPhone(clinicData.owner_phone || '')
          setEmergencyPhone(clinicData.emergency_phone || '')
          setTransferEnabled(clinicData.transfer_enabled !== false)
          setTransferTimeout(String(clinicData.transfer_timeout_seconds || 20))
          setTransferFallback(clinicData.transfer_fallback || 'voicemail')
        }
        if (settingsData) {
          setSettings(settingsData)
          setAgentName(settingsData.agent_name || '')
          setAgentVoice(settingsData.agent_voice || 'alloy')
          setGreeting(settingsData.greeting_template || '')
        }
        if (smsData) {
          setSmsTemplates(smsData.sms_templates || {})
          setSmsConfirmationEnabled(smsData.sms_confirmation_enabled ?? true)
          setSmsReminder24hEnabled(smsData.sms_reminder_24h_enabled ?? true)
          setSmsReminder2hEnabled(smsData.sms_reminder_2h_enabled ?? true)
          setSmsRecallEnabled(smsData.sms_recall_enabled ?? true)
        }
      } catch (error) {
        console.error('Failed to load settings:', error)
      } finally {
        setLoading(false)
        // Mark initial load complete after a brief delay to prevent false positive changes
        setTimeout(() => { isInitialLoadRef.current = false }, 100)
      }
    }
    loadData()
  }, [])

  // Debounced auto-save function
  const performAutoSave = useCallback(async () => {
    if (isInitialLoadRef.current || loading) return
    
    setSaveStatus('saving')
    setIsSaving(true)
    try {
      await Promise.all([
        updateClinicSettings({
          agent_name: agentName,
          agent_voice: agentVoice,
          greeting_template: greeting,
        }),
        updateClinicInfo({
          name: clinicName || undefined,
          phone: clinicPhone || undefined,
          address: clinicAddress || undefined,
          owner_phone: transferPhone || undefined,
          emergency_phone: emergencyPhone || undefined,
          transfer_enabled: transferEnabled,
          transfer_timeout_seconds: parseInt(transferTimeout) || 20,
          transfer_fallback: transferFallback,
        }),
        updateSmsSettings({
          sms_templates: smsTemplates,
          sms_confirmation_enabled: smsConfirmationEnabled,
          sms_reminder_24h_enabled: smsReminder24hEnabled,
          sms_reminder_2h_enabled: smsReminder2hEnabled,
          sms_recall_enabled: smsRecallEnabled,
        })
      ])
      setSaveStatus('saved')
      setHasUnsavedChanges(false)
      // Reset to idle after showing "Saved" briefly
      setTimeout(() => setSaveStatus('idle'), 2000)
    } catch (error) {
      console.error('Auto-save failed:', error)
      setSaveStatus('error')
    } finally {
      setIsSaving(false)
    }
  }, [
    agentName, agentVoice, greeting, clinicName, clinicPhone, clinicAddress,
    transferPhone, emergencyPhone, transferEnabled, transferTimeout, transferFallback,
    smsTemplates, smsConfirmationEnabled, smsReminder24hEnabled, smsReminder2hEnabled,
    smsRecallEnabled, loading
  ])

  // Auto-save effect: debounce changes by 1.5 seconds
  useEffect(() => {
    if (isInitialLoadRef.current || loading) return
    
    setHasUnsavedChanges(true)
    setSaveStatus('idle')
    
    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }
    
    // Set new debounce timer
    debounceTimerRef.current = setTimeout(() => {
      performAutoSave()
    }, 1500)
    
    // Cleanup on unmount
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [
    agentName, agentVoice, greeting, clinicName, clinicPhone, clinicAddress,
    transferPhone, emergencyPhone, transferEnabled, transferTimeout, transferFallback,
    smsTemplates, smsConfirmationEnabled, smsReminder24hEnabled, smsReminder2hEnabled,
    smsRecallEnabled, performAutoSave, loading
  ])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      // Save agent settings
      await updateClinicSettings({
        agent_name: agentName,
        agent_voice: agentVoice,
        greeting_template: greeting,
      })
      
      // FIX-02: Save clinic info including name, phone, address + transfer settings
      await updateClinicInfo({
        name: clinicName || undefined,
        phone: clinicPhone || undefined,
        address: clinicAddress || undefined,
        owner_phone: transferPhone || undefined,
        emergency_phone: emergencyPhone || undefined,
        transfer_enabled: transferEnabled,
        transfer_timeout_seconds: parseInt(transferTimeout) || 20,
        transfer_fallback: transferFallback,
      })
      
      // Save SMS templates and settings
      await updateSmsSettings({
        sms_templates: smsTemplates,
        sms_confirmation_enabled: smsConfirmationEnabled,
        sms_reminder_24h_enabled: smsReminder24hEnabled,
        sms_reminder_2h_enabled: smsReminder2hEnabled,
        sms_recall_enabled: smsRecallEnabled,
      })
      
      // FIX-04: Show success toast
      toast({
        title: "Settings saved",
        description: "Your changes have been saved successfully.",
      })
    } catch (error) {
      console.error('Failed to save settings:', error)
      // FIX-04: Show error toast
      toast({
        title: "Failed to save",
        description: "There was an error saving your settings. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">Configure your AI receptionist and clinic settings</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Auto-save status indicator */}
          {saveStatus === 'saving' && (
            <span className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Saving...
            </span>
          )}
          {saveStatus === 'saved' && (
            <span className="flex items-center gap-2 text-sm text-green-600">
              <CheckCircle2 className="h-4 w-4" />
              Saved
            </span>
          )}
          {saveStatus === 'error' && (
            <span className="flex items-center gap-2 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              Failed to save
            </span>
          )}
          {/* Manual save button (instant save) */}
          <Button 
            onClick={handleSave} 
            disabled={isSaving}
            variant={hasUnsavedChanges ? "default" : "outline"}
            size="sm"
          >
            <Save className="mr-2 h-4 w-4" />
            {isSaving ? 'Saving...' : hasUnsavedChanges ? 'Save Now' : 'Save'}
          </Button>
        </div>
      </div>

      <Tabs defaultValue="agent" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 h-auto p-1.5 bg-muted/50 rounded-xl">
          {/* AI Assistant - PRIMARY (Core Product!) */}
          <TabsTrigger value="agent" className="gap-2 py-2.5 data-[state=active]:bg-white data-[state=active]:shadow-sm rounded-lg">
            <Bot className="h-4 w-4" />
            <span className="hidden sm:inline font-medium">AI Assistant</span>
            <span className="sm:hidden text-xs">AI</span>
          </TabsTrigger>
          
          {/* Practice Setup */}
          <TabsTrigger value="practice" className="gap-2 py-2.5 data-[state=active]:bg-white data-[state=active]:shadow-sm rounded-lg">
            <Building2 className="h-4 w-4" />
            <span className="hidden sm:inline font-medium">Practice</span>
            <span className="sm:hidden text-xs">Setup</span>
          </TabsTrigger>
          
          {/* Communications */}
          <TabsTrigger value="communications" className="gap-2 py-2.5 data-[state=active]:bg-white data-[state=active]:shadow-sm rounded-lg">
            <MessageSquare className="h-4 w-4" />
            <span className="hidden sm:inline font-medium">Communications</span>
            <span className="sm:hidden text-xs">Comms</span>
          </TabsTrigger>
          
          {/* Account */}
          <TabsTrigger value="account" className="gap-2 py-2.5 data-[state=active]:bg-white data-[state=active]:shadow-sm rounded-lg">
            <CreditCard className="h-4 w-4" />
            <span className="hidden sm:inline font-medium">Account</span>
            <span className="sm:hidden text-xs">Acct</span>
          </TabsTrigger>
        </TabsList>

        {/* ===== COMMUNICATIONS TAB ===== */}
        <TabsContent value="communications">
          <div className="space-y-8">
            {/* Quick Nav */}
            <div className="flex flex-wrap gap-2 pb-2 border-b">
              <a href="#forwarding" className="text-sm text-muted-foreground hover:text-primary transition-colors">Forwarding</a>
              <span className="text-muted-foreground/50">•</span>
              <a href="#transfer" className="text-sm text-muted-foreground hover:text-primary transition-colors">Transfer</a>
              <span className="text-muted-foreground/50">•</span>
              <a href="#notifications" className="text-sm text-muted-foreground hover:text-primary transition-colors">Notifications</a>
              <span className="text-muted-foreground/50">•</span>
              <a href="#sms" className="text-sm text-muted-foreground hover:text-primary transition-colors">SMS Templates</a>
            </div>

            {/* Section: Call Forwarding */}
            <div id="forwarding">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Phone className="h-5 w-5 text-[#0099CC]" />
                Call Forwarding Setup
              </h3>
              <CallForwardingGuide twilioNumber={clinic?.twilio_number || '(904) 867-9643'} />
            </div>

            {/* Section: Call Transfer */}
            <div id="transfer">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <PhoneForwarded className="h-5 w-5 text-[#0099CC]" />
                Call Transfer Settings
              </h3>
          <div className="grid gap-6">
            {/* Main Takeover Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PhoneForwarded className="h-5 w-5" />
                  Call Transfer Settings
                </CardTitle>
                <CardDescription>
                  Configure where calls get transferred when AI hands off to a human
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Info Box */}
                <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-900 dark:bg-blue-950">
                  <div className="flex gap-3">
                    <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-blue-800 dark:text-blue-200">
                      <p className="font-medium mb-1">Flexible Transfer Destinations</p>
                      <p>Transfers can go to you, your office manager, a receptionist&apos;s direct line, or anyone you designate. 
                         Set different numbers for routine vs emergency transfers.</p>
                    </div>
                  </div>
                </div>

                {/* Enable/Disable Toggle */}
                <div className="flex items-center justify-between p-4 rounded-lg border bg-muted/50">
                  <div>
                    <p className="font-medium">Enable Call Transfers</p>
                    <p className="text-sm text-muted-foreground">Allow AI to transfer calls to a human</p>
                  </div>
                  <Switch 
                    checked={transferEnabled} 
                    onCheckedChange={setTransferEnabled}
                  />
                </div>

                {/* Primary Transfer Phone Number */}
                <div className="space-y-2">
                  <Label htmlFor="transferPhone">Primary Transfer Phone</Label>
                  <Input 
                    id="transferPhone" 
                    type="tel"
                    placeholder="+1 (555) 123-4567"
                    value={transferPhone}
                    onChange={(e) => setTransferPhone(e.target.value)}
                    disabled={!transferEnabled}
                  />
                  <p className="text-xs text-muted-foreground">
                    Where routine transfers go: when you click &quot;Transfer to Me&quot; or patient asks for a human.
                    Can be owner, office manager, or front desk direct line.
                  </p>
                </div>

                {/* Emergency Transfer Phone Number */}
                <div className="space-y-2">
                  <Label htmlFor="emergencyPhone">Emergency Transfer Phone (Optional)</Label>
                  <Input 
                    id="emergencyPhone" 
                    type="tel"
                    placeholder="+1 (555) 999-0000"
                    value={emergencyPhone}
                    onChange={(e) => setEmergencyPhone(e.target.value)}
                    disabled={!transferEnabled}
                  />
                  <p className="text-xs text-muted-foreground">
                    Where urgent cases go (severe pain, bleeding, etc.). Leave blank to use primary number.
                  </p>
                </div>

                {/* Timeout Setting */}
                <div className="space-y-2">
                  <Label>Ring Timeout</Label>
                  <Select 
                    value={transferTimeout} 
                    onValueChange={setTransferTimeout}
                    disabled={!transferEnabled}
                  >
                    <SelectTrigger className="w-48">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="10">10 seconds</SelectItem>
                      <SelectItem value="15">15 seconds</SelectItem>
                      <SelectItem value="20">20 seconds (recommended)</SelectItem>
                      <SelectItem value="30">30 seconds</SelectItem>
                      <SelectItem value="45">45 seconds</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    How long to ring before triggering the fallback action
                  </p>
                </div>

                {/* Fallback Behavior */}
                <div className="space-y-2">
                  <Label>If No One Answers</Label>
                  <Select 
                    value={transferFallback} 
                    onValueChange={setTransferFallback}
                    disabled={!transferEnabled}
                  >
                    <SelectTrigger className="w-full sm:w-80">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="voicemail">Take a voicemail message</SelectItem>
                      <SelectItem value="callback">Promise callback within 30 minutes</SelectItem>
                      <SelectItem value="callback_1h">Promise callback within 1 hour</SelectItem>
                      <SelectItem value="callback_2h">Promise callback within 2 hours</SelectItem>
                      <SelectItem value="retry">Try calling again (up to 2 retries)</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    What the AI tells the caller if no one picks up the transfer
                  </p>
                </div>

                {/* Test Transfer Button */}
                <div className="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-900 dark:bg-green-950">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                      <p className="font-medium text-green-800 dark:text-green-200">Test Your Transfer Setup</p>
                      <p className="text-sm text-green-700 dark:text-green-300">
                        We&apos;ll call your transfer phone to make sure it&apos;s working
                      </p>
                    </div>
                    <Button 
                      variant="outline" 
                      className="border-green-600 text-green-700 hover:bg-green-100"
                      disabled={!transferPhone || !transferEnabled}
                    >
                      <Phone className="mr-2 h-4 w-4" />
                      Test Transfer
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* How It Works Card */}
            <Card>
              <CardHeader>
                <CardTitle>How Call Takeover Works</CardTitle>
                <CardDescription>Step-by-step guide to taking over a call</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex gap-4">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium flex-shrink-0">
                      1
                    </div>
                    <div>
                      <p className="font-medium">See Live Calls</p>
                      <p className="text-sm text-muted-foreground">
                        Go to &quot;Live Calls&quot; in your dashboard or watch the notification badge in your sidebar
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium flex-shrink-0">
                      2
                    </div>
                    <div>
                      <p className="font-medium">Click &quot;Transfer to Me&quot;</p>
                      <p className="text-sm text-muted-foreground">
                        Found a call you want to handle personally? Click the transfer button
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium flex-shrink-0">
                      3
                    </div>
                    <div>
                      <p className="font-medium">AI Announces Transfer</p>
                      <p className="text-sm text-muted-foreground">
                        The AI politely says: &quot;I&apos;m connecting you with the practice owner now. One moment please.&quot;
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-4">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium flex-shrink-0">
                      4
                    </div>
                    <div>
                      <p className="font-medium">Your Phone Rings</p>
                      <p className="text-sm text-muted-foreground">
                        Answer to speak directly with the caller. The AI drops off automatically.
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Use Cases Card */}
            <Card>
              <CardHeader>
                <CardTitle>When to Use This</CardTitle>
                <CardDescription>Common scenarios where taking over makes sense</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-lg border p-3">
                    <p className="font-medium text-green-700 dark:text-green-400">🦷 Urgent Cases</p>
                    <p className="text-sm text-muted-foreground">Patient says &quot;I&apos;m in severe pain&quot; - take over to assess urgency</p>
                  </div>
                  <div className="rounded-lg border p-3">
                    <p className="font-medium text-green-700 dark:text-green-400">💰 High-Value Leads</p>
                    <p className="text-sm text-muted-foreground">New patient asking about implants or cosmetic work</p>
                  </div>
                  <div className="rounded-lg border p-3">
                    <p className="font-medium text-green-700 dark:text-green-400">⭐ VIP Patients</p>
                    <p className="text-sm text-muted-foreground">Recognize a long-time patient who deserves personal touch</p>
                  </div>
                  <div className="rounded-lg border p-3">
                    <p className="font-medium text-green-700 dark:text-green-400">🔧 AI Confusion</p>
                    <p className="text-sm text-muted-foreground">The AI seems stuck or the caller is getting frustrated</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            </div>
            </div>

            {/* Section: Notifications */}
            <div id="notifications">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Bell className="h-5 w-5 text-[#0099CC]" />
                Notification Preferences
              </h3>
              <Card>
                <CardHeader>
                  <CardTitle>Notification Preferences</CardTitle>
                  <CardDescription>Choose how you want to be notified about calls and bookings</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-4">
                    <h4 className="font-medium">Email Notifications</h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium">Daily Summary</p>
                          <p className="text-xs text-muted-foreground">Receive a daily email with call stats</p>
                        </div>
                        <Switch defaultChecked />
                      </div>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium">New Appointments</p>
                          <p className="text-xs text-muted-foreground">Get notified when AI books appointments</p>
                        </div>
                        <Switch defaultChecked />
                      </div>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium">Transfers</p>
                          <p className="text-xs text-muted-foreground">Alert when calls are transferred</p>
                        </div>
                        <Switch defaultChecked />
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="notifyEmail">Notification Email</Label>
                    <Input id="notifyEmail" type="email" placeholder="reception@yourpractice.com" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Section: SMS Templates */}
            <div id="sms">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-[#0099CC]" />
                SMS Templates
              </h3>
              <div className="grid gap-6">
                {/* Template Variables */}
                <Card>
                  <CardHeader>
                    <CardTitle>Template Variables</CardTitle>
                    <CardDescription>Use these in your templates - they&apos;ll be replaced with actual values</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {[
                        { var: '{patient_name}', desc: 'Patient name' },
                        { var: '{clinic_name}', desc: 'Clinic name' },
                        { var: '{date}', desc: 'Date' },
                        { var: '{time}', desc: 'Time' },
                        { var: '{phone}', desc: 'Phone' },
                      ].map((item) => (
                        <button
                          key={item.var}
                          onClick={() => navigator.clipboard.writeText(item.var)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-primary/10 text-primary text-sm hover:bg-primary/20 transition-colors"
                          title={item.desc}
                        >
                          <code>{item.var}</code>
                          <Copy className="h-3 w-3" />
                        </button>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Appointment Confirmation */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                      Appointment Confirmation
                    </CardTitle>
                    <CardDescription>Sent immediately after booking</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="sms-confirmation">Message Template</Label>
                        <span className="text-xs text-muted-foreground">
                          {(smsTemplates.confirmation || '').length}/160
                        </span>
                      </div>
                      <Textarea
                        id="sms-confirmation"
                        rows={3}
                        value={smsTemplates.confirmation || ''}
                        placeholder="Hi {patient_name}! Your appointment at {clinic_name} is confirmed for {date} at {time}. Reply YES to confirm."
                        onChange={(e) => setSmsTemplates({ ...smsTemplates, confirmation: e.target.value })}
                        className="font-mono text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <Switch 
                        id="confirmation-enabled" 
                        checked={smsConfirmationEnabled}
                        onCheckedChange={setSmsConfirmationEnabled}
                      />
                      <Label htmlFor="confirmation-enabled">Auto-send on booking</Label>
                    </div>
                  </CardContent>
                </Card>

                {/* 24-Hour Reminder */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Clock className="h-5 w-5 text-blue-600" />
                      24-Hour Reminder
                    </CardTitle>
                    <CardDescription>Sent 24 hours before appointment</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Textarea
                      rows={3}
                      value={smsTemplates.reminder_24h || ''}
                      placeholder="Reminder: {patient_name}, appointment tomorrow at {clinic_name} at {time}."
                      onChange={(e) => setSmsTemplates({ ...smsTemplates, reminder_24h: e.target.value })}
                      className="font-mono text-sm"
                    />
                    <div className="flex items-center gap-2">
                      <Switch 
                        checked={smsReminder24hEnabled}
                        onCheckedChange={setSmsReminder24hEnabled}
                      />
                      <Label>Enable 24h reminder</Label>
                    </div>
                  </CardContent>
                </Card>

                {/* Recall Messages */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Bell className="h-5 w-5 text-purple-600" />
                      Recall / Reactivation
                    </CardTitle>
                    <CardDescription>For patients who haven&apos;t visited in 6+ months</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Textarea
                      rows={3}
                      value={smsTemplates.recall || ''}
                      placeholder="Hi {patient_name}! It's been a while since your last visit to {clinic_name}. Reply BOOK to schedule."
                      onChange={(e) => setSmsTemplates({ ...smsTemplates, recall: e.target.value })}
                      className="font-mono text-sm"
                    />
                    <div className="flex items-center gap-2">
                      <Switch 
                        checked={smsRecallEnabled}
                        onCheckedChange={setSmsRecallEnabled}
                      />
                      <Label>Enable recall automation</Label>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* ===== PRACTICE TAB ===== */}
        <TabsContent value="practice">
          <div className="space-y-8">
            {/* Quick Nav */}
            <div className="flex flex-wrap gap-2 pb-2 border-b">
              <a href="#clinic-info" className="text-sm text-muted-foreground hover:text-primary transition-colors">Clinic Info</a>
              <span className="text-muted-foreground/50">•</span>
              <a href="#calendar" className="text-sm text-muted-foreground hover:text-primary transition-colors">Calendar</a>
            </div>

            {/* Section: Clinic Information */}
            <div id="clinic-info">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Building2 className="h-5 w-5 text-[#0099CC]" />
                Clinic Information
              </h3>
          <Card>
            <CardHeader>
              <CardTitle>Clinic Information</CardTitle>
              <CardDescription>Basic information about your dental practice</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="clinicName">Clinic Name</Label>
                  <Input 
                    id="clinicName" 
                    value={clinicName}
                    onChange={(e) => setClinicName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input 
                    id="phone" 
                    value={clinicPhone}
                    onChange={(e) => setClinicPhone(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="address">Address</Label>
                <Input 
                  id="address" 
                  value={clinicAddress}
                  onChange={(e) => setClinicAddress(e.target.value)}
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="twilioNumber">Twilio Phone Number</Label>
                  <Input id="twilioNumber" value={clinic?.twilio_number || ''} disabled />
                  <p className="text-xs text-muted-foreground">Contact support to change</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="timezone">Timezone</Label>
                  <Select value={clinicTimezone} onValueChange={setClinicTimezone}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="america_new_york">Eastern Time (ET)</SelectItem>
                      <SelectItem value="america_chicago">Central Time (CT)</SelectItem>
                      <SelectItem value="america_denver">Mountain Time (MT)</SelectItem>
                      <SelectItem value="america_los_angeles">Pacific Time (PT)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium">Business Hours</h4>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={copyMondayToWeekdays}
                    className="text-xs text-muted-foreground hover:text-foreground"
                  >
                    <Copy className="mr-1.5 h-3 w-3" />
                    Copy Monday → Tue-Fri
                  </Button>
                </div>
                <div className="grid gap-3">
                  {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((day) => (
                    <div key={day} className="flex items-center gap-4">
                      <span className="w-24 text-sm">{day}</span>
                      <Select 
                        value={businessHours[day]?.isOpen ? 'open' : 'closed'}
                        onValueChange={(value) => updateBusinessHour(day, 'isOpen', value === 'open')}
                      >
                        <SelectTrigger className="w-24">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="open">Open</SelectItem>
                          <SelectItem value="closed">Closed</SelectItem>
                        </SelectContent>
                      </Select>
                      {businessHours[day]?.isOpen && (
                        <>
                          <Input 
                            value={businessHours[day]?.open || '8:00 AM'} 
                            onChange={(e) => updateBusinessHour(day, 'open', e.target.value)}
                            className="w-28" 
                          />
                          <span>to</span>
                          <Input 
                            value={businessHours[day]?.close || '5:00 PM'} 
                            onChange={(e) => updateBusinessHour(day, 'close', e.target.value)}
                            className="w-28" 
                          />
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
            </Card>
            </div>

            {/* Section: Calendar Integration */}
            <div id="calendar">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Calendar className="h-5 w-5 text-[#0099CC]" />
                Calendar & Scheduling
              </h3>
              <div className="grid gap-6">
                {/* Connection Status Card */}
                <Card>
                  <CardHeader>
                    <CardTitle>Calendar Integration</CardTitle>
                    <CardDescription>Connect your calendar so AI can check availability and book appointments</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Not Connected State */}
                    <div className="rounded-lg border-2 border-dashed border-muted-foreground/25 p-6 text-center">
                      <div className="flex justify-center gap-4 mb-4">
                        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-white shadow-sm border">
                          <svg className="h-6 w-6" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
                        </div>
                        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-white shadow-sm border">
                          <svg className="h-6 w-6" viewBox="0 0 24 24"><path fill="#0078D4" d="M21.17 3H7.83A.83.83 0 0 0 7 3.83v16.34c0 .46.37.83.83.83h13.34c.46 0 .83-.37.83-.83V3.83a.83.83 0 0 0-.83-.83zM17 18H9v-2h8v2zm0-4H9v-2h8v2zm0-4H9V8h8v2z"/><path fill="#0078D4" opacity=".5" d="M3 7h2v14H3z"/></svg>
                        </div>
                      </div>
                      <h3 className="font-medium mb-2">Connect Your Calendar</h3>
                      <p className="text-sm text-muted-foreground mb-4">
                        DentSignal needs calendar access to check your availability and book appointments.
                      </p>
                      <div className="flex flex-col sm:flex-row gap-3 justify-center">
                        <Button className="gap-2">
                          <svg className="h-4 w-4" viewBox="0 0 24 24"><path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/></svg>
                          Connect Google Calendar
                        </Button>
                        <Button variant="outline" className="gap-2">
                          <svg className="h-4 w-4" viewBox="0 0 24 24"><path fill="currentColor" d="M21.17 3H7.83A.83.83 0 0 0 7 3.83v16.34c0 .46.37.83.83.83h13.34c.46 0 .83-.37.83-.83V3.83a.83.83 0 0 0-.83-.83z"/></svg>
                          Connect Outlook
                        </Button>
                      </div>
                    </div>

                    {/* Alternative: Manual Mode */}
                    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-900 dark:bg-amber-950">
                      <div className="flex gap-3">
                        <Info className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
                        <div className="text-sm text-amber-800 dark:text-amber-200">
                          <p className="font-medium mb-1">Don&apos;t have Google or Outlook?</p>
                          <p>DentSignal can work in &quot;manual mode&quot; - AI collects patient info and you confirm appointments manually.</p>
                        </div>
                      </div>
                    </div>

                    {/* Practice Management Systems */}
                    <div className="space-y-3">
                      <Label>Practice Management System (Coming Soon)</Label>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <div className="rounded-lg border p-3 text-center opacity-50">
                          <p className="font-medium text-sm">Dentrix</p>
                          <p className="text-xs text-muted-foreground">Coming Q1</p>
                        </div>
                        <div className="rounded-lg border p-3 text-center opacity-50">
                          <p className="font-medium text-sm">Eaglesoft</p>
                          <p className="text-xs text-muted-foreground">Coming Q1</p>
                        </div>
                        <div className="rounded-lg border p-3 text-center opacity-50">
                          <p className="font-medium text-sm">Open Dental</p>
                          <p className="text-xs text-muted-foreground">Coming Q2</p>
                        </div>
                        <div className="rounded-lg border p-3 text-center opacity-50">
                          <p className="font-medium text-sm">Curve</p>
                          <p className="text-xs text-muted-foreground">Coming Q2</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Booking Settings */}
                <Card>
                  <CardHeader>
                    <CardTitle>Booking Settings</CardTitle>
                    <CardDescription>Configure how AI handles appointment booking</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label>Default Appointment Duration</Label>
                        <Select defaultValue="60">
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="30">30 minutes</SelectItem>
                            <SelectItem value="45">45 minutes</SelectItem>
                            <SelectItem value="60">60 minutes</SelectItem>
                            <SelectItem value="90">90 minutes</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Buffer Time Between Appointments</Label>
                        <Select defaultValue="15">
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="0">No buffer</SelectItem>
                            <SelectItem value="5">5 minutes</SelectItem>
                            <SelectItem value="10">10 minutes</SelectItem>
                            <SelectItem value="15">15 minutes</SelectItem>
                            <SelectItem value="30">30 minutes</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Double-Booking Prevention</p>
                        <p className="text-sm text-muted-foreground">Check calendar before confirming</p>
                      </div>
                      <Switch defaultChecked />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Same-Day Appointments</p>
                        <p className="text-sm text-muted-foreground">Allow booking appointments for today</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* ===== AI ASSISTANT TAB (PRIMARY) ===== */}
        <TabsContent value="agent">
          <div className="grid gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Agent Personality</CardTitle>
                <CardDescription>Customize how your AI receptionist sounds and behaves</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="agentName">Agent Name</Label>
                    <Input 
                      id="agentName" 
                      value={agentName}
                      onChange={(e) => setAgentName(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">The name your AI will use when answering</p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="voice">Voice</Label>
                    <div className="flex gap-2">
                      <Select value={agentVoice} onValueChange={setAgentVoice}>
                        <SelectTrigger className="flex-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="alloy">Alloy (Neutral)</SelectItem>
                          <SelectItem value="echo">Echo (Male)</SelectItem>
                          <SelectItem value="fable">Fable (British)</SelectItem>
                          <SelectItem value="onyx">Onyx (Male, Deep)</SelectItem>
                          <SelectItem value="nova">Nova (Female)</SelectItem>
                          <SelectItem value="shimmer">Shimmer (Female, Warm)</SelectItem>
                        </SelectContent>
                      </Select>
                      <Button variant="outline" size="icon">
                        <Play className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="greeting">Custom Greeting</Label>
                  <Textarea 
                    id="greeting" 
                    rows={3}
                    value={greeting}
                    onChange={(e) => setGreeting(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">This is what the AI says when answering calls. Use {'{clinic_name}'}, {'{agent_name}'}, {'{time_of_day}'}</p>
                </div>

                <div className="space-y-2">
                  <Label>Dentist Names</Label>
                  <Input defaultValue={settings?.dentist_names?.join(', ') || ''} />
                  <p className="text-xs text-muted-foreground">Comma-separated list of dentist names</p>
                </div>

                <div className="space-y-2">
                  <Label>Services Offered</Label>
                  <Textarea 
                    rows={2}
                    defaultValue={settings?.services?.join(', ') || ''}
                  />
                  <p className="text-xs text-muted-foreground">Comma-separated list of services (cleanings, fillings, crowns, etc.)</p>
                </div>

                <div className="space-y-2">
                  <Label>Accepted Insurance Plans</Label>
                  <Textarea 
                    rows={2}
                    placeholder="Delta Dental, Cigna, Aetna, MetLife, United Healthcare"
                    defaultValue={settings?.insurance_accepted || ''}
                  />
                  <p className="text-xs text-muted-foreground">Comma-separated list of insurance plans you accept. AI will tell callers which plans you take.</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Behavior Settings</CardTitle>
                <CardDescription>Control how the AI handles different situations</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Insurance Verification</p>
                    <p className="text-sm text-muted-foreground">Ask callers about insurance</p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Emergency Transfers</p>
                    <p className="text-sm text-muted-foreground">Transfer urgent cases to on-call dentist</p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Appointment Confirmations</p>
                    <p className="text-sm text-muted-foreground">Read back appointment details to confirm</p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">After-Hours Messages</p>
                    <p className="text-sm text-muted-foreground">Take messages when office is closed</p>
                  </div>
                  <Switch defaultChecked />
                </div>

                <div className="space-y-2">
                  <Label>Max Transfer Attempts</Label>
                  <Select defaultValue="3">
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1 attempt</SelectItem>
                      <SelectItem value="2">2 attempts</SelectItem>
                      <SelectItem value="3">3 attempts</SelectItem>
                      <SelectItem value="5">5 attempts</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">How many times to try before taking a message</p>
                </div>
              </CardContent>
            </Card>

            {/* After-Hours Mode Card */}
            <Card>
              <CardHeader>
                <CardTitle>After-Hours Mode</CardTitle>
                <CardDescription>How the AI behaves outside business hours</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-900 dark:bg-amber-950">
                  <div className="flex gap-3">
                    <Clock className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-amber-800 dark:text-amber-200">
                      <p className="font-medium mb-1">Business Hours Aware</p>
                      <p>The AI automatically knows when you&apos;re open based on the hours set in the Clinic tab. 
                         Outside those hours, it uses the after-hours behavior you configure here.</p>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>After-Hours Behavior</Label>
                  <Select defaultValue="message">
                    <SelectTrigger className="w-full sm:w-80">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="message">Take a message for callback</SelectItem>
                      <SelectItem value="book">Still allow appointment booking</SelectItem>
                      <SelectItem value="emergency_only">Only handle emergencies, take messages for rest</SelectItem>
                      <SelectItem value="redirect">Redirect to after-hours voicemail</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Announce Office is Closed</p>
                    <p className="text-sm text-muted-foreground">&quot;Thank you for calling. Our office is currently closed...&quot;</p>
                  </div>
                  <Switch defaultChecked />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Emergency Transfers After Hours</p>
                    <p className="text-sm text-muted-foreground">Transfer severe pain/bleeding cases to emergency phone</p>
                  </div>
                  <Switch defaultChecked />
                </div>

                <div className="space-y-2">
                  <Label>After-Hours Greeting (Optional)</Label>
                  <Textarea 
                    rows={2}
                    placeholder="Thank you for calling {clinic_name}. Our office is currently closed. For emergencies, please press 1..."
                  />
                  <p className="text-xs text-muted-foreground">Leave blank to use default greeting</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ===== ACCOUNT TAB ===== */}
        <TabsContent value="account">
          <div className="space-y-8">
            {/* Quick Nav */}
            <div className="flex flex-wrap gap-2 pb-2 border-b">
              <a href="#billing" className="text-sm text-muted-foreground hover:text-primary transition-colors">Billing</a>
              <span className="text-muted-foreground/50">•</span>
              <a href="#security" className="text-sm text-muted-foreground hover:text-primary transition-colors">Security</a>
            </div>

            {/* Section: Billing */}
            <div id="billing">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-[#0099CC]" />
                Billing & Subscription
              </h3>
          <div className="grid gap-6">
            {/* Current Plan */}
            <Card>
              <CardHeader>
                <CardTitle>Current Plan</CardTitle>
                <CardDescription>Your subscription details and billing information</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {subscription ? (
                  <>
                    <div className="flex items-center justify-between p-4 rounded-lg border bg-muted/50">
                      <div className="flex items-center gap-4">
                        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                          <CreditCard className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                          <p className="font-semibold text-lg">
                            {getPlanDisplayName(subscription.planType)} Plan
                          </p>
                          <p className="text-sm text-muted-foreground">
                            ${getPlanPrice(subscription.planType)}/month
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium ${
                          subscription.isActive 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {subscription.isActive ? (
                            <CheckCircle2 className="h-4 w-4" />
                          ) : (
                            <AlertCircle className="h-4 w-4" />
                          )}
                          {subscription.status === 'trial' ? 'Trial' : 
                           subscription.isActive ? 'Active' : 'Expired'}
                        </span>
                      </div>
                    </div>

                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="rounded-lg border p-4">
                        <p className="text-sm text-muted-foreground">Status</p>
                        <p className="font-medium capitalize">{subscription.status}</p>
                      </div>
                      <div className="rounded-lg border p-4">
                        <p className="text-sm text-muted-foreground">
                          {subscription.isActive ? 'Renews On' : 'Expired On'}
                        </p>
                        <p className="font-medium">
                          {subscription.expiresAt?.toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                          }) || 'N/A'}
                        </p>
                      </div>
                      <div className="rounded-lg border p-4">
                        <p className="text-sm text-muted-foreground">Days Remaining</p>
                        <p className="font-medium">{subscription.daysRemaining} days</p>
                      </div>
                      <div className="rounded-lg border p-4">
                        <p className="text-sm text-muted-foreground">Monthly Cost</p>
                        <p className="font-medium">${getPlanPrice(subscription.planType)}</p>
                      </div>
                    </div>

                    {subscription.isExpiringSoon && (
                      <div className="rounded-lg bg-amber-50 border border-amber-200 p-4">
                        <div className="flex items-start gap-3">
                          <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5" />
                          <div>
                            <p className="font-medium text-amber-800">Subscription Renewing Soon</p>
                            <p className="text-sm text-amber-700 mt-1">
                              Your subscription will renew in {subscription.daysRemaining} days. 
                              Contact us if you need to make changes.
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-muted-foreground">Loading subscription info...</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Plan Features */}
            <Card>
              <CardHeader>
                <CardTitle>Plan Features</CardTitle>
                <CardDescription>What&apos;s included in your plan</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 sm:grid-cols-2">
                  {[
                    'Unlimited inbound calls',
                    'AI appointment booking',
                    'Call transcriptions',
                    'Real-time analytics',
                    'Email notifications',
                    'Calendar integration',
                    'Custom AI voice',
                    'Priority support',
                  ].map((feature) => (
                    <div key={feature} className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      <span className="text-sm">{feature}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Billing Contact */}
            <Card>
              <CardHeader>
                <CardTitle>Billing Support</CardTitle>
                <CardDescription>Need help with billing or want to change your plan?</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  For billing inquiries, plan changes, or cancellations, please contact our support team.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Button asChild>
                    <a href="mailto:hello@dentsignal.com?subject=Billing%20Inquiry">
                      Contact Billing Support
                    </a>
                  </Button>
                  <Button variant="outline" asChild>
                    <a href="mailto:hello@dentsignal.com?subject=Plan%20Upgrade%20Request">
                      Request Plan Change
                    </a>
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Cancel Subscription */}
            <Card className="border-red-200 dark:border-red-900">
              <CardHeader>
                <CardTitle className="text-red-700 dark:text-red-400">Cancel Subscription</CardTitle>
                <CardDescription>End your DentSignal subscription</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950">
                  <p className="text-sm text-red-800 dark:text-red-200">
                    <strong>Before you go:</strong> Cancelling will immediately stop AI from answering your calls. 
                    All your call data and settings will be preserved for 30 days in case you change your mind.
                  </p>
                </div>
                <div className="flex flex-wrap gap-3">
                  <Button 
                    variant="outline" 
                    className="border-red-300 text-red-700 hover:bg-red-50 hover:text-red-800"
                    asChild
                  >
                    <a href="mailto:hello@dentsignal.com?subject=Cancellation%20Request&body=Hi%2C%0A%0AI%20would%20like%20to%20cancel%20my%20DentSignal%20subscription.%0A%0AReason%20(optional)%3A%0A%0AClinic%20Name%3A%0AAccount%20Email%3A">
                      Request Cancellation
                    </a>
                  </Button>
                  <Button variant="ghost" asChild>
                    <a href="mailto:founder@dentsignal.me?subject=Feedback%20Before%20Cancelling">
                      Talk to Founder First
                    </a>
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Cancellation requests are processed within 24 hours. You won&apos;t be charged after cancellation.
                </p>
              </CardContent>
            </Card>
            </div>
            </div>

            {/* Section: Security */}
            <div id="security">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Shield className="h-5 w-5 text-[#0099CC]" />
                Security
              </h3>
              <div className="grid gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Account Security</CardTitle>
                <CardDescription>Manage your account security settings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input id="email" type="email" defaultValue="admin@sunshinedental.com" />
                </div>
                <Button variant="outline">Change Password</Button>
                
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Two-Factor Authentication</p>
                    <p className="text-sm text-muted-foreground">Add an extra layer of security</p>
                  </div>
                  <Switch />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>API Keys</CardTitle>
                <CardDescription>Manage API keys for integrations</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-lg border bg-muted/50 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-mono text-sm">sk_live_•••••••••••••••••••••••••</p>
                      <p className="text-xs text-muted-foreground">Created Dec 1, 2024</p>
                    </div>
                    <Button variant="outline" size="sm">Regenerate</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
