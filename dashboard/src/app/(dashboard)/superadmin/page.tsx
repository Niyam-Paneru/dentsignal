"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { createClient } from "@/lib/supabase/client";
import {
  Activity,
  AlertTriangle,
  Building2,
  CheckCircle2,
  DollarSign,
  Phone,
  RefreshCw,
  Server,
  TrendingUp,
  Zap,
  Eye,
  Shield,
  Lock,
} from "lucide-react";

// Super Admin emails - only platform owner(s)
const SUPER_ADMIN_EMAILS = [
  "niyampaneru79@gmail.com",
];

// Types
interface APIUsage {
  openai: { status: string; cost_today: number; cost_month: number; remaining_percent?: number };
  gemini: { status: string; cost_today: number; cost_month: number; requests_remaining?: number };
  huggingface: { status: string; cost_today: number; cost_month: number };
  deepgram: { status: string; cost_today: number; cost_month: number; remaining_percent?: number };
  twilio: { status: string; balance: number; cost_today: number; cost_month: number };
  total_estimated_cost_today: number;
  total_estimated_cost_month: number;
  alerts: string[];
}

interface ClinicUsage {
  clinic_id: string;
  clinic_name: string;
  created_at: string;
  is_active: boolean;
  plan: string;
  total_calls: number;
  calls_today: number;
  calls_this_week: number;
  calls_this_month: number;
  avg_call_duration: number;
  appointment_rate: number;
  avg_sentiment_score: number;
  estimated_cost_month: number;
}

interface CallSummary {
  call_id: string;
  clinic_name: string;
  timestamp: string;
  duration_seconds: number;
  outcome: string;
  sentiment: string;
  quality_score: number;
  summary_anonymized: string;
  topics: string[];
  needs_review: boolean;
  review_reason?: string;
}

interface SystemHealth {
  status: string;
  uptime_hours: number;
  services: Record<string, string>;
  recent_errors: Array<{ error: string; time: string }>;
  recommendations: string[];
}

// Mock data for demo (replace with real API calls)
const mockAPIUsage: APIUsage = {
  openai: { status: "active", cost_today: 18.75, cost_month: 562.50, remaining_percent: 85 },
  gemini: { status: "active", cost_today: 0, cost_month: 0, requests_remaining: 1050 },
  huggingface: { status: "active", cost_today: 0, cost_month: 0 },
  deepgram: { status: "active", cost_today: 5.50, cost_month: 165.00, remaining_percent: 75 },
  twilio: { status: "active", balance: 450.00, cost_today: 12.50, cost_month: 375.00 },
  total_estimated_cost_today: 36.75,
  total_estimated_cost_month: 1102.50,
  alerts: [],
};

const mockClinics: ClinicUsage[] = [
  {
    clinic_id: "1",
    clinic_name: "Sunny Dental Care",
    created_at: "2024-10-15T00:00:00Z",
    is_active: true,
    plan: "professional",
    total_calls: 1250,
    calls_today: 15,
    calls_this_week: 89,
    calls_this_month: 342,
    avg_call_duration: 185,
    appointment_rate: 0.42,
    avg_sentiment_score: 0.78,
    estimated_cost_month: 51.30,
  },
  {
    clinic_id: "2",
    clinic_name: "Happy Smiles Dentistry",
    created_at: "2024-11-01T00:00:00Z",
    is_active: true,
    plan: "starter",
    total_calls: 456,
    calls_today: 8,
    calls_this_week: 45,
    calls_this_month: 178,
    avg_call_duration: 165,
    appointment_rate: 0.35,
    avg_sentiment_score: 0.72,
    estimated_cost_month: 26.70,
  },
  {
    clinic_id: "3",
    clinic_name: "Downtown Family Dental",
    created_at: "2024-09-20T00:00:00Z",
    is_active: true,
    plan: "professional",
    total_calls: 2100,
    calls_today: 22,
    calls_this_week: 156,
    calls_this_month: 589,
    avg_call_duration: 210,
    appointment_rate: 0.48,
    avg_sentiment_score: 0.85,
    estimated_cost_month: 88.35,
  },
];

