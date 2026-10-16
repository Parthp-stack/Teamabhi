import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import { Lock, Mail, User, Sparkles, CheckCircle2 } from 'lucide-react';

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
      setError(err.response?.data?.detail || 'Login failed. Please check credentials.');
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
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
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
            Knowledge Tracing & Sandbox Assessment Platform
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
              Hackathon Demo Quick Fill
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '6px' }}>
            <button
              type="button"
              onClick={() => setDemoAccount('student.a@adaptive.edu', 'student123')}
              style={{
                textAlign: 'left',
                padding: '8px 12px',
                borderRadius: '8px',
                backgroundColor: email === 'student.a@adaptive.edu' ? '#e0e7ff' : '#ffffff',
                border: email === 'student.a@adaptive.edu' ? '1.5px solid #4f46e5' : '1px solid #cbd5e1',
                fontSize: '12px',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 700, color: '#1e293b' }}>Student A (Alice Walker)</div>
              <div style={{ color: '#64748b', fontSize: '11px' }}>High in Classes/Objects · Weak in Polymorphism</div>
            </button>

            <button
              type="button"
              onClick={() => setDemoAccount('student.b@adaptive.edu', 'student123')}
              style={{
                textAlign: 'left',
                padding: '8px 12px',
                borderRadius: '8px',
                backgroundColor: email === 'student.b@adaptive.edu' ? '#e0e7ff' : '#ffffff',
                border: email === 'student.b@adaptive.edu' ? '1.5px solid #4f46e5' : '1px solid #cbd5e1',
                fontSize: '12px',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 700, color: '#1e293b' }}>Student B (Bob Martinez)</div>
              <div style={{ color: '#64748b', fontSize: '11px' }}>Mastered through Polymorphism · Targets Dependency Injection</div>
            </button>

            <button
              type="button"
              onClick={() => setDemoAccount('trainer@adaptive.edu', 'trainer123')}
              style={{
                textAlign: 'left',
                padding: '8px 12px',
                borderRadius: '8px',
                backgroundColor: email === 'trainer@adaptive.edu' ? '#d1fae5' : '#ffffff',
                border: email === 'trainer@adaptive.edu' ? '1.5px solid #059669' : '1px solid #cbd5e1',
                fontSize: '12px',
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 700, color: '#065f46' }}>Trainer (Dr. Alan Turing)</div>
              <div style={{ color: '#64748b', fontSize: '11px' }}>Access cohort analytics, integrity evidence, and code replays</div>
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
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
              Email Address
            </label>
            <div style={{ position: 'relative' }}>
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
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
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
              marginTop: '8px',
              transition: 'background-color 0.2s',
            }}
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
