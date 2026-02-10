'use client'

import { useEffect, useState, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Phone, 
  MessageSquare, 
  Calendar, 
  Users, 
  RefreshCw, 
  CheckCircle,
  XCircle,
  DollarSign,
  Plus,
  Loader2,
  Building2,
  Sparkles
} from 'lucide-react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog'
import { getClinic } from '@/lib/api/dental'

// Recall types and statuses
const RECALL_TYPES = [
  { value: 'cleaning', label: '6-Month Cleaning', icon: '🦷', interval: '6 months' },
  { value: 'checkup', label: 'Annual Checkup', icon: '📋', interval: '12 months' },
  { value: 'periodontal', label: 'Periodontal Maintenance', icon: '🩺', interval: '3-4 months' },
  { value: 'followup', label: 'Treatment Follow-up', icon: '📞', interval: '30 days' },
]

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-800',
  sms_sent: 'bg-blue-100 text-blue-800',
  call_scheduled: 'bg-purple-100 text-purple-800',
  call_completed: 'bg-indigo-100 text-indigo-800',
  booked: 'bg-green-100 text-green-800',
  declined: 'bg-red-100 text-red-800',
  no_response: 'bg-amber-100 text-amber-800',
  cancelled: 'bg-gray-200 text-gray-600',
}

interface RecallItem {
  id: number
  patient_name: string
  patient_phone: string
  patient_email?: string
  recall_type: string
  status: string
  due_date: string
  days_overdue: number
  sms_attempts: number
  call_attempts: number
  last_contact?: string
  patient_response?: string
}

interface RecallStats {
  total_recalls: number
  pending: number
  sms_sent: number
  calls_made: number
  booked: number
  declined: number
  no_response: number
  conversion_rate: number
  estimated_revenue: number
}

interface Campaign {
  id: number
  name: string
  recall_type: string
  total_recalls: number
  appointments_booked: number
  conversion_rate: number
  estimated_revenue: number
  actual_revenue: number
  is_active: boolean
  started_at?: string
}

