import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import StudentDashboard from './pages/StudentDashboard';
import ConceptMapPage from './pages/ConceptMapPage';
import AdaptiveLearningPage from './pages/AdaptiveLearningPage';
import CodingAssessmentPage from './pages/CodingAssessmentPage';
import ExplainCodePage from './pages/ExplainCodePage';
import TrainerDashboard from './pages/TrainerDashboard';
import TrainerStudentDetailPage from './pages/TrainerStudentDetailPage';
import SessionReplayPage from './pages/SessionReplayPage';
import CodingIntegrityDashboard from './pages/CodingIntegrityDashboard';
import { authService } from './services/authService';

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
          {children}
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

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
