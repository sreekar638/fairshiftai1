import { User, Shift, Payslip, SafetyReport, SkillItem, FatigueAlert, DashboardSummary, AIRecommendation } from '../types';

const API_BASE = '/api/v1';

// Initial pre-loaded demo personas
export const DEMO_USERS: User[] = [
  {
    id: 4,
    email: "worker.construction@fairshift.io",
    full_name: "Ravi Kumar (Tower Crane Specialist)",
    role: "worker",
    hourly_rate: 21.00,
    worker_code: "CST-WRK-01",
    phone: "+1 555-0103",
    language_pref: "en",
    org_id: 1,
    site_id: 1,
    created_at: new Date().toISOString(),
    organization_name: "Apex BuildTech Infrastructure",
    organization_industry: "construction",
    site_name: "Tower A - High-Rise Foundation"
  },
  {
    id: 2,
    email: "admin.construction@fairshift.io",
    full_name: "Marcus Vance (Site Director)",
    role: "admin",
    hourly_rate: 32.00,
    worker_code: "CST-ADM-01",
    phone: "+1 555-0101",
    language_pref: "en",
    org_id: 1,
    site_id: 1,
    created_at: new Date().toISOString(),
    organization_name: "Apex BuildTech Infrastructure",
    organization_industry: "construction",
    site_name: "Tower A - High-Rise Foundation"
  },
  {
    id: 8,
    email: "worker.college@fairshift.io",
    full_name: "Ananya Sharma (Senior Lab Instructor)",
    role: "worker",
    hourly_rate: 24.00,
    worker_code: "EDU-WRK-01",
    phone: "+1 555-0203",
    language_pref: "en",
    org_id: 2,
    site_id: 3,
    created_at: new Date().toISOString(),
    organization_name: "St. Jude Metropolitan College",
    organization_industry: "education",
    site_name: "Faculty of Science & Chemical Labs"
  },
  {
    id: 6,
    email: "admin.college@fairshift.io",
    full_name: "Dr. Eleanor Vance (Dean of Operations)",
    role: "admin",
    hourly_rate: 38.00,
    worker_code: "EDU-ADM-01",
    phone: "+1 555-0201",
    language_pref: "en",
    org_id: 2,
    site_id: 3,
    created_at: new Date().toISOString(),
    organization_name: "St. Jude Metropolitan College",
    organization_industry: "education",
    site_name: "Faculty of Science & Chemical Labs"
  }
];

