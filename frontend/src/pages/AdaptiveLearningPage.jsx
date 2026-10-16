import React, { useState, useEffect } from 'react';
import { learningService } from '../services/learningService';
import {
  Sparkles,
  HelpCircle,
  CheckCircle2,
  XCircle,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  BookOpen,
  Info,
} from 'lucide-react';

export default function AdaptiveLearningPage() {
  const [activity, setActivity] = useState(null);
  const [selectedOption, setSelectedOption] = useState('');
  const [shortAnswerText, setShortAnswerText] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [hint, setHint] = useState('');
  const [loadingHint, setLoadingHint] = useState(false);

  const fetchNextQuestion = async () => {
    setLoading(true);
    setResult(null);
    setSelectedOption('');
    setShortAnswerText('');
    setHint('');

    try {
      const data = await learningService.getNextActivity();
      setActivity(data);
    } catch (err) {
      console.error('Failed to load next activity:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNextQuestion();
  }, []);

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!activity?.question) return;

    const answerToSend = activity.question.type === 'SHORT_ANSWER' ? shortAnswerText : selectedOption;
    if (!answerToSend.trim()) return;

    setSubmitting(true);
    try {
      const res = await learningService.submitAttempt(activity.question.id, answerToSend);
      setResult(res);
    } catch (err) {
      console.error('Submission failed:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRequestHint = async () => {
    if (!activity?.question) return;
    setLoadingHint(true);
    try {
      const currentAns = activity.question.type === 'SHORT_ANSWER' ? shortAnswerText : selectedOption;
      const data = await learningService.getHint(activity.question.id, currentAns);
      setHint(data.hint);
    } catch (err) {
      setHint('Hint: Consider the object lifecycle and state encapsulation principles.');
    } finally {
      setLoadingHint(false);
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
      <div style={{ padding: '40px', backgroundColor: '#ffffff', borderRadius: '12px', textAlign: 'center' }}>
        <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Course Module Complete!</h3>
        <p style={{ color: '#64748b' }}>You have completed all active questions for your eligible concepts.</p>
        <button
          onClick={fetchNextQuestion}
          style={{ padding: '10px 20px', backgroundColor: '#4f46e5', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
        >
          Check for New Targets
        </button>
      </div>
    );
  }

  const { target_concept, rationale, question } = activity;

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Explainable Adaptive Reason Banner */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          border: '1px solid #e0e7ff',
          borderLeft: '5px solid #4f46e5',
          padding: '16px 20px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
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
              fontWeight: 700,
              color: '#374151',
              backgroundColor: '#f1f5f9',
              padding: '2px 8px',
              borderRadius: '6px',
            }}
          >
            Current Mastery: {target_concept.current_mastery?.toFixed(1)}%
          </span>
        </div>
        <div style={{ fontSize: '13px', color: '#1e293b', lineHeight: '1.5' }}>
          {rationale}
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
              {question.concept_name}
            </span>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
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
          <span style={{ fontSize: '12px', color: '#94a3b8' }}>
            Type: {question.type.replace('_', ' ')}
          </span>
        </div>

        {/* Question Title & Description */}
        <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#0f172a', margin: '0 0 10px 0' }}>
          {question.title}
        </h2>
        <p style={{ fontSize: '15px', color: '#334155', lineHeight: '1.6', margin: '0 0 24px 0' }}>
          {question.description}
        </p>

        {/* Options / Input Field */}
        {!result && (
          <form onSubmit={handleSubmit}>
            {question.type === 'MCQ' && question.options && (
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
                      border: selectedOption === opt ? '2px solid #4f46e5' : '1px solid #cbd5e1',
                      backgroundColor: selectedOption === opt ? '#f5f3ff' : '#ffffff',
                      cursor: 'pointer',
                      fontSize: '14px',
                      fontWeight: 500,
                      color: '#1e293b',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <input
                      type="radio"
                      name="mcq-option"
                      value={opt}
                      checked={selectedOption === opt}
                      onChange={() => setSelectedOption(opt)}
                      style={{ accentColor: '#4f46e5' }}
                    />
                    <span>{opt}</span>
                  </label>
                ))}
              </div>
            )}

            {question.type === 'SHORT_ANSWER' && (
              <div style={{ marginBottom: '24px' }}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#475569', marginBottom: '6px' }}>
                  Your Technical Answer:
                </label>
                <input
                  type="text"
                  value={shortAnswerText}
                  onChange={(e) => setShortAnswerText(e.target.value)}
                  placeholder="Type the exact keyword or concept name..."
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

            {/* Actions Bar */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button
                type="button"
                onClick={handleRequestHint}
                disabled={loadingHint}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'none',
                  border: 'none',
                  color: '#6366f1',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                <HelpCircle size={16} />
                {loadingHint ? 'Requesting AI Hint...' : 'Need an AI Hint?'}
              </button>

              <button
                type="submit"
                disabled={submitting || (question.type === 'MCQ' ? !selectedOption : !shortAnswerText.trim())}
                style={{
                  padding: '12px 28px',
                  backgroundColor: '#4f46e5',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '10px',
                  fontWeight: 700,
                  fontSize: '14px',
                  cursor: submitting ? 'not-allowed' : 'pointer',
                  boxShadow: '0 4px 6px rgba(79, 70, 229, 0.25)',
                }}
              >
                {submitting ? 'Evaluating...' : 'Submit Answer'}
              </button>
            </div>
          </form>
        )}

        {/* AI Hint Display */}
        {hint && !result && (
          <div
            style={{
              marginTop: '18px',
              padding: '14px 18px',
              backgroundColor: '#f8fafc',
              border: '1px dashed #cbd5e1',
              borderRadius: '10px',
              fontSize: '13px',
              color: '#334155',
            }}
          >
            <strong>Tutor Hint:</strong> {hint}
          </div>
        )}

        {/* Result & Bayesian Mastery Update Feedback */}
        {result && (
          <div style={{ marginTop: '20px' }}>
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
                  <CheckCircle2 size={22} color="#16a34a" />
                ) : (
                  <XCircle size={22} color="#dc2626" />
                )}
                <span
                  style={{
                    fontSize: '16px',
                    fontWeight: 800,
                    color: result.is_correct ? '#166534' : '#991b1b',
                  }}
                >
                  {result.is_correct ? 'Correct! Knowledge Confirmed.' : 'Incorrect.'}
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

            {/* Mastery Change Badge */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '14px 18px',
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '10px',
                marginBottom: '24px',
              }}
            >
              <div>
                <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>
                  Concept Mastery Updated:
                </span>
                <div style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a' }}>
                  {result.concept_name}: {result.previous_mastery}% → {result.new_mastery}%
                </div>
              </div>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontWeight: 800,
                  fontSize: '16px',
                  color: result.mastery_change >= 0 ? '#16a34a' : '#dc2626',
                }}
              >
                {result.mastery_change >= 0 ? <TrendingUp size={18} /> : <TrendingDown size={18} />}
                {result.mastery_change >= 0 ? `+${result.mastery_change}%` : `${result.mastery_change}%`}
              </div>
            </div>

            {/* Next Adaptive Step Button */}
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
              Continue to Next Adaptive Question <ArrowRight size={18} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
