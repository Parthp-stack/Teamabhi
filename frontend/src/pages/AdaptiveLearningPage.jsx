import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { assessmentService, integrityService } from '../services/codingService';
import { aiService } from '../services/learningService';
import {
  Sparkles,
  BookOpen,
  CheckCircle2,
  XCircle,
  ChevronLeft,
  ChevronRight,
  Clock,
  AlertTriangle,
  Save,
  Check,
  ShieldAlert,
  RotateCcw,
  Flag,
  HelpCircle,
  X,
  ExternalLink,
} from 'lucide-react';

export default function AdaptiveLearningPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const targetConceptId = searchParams.get('concept_id');
  const targetModuleId = searchParams.get('module_id');
  const targetCourseId = searchParams.get('course_id');
  const queryAssessmentId = searchParams.get('assessment_id');

  // Compute a stable assessment ID
  const assessmentId = queryAssessmentId || (targetCourseId ? `course-quiz-${targetCourseId}` : 'adaptive-assessment-main');

  const [attemptState, setAttemptState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [navigating, setNavigating] = useState(false);
  const [savingAnswer, setSavingAnswer] = useState(false);
  const [selectedAnswer, setSelectedAnswer] = useState('');
  const [saveSuccessMsg, setSaveSuccessMsg] = useState('');

  // Timer & question time tracking
  const [startTime, setStartTime] = useState(Date.now());
  const [secondsElapsed, setSecondsElapsed] = useState(0);

  // Progressive Integrity Warning banner
  const [activeWarning, setActiveWarning] = useState(null);
  const [warningCount, setWarningCount] = useState(0);

  // AI Explain Concept Modal state
  const [aiModalOpen, setAiModalOpen] = useState(false);
  const [aiExplanation, setAiExplanation] = useState(null);
  const [loadingAi, setLoadingAi] = useState(false);

  // AI Wrong Answer Tutor state
  const [aiWrongAnswerFeedback, setAiWrongAnswerFeedback] = useState(null);
  const [loadingWrongAnswerAi, setLoadingWrongAnswerAi] = useState(false);

  // Assessment completed summary state
  const [completedSummary, setCompletedSummary] = useState(null);

  // Refs for tracking
  const attemptIdRef = useRef(null);
  const activeQRef = useRef(null);
  const hasWarnedSplitScreenRef = useRef(false);

  // Timer interval
  useEffect(() => {
    const timer = setInterval(() => {
      setSecondsElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);
    return () => clearInterval(timer);
  }, [startTime]);

  // Load / Start Assessment
  const loadAssessment = useCallback(async (isResume = true) => {
    setLoading(true);
    setSaveSuccessMsg('');
    try {
      const state = await assessmentService.startAttempt(assessmentId, 'ADAPTIVE_QUIZ', {
        course_id: targetCourseId ? parseInt(targetCourseId) : undefined,
        module_id: targetModuleId ? parseInt(targetModuleId) : undefined,
        concept_id: targetConceptId ? parseInt(targetConceptId) : undefined,
        resume: isResume,
      });

      setAttemptState(state);
      attemptIdRef.current = state.attempt_id;

      // Active question based on current_question_index
      const activeQ = state.questions?.find((q) => q.question_number === state.current_question_index) || state.questions?.[0];
      activeQRef.current = activeQ;

      // Restore previously selected answer
      setSelectedAnswer(activeQ?.selected_answer || '');
      setStartTime(Date.now());
      setSecondsElapsed(0);
    } catch (err) {
      console.error('Failed to start/resume assessment:', err);
    } finally {
      setLoading(false);
    }
  }, [assessmentId, targetCourseId, targetModuleId, targetConceptId]);

  useEffect(() => {
    loadAssessment(true);
  }, [loadAssessment]);

  // Active question object helper
  const activeQuestion = attemptState?.questions?.find(
    (q) => q.question_number === (attemptState?.current_question_index || 1)
  ) || attemptState?.questions?.[0];

  useEffect(() => {
    if (activeQuestion) {
      activeQRef.current = activeQuestion;
      setSelectedAnswer(activeQuestion.selected_answer || '');
      setStartTime(Date.now());
      setSecondsElapsed(0);
      setSaveSuccessMsg('');
      setAiWrongAnswerFeedback(null);
    }
  }, [activeQuestion?.question_number, activeQuestion?.id]);

  // Trigger progressive warning
  const triggerWarning = useCallback(
    async (warningType, defaultMsg, evidence = {}) => {
      const attemptId = attemptIdRef.current;
      if (!attemptId) return;

      try {
        const res = await integrityService.recordIntegrityEvent({
          event_type: warningType,
          action: 'Assessment interruption',
          details: defaultMsg,
          risk_level: 'MEDIUM',
          source: 'ADAPTIVE_QUIZ',
          assessment_id: assessmentId,
          attempt_id: attemptId,
          question_number: activeQRef.current?.question_number || 1,
          metadata: evidence,
        });

        const newCount = (warningCount || 0) + 1;
        setWarningCount(newCount);

        let displayMsg = defaultMsg;
        if (newCount === 1) {
          displayMsg = 'Assessment environment interruption detected. Please remain in the assessment window.';
        } else {
          displayMsg = `Notice (Interruption #${newCount}): Continued interruptions or focus changes recorded. Please focus solely on the assessment tab.`;
        }

        setActiveWarning({
          warning_number: newCount,
          warning_type: warningType,
          message: displayMsg,
        });
      } catch (err) {
        console.warn('Could not record warning event:', err);
      }
    },
    [assessmentId, warningCount]
  );

  // Setup Browser / Window Integrity Event Listeners
  useEffect(() => {
    const attemptId = attemptIdRef.current;
    if (!attemptId) return;

    // 1. Tab Switch / Visibility Change
    const handleVisibilityChange = () => {
      const isHidden = document.hidden;
      integrityService.recordIntegrityEvent({
        event_type: 'TAB_SWITCH',
        action: isHidden ? 'Assessment tab hidden' : 'Assessment tab visible',
        details: isHidden ? 'Student switched tabs away from assessment' : 'Student returned to assessment tab',
        risk_level: isHidden ? 'MEDIUM' : 'LOW',
        source: 'BROWSER',
        assessment_id: assessmentId,
        attempt_id: attemptIdRef.current,
        question_number: activeQRef.current?.question_number,
        metadata: { hidden: isHidden, timestamp: new Date().toISOString() },
      });

      if (isHidden) {
        triggerWarning('TAB_SWITCH', 'Assessment tab hidden. Please remain in the assessment window.');
      }
    };

    // 2. Window Blur / Focus
    const handleWindowBlur = () => {
      integrityService.recordIntegrityEvent({
        event_type: 'WINDOW_BLUR',
        action: 'Window lost focus',
        details: 'Assessment window lost focus to another application',
        risk_level: 'MEDIUM',
        source: 'BROWSER',
        assessment_id: assessmentId,
        attempt_id: attemptIdRef.current,
        question_number: activeQRef.current?.question_number,
        metadata: { action: 'window_blur', timestamp: new Date().toISOString() },
      });
      triggerWarning('WINDOW_BLUR', 'Window lost focus. Please keep the assessment window active.');
    };

    const handleWindowFocus = () => {
      integrityService.recordIntegrityEvent({
        event_type: 'WINDOW_FOCUS',
        action: 'Window gained focus',
        details: 'Assessment window regained focus',
        risk_level: 'LOW',
        source: 'BROWSER',
        assessment_id: assessmentId,
        attempt_id: attemptIdRef.current,
        question_number: activeQRef.current?.question_number,
      });
    };

    // 3. Fullscreen Exit
    const handleFullscreenChange = () => {
      if (!document.fullscreenElement) {
        integrityService.recordIntegrityEvent({
          event_type: 'FULLSCREEN_EXIT',
          action: 'Fullscreen exited',
          details: 'Assessment exited fullscreen display mode',
          risk_level: 'MEDIUM',
          source: 'BROWSER',
          assessment_id: assessmentId,
          attempt_id: attemptIdRef.current,
          question_number: activeQRef.current?.question_number,
        });
        triggerWarning('FULLSCREEN_EXIT', 'Fullscreen exited. Please remain in full assessment window.');
      }
    };

    // 4. Resize & Possible Split Screen detection
    let resizeTimer = null;
    const handleResize = () => {
      if (resizeTimer) clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        const screenW = window.screen.availWidth || 1200;
        const currentW = window.innerWidth;
        const ratio = currentW / screenW;
        const evidence = {
          window_width: window.innerWidth,
          window_height: window.innerHeight,
          screen_width: screenW,
          width_ratio: Math.round(ratio * 100) / 100,
        };

        if (ratio < 0.65 && !document.fullscreenElement) {
          integrityService.recordIntegrityEvent({
            event_type: 'POSSIBLE_SPLIT_SCREEN',
            action: 'Resize anomaly',
            details: `Window width ratio ${Math.round(ratio * 100)}% consistent with side-by-side view`,
            risk_level: 'MEDIUM',
            source: 'BROWSER',
            assessment_id: assessmentId,
            attempt_id: attemptIdRef.current,
            question_number: activeQRef.current?.question_number,
            metadata: evidence,
          });

          if (!hasWarnedSplitScreenRef.current) {
            hasWarnedSplitScreenRef.current = true;
            triggerWarning('POSSIBLE_SPLIT_SCREEN', 'Assessment window appears resized to a split-screen view.', evidence);
          }
        } else {
          hasWarnedSplitScreenRef.current = false;
          integrityService.recordIntegrityEvent({
            event_type: 'RESIZE_ANOMALY',
            action: 'Viewport resized',
            details: `Window dimension: ${window.innerWidth}x${window.innerHeight}`,
            risk_level: 'NORMAL',
            source: 'BROWSER',
            assessment_id: assessmentId,
            attempt_id: attemptIdRef.current,
            question_number: activeQRef.current?.question_number,
            metadata: evidence,
          });
        }
      }, 500);
    };

    // 5. Keyboard Copy / Paste shortcuts (Ctrl+C, Ctrl+V, Ctrl+X)
    const handleKeyDown = (e) => {
      const isCtrlOrMeta = e.ctrlKey || e.metaKey;
      if (!isCtrlOrMeta) return;

      const key = e.key.toLowerCase();
      if (key === 'c') {
        const selText = window.getSelection ? window.getSelection().toString() : '';
        integrityService.recordIntegrityEvent({
          event_type: 'COPY / CTRL+C',
          action: 'Code copied',
          details: `Keyboard copy shortcut (length: ${selText.length})`,
          risk_level: 'LOW',
          source: 'ADAPTIVE_QUIZ',
          assessment_id: assessmentId,
          attempt_id: attemptIdRef.current,
          question_number: activeQRef.current?.question_number,
          metadata: { preview: selText.slice(0, 50) },
        });
      } else if (key === 'v') {
        integrityService.recordIntegrityEvent({
          event_type: 'PASTE / CTRL+V',
          action: 'Code pasted',
          details: 'Keyboard paste shortcut executed in assessment',
          risk_level: 'MEDIUM',
          source: 'ADAPTIVE_QUIZ',
          assessment_id: assessmentId,
          attempt_id: attemptIdRef.current,
          question_number: activeQRef.current?.question_number,
        });
      } else if (key === 'x') {
        integrityService.recordIntegrityEvent({
          event_type: 'CUT / CTRL+X',
          action: 'Content cut',
          details: 'Keyboard cut shortcut executed in assessment',
          risk_level: 'LOW',
          source: 'ADAPTIVE_QUIZ',
          assessment_id: assessmentId,
          attempt_id: attemptIdRef.current,
          question_number: activeQRef.current?.question_number,
        });
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleWindowBlur);
    window.addEventListener('focus', handleWindowFocus);
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    window.addEventListener('resize', handleResize);
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      if (resizeTimer) clearTimeout(resizeTimer);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleWindowBlur);
      window.removeEventListener('focus', handleWindowFocus);
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [assessmentId, triggerWarning, attemptState?.attempt_id]);

  // Save Current Question Answer
  const handleSaveAnswer = async (explicitAnswer = selectedAnswer) => {
    if (!attemptState?.attempt_id || !activeQuestion) return null;
    if (!explicitAnswer || !explicitAnswer.trim()) return null;

    setSavingAnswer(true);
    const timeSpent = Math.max(1, Math.round((Date.now() - startTime) / 100) / 10);

    try {
      const updatedState = await assessmentService.saveAnswer(
        attemptState.attempt_id,
        activeQuestion.question_number,
        explicitAnswer.trim(),
        timeSpent
      );
      setAttemptState(updatedState);
      setSaveSuccessMsg('Answer saved successfully!');
      setTimeout(() => setSaveSuccessMsg(''), 3000);
      return updatedState;
    } catch (err) {
      console.error('Failed to save answer:', err);
      alert('Could not save answer. Please check connection.');
      return null;
    } finally {
      setSavingAnswer(false);
    }
  };

  // Next Question Navigation
  const handleNextQuestion = async () => {
    if (!attemptState?.attempt_id || navigating) return;
    setNavigating(true);

    try {
      // Auto-save if student selected an answer that differs from stored
      if (selectedAnswer.trim() && selectedAnswer.trim() !== activeQuestion?.selected_answer) {
        await handleSaveAnswer(selectedAnswer.trim());
      }

      const updatedState = await assessmentService.nextQuestion(attemptState.attempt_id);
      if (updatedState.all_completed) {
        alert(updatedState.message || 'All questions completed!');
      }
      setAttemptState(updatedState);
    } catch (err) {
      console.error('Failed to move to next question:', err);
    } finally {
      setNavigating(false);
    }
  };

  // Previous Question Navigation
  const handlePreviousQuestion = async () => {
    if (!attemptState?.attempt_id || navigating) return;
    if ((attemptState.current_question_index || 1) <= 1) return;

    setNavigating(true);
    try {
      // Auto-save if student selected an answer that differs from stored
      if (selectedAnswer.trim() && selectedAnswer.trim() !== activeQuestion?.selected_answer) {
        await handleSaveAnswer(selectedAnswer.trim());
      }

      const updatedState = await assessmentService.previousQuestion(attemptState.attempt_id);
      setAttemptState(updatedState);
    } catch (err) {
      console.error('Failed to move to previous question:', err);
    } finally {
      setNavigating(false);
    }
  };

  // Direct Jump Navigation
  const handleNavigateDirect = async (qNum) => {
    if (!attemptState?.attempt_id || navigating || qNum === attemptState.current_question_index) return;
    setNavigating(true);
    try {
      if (selectedAnswer.trim() && selectedAnswer.trim() !== activeQuestion?.selected_answer) {
        await handleSaveAnswer(selectedAnswer.trim());
      }
      const updatedState = await assessmentService.navigate(attemptState.attempt_id, qNum);
      setAttemptState(updatedState);
    } catch (err) {
      console.error('Failed direct question navigation:', err);
    } finally {
      setNavigating(false);
    }
  };

  // Complete Assessment
  const handleFinishAssessment = async () => {
    if (!attemptState?.attempt_id) return;
    const confirmFinish = window.confirm('Are you sure you want to finalize and submit this assessment?');
    if (!confirmFinish) return;

    setLoading(true);
    try {
      if (selectedAnswer.trim() && selectedAnswer.trim() !== activeQuestion?.selected_answer) {
        await handleSaveAnswer(selectedAnswer.trim());
      }
      const res = await assessmentService.finishAttempt(attemptState.attempt_id);
      setCompletedSummary(res);
    } catch (err) {
      console.error('Failed to finalize assessment:', err);
      alert('Encountered an issue finalizing assessment.');
    } finally {
      setLoading(false);
    }
  };

  // AI Conceptual Tutor Modal
  const handleExplainConceptAI = async () => {
    if (!activeQuestion) return;
    setAiModalOpen(true);
    if (aiExplanation) return;

    setLoadingAi(true);
    try {
      const data = await aiService.explainConcept(
        activeQuestion.concept_name || 'Core Concept',
        0.0,
        activeQuestion.difficulty || 'MEDIUM'
      );
      setAiExplanation(data);
    } catch (err) {
      console.error('AI explanation failed:', err);
    } finally {
      setLoadingAi(false);
    }
  };

  // AI Wrong Answer Explainer
  const handleAskAiAboutWrongAnswer = async () => {
    if (!activeQuestion) return;
    setLoadingWrongAnswerAi(true);
    try {
      const data = await aiService.explainAnswer(
        activeQuestion.question_text,
        activeQuestion.concept_name || 'Core Concept',
        activeQuestion.selected_answer || selectedAnswer,
        activeQuestion.correct_answer || '',
        activeQuestion.explanation || ''
      );
      setAiWrongAnswerFeedback(data);
    } catch (err) {
      console.error('Failed to get AI wrong answer explanation:', err);
    } finally {
      setLoadingWrongAnswerAi(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: '#64748b' }}>
        <Sparkles size={36} color="#4f46e5" style={{ animation: 'spin 2s linear infinite', marginBottom: '14px' }} />
        <div style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a' }}>Loading Adaptive Assessment...</div>
        <div style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
          Restoring assessment state, question attempts, and adaptive calibration...
        </div>
      </div>
    );
  }

  // Assessment Completed Screen
  if (completedSummary) {
    return (
      <div style={{ maxWidth: '720px', margin: '40px auto', backgroundColor: '#ffffff', borderRadius: '16px', border: '1px solid #e2e8f0', padding: '36px', textAlign: 'center', boxShadow: '0 4px 6px rgba(0,0,0,0.05)' }}>
        <CheckCircle2 size={54} color="#10b981" style={{ margin: '0 auto 16px auto' }} />
        <h2 style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a', margin: '0 0 8px 0' }}>
          Assessment Finalized & Submitted!
        </h2>
        <p style={{ color: '#64748b', fontSize: '14px', marginBottom: '24px' }}>
          Your answers have been stored and evaluated against our Bayesian knowledge tracing model.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', backgroundColor: '#f8fafc', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0', marginBottom: '28px' }}>
          <div>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>Final Score</div>
            <div style={{ fontSize: '28px', fontWeight: 800, color: '#4f46e5', marginTop: '4px' }}>
              {completedSummary.score}%
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>Correct Answers</div>
            <div style={{ fontSize: '28px', fontWeight: 800, color: '#16a34a', marginTop: '4px' }}>
              {completedSummary.questions_correct} / {completedSummary.questions_attempted}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>Integrity Risk</div>
            <div style={{ fontSize: '24px', fontWeight: 800, color: completedSummary.risk_level === 'NORMAL' ? '#059669' : '#d97706', marginTop: '4px' }}>
              {completedSummary.risk_level?.replace('_RISK', '') || 'NORMAL'}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '14px', justifyContent: 'center' }}>
          <button
            onClick={() => loadAssessment(false)}
            style={{
              padding: '12px 24px',
              backgroundColor: '#4f46e5',
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 700,
              fontSize: '14px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <RotateCcw size={16} /> Start New Attempt
          </button>
          <button
            onClick={() => navigate('/student/integrity')}
            style={{
              padding: '12px 24px',
              backgroundColor: '#ffffff',
              color: '#4f46e5',
              border: '1px solid #c7d2fe',
              borderRadius: '8px',
              fontWeight: 700,
              fontSize: '14px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <ShieldAlert size={16} /> View Student Integrity Log
          </button>
        </div>
      </div>
    );
  }

  const questionsList = attemptState?.questions || [];
  const currentQNum = attemptState?.current_question_index || 1;
  const isFirstQuestion = currentQNum <= 1;
  const isAnswerModified = activeQuestion && selectedAnswer.trim() !== (activeQuestion.selected_answer || '').trim();

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '18px' }}>
      {/* Progressive Integrity Warning Banner */}
      {activeWarning && (
        <div
          style={{
            backgroundColor: activeWarning.warning_number === 1 ? '#fffbeb' : '#fef2f2',
            border: `1.5px solid ${activeWarning.warning_number === 1 ? '#f59e0b' : '#ef4444'}`,
            borderRadius: '10px',
            padding: '12px 18px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            color: activeWarning.warning_number === 1 ? '#92400e' : '#991b1b',
            fontSize: '13px',
            fontWeight: 700,
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertTriangle size={20} color={activeWarning.warning_number === 1 ? '#f59e0b' : '#ef4444'} />
            <div>
              <span>{activeWarning.message}</span>
              <span style={{ fontSize: '11px', fontWeight: 500, marginLeft: '8px', color: '#6b7280' }}>
                (All environment events are stored for human integrity audit)
              </span>
            </div>
          </div>
          <button
            onClick={() => setActiveWarning(null)}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 800,
              color: 'inherit',
              padding: '2px 8px',
            }}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Assessment Header Bar */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '14px',
          border: '1px solid #e2e8f0',
          padding: '16px 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
              Adaptive Assessment · Attempt #{attemptState?.attempt_number || 1}
            </h1>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 800,
                backgroundColor: '#eef2ff',
                color: '#4f46e5',
                padding: '2px 8px',
                borderRadius: '6px',
                textTransform: 'uppercase',
              }}
            >
              In Progress
            </span>
          </div>
          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px', display: 'flex', gap: '16px' }}>
            <span>
              Answered: <strong>{attemptState?.summary?.answered || 0} / {attemptState?.summary?.total || 1}</strong>
            </span>
            <span>
              Changed: <strong>{attemptState?.summary?.changed || 0}</strong>
            </span>
            <span>
              Visited: <strong>{attemptState?.summary?.visited || 1} / {attemptState?.summary?.total || 1}</strong>
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Link
            to="/student/integrity"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              backgroundColor: '#f8fafc',
              border: '1px solid #cbd5e1',
              borderRadius: '8px',
              fontSize: '12px',
              fontWeight: 700,
              color: '#334155',
              textDecoration: 'none',
            }}
          >
            <ShieldAlert size={14} color="#4f46e5" />
            Student Integrity Log
          </Link>

          <button
            onClick={handleFinishAssessment}
            style={{
              padding: '6px 14px',
              backgroundColor: '#dc2626',
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Flag size={14} /> Finish Assessment
          </button>
        </div>
      </div>

      {/* Requirement 1 & 2: Question Navigation Strip / Status Pills */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          border: '1px solid #e2e8f0',
          padding: '12px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          overflowX: 'auto',
        }}
      >
        <span style={{ fontSize: '12px', fontWeight: 800, color: '#64748b', textTransform: 'uppercase', minWidth: '90px' }}>
          Questions:
        </span>
        <div style={{ display: 'flex', gap: '8px', flex: 1, overflowX: 'auto', paddingBottom: '2px' }}>
          {questionsList.map((q) => {
            const isCurrent = q.question_number === currentQNum;
            const isAnswered = q.selected_answer && q.selected_answer.trim().length > 0;
            const isChanged = q.is_changed;

            let bgColor = '#ffffff';
            let borderColor = '#cbd5e1';
            let textColor = '#475569';

            if (isCurrent) {
              bgColor = '#eef2ff';
              borderColor = '#4f46e5';
              textColor = '#4338ca';
            } else if (isChanged) {
              bgColor = '#fffbeb';
              borderColor = '#f59e0b';
              textColor = '#92400e';
            } else if (isAnswered) {
              bgColor = '#f0fdf4';
              borderColor = '#86efac';
              textColor = '#166534';
            }

            return (
              <button
                key={q.question_number}
                onClick={() => handleNavigateDirect(q.question_number)}
                disabled={navigating}
                title={`Question ${q.question_number} · Status: ${q.answer_status}${isChanged ? ' (Answer changed)' : ''}`}
                style={{
                  minWidth: '46px',
                  height: '36px',
                  borderRadius: '8px',
                  border: isCurrent ? '2.5px solid #4f46e5' : `1.5px solid ${borderColor}`,
                  backgroundColor: bgColor,
                  color: textColor,
                  fontSize: '13px',
                  fontWeight: isCurrent ? 800 : 700,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px',
                  transition: 'all 0.15s ease',
                  position: 'relative',
                }}
              >
                <span>Q{q.question_number}</span>
                {isChanged ? (
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#f59e0b' }} />
                ) : isAnswered ? (
                  <Check size={12} color="#16a34a" />
                ) : null}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Question Card */}
      {activeQuestion ? (
        <div
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '16px',
            border: '1px solid #e2e8f0',
            padding: '30px 32px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
            display: 'flex',
            flexDirection: 'column',
            gap: '20px',
          }}
        >
          {/* Question Meta Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  fontSize: '13px',
                  fontWeight: 800,
                  color: '#4f46e5',
                  backgroundColor: '#eef2ff',
                  padding: '4px 12px',
                  borderRadius: '6px',
                }}
              >
                Question {activeQuestion.question_number}
              </span>
              <span
                style={{
                  fontSize: '12px',
                  fontWeight: 700,
                  color: '#334155',
                  backgroundColor: '#f1f5f9',
                  padding: '4px 10px',
                  borderRadius: '6px',
                }}
              >
                {activeQuestion.concept_name || 'Core Concept'}
              </span>
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 800,
                  color: activeQuestion.difficulty === 'EASY' ? '#059669' : activeQuestion.difficulty === 'MEDIUM' ? '#d97706' : '#dc2626',
                  backgroundColor: activeQuestion.difficulty === 'EASY' ? '#ecfdf5' : activeQuestion.difficulty === 'MEDIUM' ? '#fffbeb' : '#fef2f2',
                  padding: '4px 8px',
                  borderRadius: '6px',
                  textTransform: 'uppercase',
                }}
              >
                {activeQuestion.difficulty}
              </span>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontSize: '11px',
                  fontWeight: 700,
                  color: '#64748b',
                  backgroundColor: '#f8fafc',
                  padding: '4px 8px',
                  borderRadius: '6px',
                }}
              >
                <Clock size={12} /> {secondsElapsed}s on this question
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
          <div>
            <h2 style={{ fontSize: '17px', fontWeight: 800, color: '#0f172a', margin: 0, lineHeight: '1.6' }}>
              {activeQuestion.question_text}
            </h2>
            {activeQuestion.code_snippet && (
              <pre
                style={{
                  backgroundColor: '#0f172a',
                  color: '#f8fafc',
                  padding: '14px',
                  borderRadius: '8px',
                  fontSize: '13px',
                  overflowX: 'auto',
                  marginTop: '14px',
                  fontFamily: 'monospace',
                }}
              >
                {activeQuestion.code_snippet}
              </pre>
            )}
          </div>

          {/* Answer Selection / Form */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#475569', textTransform: 'uppercase' }}>
                Select Your Answer:
              </div>
              {activeQuestion.answer_status === 'CHANGED' && (
                <span style={{ fontSize: '11px', fontWeight: 800, color: '#92400e', backgroundColor: '#fef3c7', padding: '2px 8px', borderRadius: '4px' }}>
                  Answer Changed (Previously: {activeQuestion.previous_answer})
                </span>
              )}
            </div>

            {/* MCQ / Options */}
            {activeQuestion.options && activeQuestion.options.length > 0 ? (
              activeQuestion.options.map((opt, idx) => {
                const isSelected = selectedAnswer === opt;
                return (
                  <label
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '14px 18px',
                      borderRadius: '10px',
                      border: isSelected ? '2px solid #4f46e5' : '1px solid #cbd5e1',
                      backgroundColor: isSelected ? '#f5f3ff' : '#ffffff',
                      cursor: 'pointer',
                      fontSize: '14px',
                      fontWeight: 500,
                      color: '#1e293b',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <input
                      type="radio"
                      name={`question-ans-${activeQuestion.question_number}`}
                      value={opt}
                      checked={isSelected}
                      onChange={() => setSelectedAnswer(opt)}
                      style={{ accentColor: '#4f46e5', width: '16px', height: '16px' }}
                    />
                    <span>{opt}</span>
                  </label>
                );
              })
            ) : (
              <div>
                <input
                  type="text"
                  value={selectedAnswer}
                  onChange={(e) => setSelectedAnswer(e.target.value)}
                  placeholder="Enter technical keyword or answer..."
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
          </div>

          {/* Answer Evaluation & Concept Identification Feedback */}
          {activeQuestion.selected_answer && activeQuestion.is_correct !== undefined && activeQuestion.is_correct !== null && (
            <div
              style={{
                padding: '16px 20px',
                borderRadius: '12px',
                backgroundColor: activeQuestion.is_correct ? '#f0fdf4' : '#fff5f5',
                border: `1px solid ${activeQuestion.is_correct ? '#bbf7d0' : '#fecaca'}`,
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {activeQuestion.is_correct ? (
                    <CheckCircle2 size={20} color="#16a34a" />
                  ) : (
                    <XCircle size={20} color="#dc2626" />
                  )}
                  <span
                    style={{
                      fontSize: '14px',
                      fontWeight: 800,
                      color: activeQuestion.is_correct ? '#166534' : '#991b1b',
                    }}
                  >
                    {activeQuestion.is_correct ? 'Correct Answer!' : 'Incorrect Answer'}
                  </span>
                </div>
                <span
                  style={{
                    fontSize: '12px',
                    fontWeight: 700,
                    color: '#475569',
                    backgroundColor: '#ffffff',
                    padding: '3px 10px',
                    borderRadius: '6px',
                    border: '1px solid #e2e8f0',
                  }}
                >
                  Core Concept: <strong>{activeQuestion.concept_name}</strong>
                </span>
              </div>

              {!activeQuestion.is_correct && (
                <div style={{ fontSize: '13px', color: '#7f1d1d', lineHeight: '1.5' }}>
                  <div>
                    This question is built on the concept of <strong>{activeQuestion.concept_name}</strong>.
                    {activeQuestion.correct_answer && (
                      <span> Correct Answer: <strong>{activeQuestion.correct_answer}</strong>.</span>
                    )}
                  </div>
                  {activeQuestion.explanation && (
                    <div style={{ marginTop: '6px', color: '#475569', fontSize: '12px', fontStyle: 'italic' }}>
                      {activeQuestion.explanation}
                    </div>
                  )}
                </div>
              )}

              {activeQuestion.is_correct && activeQuestion.explanation && (
                <div style={{ fontSize: '13px', color: '#166534' }}>
                  {activeQuestion.explanation}
                </div>
              )}

              {/* Ask AI Tutor for Explanation if Wrong */}
              {!activeQuestion.is_correct && (
                <div style={{ marginTop: '4px' }}>
                  <button
                    type="button"
                    onClick={handleAskAiAboutWrongAnswer}
                    disabled={loadingWrongAnswerAi}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '7px 14px',
                      backgroundColor: '#4f46e5',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '12px',
                      fontWeight: 700,
                      cursor: loadingWrongAnswerAi ? 'not-allowed' : 'pointer',
                    }}
                  >
                    <Sparkles size={14} /> {loadingWrongAnswerAi ? 'AI Tutor Analyzing...' : `Ask AI: Why is this wrong in ${activeQuestion.concept_name}?`}
                  </button>

                  {aiWrongAnswerFeedback && (
                    <div
                      style={{
                        marginTop: '10px',
                        padding: '14px 16px',
                        backgroundColor: '#ffffff',
                        borderRadius: '8px',
                        border: '1px solid #cbd5e1',
                        fontSize: '12px',
                        color: '#334155',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '6px',
                      }}
                    >
                      <div style={{ fontWeight: 800, color: '#4f46e5', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Sparkles size={14} /> AI Pedagogical Feedback ({aiWrongAnswerFeedback.concept || activeQuestion.concept_name})
                      </div>
                      <div style={{ lineHeight: '1.5' }}>
                        {aiWrongAnswerFeedback.concept_breakdown || aiWrongAnswerFeedback.why_selected_is_wrong}
                      </div>
                      {aiWrongAnswerFeedback.why_correct_is_right && (
                        <div style={{ color: '#047857', marginTop: '2px' }}>
                          <strong>Key Takeaway:</strong> {aiWrongAnswerFeedback.why_correct_is_right}
                        </div>
                      )}
                      {aiWrongAnswerFeedback.pedagogical_tip && (
                        <div style={{ fontStyle: 'italic', color: '#64748b', marginTop: '2px' }}>
                          💡 Tip: {aiWrongAnswerFeedback.pedagogical_tip}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Feedback & Save Status banner */}
          {saveSuccessMsg && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#166534', backgroundColor: '#f0fdf4', padding: '10px 14px', borderRadius: '8px', fontSize: '13px', fontWeight: 700, border: '1px solid #bbf7d0' }}>
              <Check size={16} /> {saveSuccessMsg}
            </div>
          )}

          {/* Requirement 1: [ Previous Question ]  [ Save Answer ]  [ Next Question ] */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderTop: '1px solid #f1f5f9',
              paddingTop: '20px',
              marginTop: '10px',
            }}
          >
            {/* Previous Question Button */}
            <button
              type="button"
              onClick={handlePreviousQuestion}
              disabled={isFirstQuestion || navigating}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 20px',
                backgroundColor: isFirstQuestion ? '#f8fafc' : '#ffffff',
                color: isFirstQuestion ? '#94a3b8' : '#334155',
                border: '1px solid #cbd5e1',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: 700,
                cursor: isFirstQuestion ? 'not-allowed' : 'pointer',
              }}
            >
              <ChevronLeft size={16} /> Previous Question
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              {/* Save Answer Button */}
              <button
                type="button"
                onClick={() => handleSaveAnswer()}
                disabled={savingAnswer || !selectedAnswer.trim()}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '10px 18px',
                  backgroundColor: isAnswerModified ? '#f59e0b' : '#f1f5f9',
                  color: isAnswerModified ? '#ffffff' : '#475569',
                  border: isAnswerModified ? 'none' : '1px solid #cbd5e1',
                  borderRadius: '8px',
                  fontSize: '13px',
                  fontWeight: 700,
                  cursor: savingAnswer || !selectedAnswer.trim() ? 'not-allowed' : 'pointer',
                }}
              >
                <Save size={14} /> {savingAnswer ? 'Saving...' : isAnswerModified ? 'Save Updated Answer' : 'Save Answer'}
              </button>

              {/* Next Question Button */}
              <button
                type="button"
                onClick={handleNextQuestion}
                disabled={navigating}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 24px',
                  backgroundColor: '#4f46e5',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: 800,
                  cursor: navigating ? 'not-allowed' : 'pointer',
                  boxShadow: '0 2px 4px rgba(79, 70, 229, 0.25)',
                }}
              >
                {navigating ? 'Loading...' : 'Next Question'} <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div style={{ padding: '40px', backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', textAlign: 'center' }}>
          <CheckCircle2 size={40} color="#10b981" style={{ margin: '0 auto 12px auto' }} />
          <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a' }}>Assessment Finished</h3>
          <p style={{ color: '#64748b', fontSize: '14px' }}>
            All eligible questions for this assessment session have been answered.
          </p>
          <button
            onClick={handleFinishAssessment}
            style={{ padding: '10px 20px', backgroundColor: '#4f46e5', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 700 }}
          >
            Finalize and View Results
          </button>
        </div>
      )}

      {/* AI Conceptual Tutor Modal */}
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
                  AI Conceptual Tutor · {activeQuestion?.concept_name}
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
