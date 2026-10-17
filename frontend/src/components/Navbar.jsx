import React from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import { LogOut, User, Sparkles } from 'lucide-react';
import AdaptiveLogo from './AdaptiveLogo';

export default function Navbar() {
  const navigate = useNavigate();
  const user = authService.getCurrentUser();

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  const handleQuickSwitch = async (email, password) => {
    try {
      await authService.login(email, password);
      window.location.reload();
    } catch (err) {
      console.error('Quick switch failed:', err);
    }
  };

  return (
    <header
      style={{
        height: '64px',
        backgroundColor: '#ffffff',
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }} onClick={() => navigate(user?.role === 'TRAINER' ? '/trainer/dashboard' : '/student/dashboard')}>
        <AdaptiveLogo size={36} />
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontWeight: 800, fontSize: '19px', color: '#0f172a', letterSpacing: '-0.02em' }}>
              Adapt<span style={{ color: '#4f46e5' }}>IQ</span>
            </span>
          </div>
        </div>
      </div>

      {/* Demo Student Differentiation Switcher */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
          Adaptive Demo Switch:
        </span>
        <button
          onClick={() => handleQuickSwitch('student.a@adaptive.edu', 'student123')}
          style={{
            fontSize: '12px',
            padding: '6px 12px',
            borderRadius: '6px',
            border: user?.email === 'student.a@adaptive.edu' ? '2px solid #4f46e5' : '1px solid #cbd5e1',
            backgroundColor: user?.email === 'student.a@adaptive.edu' ? '#eef2ff' : '#ffffff',
            color: user?.email === 'student.a@adaptive.edu' ? '#4338ca' : '#334155',
            fontWeight: 700,
            cursor: 'pointer',
          }}
          title="Classes 90, Objects 85, Constructors 40 -> Target: Constructors"
        >
          Student A (Target: Constructors)
        </button>
        <button
          onClick={() => handleQuickSwitch('student.b@adaptive.edu', 'student123')}
          style={{
            fontSize: '12px',
            padding: '6px 12px',
            borderRadius: '6px',
            border: user?.email === 'student.b@adaptive.edu' ? '2px solid #4f46e5' : '1px solid #cbd5e1',
            backgroundColor: user?.email === 'student.b@adaptive.edu' ? '#eef2ff' : '#ffffff',
            color: user?.email === 'student.b@adaptive.edu' ? '#4338ca' : '#334155',
            fontWeight: 700,
            cursor: 'pointer',
          }}
          title="Classes 40, Objects 30, Constructors 20 -> Target: Classes (Prerequisite)"
        >
          Student B (Target: Classes)
        </button>
        <button
          onClick={() => handleQuickSwitch('trainer@adaptive.edu', 'trainer123')}
          style={{
            fontSize: '12px',
            padding: '6px 12px',
            borderRadius: '6px',
            border: user?.role === 'TRAINER' ? '2px solid #059669' : '1px solid #cbd5e1',
            backgroundColor: user?.role === 'TRAINER' ? '#ecfdf5' : '#ffffff',
            color: user?.role === 'TRAINER' ? '#047857' : '#334155',
            fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          Trainer
        </button>
        {user?.role === 'TRAINER' && (
          <button
            onClick={() => navigate('/trainer/integrity')}
            style={{
              fontSize: '12px',
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid #dc2626',
              backgroundColor: '#fef2f2',
              color: '#dc2626',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Integrity Dashboard
          </button>
        )}
      </div>

      {/* User Info & Logout */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '13px', fontWeight: 800, color: '#0f172a' }}>{user.name}</div>
              <div style={{ fontSize: '11px', color: '#64748b' }}>
                <span
                  style={{
                    fontWeight: 700,
                    color: user.role === 'TRAINER' ? '#059669' : '#4f46e5',
                  }}
                >
                  {user.role}
                </span>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Logout"
              style={{
                background: '#f1f5f9',
                border: 'none',
                borderRadius: '8px',
                padding: '8px',
                color: '#475569',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <LogOut size={16} />
            </button>
          </div>
        ) : (
          <button
            onClick={() => navigate('/login')}
            style={{
              padding: '8px 16px',
              backgroundColor: '#4f46e5',
              color: '#ffffff',
              borderRadius: '8px',
              border: 'none',
              fontWeight: 700,
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            Sign In
          </button>
        )}
      </div>
    </header>
  );
}
