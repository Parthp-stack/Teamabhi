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
  Sparkles,
  ChevronRight,
  Code2,
  Copy,
  ClipboardPaste,
  Maximize2,
  Minimize2,
  Columns,
  Layers,
  ArrowUpDown,
  RefreshCw,
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
import { authService } from '../services/authService';

export default function CodingIntegrityDashboard({ isStudentView = false }) {
  const navigate = useNavigate();
  const currentUser = authService.getCurrentUser();
  const isTrainer = currentUser?.role === 'TRAINER' && !isStudentView;

  // Active view: 'TABLE' (mandatory 12-column table & 11 summary cards) or 'RHYTHM' (deep dive / replay)
  const [activeTab, setActiveTab] = useState('TABLE');

  // ==========================================
  // TABLE STATE (Requirement 4, 7, 8)
  // ==========================================
  const [loadingTable, setLoadingTable] = useState(true);
  const [tableEvents, setTableEvents] = useState([]);
  const [tableSummary, setTableSummary] = useState(null);
  const [totalCount, setTotalCount] = useState(0);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStudentFilter, setSelectedStudentFilter] = useState('');
  const [selectedAssessmentFilter, setSelectedAssessmentFilter] = useState('');
  const [selectedAttemptFilter, setSelectedAttemptFilter] = useState('');
  const [selectedEventType, setSelectedEventType] = useState('ALL');
  const [selectedRiskLevel, setSelectedRiskLevel] = useState('ALL');
  const [sortBy, setSortBy] = useState('timestamp');
  const [sortOrder, setSortOrder] = useState('desc');

  // ==========================================
  // RHYTHM & SESSIONS STATE (Preserved features)
  // ==========================================
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [rhythmMetrics, setRhythmMetrics] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [revisionData, setRevisionData] = useState(null);
  const [reviewNote, setReviewNote] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);

  // Fetch 12-column table & summary cards
  const fetchTableData = async () => {
    try {
      setLoadingTable(true);
      const params = {
        search: searchQuery || undefined,
        student_id: isTrainer ? (selectedStudentFilter || undefined) : currentUser?.id,
        assessment_id: selectedAssessmentFilter || undefined,
        attempt_id: selectedAttemptFilter || undefined,
        event_type: selectedEventType !== 'ALL' ? selectedEventType : undefined,
        risk_level: selectedRiskLevel !== 'ALL' ? selectedRiskLevel : undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        limit: 200,
      };

      const res = await integrityService.getIntegrityEvents(params);
      setTableEvents(res.events || []);
      setTableSummary(res.summary || null);
      setTotalCount(res.total || 0);
    } catch (err) {
      console.error('Failed to load integrity events table:', err);
    } finally {
      setLoadingTable(false);
    }
  };

  useEffect(() => {
    fetchTableData();
  }, [
    selectedStudentFilter,
    selectedAssessmentFilter,
    selectedAttemptFilter,
    selectedEventType,
    selectedRiskLevel,
    sortBy,
    sortOrder,
  ]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchTableData();
  };

  // Fetch sessions for Rhythm view
  const fetchDashboardSessions = async () => {
    if (!isTrainer) return;
    try {
      setLoadingSessions(true);
      const data = await integrityService.getDashboardSessions({});
      setDashboardData(data);
      if (data.sessions && data.sessions.length > 0 && !selectedSessionId) {
        loadSessionDetail(data.sessions[0].id);
      }
    } catch (err) {
      console.error('Failed to load sessions for rhythm view:', err);
    } finally {
      setLoadingSessions(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'RHYTHM') {
      fetchDashboardSessions();
    }
  }, [activeTab]);

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
        const firstReview = timeline.find((e) => e.review_status === 'REVIEW_SUGGESTED') || timeline[0];
        handleSelectEvent(firstReview, sessionId);
      }
    } catch (err) {
      console.error('Failed to load session details:', err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleSelectEvent = async (eventItem, sessId = selectedSessionId) => {
    setSelectedEvent(eventItem);
    setRevisionData(null);
    if (eventItem.revision_id) {
      try {
        const rev = await integrityService.getRevisionComparison(sessId, eventItem.revision_id);
        setRevisionData(rev);
      } catch (err) {
        console.warn('Could not load code revision:', err);
      }
    }
  };

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
      const updatedTimeline = await integrityService.getSessionTimeline(selectedSessionId);
      setTimelineEvents(updatedTimeline);
      fetchDashboardSessions();
      fetchTableData();
    } catch (err) {
      console.error('Review action failed:', err);
    } finally {
      setSubmittingReview(false);
    }
  };

  const selectedSession = dashboardData?.sessions?.find((s) => s.id === selectedSessionId);

  // Helper for risk badge styling
  const renderRiskBadge = (risk) => {
    const r = (risk || 'Normal').toUpperCase();
    if (r === 'HIGH' || r === 'HIGH_RISK') {
      return (
        <span style={{ backgroundColor: '#fef2f2', color: '#dc2626', border: '1px solid #fecaca', padding: '3px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 700 }}>
          ▲ High
        </span>
      );
    }
    if (r === 'MEDIUM' || r === 'MEDIUM_RISK') {
      return (
        <span style={{ backgroundColor: '#fffbeb', color: '#d97706', border: '1px solid #fde68a', padding: '3px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 700 }}>
          ▲ Medium
        </span>
      );
    }
    if (r === 'LOW' || r === 'LOW_RISK') {
      return (
        <span style={{ backgroundColor: '#eff6ff', color: '#2563eb', border: '1px solid #bfdbfe', padding: '3px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 700 }}>
          ● Low
        </span>
      );
    }
    return (
      <span style={{ backgroundColor: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0', padding: '3px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 700 }}>
        ● Normal
      </span>
    );
  };

  // Helper for event type badge styling
  const renderEventTypeBadge = (eventType) => {
    const et = (eventType || '').toUpperCase();
    let bg = '#f8fafc';
    let text = '#334155';
    let border = '#e2e8f0';

    if (et.includes('COPY') || et.includes('CTRL+C')) {
      bg = '#eef2ff'; text = '#4f46e5'; border = '#c7d2fe';
    } else if (et.includes('PASTE') || et.includes('CTRL+V')) {
      bg = '#fef3c7'; text = '#b45309'; border = '#fde68a';
    } else if (et.includes('TAB_SWITCH') || et.includes('VISIBILITY')) {
      bg = '#fee2e2'; text = '#b91c1c'; border = '#fecaca';
    } else if (et.includes('WINDOW_BLUR')) {
      bg = '#fef2f2'; text = '#dc2626'; border = '#fecaca';
    } else if (et.includes('FULLSCREEN')) {
      bg = '#ffedd5'; text = '#c2410c'; border = '#fed7aa';
    } else if (et.includes('SPLIT_SCREEN')) {
      bg = '#fce7f3'; text = '#be185d'; border = '#fbcfe8';
    } else if (et.includes('RUN')) {
      bg = '#f0fdf4'; text = '#15803d'; border = '#bbf7d0';
    } else if (et.includes('SUBMISSION') || et.includes('SUBMIT')) {
      bg = '#ecfdf5'; text = '#047857'; border = '#a7f3d0';
    }

    return (
      <span style={{ backgroundColor: bg, color: text, border: `1px solid ${border}`, padding: '2px 8px', borderRadius: '6px', fontSize: '11px', fontWeight: 800 }}>
        {eventType}
      </span>
    );
  };

  // Chart data for typing rhythm tab
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
    <div style={{ maxWidth: '1440px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Banner */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '16px',
          border: '1px solid #e2e8f0',
          padding: '20px 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ padding: '10px', backgroundColor: '#eef2ff', borderRadius: '12px', color: '#4f46e5' }}>
            <ShieldAlert size={28} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                Student Integrity
              </h1>
              <span style={{ fontSize: '11px', fontWeight: 700, backgroundColor: isTrainer ? '#f1f5f9' : '#e0e7ff', color: isTrainer ? '#475569' : '#4338ca', padding: '2px 8px', borderRadius: '12px' }}>
                {isTrainer ? 'Trainer View' : 'Student Assessment View'}
              </span>
            </div>
            <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0 0' }}>
              Full audit trail of assessment and coding environment activities from actual database records.
            </p>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            onClick={() => setActiveTab('TABLE')}
            style={{
              padding: '8px 16px',
              backgroundColor: activeTab === 'TABLE' ? '#4f46e5' : '#f8fafc',
              border: `1px solid ${activeTab === 'TABLE' ? '#4f46e5' : '#cbd5e1'}`,
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: 700,
              color: activeTab === 'TABLE' ? '#ffffff' : '#334155',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Layers size={15} /> All Integrity Events Table
          </button>

          {isTrainer && (
            <button
              onClick={() => setActiveTab('RHYTHM')}
              style={{
                padding: '8px 16px',
                backgroundColor: activeTab === 'RHYTHM' ? '#4f46e5' : '#f8fafc',
                border: `1px solid ${activeTab === 'RHYTHM' ? '#4f46e5' : '#cbd5e1'}`,
                borderRadius: '8px',
                fontSize: '13px',
                fontWeight: 700,
                color: activeTab === 'RHYTHM' ? '#ffffff' : '#334155',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <Activity size={15} /> Typing Rhythm & Replay
            </button>
          )}

          <button
            onClick={fetchTableData}
            title="Refresh database records"
            style={{
              padding: '8px 12px',
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: 600,
              color: '#334155',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {/* ======================================================== */}
      {/* 8. STUDENT INTEGRITY SUMMARY CARDS (Actual DB Records)  */}
      {/* ======================================================== */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '12px' }}>
        {/* Card 1: Total Events */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '14px 16px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
            Total Events
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a', marginTop: '4px' }}>
            {tableSummary?.total_events || 0}
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>Recorded in DB</div>
        </div>

        {/* Card 2: Copy Events */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '14px 16px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#4f46e5', textTransform: 'uppercase' }}>
            Ctrl+C / Copy
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#4f46e5', marginTop: '4px' }}>
            {tableSummary?.copy_events || 0}
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>Clipboard copies</div>
        </div>

        {/* Card 3: Paste Events */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '14px 16px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#d97706', textTransform: 'uppercase' }}>
            Ctrl+V / Paste
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#d97706', marginTop: '4px' }}>
            {tableSummary?.paste_events || 0}
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>Clipboard pastes</div>
        </div>

        {/* Card 4: Tab Switches */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '14px 16px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#dc2626', textTransform: 'uppercase' }}>
            Tab Switches
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#dc2626', marginTop: '4px' }}>
            {tableSummary?.tab_switches || 0}
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>Tab visibility changes</div>
        </div>

        {/* Card 5: Window Blur */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '14px 16px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#ea580c', textTransform: 'uppercase' }}>
            Window Blur
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#ea580c', marginTop: '4px' }}>
            {tableSummary?.window_blur_events || 0}
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>Focus lost events</div>
        </div>

        {/* Card 6: Fullscreen Exits */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '14px 16px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#c026d3', textTransform: 'uppercase' }}>
            Fullscreen Exits
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#c026d3', marginTop: '4px' }}>
            {tableSummary?.fullscreen_exits || 0}
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>Exit fullscreen mode</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px' }}>
        {/* Card 7: Possible Split-Screen */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '14px 16px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#be185d', textTransform: 'uppercase' }}>
            Possible Split Screen
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#be185d', marginTop: '4px' }}>
            {tableSummary?.possible_split_screen_events || 0}
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>Resize anomalies (evidence)</div>
        </div>

        {/* Card 8: Code Runs */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '14px 16px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#16a34a', textTransform: 'uppercase' }}>
            Code Runs
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#16a34a', marginTop: '4px' }}>
            {tableSummary?.code_runs || 0}
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>Sandbox test executions</div>
        </div>

        {/* Card 9: Submissions */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '14px 16px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#0d9488', textTransform: 'uppercase' }}>
            Submissions
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#0d9488', marginTop: '4px' }}>
            {tableSummary?.submissions || 0}
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>Completed solutions</div>
        </div>

        {/* Card 10: Warnings */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '14px 16px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#e11d48', textTransform: 'uppercase' }}>
            Warnings
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#e11d48', marginTop: '4px' }}>
            {tableSummary?.warnings || 0}
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>Alerts issued</div>
        </div>

        {/* Card 11: Risk Score & Level */}
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '14px 16px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#475569', textTransform: 'uppercase' }}>
            Risk Score
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
            <span style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a' }}>
              {Math.round(tableSummary?.risk_score || 0)}
            </span>
            {renderRiskBadge(tableSummary?.risk_level || 'NORMAL')}
          </div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>Evaluated score (0-100)</div>
        </div>
      </div>

      {/* ======================================================== */}
      {/* VIEW 1: 12-COLUMN TABLE WITH FILTERS & SEARCH           */}
      {/* ======================================================== */}
      {activeTab === 'TABLE' && (
        <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', overflow: 'hidden' }}>
          {/* Filter Bar */}
          <div style={{ padding: '18px 20px', borderBottom: '1px solid #e2e8f0', backgroundColor: '#f8fafc', display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center', justifyContent: 'space-between' }}>
            {/* Search Input */}
            <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '8px', minWidth: '280px' }}>
              <div style={{ position: 'relative', flex: 1 }}>
                <Search size={14} style={{ position: 'absolute', left: '10px', top: '10px', color: '#94a3b8' }} />
                <input
                  type="text"
                  placeholder="Search student, event, action..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '7px 10px 7px 32px',
                    fontSize: '12px',
                    border: '1px solid #cbd5e1',
                    borderRadius: '6px',
                    backgroundColor: '#ffffff',
                  }}
                />
              </div>
              <button
                type="submit"
                style={{
                  padding: '7px 14px',
                  backgroundColor: '#0f172a',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Search
              </button>
            </form>

            {/* Dropdown Filters */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
              {/* Event Type Filter */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, color: '#64748b' }}>Event:</span>
                <select
                  value={selectedEventType}
                  onChange={(e) => setSelectedEventType(e.target.value)}
                  style={{ padding: '6px 10px', fontSize: '12px', borderRadius: '6px', border: '1px solid #cbd5e1', backgroundColor: '#ffffff' }}
                >
                  <option value="ALL">All Events</option>
                  <option value="COPY">Ctrl+C / Copy</option>
                  <option value="PASTE">Ctrl+V / Paste</option>
                  <option value="TAB_SWITCH">Tab Switch</option>
                  <option value="WINDOW_BLUR">Window Blur</option>
                  <option value="FULLSCREEN">Fullscreen Exit</option>
                  <option value="SPLIT_SCREEN">Possible Split Screen</option>
                  <option value="CODE_RUN">Code Run</option>
                  <option value="SUBMISSION">Submission</option>
                  <option value="ANSWER_SELECTED">Answer Selected</option>
                  <option value="ANSWER_CHANGED">Answer Changed</option>
                  <option value="QUESTION_REVISITED">Question Revisited</option>
                </select>
              </div>

              {/* Risk Level Filter */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, color: '#64748b' }}>Risk:</span>
                <select
                  value={selectedRiskLevel}
                  onChange={(e) => setSelectedRiskLevel(e.target.value)}
                  style={{ padding: '6px 10px', fontSize: '12px', borderRadius: '6px', border: '1px solid #cbd5e1', backgroundColor: '#ffffff' }}
                >
                  <option value="ALL">All Risks</option>
                  <option value="NORMAL">Normal</option>
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                </select>
              </div>

              {/* Sorting Filter */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, color: '#64748b' }}>Sort:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  style={{ padding: '6px 10px', fontSize: '12px', borderRadius: '6px', border: '1px solid #cbd5e1', backgroundColor: '#ffffff' }}
                >
                  <option value="timestamp">Timestamp</option>
                  <option value="student_name">Student Name</option>
                  <option value="risk_level">Risk Level</option>
                  <option value="event_type">Event Type</option>
                </select>

                <button
                  onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
                  style={{
                    padding: '6px 10px',
                    fontSize: '12px',
                    fontWeight: 600,
                    borderRadius: '6px',
                    border: '1px solid #cbd5e1',
                    backgroundColor: '#ffffff',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                  title="Toggle Chronological Order"
                >
                  <ArrowUpDown size={12} />
                  {sortOrder === 'desc' ? 'Newest' : 'Oldest'}
                </button>
              </div>
            </div>
          </div>

          {/* 12-Column Table */}
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '12px' }}>
              <thead>
                <tr style={{ backgroundColor: '#f1f5f9', borderBottom: '2px solid #e2e8f0', color: '#475569', textTransform: 'uppercase', fontSize: '11px', fontWeight: 700, letterSpacing: '0.04em' }}>
                  <th style={{ padding: '12px 14px' }}>#</th>
                  <th style={{ padding: '12px 14px' }}>Timestamp</th>
                  <th style={{ padding: '12px 14px' }}>Student Name</th>
                  <th style={{ padding: '12px 14px' }}>Student ID</th>
                  <th style={{ padding: '12px 14px' }}>Assessment</th>
                  <th style={{ padding: '12px 14px' }}>Attempt</th>
                  <th style={{ padding: '12px 14px' }}>Question</th>
                  <th style={{ padding: '12px 14px' }}>Event Type</th>
                  <th style={{ padding: '12px 14px' }}>Action</th>
                  <th style={{ padding: '12px 14px', minWidth: '220px' }}>Details</th>
                  <th style={{ padding: '12px 14px' }}>Risk Level</th>
                  <th style={{ padding: '12px 14px', minWidth: '160px' }}>Warning</th>
                  <th style={{ padding: '12px 14px' }}>Source</th>
                </tr>
              </thead>
              <tbody>
                {loadingTable ? (
                  <tr>
                    <td colSpan="13" style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
                      Loading database integrity records...
                    </td>
                  </tr>
                ) : tableEvents.length === 0 ? (
                  <tr>
                    <td colSpan="13" style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>
                      No integrity events found matching the criteria.
                    </td>
                  </tr>
                ) : (
                  tableEvents.map((row, idx) => (
                    <tr
                      key={row.id || idx}
                      style={{
                        borderBottom: '1px solid #f1f5f9',
                        backgroundColor: idx % 2 === 0 ? '#ffffff' : '#fafafa',
                        transition: 'background-color 0.15s ease',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f8fafc')}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = idx % 2 === 0 ? '#ffffff' : '#fafafa')}
                    >
                      <td style={{ padding: '10px 14px', color: '#94a3b8' }}>{idx + 1}</td>
                      <td style={{ padding: '10px 14px', fontWeight: 600, color: '#0f172a', whiteSpace: 'nowrap' }}>
                        {row.timestamp}
                      </td>
                      <td style={{ padding: '10px 14px', fontWeight: 700, color: '#1e293b' }}>
                        {row.student_name}
                      </td>
                      <td style={{ padding: '10px 14px', color: '#64748b' }}>
                        #{row.student_id}
                      </td>
                      <td style={{ padding: '10px 14px', color: '#334155', fontWeight: 600 }}>
                        {row.assessment}
                      </td>
                      <td style={{ padding: '10px 14px', textAlign: 'center', color: '#64748b' }}>
                        {row.attempt_no}
                      </td>
                      <td style={{ padding: '10px 14px', textAlign: 'center', fontWeight: 700, color: '#4f46e5' }}>
                        {row.question_no}
                      </td>
                      <td style={{ padding: '10px 14px', whiteSpace: 'nowrap' }}>
                        {renderEventTypeBadge(row.event_type)}
                      </td>
                      <td style={{ padding: '10px 14px', fontWeight: 600, color: '#334155' }}>
                        {row.action}
                      </td>
                      <td style={{ padding: '10px 14px', color: '#475569', fontSize: '11px', lineHeight: '1.4' }}>
                        {row.details}
                      </td>
                      <td style={{ padding: '10px 14px', whiteSpace: 'nowrap' }}>
                        {renderRiskBadge(row.risk_level)}
                      </td>
                      <td style={{ padding: '10px 14px', color: row.warning !== '-' ? '#b91c1c' : '#94a3b8', fontSize: '11px', fontWeight: row.warning !== '-' ? 600 : 400 }}>
                        {row.warning}
                      </td>
                      <td style={{ padding: '10px 14px', color: '#64748b', fontSize: '11px' }}>
                        {row.source}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Table Footer */}
          <div style={{ padding: '12px 20px', borderTop: '1px solid #e2e8f0', backgroundColor: '#f8fafc', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', color: '#64748b' }}>
            <span>Showing <strong>{tableEvents.length}</strong> of <strong>{totalCount}</strong> database records</span>
            <span>All integrity events strictly audited with zero automated punishment</span>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* VIEW 2: TYPING RHYTHM & REPLAY STUDIO (Trainer View)    */}
      {/* ======================================================== */}
      {activeTab === 'RHYTHM' && isTrainer && (
        <div style={{ display: 'grid', gridTemplateColumns: '400px 1fr', gap: '20px', alignItems: 'start' }}>
          {/* Left Column: Filterable Sessions List */}
          <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', backgroundColor: '#f8fafc' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a', margin: '0 0 4px 0' }}>
                Monitored Coding Sessions
              </h3>
              <p style={{ fontSize: '12px', color: '#64748b', margin: 0 }}>
                Select a session for typing rhythm and revision replay
              </p>
            </div>

            <div style={{ maxHeight: '650px', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
              {loadingSessions ? (
                <div style={{ padding: '30px', textAlign: 'center', color: '#94a3b8' }}>Loading sessions...</div>
              ) : dashboardData?.sessions?.length === 0 ? (
                <div style={{ padding: '30px', textAlign: 'center', color: '#94a3b8', fontSize: '13px' }}>
                  No sessions found.
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
                        {renderRiskBadge(sess.overall_review_status)}
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
                      {renderRiskBadge(selectedSession.overall_review_status)}
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
                    {renderRiskBadge(rhythmMetrics?.review_status || 'INSUFFICIENT_DATA')}
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
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Right: Selected Event Inspector & Trainer Action */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
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

                          {/* Code revision compare preview */}
                          {selectedEvent.revision_id && (
                            <div style={{ marginTop: '8px', borderTop: '1px solid #f1f5f9', paddingTop: '10px' }}>
                              <span style={{ fontSize: '11px', fontWeight: 700, color: '#4f46e5', textTransform: 'uppercase' }}>
                                Code Snapshot Available
                              </span>
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
      )}
    </div>
  );
}
