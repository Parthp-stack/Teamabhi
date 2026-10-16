import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import { Lock, Mail, Sparkles } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('student.a@adaptive.edu');
  const [password, setPassword] = useState('student123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const data = await authService.login(email, password);
      if (data.user.role === 'TRAINER') {
        navigate('/trainer/dashboard');
      } else {
        navigate('/student/dashboard');
      }
    } catch (err) {
      if (!err.response) {
        setError('Cannot connect to backend server. Please make sure the backend is running on http://localhost:8000.');
      } else {
        setError(err.response?.data?.detail || 'Login failed. Please check your email and password.');
      }
    } finally {
      setLoading(false);
    }
  };

  const setDemoAccount = (demoEmail, demoPass) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError('');
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f8fafc',
        padding: '24px',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '480px',
          backgroundColor: '#ffffff',
          borderRadius: '16px',
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.05)',
          border: '1px solid #e2e8f0',
          padding: '36px',
        }}
      >
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              backgroundColor: '#4f46e5',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              fontWeight: 800,
              fontSize: '24px',
              marginBottom: '12px',
            }}
          >
            A
          </div>
          <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a', margin: '0 0 6px 0' }}>
            Adaptive Learning Portal
          </h1>
          <p style={{ fontSize: '14px', color: '#64748b', margin: 0 }}>
            Phase 2 · Prerequisite Knowledge Tracing & AI Engine
          </p>
        </div>

        {/* Demo Accounts Quick-Fill Box */}
        <div
          style={{
            backgroundColor: '#f1f5f9',
            borderRadius: '12px',
            padding: '14px',
            marginBottom: '24px',
            border: '1px solid #e2e8f0',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <Sparkles size={14} color="#4f46e5" />
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#334155', textTransform: 'uppercase' }}>
              Phase 2 Demo Accounts (Click to Load)
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '8px' }}>
            <button
              type="button"
              onClick={() => setDemoAccount('student.a@adaptive.edu', 'student123')}
              style={{
                textAlign: 'left',
                padding: '10px 12px',
                borderRadius: '8px',
                backgroundColor: email === 'student.a@adaptive.edu' ? '#e0e7ff' : '#ffffff',
                border: email === 'student.a@adaptive.edu' ? '1.5px solid #4f46e5' : '1px solid #cbd5e1',
                fontSize: '12px',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 800, color: '#1e293b' }}>Student A (Alice Walker)</div>
              <div style={{ color: '#4338ca', fontSize: '11px', fontWeight: 600 }}>
                Classes 90, Objects 85, Constructors 40 → Target: Constructors
              </div>
            </button>

            <button
              type="button"
              onClick={() => setDemoAccount('student.b@adaptive.edu', 'student123')}
              style={{
                textAlign: 'left',
                padding: '10px 12px',
                borderRadius: '8px',
                backgroundColor: email === 'student.b@adaptive.edu' ? '#e0e7ff' : '#ffffff',
                border: email === 'student.b@adaptive.edu' ? '1.5px solid #4f46e5' : '1px solid #cbd5e1',
                fontSize: '12px',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 800, color: '#1e293b' }}>Student B (Bob Martinez)</div>
              <div style={{ color: '#4338ca', fontSize: '11px', fontWeight: 600 }}>
                Classes 40, Objects 30, Constructors 20 → Target: Classes (Prerequisite)
              </div>
            </button>

            <button
              type="button"
              onClick={() => setDemoAccount('trainer@adaptive.edu', 'trainer123')}
              style={{
                textAlign: 'left',
                padding: '10px 12px',
                borderRadius: '8px',
                backgroundColor: email === 'trainer@adaptive.edu' ? '#d1fae5' : '#ffffff',
                border: email === 'trainer@adaptive.edu' ? '1.5px solid #059669' : '1px solid #cbd5e1',
                fontSize: '12px',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 800, color: '#065f46' }}>Trainer (Dr. Alan Turing)</div>
              <div style={{ color: '#047857', fontSize: '11px', fontWeight: 600 }}>
                Course concepts, cohort average mastery, weakest concepts
              </div>
            </button>
          </div>
        </div>

        {error && (
          <div
            style={{
              padding: '12px',
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '8px',
              color: '#991b1b',
              fontSize: '13px',
              marginBottom: '18px',
            }}
          >
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                border: '1px solid #cbd5e1',
                fontSize: '14px',
                boxSizing: 'border-box',
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                border: '1px solid #cbd5e1',
                fontSize: '14px',
                boxSizing: 'border-box',
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '12px',
              borderRadius: '8px',
              backgroundColor: '#4f46e5',
              color: '#ffffff',
              border: 'none',
              fontWeight: 700,
              fontSize: '14px',
              cursor: loading ? 'not-allowed' : 'pointer',
              marginTop: '6px',
            }}
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
