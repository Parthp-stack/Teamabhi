import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import ResetPasswordPage from './pages/ResetPasswordPage';
import StudentDashboard from './pages/StudentDashboard';
import ConceptMapPage from './pages/ConceptMapPage';
import AdaptiveLearningPage from './pages/AdaptiveLearningPage';
import CodingAssessmentPage from './pages/CodingAssessmentPage';
import ExplainCodePage from './pages/ExplainCodePage';
import TrainerDashboard from './pages/TrainerDashboard';
import TrainerStudentDetailPage from './pages/TrainerStudentDetailPage';
import SessionReplayPage from './pages/SessionReplayPage';
import CodingIntegrityDashboard from './pages/CodingIntegrityDashboard';
import CurriculumManagementPage from './pages/CurriculumManagementPage';
import RepoEvaluationDevOpsPage from './pages/RepoEvaluationDevOpsPage';
import { authService } from './services/authService';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '40px', maxWidth: '600px', margin: '40px auto', backgroundColor: '#ffffff', borderRadius: '12px', border: '1px solid #fecaca', boxShadow: '0 4px 6px rgba(0,0,0,0.05)' }}>
          <h2 style={{ color: '#dc2626', fontSize: '18px', fontWeight: 800, marginTop: 0 }}>An unexpected error occurred</h2>
          <p style={{ color: '#64748b', fontSize: '14px', lineHeight: '1.5' }}>
            {this.state.error?.message || "Something went wrong while rendering this section."}
          </p>
          <button
            onClick={() => { this.setState({ hasError: false }); window.location.reload(); }}
            style={{ padding: '8px 16px', backgroundColor: '#4f46e5', color: '#ffffff', border: 'none', borderRadius: '6px', fontWeight: 700, cursor: 'pointer' }}
          >
            Reload Page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

// Layout wrapper for authenticated views
function AppLayout({ children }) {
  const user = authService.getCurrentUser();
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#f8fafc' }}>
      <Navbar />
      <div style={{ display: 'flex', flex: 1 }}>
        <Sidebar />
        <main style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}

// Protected Trainer Route wrapper
function TrainerRoute({ children }) {
  const user = authService.getCurrentUser();
  if (!user || user.role !== 'TRAINER') {
    return <Navigate to="/student/dashboard" replace />;
  }
  return children;
}

export default function App() {
  const user = authService.getCurrentUser();

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />

        {/* Default route redirect */}
        <Route
          path="/"
          element={
            user ? (
              user.role === 'TRAINER' ? (
                <Navigate to="/trainer/dashboard" replace />
              ) : (
                <Navigate to="/student/dashboard" replace />
              )
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />

        {/* Student Routes */}
        <Route
          path="/student/dashboard"
          element={
            <AppLayout>
              <StudentDashboard />
            </AppLayout>
          }
        />
        <Route
          path="/student/concept-map"
          element={
            <AppLayout>
              <ConceptMapPage />
            </AppLayout>
          }
        />
        <Route
          path="/student/learning"
          element={
            <AppLayout>
              <AdaptiveLearningPage />
            </AppLayout>
          }
        />
        <Route
          path="/student/assessment"
          element={
            <AppLayout>
              <CodingAssessmentPage />
            </AppLayout>
          }
        />
        <Route
          path="/student/explain/:submissionId"
          element={
            <AppLayout>
              <ExplainCodePage />
            </AppLayout>
          }
        />
        <Route
          path="/student/integrity"
          element={
            <AppLayout>
              <CodingIntegrityDashboard isStudentView={true} />
            </AppLayout>
          }
        />

        {/* Trainer Routes */}
        <Route
          path="/trainer/dashboard"
          element={
            <AppLayout>
              <TrainerRoute>
                <TrainerDashboard />
              </TrainerRoute>
            </AppLayout>
          }
        />
        <Route
          path="/trainer/student/:id"
          element={
            <AppLayout>
              <TrainerRoute>
                <TrainerStudentDetailPage />
              </TrainerRoute>
            </AppLayout>
          }
        />
        <Route
          path="/trainer/replay/:sessionId"
          element={
            <AppLayout>
              <TrainerRoute>
                <SessionReplayPage />
              </TrainerRoute>
            </AppLayout>
          }
        />
        <Route
          path="/trainer/integrity"
          element={
            <AppLayout>
              <TrainerRoute>
                <CodingIntegrityDashboard />
              </TrainerRoute>
            </AppLayout>
          }
        />
        <Route
          path="/trainer/curriculum"
          element={
            <AppLayout>
              <TrainerRoute>
                <CurriculumManagementPage />
              </TrainerRoute>
            </AppLayout>
          }
        />
        <Route
          path="/trainer/repo-eval"
          element={
            <AppLayout>
              <TrainerRoute>
                <RepoEvaluationDevOpsPage />
              </TrainerRoute>
            </AppLayout>
          }
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