const mockCallSummaries: CallSummary[] = [
  {
    call_id: "c1",
    clinic_name: "Sunny Dental Care",
    timestamp: new Date().toISOString(),
    duration_seconds: 245,
    outcome: "appointment_booked",
    sentiment: "positive",
    quality_score: 92,
    summary_anonymized: "[PATIENT] called to schedule a cleaning appointment. AI successfully booked for [DATE] at 2:00 PM. Patient was satisfied.",
    topics: ["cleaning", "appointment scheduling", "availability"],
    needs_review: false,
  },
  {
    call_id: "c2",
    clinic_name: "Happy Smiles Dentistry",
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    duration_seconds: 180,
    outcome: "question_answered",
    sentiment: "neutral",
    quality_score: 78,
    summary_anonymized: "[PATIENT] asked about insurance coverage for root canal. AI provided general information and offered to have office call back.",
    topics: ["insurance", "root canal", "pricing"],
    needs_review: false,
  },
  {
    call_id: "c3",
    clinic_name: "Downtown Family Dental",
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    duration_seconds: 95,
    outcome: "hung_up",
    sentiment: "frustrated",
    quality_score: 45,
    summary_anonymized: "[PATIENT] expressed frustration about wait times. Call ended abruptly. Possible issue with appointment availability.",
    topics: ["wait times", "scheduling", "availability"],
    needs_review: true,
    review_reason: "Patient hung up - frustrated",
  },
];

const mockSystemHealth: SystemHealth = {
  status: "healthy",
  uptime_hours: 720,
  services: {
    openai: "configured",
    gemini: "configured",
    deepgram: "configured",
    twilio: "configured",
    huggingface: "configured",
    database: "connected",
    redis: "configured",
  },
  recent_errors: [],
  recommendations: [
    "Consider upgrading Gemini to paid tier for higher limits",
    "Add more phone numbers for scaling",
  ],
};

