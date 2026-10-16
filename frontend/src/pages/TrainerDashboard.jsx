import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { trainerService } from '../services/codingService';
import IntegritySignalBadge from '../components/IntegritySignalBadge';
import {
  Users,
  Award,
  AlertTriangle,
  PlayCircle,
  Eye,
  ArrowUpRight,
  ShieldCheck,
} from 'lucide-react';

export default function TrainerDashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await trainerService.getDashboardOverview();
        setData(res);
      } catch (err) {
        console.error('Failed to load trainer dashboard:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: '#64748b' }}>
        Loading trainer analytics...
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px', maxWidth: '1200px' }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a', margin: '0 0 6px 0' }}>
          Trainer Analytics & Review Console
        </h1>
        <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>
          Monitor cohort mastery distribution, investigate integrity evidence timelines, and review student code viva scores.
        </p>
      </div>

      {/* Top Metrics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '18px' }}>
        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e5e7eb' }}>
          <div style={{ fontSize: '12px', color: '#6b7280', fontWeight: 600, textTransform: 'uppercase' }}>
            Enrolled Students
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#111827', margin: '4px 0' }}>
            {data?.total_students || 0}
          </div>
          <div style={{ fontSize: '12px', color: '#10b981', fontWeight: 600 }}>Active in OOP Course</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e5e7eb' }}>
          <div style={{ fontSize: '12px', color: '#6b7280', fontWeight: 600, textTransform: 'uppercase' }}>
            Cohort Average Mastery
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#4f46e5', margin: '4px 0' }}>
            {data?.average_mastery || 0}%
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280' }}>Across all 6 DAG concepts</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e5e7eb' }}>
          <div style={{ fontSize: '12px', color: '#6b7280', fontWeight: 600, textTransform: 'uppercase' }}>
            Weakest Cohort Concept
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, color: '#f59e0b', margin: '6px 0' }}>
            {data?.weakest_concepts?.[0]?.name || 'None'}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280' }}>
            Avg: {data?.weakest_concepts?.[0]?.average_mastery}%
          </div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e5e7eb' }}>
          <div style={{ fontSize: '12px', color: '#6b7280', fontWeight: 600, textTransform: 'uppercase' }}>
            Flagged Review Sessions
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#ef4444', margin: '4px 0' }}>
            {data?.flagged_sessions?.length || 0}
          </div>
          <div style={{ fontSize: '12px', color: '#dc2626', fontWeight: 600 }}>Requires Human Review</div>
        </div>
      </div>

      {/* Flagged Integrity Sessions Requiring Review */}
      {data?.flagged_sessions && data.flagged_sessions.length > 0 && (
        <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #fee2e2', padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <AlertTriangle size={18} color="#dc2626" />
            <h3 style={{ fontSize: '17px', fontWeight: 800, color: '#991b1b', margin: 0 }}>
              Assessment Integrity Signals (Evidence Requiring Human Review)
            </h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px' }}>
            {data.flagged_sessions.map((sess) => (
              <div
                key={sess.session_id}
                style={{
                  padding: '16px',
                  backgroundColor: '#fff5f5',
                  border: '1px solid #fecaca',
                  borderRadius: '10px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 800, fontSize: '14px', color: '#111827' }}>
                      {sess.student_name}
                    </span>
                    <span style={{ fontSize: '11px', color: '#6b7280' }}>· {sess.problem_title}</span>
                  </div>
                  <div style={{ fontSize: '12px', color: '#991b1b', marginBottom: '4px' }}>
                    <strong>{sess.signal_type.replace('_', ' ')}:</strong> {sess.description}
                  </div>
                  <div style={{ fontSize: '11px', color: '#6b7280' }}>
                    Recorded at {new Date(sess.timestamp).toLocaleTimeString()}
                  </div>
                </div>

                <button
                  onClick={() => navigate(`/trainer/replay/${sess.session_id}`)}
                  style={{
                    padding: '8px 14px',
                    backgroundColor: '#dc2626',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    fontWeight: 700,
                    fontSize: '12px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    whiteSpace: 'nowrap',
                  }}
                >
                  <PlayCircle size={14} /> Open Replay
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Student Roster Table */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e5e7eb', padding: '24px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#111827', margin: '0 0 16px 0' }}>
          Student Mastery & Assessment Roster
        </h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #e5e7eb', color: '#64748b' }}>
              <th style={{ padding: '12px 16px' }}>Student</th>
              <th style={{ padding: '12px 16px' }}>Email</th>
              <th style={{ padding: '12px 16px' }}>Average Mastery</th>
              <th style={{ padding: '12px 16px' }}>Coding Submissions</th>
              <th style={{ padding: '12px 16px' }}>Integrity Signals</th>
              <th style={{ padding: '12px 16px' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.students?.map((s) => (
              <tr key={s.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '14px 16px', fontWeight: 700, color: '#0f172a' }}>{s.name}</td>
                <td style={{ padding: '14px 16px', color: '#64748b' }}>{s.email}</td>
                <td style={{ padding: '14px 16px' }}>
                  <span
                    style={{
                      fontWeight: 800,
                      color: s.average_mastery >= 75 ? '#16a34a' : s.average_mastery >= 50 ? '#2563eb' : '#ea580c',
                    }}
                  >
                    {s.average_mastery}%
                  </span>
                </td>
                <td style={{ padding: '14px 16px', color: '#334155' }}>{s.submissions_count}</td>
                <td style={{ padding: '14px 16px' }}>
                  {s.signals_count > 0 ? (
                    <span
                      style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        backgroundColor: '#fee2e2',
                        color: '#991b1b',
                        fontWeight: 700,
                        fontSize: '11px',
                      }}
                    >
                      {s.signals_count} Signals (Review)
                    </span>
                  ) : (
                    <span style={{ color: '#10b981', fontWeight: 600, fontSize: '12px' }}>Clear</span>
                  )}
                </td>
                <td style={{ padding: '14px 16px' }}>
                  <button
                    onClick={() => navigate(`/trainer/student/${s.id}`)}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: '#f3f4f6',
                      border: '1px solid #d1d5db',
                      borderRadius: '6px',
                      color: '#1f2937',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    Deep Dive <ArrowUpRight size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
