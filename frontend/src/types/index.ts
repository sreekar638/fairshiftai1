export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'worker' | 'supervisor' | 'admin';
  hourly_rate: number;
  worker_code?: string;
  phone?: string;
  language_pref: string;
  site_id?: number;
  org_id: number;
  created_at: string;
  organization_name: string;
  organization_industry: string;
  site_name?: string;
}

export interface Shift {
  id: number;
  org_id: number;
  user_id: number;
  site_id?: number;
  scheduled_start: string;
  scheduled_end: string;
  actual_check_in?: string;
  actual_check_out?: string;
  regular_hours: number;
  overtime_hours: number;
  status: 'scheduled' | 'in_progress' | 'completed' | 'missed';
  notes?: string;
  user_name?: string;
  site_name?: string;
}

export interface Payslip {
  id: number;
  org_id: number;
  user_id: number;
  period_start: string;
  period_end: string;
  base_hourly_rate: number;
  regular_hours: number;
  overtime_hours: number;
  overtime_rate: number;
  allowances: number;
  deductions: number;
  gross_pay: number;
  net_pay: number;
  status: string;
  synthetic_disclaimer: string;
  created_at: string;
  user_name?: string;
}

export interface SafetyReport {
  id: number;
  ref_number: string;
  org_id: number;
  user_id?: number;
  site_id?: number;
  category: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  is_anonymous: boolean;
  status: 'reported' | 'investigating' | 'resolved' | 'dismissed';
  resolution_notes?: string;
  reported_at: string;
  resolved_at?: string;
  reporter_name?: string;
  site_name?: string;
}

export interface SkillItem {
  id: number;
  org_id: number;
  user_id: number;
  title: string;
  category: string;
  issuer: string;
  issue_date: string;
  expiry_date?: string;
  is_verified: boolean;
  verified_by?: string;
  verification_notes?: string;
  created_at: string;
  user_name?: string;
}

export interface FatigueAlert {
  id: number;
  org_id: number;
  user_id: number;
  shift_id?: number;
  rule_code: string;
  severity: 'info' | 'warning' | 'critical';
  title: string;
  details: string;
  suggested_action: string;
  status: string;
  created_at: string;
  user_name?: string;
}

export interface DashboardSummary {
  organization_name: string;
  industry: string;
  total_workers: number;
  active_shifts_now: number;
  total_hours_worked: number;
  total_overtime_hours: number;
  unresolved_safety_reports: number;
  critical_fatigue_alerts: number;
  average_worker_satisfaction: number;
  verified_skills_percentage: number;
  weekly_attendance_trend: {
    day: string;
    date: string;
    regularHours: number;
    overtimeHours: number;
    attendees: number;
  }[];
  fatigue_by_category: { name: string; value: number }[];
  safety_by_category: { name: string; count: number }[];
}

export interface AIRecommendation {
  category: string;
  title: string;
  observation: string;
  evidence_metric: string;
  recommended_action: string;
  confidence: number;
  source: string;
}
