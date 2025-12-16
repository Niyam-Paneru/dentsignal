'use client'

import { useState, useEffect } from 'react'
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
  Volume2,
  Loader2
} from 'lucide-react'
import { getClinicSettings, getClinic, updateClinicSettings } from '@/lib/api/dental'

interface ClinicData {
  name: string
  phone: string
  twilio_number: string
  address: string | null
  business_hours: Record<string, { open: string; close: string } | null>
}

interface SettingsData {
  agent_name: string
  agent_voice: string
  greeting_template: string
  services: string[]
  dentist_names: string[]
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
  const [agentName, setAgentName] = useState('')
  const [agentVoice, setAgentVoice] = useState('alloy')
  const [greeting, setGreeting] = useState('')

  useEffect(() => {
    async function loadData() {
      setLoading(true)
      try {
        const [clinicData, settingsData] = await Promise.all([
          getClinic(),
          getClinicSettings()
        ])
        if (clinicData) setClinic(clinicData)
        if (settingsData) {
          setSettings(settingsData)
          setAgentName(settingsData.agent_name || '')
          setAgentVoice(settingsData.agent_voice || 'alloy')
          setGreeting(settingsData.greeting_template || '')
        }
      } catch (error) {
        console.error('Failed to load settings:', error)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await updateClinicSettings({
        agent_name: agentName,
        agent_voice: agentVoice,
        greeting_template: greeting,
      })
    } catch (error) {
      console.error('Failed to save settings:', error)
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
        <Button onClick={handleSave} disabled={isSaving}>
          <Save className="mr-2 h-4 w-4" />
          {isSaving ? 'Saving...' : 'Save Changes'}
        </Button>
      </div>

      <Tabs defaultValue="clinic" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5 lg:w-auto lg:grid-cols-none">
          <TabsTrigger value="clinic" className="gap-2">
            <Building2 className="h-4 w-4" />
            <span className="hidden sm:inline">Clinic</span>
          </TabsTrigger>
          <TabsTrigger value="agent" className="gap-2">
            <Bot className="h-4 w-4" />
            <span className="hidden sm:inline">AI Agent</span>
          </TabsTrigger>
          <TabsTrigger value="calendar" className="gap-2">
            <Calendar className="h-4 w-4" />
            <span className="hidden sm:inline">Calendar</span>
          </TabsTrigger>
          <TabsTrigger value="notifications" className="gap-2">
            <Bell className="h-4 w-4" />
            <span className="hidden sm:inline">Notifications</span>
          </TabsTrigger>
          <TabsTrigger value="security" className="gap-2">
            <Shield className="h-4 w-4" />
            <span className="hidden sm:inline">Security</span>
          </TabsTrigger>
        </TabsList>

        {/* Clinic Settings */}
        <TabsContent value="clinic">
          <Card>
            <CardHeader>
              <CardTitle>Clinic Information</CardTitle>
              <CardDescription>Basic information about your dental practice</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="clinicName">Clinic Name</Label>
                  <Input id="clinicName" defaultValue={clinic?.name || ''} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input id="phone" defaultValue={clinic?.phone || ''} />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="address">Address</Label>
                <Input id="address" defaultValue={clinic?.address || ''} />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="twilioNumber">Twilio Phone Number</Label>
                  <Input id="twilioNumber" defaultValue={clinic?.twilio_number || ''} disabled />
                  <p className="text-xs text-muted-foreground">Contact support to change</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="timezone">Timezone</Label>
                  <Select defaultValue="america_new_york">
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
                <h4 className="font-medium">Business Hours</h4>
                <div className="grid gap-3">
                  {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((day) => (
                    <div key={day} className="flex items-center gap-4">
                      <span className="w-24 text-sm">{day}</span>
                      <Select defaultValue={day === 'Sunday' ? 'closed' : 'open'}>
                        <SelectTrigger className="w-24">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="open">Open</SelectItem>
                          <SelectItem value="closed">Closed</SelectItem>
                        </SelectContent>
                      </Select>
                      {day !== 'Sunday' && (
                        <>
                          <Input defaultValue="8:00 AM" className="w-28" />
                          <span>to</span>
                          <Input defaultValue={day === 'Saturday' ? '2:00 PM' : '5:00 PM'} className="w-28" />
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI Agent Settings */}
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
          </div>
        </TabsContent>

        {/* Calendar Settings */}
        <TabsContent value="calendar">
          <Card>
            <CardHeader>
              <CardTitle>Calendar Integration</CardTitle>
              <CardDescription>Connect and configure your calendar for appointment booking</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="rounded-lg border bg-muted/50 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white">
                      <Calendar className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-medium">Google Calendar</p>
                      <p className="text-sm text-muted-foreground">Connected as dr-smith@clinic.com</p>
                    </div>
                  </div>
                  <Button variant="outline">Disconnect</Button>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Sync Frequency</Label>
                  <Select defaultValue="5">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">Every 1 minute</SelectItem>
                      <SelectItem value="5">Every 5 minutes</SelectItem>
                      <SelectItem value="15">Every 15 minutes</SelectItem>
                      <SelectItem value="30">Every 30 minutes</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
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
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Double-Booking Prevention</p>
                  <p className="text-sm text-muted-foreground">Check calendar before booking</p>
                </div>
                <Switch defaultChecked />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Auto-Book Appointments</p>
                  <p className="text-sm text-muted-foreground">AI directly adds to calendar (no confirmation needed)</p>
                </div>
                <Switch />
              </div>

              <div className="space-y-2">
                <Label>Buffer Time Between Appointments</Label>
                <Select defaultValue="15">
                  <SelectTrigger className="w-48">
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
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notification Settings */}
        <TabsContent value="notifications">
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
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">Missed Calls</p>
                      <p className="text-xs text-muted-foreground">Notify about missed or dropped calls</p>
                    </div>
                    <Switch />
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="notifyEmail">Notification Email</Label>
                <Input id="notifyEmail" type="email" defaultValue="reception@sunshinedental.com" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Settings */}
        <TabsContent value="security">
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
        </TabsContent>
      </Tabs>
    </div>
  )
}
