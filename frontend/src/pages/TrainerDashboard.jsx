import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { trainerService } from '../services/learningService';
import {
  Users,
  Award,
  BookOpen,
  AlertTriangle,
  Search,
  Filter,
  ArrowRight,
  ShieldAlert,
  FolderTree,
  GitBranch,
  Sparkles,
  BarChart3,
  CheckCircle2,
  Code2,
} from 'lucide-react';

export default function TrainerDashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Search & Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [masteryFilter, setMasteryFilter] = useState('ALL');

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const res = await trainerService.getDashboardOverview();
        setData(res);
      } catch (err) {
        console.error('Failed to load trainer overview:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '80px', textAlign: 'center', color: '#64748b' }}>
        <Users size={36} color="#4f46e5" style={{ animation: 'pulse 1.5s infinite', marginBottom: '12px' }} />
        <div style={{ fontSize: '18px', fontWeight: 700, color: '#1e293b' }}>
          Loading Trainer Cohort Analytics...
        </div>
      </div>
    );
  }

  // Filter students based on search and mastery criteria
  const students = data?.students || [];
  const filteredStudents = students.filter((s) => {
    const matchesSearch =
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.email.toLowerCase().includes(searchQuery.toLowerCase());

    let matchesFilter = true;
    if (masteryFilter === 'HIGH') matchesFilter = s.average_mastery >= 75;
    else if (masteryFilter === 'MEDIUM') matchesFilter = s.average_mastery >= 50 && s.average_mastery < 75;
    else if (masteryFilter === 'LOW') matchesFilter = s.average_mastery < 50;

    return matchesSearch && matchesFilter;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1180px', margin: '0 auto' }}>
      {/* Header & Quick Action Hub */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ fontSize: '11px', fontWeight: 800, color: '#4f46e5', textTransform: 'uppercase' }}>
              Trainer Administration · Cohort Mastery & Integrity Analytics
            </span>
          </div>
          <h1 style={{ fontSize: '26px', fontWeight: 800, color: '#0f172a', margin: '0 0 4px 0' }}>
            {data?.course?.title || 'Object Oriented Programming'}
          </h1>
          <p style={{ margin: 0, fontSize: '14px', color: '#64748b', maxWidth: '640px' }}>
            {data?.course?.description || 'Bayesian Knowledge Tracing and Sandbox Assessment Portal'}
          </p>
        </div>

        {/* Action Shortcuts */}
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => navigate('/trainer/curriculum')}
            style={{
              padding: '10px 16px',
              backgroundColor: '#ffffff',
              color: '#334155',
              border: '1px solid #cbd5e1',
              borderRadius: '8px',
              fontWeight: 700,
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
            }}
          >
            <FolderTree size={16} color="#4f46e5" /> Course & Question Bank
          </button>

          <button
            onClick={() => navigate('/trainer/integrity')}
            style={{
              padding: '10px 16px',
              backgroundColor: '#4f46e5',
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 700,
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: '0 2px 4px rgba(79, 70, 229, 0.25)',
            }}
          >
            <ShieldAlert size={16} /> Coding Integrity Dashboard
          </button>

          <button
            onClick={() => navigate('/trainer/repo-eval')}
            style={{
              padding: '10px 16px',
              backgroundColor: '#0f172a',
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 700,
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <GitBranch size={16} /> Repo Eval & DevOps
          </button>
        </div>
      </div>

      {/* Section 7: Class Overview Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
            Total Students
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#0f172a', margin: '4px 0' }}>
            {data?.total_students || 0}
          </div>
          <div style={{ fontSize: '12px', color: '#10b981', fontWeight: 600 }}>Active in Adaptive Syllabus</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
            Average Mastery
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#4f46e5', margin: '4px 0' }}>
            {data?.cohort_average_mastery || 0}%
          </div>
          <div style={{ fontSize: '12px', color: '#64748b' }}>Across all 7 DAG concepts</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
            Avg Assessment Score
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#16a34a', margin: '4px 0' }}>
            {data?.cohort_average_assessment_score || 0}%
          </div>
          <div style={{ fontSize: '12px', color: '#64748b' }}>Quiz attempt accuracy</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
            Coding Performance
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#2563eb', margin: '4px 0' }}>
            {data?.cohort_average_coding_score || 0}%
          </div>
          <div style={{ fontSize: '12px', color: '#64748b' }}>Sandbox test pass rate</div>
        </div>
      </div>

      {/* Cohort Recommendations Banner (Section 18) */}
      {data?.recommendations && data.recommendations.length > 0 && (
        <div
          style={{
            backgroundColor: '#fffbeb',
            borderRadius: '12px',
            border: '1px solid #fde68a',
            padding: '16px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} color="#d97706" />
            <span style={{ fontSize: '13px', fontWeight: 800, color: '#92400e', textTransform: 'uppercase' }}>
              Cohort Pedagogical Alert · Weak Concepts Requiring Attention
            </span>
          </div>
          {data.recommendations.map((rec, i) => (
            <div key={i} style={{ fontSize: '13px', color: '#78350f', marginLeft: '26px' }}>
              • <strong>{rec.concept_name}</strong>: {rec.message}
            </div>
          ))}
        </div>
      )}

      {/* Section 8: Trainer Concept Analytics */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
              Cohort Concept Mastery Distribution & Bottlenecks
            </h3>
            <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#64748b' }}>
              Average mastery per concept across all enrolled students. Highlights concepts where additional instruction is required.
            </p>
          </div>
          <span style={{ fontSize: '12px', fontWeight: 700, color: '#64748b' }}>
            Prerequisite Threshold: 65%
          </span>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#64748b' }}>
              <th style={{ padding: '12px 14px' }}>Concept Name</th>
              <th style={{ padding: '12px 14px' }}>Prerequisites</th>
              <th style={{ padding: '12px 14px' }}>Difficulty</th>
              <th style={{ padding: '12px 14px' }}>Avg Cohort Mastery</th>
              <th style={{ padding: '12px 14px' }}>Weak Students (&lt;50%)</th>
              <th style={{ padding: '12px 14px' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {data?.concepts?.map((c) => {
              const isWeak = c.average_mastery < 50;
              const isStrong = c.average_mastery >= 75;

              return (
                <tr key={c.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '14px', fontWeight: 800, color: '#0f172a' }}>
                    {c.name}
                  </td>
                  <td style={{ padding: '14px', color: '#64748b' }}>
                    {c.prerequisites && c.prerequisites.length > 0 ? c.prerequisites.join(', ') : 'None (Root)'}
                  </td>
                  <td style={{ padding: '14px', color: '#64748b', fontWeight: 600 }}>
                    {c.difficulty}
                  </td>
                  <td style={{ padding: '14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ width: '140px', height: '6px', backgroundColor: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${c.average_mastery}%`,
                            height: '100%',
                            backgroundColor: isStrong ? '#16a34a' : isWeak ? '#ea580c' : '#2563eb',
                          }}
                        />
                      </div>
                      <span style={{ fontWeight: 800, color: isStrong ? '#16a34a' : isWeak ? '#ea580c' : '#2563eb' }}>
                        {c.average_mastery}%
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '14px', fontWeight: 700, color: isWeak ? '#ea580c' : '#64748b' }}>
                    {c.weak_student_count} students ({c.weak_student_percent}%)
                  </td>
                  <td style={{ padding: '14px' }}>
                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 800,
                        backgroundColor: isStrong ? '#dcfce7' : isWeak ? '#ffedd5' : '#dbeafe',
                        color: isStrong ? '#166534' : isWeak ? '#9a3412' : '#1e40af',
                      }}
                    >
                      {isStrong ? 'STRONG' : isWeak ? 'BOTTLENECK' : 'DEVELOPING'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Section 7: Enrolled Student List with Search & Filtering */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
              Enrolled Students Directory & Performance Deep Dive
            </h3>
            <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#64748b' }}>
              Select any student to inspect their individual adaptive learning path, quiz attempts, and coding sessions.
            </p>
          </div>

          {/* Search & Filter Bar */}
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <div style={{ position: 'relative' }}>
              <Search size={14} color="#94a3b8" style={{ position: 'absolute', left: '10px', top: '10px' }} />
              <input
                type="text"
                placeholder="Search student name or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  padding: '8px 12px 8px 30px',
                  borderRadius: '8px',
                  border: '1px solid #cbd5e1',
                  fontSize: '13px',
                  width: '240px',
                }}
              />
            </div>

            <select
              value={masteryFilter}
              onChange={(e) => setMasteryFilter(e.target.value)}
              style={{
                padding: '8px 12px',
                borderRadius: '8px',
                border: '1px solid #cbd5e1',
                fontSize: '13px',
                backgroundColor: '#ffffff',
              }}
            >
              <option value="ALL">All Mastery Levels</option>
              <option value="HIGH">High Mastery (≥75%)</option>
              <option value="MEDIUM">Medium Mastery (50-74%)</option>
              <option value="LOW">Low Mastery (&lt;50%)</option>
            </select>
          </div>
        </div>

        {filteredStudents.length > 0 ? (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#64748b' }}>
                <th style={{ padding: '12px' }}>Student</th>
                <th style={{ padding: '12px' }}>Overall Mastery</th>
                <th style={{ padding: '12px' }}>Weakest Concept</th>
                <th style={{ padding: '12px' }}>Assessment Score</th>
                <th style={{ padding: '12px' }}>Coding Score</th>
                <th style={{ padding: '12px' }}>Last Activity</th>
                <th style={{ padding: '12px' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredStudents.map((s) => (
                <tr key={s.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '14px' }}>
                    <div style={{ fontWeight: 800, color: '#0f172a' }}>{s.name}</div>
                    <div style={{ fontSize: '12px', color: '#64748b' }}>{s.email}</div>
                  </td>
                  <td style={{ padding: '14px' }}>
                    <span
                      style={{
                        fontWeight: 800,
                        fontSize: '14px',
                        color: s.average_mastery >= 75 ? '#16a34a' : s.average_mastery >= 50 ? '#2563eb' : '#ea580c',
                      }}
                    >
                      {s.average_mastery}%
                    </span>
                  </td>
                  <td style={{ padding: '14px' }}>
                    <span
                      style={{
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: '#fee2e2',
                        color: '#991b1b',
                        padding: '2px 8px',
                        borderRadius: '4px',
                      }}
                    >
                      {s.weakest_concept}
                    </span>
                  </td>
                  <td style={{ padding: '14px', fontWeight: 700, color: '#0f172a' }}>
                    {s.assessment_score}%
                  </td>
                  <td style={{ padding: '14px', fontWeight: 700, color: '#0f172a' }}>
                    {s.coding_score}%
                  </td>
                  <td style={{ padding: '14px', color: '#64748b', fontSize: '12px' }}>
                    {new Date(s.last_activity).toLocaleDateString()}
                  </td>
                  <td style={{ padding: '14px' }}>
                    <button
                      onClick={() => navigate(`/trainer/student/${s.id}`)}
                      style={{
                        padding: '6px 14px',
                        backgroundColor: '#eef2ff',
                        color: '#4f46e5',
                        border: '1px solid #c7d2fe',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: 700,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      Inspect Student <ArrowRight size={13} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ padding: '48px', textAlign: 'center', color: '#94a3b8' }}>
            No students found matching current search criteria.
          </div>
        )}
      </div>
    </div>
  );
}
