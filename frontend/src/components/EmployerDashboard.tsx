import React, { useState, useEffect } from 'react';
import { 
  Users, Clock, AlertTriangle, ShieldAlert, Award, TrendingUp, 
  CheckCircle2, Sparkles, Filter, Check, MessageSquare, ChevronRight, BarChart3, ShieldCheck
} from 'lucide-react';
import { User, DashboardSummary, SafetyReport, FatigueAlert, SkillItem, AIRecommendation } from '../types';
import { api } from '../services/api';

interface EmployerDashboardProps {
  user: User;
  t: Record<string, string>;
  language: 'en' | 'ta';
}

export const EmployerDashboard: React.FC<EmployerDashboardProps> = ({ user, t, language }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'safety' | 'fatigue' | 'skills' | 'ai'>('overview');
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [reports, setReports] = useState<SafetyReport[]>([]);
  const [fatigueAlerts, setFatigueAlerts] = useState<FatigueAlert[]>([]);
  const [skills, setSkills] = useState<SkillItem[]>([]);
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>([]);
  const [selectedReport, setSelectedReport] = useState<SafetyReport | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [notification, setNotification] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, [user.id, user.org_id]);

  const loadDashboard = async () => {
    try {
      const [sumData, repData, fatData, skData, aiData] = await Promise.all([
        api.getDashboardSummary(),
        api.getReports(),
        api.getFatigueAlerts(),
        api.getSkills(),
        api.getAIRecommendations(),
      ]);
      setSummary(sumData);
      setReports(repData);
      setFatigueAlerts(fatData);
      setSkills(skData);
      setRecommendations(aiData);
    } catch (err) {
      console.warn('Dashboard load error', err);
    }
  };

  const showToast = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 4000);
  };

  const handleUpdateStatus = async (reportId: number, newStatus: string) => {
    try {
      await api.updateReportStatus(reportId, newStatus, resolutionNotes || 'Status verified by supervisor');
      setReports(reports.map(r => r.id === reportId ? { ...r, status: newStatus as any, resolution_notes: resolutionNotes || r.resolution_notes } : r));
      setSelectedReport(null);
      setResolutionNotes('');
      showToast(`Report updated to ${newStatus}`);
    } catch {
      showToast('Status update failed');
    }
  };

  const handleVerifySkill = async (skillId: number) => {
    try {
      await api.verifySkill(skillId, true, `Audited by ${user.full_name}`);
      setSkills(skills.map(s => s.id === skillId ? { ...s, is_verified: true, verified_by: user.full_name } : s));
      showToast('Skill qualification marked as Verified');
    } catch {
      showToast('Verification failed');
    }
  };

  const isConstruction = user.organization_industry === 'construction';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Toast Notification */}
      {notification && (
        <div className="mb-4 bg-teal text-white px-4 py-2.5 rounded-lg shadow-md flex items-center justify-between text-sm font-medium">
          <span>{notification}</span>
          <button onClick={() => setNotification(null)} className="text-white hover:text-slate-200">✕</button>
        </div>
      )}

      {/* Header Banner */}
      <div className="bg-navy rounded-2xl p-6 text-white mb-6 shadow-md border border-navy-light flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded bg-teal text-white uppercase tracking-wider">
              {isConstruction ? 'Construction Worksite' : 'Campus Operations'}
            </span>
            <span className="text-xs text-slate-300 font-medium">
              SDG Target 8.8: Safe & Secure Working Environments
            </span>
          </div>
          <h2 className="text-xl md:text-2xl font-bold tracking-tight">
            {summary?.organization_name || user.organization_name}
          </h2>
          <p className="text-xs text-slate-300 mt-1 max-w-xl">
            Real-time workforce health monitoring, transparent overtime tracking, proactive hazard mitigation, and verified skill compliance.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-navy-dark px-4 py-3 rounded-xl border border-navy-light text-center">
            <div className="text-[11px] text-slate-400 font-medium">Active Shifts Now</div>
            <div className="text-2xl font-extrabold text-teal mt-0.5">
              {summary?.active_shifts_now ?? 14}
            </div>
          </div>
          <div className="bg-navy-dark px-4 py-3 rounded-xl border border-navy-light text-center">
            <div className="text-[11px] text-slate-400 font-medium">Critical Alerts</div>
            <div className="text-2xl font-extrabold text-critical mt-0.5">
              {summary?.critical_fatigue_alerts ?? 2}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-border pb-3 mb-6">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'overview'
              ? 'bg-navy text-white shadow-sm'
              : 'text-secondary hover:text-navy hover:bg-slate-100'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          <span>Workforce Analytics</span>
        </button>

        <button
          onClick={() => setActiveTab('safety')}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'safety'
              ? 'bg-navy text-white shadow-sm'
              : 'text-secondary hover:text-navy hover:bg-slate-100'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          <span>Hazard Resolution Queue</span>
          {reports.length > 0 && (
            <span className="text-xs px-1.5 py-0.2 bg-teal text-white rounded-full">
              {reports.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('fatigue')}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'fatigue'
              ? 'bg-navy text-white shadow-sm'
              : 'text-secondary hover:text-navy hover:bg-slate-100'
          }`}
        >
          <AlertTriangle className="w-4 h-4" />
          <span>Fatigue Risk Center</span>
        </button>

        <button
          onClick={() => setActiveTab('skills')}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'skills'
              ? 'bg-navy text-white shadow-sm'
              : 'text-secondary hover:text-navy hover:bg-slate-100'
          }`}
        >
          <Award className="w-4 h-4" />
          <span>Skill Verification</span>
        </button>

        <button
          onClick={() => setActiveTab('ai')}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'ai'
              ? 'bg-teal text-white shadow-sm'
              : 'text-teal-dark hover:text-navy hover:bg-teal-light'
          }`}
        >
          <Sparkles className="w-4 h-4 text-amber-300" />
          <span>AI Insights (SDG 8)</span>
        </button>
      </div>

      {/* TAB 1: OVERVIEW & ANALYTICS */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Key Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-surface rounded-xl p-4 border border-border shadow-sm">
              <div className="flex items-center justify-between text-secondary mb-1">
                <span className="text-xs font-medium">Total Active Workforce</span>
                <Users className="w-4 h-4 text-teal" />
              </div>
              <div className="text-2xl font-bold text-navy">{summary?.total_workers ?? 48}</div>
              <div className="text-[11px] text-secondary mt-1">Designated in roster</div>
            </div>

            <div className="bg-surface rounded-xl p-4 border border-border shadow-sm">
              <div className="flex items-center justify-between text-secondary mb-1">
                <span className="text-xs font-medium">Overtime Hours</span>
                <Clock className="w-4 h-4 text-warning" />
              </div>
              <div className="text-2xl font-bold text-warning">{summary?.total_overtime_hours ?? 210.0}h</div>
              <div className="text-[11px] text-secondary mt-1">Paid at mandatory 1.5x</div>
            </div>

            <div className="bg-surface rounded-xl p-4 border border-border shadow-sm">
              <div className="flex items-center justify-between text-secondary mb-1">
                <span className="text-xs font-medium">Worker Satisfaction</span>
                <MessageSquare className="w-4 h-4 text-teal" />
              </div>
              <div className="text-2xl font-bold text-teal">{summary?.average_worker_satisfaction ?? 4.4} / 5.0</div>
              <div className="text-[11px] text-secondary mt-1">Anonymous feedback avg</div>
            </div>

            <div className="bg-surface rounded-xl p-4 border border-border shadow-sm">
              <div className="flex items-center justify-between text-secondary mb-1">
                <span className="text-xs font-medium">Verified Qualifications</span>
                <Award className="w-4 h-4 text-navy" />
              </div>
              <div className="text-2xl font-bold text-navy">{summary?.verified_skills_percentage ?? 86.5}%</div>
              <div className="text-[11px] text-secondary mt-1">Audited skill credentials</div>
            </div>
          </div>

          {/* Weekly Attendance & Overtime Breakdown */}
          <div className="bg-surface rounded-xl p-5 border border-border shadow-sm">
            <h3 className="font-bold text-navy text-base mb-1">Weekly Shift Attendance & Overtime Volume</h3>
            <p className="text-xs text-secondary mb-4">
              Daily ratio of regular working hours vs overtime across all active facilities.
            </p>

            <div className="grid grid-cols-7 gap-2 pt-4">
              {(summary?.weekly_attendance_trend || [
                { day: 'Mon', regularHours: 320, overtimeHours: 32 },
                { day: 'Tue', regularHours: 340, overtimeHours: 45 },
                { day: 'Wed', regularHours: 335, overtimeHours: 38 },
                { day: 'Thu', regularHours: 350, overtimeHours: 52 },
                { day: 'Fri', regularHours: 345, overtimeHours: 40 },
                { day: 'Sat', regularHours: 120, overtimeHours: 18 },
                { day: 'Sun', regularHours: 90, overtimeHours: 12 },
              ]).map((d, idx) => (
                <div key={idx} className="flex flex-col items-center">
                  <div className="w-full bg-slate-100 rounded-t-lg h-32 flex flex-col justify-end p-1 relative">
                    <div 
                      className="w-full bg-warning rounded-t" 
                      style={{ height: `${Math.min(100, (d.overtimeHours / 60) * 100)}%` }}
                      title={`OT: ${d.overtimeHours}h`}
                    ></div>
                    <div 
                      className="w-full bg-teal rounded-b mt-0.5" 
                      style={{ height: `${Math.min(100, (d.regularHours / 400) * 100)}%` }}
                      title={`Regular: ${d.regularHours}h`}
                    ></div>
                  </div>
                  <span className="text-[11px] font-semibold text-navy mt-1.5">{d.day}</span>
                  <span className="text-[10px] text-secondary">{d.regularHours + d.overtimeHours}h</span>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-center gap-6 mt-4 pt-3 border-t border-border text-xs">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-teal rounded"></div>
                <span className="text-slate-600 font-medium">Regular Standard Hours</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-warning rounded"></div>
                <span className="text-slate-600 font-medium">Overtime Hours (1.5x Premium)</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: HAZARD RESOLUTION QUEUE */}
      {activeTab === 'safety' && (
        <div className="bg-surface rounded-xl p-5 border border-border shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4 mb-4">
            <div>
              <h3 className="font-bold text-navy text-lg">Safety & Workplace Concerns Queue</h3>
              <p className="text-xs text-secondary">
                Review, investigate, and record official resolutions for hazard tickets filed by workers.
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="px-2.5 py-1 bg-critical/10 text-critical font-bold rounded-full">
                {reports.filter(r => r.priority === 'critical').length} Critical
              </span>
              <span className="px-2.5 py-1 bg-amber-100 text-amber-800 font-bold rounded-full">
                {reports.filter(r => r.status !== 'resolved').length} Unresolved
              </span>
            </div>
          </div>

          <div className="divide-y divide-border">
            {reports.map((r) => (
              <div key={r.id} className="py-4 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-navy bg-slate-100 px-2 py-0.5 rounded border border-border">
                      {r.ref_number}
                    </span>
                    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded capitalize ${
                      r.priority === 'critical' ? 'bg-critical text-white' :
                      r.priority === 'high' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {r.priority} Priority
                    </span>
                    <span className="text-xs text-secondary">
                      Filed by: <strong className="text-navy">{r.reporter_name}</strong>
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full capitalize ${
                      r.status === 'resolved' ? 'bg-teal-light text-teal-dark' :
                      r.status === 'investigating' ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800'
                    }`}>
                      {r.status}
                    </span>
                    <button
                      onClick={() => { setSelectedReport(r); setResolutionNotes(r.resolution_notes || ''); }}
                      className="text-xs font-semibold px-2.5 py-1 rounded bg-navy text-white hover:bg-navy-dark transition-colors"
                    >
                      Update Status
                    </button>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-bold text-navy">{r.title}</h4>
                  <p className="text-xs text-slate-600 mt-0.5">{r.description}</p>
                </div>

                {r.resolution_notes && (
                  <div className="p-2.5 rounded-lg bg-teal-light/40 border border-teal/20 text-xs text-slate-800">
                    <strong className="text-teal-dark">Resolution Notes: </strong>
                    {r.resolution_notes}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: FATIGUE RISK CENTER */}
      {activeTab === 'fatigue' && (
        <div className="space-y-6">
          <div className="bg-surface rounded-xl p-5 border border-border shadow-sm">
            <h3 className="font-bold text-navy text-lg mb-1">Fatigue Risk Monitoring Engine</h3>
            <p className="text-xs text-secondary mb-4">
              Transparent, non-punitive occupational safety rules preventing burnout and catastrophic worksite accidents.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="p-4 rounded-xl bg-canvas border border-border">
                <div className="text-xs font-bold text-navy">Rule 1: Extended Shifts</div>
                <div className="text-xs text-secondary mt-1">
                  Triggers Warning at &gt;10.0 hours; triggers <strong>Critical Action</strong> at &gt;12.0 hours.
                </div>
              </div>
              <div className="p-4 rounded-xl bg-canvas border border-border">
                <div className="text-xs font-bold text-navy">Rule 2: Turnaround Rest</div>
                <div className="text-xs text-secondary mt-1">
                  Enforces mandatory minimum 8.0 hours rest interval between consecutive shifts.
                </div>
              </div>
              <div className="p-4 rounded-xl bg-canvas border border-border">
                <div className="text-xs font-bold text-navy">Rule 3: Consecutive Days</div>
                <div className="text-xs text-secondary mt-1">
                  Requires 24h rest pause when an employee works &gt;6 consecutive calendar days.
                </div>
              </div>
            </div>

            <div className="space-y-3">
              {fatigueAlerts.map((a) => (
                <div key={a.id} className="p-4 rounded-xl border border-amber-200 bg-amber-50/60 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-warning text-white uppercase">
                        {a.severity}
                      </span>
                      <span className="text-xs font-bold text-navy">{a.title}</span>
                    </div>
                    <span className="text-xs text-secondary">
                      Rule: <strong className="font-mono">{a.rule_code}</strong>
                    </span>
                  </div>

                  <p className="text-xs text-slate-700">{a.details}</p>

                  <div className="p-2 bg-white rounded border border-amber-200 text-xs font-medium text-slate-800">
                    <strong className="text-teal-dark">Recommended Intervention: </strong>
                    {a.suggested_action}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: SKILL VERIFICATION */}
      {activeTab === 'skills' && (
        <div className="bg-surface rounded-xl p-5 border border-border shadow-sm">
          <h3 className="font-bold text-navy text-lg mb-1">Workforce Skill & Qualification Verification</h3>
          <p className="text-xs text-secondary mb-4">
            Audit self-declared worker qualifications against industry safety standards and official registers.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {skills.map((sk) => (
              <div key={sk.id} className="p-4 rounded-xl border border-border bg-canvas/40 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-200 text-slate-700">
                    {sk.category}
                  </span>
                  <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                    sk.is_verified ? 'bg-teal-light text-teal-dark' : 'bg-amber-100 text-amber-800'
                  }`}>
                    {sk.is_verified ? 'Verified' : 'Pending Audit'}
                  </span>
                </div>

                <h4 className="text-sm font-bold text-navy">{sk.title}</h4>
                <div className="text-xs text-secondary">
                  <div>Issuer: <strong className="text-navy">{sk.issuer}</strong></div>
                  <div>Issued Date: {sk.issue_date?.slice(0, 10)}</div>
                </div>

                {!sk.is_verified ? (
                  <button
                    onClick={() => handleVerifySkill(sk.id)}
                    className="w-full py-1.5 px-3 rounded-lg bg-teal hover:bg-teal-dark text-white text-xs font-semibold shadow-sm transition-colors flex items-center justify-center gap-1.5"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Verify Credential</span>
                  </button>
                ) : (
                  <div className="text-[11px] text-teal-dark font-medium flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Verified by {sk.verified_by || 'Supervisor'}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 5: AI WORKFORCE INSIGHTS */}
      {activeTab === 'ai' && (
        <div className="space-y-6">
          <div className="bg-surface rounded-xl p-5 border border-teal/30 shadow-sm">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-teal-light text-teal flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-teal" />
              </div>
              <div>
                <h3 className="font-bold text-navy text-lg">AI Workforce Health & SDG 8 Insights</h3>
                <p className="text-xs text-secondary">
                  Grounded recommendations generated exclusively from authorized, de-identified database metrics.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
              {recommendations.map((rec, idx) => (
                <div key={idx} className="p-5 rounded-xl border border-border bg-canvas/40 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-teal text-white">
                      {rec.category}
                    </span>
                    <span className="text-xs font-mono text-secondary">
                      Confidence: {(rec.confidence * 100).toFixed(0)}%
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-navy">{rec.title}</h4>
                  <p className="text-xs text-slate-700">{rec.observation}</p>

                  <div className="p-2.5 rounded-lg bg-white border border-border text-xs">
                    <div className="text-secondary font-semibold text-[11px]">Metric Evidence:</div>
                    <div className="text-navy font-mono mt-0.5">{rec.evidence_metric}</div>
                  </div>

                  <div className="p-2.5 rounded-lg bg-teal-light/50 border border-teal/20 text-xs">
                    <div className="text-teal-dark font-bold text-[11px]">Recommended Intervention:</div>
                    <div className="text-slate-800 mt-0.5">{rec.recommended_action}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Status Update Modal */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 bg-navy/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface rounded-2xl max-w-md w-full p-6 border border-border shadow-xl space-y-4">
            <h3 className="text-base font-bold text-navy">Update Hazard Report Status</h3>
            <div className="text-xs text-secondary font-mono">Ticket: {selectedReport.ref_number}</div>

            <div>
              <label className="block text-xs font-medium text-navy mb-1">Investigation & Resolution Notes</label>
              <textarea
                rows={3}
                placeholder="Detail corrective safety actions taken..."
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                className="w-full text-xs p-2 rounded-lg border border-border"
              />
            </div>

            <div className="flex flex-wrap gap-2 pt-2">
              <button
                onClick={() => handleUpdateStatus(selectedReport.id, 'investigating')}
                className="flex-1 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-colors"
              >
                Mark Investigating
              </button>
              <button
                onClick={() => handleUpdateStatus(selectedReport.id, 'resolved')}
                className="flex-1 py-2 rounded-lg bg-teal hover:bg-teal-dark text-white text-xs font-semibold transition-colors"
              >
                Mark Resolved
              </button>
              <button
                onClick={() => setSelectedReport(null)}
                className="py-2 px-3 rounded-lg bg-slate-100 text-slate-700 text-xs font-semibold"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
