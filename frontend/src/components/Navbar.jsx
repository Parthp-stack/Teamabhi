import React from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import { LogOut, User, ShieldCheck, Zap } from 'lucide-react';

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
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            backgroundColor: '#4f46e5',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#ffffff',
            fontWeight: 800,
            fontSize: '18px',
          }}
        >
          A
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontWeight: 800, fontSize: '18px', color: '#111827', letterSpacing: '-0.02em' }}>
              AdaptivePortal
            </span>
            <span
              style={{
                fontSize: '10px',
                fontWeight: 700,
                backgroundColor: '#e0e7ff',
                color: '#4338ca',
                padding: '2px 8px',
                borderRadius: '12px',
                textTransform: 'uppercase',
              }}
            >
              Bayesian AI Sandbox
            </span>
          </div>
        </div>
      </div>

      {/* Demo Account Quick Switcher */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '11px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase' }}>
          Demo Switch:
        </span>
        <button
          onClick={() => handleQuickSwitch('student.a@adaptive.edu', 'student123')}
          style={{
            fontSize: '12px',
            padding: '5px 10px',
            borderRadius: '6px',
            border: user?.email === 'student.a@adaptive.edu' ? '2px solid #4f46e5' : '1px solid #d1d5db',
            backgroundColor: user?.email === 'student.a@adaptive.edu' ? '#eef2ff' : '#ffffff',
            color: user?.email === 'student.a@adaptive.edu' ? '#4338ca' : '#374151',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Student A (Weak)
        </button>
        <button
          onClick={() => handleQuickSwitch('student.b@adaptive.edu', 'student123')}
          style={{
            fontSize: '12px',
            padding: '5px 10px',
            borderRadius: '6px',
            border: user?.email === 'student.b@adaptive.edu' ? '2px solid #4f46e5' : '1px solid #d1d5db',
            backgroundColor: user?.email === 'student.b@adaptive.edu' ? '#eef2ff' : '#ffffff',
            color: user?.email === 'student.b@adaptive.edu' ? '#4338ca' : '#374151',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Student B (Advanced)
        </button>
        <button
          onClick={() => handleQuickSwitch('trainer@adaptive.edu', 'trainer123')}
          style={{
            fontSize: '12px',
            padding: '5px 10px',
            borderRadius: '6px',
            border: user?.role === 'TRAINER' ? '2px solid #059669' : '1px solid #d1d5db',
            backgroundColor: user?.role === 'TRAINER' ? '#ecfdf5' : '#ffffff',
            color: user?.role === 'TRAINER' ? '#047857' : '#374151',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Trainer
        </button>
      </div>

      {/* User Info & Logout */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {user ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#111827' }}>{user.name}</div>
              <div style={{ fontSize: '11px', color: '#6b7280' }}>
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
                background: '#f3f4f6',
                border: 'none',
                borderRadius: '8px',
                padding: '8px',
                color: '#4b5563',
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
              fontWeight: 600,
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
