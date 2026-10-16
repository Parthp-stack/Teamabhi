import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { trainerService } from '../services/learningService';
import {
  FolderTree,
  BookOpen,
  Plus,
  Edit2,
  Trash2,
  GitFork,
  HelpCircle,
  Sparkles,
  Search,
  Filter,
  Check,
  X,
  AlertCircle,
  CheckCircle2,
  Layers,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';

export default function CurriculumManagementPage() {
  const navigate = useNavigate();

  // Active Tab: 'concepts' | 'questions' | 'course'
  const [activeTab, setActiveTab] = useState('concepts');

  const [curriculum, setCurriculum] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Question Bank filters
  const [questionConceptFilter, setQuestionConceptFilter] = useState('');
  const [questionDiffFilter, setQuestionDiffFilter] = useState('');
  const [questionSearch, setQuestionSearch] = useState('');

  // Concept Modal states
  const [conceptModalOpen, setConceptModalOpen] = useState(false);
  const [editingConcept, setEditingConcept] = useState(null);
  const [conceptForm, setConceptForm] = useState({
    name: '',
    module_id: 1,
    description: '',
    difficulty: 'MEDIUM',
    order_index: 0,
  });

  // Prerequisite Relationship Matrix Modal
  const [prereqModalOpen, setPrereqModalOpen] = useState(false);
  const [selectedConceptForPrereq, setSelectedConceptForPrereq] = useState(null);

  // Question Modal states
  const [questionModalOpen, setQuestionModalOpen] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [questionForm, setQuestionForm] = useState({
    concept_id: 1,
    question_text: '',
    question_type: 'MCQ',
    difficulty: 'MEDIUM',
    options: ['', '', '', ''],
    correct_answer: '',
    explanation: '',
  });

  // AI Question Preview Modal (Section 13)
  const [aiPreviewOpen, setAiPreviewOpen] = useState(false);
  const [aiGenerating, setAiGenerating] = useState(false);
  const [aiConfig, setAiConfig] = useState({
    concept_name: 'Classes',
    difficulty: 'MEDIUM',
    question_type: 'MCQ',
  });
  const [aiDraft, setAiDraft] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setErrorMsg('');
      const [curricRes, questRes] = await Promise.all([
        trainerService.getCurriculum(),
        trainerService.getQuestionBank({
          concept_id: questionConceptFilter ? parseInt(questionConceptFilter) : undefined,
          difficulty: questionDiffFilter || undefined,
          search: questionSearch || undefined,
        }),
      ]);
      setCurriculum(curricRes);
      setQuestions(questRes?.questions || []);
    } catch (err) {
      console.error('Failed to load curriculum data:', err);
      setErrorMsg('Failed to load curriculum records. Please verify connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [questionConceptFilter, questionDiffFilter]);

  const handleQuestionSearchSubmit = (e) => {
    e.preventDefault();
    loadData();
  };

  // Concept CRUD
  const handleOpenConceptCreate = () => {
    setEditingConcept(null);
    setConceptForm({
      name: '',
      module_id: curriculum?.modules?.[0]?.id || 1,
      description: '',
      difficulty: 'MEDIUM',
      order_index: curriculum?.concepts?.length || 0,
    });
    setConceptModalOpen(true);
  };

  const handleOpenConceptEdit = (concept) => {
    setEditingConcept(concept);
    setConceptForm({
      name: concept.name,
      module_id: concept.module_id || 1,
      description: concept.description || '',
      difficulty: concept.difficulty || 'MEDIUM',
      order_index: concept.order_index || 0,
    });
    setConceptModalOpen(true);
  };

  const handleSaveConcept = async (e) => {
    e.preventDefault();
    try {
      setErrorMsg('');
      if (editingConcept) {
        await trainerService.updateConcept(editingConcept.id, conceptForm);
        setSuccessMsg(`Concept '${conceptForm.name}' updated successfully.`);
      } else {
        await trainerService.createConcept(conceptForm);
        setSuccessMsg(`Concept '${conceptForm.name}' created successfully.`);
      }
      setConceptModalOpen(false);
      loadData();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to save concept.');
    }
  };

  const handleDeleteConcept = async (conceptId, name) => {
    if (!window.confirm(`Are you sure you want to delete concept '${name}'? All prerequisite edges will be removed.`)) {
      return;
    }
    try {
      setErrorMsg('');
      await trainerService.deleteConcept(conceptId);
      setSuccessMsg(`Concept '${name}' deleted successfully.`);
      loadData();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to delete concept.');
    }
  };

  // Prerequisite Toggle with Cycle Detection Handling
  const handleTogglePrerequisite = async (candidateConceptId) => {
    if (!selectedConceptForPrereq) return;
    setErrorMsg('');
    setSuccessMsg('');

    const targetId = selectedConceptForPrereq.id;
    const isAlreadyPrereq = selectedConceptForPrereq.prerequisites?.some(
      (p) => p.id === candidateConceptId
    );

    try {
      if (isAlreadyPrereq) {
        await trainerService.removePrerequisite(targetId, candidateConceptId);
        setSuccessMsg('Prerequisite relationship removed.');
      } else {
        await trainerService.addPrerequisite(targetId, candidateConceptId);
        setSuccessMsg('Prerequisite edge added successfully.');
      }
      // Reload curriculum and refresh the active concept's prerequisites
      const curricRes = await trainerService.getCurriculum();
      setCurriculum(curricRes);
      const updatedConcept = curricRes.concepts.find((c) => c.id === targetId);
      setSelectedConceptForPrereq(updatedConcept);
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to update prerequisite edge.');
    }
  };

  // Question CRUD
  const handleOpenQuestionCreate = () => {
    setEditingQuestion(null);
    setQuestionForm({
      concept_id: curriculum?.concepts?.[0]?.id || 1,
      question_text: '',
      question_type: 'MCQ',
      difficulty: 'MEDIUM',
      options: ['', '', '', ''],
      correct_answer: '',
      explanation: '',
    });
    setQuestionModalOpen(true);
  };

  const handleOpenQuestionEdit = (q) => {
    setEditingQuestion(q);
    setQuestionForm({
      concept_id: q.concept_id,
      question_text: q.question_text,
      question_type: q.question_type,
      difficulty: q.difficulty,
      options: q.options || ['', '', '', ''],
      correct_answer: q.correct_answer,
      explanation: q.explanation || '',
    });
    setQuestionModalOpen(true);
  };

  const handleSaveQuestion = async (e) => {
    e.preventDefault();
    try {
      setErrorMsg('');
      const payload = {
        ...questionForm,
        options: questionForm.options.filter((o) => o.trim() !== ''),
      };
      if (editingQuestion) {
        await trainerService.updateQuestion(editingQuestion.id, payload);
        setSuccessMsg('Question updated successfully.');
      } else {
        await trainerService.createQuestion(payload);
        setSuccessMsg('Question created in Question Bank.');
      }
      setQuestionModalOpen(false);
      loadData();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to save question.');
    }
  };

  const handleDeleteQuestion = async (qId) => {
    if (!window.confirm('Delete this question from question bank?')) return;
    try {
      setErrorMsg('');
      await trainerService.deleteQuestion(qId);
      setSuccessMsg('Question deleted.');
      loadData();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to delete question.');
    }
  };

  // AI Question Generation & Preview (Section 13)
  const handleGenerateAIPreview = async () => {
    try {
      setAiGenerating(true);
      setErrorMsg('');
      const res = await trainerService.previewAIQuestion(aiConfig);
      setAiDraft(res.draft_question);
    } catch (err) {
      setErrorMsg('Failed to generate draft question using AI: ' + (err.response?.data?.detail || err.message));
    } finally {
      setAiGenerating(false);
    }
  };

  const handleApproveAIDraft = async () => {
    if (!aiDraft) return;
    const targetConcept = curriculum?.concepts?.find((c) => c.name === aiConfig.concept_name);
    if (!targetConcept) {
      setErrorMsg('Target concept not found.');
      return;
    }

    try {
      await trainerService.createQuestion({
        concept_id: targetConcept.id,
        question_text: aiDraft.question_text,
        question_type: aiDraft.question_type || 'MCQ',
        difficulty: aiDraft.difficulty || aiConfig.difficulty,
        options: aiDraft.options || [],
        correct_answer: aiDraft.correct_answer,
        explanation: aiDraft.explanation || '',
      });
      setSuccessMsg(`AI-draft question for '${aiConfig.concept_name}' validated and saved to question bank!`);
      setAiPreviewOpen(false);
      setAiDraft(null);
      loadData();
    } catch (err) {
      setErrorMsg('Failed to save approved question: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1180px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ fontSize: '11px', fontWeight: 800, color: '#4f46e5', textTransform: 'uppercase' }}>
              Master Data & Curriculum Engine
            </span>
          </div>
          <h1 style={{ fontSize: '26px', fontWeight: 800, color: '#0f172a', margin: '0 0 4px 0' }}>
            Course, Concept & Question Bank Management
          </h1>
          <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>
            Manage the prerequisite DAG graph, maintain question banks, and validate AI-generated assessments.
          </p>
        </div>

        <button
          onClick={() => navigate('/trainer/dashboard')}
          style={{
            padding: '8px 16px',
            backgroundColor: '#f1f5f9',
            color: '#334155',
            border: '1px solid #cbd5e1',
            borderRadius: '8px',
            fontSize: '13px',
            fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          ← Back to Trainer Dashboard
        </button>
      </div>

      {/* Status Messages */}
      {errorMsg && (
        <div style={{ padding: '12px 16px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#991b1b', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertCircle size={16} /> {errorMsg}
        </div>
      )}
      {successMsg && (
        <div style={{ padding: '12px 16px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', color: '#166534', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={16} /> {successMsg}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '2px solid #e2e8f0', paddingBottom: '2px' }}>
        <button
          onClick={() => setActiveTab('concepts')}
          style={{
            padding: '10px 18px',
            borderRadius: '8px 8px 0 0',
            border: 'none',
            backgroundColor: activeTab === 'concepts' ? '#ffffff' : 'transparent',
            color: activeTab === 'concepts' ? '#4f46e5' : '#64748b',
            fontWeight: 800,
            fontSize: '14px',
            cursor: 'pointer',
            borderBottom: activeTab === 'concepts' ? '3px solid #4f46e5' : '3px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <GitFork size={16} /> Concepts & Prerequisite DAG ({curriculum?.concepts?.length || 0})
        </button>

        <button
          onClick={() => setActiveTab('questions')}
          style={{
            padding: '10px 18px',
            borderRadius: '8px 8px 0 0',
            border: 'none',
            backgroundColor: activeTab === 'questions' ? '#ffffff' : 'transparent',
            color: activeTab === 'questions' ? '#4f46e5' : '#64748b',
            fontWeight: 800,
            fontSize: '14px',
            cursor: 'pointer',
            borderBottom: activeTab === 'questions' ? '3px solid #4f46e5' : '3px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <HelpCircle size={16} /> Question Bank ({questions.length})
        </button>

        <button
          onClick={() => setActiveTab('course')}
          style={{
            padding: '10px 18px',
            borderRadius: '8px 8px 0 0',
            border: 'none',
            backgroundColor: activeTab === 'course' ? '#ffffff' : 'transparent',
            color: activeTab === 'course' ? '#4f46e5' : '#64748b',
            fontWeight: 800,
            fontSize: '14px',
            cursor: 'pointer',
            borderBottom: activeTab === 'course' ? '3px solid #4f46e5' : '3px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <BookOpen size={16} /> Course & Modules
        </button>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: CONCEPTS & PREREQUISITE DAG MATRIX (SECTION 12) */}
      {/* ========================================================================= */}
      {activeTab === 'concepts' && (
        <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                Course Concepts & Directed Acyclic Graph (DAG)
              </h3>
              <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#64748b' }}>
                Define syllabus concepts and prerequisite edges. The engine automatically rejects any circular dependencies.
              </p>
            </div>

            <button
              onClick={handleOpenConceptCreate}
              style={{
                padding: '8px 16px',
                backgroundColor: '#4f46e5',
                color: '#ffffff',
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
              <Plus size={16} /> Add Concept
            </button>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #e2e8f0', color: '#64748b' }}>
                <th style={{ padding: '12px' }}>Order</th>
                <th style={{ padding: '12px' }}>Concept Name</th>
                <th style={{ padding: '12px' }}>Difficulty</th>
                <th style={{ padding: '12px' }}>Prerequisites (Must Master First)</th>
                <th style={{ padding: '12px' }}>Questions</th>
                <th style={{ padding: '12px' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {curriculum?.concepts?.map((c) => (
                <tr key={c.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '14px', color: '#64748b', fontWeight: 700 }}>
                    #{c.order_index}
                  </td>
                  <td style={{ padding: '14px' }}>
                    <div style={{ fontWeight: 800, color: '#0f172a' }}>{c.name}</div>
                    <div style={{ fontSize: '12px', color: '#64748b', maxWidth: '320px' }}>{c.description}</div>
                  </td>
                  <td style={{ padding: '14px' }}>
                    <span
                      style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: c.difficulty === 'EASY' ? '#dcfce7' : c.difficulty === 'HARD' ? '#fee2e2' : '#e0e7ff',
                        color: c.difficulty === 'EASY' ? '#166534' : c.difficulty === 'HARD' ? '#991b1b' : '#4338ca',
                      }}
                    >
                      {c.difficulty}
                    </span>
                  </td>
                  <td style={{ padding: '14px' }}>
                    {c.prerequisites && c.prerequisites.length > 0 ? (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                        {c.prerequisites.map((p) => (
                          <span
                            key={p.id}
                            style={{
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontSize: '11px',
                              fontWeight: 700,
                              backgroundColor: '#f1f5f9',
                              color: '#334155',
                              border: '1px solid #cbd5e1',
                            }}
                          >
                            {p.name}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span style={{ color: '#94a3b8', fontStyle: 'italic' }}>None (Foundational Root)</span>
                    )}
                  </td>
                  <td style={{ padding: '14px', fontWeight: 700, color: '#0f172a' }}>
                    {c.question_count}
                  </td>
                  <td style={{ padding: '14px' }}>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button
                        onClick={() => {
                          setSelectedConceptForPrereq(c);
                          setPrereqModalOpen(true);
                        }}
                        style={{
                          padding: '5px 10px',
                          backgroundColor: '#eef2ff',
                          color: '#4f46e5',
                          border: '1px solid #c7d2fe',
                          borderRadius: '6px',
                          fontSize: '12px',
                          fontWeight: 700,
                          cursor: 'pointer',
                        }}
                        title="Configure Prerequisites"
                      >
                        Prereqs
                      </button>
                      <button
                        onClick={() => handleOpenConceptEdit(c)}
                        style={{
                          padding: '5px 10px',
                          backgroundColor: '#f8fafc',
                          color: '#334155',
                          border: '1px solid #cbd5e1',
                          borderRadius: '6px',
                          fontSize: '12px',
                          cursor: 'pointer',
                        }}
                      >
                        <Edit2 size={13} />
                      </button>
                      <button
                        onClick={() => handleDeleteConcept(c.id, c.name)}
                        style={{
                          padding: '5px 10px',
                          backgroundColor: '#fef2f2',
                          color: '#b91c1c',
                          border: '1px solid #fecaca',
                          borderRadius: '6px',
                          fontSize: '12px',
                          cursor: 'pointer',
                        }}
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: QUESTION BANK MANAGEMENT (SECTION 13) */}
      {/* ========================================================================= */}
      {activeTab === 'questions' && (
        <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                Question Bank
              </h3>
              <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#64748b' }}>
                Browse, create, edit questions, or generate new questions with the AI Question Assistant.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={() => setAiPreviewOpen(true)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#7c3aed',
                  color: '#ffffff',
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
                <Sparkles size={16} /> AI Question Assistant
              </button>

              <button
                onClick={handleOpenQuestionCreate}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#4f46e5',
                  color: '#ffffff',
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
                <Plus size={16} /> Create Question
              </button>
            </div>
          </div>

          {/* Question Filter Bar */}
          <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', alignItems: 'center' }}>
            <select
              value={questionConceptFilter}
              onChange={(e) => setQuestionConceptFilter(e.target.value)}
              style={{
                padding: '8px 12px',
                borderRadius: '8px',
                border: '1px solid #cbd5e1',
                fontSize: '13px',
                backgroundColor: '#ffffff',
              }}
            >
              <option value="">All Concepts</option>
              {curriculum?.concepts?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>

            <select
              value={questionDiffFilter}
              onChange={(e) => setQuestionDiffFilter(e.target.value)}
              style={{
                padding: '8px 12px',
                borderRadius: '8px',
                border: '1px solid #cbd5e1',
                fontSize: '13px',
                backgroundColor: '#ffffff',
              }}
            >
              <option value="">All Difficulties</option>
              <option value="EASY">EASY</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HARD">HARD</option>
            </select>

            <form onSubmit={handleQuestionSearchSubmit} style={{ display: 'flex', gap: '8px', flex: 1 }}>
              <div style={{ position: 'relative', flex: 1 }}>
                <Search size={14} color="#94a3b8" style={{ position: 'absolute', left: '10px', top: '10px' }} />
                <input
                  type="text"
                  placeholder="Search question text..."
                  value={questionSearch}
                  onChange={(e) => setQuestionSearch(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px 8px 30px',
                    borderRadius: '8px',
                    border: '1px solid #cbd5e1',
                    fontSize: '13px',
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              <button
                type="submit"
                style={{
                  padding: '8px 14px',
                  backgroundColor: '#f1f5f9',
                  border: '1px solid #cbd5e1',
                  borderRadius: '8px',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Search
              </button>
            </form>
          </div>

          {/* Question List Table */}
          {questions.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {questions.map((q) => (
                <div
                  key={q.id}
                  style={{
                    padding: '16px',
                    border: '1px solid #e2e8f0',
                    borderRadius: '10px',
                    backgroundColor: '#f8fafc',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span
                        style={{
                          fontSize: '11px',
                          fontWeight: 800,
                          backgroundColor: '#e0e7ff',
                          color: '#4338ca',
                          padding: '2px 8px',
                          borderRadius: '4px',
                        }}
                      >
                        {q.concept_name}
                      </span>
                      <span
                        style={{
                          fontSize: '11px',
                          fontWeight: 700,
                          backgroundColor: q.difficulty === 'EASY' ? '#dcfce7' : q.difficulty === 'HARD' ? '#fee2e2' : '#fef3c7',
                          color: q.difficulty === 'EASY' ? '#166534' : q.difficulty === 'HARD' ? '#991b1b' : '#92400e',
                          padding: '2px 8px',
                          borderRadius: '4px',
                        }}
                      >
                        {q.difficulty}
                      </span>
                      <span style={{ fontSize: '11px', color: '#64748b' }}>
                        ID #{q.id} · {q.question_type}
                      </span>
                    </div>

                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button
                        onClick={() => handleOpenQuestionEdit(q)}
                        style={{
                          padding: '4px 8px',
                          backgroundColor: '#ffffff',
                          border: '1px solid #cbd5e1',
                          borderRadius: '6px',
                          fontSize: '12px',
                          cursor: 'pointer',
                        }}
                      >
                        <Edit2 size={12} />
                      </button>
                      <button
                        onClick={() => handleDeleteQuestion(q.id)}
                        style={{
                          padding: '4px 8px',
                          backgroundColor: '#fef2f2',
                          color: '#b91c1c',
                          border: '1px solid #fecaca',
                          borderRadius: '6px',
                          fontSize: '12px',
                          cursor: 'pointer',
                        }}
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>

                  <div style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a', marginBottom: '10px' }}>
                    {q.question_text}
                  </div>

                  {q.options && q.options.length > 0 && (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px', marginBottom: '8px' }}>
                      {q.options.map((opt, i) => {
                        const isCorrect = opt === q.correct_answer;
                        return (
                          <div
                            key={i}
                            style={{
                              padding: '6px 10px',
                              borderRadius: '6px',
                              border: `1px solid ${isCorrect ? '#86efac' : '#e2e8f0'}`,
                              backgroundColor: isCorrect ? '#f0fdf4' : '#ffffff',
                              color: isCorrect ? '#166534' : '#475569',
                              fontSize: '12px',
                              fontWeight: isCorrect ? 700 : 500,
                            }}
                          >
                            {opt} {isCorrect && '✓'}
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {q.explanation && (
                    <div style={{ fontSize: '12px', color: '#64748b', fontStyle: 'italic', marginTop: '6px' }}>
                      <strong>Pedagogical Explanation:</strong> {q.explanation}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ padding: '48px', textAlign: 'center', color: '#94a3b8' }}>
              No questions found matching current filters.
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: COURSE & MODULES */}
      {/* ========================================================================= */}
      {activeTab === 'course' && (
        <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '24px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: '0 0 16px 0' }}>
            Course Modules Structure
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {curriculum?.modules?.map((m) => (
              <div
                key={m.id}
                style={{
                  padding: '16px',
                  borderRadius: '10px',
                  border: '1px solid #e2e8f0',
                  backgroundColor: '#f8fafc',
                }}
              >
                <div style={{ fontWeight: 800, fontSize: '15px', color: '#0f172a' }}>
                  Module #{m.order_index + 1}: {m.title}
                </div>
                <div style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
                  {m.description || 'Module curriculum block.'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: PREREQUISITE MATRIX CHECKLIST WITH CYCLE DETECTION (SECTION 12) */}
      {/* ========================================================================= */}
      {prereqModalOpen && selectedConceptForPrereq && (
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
              maxWidth: '540px',
              width: '100%',
              padding: '24px',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <span style={{ fontSize: '11px', fontWeight: 800, color: '#4f46e5', textTransform: 'uppercase' }}>
                  DAG Dependency Matrix
                </span>
                <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: '2px 0 0 0' }}>
                  Prerequisites for: {selectedConceptForPrereq.name}
                </h3>
              </div>
              <button onClick={() => setPrereqModalOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                <X size={20} color="#64748b" />
              </button>
            </div>

            <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '16px' }}>
              Select which concepts a student must master (≥65%) before <strong>{selectedConceptForPrereq.name}</strong> is unlocked.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '320px', overflowY: 'auto', marginBottom: '20px' }}>
              {curriculum?.concepts
                ?.filter((c) => c.id !== selectedConceptForPrereq.id)
                .map((c) => {
                  const isChecked = selectedConceptForPrereq.prerequisites?.some((p) => p.id === c.id);

                  return (
                    <label
                      key={c.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        padding: '10px 14px',
                        borderRadius: '8px',
                        border: isChecked ? '1.5px solid #4f46e5' : '1px solid #e2e8f0',
                        backgroundColor: isChecked ? '#eef2ff' : '#f8fafc',
                        cursor: 'pointer',
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => handleTogglePrerequisite(c.id)}
                        style={{ width: '16px', height: '16px', accentColor: '#4f46e5' }}
                      />
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '13px', color: '#0f172a' }}>{c.name}</div>
                        <div style={{ fontSize: '11px', color: '#64748b' }}>Difficulty: {c.difficulty}</div>
                      </div>
                    </label>
                  );
                })}
            </div>

            <div style={{ textAlign: 'right' }}>
              <button
                onClick={() => setPrereqModalOpen(false)}
                style={{
                  padding: '8px 18px',
                  backgroundColor: '#4f46e5',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: 700,
                  fontSize: '13px',
                  cursor: 'pointer',
                }}
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: CREATE / EDIT CONCEPT */}
      {/* ========================================================================= */}
      {conceptModalOpen && (
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
              maxWidth: '480px',
              width: '100%',
              padding: '24px',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                {editingConcept ? 'Edit Concept' : 'Create New Concept'}
              </h3>
              <button onClick={() => setConceptModalOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                <X size={20} color="#64748b" />
              </button>
            </div>

            <form onSubmit={handleSaveConcept} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>
                  Concept Name
                </label>
                <input
                  type="text"
                  required
                  value={conceptForm.name}
                  onChange={(e) => setConceptForm({ ...conceptForm, name: e.target.value })}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>
                  Description
                </label>
                <textarea
                  rows={3}
                  value={conceptForm.description}
                  onChange={(e) => setConceptForm({ ...conceptForm, description: e.target.value })}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>
                    Difficulty
                  </label>
                  <select
                    value={conceptForm.difficulty}
                    onChange={(e) => setConceptForm({ ...conceptForm, difficulty: e.target.value })}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13px', backgroundColor: '#ffffff' }}
                  >
                    <option value="EASY">EASY</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HARD">HARD</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>
                    Order Index
                  </label>
                  <input
                    type="number"
                    value={conceptForm.order_index}
                    onChange={(e) => setConceptForm({ ...conceptForm, order_index: parseInt(e.target.value) || 0 })}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
                <button
                  type="button"
                  onClick={() => setConceptModalOpen(false)}
                  style={{ padding: '8px 16px', backgroundColor: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{ padding: '8px 16px', backgroundColor: '#4f46e5', color: '#ffffff', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: 700, cursor: 'pointer' }}
                >
                  Save Concept
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: CREATE / EDIT QUESTION */}
      {/* ========================================================================= */}
      {questionModalOpen && (
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
              maxWidth: '600px',
              width: '100%',
              padding: '24px',
              maxHeight: '90vh',
              overflowY: 'auto',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                {editingQuestion ? 'Edit Question' : 'Create Question'}
              </h3>
              <button onClick={() => setQuestionModalOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                <X size={20} color="#64748b" />
              </button>
            </div>

            <form onSubmit={handleSaveQuestion} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>
                    Concept
                  </label>
                  <select
                    value={questionForm.concept_id}
                    onChange={(e) => setQuestionForm({ ...questionForm, concept_id: parseInt(e.target.value) })}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13px', backgroundColor: '#ffffff' }}
                  >
                    {curriculum?.concepts?.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>
                    Difficulty
                  </label>
                  <select
                    value={questionForm.difficulty}
                    onChange={(e) => setQuestionForm({ ...questionForm, difficulty: e.target.value })}
                    style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13px', backgroundColor: '#ffffff' }}
                  >
                    <option value="EASY">EASY</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HARD">HARD</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>
                  Question Text
                </label>
                <textarea
                  required
                  rows={3}
                  value={questionForm.question_text}
                  onChange={(e) => setQuestionForm({ ...questionForm, question_text: e.target.value })}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>
                  Options (4 Multiple Choice Options)
                </label>
                {questionForm.options.map((opt, i) => (
                  <input
                    key={i}
                    type="text"
                    placeholder={`Option ${i + 1}`}
                    value={opt}
                    onChange={(e) => {
                      const newOpts = [...questionForm.options];
                      newOpts[i] = e.target.value;
                      setQuestionForm({ ...questionForm, options: newOpts });
                    }}
                    style={{ width: '100%', padding: '6px 10px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '12px', marginBottom: '6px', boxSizing: 'border-box' }}
                  />
                ))}
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>
                  Correct Answer (Must match one of the options)
                </label>
                <input
                  type="text"
                  required
                  value={questionForm.correct_answer}
                  onChange={(e) => setQuestionForm({ ...questionForm, correct_answer: e.target.value })}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>
                  Explanation (Shown after attempt)
                </label>
                <textarea
                  rows={2}
                  value={questionForm.explanation}
                  onChange={(e) => setQuestionForm({ ...questionForm, explanation: e.target.value })}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
                <button
                  type="button"
                  onClick={() => setQuestionModalOpen(false)}
                  style={{ padding: '8px 16px', backgroundColor: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{ padding: '8px 16px', backgroundColor: '#4f46e5', color: '#ffffff', border: 'none', borderRadius: '8px', fontSize: '13px', fontWeight: 700, cursor: 'pointer' }}
                >
                  Save Question
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: AI QUESTION ASSISTANT & PREVIEW (SECTION 13) */}
      {/* ========================================================================= */}
      {aiPreviewOpen && (
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
              maxWidth: '640px',
              width: '100%',
              padding: '24px',
              maxHeight: '90vh',
              overflowY: 'auto',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={20} color="#7c3aed" />
                <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                  AI Question Generator & Human Validation
                </h3>
              </div>
              <button onClick={() => setAiPreviewOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                <X size={20} color="#64748b" />
              </button>
            </div>

            <p style={{ fontSize: '13px', color: '#64748b', marginBottom: '16px' }}>
              Per Section 13 guidelines: AI-generated questions are presented for trainer preview and adjustment before being approved into the live question bank.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '10px', alignItems: 'flex-end', marginBottom: '20px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>
                  Target Concept
                </label>
                <select
                  value={aiConfig.concept_name}
                  onChange={(e) => setAiConfig({ ...aiConfig, concept_name: e.target.value })}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13px', backgroundColor: '#ffffff' }}
                >
                  {curriculum?.concepts?.map((c) => (
                    <option key={c.id} value={c.name}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '4px' }}>
                  Difficulty
                </label>
                <select
                  value={aiConfig.difficulty}
                  onChange={(e) => setAiConfig({ ...aiConfig, difficulty: e.target.value })}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13px', backgroundColor: '#ffffff' }}
                >
                  <option value="EASY">EASY</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HARD">HARD</option>
                </select>
              </div>

              <button
                onClick={handleGenerateAIPreview}
                disabled={aiGenerating}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#7c3aed',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '13px',
                  fontWeight: 700,
                  cursor: aiGenerating ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  height: '36px',
                }}
              >
                {aiGenerating ? <RefreshCw size={14} style={{ animation: 'spin 1s infinite' }} /> : <Sparkles size={14} />}
                {aiGenerating ? 'Synthesizing...' : 'Generate Draft'}
              </button>
            </div>

            {/* AI Draft Preview with Editable Controls */}
            {aiDraft && (
              <div style={{ backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '11px', fontWeight: 800, color: '#7c3aed', textTransform: 'uppercase' }}>
                    Draft Question Preview (Review & Validate)
                  </span>
                  <span style={{ fontSize: '11px', fontWeight: 700, backgroundColor: '#e9d5ff', color: '#6b21a8', padding: '2px 8px', borderRadius: '4px' }}>
                    {aiConfig.concept_name} · {aiDraft.difficulty}
                  </span>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#475569', marginBottom: '2px' }}>
                    Question Text
                  </label>
                  <textarea
                    rows={3}
                    value={aiDraft.question_text}
                    onChange={(e) => setAiDraft({ ...aiDraft, question_text: e.target.value })}
                    style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#475569', marginBottom: '2px' }}>
                    Options (Editable)
                  </label>
                  {aiDraft.options?.map((opt, i) => (
                    <input
                      key={i}
                      type="text"
                      value={opt}
                      onChange={(e) => {
                        const newOpts = [...aiDraft.options];
                        newOpts[i] = e.target.value;
                        setAiDraft({ ...aiDraft, options: newOpts });
                      }}
                      style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '12px', marginBottom: '4px', boxSizing: 'border-box' }}
                    />
                  ))}
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#475569', marginBottom: '2px' }}>
                    Correct Answer
                  </label>
                  <input
                    type="text"
                    value={aiDraft.correct_answer}
                    onChange={(e) => setAiDraft({ ...aiDraft, correct_answer: e.target.value })}
                    style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '12px', boxSizing: 'border-box' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#475569', marginBottom: '2px' }}>
                    Pedagogical Explanation
                  </label>
                  <textarea
                    rows={2}
                    value={aiDraft.explanation}
                    onChange={(e) => setAiDraft({ ...aiDraft, explanation: e.target.value })}
                    style={{ width: '100%', padding: '6px 8px', borderRadius: '4px', border: '1px solid #cbd5e1', fontSize: '12px', boxSizing: 'border-box' }}
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                  <button
                    onClick={() => setAiDraft(null)}
                    style={{ padding: '8px 14px', backgroundColor: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
                  >
                    Discard
                  </button>
                  <button
                    onClick={handleApproveAIDraft}
                    style={{ padding: '8px 18px', backgroundColor: '#16a34a', color: '#ffffff', border: 'none', borderRadius: '6px', fontSize: '12px', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
                  >
                    <Check size={14} /> Approve & Save to Question Bank
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