class ApiClient {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('fairshift_token');
  }

  setToken(t: string | null) {
    this.token = t;
    if (t) localStorage.setItem('fairshift_token', t);
    else localStorage.removeItem('fairshift_token');
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
      if (!res.ok) {
        throw new Error(`API error: ${res.statusText}`);
      }
      return await res.json();
    } catch (err) {
      console.warn(`Fetch error for ${path}:`, err);
      throw err;
    }
  }

  async login(email: string, password: string): Promise<{ access_token: string; user: User }> {
    try {
      const res = await this.request<{ access_token: string; user: User }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });
      this.setToken(res.access_token);
      return res;
    } catch {
      // Offline fallback: match demo user
      const matched = DEMO_USERS.find(u => u.email === email) || DEMO_USERS[0];
      const fakeToken = `simulated-jwt-token-for-${matched.email}`;
      this.setToken(fakeToken);
      return { access_token: fakeToken, user: matched };
    }
  }

  async getShifts(): Promise<Shift[]> {
    try {
      return await this.request<Shift[]>('/attendance/my-shifts');
    } catch {
      return [
        {
          id: 101,
          org_id: 1,
          user_id: 4,
          scheduled_start: new Date(Date.now() - 3600000 * 3).toISOString(),
          scheduled_end: new Date(Date.now() + 3600000 * 5).toISOString(),
          actual_check_in: new Date(Date.now() - 3600000 * 3).toISOString(),
          regular_hours: 3.0,
          overtime_hours: 0.0,
          status: 'in_progress',
          notes: 'High-Rise Tower A Crane Inspection & Operations',
          site_name: 'Tower A - High-Rise Foundation'
        },
        {
          id: 100,
          org_id: 1,
          user_id: 4,
          scheduled_start: new Date(Date.now() - 86400000).toISOString(),
          scheduled_end: new Date(Date.now() - 86400000 + 3600000 * 13).toISOString(),
          actual_check_in: new Date(Date.now() - 86400000).toISOString(),
          actual_check_out: new Date(Date.now() - 86400000 + 3600000 * 13.5).toISOString(),
          regular_hours: 8.0,
          overtime_hours: 5.5,
          status: 'completed',
          notes: 'Overtime emergency concrete reinforcement placement',
          site_name: 'Tower A - High-Rise Foundation'
        }
      ];
    }
  }

  async checkIn(method: 'qr' | 'manual', qrToken?: string, notes?: string): Promise<Shift> {
    try {
      return await this.request<Shift>('/attendance/check-in', {
        method: 'POST',
        body: JSON.stringify({ method, qr_token: qrToken, notes })
      });
    } catch {
      return {
        id: Date.now(),
        org_id: 1,
        user_id: 4,
        scheduled_start: new Date().toISOString(),
        scheduled_end: new Date(Date.now() + 3600000 * 8).toISOString(),
        actual_check_in: new Date().toISOString(),
        regular_hours: 0,
        overtime_hours: 0,
        status: 'in_progress',
        notes: notes || 'Verified Site Attendance Recorded',
        site_name: method === 'qr' ? 'Tower A Gate 1 (QR Verified)' : 'Manual Fallback Check-In'
      };
    }
  }

  async checkOut(notes?: string): Promise<Shift> {
    try {
      return await this.request<Shift>('/attendance/check-out', {
        method: 'POST',
        body: JSON.stringify({ method: 'manual', notes })
      });
    } catch {
      return {
        id: Date.now(),
        org_id: 1,
        user_id: 4,
        scheduled_start: new Date(Date.now() - 3600000 * 8.5).toISOString(),
        scheduled_end: new Date().toISOString(),
        actual_check_in: new Date(Date.now() - 3600000 * 8.5).toISOString(),
        actual_check_out: new Date().toISOString(),
        regular_hours: 8.0,
        overtime_hours: 0.5,
        status: 'completed',
        notes: notes || 'Shift completed safely.',
        site_name: 'Tower A - High-Rise Foundation'
      };
    }
  }

  async getPayslips(): Promise<Payslip[]> {
    try {
      return await this.request<Payslip[]>('/payslips/my-payslips');
    } catch {
      return [
        {
          id: 501,
          org_id: 1,
          user_id: 4,
          period_start: new Date(Date.now() - 86400000 * 14).toISOString(),
          period_end: new Date(Date.now() - 86400000 * 1).toISOString(),
          base_hourly_rate: 21.00,
          regular_hours: 80.0,
          overtime_hours: 14.5,
          overtime_rate: 1.5,
          allowances: 120.00,
          deductions: 145.50,
          gross_pay: 2256.75,
          net_pay: 2111.25,
          status: 'approved',
          synthetic_disclaimer: 'Synthetic demonstration payslip for FairShift AI — not legal tax/wage counsel.',
          created_at: new Date().toISOString()
        }
      ];
    }
  }

  async getReports(): Promise<SafetyReport[]> {
    try {
      return await this.request<SafetyReport[]>('/reports/my-reports');
    } catch {
      return [
        {
          id: 301,
          ref_number: 'SAF-2026-081',
          org_id: 1,
          category: 'hazard',
          title: 'Unsecured Perimeter Guardrail on 14th Floor Slab',
          description: 'The safety toe-board and wire rope perimeter railing on the east edge of floor 14 are loose after wind gusts.',
          priority: 'critical',
          is_anonymous: false,
          status: 'investigating',
          resolution_notes: 'Safety officer Marcus dispatched scaffolding team for immediate tie-off and re-anchoring.',
          reported_at: new Date(Date.now() - 86400000).toISOString(),
          reporter_name: 'Ravi Kumar',
          site_name: 'Tower A - High-Rise Foundation'
        },
        {
          id: 302,
          ref_number: 'SAF-2026-082',
          org_id: 1,
          category: 'equipment',
          title: 'Forklift Hydraulic Fluid Leak Near Pedestrian Walkway',
          description: 'Forklift FL-04 has a steady oil leak near the main material staging zone causing severe slip hazard.',
          priority: 'high',
          is_anonymous: true,
          status: 'reported',
          reported_at: new Date(Date.now() - 43200000).toISOString(),
          reporter_name: 'Anonymous Worker',
          site_name: 'Pre-Cast Concrete Yard B'
        }
      ];
    }
  }

  async submitReport(payload: { category: string; title: string; description: string; priority: string; is_anonymous: boolean }): Promise<SafetyReport> {
    try {
      return await this.request<SafetyReport>('/reports', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
    } catch {
      return {
        id: Date.now(),
        ref_number: `SAF-2026-${Math.floor(100 + Math.random() * 900)}`,
        org_id: 1,
        ...payload,
        priority: payload.priority as any,
        status: 'reported',
        reported_at: new Date().toISOString(),
        reporter_name: payload.is_anonymous ? 'Anonymous Worker' : 'Current User',
        site_name: 'Site Facility'
      };
    }
  }

  async updateReportStatus(id: number, status: string, resolution_notes?: string): Promise<any> {
    try {
      return await this.request<any>(`/reports/${id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status, resolution_notes })
      });
    } catch {
      return { status, resolution_notes };
    }
  }

  async submitFeedback(data: { condition_rating: number; workload_rating: number; break_rating: number; facility_rating: number; supervisor_rating: number; comments?: string }): Promise<any> {
    try {
      return await this.request('/feedback', {
        method: 'POST',
        body: JSON.stringify(data)
      });
    } catch {
      return { message: 'Feedback recorded' };
    }
  }

  async getSkills(): Promise<SkillItem[]> {
    try {
      return await this.request<SkillItem[]>('/skills/my-skills');
    } catch {
      return [
        {
          id: 401,
          org_id: 1,
          user_id: 4,
          title: 'Heavy Tower Crane Operator Certification (Class A)',
          category: 'machinery',
          issuer: 'National Heavy Machinery Safety Board',
          issue_date: '2025-04-10',
          expiry_date: '2027-04-10',
          is_verified: true,
          verified_by: 'Marcus Vance (Site Director)',
          verification_notes: 'Verified against national crane database #CRN-9981',
          created_at: new Date().toISOString()
        },
        {
          id: 402,
          org_id: 1,
          user_id: 4,
          title: 'OSHA 30-Hour Construction Safety & Fall Protection',
          category: 'safety',
          issuer: 'Occupational Safety Council',
          issue_date: '2025-08-15',
          expiry_date: '2027-08-15',
          is_verified: true,
          verified_by: 'Marcus Vance (Site Director)',
          verification_notes: 'Completed 30-hour course.',
          created_at: new Date().toISOString()
        },
        {
          id: 403,
          org_id: 1,
          user_id: 4,
          title: 'First Aid & CPR Level 2 Responder',
          category: 'first_aid',
          issuer: 'Red Crescent & Safety Institute',
          issue_date: '2026-01-10',
          is_verified: false,
          created_at: new Date().toISOString()
        }
      ];
    }
  }

  async addSkill(payload: { title: string; category: string; issuer: string; issue_date: string; expiry_date?: string }): Promise<SkillItem> {
    try {
      return await this.request<SkillItem>('/skills', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
    } catch {
      return {
        id: Date.now(),
        org_id: 1,
        user_id: 4,
        ...payload,
        is_verified: false,
        created_at: new Date().toISOString()
      };
    }
  }

  async verifySkill(id: number, is_verified: boolean, notes?: string): Promise<any> {
    try {
      return await this.request(`/skills/${id}/verify`, {
        method: 'PATCH',
        body: JSON.stringify({ is_verified, verification_notes: notes })
      });
    } catch {
      return { id, is_verified, verification_notes: notes };
    }
  }

  async getFatigueAlerts(): Promise<FatigueAlert[]> {
    try {
      return await this.request<FatigueAlert[]>('/fatigue/my-alerts');
    } catch {
      return [
        {
          id: 601,
          org_id: 1,
          user_id: 4,
          rule_code: 'EXCESSIVE_HOURS_CRITICAL',
          severity: 'critical',
          title: 'Critical Shift Duration Exceeded',
          details: 'Shift duration was 13.5 hours (exceeded mandatory 12.0 hour safety threshold).',
          suggested_action: 'Mandate minimum 12-hour recovery rest before next scheduled dispatch.',
          status: 'active',
          created_at: new Date(Date.now() - 86400000).toISOString()
        }
      ];
    }
  }

  async getDashboardSummary(): Promise<DashboardSummary> {
    try {
      return await this.request<DashboardSummary>('/analytics/dashboard');
    } catch {
      return {
        organization_name: 'Apex BuildTech Infrastructure',
        industry: 'construction',
        total_workers: 48,
        active_shifts_now: 14,
        total_hours_worked: 1840.5,
        total_overtime_hours: 210.0,
        unresolved_safety_reports: 3,
        critical_fatigue_alerts: 2,
        average_worker_satisfaction: 4.4,
        verified_skills_percentage: 86.5,
        weekly_attendance_trend: [
          { day: 'Mon', date: 'Oct 21', regularHours: 320, overtimeHours: 32, attendees: 40 },
          { day: 'Tue', date: 'Oct 22', regularHours: 340, overtimeHours: 45, attendees: 42 },
          { day: 'Wed', date: 'Oct 23', regularHours: 335, overtimeHours: 38, attendees: 41 },
          { day: 'Thu', date: 'Oct 24', regularHours: 350, overtimeHours: 52, attendees: 43 },
          { day: 'Fri', date: 'Oct 25', regularHours: 345, overtimeHours: 40, attendees: 42 },
          { day: 'Sat', date: 'Oct 26', regularHours: 120, overtimeHours: 18, attendees: 15 },
          { day: 'Sun', date: 'Oct 27', regularHours: 90, overtimeHours: 12, attendees: 11 }
        ],
        fatigue_by_category: [
          { name: 'Shift > 12h', value: 3 },
          { name: 'Rest < 8h', value: 2 },
          { name: 'Consecutive Days', value: 1 }
        ],
        safety_by_category: [
          { name: 'Hazard', count: 4 },
          { name: 'Equipment', count: 2 },
          { name: 'Workload', count: 1 }
        ]
      };
    }
  }

  async getAIRecommendations(): Promise<AIRecommendation[]> {
    try {
      return await this.request<AIRecommendation[]>('/ai/recommendations');
    } catch {
      return [
        {
          category: 'Overtime & Workload (SDG 8.5)',
          title: 'Excessive Overtime Strain Detected',
          observation: 'Overtime accounts for 21.4% of all logged hours, exceeding the 20% sustainable threshold.',
          evidence_metric: '210.0 OT hours logged against 980 regular hours across Tower A.',
          recommended_action: 'Review shift staffing allocations and dispatch relief crew to mitigate fatigue accidents.',
          confidence: 0.94,
          source: 'deterministic_rule'
        },
        {
          category: 'Safety & Compliance (SDG 8.8)',
          title: 'Immediate Safety Hazard Intervention Required',
          observation: '2 high/critical priority workplace reports remain active on Floor 14 perimeter.',
          evidence_metric: 'Unresolved critical cases: SAF-2026-081, SAF-2026-082.',
          recommended_action: 'Dispatch certified safety supervisor Marcus Vance to verify tie-off and re-anchoring before concrete pour.',
          confidence: 0.97,
          source: 'deterministic_rule'
        },
        {
          category: 'Skill Passport Verification',
          title: 'Skill Verification Backlog',
          observation: '13.5% of self-declared worker certifications remain pending supervisor audit.',
          evidence_metric: '7 pending qualification records awaiting inspection.',
          recommended_action: 'Perform weekly fast-track verification audits in the supervisor portal.',
          confidence: 0.89,
          source: 'deterministic_rule'
        }
      ];
    }
  }
}

export const api = new ApiClient();
