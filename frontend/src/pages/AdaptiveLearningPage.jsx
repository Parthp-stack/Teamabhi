import React, { useState, useEffect } from 'react';
import { learningService, aiService } from '../services/learningService';
import {
  Sparkles,
  BookOpen,
  CheckCircle2,
  XCircle,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  HelpCircle,
  X,
  Code,
  AlertCircle,
} from 'lucide-react';

export default function AdaptiveLearningPage() {
  const [activity, setActivity] = useState(null);
  const [selectedAnswer, setSelectedAnswer] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  // AI Explain Concept Modal state
  const [aiModalOpen, setAiModalOpen] = useState(false);
  const [aiExplanation, setAiExplanation] = useState(null);
  const [loadingAi, setLoadingAi] = useState(false);

  const fetchNextQuestion = async () => {
    setLoading(true);
    setResult(null);
    setSelectedAnswer('');
    setAiExplanation(null);

    try {
      const data = await learningService.getNextQuestion();
      setActivity(data);
    } catch (err) {
      console.error('Failed to load next question:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNextQuestion();
  }, []);

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!activity?.question || !selectedAnswer.trim()) return;

    setSubmitting(true);
    try {
      const res = await learningService.submitAttempt(activity.question.id, selectedAnswer);
      setResult(res);
    } catch (err) {
      console.error('Submission failed:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleExplainConceptAI = async () => {
    if (!activity) return;
    setAiModalOpen(true);
    if (aiExplanation) return; // already loaded

    setLoadingAi(true);
    try {
      const data = await aiService.explainConcept(
        activity.concept,
        activity.current_mastery || 0.0,
        activity.question?.difficulty || 'MEDIUM'
      );
      setAiExplanation(data);
    } catch (err) {
      console.error('AI explanation failed:', err);
    } finally {
      setLoadingAi(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: '#64748b' }}>
        <Sparkles size={32} color="#4f46e5" style={{ animation: 'spin 2s linear infinite', marginBottom: '12px' }} />
        <div style={{ fontSize: '16px', fontWeight: 600 }}>Calculating next optimal learning activity...</div>
      </div>
    );
  }

  if (!activity || !activity.question) {
    return (
      <div style={{ padding: '40px', backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
        <CheckCircle2 size={40} color="#10b981" style={{ margin: '0 auto 12px auto' }} />
        <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a' }}>All Active Concepts Practiced!</h3>
        <p style={{ color: '#64748b', fontSize: '14px' }}>
          You have completed all currently eligible prerequisite questions.
        </p>
        <button
          onClick={fetchNextQuestion}
          style={{ padding: '10px 20px', backgroundColor: '#4f46e5', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 700 }}
        >
          Re-evaluate Learning Path
        </button>
      </div>
    );
  }

  const { concept, current_mastery, reason, question } = activity;

  return (
    <div style={{ maxWidth: '820px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Explainable Adaptive Rationale Banner */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          border: '1px solid #e0e7ff',
          borderLeft: '5px solid #4f46e5',
          padding: '16px 20px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={16} color="#4f46e5" />
            <span style={{ fontSize: '11px', fontWeight: 800, color: '#4338ca', textTransform: 'uppercase' }}>
              Adaptive Recommendation Logic
            </span>
          </div>
          <span
            style={{
              fontSize: '12px',
              fontWeight: 800,
              color: '#334155',
              backgroundColor: '#f1f5f9',
              padding: '2px 8px',
              borderRadius: '6px',
            }}
          >
            Current Mastery: {current_mastery?.toFixed(0)}%
          </span>
        </div>
        <div style={{ fontSize: '13px', color: '#1e293b', lineHeight: '1.5' }}>
          {reason}
        </div>
      </div>

      {/* Main Question Card */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '16px',
          border: '1px solid #e2e8f0',
          padding: '32px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
        }}
      >
        {/* Question Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                fontSize: '12px',
                fontWeight: 700,
                color: '#4f46e5',
                backgroundColor: '#eef2ff',
                padding: '4px 10px',
                borderRadius: '6px',
              }}
            >
              {question.concept_name || concept}
            </span>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 800,
                color: question.difficulty === 'EASY' ? '#059669' : question.difficulty === 'MEDIUM' ? '#d97706' : '#dc2626',
                backgroundColor: question.difficulty === 'EASY' ? '#ecfdf5' : question.difficulty === 'MEDIUM' ? '#fffbeb' : '#fef2f2',
                padding: '4px 8px',
                borderRadius: '6px',
                textTransform: 'uppercase',
              }}
            >
              {question.difficulty}
            </span>
          </div>

          {/* AI Explain Concept Button */}
          <button
            type="button"
            onClick={handleExplainConceptAI}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: '#f5f3ff',
              border: '1px solid #ddd6fe',
              color: '#6d28d9',
              borderRadius: '8px',
              padding: '6px 12px',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            <BookOpen size={14} /> Explain Concept (AI)
          </button>
        </div>

        {/* Question Text */}
        <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: '0 0 20px 0', lineHeight: '1.5' }}>
          {question.question_text}
        </h2>

        {/* Options / Form */}
        {!result && (
          <form onSubmit={handleSubmit}>
            {/* MCQ & TRUE_FALSE Options */}
            {(question.question_type === 'MCQ' || question.question_type === 'TRUE_FALSE') && question.options && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '24px' }}>
                {question.options.map((opt, idx) => (
                  <label
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '14px 18px',
                      borderRadius: '10px',
                      border: selectedAnswer === opt ? '2px solid #4f46e5' : '1px solid #cbd5e1',
                      backgroundColor: selectedAnswer === opt ? '#f5f3ff' : '#ffffff',
                      cursor: 'pointer',
                      fontSize: '14px',
                      fontWeight: 500,
                      color: '#1e293b',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <input
                      type="radio"
                      name="quiz-answer"
                      value={opt}
                      checked={selectedAnswer === opt}
                      onChange={() => setSelectedAnswer(opt)}
                      style={{ accentColor: '#4f46e5' }}
                    />
                    <span>{opt}</span>
                  </label>
                ))}
              </div>
            )}

            {/* SHORT_ANSWER Input */}
            {question.question_type === 'SHORT_ANSWER' && (
              <div style={{ marginBottom: '24px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>
                  Your Answer:
                </label>
                <input
                  type="text"
                  value={selectedAnswer}
                  onChange={(e) => setSelectedAnswer(e.target.value)}
                  placeholder="Enter the exact technical term or keyword..."
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    borderRadius: '8px',
                    border: '1px solid #cbd5e1',
                    fontSize: '14px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                type="submit"
                disabled={submitting || !selectedAnswer.trim()}
                style={{
                  padding: '12px 28px',
                  backgroundColor: '#4f46e5',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '10px',
                  fontWeight: 700,
                  fontSize: '14px',
                  cursor: submitting || !selectedAnswer.trim() ? 'not-allowed' : 'pointer',
                  boxShadow: '0 4px 6px rgba(79, 70, 229, 0.25)',
                }}
              >
                {submitting ? 'Checking...' : 'Submit Answer'}
              </button>
            </div>
          </form>
        )}

        {/* Immediate Result Feedback & Mastery Delta */}
        {result && (
          <div style={{ marginTop: '10px' }}>
            <div
              style={{
                padding: '20px',
                borderRadius: '12px',
                backgroundColor: result.is_correct ? '#f0fdf4' : '#fef2f2',
                border: `1.5px solid ${result.is_correct ? '#86efac' : '#fca5a5'}`,
                marginBottom: '20px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                {result.is_correct ? (
                  <CheckCircle2 size={24} color="#16a34a" />
                ) : (
                  <XCircle size={24} color="#dc2626" />
                )}
                <span
                  style={{
                    fontSize: '17px',
                    fontWeight: 800,
                    color: result.is_correct ? '#166534' : '#991b1b',
                  }}
                >
                  {result.is_correct ? 'Correct! Mastery Score Increased.' : 'Incorrect.'}
                </span>
              </div>

              {!result.is_correct && (
                <div style={{ fontSize: '14px', color: '#991b1b', marginBottom: '8px' }}>
                  <strong>Correct Answer:</strong> {result.correct_answer}
                </div>
              )}

              {result.explanation && (
                <p style={{ margin: '8px 0 0 0', fontSize: '13px', color: '#374151', lineHeight: '1.5' }}>
                  {result.explanation}
                </p>
              )}
            </div>

            {/* Mastery Change & Next Concept Recalculation */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '14px 18px',
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '10px',
                marginBottom: '20px',
              }}
            >
              <div>
                <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
                  Bayesian Knowledge Tracing Update:
                </span>
                <div style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a' }}>
                  {result.concept_name}: {result.previous_mastery}% → {result.new_mastery}%
                </div>
                <div style={{ fontSize: '12px', color: '#4f46e5', fontWeight: 700, marginTop: '2px' }}>
                  Next Target Recalculated: {result.next_recommended_concept}
                </div>
              </div>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontWeight: 800,
                  fontSize: '18px',
                  color: result.mastery_change >= 0 ? '#16a34a' : '#dc2626',
                }}
              >
                {result.mastery_change >= 0 ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
                {result.mastery_change >= 0 ? `+${result.mastery_change}%` : `${result.mastery_change}%`}
              </div>
            </div>

            <button
              onClick={fetchNextQuestion}
              style={{
                width: '100%',
                padding: '14px',
                backgroundColor: '#4f46e5',
                color: '#ffffff',
                border: 'none',
                borderRadius: '10px',
                fontWeight: 800,
                fontSize: '15px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                boxShadow: '0 4px 10px rgba(79, 70, 229, 0.25)',
              }}
            >
              Proceed to Next Adaptive Question <ArrowRight size={18} />
            </button>
          </div>
        )}
      </div>

      {/* AI Explain Concept Modal */}
      {aiModalOpen && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px',
          }}
        >
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              maxWidth: '600px',
              width: '100%',
              padding: '28px',
              boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)',
              maxHeight: '90vh',
              overflowY: 'auto',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={18} color="#7c3aed" />
                <h3 style={{ fontSize: '18px', fontWeight: 800, margin: 0, color: '#0f172a' }}>
                  AI Conceptual Tutor · {concept}
                </h3>
              </div>
              <button
                onClick={() => setAiModalOpen(false)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
              >
                <X size={20} />
              </button>
            </div>

            {loadingAi ? (
              <div style={{ padding: '30px', textAlign: 'center', color: '#64748b' }}>
                Synthesizing personalized explanation via OpenRouter Nemotron...
              </div>
            ) : aiExplanation ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontSize: '14px', lineHeight: '1.6' }}>
                <div>
                  <h4 style={{ fontSize: '12px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Concept Explanation
                  </h4>
                  <p style={{ margin: 0, color: '#1e293b' }}>{aiExplanation.explanation}</p>
                </div>

                {aiExplanation.example && (
                  <div>
                    <h4 style={{ fontSize: '12px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '4px' }}>
                      Code Example
                    </h4>
                    <pre
                      style={{
                        backgroundColor: '#0f172a',
                        color: '#f8fafc',
                        padding: '12px',
                        borderRadius: '8px',
                        fontSize: '12px',
                        overflowX: 'auto',
                        margin: 0,
                      }}
                    >
                      {aiExplanation.example}
                    </pre>
                  </div>
                )}

                {aiExplanation.common_mistake && (
                  <div style={{ backgroundColor: '#fff7ed', padding: '12px', borderRadius: '8px', border: '1px solid #ffedd5' }}>
                    <h4 style={{ fontSize: '12px', fontWeight: 700, color: '#c2410c', textTransform: 'uppercase', marginBottom: '4px' }}>
                      Common Pitfall
                    </h4>
                    <p style={{ margin: 0, color: '#9a3412', fontSize: '13px' }}>{aiExplanation.common_mistake}</p>
                  </div>
                )}

                {aiExplanation.practice_question && (
                  <div style={{ backgroundColor: '#f0fdf4', padding: '12px', borderRadius: '8px', border: '1px solid #dcfce7' }}>
                    <h4 style={{ fontSize: '12px', fontWeight: 700, color: '#166534', textTransform: 'uppercase', marginBottom: '4px' }}>
                      Quick Check
                    </h4>
                    <p style={{ margin: 0, color: '#14532d', fontSize: '13px' }}>{aiExplanation.practice_question}</p>
                  </div>
                )}
              </div>
            ) : (
              <div>Failed to generate explanation.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