export default function RecallsPage() {
  const [loading, setLoading] = useState(true)
  const [noClinic, setNoClinic] = useState(false)
  const [recalls, setRecalls] = useState<RecallItem[]>([])
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [stats, setStats] = useState<RecallStats | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [isCreatingCampaign, setIsCreatingCampaign] = useState(false)
  const [newCampaign, setNewCampaign] = useState({
    name: '',
    recall_type: 'cleaning',
    overdue_days: 30,
  })

  // Simulated data for demo (replace with real API calls)
  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const clinic = await getClinic()
      if (!clinic) {
        setNoClinic(true)
        setLoading(false)
        return
      }

      // Demo data - in production, fetch from API
      setStats({
        total_recalls: 127,
        pending: 45,
        sms_sent: 32,
        calls_made: 18,
        booked: 28,
        declined: 4,
        no_response: 0,
        conversion_rate: 22.0,
        estimated_revenue: 5600,
      })

      setRecalls([
        {
          id: 1,
          patient_name: 'Sarah Johnson',
          patient_phone: '+1 (555) 123-4567',
          patient_email: 'sarah.j@email.com',
          recall_type: 'cleaning',
          status: 'pending',
          due_date: '2024-11-15',
          days_overdue: 45,
          sms_attempts: 0,
          call_attempts: 0,
        },
        {
          id: 2,
          patient_name: 'Michael Chen',
          patient_phone: '+1 (555) 234-5678',
          recall_type: 'cleaning',
          status: 'sms_sent',
          due_date: '2024-11-10',
          days_overdue: 50,
          sms_attempts: 1,
          call_attempts: 0,
          last_contact: '2024-12-28',
        },
        {
          id: 3,
          patient_name: 'Emily Davis',
          patient_phone: '+1 (555) 345-6789',
          recall_type: 'checkup',
          status: 'call_scheduled',
          due_date: '2024-10-01',
          days_overdue: 90,
          sms_attempts: 2,
          call_attempts: 0,
          last_contact: '2024-12-26',
        },
        {
          id: 4,
          patient_name: 'James Wilson',
          patient_phone: '+1 (555) 456-7890',
          recall_type: 'cleaning',
          status: 'booked',
          due_date: '2024-11-20',
          days_overdue: 40,
          sms_attempts: 1,
          call_attempts: 1,
          last_contact: '2024-12-29',
          patient_response: 'BOOK - scheduled for Jan 5th',
        },
        {
          id: 5,
          patient_name: 'Lisa Anderson',
          patient_phone: '+1 (555) 567-8901',
          recall_type: 'periodontal',
          status: 'declined',
          due_date: '2024-12-01',
          days_overdue: 30,
          sms_attempts: 2,
          call_attempts: 1,
          last_contact: '2024-12-27',
          patient_response: 'Will call back in February',
        },
      ])

      setCampaigns([
        {
          id: 1,
          name: 'Q4 Cleaning Campaign',
          recall_type: 'cleaning',
          total_recalls: 85,
          appointments_booked: 23,
          conversion_rate: 27.1,
          estimated_revenue: 17000,
          actual_revenue: 4600,
          is_active: true,
          started_at: '2024-12-01',
        },
        {
          id: 2,
          name: 'Annual Checkup Push',
          recall_type: 'checkup',
          total_recalls: 42,
          appointments_booked: 5,
          conversion_rate: 11.9,
          estimated_revenue: 8400,
          actual_revenue: 1000,
          is_active: true,
          started_at: '2024-12-15',
        },
      ])

    } catch (error) {
      console.error('Failed to load recalls:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleCreateCampaign = async () => {
    setIsCreatingCampaign(true)
    // In production, call API to create campaign
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    const newCampaignItem: Campaign = {
      id: campaigns.length + 1,
      name: newCampaign.name,
      recall_type: newCampaign.recall_type,
      total_recalls: Math.floor(Math.random() * 50) + 20,
      appointments_booked: 0,
      conversion_rate: 0,
      estimated_revenue: Math.floor(Math.random() * 10000) + 5000,
      actual_revenue: 0,
      is_active: true,
      started_at: new Date().toISOString(),
    }
    
    setCampaigns([newCampaignItem, ...campaigns])
    setNewCampaign({ name: '', recall_type: 'cleaning', overdue_days: 30 })
    setIsCreatingCampaign(false)
  }

  const handleSendSms = async (recallId: number) => {
    void recallId
    // TODO: Call API to trigger SMS when backend SMS service is ready
  }

  const handleScheduleCall = async (recallId: number) => {
    void recallId
    // TODO: Call API to schedule AI call when backend is ready
  }

  const filteredRecalls = recalls.filter(recall => {
    if (statusFilter !== 'all' && recall.status !== statusFilter) return false
    if (typeFilter !== 'all' && recall.recall_type !== typeFilter) return false
    return true
  })

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (noClinic) {
    return (
      <div className="flex h-[calc(100vh-200px)] items-center justify-center">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
              <Building2 className="h-8 w-8 text-primary" />
            </div>
            <CardTitle className="text-2xl">No Clinic Found</CardTitle>
            <CardDescription>
              Set up your clinic to start using the recall system.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-indigo-500" />
            Proactive Recalls
          </h1>
          <p className="text-muted-foreground">
            Automated outreach to bring patients back for cleanings and checkups
          </p>
        </div>
        <Dialog>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Campaign
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Recall Campaign</DialogTitle>
              <DialogDescription>
                Start a new campaign to reach out to overdue patients
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="campaign-name">Campaign Name</Label>
                <Input
                  id="campaign-name"
                  placeholder="e.g., January Cleaning Push"
                  value={newCampaign.name}
                  onChange={(e) => setNewCampaign({ ...newCampaign, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="recall-type">Recall Type</Label>
                <Select 
                  value={newCampaign.recall_type}
                  onValueChange={(v) => setNewCampaign({ ...newCampaign, recall_type: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {RECALL_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.icon} {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="overdue-days">Minimum Days Overdue</Label>
                <Input
                  id="overdue-days"
                  type="number"
                  value={newCampaign.overdue_days}
                  onChange={(e) => setNewCampaign({ ...newCampaign, overdue_days: parseInt(e.target.value) || 30 })}
                />
                <p className="text-xs text-muted-foreground">
                  Only patients overdue by at least this many days will be included
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button 
                onClick={handleCreateCampaign} 
                disabled={!newCampaign.name || isCreatingCampaign}
              >
                {isCreatingCampaign ? (
                  <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Creating...</>
                ) : (
                  'Create Campaign'
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Users className="h-4 w-4 text-muted-foreground" />
                Total Recalls
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_recalls}</div>
              <p className="text-xs text-muted-foreground">{stats.pending} pending</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-blue-500" />
                SMS Sent
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.sms_sent}</div>
              <p className="text-xs text-muted-foreground">this month</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Phone className="h-4 w-4 text-purple-500" />
                AI Calls Made
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.calls_made}</div>
              <p className="text-xs text-muted-foreground">this month</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Calendar className="h-4 w-4 text-green-500" />
                Booked
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{stats.booked}</div>
              <p className="text-xs text-muted-foreground">{stats.conversion_rate}% conversion</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2 text-green-800">
                <DollarSign className="h-4 w-4" />
                Revenue Recovered
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-700">
                ${stats.estimated_revenue.toLocaleString()}
              </div>
              <p className="text-xs text-green-600">from {stats.booked} bookings</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <Tabs defaultValue="recalls" className="space-y-4">
        <TabsList>
          <TabsTrigger value="recalls">Patient Recalls</TabsTrigger>
          <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
        </TabsList>

        {/* Recalls Tab */}
        <TabsContent value="recalls" className="space-y-4">
          {/* Filters */}
          <div className="flex gap-4 items-center">
            <div className="flex gap-2 items-center">
              <Label className="text-sm text-muted-foreground">Status:</Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="sms_sent">SMS Sent</SelectItem>
                  <SelectItem value="call_scheduled">Call Scheduled</SelectItem>
                  <SelectItem value="booked">Booked</SelectItem>
                  <SelectItem value="declined">Declined</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-2 items-center">
              <Label className="text-sm text-muted-foreground">Type:</Label>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {RECALL_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.icon} {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button variant="outline" size="sm" onClick={loadData}>
              <RefreshCw className="h-4 w-4 mr-1" />
              Refresh
            </Button>
          </div>

          {/* Recalls Table */}
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Patient</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Days Overdue</TableHead>
                    <TableHead>Attempts</TableHead>
                    <TableHead>Last Contact</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredRecalls.map((recall) => (
                    <TableRow key={recall.id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{recall.patient_name}</p>
                          <p className="text-xs text-muted-foreground">{recall.patient_phone}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {RECALL_TYPES.find(t => t.value === recall.recall_type)?.icon}{' '}
                          {recall.recall_type}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={STATUS_COLORS[recall.status] || 'bg-gray-100'}>
                          {recall.status.replace(/_/g, ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className={recall.days_overdue > 60 ? 'text-red-600 font-medium' : ''}>
                          {recall.days_overdue} days
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2 text-xs">
                          <span className="flex items-center gap-1">
                            <MessageSquare className="h-3 w-3" />
                            {recall.sms_attempts}
                          </span>
                          <span className="flex items-center gap-1">
                            <Phone className="h-3 w-3" />
                            {recall.call_attempts}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {recall.last_contact ? (
                          <span className="text-sm">
                            {new Date(recall.last_contact).toLocaleDateString()}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {recall.status === 'pending' && (
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => handleSendSms(recall.id)}
                          >
                            <MessageSquare className="h-3 w-3 mr-1" />
                            Send SMS
                          </Button>
                        )}
                        {recall.status === 'sms_sent' && (
                          <div className="flex gap-1">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleSendSms(recall.id)}
                            >
                              <MessageSquare className="h-3 w-3 mr-1" />
                              Follow-up
                            </Button>
                            <Button 
                              size="sm" 
                              variant="default"
                              onClick={() => handleScheduleCall(recall.id)}
                            >
                              <Phone className="h-3 w-3 mr-1" />
                              AI Call
                            </Button>
                          </div>
                        )}
                        {recall.status === 'booked' && (
                          <Badge className="bg-green-100 text-green-800">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Completed
                          </Badge>
                        )}
                        {recall.status === 'declined' && (
                          <Badge variant="secondary">
                            <XCircle className="h-3 w-3 mr-1" />
                            Closed
                          </Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Campaigns Tab */}
        <TabsContent value="campaigns" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {campaigns.map((campaign) => (
              <Card key={campaign.id} className={campaign.is_active ? 'border-green-200' : ''}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{campaign.name}</CardTitle>
                    <Badge className={campaign.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100'}>
                      {campaign.is_active ? 'Active' : 'Completed'}
                    </Badge>
                  </div>
                  <CardDescription>
                    {RECALL_TYPES.find(t => t.value === campaign.recall_type)?.icon}{' '}
                    {RECALL_TYPES.find(t => t.value === campaign.recall_type)?.label}
                    {campaign.started_at && (
                      <span className="ml-2 text-xs">
                        Started {new Date(campaign.started_at).toLocaleDateString()}
                      </span>
                    )}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-2xl font-bold">{campaign.total_recalls}</p>
                      <p className="text-xs text-muted-foreground">Total Patients</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-green-600">{campaign.appointments_booked}</p>
                      <p className="text-xs text-muted-foreground">Booked</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{campaign.conversion_rate}%</p>
                      <p className="text-xs text-muted-foreground">Conversion</p>
                    </div>
                  </div>
                  <div className="mt-4 p-3 bg-green-50 rounded-lg">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-green-700">Revenue Recovered</span>
                      <span className="font-bold text-green-700">
                        ${campaign.actual_revenue.toLocaleString()}
                      </span>
                    </div>
                    <div className="mt-1 h-2 bg-green-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-green-500 rounded-full"
                        style={{ 
                          width: `${Math.min(100, (campaign.actual_revenue / campaign.estimated_revenue) * 100)}%` 
                        }}
                      />
                    </div>
                    <p className="text-xs text-green-600 mt-1">
                      of ${campaign.estimated_revenue.toLocaleString()} potential
                    </p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* Info Card */}
      <Card className="border-indigo-200 bg-indigo-50">
        <CardHeader>
          <CardTitle className="text-indigo-800 flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            How Proactive Recalls Work
          </CardTitle>
        </CardHeader>
        <CardContent className="text-indigo-700 text-sm">
          <div className="grid md:grid-cols-4 gap-4">
            <div className="flex flex-col items-center text-center p-3 bg-white rounded-lg">
              <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center mb-2">
                <span className="text-indigo-700 font-bold">1</span>
              </div>
              <p className="font-medium">Find Overdue</p>
              <p className="text-xs text-indigo-600">Identify patients past their recall date</p>
            </div>
            <div className="flex flex-col items-center text-center p-3 bg-white rounded-lg">
              <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center mb-2">
                <span className="text-indigo-700 font-bold">2</span>
              </div>
              <p className="font-medium">Send SMS</p>
              <p className="text-xs text-indigo-600">Friendly text reminder to schedule</p>
            </div>
            <div className="flex flex-col items-center text-center p-3 bg-white rounded-lg">
              <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center mb-2">
                <span className="text-indigo-700 font-bold">3</span>
              </div>
              <p className="font-medium">AI Call</p>
              <p className="text-xs text-indigo-600">Automated call if no SMS response</p>
            </div>
            <div className="flex flex-col items-center text-center p-3 bg-white rounded-lg">
              <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center mb-2">
                <CheckCircle className="h-4 w-4 text-green-700" />
              </div>
              <p className="font-medium">Booked!</p>
              <p className="text-xs text-green-600">~$200/cleaning recovered</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
