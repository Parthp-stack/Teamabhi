import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { trainerService } from '../services/learningService';
import {
  GitBranch,
  Terminal,
  Code2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Play,
  Sparkles,
  Layers,
  FileCode,
  ShieldCheck,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';

export default function RepoEvaluationDevOpsPage() {
  const navigate = useNavigate();

  // Active view: 'github_eval' | 'devops_lab'
  const [activeTab, setActiveTab] = useState('github_eval');

  // GitHub Evaluation State
  const [repoUrl, setRepoUrl] = useState('https://github.com/tiangolo/fastapi');
  const [analyzingRepo, setAnalyzingRepo] = useState(false);
  const [repoAnalysis, setRepoAnalysis] = useState(null);
  const [repoError, setRepoError] = useState('');

  // Viva Voce State
  const [vivaAnswers, setVivaAnswers] = useState({});
  const [evaluatingViva, setEvaluatingViva] = useState(false);
  const [vivaEvaluationResult, setVivaEvaluationResult] = useState(null);

  // DevOps Lab State
  const [selectedTask, setSelectedTask] = useState('dockerfile_basic');
  const [devopsCode, setDevopsCode] = useState(`# Task 1: Production FastAPI Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
`);
  const [verifyingDevops, setVerifyingDevops] = useState(false);
  const [devopsResult, setDevopsResult] = useState(null);

  // Switch DevOps tasks
  const handleSelectDevOpsTask = (taskId) => {
    setSelectedTask(taskId);
    setDevopsResult(null);
    if (taskId === 'dockerfile_basic') {
      setDevopsCode(`# Task 1: Production FastAPI Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
`);
    } else if (taskId === 'dockerfile_multistage') {
      setDevopsCode(`# Task 2: Multi-Stage Secure Dockerfile
# Stage 1: Build & Dependencies
FROM python:3.12-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Production Minimal Runtime
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN useradd -m -u 1000 appuser
USER appuser

COPY --from=builder /root/.local /home/appuser/.local
COPY . .

EXPOSE 8000
CMD ["python", "main.py"]
`);
    } else if (taskId === 'ci_workflow') {
      setDevopsCode(`# Task 3: GitHub Actions CI Pipeline (.github/workflows/ci.yml)
name: Continuous Integration

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run Pytest Test Suite
        run: |
          pytest backend/tests
`);
    }
  };

  // Run GitHub analysis
  const handleAnalyzeRepo = async (e) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    setAnalyzingRepo(true);
    setRepoError('');
    setRepoAnalysis(null);
    setVivaEvaluationResult(null);
    setVivaAnswers({});

    try {
      const data = await trainerService.analyzeGitHubRepo(repoUrl.trim());
      setRepoAnalysis(data);
    } catch (err) {
      setRepoError(err.response?.data?.detail || 'Failed to inspect GitHub repository.');
    } finally {
      setAnalyzingRepo(false);
    }
  };

  // Submit Viva answers
  const handleSubmitViva = async () => {
    if (!repoAnalysis) return;
    setEvaluatingViva(true);
    try {
      const answersList = repoAnalysis.viva_questions.map((q) => ({
        question_id: q.id,
        question: q.question,
        answer: vivaAnswers[q.id] || 'Not answered',
        expected_concept: q.expected_concept,
      }));

      const res = await trainerService.evaluateRepoViva({
        repo_context: `${repoAnalysis.owner}/${repoAnalysis.repo_name}`,
        answers: answersList,
      });
      setVivaEvaluationResult(res);
    } catch (err) {
      setRepoError('Viva evaluation failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setEvaluatingViva(false);
    }
  };

  // Run DevOps Verification
  const handleVerifyDevOps = async () => {
    setVerifyingDevops(true);
    try {
      const res = await trainerService.verifyDevOpsLab(selectedTask, devopsCode);
      setDevopsResult(res);
    } catch (err) {
      console.error('DevOps verification error:', err);
    } finally {
      setVerifyingDevops(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1180px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ fontSize: '11px', fontWeight: 800, color: '#4f46e5', textTransform: 'uppercase' }}>
              Phase 4 Advanced Features · Demonstration Suite
            </span>
          </div>
          <h1 style={{ fontSize: '26px', fontWeight: 800, color: '#0f172a', margin: '0 0 4px 0' }}>
            GitHub Repository Evaluation & DevOps Labs
          </h1>
          <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>
            Inspect student source repositories, conduct code structure viva evaluations, and complete isolated DevOps laboratory tasks.
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
          ← Back to Trainer View
        </button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '2px solid #e2e8f0', paddingBottom: '2px' }}>
        <button
          onClick={() => setActiveTab('github_eval')}
          style={{
            padding: '10px 18px',
            borderRadius: '8px 8px 0 0',
            border: 'none',
            backgroundColor: activeTab === 'github_eval' ? '#ffffff' : 'transparent',
            color: activeTab === 'github_eval' ? '#4f46e5' : '#64748b',
            fontWeight: 800,
            fontSize: '14px',
            cursor: 'pointer',
            borderBottom: activeTab === 'github_eval' ? '3px solid #4f46e5' : '3px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <GitBranch size={16} /> GitHub Repository Evaluation & Viva
        </button>

        <button
          onClick={() => setActiveTab('devops_lab')}
          style={{
            padding: '10px 18px',
            borderRadius: '8px 8px 0 0',
            border: 'none',
            backgroundColor: activeTab === 'devops_lab' ? '#ffffff' : 'transparent',
            color: activeTab === 'devops_lab' ? '#4f46e5' : '#64748b',
            fontWeight: 800,
            fontSize: '14px',
            cursor: 'pointer',
            borderBottom: activeTab === 'devops_lab' ? '3px solid #4f46e5' : '3px solid transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <Terminal size={16} /> Browser-Based DevOps Labs
        </button>
      </div>

      {/* ========================================================================= */}
      {/* VIEW 1: GITHUB REPO EVALUATION & VIVA (SECTIONS 14 & 15) */}
      {/* ========================================================================= */}
      {activeTab === 'github_eval' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Repo Input Box */}
          <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '24px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: '0 0 8px 0' }}>
              Connect & Analyze Public GitHub Repository
            </h3>
            <p style={{ margin: '0 0 16px 0', fontSize: '13px', color: '#64748b' }}>
              The backend safely inspects tree structures, architecture patterns, concepts demonstrated, and flags potential line-level issues.
            </p>

            <form onSubmit={handleAnalyzeRepo} style={{ display: 'flex', gap: '10px' }}>
              <input
                type="text"
                placeholder="https://github.com/owner/repository"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                style={{
                  flex: 1,
                  padding: '10px 14px',
                  borderRadius: '8px',
                  border: '1px solid #cbd5e1',
                  fontSize: '14px',
                }}
              />
              <button
                type="submit"
                disabled={analyzingRepo}
                style={{
                  padding: '10px 22px',
                  backgroundColor: '#0f172a',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: 700,
                  fontSize: '14px',
                  cursor: analyzingRepo ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                {analyzingRepo ? <Sparkles size={16} style={{ animation: 'spin 1s infinite' }} /> : <GitBranch size={16} />}
                {analyzingRepo ? 'Inspecting Repo...' : 'Analyze Repository'}
              </button>
            </form>

            {repoError && (
              <div style={{ marginTop: '14px', padding: '10px 14px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#991b1b', fontSize: '13px' }}>
                {repoError}
              </div>
            )}
          </div>

          {/* Analysis Results */}
          {repoAnalysis && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Overview Metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px' }}>
                <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>Repository</div>
                  <div style={{ fontSize: '16px', fontWeight: 800, color: '#0f172a', marginTop: '4px' }}>
                    {repoAnalysis.owner}/{repoAnalysis.repo_name}
                  </div>
                </div>

                <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>Detected Languages</div>
                  <div style={{ fontSize: '15px', fontWeight: 800, color: '#4f46e5', marginTop: '4px' }}>
                    {repoAnalysis.detected_languages?.join(', ') || 'Python'}
                  </div>
                </div>

                <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>Files Sampled</div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: '#0f172a', marginTop: '2px' }}>
                    {repoAnalysis.file_count} files
                  </div>
                </div>

                <div style={{ backgroundColor: '#ffffff', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>Quality Badges</div>
                  <div style={{ display: 'flex', gap: '4px', marginTop: '4px', flexWrap: 'wrap' }}>
                    {repoAnalysis.has_tests && (
                      <span style={{ fontSize: '10px', fontWeight: 800, backgroundColor: '#dcfce7', color: '#166534', padding: '1px 6px', borderRadius: '4px' }}>
                        Tests
                      </span>
                    )}
                    {repoAnalysis.has_docker && (
                      <span style={{ fontSize: '10px', fontWeight: 800, backgroundColor: '#e0e7ff', color: '#4338ca', padding: '1px 6px', borderRadius: '4px' }}>
                        Docker
                      </span>
                    )}
                    {repoAnalysis.has_readme && (
                      <span style={{ fontSize: '10px', fontWeight: 800, backgroundColor: '#f1f5f9', color: '#334155', padding: '1px 6px', borderRadius: '4px' }}>
                        README
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Concepts Demonstrated & Line-Level Findings */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '20px' }}>
                  <h4 style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a', margin: '0 0 12px 0' }}>
                    Concepts Demonstrated in Repository
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {repoAnalysis.concepts_demonstrated?.map((concept, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: '#166534', backgroundColor: '#f0fdf4', padding: '8px 12px', borderRadius: '6px' }}>
                        <CheckCircle2 size={16} /> {concept}
                      </div>
                    ))}
                  </div>
                </div>

                <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '20px' }}>
                  <h4 style={{ fontSize: '15px', fontWeight: 800, color: '#0f172a', margin: '0 0 12px 0' }}>
                    Line-Level Observations & Recommendations
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {repoAnalysis.code_findings?.map((finding, i) => (
                      <div key={i} style={{ padding: '10px 12px', borderRadius: '6px', border: '1px solid #e2e8f0', backgroundColor: '#f8fafc' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                          <span style={{ fontWeight: 800, fontSize: '12px', color: '#0f172a' }}>
                            {finding.file} : Line {finding.line}
                          </span>
                          <span style={{ fontSize: '10px', fontWeight: 800, color: finding.severity === 'SUGGESTION' ? '#ea580c' : '#2563eb' }}>
                            {finding.category}
                          </span>
                        </div>
                        <div style={{ fontSize: '12px', color: '#475569' }}>{finding.observation}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Section 15: Repository Viva Voce */}
              <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <Sparkles size={18} color="#7c3aed" />
                  <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                    Repository Viva Voce (Section 15)
                  </h3>
                </div>
                <p style={{ margin: '0 0 20px 0', fontSize: '13px', color: '#64748b' }}>
                  Answer the synthesized architectural questions based on this repository. AI will evaluate whether your comprehension matches the implementation.
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {repoAnalysis.viva_questions?.map((vq) => (
                    <div key={vq.id} style={{ border: '1px solid #e2e8f0', borderRadius: '10px', padding: '16px', backgroundColor: '#f8fafc' }}>
                      <div style={{ fontWeight: 700, fontSize: '13px', color: '#0f172a', marginBottom: '4px' }}>
                        Question {vq.id}: {vq.question}
                      </div>
                      <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '8px' }}>
                        Target Concept: <em>{vq.expected_concept}</em>
                      </div>
                      <textarea
                        rows={2}
                        placeholder="Type your explanation here..."
                        value={vivaAnswers[vq.id] || ''}
                        onChange={(e) => setVivaAnswers({ ...vivaAnswers, [vq.id]: e.target.value })}
                        style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '13px', boxSizing: 'border-box' }}
                      />
                    </div>
                  ))}

                  <div style={{ textAlign: 'right' }}>
                    <button
                      onClick={handleSubmitViva}
                      disabled={evaluatingViva}
                      style={{
                        padding: '10px 24px',
                        backgroundColor: '#7c3aed',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: '8px',
                        fontWeight: 700,
                        fontSize: '13px',
                        cursor: evaluatingViva ? 'not-allowed' : 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                    >
                      {evaluatingViva ? 'Evaluating Answers...' : 'Submit Viva Voce for AI Evaluation'}
                    </button>
                  </div>

                  {/* Viva Evaluation Feedback */}
                  {vivaEvaluationResult && (
                    <div style={{ marginTop: '16px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '10px', padding: '18px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                        <h4 style={{ fontSize: '16px', fontWeight: 800, color: '#166534', margin: 0 }}>
                          Viva Voce Evaluation Results
                        </h4>
                        <span style={{ fontSize: '16px', fontWeight: 800, backgroundColor: '#166534', color: '#ffffff', padding: '4px 12px', borderRadius: '6px' }}>
                          Score: {vivaEvaluationResult.overall_score} / 10
                        </span>
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        {vivaEvaluationResult.evaluations?.map((ev, idx) => (
                          <div key={idx} style={{ backgroundColor: '#ffffff', padding: '12px', borderRadius: '8px', border: '1px solid #dcfce7' }}>
                            <div style={{ fontWeight: 700, fontSize: '13px', color: '#0f172a', marginBottom: '4px' }}>
                              Q: {ev.question}
                            </div>
                            <div style={{ fontSize: '12px', color: '#166534', fontWeight: 600 }}>
                              Score: {ev.score}/10 · {ev.evaluation}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* VIEW 2: BROWSER-BASED DEVOPS LABS (SECTION 16) */}
      {/* ========================================================================= */}
      {activeTab === 'devops_lab' && (
        <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: '20px' }}>
          {/* Task Selector Sidebar */}
          <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '18px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span style={{ fontSize: '11px', fontWeight: 800, color: '#64748b', textTransform: 'uppercase', marginBottom: '4px' }}>
              Select Laboratory Task
            </span>

            <button
              onClick={() => handleSelectDevOpsTask('dockerfile_basic')}
              style={{
                textAlign: 'left',
                padding: '12px',
                borderRadius: '8px',
                border: selectedTask === 'dockerfile_basic' ? '2px solid #4f46e5' : '1px solid #e2e8f0',
                backgroundColor: selectedTask === 'dockerfile_basic' ? '#eef2ff' : '#f8fafc',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 800, fontSize: '13px', color: '#0f172a' }}>Task 1: Basic Dockerfile</div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>FastAPI runtime packaging</div>
            </button>

            <button
              onClick={() => handleSelectDevOpsTask('dockerfile_multistage')}
              style={{
                textAlign: 'left',
                padding: '12px',
                borderRadius: '8px',
                border: selectedTask === 'dockerfile_multistage' ? '2px solid #4f46e5' : '1px solid #e2e8f0',
                backgroundColor: selectedTask === 'dockerfile_multistage' ? '#eef2ff' : '#f8fafc',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 800, fontSize: '13px', color: '#0f172a' }}>Task 2: Multi-Stage Build</div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>Non-root security hardening</div>
            </button>

            <button
              onClick={() => handleSelectDevOpsTask('ci_workflow')}
              style={{
                textAlign: 'left',
                padding: '12px',
                borderRadius: '8px',
                border: selectedTask === 'ci_workflow' ? '2px solid #4f46e5' : '1px solid #e2e8f0',
                backgroundColor: selectedTask === 'ci_workflow' ? '#eef2ff' : '#f8fafc',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 800, fontSize: '13px', color: '#0f172a' }}>Task 3: GitHub Actions CI</div>
              <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>Automated test pipeline</div>
            </button>

            <div style={{ marginTop: 'auto', padding: '12px', backgroundColor: '#f1f5f9', borderRadius: '8px', fontSize: '11px', color: '#475569', lineHeight: '1.4' }}>
              🔒 <strong>Safe Sandbox Verification</strong>: Directives and syntax are evaluated via AST structure analysis without executing arbitrary root commands.
            </div>
          </div>

          {/* Editor & Verification Output */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '1px solid #e2e8f0', padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
                    DevOps Configuration Editor
                  </h3>
                  <span style={{ fontSize: '12px', color: '#64748b' }}>
                    {selectedTask === 'ci_workflow' ? '.github/workflows/ci.yml' : 'Dockerfile'}
                  </span>
                </div>

                <button
                  onClick={handleVerifyDevOps}
                  disabled={verifyingDevops}
                  style={{
                    padding: '8px 18px',
                    backgroundColor: '#16a34a',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '8px',
                    fontWeight: 700,
                    fontSize: '13px',
                    cursor: verifyingDevops ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <Play size={14} /> {verifyingDevops ? 'Verifying...' : 'Verify Configuration'}
                </button>
              </div>

              <textarea
                rows={16}
                value={devopsCode}
                onChange={(e) => setDevopsCode(e.target.value)}
                style={{
                  width: '100%',
                  fontFamily: 'monospace',
                  fontSize: '13px',
                  padding: '14px',
                  borderRadius: '8px',
                  border: '1px solid #cbd5e1',
                  backgroundColor: '#0f172a',
                  color: '#f8fafc',
                  lineHeight: '1.5',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            {/* Verification Result Card */}
            {devopsResult && (
              <div
                style={{
                  backgroundColor: devopsResult.all_passed ? '#f0fdf4' : '#fffbeb',
                  borderRadius: '12px',
                  border: `1px solid ${devopsResult.all_passed ? '#bbf7d0' : '#fde68a'}`,
                  padding: '20px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {devopsResult.all_passed ? (
                      <CheckCircle2 size={20} color="#16a34a" />
                    ) : (
                      <AlertTriangle size={20} color="#d97706" />
                    )}
                    <span style={{ fontWeight: 800, fontSize: '15px', color: devopsResult.all_passed ? '#166534' : '#92400e' }}>
                      {devopsResult.all_passed ? 'Task Complete — All Directives Verified' : 'Incomplete Verification'}
                    </span>
                  </div>
                  <span
                    style={{
                      fontSize: '14px',
                      fontWeight: 800,
                      backgroundColor: devopsResult.all_passed ? '#16a34a' : '#d97706',
                      color: '#ffffff',
                      padding: '4px 12px',
                      borderRadius: '6px',
                    }}
                  >
                    Score: {devopsResult.score}% ({devopsResult.passed_checks}/{devopsResult.total_checks})
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {devopsResult.checks?.map((check, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '8px 12px',
                        borderRadius: '6px',
                        backgroundColor: '#ffffff',
                        border: '1px solid #e2e8f0',
                        fontSize: '12px',
                      }}
                    >
                      <span style={{ fontWeight: 600, color: '#1e293b' }}>{check.check}</span>
                      <span
                        style={{
                          fontWeight: 800,
                          fontSize: '11px',
                          color: check.passed ? '#16a34a' : '#dc2626',
                        }}
                      >
                        {check.passed ? '✓ PASSED' : '✗ FAILED'}
                      </span>
                    </div>
                  ))}
                </div>

                <div style={{ marginTop: '12px', fontSize: '12px', color: '#475569' }}>
                  <strong>Feedback:</strong> {devopsResult.feedback}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
