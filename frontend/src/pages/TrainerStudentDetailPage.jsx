import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { trainerService } from '../services/codingService';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  User,
  Award,
  ArrowLeft,
  Clock,
  PlayCircle,
  Code2,
  AlertTriangle,
} from 'lucide-react';

export default function TrainerStudentDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await trainerService.getStudentDeepDive(id);
        setData(res);
      } catch (err) {
        console.error('Failed to load student deep dive:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: '#64748b' }}>
        Loading student record...
      </div>
    );
  }

  const chartData = data?.history?.map((h, i) => ({
    name: `#${i + 1}`,
    mastery: h.mastery,
    reason: h.reason,
    time: new Date(h.timestamp).toLocaleTimeString(),
  })) || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1200px' }}>
      {/* Back button & Header */}
      <div>
        <button
          onClick={() => navigate('/trainer/dashboard')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'none',
            border: 'none',
            color: '#6366f1',
            fontWeight: 600,
            fontSize: '13px',
            cursor: 'pointer',
            padding: 0,
            marginBottom: '10px',
          }}
        >
          <ArrowLeft size={16} /> Back to Trainer Overview
        </button>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a', margin: '0 0 4px 0' }}>
              {data?.student?.name}
            </h1>
            <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>
              {data?.student?.email} · Enrolled: {new Date(data?.student?.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>

      {/* Concept Mastery Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
        {data?.concepts?.map((c) => (
          <div
            key={c.concept_id}
            style={{
              padding: '16px',
              backgroundColor: '#ffffff',
              borderRadius: '12px',
              border: '1px solid #e5e7eb',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontWeight: 700, fontSize: '14px', color: '#111827' }}>{c.name}</span>
              <span
                style={{
                  fontWeight: 800,
                  fontSize: '15px',
                  color: c.mastery >= 75 ? '#16a34a' : c.mastery >= 50 ? '#2563eb' : '#dc2626',
                }}
              >
                {c.mastery.toFixed(0)}%
              </span>
            </div>
            <div
              style={{
                height: '6px',
                backgroundColor: '#e5e7eb',
                borderRadius: '3px',
                overflow: 'hidden',
                marginBottom: '8px',
              }}
            >
              <div
                style={{
                  width: `${c.mastery}%`,
                  height: '100%',
                  backgroundColor: c.mastery >= 75 ? '#16a34a' : c.mastery >= 50 ? '#3b82f6' : '#ea580c',
                }}
              />
            </div>
            <div style={{ fontSize: '11px', color: '#6b7280' }}>
              {c.attempts} attempts · {c.correct_attempts} correct
            </div>
          </div>
        ))}
      </div>

      {/* Historical Knowledge Tracing Chart */}
      {chartData.length > 0 && (
        <div style={{ backgroundColor: '#ffffff', padding: '24px', borderRadius: '14px', border: '1px solid #e5e7eb' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#111827', margin: '0 0 16px 0' }}>
            Bayesian Knowledge Tracing Progression
          </h3>
          <div style={{ width: '100%', height: '240px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={12} />
                <Tooltip />
                <Line type="monotone" dataKey="mastery" stroke="#4f46e5" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Learning Path & Recommendation Summary (Section 9) */}
      {data?.learning_path && (
        <div style={{ backgroundColor: '#ffffff', padding: '24px', borderRadius: '14px', border: '1px solid #e5e7eb' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#111827', margin: 0 }}>
              Student's Adaptive Learning Path
            </h3>
            <span style={{ fontSize: '12px', fontWeight: 700, color: '#4f46e5' }}>
              Target Concept: {data.learning_path.current_concept}
            </span>
          </div>

          <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '10px' }}>
            {data.learning_path.path?.map((step, idx) => (
              <div
                key={step.concept_id}
                style={{
                  padding: '10px 14px',
                  borderRadius: '8px',
                  border: step.is_target ? '2px solid #4f46e5' : '1px solid #e2e8f0',
                  backgroundColor: step.is_target ? '#eef2ff' : '#f8fafc',
                  minWidth: '120px',
                  textAlign: 'center',
                }}
              >
                <div style={{ fontWeight: 800, fontSize: '12px', color: step.is_target ? '#4338ca' : '#1e293b' }}>
                  {step.concept_name}
                </div>
                <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                  {step.mastery.toFixed(0)}% · {step.status}
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: '12px', padding: '10px 14px', backgroundColor: '#f8fafc', borderRadius: '8px', fontSize: '12px', color: '#475569' }}>
            <strong>Engine Rationale:</strong> {data.learning_path.reason}
          </div>
        </div>
      )}

      {/* Quiz Attempts (Section 9) */}
      {data?.quiz_attempts && data.quiz_attempts.length > 0 && (
        <div style={{ backgroundColor: '#ffffff', padding: '24px', borderRadius: '14px', border: '1px solid #e5e7eb' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#111827', margin: '0 0 16px 0' }}>
            Recent Quiz Attempts
          </h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e5e7eb', color: '#64748b' }}>
                <th style={{ padding: '8px 12px' }}>Question / Concept</th>
                <th style={{ padding: '8px 12px' }}>Answer</th>
                <th style={{ padding: '8px 12px' }}>Score</th>
                <th style={{ padding: '8px 12px' }}>Result</th>
                <th style={{ padding: '8px 12px' }}>Date</th>
              </tr>
            </thead>
            <tbody>
              {data.quiz_attempts.map((att) => (
                <tr key={att.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '10px 12px' }}>
                    <div style={{ fontWeight: 600, color: '#0f172a' }}>{att.question_text}</div>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>{att.concept_name}</span>
                  </td>
                  <td style={{ padding: '10px 12px', color: '#475569' }}>{att.selected_answer}</td>
                  <td style={{ padding: '10px 12px', fontWeight: 700 }}>{att.score}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <span
                      style={{
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: att.is_correct ? '#ecfdf5' : '#fef2f2',
                        color: att.is_correct ? '#047857' : '#b91c1c',
                      }}
                    >
                      {att.is_correct ? 'CORRECT' : 'INCORRECT'}
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px', color: '#64748b', fontSize: '12px' }}>
                    {new Date(att.timestamp).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Coding Submissions & Viva Comprehension Scores */}
      <div style={{ backgroundColor: '#ffffff', padding: '24px', borderRadius: '14px', border: '1px solid #e5e7eb' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#111827', margin: '0 0 16px 0' }}>
          Coding Submissions & Code Viva Comprehension
        </h3>
        {data?.submissions?.length === 0 ? (
          <div style={{ color: '#6b7280', fontSize: '13px' }}>No coding submissions yet.</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e5e7eb', color: '#64748b' }}>
                <th style={{ padding: '10px 14px' }}>Problem</th>
                <th style={{ padding: '10px 14px' }}>Language</th>
                <th style={{ padding: '10px 14px' }}>Status</th>
                <th style={{ padding: '10px 14px' }}>Test Score</th>
                <th style={{ padding: '10px 14px' }}>Viva Voce Score</th>
                <th style={{ padding: '10px 14px' }}>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {data?.submissions?.map((sub) => (
                <tr key={sub.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '12px 14px', fontWeight: 600, color: '#1e293b' }}>{sub.problem_title}</td>
                  <td style={{ padding: '12px 14px', color: '#64748b', textTransform: 'uppercase' }}>{sub.language}</td>
                  <td style={{ padding: '12px 14px' }}>
                    <span
                      style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontWeight: 700,
                        fontSize: '11px',
                        backgroundColor: sub.status === 'PASSED' ? '#ecfdf5' : '#fef2f2',
                        color: sub.status === 'PASSED' ? '#047857' : '#b91c1c',
                      }}
                    >
                      {sub.status}
                    </span>
                  </td>
                  <td style={{ padding: '12px 14px', fontWeight: 700 }}>{sub.score}%</td>
                  <td style={{ padding: '12px 14px' }}>
                    {sub.viva_score !== null ? (
                      <span
                        style={{
                          fontWeight: 700,
                          color: sub.viva_score >= 7.0 ? '#10b981' : '#f59e0b',
                        }}
                      >
                        {sub.viva_score} / 10
                      </span>
                    ) : (
                      <span style={{ color: '#94a3b8' }}>Pending</span>
                    )}
                  </td>
                  <td style={{ padding: '12px 14px', color: '#64748b' }}>
                    {new Date(sub.created_at).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Recorded Sessions & Integrity Dashboard Link (Section 9 & 10) */}
      <div style={{ backgroundColor: '#ffffff', padding: '24px', borderRadius: '14px', border: '1px solid #e5e7eb' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#111827', margin: 0 }}>
              Recorded Assessment Sessions (Evidence Timelines)
            </h3>
            <p style={{ margin: '2px 0 0 0', fontSize: '12px', color: '#64748b' }}>
              Full session audit trails, typing rhythms, and human review evidence
            </p>
          </div>
          <button
            onClick={() => navigate(`/trainer/integrity?student_id=${data?.student?.id}`)}
            style={{
              padding: '6px 12px',
              backgroundColor: '#eef2ff',
              color: '#4f46e5',
              border: '1px solid #c7d2fe',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Open in Integrity Dashboard →
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {data?.sessions?.map((sess) => (
            <div
              key={sess.id}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '12px 16px',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                backgroundColor: '#ffffff',
              }}
            >
              <div>
                <span style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>
                  Session #{sess.id} · {sess.problem_title}
                </span>
                <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
                  {sess.total_events} recorded events · {sess.signals_count} integrity signals · Review Status: <strong>{sess.overall_review_status}</strong>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={() => navigate(`/trainer/replay/${sess.id}`)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 14px',
                    backgroundColor: '#4f46e5',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  <PlayCircle size={14} /> Full Replay Studio
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
