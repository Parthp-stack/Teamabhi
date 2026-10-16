import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { codingService } from '../services/codingService';
import {
  Sparkles,
  HelpCircle,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ShieldCheck,
  Send,
} from 'lucide-react';

export default function ExplainCodePage() {
  const { submissionId } = useParams();
  const navigate = useNavigate();

  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    async function loadQuestions() {
      try {
        const data = await codingService.getVivaQuestions(submissionId);
        setQuestions(data);
        const initialAnswers = {};
        data.forEach((q) => {
          initialAnswers[q.id] = '';
        });
        setAnswers(initialAnswers);
      } catch (err) {
        console.error('Failed to load explanation questions:', err);
      } finally {
        setLoading(false);
      }
    }
    loadQuestions();
  }, [submissionId]);

  const handleAnswerChange = (questionId, text) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: text,
    }));
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setSubmitting(true);

    try {
      const payload = Object.entries(answers).map(([qid, ans]) => ({
        question_id: parseInt(qid),
        student_answer: ans,
      }));

      const res = await codingService.submitVivaAnswers(payload);
      setResult(res);
    } catch (err) {
      console.error('Failed to evaluate viva answers:', err);
      alert('Failed to evaluate viva. Please check answers and try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: '#64748b' }}>
        <Sparkles size={32} color="#4f46e5" style={{ animation: 'spin 2s linear infinite', marginBottom: '12px' }} />
        <div style={{ fontSize: '16px', fontWeight: 600 }}>
          Analyzing submitted code & synthesizing technical viva questions...
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Banner */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '16px',
          border: '1px solid #e2e8f0',
          padding: '28px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
          <Sparkles size={18} color="#4f46e5" />
          <span style={{ fontSize: '12px', fontWeight: 700, color: '#4338ca', textTransform: 'uppercase' }}>
            Integrity Verification & Viva Voce
          </span>
        </div>
        <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a', margin: '0 0 10px 0' }}>
          Explain Your Code
        </h1>
        <p style={{ fontSize: '14px', color: '#475569', lineHeight: '1.6', margin: 0 }}>
          Our AI engine inspected your submitted implementation and generated 2–3 targeted technical questions.
          Explain the rationale, algorithmic trade-offs, and invariants in your code below.
        </p>
      </div>

      {/* Questions Form or Evaluation Results */}
      {!result ? (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {questions.map((q, idx) => (
            <div
              key={q.id}
              style={{
                backgroundColor: '#ffffff',
                borderRadius: '14px',
                border: '1px solid #e2e8f0',
                padding: '24px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    color: '#6366f1',
                    textTransform: 'uppercase',
                    backgroundColor: '#eef2ff',
                    padding: '2px 8px',
                    borderRadius: '4px',
                  }}
                >
                  Question {idx + 1} · {q.expected_concept}
                </span>
              </div>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#1e293b', margin: '0 0 14px 0' }}>
                {q.question}
              </h3>
              <textarea
                rows={4}
                value={answers[q.id] || ''}
                onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                placeholder="Explain the technical mechanics and reason behind your code choice..."
                required
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  borderRadius: '8px',
                  border: '1px solid #cbd5e1',
                  fontSize: '14px',
                  fontFamily: 'inherit',
                  lineHeight: '1.5',
                  boxSizing: 'border-box',
                }}
              />
            </div>
          ))}

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
            <button
              type="submit"
              disabled={submitting}
              style={{
                padding: '14px 32px',
                backgroundColor: '#4f46e5',
                color: '#ffffff',
                border: 'none',
                borderRadius: '10px',
                fontWeight: 700,
                fontSize: '15px',
                cursor: submitting ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 4px 10px rgba(79, 70, 229, 0.25)',
              }}
            >
              <Send size={16} />
              {submitting ? 'Analyzing Viva Answers...' : 'Submit Explanation'}
            </button>
          </div>
        </form>
      ) : (
        /* Evaluation Feedback Card */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Overall Score Card */}
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              border: '1px solid #e2e8f0',
              padding: '28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <span style={{ fontSize: '12px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
                Code Comprehension Assessment
              </span>
              <div style={{ fontSize: '32px', fontWeight: 800, color: '#0f172a', margin: '4px 0' }}>
                {result.overall_understanding_score} / 10
              </div>
              <p style={{ margin: 0, fontSize: '13px', color: '#475569' }}>
                {result.summary_review}
              </p>
            </div>

            <div
              style={{
                padding: '10px 18px',
                borderRadius: '10px',
                backgroundColor: result.overall_understanding_score >= 7.0 ? '#f0fdf4' : '#fffbeb',
                border: `1px solid ${result.overall_understanding_score >= 7.0 ? '#86efac' : '#fcd34d'}`,
                color: result.overall_understanding_score >= 7.0 ? '#166534' : '#92400e',
                fontWeight: 700,
                fontSize: '14px',
              }}
            >
              {result.overall_understanding_score >= 7.0 ? 'Verified Consistent' : 'Needs Reinforcement'}
            </div>
          </div>

          {/* Requirement 7: 4-Tier Understanding Verdict Banner */}
          {result.understanding_verdict && (
            <div
              style={{
                backgroundColor:
                  result.understanding_verdict.includes('poor understanding')
                    ? result.understanding_verdict.includes('Correct code')
                      ? '#fffbeb'
                      : '#fef2f2'
                    : '#f0fdf4',
                border: `1.5px solid ${
                  result.understanding_verdict.includes('poor understanding')
                    ? result.understanding_verdict.includes('Correct code')
                      ? '#fde68a'
                      : '#fecaca'
                    : '#bbf7d0'
                }`,
                borderRadius: '14px',
                padding: '20px 24px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <Sparkles
                  size={18}
                  color={
                    result.understanding_verdict.includes('poor understanding')
                      ? '#d97706'
                      : '#16a34a'
                  }
                />
                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: 800,
                    textTransform: 'uppercase',
                    color:
                      result.understanding_verdict.includes('poor understanding')
                        ? '#92400e'
                        : '#166534',
                  }}
                >
                  AI Comprehension Verdict (Code + VIVA Evaluation)
                </span>
              </div>
              <div
                style={{
                  fontSize: '20px',
                  fontWeight: 800,
                  color:
                    result.understanding_verdict.includes('poor understanding')
                      ? result.understanding_verdict.includes('Correct code')
                        ? '#b45309'
                        : '#b91c1c'
                      : '#15803d',
                }}
              >
                "{result.understanding_verdict}"
              </div>
              <p
                style={{
                  fontSize: '13px',
                  color: '#475569',
                  marginTop: '6px',
                  marginBottom: 0,
                  lineHeight: '1.5',
                }}
              >
                {result.understanding_verdict === 'Correct code + understood'
                  ? 'Your code passed validation test cases and your viva explanation demonstrated solid grasp of algorithmic logic, time/space complexity, and invariants.'
                  : result.understanding_verdict === 'Correct code + poor understanding'
                  ? 'The submitted code passed unit tests, but the oral explanation revealed gaps in understanding why this algorithm works or how its complexity scales.'
                  : result.understanding_verdict === 'Wrong code + good conceptual understanding'
                  ? 'Your solution had runtime or logical errors on test cases, yet your oral answers showed genuine comprehension of the underlying concepts.'
                  : 'Both the code execution and the oral explanation require conceptual remediation before proceeding.'}
              </p>
            </div>
          )}

          {/* Strengths & Weaknesses Grid */}
          {((result.detected_strengths && result.detected_strengths.length > 0) ||
            (result.detected_weaknesses && result.detected_weaknesses.length > 0)) && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              {/* Strengths */}
              <div
                style={{
                  backgroundColor: '#ffffff',
                  borderRadius: '12px',
                  border: '1px solid #d1fae5',
                  padding: '18px',
                }}
              >
                <div style={{ fontSize: '13px', fontWeight: 800, color: '#065f46', marginBottom: '10px' }}>
                  ✓ Demonstrated Strengths
                </div>
                {result.detected_strengths?.length > 0 ? (
                  <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '13px', color: '#1f2937', lineHeight: '1.6' }}>
                    {result.detected_strengths.map((str, i) => (
                      <li key={i}>{str}</li>
                    ))}
                  </ul>
                ) : (
                  <div style={{ fontSize: '12px', color: '#6b7280' }}>No specific strengths highlighted.</div>
                )}
              </div>

              {/* Weaknesses */}
              <div
                style={{
                  backgroundColor: '#ffffff',
                  borderRadius: '12px',
                  border: '1px solid #fed7aa',
                  padding: '18px',
                }}
              >
                <div style={{ fontSize: '13px', fontWeight: 800, color: '#9a3412', marginBottom: '10px' }}>
                  ⚠ Areas for Reinforcement
                </div>
                {result.detected_weaknesses?.length > 0 ? (
                  <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '13px', color: '#1f2937', lineHeight: '1.6' }}>
                    {result.detected_weaknesses.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                ) : (
                  <div style={{ fontSize: '12px', color: '#15803d' }}>No significant conceptual weaknesses detected!</div>
                )}
              </div>
            </div>
          )}

          {/* Recommendations Banner */}
          {(result.difficulty_recommendation || result.next_question_recommendation) && (
            <div
              style={{
                backgroundColor: '#eff6ff',
                borderRadius: '12px',
                border: '1px solid #bfdbfe',
                padding: '16px 20px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <div style={{ fontSize: '11px', fontWeight: 800, color: '#1e40af', textTransform: 'uppercase' }}>
                  Adaptive Learning Next Step
                </div>
                <div style={{ fontSize: '14px', fontWeight: 700, color: '#1e3a8a', marginTop: '2px' }}>
                  {result.next_question_recommendation || 'Proceed with adaptive practice questions.'}
                </div>
                {result.difficulty_recommendation && (
                  <div style={{ fontSize: '12px', color: '#3b82f6', marginTop: '2px' }}>
                    Recommended Difficulty: <strong>{result.difficulty_recommendation}</strong>
                  </div>
                )}
              </div>

              <button
                onClick={() => navigate('/student/learning')}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#2563eb',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '13px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                }}
              >
                Start Recommended Practice →
              </button>
            </div>
          )}

          {/* Detailed Question Evaluations */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#0f172a', margin: '8px 0 0 0' }}>
              Detailed Question-by-Question Evaluation
            </h3>
            {result.evaluated_answers?.map((ea, idx) => (
              <div
                key={idx}
                style={{
                  backgroundColor: '#ffffff',
                  borderRadius: '12px',
                  border: '1px solid #e2e8f0',
                  padding: '20px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '14px', fontWeight: 700, color: '#1e293b' }}>
                    {ea.question}
                  </span>
                  <span style={{ fontWeight: 800, color: '#4f46e5', fontSize: '14px' }}>
                    Score: {ea.score}/10
                  </span>
                </div>
                <div style={{ backgroundColor: '#f8fafc', padding: '10px 12px', borderRadius: '6px', fontSize: '13px', color: '#334155', marginBottom: '10px' }}>
                  <strong>Your Answer:</strong> {ea.student_answer}
                </div>
                <div style={{ fontSize: '13px', color: '#059669', lineHeight: '1.5' }}>
                  <strong>AI Evaluation:</strong> {ea.evaluation}
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={() => navigate('/student/dashboard')}
            style={{
              padding: '14px',
              backgroundColor: '#4f46e5',
              color: '#ffffff',
              border: 'none',
              borderRadius: '10px',
              fontWeight: 700,
              fontSize: '15px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            Return to Student Dashboard <ArrowRight size={18} />
          </button>
        </div>
      )}
    </div>
  );
}
