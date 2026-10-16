import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  Search,
  Filter,
  Clock,
  Eye,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Play,
  RotateCcw,
  Activity,
  FileCode,
  User,
  MessageSquare,
  Sparkles,
  ChevronRight,
  Code2,
  Trash2,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
  ReferenceLine,
} from 'recharts';
import { integrityService } from '../services/codingService';

export default function CodingIntegrityDashboard() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Selected session for deep dive
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [rhythmMetrics, setRhythmMetrics] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Selected event for inspection & revision modal
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [revisionData, setRevisionData] = useState(null);
  const [loadingRevision, setLoadingRevision] = useState(false);

  // Trainer review form
  const [reviewNote, setReviewNote] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);

  // Fetch sessions overview
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const data = await integrityService.getDashboardSessions({
        review_status: statusFilter,
        search: searchQuery || undefined,
      });
      setDashboardData(data);
      if (data.sessions && data.sessions.length > 0 && !selectedSessionId) {
        loadSessionDetail(data.sessions[0].id);
      }
    } catch (err) {
      console.error('Failed to load integrity dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchDashboardData();
  };

  // Load detailed timeline & typing rhythm for a session
  const loadSessionDetail = async (sessionId) => {
    setSelectedSessionId(sessionId);
    setSelectedEvent(null);
    setRevisionData(null);
    setLoadingDetail(true);
    try {
      const [timeline, rhythm] = await Promise.all([
        integrityService.getSessionTimeline(sessionId),
        integrityService.getTypingRhythm(sessionId),
      ]);
      setTimelineEvents(timeline);
      setRhythmMetrics(rhythm);
      if (timeline.length > 0) {
        // Focus first review-suggested event or first event
        const firstReview = timeline.find((e) => e.review_status === 'REVIEW_SUGGESTED') || timeline[0];
        handleSelectEvent(firstReview, sessionId);
      }
    } catch (err) {
      console.error('Failed to load session details:', err);
    } finally {
      setLoadingDetail(false);
    }
  };

  // Select event and load revision if available
  const handleSelectEvent = async (eventItem, sessId = selectedSessionId) => {
    setSelectedEvent(eventItem);
    setRevisionData(null);
    if (eventItem.revision_id) {
      setLoadingRevision(true);
      try {
        const rev = await integrityService.getRevisionComparison(sessId, eventItem.revision_id);
        setRevisionData(rev);
      } catch (err) {
        console.warn('Could not load code revision:', err);
      } finally {
        setLoadingRevision(false);
      }
    }
  };

  // Handle Trainer review actions: MARK_REVIEWED, DISMISS, ADD_NOTE
  const handleReviewAction = async (action) => {
    if (!selectedSessionId) return;
    setSubmittingReview(true);
    try {
      await integrityService.submitTrainerReview(selectedSessionId, {
        action: action,
        notes: reviewNote || undefined,
        signal_id: selectedEvent?.signal?.id || undefined,
      });
      setReviewNote('');
      // Refresh timeline & dashboard
      const updatedTimeline = await integrityService.getSessionTimeline(selectedSessionId);
      setTimelineEvents(updatedTimeline);
      const data = await integrityService.getDashboardSessions({
        review_status: statusFilter,
        search: searchQuery || undefined,
      });
      setDashboardData(data);
    } catch (err) {
      console.error('Review action failed:', err);
      alert('Review action encountered an error.');
    } finally {
      setSubmittingReview(false);
    }
  };

  const selectedSession = dashboardData?.sessions?.find((s) => s.id === selectedSessionId);

  // Status badge style helper
  const renderStatusBadge = (status) => {
    switch (status) {
      case 'NORMAL_RHYTHM':
      case 'NORMAL':
        return (
          <span style={{ backgroundColor: '#ecfdf5', color: '#059669', padding: '4px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 700 }}>
            ● Normal
          </span>
        );
      case 'LOW_RISK':
        return (
          <span style={{ backgroundColor: '#eff6ff', color: '#2563eb', padding: '4px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 700 }}>
            ● Low Risk
          </span>
        );
      case 'MEDIUM_RISK':
        return (
          <span style={{ backgroundColor: '#fffbeb', color: '#d97706', padding: '4px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 700 }}>
            ▲ Medium Risk
          </span>
        );
      case 'HIGH_RISK':
        return (
          <span style={{ backgroundColor: '#fef2f2', color: '#dc2626', padding: '4px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 700 }}>
            ▲ High Risk
          </span>
        );
      case 'REVIEW_SUGGESTED':
        return (
          <span style={{ backgroundColor: '#fff7ed', color: '#ea580c', padding: '4px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 700 }}>
            ▲ Review Suggested
          </span>
        );
      case 'INSUFFICIENT_DATA':
      default:
        return (
          <span style={{ backgroundColor: '#f1f5f9', color: '#64748b', padding: '4px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 700 }}>
            ■ Insufficient Data
          </span>
        );
    }
  };

  // Chart data: map timeline events into insertion size plot
  const chartData = timelineEvents
    .filter((e) => ['TYPE', 'PASTE', 'REPLACE', 'RUN', 'SUBMIT'].includes(e.event_type.toUpperCase()))
    .map((e, idx) => ({
      index: idx + 1,
      type: e.event_type,
      chars: e.inserted_character_count || 0,
      classification: e.classification || 'Normal typing',
      status: e.review_status,
      timestamp: new Date(e.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    }));

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '16px',
          border: '1px solid #e2e8f0',
          padding: '24px 28px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ padding: '8px', backgroundColor: '#eef2ff', borderRadius: '10px', color: '#4f46e5' }}>
              <ShieldAlert size={24} />
            </div>
            <div>
              <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                Coding Activity Tracking & Integrity Dashboard
              </h1>
              <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0 0' }}>
                Evidence-based integrity signals & typing rhythm evaluation. <strong>Human review only — no automated misconduct verdicts.</strong>
              </p>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button
            onClick={() => navigate('/trainer/dashboard')}
            style={{
              padding: '8px 16px',
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: 600,
              color: '#334155',
              cursor: 'pointer',
            }}
          >
            Cohort View
          </button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '18px 20px' }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
            Total Monitored Sessions
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#0f172a', marginTop: '6px' }}>
            {dashboardData?.metrics?.total_sessions || 0}
          </div>
          <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>Active assessment audits</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '18px 20px' }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: '#059669', textTransform: 'uppercase' }}>
            Normal Rhythm
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#059669', marginTop: '6px' }}>
            {dashboardData?.metrics?.normal_rhythm_count || 0}
          </div>
          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>Consistent with observed rhythm</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', border: '1px solid #fecaca', borderRadius: '14px', padding: '18px 20px', backgroundColor: '#fff5f5' }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: '#dc2626', textTransform: 'uppercase' }}>
            Review Suggested
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#dc2626', marginTop: '6px' }}>
            {dashboardData?.metrics?.review_suggested_count || 0}
          </div>
          <div style={{ fontSize: '12px', color: '#b91c1c', marginTop: '4px' }}>Unusual insertions flagged for trainer</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '18px 20px' }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
            Insufficient Data
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#475569', marginTop: '6px' }}>
            {dashboardData?.metrics?.insufficient_data_count || 0}
          </div>
          <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>Short sessions / brief edits</div>
        </div>
      </div>

      {/* Main Split Layout: Left Sessions Table / Right Detail & Replay */}
      <div style={{ display: 'grid', gridTemplateColumns: '400px 1fr', gap: '20px', alignItems: 'start' }}>
        {/* Left Column: Filterable Sessions List */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', backgroundColor: '#f8fafc' }}>
            <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a', margin: '0 0 12px 0' }}>
              Assessment Sessions
            </h3>

            {/* Filter buttons */}
            <div style={{ display: 'flex', gap: '6px', marginBottom: '12px' }}>
              {['ALL', 'REVIEW_SUGGESTED', 'NORMAL_RHYTHM', 'INSUFFICIENT_DATA'].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  style={{
                    padding: '4px 8px',
                    fontSize: '11px',
                    fontWeight: 700,
                    borderRadius: '6px',
                    border: '1px solid',
                    borderColor: statusFilter === st ? '#4f46e5' : '#cbd5e1',
                    backgroundColor: statusFilter === st ? '#4f46e5' : '#ffffff',
                    color: statusFilter === st ? '#ffffff' : '#475569',
                    cursor: 'pointer',
                  }}
                >
                  {st === 'ALL' ? 'All' : st === 'REVIEW_SUGGESTED' ? 'Review' : st === 'NORMAL_RHYTHM' ? 'Normal' : 'Brief'}
                </button>
              ))}
            </div>

            {/* Search */}
            <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '8px' }}>
              <div style={{ position: 'relative', flex: 1 }}>
                <Search size={14} style={{ position: 'absolute', left: '10px', top: '10px', color: '#94a3b8' }} />
                <input
                  type="text"
                  placeholder="Search student name or email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '6px 10px 6px 32px',
                    fontSize: '12px',
                    border: '1px solid #cbd5e1',
                    borderRadius: '6px',
                  }}
                />
              </div>
              <button
                type="submit"
                style={{
                  padding: '6px 12px',
                  backgroundColor: '#0f172a',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Go
              </button>
            </form>
          </div>

          {/* Session Cards List */}
          <div style={{ maxHeight: '650px', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
            {dashboardData?.sessions?.length === 0 ? (
              <div style={{ padding: '30px', textAlign: 'center', color: '#94a3b8', fontSize: '13px' }}>
                No sessions match criteria.
              </div>
            ) : (
              dashboardData?.sessions?.map((sess) => {
                const isSelected = sess.id === selectedSessionId;
                return (
                  <div
                    key={sess.id}
                    onClick={() => loadSessionDetail(sess.id)}
                    style={{
                      padding: '16px 20px',
                      borderBottom: '1px solid #f1f5f9',
                      backgroundColor: isSelected ? '#eef2ff' : '#ffffff',
                      borderLeft: isSelected ? '4px solid #4f46e5' : '4px solid transparent',
                      cursor: 'pointer',
                      transition: 'background-color 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '14px', fontWeight: 800, color: '#0f172a' }}>
                        {sess.student_name}
                      </span>
                      {renderStatusBadge(sess.overall_review_status)}
                    </div>
                    <div style={{ fontSize: '12px', color: '#475569', marginTop: '4px' }}>
                      {sess.problem_title}
                    </div>
                    <div style={{ display: 'flex', gap: '14px', marginTop: '8px', fontSize: '11px', color: '#64748b' }}>
                      <span>Events: <strong>{sess.total_events}</strong></span>
                      <span>Pastes: <strong>{sess.paste_count}</strong></span>
                      <span>Duration: <strong>{sess.duration_seconds}s</strong></span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Deep Dive, Typing Rhythm & Timeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {selectedSession ? (
            <>
              {/* Session Header Card */}
              <div
                style={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '14px',
                  padding: '20px 24px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                      Session #{selectedSession.id} — {selectedSession.student_name}
                    </h2>
                    {renderStatusBadge(selectedSession.overall_review_status)}
                  </div>
                  <div style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
                    Assessment: <strong>{selectedSession.problem_title}</strong> · Started: {new Date(selectedSession.started_at).toLocaleString()}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    onClick={() => navigate(`/trainer/replay/${selectedSession.id}`)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '8px 16px',
                      backgroundColor: '#4f46e5',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '8px',
                      fontSize: '13px',
                      fontWeight: 700,
                      cursor: 'pointer',
                    }}
                  >
                    <Play size={14} /> Full Replay Studio
                  </button>
                </div>
              </div>

              {/* Typing Rhythm Evaluation Card */}
              <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '20px 24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                  <div>
                    <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                      Observed Typing Rhythm & Baseline Estimation
                    </h3>
                    <p style={{ fontSize: '12px', color: '#64748b', margin: '2px 0 0 0' }}>
                      Compares insertion size and intervals against the student's individual session baseline.
                    </p>
                  </div>
                  {renderStatusBadge(rhythmMetrics?.review_status || 'INSUFFICIENT_DATA')}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', backgroundColor: '#f8fafc', padding: '14px', borderRadius: '10px', marginBottom: '18px' }}>
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>Baseline Rhythm</div>
                    <div style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', marginTop: '2px' }}>
                      {rhythmMetrics?.baseline_cps || 0} <span style={{ fontSize: '11px', fontWeight: 500, color: '#64748b' }}>chars/sec</span>
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>Typical Insertion</div>
                    <div style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', marginTop: '2px' }}>
                      {rhythmMetrics?.typical_insertion_range || '5 - 20 chars'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>Typical Interval</div>
                    <div style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', marginTop: '2px' }}>
                      {rhythmMetrics?.typical_interval_range || '0.2s - 1.5s'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>Rapid Bulk Insertions</div>
                    <div style={{ fontSize: '18px', fontWeight: 800, color: rhythmMetrics?.rapid_insertions_count > 0 ? '#dc2626' : '#059669', marginTop: '2px' }}>
                      {rhythmMetrics?.rapid_insertions_count || 0}
                    </div>
                  </div>
                </div>

                {/* Insertion Sizes Timeline Chart */}
                {chartData.length > 0 && (
                  <div style={{ height: '180px', width: '100%' }}>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '6px' }}>
                      Chronological Editing Burst Sizes (Characters Inserted)
                    </div>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis dataKey="index" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                        <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                        <Tooltip
                          content={({ active, payload }) => {
                            if (active && payload && payload.length) {
                              const p = payload[0].payload;
                              return (
                                <div style={{ backgroundColor: '#1e293b', color: '#ffffff', padding: '8px 12px', borderRadius: '6px', fontSize: '12px' }}>
                                  <div style={{ fontWeight: 700 }}>{p.type} (#{p.index})</div>
                                  <div>Chars: +{p.chars}</div>
                                  <div>Class: {p.classification}</div>
                                  <div>Time: {p.timestamp}</div>
                                </div>
                              );
                            }
                            return null;
                          }}
                        />
                        <ReferenceLine y={100} stroke="#f87171" strokeDasharray="3 3" label={{ value: 'Rapid Threshold (100+)', fill: '#ef4444', fontSize: 10 }} />
                        <Bar dataKey="chars" radius={[4, 4, 0, 0]}>
                          {chartData.map((entry, index) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={entry.status === 'REVIEW_SUGGESTED' ? '#ef4444' : entry.type === 'PASTE' ? '#f59e0b' : '#3b82f6'}
                            />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

              {/* Chronological Timeline & Trainer Review Action */}
              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
                {/* Timeline Column */}
                <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '20px', maxHeight: '550px', overflowY: 'auto' }}>
                  <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a', margin: '0 0 14px 0' }}>
                    Activity Timeline
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {timelineEvents.map((ev, i) => {
                      const isSelected = selectedEvent?.id === ev.id;
                      const isReview = ev.review_status === 'REVIEW_SUGGESTED';
                      return (
                        <div
                          key={ev.id || i}
                          onClick={() => handleSelectEvent(ev)}
                          style={{
                            padding: '12px 14px',
                            borderRadius: '10px',
                            border: isSelected ? '2px solid #4f46e5' : isReview ? '1px solid #fecaca' : '1px solid #e2e8f0',
                            backgroundColor: isSelected ? '#f5f3ff' : isReview ? '#fff5f5' : '#ffffff',
                            cursor: 'pointer',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span
                                style={{
                                  fontSize: '11px',
                                  fontWeight: 800,
                                  padding: '2px 6px',
                                  borderRadius: '4px',
                                  backgroundColor: isReview ? '#ef4444' : '#0f172a',
                                  color: '#ffffff',
                                }}
                              >
                                {ev.event_type}
                              </span>
                              <span style={{ fontSize: '11px', color: '#64748b' }}>
                                {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                              </span>
                            </div>
                            {isReview && (
                              <span style={{ fontSize: '11px', fontWeight: 700, color: '#dc2626' }}>
                                Review Suggested
                              </span>
                            )}
                          </div>

                          <div style={{ fontSize: '12px', color: '#334155', marginTop: '6px' }}>
                            <strong>{ev.classification || ev.event_type}</strong>
                            {ev.inserted_character_count > 0 && <span style={{ color: '#059669', marginLeft: '6px' }}>+{ev.inserted_character_count} chars</span>}
                            {ev.deleted_character_count > 0 && <span style={{ color: '#dc2626', marginLeft: '6px' }}>-{ev.deleted_character_count} chars</span>}
                          </div>

                          {/* Code Location & Reason */}
                          {ev.code_location && (
                            <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px', fontFamily: 'monospace' }}>
                              📍 Lines {ev.code_location.start_line}:{ev.code_location.start_column} → {ev.code_location.end_line}:{ev.code_location.end_column}
                            </div>
                          )}

                          {ev.classification_reason && (
                            <div style={{ fontSize: '11px', color: '#475569', marginTop: '4px', fontStyle: 'italic' }}>
                              {ev.classification_reason}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Right: Selected Event Inspector & Trainer Action */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {/* Event Detail Box */}
                  <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '20px' }}>
                    <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a', margin: '0 0 12px 0' }}>
                      Event Detail & Classification
                    </h3>
                    {selectedEvent ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        <div>
                          <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>Classification</div>
                          <div style={{ fontSize: '15px', fontWeight: 800, color: selectedEvent.review_status === 'REVIEW_SUGGESTED' ? '#dc2626' : '#0f172a' }}>
                            {selectedEvent.classification}
                          </div>
                        </div>

                        <div>
                          <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>Observation Reason</div>
                          <div style={{ fontSize: '12px', color: '#334155', backgroundColor: '#f8fafc', padding: '8px 10px', borderRadius: '6px', marginTop: '4px' }}>
                            {selectedEvent.classification_reason || 'Editing activity consistent with observed session rhythm.'}
                          </div>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
                          <div>
                            <span style={{ color: '#64748b' }}>Characters:</span> <strong>+{selectedEvent.inserted_character_count || 0} / -{selectedEvent.deleted_character_count || 0}</strong>
                          </div>
                          <div>
                            <span style={{ color: '#64748b' }}>Timestamp:</span> <strong>{new Date(selectedEvent.timestamp).toLocaleTimeString()}</strong>
                          </div>
                        </div>

                        {/* Code revision compare preview */}
                        {selectedEvent.revision_id && (
                          <div style={{ marginTop: '8px', borderTop: '1px solid #f1f5f9', paddingTop: '10px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ fontSize: '11px', fontWeight: 700, color: '#4f46e5', textTransform: 'uppercase' }}>
                                Code Snapshot Available
                              </span>
                              <span style={{ fontSize: '11px', color: '#64748b' }}>Revision #{selectedEvent.revision_id}</span>
                            </div>

                            {revisionData && (
                              <div style={{ marginTop: '8px', backgroundColor: '#0f172a', color: '#f8fafc', padding: '10px', borderRadius: '6px', fontSize: '11px', fontFamily: 'monospace', maxHeight: '140px', overflowY: 'auto', whiteSpace: 'pre-wrap' }}>
                                {revisionData.current_code.slice(0, 400)}
                                {revisionData.current_code.length > 400 ? '\n... (truncated)' : ''}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div style={{ color: '#94a3b8', fontSize: '13px' }}>Select an event on the left to inspect.</div>
                    )}
                  </div>

                  {/* Trainer Review Action Card */}
                  <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '20px' }}>
                    <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a', margin: '0 0 8px 0' }}>
                      Trainer Review Actions
                    </h3>
                    <p style={{ fontSize: '12px', color: '#64748b', margin: '0 0 12px 0' }}>
                      Mark events reviewed or dismiss non-misconduct.
                    </p>

                    <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                      <button
                        onClick={() => handleReviewAction('MARK_REVIEWED')}
                        disabled={submittingReview}
                        style={{
                          flex: 1,
                          padding: '8px',
                          backgroundColor: '#059669',
                          color: '#ffffff',
                          border: 'none',
                          borderRadius: '6px',
                          fontSize: '12px',
                          fontWeight: 700,
                          cursor: 'pointer',
                        }}
                      >
                        ✓ Mark Reviewed
                      </button>
                      <button
                        onClick={() => handleReviewAction('DISMISS')}
                        disabled={submittingReview}
                        style={{
                          flex: 1,
                          padding: '8px',
                          backgroundColor: '#64748b',
                          color: '#ffffff',
                          border: 'none',
                          borderRadius: '6px',
                          fontSize: '12px',
                          fontWeight: 700,
                          cursor: 'pointer',
                        }}
                      >
                        ✕ Dismiss
                      </button>
                    </div>

                    <textarea
                      placeholder="Add academic review notes..."
                      value={reviewNote}
                      onChange={(e) => setReviewNote(e.target.value)}
                      rows={2}
                      style={{
                        width: '100%',
                        padding: '8px',
                        fontSize: '12px',
                        border: '1px solid #cbd5e1',
                        borderRadius: '6px',
                        marginBottom: '8px',
                      }}
                    />

                    <button
                      onClick={() => handleReviewAction('ADD_NOTE')}
                      disabled={!reviewNote.trim() || submittingReview}
                      style={{
                        width: '100%',
                        padding: '6px',
                        backgroundColor: '#1e293b',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: 600,
                        cursor: reviewNote.trim() ? 'pointer' : 'not-allowed',
                      }}
                    >
                      Save Review Note
                    </button>

                    {/* Existing Review Notes */}
                    {selectedSession.review_notes && (
                      <div style={{ marginTop: '12px', padding: '10px', backgroundColor: '#f8fafc', borderRadius: '6px', fontSize: '11px', color: '#475569', whiteSpace: 'pre-wrap' }}>
                        <strong>Trainer Notes:</strong>
                        <div>{selectedSession.review_notes}</div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div style={{ padding: '60px', textAlign: 'center', backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', color: '#94a3b8' }}>
              Select an assessment session from the left column to view its typing rhythm and timeline.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
