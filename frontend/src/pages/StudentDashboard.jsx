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
  Award,
  Clock,
  Lock,
  Check,
  Search,
  Filter,
  BarChart3,
  History,
  Code2,
  HelpCircle,
  FileText,
  X,
  Target,
  Layers,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  Cell,
} from 'recharts';

export default function StudentDashboard() {
  const navigate = useNavigate();

  // Active Tab: 'overview' | 'analytics' | 'quizzes' | 'coding'
  const [activeTab, setActiveTab] = useState('overview');

  const [learningPath, setLearningPath] = useState(null);
  const [masteryData, setMasteryData] = useState(null);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [quizHistory, setQuizHistory] = useState([]);
  const [codingHistory, setCodingHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters for history tables
  const [quizSearch, setQuizSearch] = useState('');
  const [quizFilter, setQuizFilter] = useState('ALL');
  const [codingSearch, setCodingSearch] = useState('');

  // Explain Your Code Modal state
  const [selectedVivaSubmission, setSelectedVivaSubmission] = useState(null);
  const [selectedConceptModal, setSelectedConceptModal] = useState(null);

  // Requirement 4 & 13: Personalized Score & Concept Breakdown
  const [adaptiveScoreData, setAdaptiveScoreData] = useState(null);
  const [conceptBreakdownData, setConceptBreakdownData] = useState(null);
  const [aiEvaluations, setAiEvaluations] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState(null);
  const [selectedTopicId, setSelectedTopicId] = useState('ALL');

  useEffect(() => {
    async function loadAllDashboardData() {
      try {
        setLoading(true);
        const [path, mastery, analytics, quizzes, coding, score, breakdown, evals] = await Promise.all([
          learningService.getLearningPath().catch(() => null),
          learningService.getStudentMastery().catch(() => null),
          learningService.getAnalytics().catch(() => null),
          learningService.getAssessmentHistory().catch(() => ({ attempts: [] })),
          learningService.getCodingHistory().catch(() => ({ submissions: [] })),
          learningService.getAdaptiveScore().catch(() => null),
          learningService.getConceptBreakdown().catch(() => null),
          learningService.getStudentAIEvaluations().catch(() => []),
        ]);

        setLearningPath(path);
        setMasteryData(mastery);
        setAnalyticsData(analytics);
        setQuizHistory(quizzes?.attempts || []);
        setCodingHistory(coding?.submissions || []);
        setAdaptiveScoreData(score);
        setConceptBreakdownData(breakdown);
        setAiEvaluations(evals || []);

        if (breakdown?.courses?.length > 0) {
          setSelectedSubjectId(breakdown.courses[0].id);
        }
      } catch (err) {
        console.error('Failed to load comprehensive student dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadAllDashboardData();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '80px', textAlign: 'center', color: '#64748b' }}>
        <Sparkles size={36} color="#4f46e5" style={{ animation: 'spin 2s linear infinite', marginBottom: '14px' }} />
        <div style={{ fontSize: '18px', fontWeight: 700, color: '#1e293b' }}>
          Loading Your Adaptive Learning Profile...
        </div>
        <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '6px' }}>
          Evaluating Bayesian knowledge tracing and personalized prerequisite path
        </p>
      </div>
    );
  }

  // Derived counts
  const concepts = masteryData?.concepts || [];
  const strongConcepts = concepts.filter((c) => c.status === 'STRONG');
  const developingConcepts = concepts.filter((c) => c.status === 'DEVELOPING');
  const weakConcepts = concepts.filter((c) => c.status === 'WEAK');
  const lockedConcepts = concepts.filter((c) => c.status === 'LOCKED');

  // Chart data formatting
  const conceptBarData = concepts.map((c) => ({
    name: c.concept_name,
    mastery: c.mastery_score,
    status: c.status,
  }));

  const progressionLineData =
    analyticsData?.mastery_progression?.map((p, idx) => ({
      index: `#${idx + 1}`,
      mastery: p.mastery,
      reason: p.reason,
      time: new Date(p.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    })) || [];

  // Filtered Quiz History
  const filteredQuizzes = quizHistory.filter((q) => {
    const matchesSearch =
      q.question_text.toLowerCase().includes(quizSearch.toLowerCase()) ||
      q.concept_name.toLowerCase().includes(quizSearch.toLowerCase());
    const matchesFilter =
      quizFilter === 'ALL' ||
      (quizFilter === 'CORRECT' && q.is_correct) ||
      (quizFilter === 'INCORRECT' && !q.is_correct);
    return matchesSearch && matchesFilter;
  });

  // Filtered Coding History
  const filteredCoding = codingHistory.filter((c) =>
    c.problem_title.toLowerCase().includes(codingSearch.toLowerCase()) ||
    c.language.toLowerCase().includes(codingSearch.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1180px', margin: '0 auto' }}>
      {/* Top Banner: Adaptive Next Topic */}
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
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Sparkles size={18} color="#fde047" />
            <span style={{ fontSize: '11px', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Adaptive Recommendation · Weakest Eligible Prerequisite
            </span>
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 800, margin: '0 0 8px 0', letterSpacing: '-0.01em' }}>
            Current Target: {learningPath?.current_concept || 'Object Oriented Programming'}
          </h2>
          <p style={{ margin: 0, fontSize: '14px', color: '#e0e7ff', maxWidth: '680px', lineHeight: '1.5' }}>
            {learningPath?.reason ||
              'Based on your prerequisite competency, the adaptive engine identified this topic as your optimal learning target.'}
          </p>
          {learningPath?.recommended_action && (
            <div style={{ marginTop: '10px', fontSize: '13px', color: '#fef08a', fontWeight: 600 }}>
              💡 Recommended Next: {learningPath.recommended_action}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', alignItems: 'flex-end' }}>
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
            Practice Adaptive Question <ArrowRight size={16} />
          </button>
          <button
            onClick={() => navigate('/student/assessment')}
            style={{
              padding: '8px 18px',
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
              color: '#ffffff',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '8px',
              fontWeight: 700,
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Code2 size={15} /> Open Coding Sandbox
          </button>
        </div>
      </div>

      {/* Top Level Metric Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '14px' }}>
        <div style={{ backgroundColor: '#ffffff', padding: '18px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
            Overall Mastery
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#4f46e5', margin: '4px 0' }}>
            {masteryData?.overall_mastery || 0}%
          </div>
          <div style={{ fontSize: '12px', color: '#10b981', fontWeight: 600 }}>Bayesian Knowledge Tracing</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '18px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
            Strong (≥75%)
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#16a34a', margin: '4px 0' }}>
            {strongConcepts.length}
          </div>
          <div style={{ fontSize: '12px', color: '#64748b' }}>Mastered Concepts</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '18px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
            Developing (50-74%)
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#2563eb', margin: '4px 0' }}>
            {developingConcepts.length}
          </div>
          <div style={{ fontSize: '12px', color: '#64748b' }}>In-Progress Concepts</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '18px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
            Weak (&lt;50%)
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#ea580c', margin: '4px 0' }}>
            {weakConcepts.length}
          </div>
          <div style={{ fontSize: '12px', color: '#64748b' }}>Needs Targeted Practice</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '18px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
            Locked Concepts
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#64748b', margin: '4px 0' }}>
            {lockedConcepts.length}
          </div>
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>Prereqs Incomplete (&lt;65%)</div>
        </div>
      </div>

      {/* Navigation Tab Bar */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          borderBottom: '2px solid #e2e8f0',
          paddingBottom: '2px',
        }}
      >
        <button
          onClick={() => setActiveTab('overview')}
          style={{
            padding: '10px 18px',
            borderRadius: '8px 8px 0 0',
            border: 'none',
            backgroundColor: activeTab === 'overview' ? '#ffffff' : 'transparent',
            color: activeTab === 'overview' ? '#4f46e5' : '#64748b',
            fontWeight: 800,
            fontSize: '14px',
            cursor: 'pointer',
            borderBottom: activeTab === 'overview' ? '3px solid #4f46e5' : '3px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <Layers size={16} /> Overview & Adaptive Path
        </button>

        <button
          onClick={() => setActiveTab('curriculum')}
          style={{
            padding: '10px 18px',
            borderRadius: '8px 8px 0 0',
            border: 'none',
            backgroundColor: activeTab === 'curriculum' ? '#ffffff' : 'transparent',
            color: activeTab === 'curriculum' ? '#4f46e5' : '#64748b',
            fontWeight: 800,
            fontSize: '14px',
            cursor: 'pointer',
            borderBottom: activeTab === 'curriculum' ? '3px solid #4f46e5' : '3px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <BookOpen size={16} /> Syllabus & Concepts (Subject → Topic → Concept)
        </button>

        <button
          onClick={() => setActiveTab('analytics')}
          style={{
            padding: '10px 18px',
            borderRadius: '8px 8px 0 0',
            border: 'none',
            backgroundColor: activeTab === 'analytics' ? '#ffffff' : 'transparent',
            color: activeTab === 'analytics' ? '#4f46e5' : '#64748b',
            fontWeight: 800,
            fontSize: '14px',
            cursor: 'pointer',
            borderBottom: activeTab === 'analytics' ? '3px solid #4f46e5' : '3px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <BarChart3 size={16} /> Mastery Analytics Charts
        </button>

        <button
          onClick={() => setActiveTab('quizzes')}
          style={{
            padding: '10px 18px',
            borderRadius: '8px 8px 0 0',
            border: 'none',
            backgroundColor: activeTab === 'quizzes' ? '#ffffff' : 'transparent',
            color: activeTab === 'quizzes' ? '#4f46e5' : '#64748b',
            fontWeight: 800,
            fontSize: '14px',
            cursor: 'pointer',
            borderBottom: activeTab === 'quizzes' ? '3px solid #4f46e5' : '3px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <FileText size={16} /> Quiz Assessment History ({quizHistory.length})
        </button>

        <button
          onClick={() => setActiveTab('coding')}
          style={{
            padding: '10px 18px',
            borderRadius: '8px 8px 0 0',
            border: 'none',
            backgroundColor: activeTab === 'coding' ? '#ffffff' : 'transparent',
            color: activeTab === 'coding' ? '#4f46e5' : '#64748b',
            fontWeight: 800,
            fontSize: '14px',
            cursor: 'pointer',
            borderBottom: activeTab === 'coding' ? '3px solid #4f46e5' : '3px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <Code2 size={16} /> Coding Assessment & Viva Results ({codingHistory.length})
        </button>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: OVERVIEW & PERSONALIZED ADAPTIVE LEARNING PATH */}
      {/* ========================================================================= */}
      {activeTab === 'overview' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Requirement 13: Personalized Adaptive Learning Score Card */}
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              border: '1px solid #e2e8f0',
              padding: '24px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Sparkles size={18} color="#4f46e5" />
                  <span style={{ fontSize: '11px', fontWeight: 800, color: '#4f46e5', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Personalized Adaptive Assessment Engine
                  </span>
                </div>
                <h3 style={{ fontSize: '20px', fontWeight: 800, color: '#0f172a', margin: '4px 0 0 0' }}>
                  Your Adaptive Learning Competency Profile
                </h3>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  style={{
                    display: 'inline-block',
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: '#10b981',
                  }}
                />
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#059669' }}>
                  Live BKT Calibration
                </span>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr 1fr', gap: '20px' }}>
              {/* Overall Score Dial */}
              <div
                style={{
                  backgroundColor: '#f8fafc',
                  borderRadius: '12px',
                  border: '1px solid #e2e8f0',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                  textAlign: 'center',
                }}
              >
                <div style={{ fontSize: '11px', fontWeight: 800, color: '#64748b', textTransform: 'uppercase', marginBottom: '4px' }}>
                  Adaptive Learning Score
                </div>
                <div
                  style={{
                    fontSize: '44px',
                    fontWeight: 900,
                    color:
                      (adaptiveScoreData?.adaptive_learning_score || masteryData?.overall_mastery || 0) >= 75
                        ? '#16a34a'
                        : (adaptiveScoreData?.adaptive_learning_score || masteryData?.overall_mastery || 0) >= 50
                        ? '#2563eb'
                        : '#ea580c',
                    lineHeight: '1',
                    margin: '8px 0',
                  }}
                >
                  {(adaptiveScoreData?.adaptive_learning_score || masteryData?.overall_mastery || 0).toFixed(0)}%
                </div>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '12px' }}>
                  {adaptiveScoreData?.mastered_concepts || strongConcepts.length} of {adaptiveScoreData?.total_concepts || concepts.length} Concepts Mastered
                </div>
                <button
                  onClick={() => navigate('/student/learning')}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#4f46e5',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '12px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                  }}
                >
                  Practice Next Question <ArrowRight size={14} />
                </button>
              </div>

              {/* Topic Mastery Breakdown */}
              <div
                style={{
                  backgroundColor: '#ffffff',
                  borderRadius: '12px',
                  border: '1px solid #e2e8f0',
                  padding: '16px 20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                  justifyContent: 'center',
                }}
              >
                <div style={{ fontSize: '12px', fontWeight: 800, color: '#334155', textTransform: 'uppercase' }}>
                  Topic Mastery Breakdown
                </div>
                {adaptiveScoreData?.topic_mastery && adaptiveScoreData.topic_mastery.length > 0 ? (
                  adaptiveScoreData.topic_mastery.slice(0, 4).map((tm) => (
                    <div key={tm.topic_id}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 700, marginBottom: '3px' }}>
                        <span style={{ color: '#1e293b' }}>{tm.topic_name}</span>
                        <span style={{ color: tm.mastery >= 75 ? '#16a34a' : tm.mastery >= 50 ? '#2563eb' : '#ea580c' }}>
                          {tm.mastery.toFixed(0)}%
                        </span>
                      </div>
                      <div style={{ height: '6px', backgroundColor: '#f1f5f9', borderRadius: '3px', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${tm.mastery}%`,
                            height: '100%',
                            backgroundColor: tm.mastery >= 75 ? '#16a34a' : tm.mastery >= 50 ? '#2563eb' : '#ea580c',
                          }}
                        />
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: '12px', color: '#94a3b8' }}>Complete practice questions to calibrate topic mastery.</div>
                )}
              </div>

              {/* Weak Concepts Priority Reinforcement */}
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
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <AlertTriangle size={15} color="#d97706" />
                  <span style={{ fontSize: '12px', fontWeight: 800, color: '#92400e', textTransform: 'uppercase' }}>
                    Targeted Weak Concepts
                  </span>
                </div>
                {adaptiveScoreData?.weak_concepts && adaptiveScoreData.weak_concepts.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '2px' }}>
                    {adaptiveScoreData.weak_concepts.slice(0, 2).map((wc) => (
                      <div
                        key={wc.id}
                        style={{
                          backgroundColor: '#ffffff',
                          borderRadius: '8px',
                          padding: '10px 12px',
                          border: '1px solid #fef3c7',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <div>
                          <div style={{ fontWeight: 800, fontSize: '13px', color: '#9a3412' }}>{wc.name}</div>
                          <div style={{ fontSize: '11px', color: '#78350f' }}>
                            Mastery: {(wc.mastery_score ?? wc.mastery ?? 0).toFixed(0)}% · {wc.topic_name || wc.topic || 'Data Structures'}
                          </div>
                        </div>
                        <button
                          onClick={() => navigate(`/student/learning?concept_id=${wc.id}`)}
                          style={{
                            padding: '4px 10px',
                            backgroundColor: '#ea580c',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: '6px',
                            fontSize: '11px',
                            fontWeight: 700,
                            cursor: 'pointer',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          Reinforce
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: '12px', color: '#166534', backgroundColor: '#f0fdf4', padding: '12px', borderRadius: '8px', marginTop: '6px' }}>
                    ✓ No weak concepts detected! Foundational prerequisites exceed passing thresholds.
                  </div>
                )}
              </div>
            </div>
          </div>
          {/* Personalized Learning Path Visualizer */}
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '14px',
              border: '1px solid #e2e8f0',
              padding: '24px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                  Your Personalized Learning Path
                </h3>
                <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#64748b' }}>
                  Dynamically sequenced by Bayesian Knowledge Tracing. Prerequisite mastery unlock threshold: 65%.
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
                <GitFork size={15} /> Visual DAG Graph →
              </button>
            </div>

            {/* Path Stepper Flow */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                overflowX: 'auto',
                padding: '12px 4px 16px 4px',
              }}
            >
              {learningPath?.path?.map((step, idx) => {
                const stepName = step.concept_name || step.name;
                const isTarget = step.is_target || (learningPath?.current_concept && stepName === learningPath.current_concept);
                const isCompleted = step.status === 'COMPLETED' || step.status === 'MASTERED';
                const isLocked = step.status === 'LOCKED' || !step.eligible;
                const isEligible = (step.status === 'ELIGIBLE' || step.eligible) && !isTarget;

                let icon = <Check size={14} color="#ffffff" />;
                let bgColor = '#10b981';
                let borderColor = '#059669';
                let textColor = '#10b981';

                if (isTarget) {
                  icon = <Target size={14} color="#ffffff" />;
                  bgColor = '#4f46e5';
                  borderColor = '#3730a3';
                  textColor = '#4f46e5';
                } else if (isLocked) {
                  icon = <Lock size={12} color="#94a3b8" />;
                  bgColor = '#f1f5f9';
                  borderColor = '#cbd5e1';
                  textColor = '#94a3b8';
                } else if (isEligible) {
                  icon = <Clock size={12} color="#2563eb" />;
                  bgColor = '#eff6ff';
                  borderColor = '#93c5fd';
                  textColor = '#2563eb';
                }

                return (
                  <React.Fragment key={step.concept_id || step.id || idx}>
                    <div
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        minWidth: '130px',
                        padding: '12px 10px',
                        borderRadius: '10px',
                        border: isTarget ? '2px solid #4f46e5' : '1px solid #e2e8f0',
                        backgroundColor: isTarget ? '#eef2ff' : '#f8fafc',
                        position: 'relative',
                      }}
                    >
                      <div
                        style={{
                          width: '28px',
                          height: '28px',
                          borderRadius: '50%',
                          backgroundColor: bgColor,
                          border: `1.5px solid ${borderColor}`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          marginBottom: '8px',
                        }}
                      >
                        {icon}
                      </div>
                      <div
                        style={{
                          fontSize: '12px',
                          fontWeight: 800,
                          color: isTarget ? '#3730a3' : '#1e293b',
                          textAlign: 'center',
                        }}
                      >
                        {stepName}
                      </div>
                      <div
                        style={{
                          fontSize: '11px',
                          fontWeight: 700,
                          color: textColor,
                          marginTop: '4px',
                        }}
                      >
                        {(step.mastery || 0).toFixed(0)}% · {step.status}
                      </div>
                      {isTarget && (
                        <div
                          style={{
                            marginTop: '6px',
                            backgroundColor: '#4f46e5',
                            color: '#ffffff',
                            fontSize: '9px',
                            fontWeight: 800,
                            padding: '2px 6px',
                            borderRadius: '4px',
                            textTransform: 'uppercase',
                          }}
                        >
                          Target
                        </div>
                      )}
                    </div>
                    {idx < learningPath.path.length - 1 && (
                      <div style={{ color: '#cbd5e1', fontWeight: 800 }}>→</div>
                    )}
                  </React.Fragment>
                );
              })}
            </div>

            {/* Target Concept Detailed Rationale Card */}
            {learningPath && (
              <div
                style={{
                  marginTop: '16px',
                  backgroundColor: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '10px',
                  padding: '16px',
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: '12px',
                }}
              >
                <div>
                  <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                    Target Concept
                  </div>
                  <div style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a', marginTop: '2px' }}>
                    {learningPath.current_concept}
                  </div>
                  <div style={{ fontSize: '12px', color: '#4f46e5', fontWeight: 600 }}>
                    Mastery: {learningPath.current_mastery}%
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                    Prerequisites Status
                  </div>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#16a34a', marginTop: '4px' }}>
                    ✓ All Satisfied (≥65%)
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                    Selection Rationale
                  </div>
                  <div style={{ fontSize: '12px', color: '#334155', marginTop: '4px', lineHeight: '1.4' }}>
                    Weakest eligible concept in DAG with completed prerequisites.
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                    Next in Syllabus
                  </div>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', marginTop: '4px' }}>
                    {learningPath.next_expected_concept || 'Inheritance'}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Concept Mastery Breakdown Grid */}
          <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '24px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: '0 0 16px 0' }}>
              Concept-by-Concept Competency Breakdown
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '14px' }}>
              {concepts.map((c) => {
                const isStrong = c.status === 'STRONG';
                const isWeak = c.status === 'WEAK';
                const isLocked = c.status === 'LOCKED';
                const isTarget = learningPath?.current_concept === c.concept_name;

                return (
                  <div
                    key={c.concept_id}
                    style={{
                      padding: '16px',
                      borderRadius: '10px',
                      border: isTarget
                        ? '2px solid #4f46e5'
                        : `1.5px solid ${isStrong ? '#d1fae5' : isWeak ? '#fed7aa' : isLocked ? '#e2e8f0' : '#dbeafe'}`,
                      backgroundColor: isTarget
                        ? '#eef2ff'
                        : isStrong
                        ? '#f0fdf4'
                        : isWeak
                        ? '#fffbeb'
                        : isLocked
                        ? '#f8fafc'
                        : '#eff6ff',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ fontWeight: 800, fontSize: '14px', color: '#0f172a' }}>{c.concept_name}</span>
                        {isTarget && (
                          <span
                            style={{
                              fontSize: '10px',
                              fontWeight: 800,
                              backgroundColor: '#4f46e5',
                              color: '#ffffff',
                              padding: '1px 6px',
                              borderRadius: '4px',
                            }}
                          >
                            TARGET
                          </span>
                        )}
                      </div>
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
                        {(c.mastery_score ?? c.mastery ?? 0).toFixed(0)}%
                      </span>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#64748b', marginTop: '8px' }}>
                      <span>{c.attempts} attempts · {c.correct_attempts} correct</span>
                      <span>{c.accuracy}% accuracy</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB: SYLLABUS & CONCEPT HIERARCHY (SUBJECT → TOPIC → CONCEPT) */}
      {/* ========================================================================= */}
      {activeTab === 'curriculum' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Subject / Course Selector Header */}
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              border: '1px solid #e2e8f0',
              padding: '24px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <BookOpen size={18} color="#4f46e5" />
                <span style={{ fontSize: '11px', fontWeight: 800, color: '#4f46e5', textTransform: 'uppercase' }}>
                  Curriculum Architecture · Subject → Topic → Concept
                </span>
              </div>
              <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#0f172a', margin: '0 0 4px 0' }}>
                Academic Syllabus & Adaptive Concept Mastery
              </h2>
              <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>
                Explore granular sub-concepts, inspect canonical code snippets, and launch topic-targeted adaptive practice.
              </p>
            </div>

            {/* Subject Selector Buttons */}
            <div style={{ display: 'flex', gap: '8px' }}>
              {conceptBreakdownData?.courses?.map((course) => {
                const isSelected = (selectedSubjectId || conceptBreakdownData.courses[0]?.id) === course.id;
                return (
                  <button
                    key={course.id}
                    onClick={() => {
                      setSelectedSubjectId(course.id);
                      setSelectedTopicId('ALL');
                    }}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '8px',
                      border: isSelected ? '2px solid #4f46e5' : '1px solid #cbd5e1',
                      backgroundColor: isSelected ? '#eef2ff' : '#ffffff',
                      color: isSelected ? '#4338ca' : '#475569',
                      fontWeight: 800,
                      fontSize: '13px',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {course.name || course.title} {course.code ? `(${course.code})` : ''}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Course View */}
          {(() => {
            const activeCourse =
              conceptBreakdownData?.courses?.find(
                (c) => c.id === (selectedSubjectId || conceptBreakdownData?.courses[0]?.id)
              ) || conceptBreakdownData?.courses?.[0];

            if (!activeCourse) {
              return (
                <div style={{ backgroundColor: '#ffffff', padding: '40px', textAlign: 'center', borderRadius: '12px' }}>
                  No syllabus curriculum configured.
                </div>
              );
            }

            // Topic Filter Chips
            const filteredModules =
              selectedTopicId === 'ALL'
                ? activeCourse.modules
                : activeCourse.modules.filter((m) => m.id === selectedTopicId);

            return (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {/* Topic Filter Pills */}
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                  <span style={{ fontSize: '12px', fontWeight: 700, color: '#64748b', marginRight: '4px' }}>
                    Topics:
                  </span>
                  <button
                    onClick={() => setSelectedTopicId('ALL')}
                    style={{
                      padding: '6px 14px',
                      borderRadius: '20px',
                      border: selectedTopicId === 'ALL' ? '2px solid #4f46e5' : '1px solid #cbd5e1',
                      backgroundColor: selectedTopicId === 'ALL' ? '#4f46e5' : '#ffffff',
                      color: selectedTopicId === 'ALL' ? '#ffffff' : '#475569',
                      fontWeight: 700,
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    All Topics ({activeCourse.modules?.length || 0})
                  </button>
                  {activeCourse.modules?.map((m) => {
                    const isSelected = selectedTopicId === m.id;
                    return (
                      <button
                        key={m.id}
                        onClick={() => setSelectedTopicId(m.id)}
                        style={{
                          padding: '6px 14px',
                          borderRadius: '20px',
                          border: isSelected ? '2px solid #4f46e5' : '1px solid #cbd5e1',
                          backgroundColor: isSelected ? '#4f46e5' : '#ffffff',
                          color: isSelected ? '#ffffff' : '#475569',
                          fontWeight: 700,
                          fontSize: '12px',
                          cursor: 'pointer',
                        }}
                      >
                        {m.name} ({m.concepts?.length || 0})
                      </button>
                    );
                  })}
                </div>

                {/* Modules & Concept Cards */}
                {filteredModules?.map((mod) => {
                  const moduleConcepts = mod.concepts || [];
                  const avgMastery =
                    moduleConcepts.length > 0
                      ? Math.round(
                          moduleConcepts.reduce((acc, c) => acc + (c.mastery_score || 0), 0) /
                            moduleConcepts.length
                        )
                      : 0;

                  return (
                    <div
                      key={mod.id}
                      style={{
                        backgroundColor: '#ffffff',
                        borderRadius: '14px',
                        border: '1px solid #e2e8f0',
                        overflow: 'hidden',
                      }}
                    >
                      {/* Topic Header with Topic Practice Button (Requirement 5) */}
                      <div
                        style={{
                          padding: '18px 24px',
                          borderBottom: '1px solid #e2e8f0',
                          backgroundColor: '#f8fafc',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ fontSize: '11px', fontWeight: 800, color: '#4f46e5', textTransform: 'uppercase' }}>
                              Topic #{mod.order || 1}
                            </span>
                            <span
                              style={{
                                fontSize: '11px',
                                fontWeight: 800,
                                padding: '2px 8px',
                                borderRadius: '4px',
                                backgroundColor: avgMastery >= 75 ? '#dcfce7' : avgMastery >= 50 ? '#dbeafe' : '#ffedd5',
                                color: avgMastery >= 75 ? '#166534' : avgMastery >= 50 ? '#1e40af' : '#9a3412',
                              }}
                            >
                              Avg Mastery: {avgMastery}%
                            </span>
                          </div>
                          <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: '2px 0 0 0' }}>
                            {mod.name}
                          </h3>
                        </div>

                        {/* Topic-Based Practice Launcher (e.g. "Practice Searching") */}
                        <button
                          onClick={() => navigate(`/student/learning?module_id=${mod.id}`)}
                          style={{
                            padding: '8px 18px',
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
                            boxShadow: '0 2px 4px rgba(79, 70, 229, 0.2)',
                          }}
                        >
                          Practice {mod.name} <ArrowRight size={14} />
                        </button>
                      </div>

                      {/* Concepts Grid for this Topic */}
                      <div
                        style={{
                          padding: '20px 24px',
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fill, minmax(310px, 1fr))',
                          gap: '14px',
                        }}
                      >
                        {moduleConcepts.map((concept) => {
                          const status = concept.status || 'NOT_STARTED';
                          let statusBg = '#f1f5f9';
                          let statusColor = '#64748b';
                          let statusLabel = 'Not Started';

                          if (status === 'MASTERED') {
                            statusBg = '#dcfce7';
                            statusColor = '#166534';
                            statusLabel = 'Mastered';
                          } else if (status === 'DEVELOPING') {
                            statusBg = '#dbeafe';
                            statusColor = '#1e40af';
                            statusLabel = 'Developing';
                          } else if (status === 'LEARNING') {
                            statusBg = '#e0e7ff';
                            statusColor = '#4338ca';
                            statusLabel = 'Learning';
                          } else if (status === 'WEAK') {
                            statusBg = '#ffedd5';
                            statusColor = '#9a3412';
                            statusLabel = 'Weak';
                          } else if (status === 'LOCKED') {
                            statusBg = '#f1f5f9';
                            statusColor = '#94a3b8';
                            statusLabel = 'Locked';
                          }

                          return (
                            <div
                              key={concept.id}
                              style={{
                                padding: '16px',
                                borderRadius: '10px',
                                border: '1px solid #e2e8f0',
                                backgroundColor: '#ffffff',
                                display: 'flex',
                                flexDirection: 'column',
                                justifyContent: 'space-between',
                                transition: 'transform 0.15s, box-shadow 0.15s',
                              }}
                            >
                              <div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                  <span
                                    style={{
                                      fontSize: '11px',
                                      fontWeight: 800,
                                      padding: '2px 8px',
                                      borderRadius: '4px',
                                      backgroundColor: statusBg,
                                      color: statusColor,
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: '4px',
                                    }}
                                  >
                                    {status === 'LOCKED' && <Lock size={10} />}
                                    {statusLabel}
                                  </span>

                                  <span
                                    style={{
                                      fontSize: '10px',
                                      fontWeight: 700,
                                      color: '#64748b',
                                      backgroundColor: '#f8fafc',
                                      padding: '2px 6px',
                                      borderRadius: '4px',
                                      border: '1px solid #e2e8f0',
                                    }}
                                  >
                                    {concept.difficulty_level || 'MEDIUM'}
                                  </span>
                                </div>

                                <h4 style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a', margin: '0 0 6px 0' }}>
                                  {concept.name}
                                </h4>

                                <p
                                  style={{
                                    fontSize: '12px',
                                    color: '#64748b',
                                    lineHeight: '1.4',
                                    margin: '0 0 12px 0',
                                    display: '-webkit-box',
                                    WebkitLineClamp: 2,
                                    WebkitBoxOrient: 'vertical',
                                    overflow: 'hidden',
                                  }}
                                >
                                  {concept.description}
                                </p>

                                {/* Mastery Bar */}
                                <div style={{ marginBottom: '12px' }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 700, marginBottom: '3px' }}>
                                    <span style={{ color: '#64748b' }}>Mastery</span>
                                    <span style={{ color: statusColor }}>{(concept.mastery_score || 0).toFixed(0)}%</span>
                                  </div>
                                  <div style={{ height: '5px', backgroundColor: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                                    <div
                                      style={{
                                        width: `${concept.mastery_score || 0}%`,
                                        height: '100%',
                                        backgroundColor:
                                          (concept.mastery_score || 0) >= 75
                                            ? '#16a34a'
                                            : (concept.mastery_score || 0) >= 50
                                            ? '#2563eb'
                                            : '#ea580c',
                                      }}
                                    />
                                  </div>
                                </div>
                              </div>

                              {/* Card Action Buttons (Requirement 4 & 5) */}
                              <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
                                <button
                                  onClick={() => setSelectedConceptModal(concept)}
                                  style={{
                                    flex: 1,
                                    padding: '6px 10px',
                                    backgroundColor: '#f8fafc',
                                    color: '#334155',
                                    border: '1px solid #cbd5e1',
                                    borderRadius: '6px',
                                    fontSize: '12px',
                                    fontWeight: 700,
                                    cursor: 'pointer',
                                    textAlign: 'center',
                                  }}
                                >
                                  Inspect & Code
                                </button>
                                <button
                                  onClick={() => navigate(`/student/learning?concept_id=${concept.id}`)}
                                  style={{
                                    flex: 1,
                                    padding: '6px 10px',
                                    backgroundColor: '#4f46e5',
                                    color: '#ffffff',
                                    border: 'none',
                                    borderRadius: '6px',
                                    fontSize: '12px',
                                    fontWeight: 700,
                                    cursor: 'pointer',
                                    textAlign: 'center',
                                  }}
                                >
                                  Practice
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            );
          })()}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: MASTERY ANALYTICS CHARTS */}
      {/* ========================================================================= */}
      {activeTab === 'analytics' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Charts Row: Line & Bar */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {/* Historical Knowledge Tracing Line Chart */}
            <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                    Mastery Progression Over Time
                  </h3>
                  <p style={{ margin: '2px 0 0 0', fontSize: '12px', color: '#64748b' }}>
                    Bayesian Knowledge Tracing trajectory from question attempts
                  </p>
                </div>
                <TrendingUp size={18} color="#4f46e5" />
              </div>

              {progressionLineData.length > 0 ? (
                <div style={{ width: '100%', height: '260px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={progressionLineData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="index" stroke="#94a3b8" fontSize={11} />
                      <YAxis stroke="#94a3b8" domain={[0, 100]} fontSize={11} unit="%" />
                      <Tooltip
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const d = payload[0].payload;
                            return (
                              <div style={{ backgroundColor: '#1e293b', color: '#fff', padding: '10px', borderRadius: '8px', fontSize: '12px' }}>
                                <div style={{ fontWeight: 700 }}>Mastery: {d.mastery}%</div>
                                <div style={{ color: '#94a3b8', fontSize: '11px', marginTop: '4px' }}>{d.reason}</div>
                                <div style={{ color: '#64748b', fontSize: '10px' }}>{d.time}</div>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Line type="monotone" dataKey="mastery" stroke="#4f46e5" strokeWidth={3} dot={{ r: 4, fill: '#4f46e5' }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div style={{ padding: '60px', textAlign: 'center', color: '#94a3b8', fontSize: '13px' }}>
                  No historical progression data recorded yet. Complete practice questions to track trajectory.
                </div>
              )}
            </div>

            {/* Mastery by Concept Bar Chart with 65% Benchmark */}
            <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                    Mastery by Concept vs Passing Threshold (65%)
                  </h3>
                  <p style={{ margin: '2px 0 0 0', fontSize: '12px', color: '#64748b' }}>
                    Concepts must achieve 65% mastery to unlock dependent topics
                  </p>
                </div>
                <BarChart3 size={18} color="#2563eb" />
              </div>

              <div style={{ width: '100%', height: '260px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={conceptBarData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis type="number" domain={[0, 100]} stroke="#94a3b8" fontSize={11} unit="%" />
                    <YAxis dataKey="name" type="category" width={110} stroke="#475569" fontSize={11} tick={{ fontWeight: 600 }} />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const d = payload[0].payload;
                          return (
                            <div style={{ backgroundColor: '#1e293b', color: '#fff', padding: '8px 12px', borderRadius: '6px', fontSize: '12px' }}>
                              <div style={{ fontWeight: 800 }}>{d.name}</div>
                              <div style={{ color: d.mastery >= 65 ? '#4ade80' : '#f87171' }}>
                                Mastery: {d.mastery}% ({d.status})
                              </div>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <ReferenceLine x={65} stroke="#ea580c" strokeDasharray="3 3" label={{ value: '65% Prereq Threshold', fill: '#ea580c', fontSize: 10, position: 'top' }} />
                    <Bar dataKey="mastery" radius={[0, 4, 4, 0]}>
                      {conceptBarData.map((entry, index) => {
                        const color =
                          entry.mastery >= 75
                            ? '#16a34a'
                            : entry.mastery >= 65
                            ? '#2563eb'
                            : entry.mastery >= 50
                            ? '#3b82f6'
                            : '#ea580c';
                        return <Cell key={`cell-${index}`} fill={color} />;
                      })}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Difficulty Performance & Concept Attempts Breakdown */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {/* Question Difficulty Breakdown */}
            <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '24px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#0f172a', margin: '0 0 16px 0' }}>
                Question Difficulty Performance
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {['EASY', 'MEDIUM', 'HARD'].map((diff) => {
                  const stat = analyticsData?.difficulty_performance?.[diff] || { total: 0, correct: 0, accuracy: 0.0 };
                  const color = diff === 'EASY' ? '#16a34a' : diff === 'MEDIUM' ? '#2563eb' : '#dc2626';

                  return (
                    <div key={diff} style={{ padding: '12px 14px', borderRadius: '8px', border: '1px solid #f1f5f9', backgroundColor: '#f8fafc' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                        <span style={{ fontWeight: 800, fontSize: '13px', color: color }}>
                          {diff} Questions
                        </span>
                        <span style={{ fontWeight: 700, fontSize: '12px', color: '#0f172a' }}>
                          {stat.correct} / {stat.total} Correct ({stat.accuracy}%)
                        </span>
                      </div>
                      <div style={{ height: '6px', backgroundColor: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${stat.accuracy}%`, height: '100%', backgroundColor: color }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Personalized Recommendations */}
            <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <Sparkles size={18} color="#4f46e5" />
                <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                  Active Learning Recommendations
                </h3>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {analyticsData?.recommendations && analyticsData.recommendations.length > 0 ? (
                  analyticsData.recommendations.map((rec, i) => (
                    <div
                      key={i}
                      style={{
                        padding: '12px 14px',
                        borderRadius: '8px',
                        border: '1px solid #fef3c7',
                        backgroundColor: '#fffbeb',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 800, fontSize: '13px', color: '#92400e' }}>
                          {rec.concept_name} Focus
                        </div>
                        <div style={{ fontSize: '12px', color: '#78350f', marginTop: '2px' }}>
                          {rec.message}
                        </div>
                      </div>
                      <button
                        onClick={() => navigate('/student/learning')}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: '#f59e0b',
                          color: '#ffffff',
                          border: 'none',
                          borderRadius: '6px',
                          fontSize: '12px',
                          fontWeight: 700,
                          cursor: 'pointer',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        Practice
                      </button>
                    </div>
                  ))
                ) : (
                  <div style={{ padding: '20px', textAlign: 'center', color: '#16a34a', backgroundColor: '#f0fdf4', borderRadius: '8px' }}>
                    <CheckCircle2 size={24} style={{ marginBottom: '6px' }} />
                    <div style={{ fontWeight: 700, fontSize: '13px' }}>All foundational competencies are strong!</div>
                    <div style={{ fontSize: '12px', color: '#166534' }}>You are ready for advanced topics in the syllabus.</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: QUIZ ASSESSMENT HISTORY */}
      {/* ========================================================================= */}
      {activeTab === 'quizzes' && (
        <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                Quiz Assessment Attempts History
              </h3>
              <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#64748b' }}>
                Review past concept question attempts and pedagogical explanations.
              </p>
            </div>

            {/* Filter Bar */}
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <div style={{ position: 'relative' }}>
                <Search size={14} color="#94a3b8" style={{ position: 'absolute', left: '10px', top: '10px' }} />
                <input
                  type="text"
                  placeholder="Search questions or concept..."
                  value={quizSearch}
                  onChange={(e) => setQuizSearch(e.target.value)}
                  style={{
                    padding: '8px 12px 8px 30px',
                    borderRadius: '8px',
                    border: '1px solid #cbd5e1',
                    fontSize: '13px',
                    width: '220px',
                  }}
                />
              </div>

              <select
                value={quizFilter}
                onChange={(e) => setQuizFilter(e.target.value)}
                style={{
                  padding: '8px 12px',
                  borderRadius: '8px',
                  border: '1px solid #cbd5e1',
                  fontSize: '13px',
                  backgroundColor: '#ffffff',
                }}
              >
                <option value="ALL">All Results</option>
                <option value="CORRECT">Correct Only</option>
                <option value="INCORRECT">Incorrect Only</option>
              </select>
            </div>
          </div>

          {filteredQuizzes.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#64748b' }}>
                  <th style={{ padding: '12px' }}>Question / Concept</th>
                  <th style={{ padding: '12px' }}>Your Answer</th>
                  <th style={{ padding: '12px' }}>Correct Answer</th>
                  <th style={{ padding: '12px' }}>Score</th>
                  <th style={{ padding: '12px' }}>Time Taken</th>
                  <th style={{ padding: '12px' }}>Date</th>
                  <th style={{ padding: '12px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredQuizzes.map((q) => (
                  <tr key={q.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '14px', maxWidth: '320px' }}>
                      <div style={{ fontWeight: 700, color: '#0f172a', marginBottom: '2px' }}>
                        {q.question_text}
                      </div>
                      <span
                        style={{
                          fontSize: '11px',
                          fontWeight: 700,
                          backgroundColor: '#e0e7ff',
                          color: '#4338ca',
                          padding: '1px 6px',
                          borderRadius: '4px',
                        }}
                      >
                        {q.concept_name}
                      </span>
                    </td>
                    <td style={{ padding: '14px', color: q.is_correct ? '#166534' : '#991b1b', fontWeight: 600 }}>
                      {q.selected_answer}
                    </td>
                    <td style={{ padding: '14px', color: '#166534', fontWeight: 600 }}>
                      {q.correct_answer}
                    </td>
                    <td style={{ padding: '14px', fontWeight: 700, color: '#0f172a' }}>
                      {q.score}
                    </td>
                    <td style={{ padding: '14px', color: '#64748b' }}>
                      {q.time_taken ? `${q.time_taken.toFixed(1)}s` : 'N/A'}
                    </td>
                    <td style={{ padding: '14px', color: '#64748b', fontSize: '12px' }}>
                      {new Date(q.timestamp).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '14px' }}>
                      <span
                        style={{
                          padding: '3px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: 800,
                          backgroundColor: q.is_correct ? '#dcfce7' : '#fee2e2',
                          color: q.is_correct ? '#166534' : '#991b1b',
                        }}
                      >
                        {q.is_correct ? 'CORRECT' : 'INCORRECT'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: '48px', textAlign: 'center', color: '#94a3b8' }}>
              <HelpCircle size={32} style={{ marginBottom: '8px' }} />
              <div style={{ fontWeight: 700, fontSize: '14px' }}>No quiz assessment attempts found</div>
              <p style={{ fontSize: '12px', marginTop: '4px' }}>
                Try adjusting your search filter or complete practice questions in Adaptive Practice.
              </p>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: CODING ASSESSMENT HISTORY & VIVA VOCE RESULTS */}
      {/* ========================================================================= */}
      {activeTab === 'coding' && (
        <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                Coding Assessment Submissions & "Explain Your Code" Viva
              </h3>
              <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#64748b' }}>
                Isolated sandbox execution results, test cases passed, and AI-driven viva evaluations.
              </p>
            </div>

            <div style={{ position: 'relative' }}>
              <Search size={14} color="#94a3b8" style={{ position: 'absolute', left: '10px', top: '10px' }} />
              <input
                type="text"
                placeholder="Search problem or language..."
                value={codingSearch}
                onChange={(e) => setCodingSearch(e.target.value)}
                style={{
                  padding: '8px 12px 8px 30px',
                  borderRadius: '8px',
                  border: '1px solid #cbd5e1',
                  fontSize: '13px',
                  width: '240px',
                }}
              />
            </div>
          </div>

          {filteredCoding.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#64748b' }}>
                  <th style={{ padding: '12px' }}>Problem Title</th>
                  <th style={{ padding: '12px' }}>Language</th>
                  <th style={{ padding: '12px' }}>Execution Status</th>
                  <th style={{ padding: '12px' }}>Test Score</th>
                  <th style={{ padding: '12px' }}>Understanding Verdict</th>
                  <th style={{ padding: '12px' }}>Viva Score</th>
                  <th style={{ padding: '12px' }}>Date</th>
                  <th style={{ padding: '12px' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredCoding.map((c) => {
                  const matchedEval = aiEvaluations?.find((e) => e.submission_id === c.id);
                  const verdict = c.viva_verdict || matchedEval?.understanding_verdict;
                  const isPoor = verdict?.includes('poor understanding');
                  const isWrong = verdict?.includes('Wrong code');
                  const verdictBg = isPoor ? (isWrong ? '#fee2e2' : '#fef3c7') : '#dcfce7';
                  const verdictColor = isPoor ? (isWrong ? '#991b1b' : '#92400e') : '#166534';

                  return (
                    <tr key={c.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '14px', fontWeight: 700, color: '#0f172a' }}>
                        {c.problem_title}
                      </td>
                      <td style={{ padding: '14px', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
                        {c.language}
                      </td>
                      <td style={{ padding: '14px' }}>
                        <span
                          style={{
                            padding: '3px 8px',
                            borderRadius: '4px',
                            fontSize: '11px',
                            fontWeight: 800,
                            backgroundColor: c.status === 'PASSED' ? '#dcfce7' : '#fee2e2',
                            color: c.status === 'PASSED' ? '#166534' : '#991b1b',
                          }}
                        >
                          {c.status}
                        </span>
                      </td>
                      <td style={{ padding: '14px', fontWeight: 800, color: c.score >= 80 ? '#16a34a' : '#ea580c' }}>
                        {c.score}%
                      </td>
                      <td style={{ padding: '14px' }}>
                        {verdict ? (
                          <span
                            style={{
                              padding: '3px 8px',
                              borderRadius: '4px',
                              fontSize: '11px',
                              fontWeight: 800,
                              backgroundColor: verdictBg,
                              color: verdictColor,
                              display: 'inline-block',
                            }}
                          >
                            {verdict}
                          </span>
                        ) : (
                          <span style={{ color: '#94a3b8', fontSize: '11px' }}>Pending Viva</span>
                        )}
                      </td>
                      <td style={{ padding: '14px' }}>
                        {c.viva_score !== null && c.viva_score !== undefined ? (
                          <span
                            style={{
                              fontWeight: 800,
                              padding: '2px 8px',
                              borderRadius: '4px',
                              backgroundColor: '#e0e7ff',
                              color: '#4338ca',
                              fontSize: '12px',
                            }}
                          >
                            {c.viva_score} / 10
                          </span>
                        ) : (
                          <span style={{ color: '#94a3b8', fontSize: '12px' }}>—</span>
                        )}
                      </td>
                      <td style={{ padding: '14px', color: '#64748b', fontSize: '12px' }}>
                        {new Date(c.timestamp).toLocaleDateString()}
                      </td>
                      <td style={{ padding: '14px' }}>
                        {c.viva_details && c.viva_details.length > 0 ? (
                          <button
                            onClick={() => setSelectedVivaSubmission(c)}
                            style={{
                              padding: '6px 12px',
                              backgroundColor: '#4f46e5',
                              color: '#ffffff',
                              border: 'none',
                              borderRadius: '6px',
                              fontSize: '12px',
                              fontWeight: 700,
                              cursor: 'pointer',
                            }}
                          >
                            View Viva Feedback
                          </button>
                        ) : (
                          <button
                            onClick={() => navigate(`/student/explain/${c.id}`)}
                            style={{
                              padding: '6px 12px',
                              backgroundColor: '#f1f5f9',
                              color: '#334155',
                              border: '1px solid #cbd5e1',
                              borderRadius: '6px',
                              fontSize: '12px',
                              fontWeight: 700,
                              cursor: 'pointer',
                            }}
                          >
                            Take Viva
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <div style={{ padding: '48px', textAlign: 'center', color: '#94a3b8' }}>
              <Code2 size={32} style={{ marginBottom: '8px' }} />
              <div style={{ fontWeight: 700, fontSize: '14px' }}>No coding submissions recorded yet</div>
              <p style={{ fontSize: '12px', marginTop: '4px' }}>
                Open Coding Assessment to write and execute code inside the isolated sandbox.
              </p>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* EXPLAIN YOUR CODE MODAL (SECTION 6) */}
      {/* ========================================================================= */}
      {selectedVivaSubmission && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
            padding: '20px',
          }}
        >
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              maxWidth: '720px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: '28px',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <span style={{ fontSize: '11px', fontWeight: 800, color: '#4f46e5', textTransform: 'uppercase' }}>
                  AI Viva Voce Evaluation
                </span>
                <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#0f172a', margin: '2px 0 0 0' }}>
                  Explain Your Code — {selectedVivaSubmission.problem_title}
                </h2>
              </div>
              <button
                onClick={() => setSelectedVivaSubmission(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#64748b',
                }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Overall Viva Score & Understanding Verdict Banner */}
            {(() => {
              const matchedEval = aiEvaluations?.find((e) => e.submission_id === selectedVivaSubmission.id);
              const verdict = selectedVivaSubmission.viva_verdict || matchedEval?.understanding_verdict;
              const isPoor = verdict?.includes('poor understanding');
              const isWrong = verdict?.includes('Wrong code');
              const verdictBg = isPoor ? (isWrong ? '#fee2e2' : '#fef3c7') : '#dcfce7';
              const verdictColor = isPoor ? (isWrong ? '#991b1b' : '#92400e') : '#166534';

              return (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '20px' }}>
                  <div
                    style={{
                      backgroundColor: '#e0e7ff',
                      borderRadius: '10px',
                      padding: '14px 18px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '11px', fontWeight: 800, color: '#3730a3', textTransform: 'uppercase' }}>
                        Overall Explanation Score
                      </div>
                      <div style={{ fontSize: '24px', fontWeight: 800, color: '#4f46e5', marginTop: '2px' }}>
                        {selectedVivaSubmission.viva_score !== null ? `${selectedVivaSubmission.viva_score} / 10` : 'Evaluated'}
                      </div>
                    </div>
                    <div style={{ fontSize: '12px', color: '#4338ca', maxWidth: '380px', textAlign: 'right' }}>
                      Evaluated against code AST structure, algorithmic complexity, and runtime invariants.
                    </div>
                  </div>

                  {verdict && (
                    <div
                      style={{
                        backgroundColor: verdictBg,
                        border: `1.5px solid ${isPoor ? (isWrong ? '#fecaca' : '#fde68a') : '#bbf7d0'}`,
                        borderRadius: '10px',
                        padding: '14px 18px',
                      }}
                    >
                      <div style={{ fontSize: '11px', fontWeight: 800, color: verdictColor, textTransform: 'uppercase' }}>
                        AI Understanding Verdict
                      </div>
                      <div style={{ fontSize: '16px', fontWeight: 800, color: verdictColor, marginTop: '2px' }}>
                        "{verdict}"
                      </div>
                      <div style={{ display: 'flex', gap: '12px', marginTop: '8px', fontSize: '12px', flexWrap: 'wrap' }}>
                        {matchedEval?.detected_strengths && matchedEval.detected_strengths.length > 0 && (
                          <div style={{ color: '#166534' }}>
                            <strong>Strengths:</strong> {matchedEval.detected_strengths.join(', ')}
                          </div>
                        )}
                        {matchedEval?.detected_weaknesses && matchedEval.detected_weaknesses.length > 0 && (
                          <div style={{ color: '#991b1b' }}>
                            <strong>Weaknesses:</strong> {matchedEval.detected_weaknesses.join(', ')}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })()}

            {/* Questions & Feedback */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {selectedVivaSubmission.viva_details?.map((vd, idx) => (
                <div
                  key={idx}
                  style={{
                    border: '1px solid #e2e8f0',
                    borderRadius: '10px',
                    padding: '16px',
                    backgroundColor: '#f8fafc',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 800, fontSize: '13px', color: '#0f172a' }}>
                      Question {idx + 1}
                    </span>
                    <span
                      style={{
                        fontSize: '11px',
                        fontWeight: 800,
                        backgroundColor: '#dcfce7',
                        color: '#166534',
                        padding: '2px 8px',
                        borderRadius: '4px',
                      }}
                    >
                      Score: {vd.score} / 10
                    </span>
                  </div>

                  <div style={{ fontSize: '13px', color: '#334155', fontWeight: 600, marginBottom: '10px' }}>
                    {vd.question}
                  </div>

                  <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '2px' }}>
                    Your Answer:
                  </div>
                  <div
                    style={{
                      fontSize: '12px',
                      color: '#1e293b',
                      backgroundColor: '#ffffff',
                      padding: '10px 12px',
                      borderRadius: '6px',
                      border: '1px solid #e2e8f0',
                      marginBottom: '10px',
                      fontStyle: 'italic',
                    }}
                  >
                    "{vd.student_answer || 'No answer submitted'}"
                  </div>

                  <div style={{ fontSize: '11px', fontWeight: 700, color: '#4f46e5', textTransform: 'uppercase', marginBottom: '2px' }}>
                    AI Evaluator Feedback:
                  </div>
                  <div style={{ fontSize: '12px', color: '#0f172a', fontWeight: 500 }}>
                    {vd.evaluation}
                  </div>
                </div>
              ))}
            </div>

            <div style={{ marginTop: '24px', textAlign: 'right' }}>
              <button
                onClick={() => setSelectedVivaSubmission(null)}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#4f46e5',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: 700,
                  fontSize: '13px',
                  cursor: 'pointer',
                }}
              >
                Close Feedback
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* CONCEPT BREAKDOWN DETAIL MODAL (REQUIREMENT 4) */}
      {/* ========================================================================= */}
      {selectedConceptModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.65)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 110,
            padding: '20px',
          }}
        >
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              maxWidth: '780px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: '28px',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
              display: 'flex',
              flexDirection: 'column',
              gap: '20px',
            }}
          >
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 800,
                      padding: '2px 8px',
                      borderRadius: '4px',
                      backgroundColor:
                        selectedConceptModal.status === 'MASTERED'
                          ? '#dcfce7'
                          : selectedConceptModal.status === 'DEVELOPING'
                          ? '#dbeafe'
                          : selectedConceptModal.status === 'WEAK'
                          ? '#ffedd5'
                          : '#f1f5f9',
                      color:
                        selectedConceptModal.status === 'MASTERED'
                          ? '#166534'
                          : selectedConceptModal.status === 'DEVELOPING'
                          ? '#1e40af'
                          : selectedConceptModal.status === 'WEAK'
                          ? '#9a3412'
                          : '#64748b',
                    }}
                  >
                    Status: {selectedConceptModal.status || 'NOT_STARTED'}
                  </span>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      color: '#64748b',
                      backgroundColor: '#f8fafc',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      border: '1px solid #e2e8f0',
                    }}
                  >
                    Difficulty: {selectedConceptModal.difficulty_level || 'MEDIUM'}
                  </span>
                </div>
                <h2 style={{ fontSize: '22px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                  {selectedConceptModal.name}
                </h2>
              </div>
              <button
                onClick={() => setSelectedConceptModal(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#64748b',
                  padding: '4px',
                }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Current Mastery Metric Card */}
            <div
              style={{
                backgroundColor: '#f8fafc',
                borderRadius: '12px',
                border: '1px solid #e2e8f0',
                padding: '16px 20px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                  Current Mastery (Bayesian Knowledge Tracing)
                </div>
                <div style={{ fontSize: '24px', fontWeight: 900, color: '#4f46e5', marginTop: '2px' }}>
                  {(selectedConceptModal.mastery_score || 0).toFixed(0)}%
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#334155' }}>
                  {selectedConceptModal.attempts_count || selectedConceptModal.attempts || 0} Total Attempts ·{' '}
                  {selectedConceptModal.correct_count || selectedConceptModal.correct_attempts || 0} Correct
                </div>
                <div style={{ fontSize: '12px', color: '#16a34a', fontWeight: 600, marginTop: '2px' }}>
                  {selectedConceptModal.accuracy || 0}% Accuracy
                </div>
              </div>
            </div>

            {/* Section 1: Conceptual Explanation */}
            <div>
              <div style={{ fontSize: '12px', fontWeight: 800, color: '#475569', textTransform: 'uppercase', marginBottom: '6px' }}>
                📖 Conceptual Explanation & Principles
              </div>
              <div
                style={{
                  fontSize: '14px',
                  color: '#1e293b',
                  lineHeight: '1.6',
                  backgroundColor: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '10px',
                  padding: '16px',
                }}
              >
                {selectedConceptModal.explanation || selectedConceptModal.description}
              </div>
            </div>

            {/* Section 2: Canonical Code Snippet */}
            {selectedConceptModal.code_snippet && (
              <div>
                <div style={{ fontSize: '12px', fontWeight: 800, color: '#475569', textTransform: 'uppercase', marginBottom: '6px' }}>
                  💻 Implementation Code Snippet
                </div>
                <div
                  style={{
                    backgroundColor: '#0f172a',
                    color: '#f8fafc',
                    borderRadius: '10px',
                    padding: '16px',
                    fontFamily: 'Consolas, Monaco, monospace',
                    fontSize: '13px',
                    overflowX: 'auto',
                    lineHeight: '1.5',
                    border: '1px solid #1e293b',
                  }}
                >
                  <pre style={{ margin: 0 }}>{selectedConceptModal.code_snippet}</pre>
                </div>
              </div>
            )}

            {/* Section 3: Practical Examples */}
            {selectedConceptModal.examples && (
              <div>
                <div style={{ fontSize: '12px', fontWeight: 800, color: '#475569', textTransform: 'uppercase', marginBottom: '6px' }}>
                  💡 Practical & Algorithmic Examples
                </div>
                <div
                  style={{
                    backgroundColor: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    borderRadius: '10px',
                    padding: '14px 18px',
                  }}
                >
                  {Array.isArray(selectedConceptModal.examples) ? (
                    <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '13px', color: '#334155', lineHeight: '1.6' }}>
                      {selectedConceptModal.examples.map((ex, i) => (
                        <li key={i}>{typeof ex === 'string' ? ex : JSON.stringify(ex)}</li>
                      ))}
                    </ul>
                  ) : typeof selectedConceptModal.examples === 'object' ? (
                    <div style={{ fontSize: '13px', color: '#334155', lineHeight: '1.6' }}>
                      {Object.entries(selectedConceptModal.examples).map(([k, v]) => (
                        <div key={k} style={{ marginBottom: '6px' }}>
                          <strong>{k.replace(/_/g, ' ')}:</strong> {typeof v === 'string' ? v : JSON.stringify(v)}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: '13px', color: '#334155' }}>
                      {String(selectedConceptModal.examples)}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Section 4: Past Question Attempts */}
            <div>
              <div style={{ fontSize: '12px', fontWeight: 800, color: '#475569', textTransform: 'uppercase', marginBottom: '6px' }}>
                📊 Your Past Assessment Attempts on This Concept
              </div>
              {selectedConceptModal.recent_attempts && selectedConceptModal.recent_attempts.length > 0 ? (
                <div style={{ border: '1px solid #e2e8f0', borderRadius: '10px', overflow: 'hidden' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
                    <thead style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#64748b' }}>
                      <tr>
                        <th style={{ padding: '8px 12px' }}>Question</th>
                        <th style={{ padding: '8px 12px' }}>Selected</th>
                        <th style={{ padding: '8px 12px' }}>Result</th>
                        <th style={{ padding: '8px 12px' }}>Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedConceptModal.recent_attempts.map((att) => (
                        <tr key={att.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                          <td style={{ padding: '8px 12px', color: '#0f172a', fontWeight: 600 }}>{att.question_text}</td>
                          <td style={{ padding: '8px 12px', color: '#475569' }}>{att.selected_answer}</td>
                          <td style={{ padding: '8px 12px' }}>
                            <span
                              style={{
                                padding: '2px 6px',
                                borderRadius: '4px',
                                fontSize: '10px',
                                fontWeight: 800,
                                backgroundColor: att.is_correct ? '#dcfce7' : '#fee2e2',
                                color: att.is_correct ? '#166534' : '#991b1b',
                              }}
                            >
                              {att.is_correct ? 'CORRECT' : 'INCORRECT'}
                            </span>
                          </td>
                          <td style={{ padding: '8px 12px', color: '#64748b' }}>
                            {att.time_taken ? `${att.time_taken.toFixed(1)}s` : 'N/A'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div style={{ padding: '16px', textAlign: 'center', color: '#94a3b8', fontSize: '12px', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
                  No question attempts recorded for this concept yet.
                </div>
              )}
            </div>

            {/* Modal Actions */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
              <button
                onClick={() => setSelectedConceptModal(null)}
                style={{
                  padding: '10px 18px',
                  backgroundColor: '#ffffff',
                  color: '#475569',
                  border: '1px solid #cbd5e1',
                  borderRadius: '8px',
                  fontWeight: 700,
                  fontSize: '13px',
                  cursor: 'pointer',
                }}
              >
                Close
              </button>
              <button
                onClick={() => {
                  const cId = selectedConceptModal.id;
                  setSelectedConceptModal(null);
                  navigate(`/student/learning?concept_id=${cId}`);
                }}
                style={{
                  padding: '10px 20px',
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
                Practice This Concept Now <ArrowRight size={15} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
