import React, { useState, useEffect } from 'react';
import { 
  Clock, QrCode, AlertTriangle, ShieldAlert, Award, FileText, 
  CheckCircle2, DollarSign, MessageSquare, AlertOctagon, HeartHandshake, Plus, Info, Check, Shield
} from 'lucide-react';
import { User, Shift, Payslip, SafetyReport, SkillItem, FatigueAlert } from '../types';
import { api } from '../services/api';

interface WorkerDashboardProps {
  user: User;
  t: Record<string, string>;
  language: 'en' | 'ta';
}

export const WorkerDashboard: React.FC<WorkerDashboardProps> = ({ user, t, language }) => {
  const [activeTab, setActiveTab] = useState<'attendance' | 'payslips' | 'safety' | 'feedback' | 'skills'>('attendance');
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [payslips, setPayslips] = useState<Payslip[]>([]);
  const [reports, setReports] = useState<SafetyReport[]>([]);
  const [skills, setSkills] = useState<SkillItem[]>([]);
  const [fatigueAlerts, setFatigueAlerts] = useState<FatigueAlert[]>([]);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  // New Report Form State
  const [reportTitle, setReportTitle] = useState('');
  const [reportCategory, setReportCategory] = useState('hazard');
  const [reportDescription, setReportDescription] = useState('');
  const [reportPriority, setReportPriority] = useState<'low' | 'medium' | 'high' | 'critical'>('high');
  const [isAnonymous, setIsAnonymous] = useState(false);

  // New Skill Form State
  const [skillTitle, setSkillTitle] = useState('');
  const [skillCategory, setSkillCategory] = useState('safety');
  const [skillIssuer, setSkillIssuer] = useState('');
  const [showSkillModal, setShowSkillModal] = useState(false);

  // Feedback State
  const [feedbackCondition, setFeedbackCondition] = useState(4);
  const [feedbackWorkload, setFeedbackWorkload] = useState(3);
  const [feedbackBreaks, setFeedbackBreaks] = useState(2);
  const [feedbackFacilities, setFeedbackFacilities] = useState(3);
  const [feedbackSupervisor, setFeedbackSupervisor] = useState(4);
  const [feedbackComments, setFeedbackComments] = useState('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  // QR Modal Simulation
  const [showQRModal, setShowQRModal] = useState(false);

  useEffect(() => {
    loadAllData();
  }, [user.id]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [sData, pData, rData, skData, fData] = await Promise.all([
        api.getShifts(),
        api.getPayslips(),
        api.getReports(),
        api.getSkills(),
        api.getFatigueAlerts(),
      ]);
      setShifts(sData);
      setPayslips(pData);
      setReports(rData);
      setSkills(skData);
      setFatigueAlerts(fData);
    } catch (err) {
      console.warn("Failed loading worker data", err);
    } finally {
      setLoading(false);
    }
  };

  const showToast = (msg: string) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 4000);
  };

  // Check in
  const handleCheckIn = async (method: 'qr' | 'manual') => {
    try {
      const res = await api.checkIn(
        method, 
        method === 'qr' ? 'QR-APEX-TOWER-A' : undefined,
        method === 'qr' ? 'Verified Gate 1 QR Scan' : 'Manual Worker Log'
      );
      setShifts([res, ...shifts.filter(s => s.id !== res.id)]);
      setShowQRModal(false);
      showToast(language === 'ta' ? 'வருகை வெற்றிகரமாக பதிவு செய்யப்பட்டது!' : 'Check-in recorded successfully!');
    } catch (e: any) {
      showToast(e.message || 'Check-in failed');
    }
  };

  // Check out
  const handleCheckOut = async () => {
    try {
      const res = await api.checkOut('Standard shift completion');
      setShifts(shifts.map(s => s.id === res.id ? res : s));
      showToast(language === 'ta' ? 'ஷிப்ட் நிறைவு செய்யப்பட்டு கூடுதல் நேரம் கணக்கிடப்பட்டது.' : 'Shift completed! Hours & overtime calculated.');
      // Refresh fatigue alerts in case hours exceeded threshold
      const newAlerts = await api.getFatigueAlerts();
      setFatigueAlerts(newAlerts);
    } catch (e: any) {
      showToast(e.message || 'Check-out failed');
    }
  };

  // Submit Safety Report
  const handleSubmitReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportTitle || !reportDescription) return;

    try {
      const newRep = await api.submitReport({
        title: reportTitle,
        category: reportCategory,
        description: reportDescription,
        priority: reportPriority,
        is_anonymous: isAnonymous
      });
      setReports([newRep, ...reports]);
      setReportTitle('');
      setReportDescription('');
      showToast(language === 'ta' ? 'பாதுகாப்பு புகார் பதிவு செய்யப்பட்டது!' : `Report ${newRep.ref_number} submitted to safety review.`);
    } catch (err: any) {
      showToast('Error filing report');
    }
  };

  // Submit Feedback
  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.submitFeedback({
        condition_rating: feedbackCondition,
        workload_rating: feedbackWorkload,
        break_rating: feedbackBreaks,
        facility_rating: feedbackFacilities,
        supervisor_rating: feedbackSupervisor,
        comments: feedbackComments
      });
      setFeedbackSubmitted(true);
      showToast(language === 'ta' ? 'உங்கள் கருத்து ரகசியமாக பதிவு செய்யப்பட்டது. நன்றி!' : 'Honest feedback submitted anonymously. Thank you!');
    } catch (err: any) {
      showToast('Feedback submission error');
    }
  };

  // Add Skill
  const handleAddSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!skillTitle || !skillIssuer) return;

    try {
      const newSk = await api.addSkill({
        title: skillTitle,
        category: skillCategory,
        issuer: skillIssuer,
        issue_date: new Date().toISOString()
      });
      setSkills([newSk, ...skills]);
      setSkillTitle('');
      setSkillIssuer('');
      setShowSkillModal(false);
      showToast('Self-declared qualification submitted for supervisor review.');
    } catch (err: any) {
      showToast('Error submitting skill');
    }
  };

  const activeShift = shifts.find(s => s.status === 'in_progress');

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Toast Notification */}
      {notification && (
        <div className="mb-4 bg-teal text-white px-4 py-2.5 rounded-lg shadow-md flex items-center justify-between animate-fade-in text-sm font-medium">
          <span>{notification}</span>
          <button onClick={() => setNotification(null)} className="text-white hover:text-slate-200">✕</button>
        </div>
      )}

      {/* Fatigue Alert Warning Banner (Feature 6) */}
      {fatigueAlerts.length > 0 && (
        <div className="mb-6 p-4 rounded-xl bg-amber-50 border border-amber-200 shadow-sm flex items-start gap-3">
          <AlertOctagon className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-sm font-bold text-navy flex items-center gap-2">
              <span>{t.fatigueRiskTitle}</span>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-warning text-white uppercase">
                {fatigueAlerts[0].severity}
              </span>
            </h4>
            <p className="text-xs text-slate-700 mt-1">
              {fatigueAlerts[0].details}
            </p>
            <div className="mt-2 text-xs font-medium text-slate-800 bg-white/80 p-2 rounded border border-amber-100">
              <span className="font-semibold text-teal-dark">{t.suggestedAction}: </span>
              {fatigueAlerts[0].suggested_action}
            </div>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-border pb-3 mb-6">
        <button
          onClick={() => setActiveTab('attendance')}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'attendance'
              ? 'bg-navy text-white shadow-sm'
              : 'text-secondary hover:text-navy hover:bg-slate-100'
          }`}
        >
          <Clock className="w-4 h-4" />
          <span>{t.shifts}</span>
        </button>

        <button
          onClick={() => setActiveTab('payslips')}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'payslips'
              ? 'bg-navy text-white shadow-sm'
              : 'text-secondary hover:text-navy hover:bg-slate-100'
          }`}
        >
          <DollarSign className="w-4 h-4" />
          <span>{t.payslips}</span>
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
          <span>{t.safetyReports}</span>
          {reports.length > 0 && (
            <span className="text-xs px-1.5 py-0.2 bg-teal text-white rounded-full">
              {reports.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('feedback')}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeTab === 'feedback'
              ? 'bg-navy text-white shadow-sm'
              : 'text-secondary hover:text-navy hover:bg-slate-100'
          }`}
        >
          <HeartHandshake className="w-4 h-4" />
          <span>{t.honestFeedback}</span>
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
          <span>{t.skillPassport}</span>
        </button>
      </div>

      {/* TAB 1: ATTENDANCE & SHIFTS */}
      {activeTab === 'attendance' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Active Shift Card */}
          <div className="lg:col-span-1 bg-surface rounded-xl p-5 border border-border shadow-sm">
            <h3 className="font-bold text-navy text-base mb-1 flex items-center justify-between">
              <span>{t.shifts}</span>
              <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                activeShift ? 'bg-teal-light text-teal-dark border border-teal/20' : 'bg-slate-100 text-slate-500'
              }`}>
                {activeShift ? t.shiftActive : t.noActiveShift}
              </span>
            </h3>
            <p className="text-xs text-secondary mb-4">
              {activeShift ? activeShift.site_name || 'Designated Workplace Zone' : 'Ready to start your work session.'}
            </p>

            {activeShift ? (
              <div className="space-y-4">
                <div className="p-3 rounded-lg bg-teal-light/50 border border-teal/20">
                  <div className="text-xs text-teal-dark font-medium">Actual Check-In Time</div>
                  <div className="text-lg font-bold text-navy mt-0.5">
                    {new Date(activeShift.actual_check_in!).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                  <div className="text-xs text-secondary mt-1">
                    Base Rate: <span className="font-semibold text-navy">${user.hourly_rate.toFixed(2)}/hr</span>
                  </div>
                </div>

                <button
                  onClick={handleCheckOut}
                  className="w-full py-2.5 px-4 rounded-lg bg-critical hover:bg-red-700 text-white font-semibold text-sm shadow-sm transition-colors flex items-center justify-center gap-2"
                >
                  <Clock className="w-4 h-4" />
                  <span>{t.checkOut}</span>
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <button
                  onClick={() => setShowQRModal(true)}
                  className="w-full py-2.5 px-4 rounded-lg bg-teal hover:bg-teal-dark text-white font-semibold text-sm shadow-sm transition-colors flex items-center justify-center gap-2"
                >
                  <QrCode className="w-4 h-4" />
                  <span>{t.qrScanCheckIn}</span>
                </button>

                <button
                  onClick={() => handleCheckIn('manual')}
                  className="w-full py-2.5 px-4 rounded-lg bg-white hover:bg-slate-50 text-navy border border-border font-medium text-sm transition-colors flex items-center justify-center gap-2"
                >
                  <Clock className="w-4 h-4 text-secondary" />
                  <span>{t.manualCheckIn}</span>
                </button>
              </div>
            )}
          </div>

          {/* Shift History Table */}
          <div className="lg:col-span-2 bg-surface rounded-xl p-5 border border-border shadow-sm">
            <h3 className="font-bold text-navy text-base mb-1">Personal Shift & Overtime Log</h3>
            <p className="text-xs text-secondary mb-4">Accurate record of regular hours, overtime, and calculated rates.</p>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-canvas text-secondary font-semibold border-b border-border">
                  <tr>
                    <th className="py-2.5 px-3">Date & Shift</th>
                    <th className="py-2.5 px-3">Duration</th>
                    <th className="py-2.5 px-3">Regular</th>
                    <th className="py-2.5 px-3">Overtime (1.5x)</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-navy">
                  {shifts.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50">
                      <td className="py-2.5 px-3">
                        <div className="font-medium">{new Date(s.scheduled_start).toLocaleDateString()}</div>
                        <div className="text-[11px] text-secondary">{s.notes || s.site_name}</div>
                      </td>
                      <td className="py-2.5 px-3 font-semibold">
                        {((s.regular_hours || 0) + (s.overtime_hours || 0)).toFixed(1)} hrs
                      </td>
                      <td className="py-2.5 px-3">{s.regular_hours?.toFixed(1) || '0.0'} hrs</td>
                      <td className="py-2.5 px-3">
                        {s.overtime_hours > 0 ? (
                          <span className="font-semibold text-warning">+{s.overtime_hours.toFixed(1)} hrs</span>
                        ) : (
                          <span className="text-secondary">-</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium capitalize ${
                          s.status === 'completed'
                            ? 'bg-teal-light text-teal-dark'
                            : s.status === 'in_progress'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-slate-100 text-slate-600'
                        }`}>
                          {s.status === 'in_progress' ? 'Active' : s.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: CLEAR PAYSLIPS */}
      {activeTab === 'payslips' && (
        <div className="space-y-6">
          <div className="bg-surface rounded-xl p-5 border border-border shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-4 mb-4">
              <div>
                <h3 className="font-bold text-navy text-lg">{t.payslips}</h3>
                <p className="text-xs text-secondary">
                  Transparent wage breakdowns ensuring every minute of regular and overtime labor is accounted for.
                </p>
              </div>
              <div className="text-xs text-amber-800 bg-amber-50 px-3 py-1.5 rounded-lg border border-amber-200">
                <span className="font-bold">Notice: </span>{t.syntheticDisclaimer}
              </div>
            </div>

            {payslips.map((p) => (
              <div key={p.id} className="p-5 rounded-xl border border-border bg-canvas/40 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <span className="text-xs text-secondary font-medium">Pay Period: </span>
                    <span className="text-xs font-bold text-navy">
                      {new Date(p.period_start).toLocaleDateString()} — {new Date(p.period_end).toLocaleDateString()}
                    </span>
                  </div>
                  <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold uppercase bg-teal-light text-teal-dark">
                    {p.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="p-3 bg-surface rounded-lg border border-border">
                    <div className="text-xs text-secondary">Base Rate</div>
                    <div className="text-base font-bold text-navy mt-1">${p.base_hourly_rate.toFixed(2)}/hr</div>
                    <div className="text-[11px] text-secondary mt-0.5">{p.regular_hours} Regular Hrs</div>
                  </div>

                  <div className="p-3 bg-surface rounded-lg border border-border">
                    <div className="text-xs text-secondary">Overtime (1.5x)</div>
                    <div className="text-base font-bold text-warning mt-1">
                      ${(p.base_hourly_rate * p.overtime_rate).toFixed(2)}/hr
                    </div>
                    <div className="text-[11px] text-secondary mt-0.5">{p.overtime_hours} Overtime Hrs</div>
                  </div>

                  <div className="p-3 bg-surface rounded-lg border border-border">
                    <div className="text-xs text-secondary">Allowances</div>
                    <div className="text-base font-bold text-teal mt-1">+${p.allowances.toFixed(2)}</div>
                    <div className="text-[11px] text-secondary mt-0.5">Transport & Safety Stipend</div>
                  </div>

                  <div className="p-3 bg-surface rounded-lg border border-border">
                    <div className="text-xs text-secondary">Statutory Deductions</div>
                    <div className="text-base font-bold text-critical mt-1">-${p.deductions.toFixed(2)}</div>
                    <div className="text-[11px] text-secondary mt-0.5">Insurance & Welfare</div>
                  </div>
                </div>

                {/* Calculation summary */}
                <div className="p-3 rounded-lg bg-surface border border-teal/20 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="text-xs text-slate-700">
                    <span className="font-semibold text-navy">Formula: </span>
                    ({p.regular_hours}h × ${p.base_hourly_rate}) + ({p.overtime_hours}h × ${p.base_hourly_rate * p.overtime_rate}) + ${p.allowances} allowances - ${p.deductions} deductions
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-secondary font-medium">Net Take-Home Pay</div>
                    <div className="text-xl font-extrabold text-navy">${p.net_pay.toFixed(2)}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: SAFETY & HAZARD REPORTING */}
      {activeTab === 'safety' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Submit Report Form */}
          <div className="lg:col-span-1 bg-surface rounded-xl p-5 border border-border shadow-sm">
            <h3 className="font-bold text-navy text-base mb-1">{t.reportHazard}</h3>
            <p className="text-xs text-secondary mb-4">
              Your safety matters. Report equipment defects, slip hazards, extreme workload, or workplace concerns.
            </p>

            <form onSubmit={handleSubmitReport} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-navy mb-1">Issue Category</label>
                <select
                  value={reportCategory}
                  onChange={(e) => setReportCategory(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-border bg-white focus:outline-none focus:ring-1 focus:ring-teal"
                >
                  <option value="hazard">Physical Safety Hazard</option>
                  <option value="equipment">Unsafe / Defective Equipment</option>
                  <option value="workload">Excessive Workload & Hours</option>
                  <option value="harassment">Unfair Treatment / Harassment</option>
                  <option value="pay_dispute">Pay Dispute / Unrecorded Hours</option>
                  <option value="maintenance">Facility Maintenance</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-navy mb-1">Title / Location Summary</label>
                <input
                  type="text"
                  placeholder="e.g. Broken ladder rung on Tower A 4th floor"
                  value={reportTitle}
                  onChange={(e) => setReportTitle(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-border bg-white focus:outline-none focus:ring-1 focus:ring-teal"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-navy mb-1">Detailed Description</label>
                <textarea
                  rows={3}
                  placeholder="Describe what occurred, any immediate risks, and exact location..."
                  value={reportDescription}
                  onChange={(e) => setReportDescription(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-border bg-white focus:outline-none focus:ring-1 focus:ring-teal"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-navy mb-1">{t.priority}</label>
                <select
                  value={reportPriority}
                  onChange={(e) => setReportPriority(e.target.value as any)}
                  className="w-full text-xs p-2 rounded-lg border border-border bg-white focus:outline-none focus:ring-1 focus:ring-teal"
                >
                  <option value="critical">🚨 {t.critical} (Immediate Danger)</option>
                  <option value="high">⚠️ {t.high} (High Risk)</option>
                  <option value="medium">⚡ {t.medium} (Standard Priority)</option>
                  <option value="low">ℹ️ {t.low} (Informational)</option>
                </select>
              </div>

              {/* Confidential / Anonymous Checkbox */}
              <div className="p-2.5 rounded-lg bg-canvas border border-border flex items-start gap-2">
                <input
                  type="checkbox"
                  id="anonCheck"
                  checked={isAnonymous}
                  onChange={(e) => setIsAnonymous(e.target.checked)}
                  className="mt-0.5 text-teal focus:ring-teal rounded"
                />
                <label htmlFor="anonCheck" className="text-xs text-navy font-medium cursor-pointer">
                  {t.anonymousReporting}
                  <span className="block text-[11px] text-secondary font-normal mt-0.5">
                    Your name and user ID will be completely excluded from the supervisor ticket.
                  </span>
                </label>
              </div>

              <button
                type="submit"
                className="w-full py-2.5 px-4 rounded-lg bg-teal hover:bg-teal-dark text-white font-semibold text-sm shadow-sm transition-colors flex items-center justify-center gap-2"
              >
                <Shield className="w-4 h-4" />
                <span>Submit Safety Report</span>
              </button>
            </form>
          </div>

          {/* Active Reports List */}
          <div className="lg:col-span-2 bg-surface rounded-xl p-5 border border-border shadow-sm">
            <h3 className="font-bold text-navy text-base mb-1">Your Filed Workplace Reports</h3>
            <p className="text-xs text-secondary mb-4">Track official supervisor investigation logs and resolutions.</p>

            <div className="space-y-3">
              {reports.map((r) => (
                <div key={r.id} className="p-4 rounded-xl border border-border bg-canvas/40 space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-navy bg-white px-2 py-0.5 rounded border border-border">
                        {r.ref_number}
                      </span>
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded capitalize ${
                        r.priority === 'critical' ? 'bg-critical text-white' :
                        r.priority === 'high' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-600'
                      }`}>
                        {r.priority}
                      </span>
                      {r.is_anonymous && (
                        <span className="text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded font-medium">
                          Anonymous
                        </span>
                      )}
                    </div>
                    <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full capitalize ${
                      r.status === 'resolved' ? 'bg-teal-light text-teal-dark' :
                      r.status === 'investigating' ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800'
                    }`}>
                      {r.status}
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-navy">{r.title}</h4>
                  <p className="text-xs text-slate-600">{r.description}</p>

                  {r.resolution_notes && (
                    <div className="mt-2 p-2.5 rounded-lg bg-teal-light/50 border border-teal/20 text-xs">
                      <div className="font-semibold text-teal-dark">Supervisor Resolution Notes:</div>
                      <div className="text-slate-800 mt-0.5">{r.resolution_notes}</div>
                    </div>
                  )}

                  <div className="text-[11px] text-secondary pt-1 border-t border-border/60">
                    Reported on {new Date(r.reported_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: HONEST ANONYMOUS FEEDBACK */}
      {activeTab === 'feedback' && (
        <div className="max-w-2xl mx-auto bg-surface rounded-xl p-6 border border-border shadow-sm">
          <div className="text-center mb-6">
            <div className="w-12 h-12 rounded-full bg-teal-light text-teal mx-auto flex items-center justify-center mb-2">
              <HeartHandshake className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-navy">{t.honestFeedback}</h3>
            <p className="text-xs text-secondary mt-1">
              Your voice helps shape fair workplace policies (SDG 8). Ratings are strictly aggregated and anonymized.
            </p>
          </div>

          {feedbackSubmitted ? (
            <div className="p-6 text-center space-y-3">
              <CheckCircle2 className="w-12 h-12 text-teal mx-auto" />
              <h4 className="text-base font-bold text-navy">Feedback Recorded</h4>
              <p className="text-xs text-secondary max-w-md mx-auto">
                Thank you for contributing to workforce health and transparency. Your ratings have been anonymized and added to the aggregate metrics.
              </p>
              <button
                onClick={() => setFeedbackSubmitted(false)}
                className="mt-2 text-xs font-semibold text-teal hover:underline"
              >
                Submit Another Rating
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmitFeedback} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-navy mb-1">
                  1. Overall Working Conditions & Safety: <span className="text-teal font-bold">{feedbackCondition} / 5</span>
                </label>
                <input
                  type="range" min={1} max={5} value={feedbackCondition}
                  onChange={(e) => setFeedbackCondition(Number(e.target.value))}
                  className="w-full accent-teal cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-navy mb-1">
                  2. {t.ratingWorkload}: <span className="text-teal font-bold">{feedbackWorkload} / 5</span>
                </label>
                <input
                  type="range" min={1} max={5} value={feedbackWorkload}
                  onChange={(e) => setFeedbackWorkload(Number(e.target.value))}
                  className="w-full accent-teal cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-navy mb-1">
                  3. {t.ratingBreaks}: <span className="text-teal font-bold">{feedbackBreaks} / 5</span>
                </label>
                <input
                  type="range" min={1} max={5} value={feedbackBreaks}
                  onChange={(e) => setFeedbackBreaks(Number(e.target.value))}
                  className="w-full accent-teal cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-navy mb-1">
                  4. {t.ratingFacilities}: <span className="text-teal font-bold">{feedbackFacilities} / 5</span>
                </label>
                <input
                  type="range" min={1} max={5} value={feedbackFacilities}
                  onChange={(e) => setFeedbackFacilities(Number(e.target.value))}
                  className="w-full accent-teal cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-navy mb-1">
                  5. {t.ratingSupervisor}: <span className="text-teal font-bold">{feedbackSupervisor} / 5</span>
                </label>
                <input
                  type="range" min={1} max={5} value={feedbackSupervisor}
                  onChange={(e) => setFeedbackSupervisor(Number(e.target.value))}
                  className="w-full accent-teal cursor-pointer"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-navy mb-1">Optional Anonymized Comment</label>
                <textarea
                  rows={3}
                  placeholder="Share constructive feedback regarding facilities, breaks, or equipment..."
                  value={feedbackComments}
                  onChange={(e) => setFeedbackComments(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-border bg-white focus:outline-none focus:ring-1 focus:ring-teal"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2.5 px-4 rounded-lg bg-navy hover:bg-navy-dark text-white font-semibold text-sm shadow-sm transition-colors"
              >
                {t.submitFeedback}
              </button>
            </form>
          )}
        </div>
      )}

      {/* TAB 5: SKILL PASSPORT */}
      {activeTab === 'skills' && (
        <div className="space-y-6">
          <div className="bg-surface rounded-xl p-5 border border-border shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4 mb-4">
              <div>
                <h3 className="font-bold text-navy text-lg">{t.skillPassport}</h3>
                <p className="text-xs text-secondary">
                  Your portable qualifications and certified competencies, safeguarded against lost paperwork.
                </p>
              </div>
              <button
                onClick={() => setShowSkillModal(true)}
                className="py-2 px-3 rounded-lg bg-teal hover:bg-teal-dark text-white font-semibold text-xs flex items-center gap-1.5 self-start shadow-sm transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span>Add Qualification</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {skills.map((sk) => (
                <div key={sk.id} className="p-4 rounded-xl border border-border bg-canvas/40 space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-200 text-slate-700">
                      {sk.category}
                    </span>
                    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-1 ${
                      sk.is_verified 
                        ? 'bg-teal-light text-teal-dark border border-teal/20' 
                        : 'bg-amber-100 text-amber-800'
                    }`}>
                      {sk.is_verified ? <CheckCircle2 className="w-3 h-3" /> : <Clock className="w-3 h-3" />}
                      <span>{sk.is_verified ? 'Supervisor Verified' : 'Self-Declared'}</span>
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-navy leading-snug">{sk.title}</h4>
                  <div className="text-xs text-secondary">
                    <div><span className="font-medium text-slate-700">Issuer: </span>{sk.issuer}</div>
                    <div><span className="font-medium text-slate-700">Issued: </span>{sk.issue_date?.slice(0, 10)}</div>
                    {sk.expiry_date && (
                      <div><span className="font-medium text-slate-700">Expires: </span>{sk.expiry_date.slice(0, 10)}</div>
                    )}
                  </div>

                  {sk.verified_by && (
                    <div className="text-[11px] text-teal-dark bg-teal-light/40 p-2 rounded border border-teal/10">
                      Verified by {sk.verified_by}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* QR Code Scanner Simulation Modal */}
      {showQRModal && (
        <div className="fixed inset-0 z-50 bg-navy/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface rounded-2xl max-w-sm w-full p-6 border border-border shadow-xl text-center space-y-4 animate-scale-in">
            <h3 className="text-base font-bold text-navy">QR Site Attendance</h3>
            <p className="text-xs text-secondary">
              Position site barcode within the viewfinder to register verified check-in.
            </p>

            <div className="w-48 h-48 mx-auto rounded-xl border-2 border-dashed border-teal flex flex-col items-center justify-center bg-slate-50 relative overflow-hidden">
              <QrCode className="w-24 h-24 text-teal/40" />
              <div className="absolute inset-x-0 h-0.5 bg-teal animate-pulse top-1/2"></div>
              <span className="text-[10px] font-mono text-secondary mt-2 bg-white px-2 py-0.5 rounded shadow-sm">
                QR-APEX-TOWER-A
              </span>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => handleCheckIn('qr')}
                className="flex-1 py-2 rounded-lg bg-teal hover:bg-teal-dark text-white font-semibold text-xs transition-colors"
              >
                Simulate QR Scan
              </button>
              <button
                onClick={() => setShowQRModal(false)}
                className="py-2 px-3 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Skill Modal */}
      {showSkillModal && (
        <div className="fixed inset-0 z-50 bg-navy/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface rounded-2xl max-w-md w-full p-6 border border-border shadow-xl space-y-4">
            <h3 className="text-base font-bold text-navy">Self-Declare Skill or Certification</h3>
            <form onSubmit={handleAddSkill} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-navy mb-1">Certification Title</label>
                <input
                  type="text"
                  placeholder="e.g. Scaffolding Fall Arrest Level 1"
                  value={skillTitle}
                  onChange={(e) => setSkillTitle(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-border"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-navy mb-1">Category</label>
                <select
                  value={skillCategory}
                  onChange={(e) => setSkillCategory(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-border bg-white"
                >
                  <option value="safety">Safety & PPE</option>
                  <option value="machinery">Heavy Machinery Operations</option>
                  <option value="technical">Technical Crafts & Electrical</option>
                  <option value="first_aid">First Aid & Emergency Response</option>
                  <option value="pedagogy">Academic Instruction</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-navy mb-1">Issuing Authority</label>
                <input
                  type="text"
                  placeholder="e.g. National Safety Council"
                  value={skillIssuer}
                  onChange={(e) => setSkillIssuer(e.target.value)}
                  className="w-full text-xs p-2 rounded-lg border border-border"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowSkillModal(false)}
                  className="py-2 px-3 rounded-lg bg-slate-100 text-slate-700 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="py-2 px-4 rounded-lg bg-teal text-white text-xs font-semibold"
                >
                  Save to Passport
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
