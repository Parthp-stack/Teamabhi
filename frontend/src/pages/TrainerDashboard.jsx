import React, { useState, useEffect } from 'react';
import { trainerService } from '../services/learningService';
import { Users, Award, BookOpen, AlertTriangle } from 'lucide-react';

export default function TrainerDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await trainerService.getBasicOverview();
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
      <div style={{ padding: '60px', textAlign: 'center', color: '#64748b' }}>
        Loading trainer overview...
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1100px' }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <span style={{ fontSize: '11px', fontWeight: 700, color: '#4f46e5', textTransform: 'uppercase' }}>
            Trainer View · Phase 2 Adaptive Analytics
          </span>
        </div>
        <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a', margin: '0 0 6px 0' }}>
          {data?.course?.title || 'Object Oriented Programming'}
        </h1>
        <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>
          {data?.course?.description}
        </p>
      </div>

      {/* Top Metric Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
            Enrolled Students
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#0f172a', margin: '4px 0' }}>
            {data?.total_students || 0}
          </div>
          <div style={{ fontSize: '12px', color: '#10b981', fontWeight: 600 }}>Active in Adaptive Syllabus</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
            Cohort Average Mastery
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#4f46e5', margin: '4px 0' }}>
            {data?.cohort_average_mastery || 0}%
          </div>
          <div style={{ fontSize: '12px', color: '#64748b' }}>Across all 7 DAG concepts</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
            Weakest Concept in Cohort
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, color: '#ea580c', margin: '6px 0' }}>
            {data?.weakest_concepts?.[0]?.name || 'None'}
          </div>
          <div style={{ fontSize: '12px', color: '#64748b' }}>
            Avg: {data?.weakest_concepts?.[0]?.average_mastery || 0}%
          </div>
        </div>
      </div>

      {/* Concepts & Average Mastery Breakdown Table */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '24px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: '0 0 16px 0' }}>
          Concepts & Average Mastery per Concept
        </h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#64748b' }}>
              <th style={{ padding: '12px 14px' }}>Concept Name</th>
              <th style={{ padding: '12px 14px' }}>Target Difficulty</th>
              <th style={{ padding: '12px 14px' }}>Cohort Average Mastery</th>
              <th style={{ padding: '12px 14px' }}>Status Indicator</th>
            </tr>
          </thead>
          <tbody>
            {data?.concepts?.map((c) => {
              const isWeak = c.average_mastery < 50;
              const isStrong = c.average_mastery >= 75;
              return (
                <tr key={c.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '14px', fontWeight: 700, color: '#0f172a' }}>{c.name}</td>
                  <td style={{ padding: '14px', color: '#64748b' }}>{c.difficulty}</td>
                  <td style={{ padding: '14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ width: '120px', height: '6px', backgroundColor: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
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
                  <td style={{ padding: '14px' }}>
                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: isStrong ? '#dcfce7' : isWeak ? '#ffedd5' : '#dbeafe',
                        color: isStrong ? '#166534' : isWeak ? '#9a3412' : '#1e40af',
                      }}
                    >
                      {isStrong ? 'Strong' : isWeak ? 'Needs Review' : 'Developing'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Student List */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '24px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: '0 0 16px 0' }}>
          Enrolled Students Overview
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px' }}>
          {data?.students?.map((s) => (
            <div
              key={s.id}
              style={{
                padding: '14px 16px',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                backgroundColor: '#f8fafc',
              }}
            >
              <div style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>{s.name}</div>
              <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px' }}>{s.email}</div>
              <div style={{ fontSize: '13px', fontWeight: 800, color: '#4f46e5' }}>
                Average Mastery: {s.average_mastery}%
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
