import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import { Lock, Mail, User, Sparkles, GraduationCap, ShieldCheck } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const [activeRole, setActiveRole] = useState('STUDENT'); // 'STUDENT' or 'TRAINER'
  const [isRegistering, setIsRegistering] = useState(false);

  // Form fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('student.a@adaptive.edu');
  const [password, setPassword] = useState('student123');
  const [targetSubject, setTargetSubject] = useState('Data Structures');
  const [department, setDepartment] = useState('Computer Science');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleAuth = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError('');
    setSuccessMsg('');

    try {
      if (isRegistering) {
        if (!name.trim()) {
          setError('Please enter your full name.');
          setLoading(false);
          return;
        }
        const data = await authService.register(name, email, password, activeRole);
        setSuccessMsg('Account created successfully! Redirecting...');
        setTimeout(() => {
          if (data.user.role === 'TRAINER') {
            navigate('/trainer/dashboard');
          } else {
            navigate('/student/dashboard');
          }
        }, 600);
      } else {
        const data = await authService.login(email, password);
        if (data.user.role === 'TRAINER') {
          navigate('/trainer/dashboard');
        } else {
          navigate('/student/dashboard');
        }
      }
    } catch (err) {
      if (!err.response) {
        setError('Cannot connect to backend server. Ensure backend is running on http://localhost:8000.');
      } else {
        setError(err.response?.data?.detail || 'Authentication failed. Please check your credentials.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRoleSwitch = (role) => {
    setActiveRole(role);
    setError('');
    setSuccessMsg('');
    if (role === 'STUDENT') {
      setEmail('student.a@adaptive.edu');
      setPassword('student123');
    } else {
      setEmail('trainer@adaptive.edu');
      setPassword('trainer123');
    }
  };

  const setDemoAccount = (demoEmail, demoPass, role) => {
    setActiveRole(role);
    setIsRegistering(false);
    setEmail(demoEmail);
    setPassword(demoPass);
    setError('');
    setSuccessMsg('');
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
          maxWidth: '520px',
          backgroundColor: '#ffffff',
          borderRadius: '20px',
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.05)',
          border: '1px solid #e2e8f0',
          padding: '36px',
        }}
      >
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div
            style={{
              width: '52px',
              height: '52px',
              borderRadius: '14px',
              backgroundColor: activeRole === 'STUDENT' ? '#4f46e5' : '#059669',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              fontWeight: 800,
              fontSize: '26px',
              marginBottom: '12px',
              transition: 'background-color 0.2s',
            }}
          >
            {activeRole === 'STUDENT' ? <GraduationCap size={28} /> : <ShieldCheck size={28} />}
          </div>
          <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a', margin: '0 0 6px 0' }}>
            Adaptive Learning Portal
          </h1>
          <p style={{ fontSize: '14px', color: '#64748b', margin: 0 }}>
            {activeRole === 'STUDENT'
              ? 'Student Portal · Knowledge Tracing & Concept-Based Practice'
              : 'Teacher Portal · Curriculum Management & Cohort Analytics'}
          </p>
        </div>

        {/* Role Separation Tabs: Student vs Teacher */}
        <div
          style={{
            display: 'flex',
            backgroundColor: '#f1f5f9',
            borderRadius: '12px',
            padding: '4px',
            marginBottom: '20px',
          }}
        >
          <button
            type="button"
            onClick={() => handleRoleSwitch('STUDENT')}
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '10px 14px',
              borderRadius: '10px',
              border: 'none',
              backgroundColor: activeRole === 'STUDENT' ? '#ffffff' : 'transparent',
              color: activeRole === 'STUDENT' ? '#4f46e5' : '#64748b',
              fontWeight: activeRole === 'STUDENT' ? 800 : 600,
              fontSize: '14px',
              cursor: 'pointer',
              boxShadow: activeRole === 'STUDENT' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
              transition: 'all 0.15s',
            }}
          >
            <GraduationCap size={16} />
            Student Portal
          </button>
          <button
            type="button"
            onClick={() => handleRoleSwitch('TRAINER')}
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              padding: '10px 14px',
              borderRadius: '10px',
              border: 'none',
              backgroundColor: activeRole === 'TRAINER' ? '#ffffff' : 'transparent',
              color: activeRole === 'TRAINER' ? '#059669' : '#64748b',
              fontWeight: activeRole === 'TRAINER' ? 800 : 600,
              fontSize: '14px',
              cursor: 'pointer',
              boxShadow: activeRole === 'TRAINER' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
              transition: 'all 0.15s',
            }}
          >
            <ShieldCheck size={16} />
            Teacher / Trainer
          </button>
        </div>

        {/* Mode Toggle: Sign In vs Register */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', marginBottom: '20px' }}>
          <button
            type="button"
            onClick={() => { setIsRegistering(false); setError(''); setSuccessMsg(''); }}
            style={{
              background: 'none',
              border: 'none',
              padding: '6px 12px',
              fontSize: '13px',
              fontWeight: !isRegistering ? 800 : 600,
              color: !isRegistering ? (activeRole === 'STUDENT' ? '#4f46e5' : '#059669') : '#64748b',
              borderBottom: !isRegistering ? `2px solid ${activeRole === 'STUDENT' ? '#4f46e5' : '#059669'}` : '2px solid transparent',
              cursor: 'pointer',
            }}
          >
            {activeRole === 'STUDENT' ? 'Student Sign In' : 'Teacher Sign In'}
          </button>
          <button
            type="button"
            onClick={() => { setIsRegistering(true); setError(''); setSuccessMsg(''); }}
            style={{
              background: 'none',
              border: 'none',
              padding: '6px 12px',
              fontSize: '13px',
              fontWeight: isRegistering ? 800 : 600,
              color: isRegistering ? (activeRole === 'STUDENT' ? '#4f46e5' : '#059669') : '#64748b',
              borderBottom: isRegistering ? `2px solid ${activeRole === 'STUDENT' ? '#4f46e5' : '#059669'}` : '2px solid transparent',
              cursor: 'pointer',
            }}
          >
            {activeRole === 'STUDENT' ? 'Student Register' : 'Teacher Register'}
          </button>
        </div>

        {/* Demo Accounts Quick-Fill Box (Only on Sign In) */}
        {!isRegistering && (
          <div
            style={{
              backgroundColor: '#f8fafc',
              borderRadius: '12px',
              padding: '12px 14px',
              marginBottom: '20px',
              border: '1px solid #e2e8f0',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
              <Sparkles size={14} color={activeRole === 'STUDENT' ? '#4f46e5' : '#059669'} />
              <span style={{ fontSize: '11px', fontWeight: 700, color: '#334155', textTransform: 'uppercase' }}>
                Quick Demo Access (Click to Load)
              </span>
            </div>
            {activeRole === 'STUDENT' ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setDemoAccount('student.a@adaptive.edu', 'student123', 'STUDENT')}
                  style={{
                    textAlign: 'left',
                    padding: '8px 10px',
                    borderRadius: '8px',
                    backgroundColor: email === 'student.a@adaptive.edu' ? '#e0e7ff' : '#ffffff',
                    border: email === 'student.a@adaptive.edu' ? '1.5px solid #4f46e5' : '1px solid #cbd5e1',
                    fontSize: '11px',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ fontWeight: 800, color: '#1e293b' }}>Student A (Alice)</div>
                  <div style={{ color: '#4338ca', fontSize: '10px' }}>Binary Search: 38% (Weak)</div>
                </button>

                <button
                  type="button"
                  onClick={() => setDemoAccount('student.b@adaptive.edu', 'student123', 'STUDENT')}
                  style={{
                    textAlign: 'left',
                    padding: '8px 10px',
                    borderRadius: '8px',
                    backgroundColor: email === 'student.b@adaptive.edu' ? '#e0e7ff' : '#ffffff',
                    border: email === 'student.b@adaptive.edu' ? '1.5px solid #4f46e5' : '1px solid #cbd5e1',
                    fontSize: '11px',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ fontWeight: 800, color: '#1e293b' }}>Student B (Bob)</div>
                  <div style={{ color: '#4338ca', fontSize: '10px' }}>Target: Basics / Classes</div>
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setDemoAccount('trainer@adaptive.edu', 'trainer123', 'TRAINER')}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  backgroundColor: '#d1fae5',
                  border: '1.5px solid #059669',
                  fontSize: '12px',
                  cursor: 'pointer',
                }}
              >
                <div style={{ fontWeight: 800, color: '#065f46' }}>Trainer (Dr. Alan Turing)</div>
                <div style={{ color: '#047857', fontSize: '11px' }}>Curriculum manager, student analytics & VIVA audits</div>
              </button>
            )}
          </div>
        )}

        {/* Error / Success Feedback */}
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
        {successMsg && (
          <div
            style={{
              padding: '12px',
              backgroundColor: '#ecfdf5',
              border: '1px solid #a7f3d0',
              borderRadius: '8px',
              color: '#065f46',
              fontSize: '13px',
              marginBottom: '18px',
            }}
          >
            {successMsg}
          </div>
        )}

        {/* Authentication Form */}
        <form onSubmit={handleAuth} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {isRegistering && (
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                Full Name
              </label>
              <input
                type="text"
                placeholder={activeRole === 'STUDENT' ? 'e.g. John Doe' : 'e.g. Prof. Jane Smith'}
                value={name}
                onChange={(e) => setName(e.target.value)}
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
          )}

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

          {isRegistering && activeRole === 'STUDENT' && (
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                Target Subject
              </label>
              <select
                value={targetSubject}
                onChange={(e) => setTargetSubject(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  border: '1px solid #cbd5e1',
                  fontSize: '14px',
                  boxSizing: 'border-box',
                  backgroundColor: '#ffffff',
                }}
              >
                <option value="Data Structures">Data Structures (Searching, Sorting, Linked Lists, Stack, Queue)</option>
                <option value="Object Oriented Programming">Object Oriented Programming (Classes, Objects, Inheritance)</option>
              </select>
            </div>
          )}

          {isRegistering && activeRole === 'TRAINER' && (
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                Academic Department
              </label>
              <input
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
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
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: '12px',
              borderRadius: '8px',
              backgroundColor: activeRole === 'STUDENT' ? '#4f46e5' : '#059669',
              color: '#ffffff',
              border: 'none',
              fontWeight: 800,
              fontSize: '14px',
              cursor: loading ? 'not-allowed' : 'pointer',
              marginTop: '6px',
              boxShadow: activeRole === 'STUDENT' ? '0 4px 12px rgba(79, 70, 229, 0.25)' : '0 4px 12px rgba(5, 150, 105, 0.25)',
              transition: 'background-color 0.2s',
            }}
          >
            {loading
              ? 'Authenticating...'
              : isRegistering
              ? `Register as ${activeRole === 'STUDENT' ? 'Student' : 'Teacher'}`
              : `Sign In to ${activeRole === 'STUDENT' ? 'Student Portal' : 'Teacher Portal'}`}
          </button>
        </form>
      </div>
    </div>
  );
}
