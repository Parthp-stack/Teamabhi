import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { learningService } from '../services/learningService';
import {
  Sparkles,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  GitFork,
  BookOpen,
} from 'lucide-react';

export default function StudentDashboard() {
  const navigate = useNavigate();
  const [learningPath, setLearningPath] = useState(null);
  const [masteryData, setMasteryData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [path, mastery] = await Promise.all([
          learningService.getLearningPath(),
          learningService.getStudentMastery(),
        ]);
        setLearningPath(path);
        setMasteryData(mastery);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: '#64748b' }}>
        <Sparkles size={32} color="#4f46e5" style={{ animation: 'spin 2s linear infinite', marginBottom: '12px' }} />
        <div style={{ fontSize: '16px', fontWeight: 600 }}>Loading adaptive learning profile...</div>
      </div>
    );
  }

  const strongCount = masteryData?.concepts?.filter((c) => c.status === 'STRONG').length || 0;
  const weakCount = masteryData?.concepts?.filter((c) => c.status === 'WEAK').length || 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1100px' }}>
      {/* Recommended Next Topic Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
          borderRadius: '16px',
          padding: '28px 32px',
          color: '#ffffff',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 10px 20px rgba(79, 70, 229, 0.2)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <Sparkles size={18} color="#fde047" />
            <span style={{ fontSize: '11px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Adaptive Recommendation · Weakest Eligible Prerequisite
            </span>
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 800, margin: '0 0 8px 0' }}>
            Recommended Next: {learningPath?.current_concept || 'Object Oriented Programming'}
          </h2>
          <p style={{ margin: 0, fontSize: '14px', color: '#e0e7ff', maxWidth: '640px', lineHeight: '1.5' }}>
            {learningPath?.reason || 'Based on your prerequisite competency, the adaptive engine identified this topic as your optimal learning target.'}
          </p>
        </div>
        <button
          onClick={() => navigate('/student/learning')}
          style={{
            padding: '12px 24px',
            backgroundColor: '#ffffff',
            color: '#4f46e5',
            border: 'none',
            borderRadius: '10px',
            fontWeight: 800,
            fontSize: '14px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
            whiteSpace: 'nowrap',
          }}
        >
          Practice Question <ArrowRight size={16} />
        </button>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
            Current Course
          </div>
          <div style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: '6px 0 2px 0' }}>
            OOP Foundations
          </div>
          <div style={{ fontSize: '12px', color: '#64748b' }}>5 Modules · 7 Concepts</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
            Overall Mastery
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#4f46e5', margin: '4px 0' }}>
            {masteryData?.overall_mastery || 0}%
          </div>
          <div style={{ fontSize: '12px', color: '#10b981', fontWeight: 600 }}>Bayesian Tracing Average</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
            Strong Concepts
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#10b981', margin: '4px 0' }}>
            {strongCount}
          </div>
          <div style={{ fontSize: '12px', color: '#64748b' }}>Mastery score ≥ 75%</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
            Weak Concepts
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#f59e0b', margin: '4px 0' }}>
            {weakCount}
          </div>
          <div style={{ fontSize: '12px', color: '#64748b' }}>Mastery score &lt; 50%</div>
        </div>
      </div>

      {/* Concept Progress List */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
              Syllabus Concept Mastery Breakdown
            </h3>
            <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#64748b' }}>
              Adaptive prerequisite knowledge graph tracking. Prerequisite threshold: 65%.
            </p>
          </div>
          <button
            onClick={() => navigate('/student/concept-map')}
            style={{
              padding: '8px 16px',
              backgroundColor: '#f1f5f9',
              color: '#334155',
              border: 'none',
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <GitFork size={15} /> Visual Concept Map →
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '14px' }}>
          {masteryData?.concepts?.map((c) => {
            const isStrong = c.status === 'STRONG';
            const isWeak = c.status === 'WEAK';
            const isLocked = c.status === 'LOCKED';

            return (
              <div
                key={c.concept_id}
                style={{
                  padding: '16px',
                  borderRadius: '10px',
                  border: `1.5px solid ${isStrong ? '#d1fae5' : isWeak ? '#fed7aa' : isLocked ? '#e2e8f0' : '#dbeafe'}`,
                  backgroundColor: isStrong ? '#f0fdf4' : isWeak ? '#fffbeb' : isLocked ? '#f8fafc' : '#eff6ff',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontWeight: 800, fontSize: '14px', color: '#0f172a' }}>{c.concept_name}</span>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 800,
                      textTransform: 'uppercase',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      backgroundColor: isStrong ? '#dcfce7' : isWeak ? '#ffedd5' : isLocked ? '#f1f5f9' : '#dbeafe',
                      color: isStrong ? '#166534' : isWeak ? '#9a3412' : isLocked ? '#64748b' : '#1e40af',
                    }}
                  >
                    {c.status}
                  </span>
                </div>

                <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '10px', minHeight: '36px' }}>
                  {c.description}
                </div>

                {/* Progress Bar */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ flex: 1, height: '6px', backgroundColor: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${c.mastery_score}%`,
                        height: '100%',
                        backgroundColor: isStrong ? '#16a34a' : isWeak ? '#ea580c' : isLocked ? '#94a3b8' : '#2563eb',
                      }}
                    />
                  </div>
                  <span style={{ fontWeight: 800, fontSize: '13px', color: '#0f172a', width: '38px', textAlign: 'right' }}>
                    {c.mastery_score.toFixed(0)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