export default function SuperAdminPage() {
  const router = useRouter();
  const [apiUsage, setApiUsage] = useState<APIUsage>(mockAPIUsage);
  const [clinics, setClinics] = useState<ClinicUsage[]>(mockClinics);
  const [callSummaries, setCallSummaries] = useState<CallSummary[]>(mockCallSummaries);
  const [systemHealth, setSystemHealth] = useState<SystemHealth>(mockSystemHealth);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState("overview");
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);

  // Check if user is a super admin
  useEffect(() => {
    const checkAuth = async () => {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      
      if (!user) {
        // Not logged in, redirect to login
        router.push("/login");
        return;
      }
      
      const email = user.email?.toLowerCase() || "";
      setUserEmail(email);
      
      // Check if user is a super admin
      const isAdmin = SUPER_ADMIN_EMAILS.map(e => e.toLowerCase()).includes(email);
      setIsAuthorized(isAdmin);
      setAuthChecked(true);
      
      if (isAdmin) {
        setIsLoading(false);
      }
    };
    
    checkAuth();
  }, [router]);

  // Fetch data from API (when backend is connected)
  const refreshData = useCallback(async () => {
    if (!userEmail) return;
    
    setIsLoading(true);
    try {
      // In production, uncomment these to fetch real data:
      // const headers = { 'X-User-Email': userEmail };
      // const apiUsageRes = await fetch('/api/superadmin/api-usage', { headers });
      // const clinicsRes = await fetch('/api/superadmin/clinics', { headers });
      // const callsRes = await fetch('/api/superadmin/calls/summaries', { headers });
      // const healthRes = await fetch('/api/superadmin/health', { headers });
      
      // For now, use mock data and keep setters exercised
      await new Promise(resolve => setTimeout(resolve, 500));
      setApiUsage(mockAPIUsage);
      setClinics(mockClinics);
      setCallSummaries(mockCallSummaries);
      setSystemHealth(mockSystemHealth);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    setIsLoading(false);
  }, [userEmail]);

  useEffect(() => {
    if (isAuthorized) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      refreshData();
    }
  }, [isAuthorized, refreshData]);

  // Show loading while checking auth
  if (!authChecked) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto text-[#1B3A7C]" />
          <p className="mt-4 text-muted-foreground">Checking authorization...</p>
        </div>
      </div>
    );
  }

  // Show access denied if not authorized
  if (!isAuthorized) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
              <Lock className="h-8 w-8 text-red-600" />
            </div>
            <CardTitle className="text-2xl text-red-600">Access Denied</CardTitle>
            <CardDescription>
              You are not authorized to access the Super Admin dashboard.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center space-y-4">
            <p className="text-sm text-muted-foreground">
              Logged in as: <strong>{userEmail}</strong>
            </p>
            <p className="text-sm text-muted-foreground">
              Only platform administrators can access this page.
            </p>
            <Button onClick={() => router.push("/dashboard")} className="w-full">
              Go to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
      case "active":
      case "configured":
      case "connected":
        return "bg-green-100 text-green-800";
      case "degraded":
        return "bg-yellow-100 text-yellow-800";
      case "down":
      case "error":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
      case "very_positive":
        return "text-green-600";
      case "neutral":
        return "text-gray-600";
      case "negative":
      case "frustrated":
        return "text-red-600";
      default:
        return "text-gray-600";
    }
  };

  return (
    <div className="flex-1 space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1B3A7C]">Super Admin Dashboard</h1>
          <p className="text-muted-foreground">Monitor your entire platform in one place</p>
        </div>
        <div className="flex items-center gap-4">
          <Badge className={getStatusColor(systemHealth.status)}>
            System: {systemHealth.status}
          </Badge>
          <Button onClick={refreshData} disabled={isLoading} variant="outline">
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Alerts */}
      {apiUsage.alerts.length > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-orange-800">
              <AlertTriangle className="h-5 w-5" />
              Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1">
              {apiUsage.alerts.map((alert, i) => (
                <li key={i} className="text-orange-700">{alert}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Clinics</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{clinics.length}</div>
            <p className="text-xs text-muted-foreground">
              ${clinics.length * 99}/month revenue
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Calls Today</CardTitle>
            <Phone className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {clinics.reduce((sum, c) => sum + c.calls_today, 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              {clinics.reduce((sum, c) => sum + c.calls_this_month, 0)} this month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cost Today</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${apiUsage.total_estimated_cost_today.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">
              ${apiUsage.total_estimated_cost_month.toFixed(2)} this month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Quality Score</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(clinics.reduce((sum, c) => sum + c.avg_sentiment_score, 0) / clinics.length * 100).toFixed(0)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {(clinics.reduce((sum, c) => sum + c.appointment_rate, 0) / clinics.length * 100).toFixed(0)}% booking rate
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="api-usage">API Usage</TabsTrigger>
          <TabsTrigger value="clinics">Clinics</TabsTrigger>
          <TabsTrigger value="calls">Call Summaries</TabsTrigger>
          <TabsTrigger value="system">System Health</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Revenue & Costs */}
            <Card>
              <CardHeader>
                <CardTitle>Monthly Financials</CardTitle>
                <CardDescription>Revenue vs. costs this month</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Revenue</span>
                    <span className="text-xl font-bold text-green-600">${clinics.length * 99}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">AI Costs</span>
                    <span className="text-xl font-bold text-red-600">-${apiUsage.total_estimated_cost_month.toFixed(2)}</span>
                  </div>
                  <div className="border-t pt-4 flex justify-between items-center">
                    <span className="text-sm font-medium">Gross Profit</span>
                    <span className="text-xl font-bold text-[#1B3A7C]">
                      ${(clinics.length * 99 - apiUsage.total_estimated_cost_month).toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Margin</span>
                    <span className="text-lg font-semibold text-green-600">
                      {((clinics.length * 99 - apiUsage.total_estimated_cost_month) / (clinics.length * 99) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Top Clinics */}
            <Card>
              <CardHeader>
                <CardTitle>Top Clinics by Usage</CardTitle>
                <CardDescription>Most active customers this month</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {clinics
                    .sort((a, b) => b.calls_this_month - a.calls_this_month)
                    .slice(0, 5)
                    .map((clinic, i) => (
                      <div key={clinic.clinic_id} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-lg font-bold text-muted-foreground">#{i + 1}</span>
                          <div>
                            <p className="font-medium">{clinic.clinic_name}</p>
                            <p className="text-xs text-muted-foreground">
                              {clinic.calls_this_month} calls · {(clinic.appointment_rate * 100).toFixed(0)}% booking
                            </p>
                          </div>
                        </div>
                        <Badge variant="outline">{clinic.plan}</Badge>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* HIPAA Compliance Note */}
          <Card className="border-blue-200 bg-blue-50">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-blue-800">
                <Shield className="h-5 w-5" />
                HIPAA Compliance
              </CardTitle>
            </CardHeader>
            <CardContent className="text-blue-700 text-sm">
              <p>
                All call summaries shown are <strong>anonymized</strong>. Patient names, phone numbers, 
                and other PHI are automatically redacted. For full transcript access, ensure clinics 
                have proper patient consent and a signed Business Associate Agreement (BAA).
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Usage Tab */}
        <TabsContent value="api-usage" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {/* OpenAI */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  OpenAI
                </CardTitle>
                <CardDescription>Voice conversations (real-time)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Status</span>
                    <Badge className={getStatusColor(apiUsage.openai.status)}>
                      {apiUsage.openai.status}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Today</span>
                    <span className="font-medium">${apiUsage.openai.cost_today}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">This Month</span>
                    <span className="font-medium">${apiUsage.openai.cost_month}</span>
                  </div>
                  {apiUsage.openai.remaining_percent && (
                    <div className="pt-2">
                      <div className="flex justify-between text-xs mb-1">
                        <span>Credits Remaining</span>
                        <span>{apiUsage.openai.remaining_percent}%</span>
                      </div>
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-green-500 rounded-full"
                          style={{ width: `${apiUsage.openai.remaining_percent}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Gemini */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Gemini
                </CardTitle>
                <CardDescription>Analysis (50% cheaper!)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Status</span>
                    <Badge className={getStatusColor(apiUsage.gemini.status)}>
                      {apiUsage.gemini.status}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Today</span>
                    <span className="font-medium">${apiUsage.gemini.cost_today} (FREE tier)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Requests Left</span>
                    <span className="font-medium">{apiUsage.gemini.requests_remaining}/day</span>
                  </div>
                  <div className="pt-2 p-2 bg-green-50 rounded-lg text-center">
                    <span className="text-green-700 text-sm font-medium">💰 Saving 50% on analysis!</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* HuggingFace */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  🤗 HuggingFace
                </CardTitle>
                <CardDescription>Embeddings (FREE!)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Status</span>
                    <Badge className={getStatusColor(apiUsage.huggingface.status)}>
                      {apiUsage.huggingface.status}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Cost</span>
                    <span className="font-bold text-green-600">$0.00 (FREE!)</span>
                  </div>
                  <div className="pt-2 p-2 bg-green-50 rounded-lg text-center">
                    <span className="text-green-700 text-sm font-medium">🆓 Unlimited embeddings!</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Deepgram */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Phone className="h-5 w-5" />
                  Deepgram
                </CardTitle>
                <CardDescription>Voice Agent (STT + LLM + TTS)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Status</span>
                    <Badge className={getStatusColor(apiUsage.deepgram.status)}>
                      {apiUsage.deepgram.status}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Today</span>
                    <span className="font-medium">${apiUsage.deepgram.cost_today}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">This Month</span>
                    <span className="font-medium">${apiUsage.deepgram.cost_month}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Twilio */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Phone className="h-5 w-5" />
                  Twilio
                </CardTitle>
                <CardDescription>Phone calls & SMS</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Status</span>
                    <Badge className={getStatusColor(apiUsage.twilio.status)}>
                      {apiUsage.twilio.status}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Balance</span>
                    <span className="font-bold text-lg">${apiUsage.twilio.balance}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">This Month</span>
                    <span className="font-medium">${apiUsage.twilio.cost_month}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Clinics Tab */}
        <TabsContent value="clinics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>All Clinics</CardTitle>
              <CardDescription>Usage and performance by clinic</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Clinic</TableHead>
                    <TableHead>Plan</TableHead>
                    <TableHead className="text-right">Calls Today</TableHead>
                    <TableHead className="text-right">This Month</TableHead>
                    <TableHead className="text-right">Booking Rate</TableHead>
                    <TableHead className="text-right">Sentiment</TableHead>
                    <TableHead className="text-right">Est. Cost</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {clinics.map((clinic) => (
                    <TableRow key={clinic.clinic_id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{clinic.clinic_name}</p>
                          <p className="text-xs text-muted-foreground">
                            Since {new Date(clinic.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{clinic.plan}</Badge>
                      </TableCell>
                      <TableCell className="text-right">{clinic.calls_today}</TableCell>
                      <TableCell className="text-right">{clinic.calls_this_month}</TableCell>
                      <TableCell className="text-right">
                        <span className={clinic.appointment_rate >= 0.4 ? "text-green-600" : "text-yellow-600"}>
                          {(clinic.appointment_rate * 100).toFixed(0)}%
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <span className={clinic.avg_sentiment_score >= 0.7 ? "text-green-600" : "text-yellow-600"}>
                          {(clinic.avg_sentiment_score * 100).toFixed(0)}%
                        </span>
                      </TableCell>
                      <TableCell className="text-right">${clinic.estimated_cost_month.toFixed(2)}</TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Call Summaries Tab */}
        <TabsContent value="calls" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Call Summaries</CardTitle>
              <CardDescription>
                Anonymized for HIPAA compliance. Patient names and PHI are redacted.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {callSummaries.map((call) => (
                  <div 
                    key={call.call_id} 
                    className={`p-4 border rounded-lg ${call.needs_review ? 'border-red-200 bg-red-50' : 'border-gray-200'}`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{call.clinic_name}</span>
                          {call.needs_review && (
                            <Badge variant="destructive">Needs Review</Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {new Date(call.timestamp).toLocaleString()} · {Math.floor(call.duration_seconds / 60)}:{(call.duration_seconds % 60).toString().padStart(2, '0')} min
                        </p>
                      </div>
                      <div className="text-right">
                        <Badge variant="outline">{call.outcome.replace(/_/g, ' ')}</Badge>
                        <p className={`text-sm ${getSentimentColor(call.sentiment)}`}>
                          {call.sentiment} · {call.quality_score}% quality
                        </p>
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{call.summary_anonymized}</p>
                    <div className="flex gap-2 flex-wrap">
                      {call.topics.map((topic) => (
                        <Badge key={topic} variant="secondary" className="text-xs">{topic}</Badge>
                      ))}
                    </div>
                    {call.review_reason && (
                      <p className="mt-2 text-sm text-red-600">⚠️ {call.review_reason}</p>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Health Tab */}
        <TabsContent value="system" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Server className="h-5 w-5" />
                  Service Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(systemHealth.services).map(([service, status]) => (
                    <div key={service} className="flex justify-between items-center">
                      <span className="capitalize">{service}</span>
                      <Badge className={getStatusColor(status)}>
                        {status === "configured" || status === "connected" ? (
                          <><CheckCircle2 className="h-3 w-3 mr-1" /> {status}</>
                        ) : (
                          status
                        )}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recommendations</CardTitle>
                <CardDescription>Ways to improve your setup</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {systemHealth.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <span className="text-yellow-500">💡</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>System Uptime</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <div className="text-5xl font-bold text-green-600">99.9%</div>
                <p className="text-muted-foreground mt-2">
                  {systemHealth.uptime_hours} hours since last restart
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
