import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { masteryService } from '../services/learningService';
import { codingService } from '../services/codingService';
import {
  Award,
  BookOpen,
  ArrowRight,
  TrendingUp,
  AlertCircle,
  Code2,
  CheckCircle2,
  Sparkles,
} from 'lucide-react';

export default function StudentDashboard() {
  const navigate = useNavigate();
  const [overview, setOverview] = useState(null);
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [mOverview, probs] = await Promise.all([
          masteryService.getMyMastery(),
          codingService.getProblems(),
        ]);
        setOverview(mOverview);
        setProblems(probs);
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
      <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
        Loading adaptive profile...
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px', maxWidth: '1200px' }}>
      {/* Top Adaptive Recommendation Banner */}
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
            <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Adaptive Recommendation
            </span>
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 800, margin: '0 0 8px 0' }}>
            Practice Target: {overview?.recommended_concept || 'Object-Oriented Programming'}
          </h2>
          <p style={{ margin: 0, fontSize: '14px', color: '#e0e7ff', maxWidth: '600px' }}>
            Based on your prerequisite competency and knowledge tracing model, our system identified this concept as your highest-priority learning target.
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
          }}
        >
          Start Practice <ArrowRight size={16} />
        </button>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '18px' }}>
        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e5e7eb' }}>
          <div style={{ fontSize: '12px', color: '#6b7280', fontWeight: 600, textTransform: 'uppercase' }}>
            Overall Mastery
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#111827', margin: '4px 0' }}>
            {overview?.overall_mastery}%
          </div>
          <div style={{ fontSize: '12px', color: '#10b981', fontWeight: 600 }}>
            Across 6 core OOP modules
          </div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e5e7eb' }}>
          <div style={{ fontSize: '12px', color: '#6b7280', fontWeight: 600, textTransform: 'uppercase' }}>
            Mastered Concepts
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#10b981', margin: '4px 0' }}>
            {overview?.strong_concepts?.length || 0}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280' }}>
            Competency score ≥ 75%
          </div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e5e7eb' }}>
          <div style={{ fontSize: '12px', color: '#6b7280', fontWeight: 600, textTransform: 'uppercase' }}>
            Concepts Needing Practice
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#f59e0b', margin: '4px 0' }}>
            {overview?.weak_concepts?.length || 0}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280' }}>
            Prerequisite priority queue
          </div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e5e7eb' }}>
          <div style={{ fontSize: '12px', color: '#6b7280', fontWeight: 600, textTransform: 'uppercase' }}>
            Coding Assessments
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: '#6366f1', margin: '4px 0' }}>
            {problems.length}
          </div>
          <div style={{ fontSize: '12px', color: '#6b7280' }}>
            Isolated sandbox challenges
          </div>
        </div>
      </div>

      {/* Concept Breakdown Grid */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e5e7eb', padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#111827', margin: 0 }}>
              Individual Concept Competencies
            </h3>
            <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#6b7280' }}>
              Mastery scores update dynamically via Bayesian learning updates after each attempt.
            </p>
          </div>
          <button
            onClick={() => navigate('/student/concept-map')}
            style={{
              padding: '8px 16px',
              backgroundColor: '#f3f4f6',
              color: '#374151',
              border: 'none',
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Open Interactive Concept Graph →
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
          {overview?.concepts?.map((c) => {
            const isWeak = c.mastery < 65;
            const isMastered = c.mastery >= 80;
            return (
              <div
                key={c.concept_id}
                style={{
                  padding: '16px',
                  borderRadius: '10px',
                  border: `1.5px solid ${isMastered ? '#d1fae5' : isWeak ? '#fed7aa' : '#e5e7eb'}`,
                  backgroundColor: isMastered ? '#f0fdf4' : isWeak ? '#fffbeb' : '#fafafa',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontWeight: 700, fontSize: '15px', color: '#111827' }}>{c.concept_name}</span>
                  <span
                    style={{
                      fontWeight: 800,
                      fontSize: '15px',
                      color: isMastered ? '#15803d' : isWeak ? '#c2410c' : '#1d4ed8',
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
                    marginBottom: '10px',
                  }}
                >
                  <div
                    style={{
                      width: `${c.mastery}%`,
                      height: '100%',
                      backgroundColor: isMastered ? '#16a34a' : isWeak ? '#ea580c' : '#2563eb',
                    }}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#6b7280' }}>
                  <span>{c.attempts} total attempts</span>
                  <span style={{ fontWeight: 600, color: isWeak ? '#c2410c' : '#4b5563' }}>
                    {isWeak ? 'Requires Attention' : 'On Track'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Coding Assessments List */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e5e7eb', padding: '24px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#111827', margin: '0 0 16px 0' }}>
          Available Coding Assessments (Sandbox Protected)
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {problems.map((prob) => (
            <div
              key={prob.id}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '16px 20px',
                border: '1px solid #e5e7eb',
                borderRadius: '10px',
                backgroundColor: '#ffffff',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontWeight: 700, fontSize: '15px', color: '#111827' }}>{prob.title}</span>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      backgroundColor: prob.difficulty === 'EASY' ? '#ecfdf5' : prob.difficulty === 'MEDIUM' ? '#eff6ff' : '#fef2f2',
                      color: prob.difficulty === 'EASY' ? '#047857' : prob.difficulty === 'MEDIUM' ? '#1d4ed8' : '#b91c1c',
                      padding: '2px 8px',
                      borderRadius: '4px',
                    }}
                  >
                    {prob.difficulty}
                  </span>
                </div>
                <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#6b7280' }}>
                  {prob.description.split('\n')[0]}
                </p>
              </div>
              <button
                onClick={() => navigate('/student/assessment', { state: { problemId: prob.id } })}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#4f46e5',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: 600,
                  fontSize: '13px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <Code2 size={16} /> Open Editor
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
