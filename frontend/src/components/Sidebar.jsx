import React from 'react';
import { NavLink } from 'react-router-dom';
import { authService } from '../services/authService';
import {
  LayoutDashboard,
  GitFork,
  Sparkles,
  Users,
  Code2,
  ShieldAlert,
  FolderTree,
  GitBranch,
} from 'lucide-react';

export default function Sidebar() {
  const user = authService.getCurrentUser();
  const isTrainer = user?.role === 'TRAINER';

  const linkStyle = ({ isActive }) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '10px 16px',
    borderRadius: '8px',
    textDecoration: 'none',
    fontSize: '14px',
    fontWeight: isActive ? 700 : 500,
    color: isActive ? '#4f46e5' : '#4b5563',
    backgroundColor: isActive ? '#eef2ff' : 'transparent',
    transition: 'all 0.15s ease',
  });

  return (
    <aside
      style={{
        width: '240px',
        backgroundColor: '#ffffff',
        borderRight: '1px solid #e5e7eb',
        display: 'flex',
        flexDirection: 'column',
        padding: '20px 16px',
        gap: '24px',
      }}
    >
      {/* Student Navigation - visible only to Students */}
      {!isTrainer && (
        <div>
          <div
            style={{
              fontSize: '11px',
              fontWeight: 700,
              color: '#9ca3af',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              padding: '0 16px',
              marginBottom: '8px',
            }}
          >
            Student Learning
          </div>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <NavLink to="/student/dashboard" style={linkStyle}>
              <LayoutDashboard size={18} />
              Learning Dashboard
            </NavLink>
            <NavLink to="/student/concept-map" style={linkStyle}>
              <GitFork size={18} />
              Visual Concept Map
            </NavLink>
            <NavLink to="/student/learning" style={linkStyle}>
              <Sparkles size={18} />
              Adaptive Practice
            </NavLink>
            <NavLink to="/student/assessment" style={linkStyle}>
              <Code2 size={18} />
              Coding Assessment
            </NavLink>
          </nav>
        </div>
      )}

      {/* Trainer Navigation - visible only to Trainers */}
      {isTrainer && (
        <div>
          <div
            style={{
              fontSize: '11px',
              fontWeight: 700,
              color: '#9ca3af',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              padding: '0 16px',
              marginBottom: '8px',
            }}
          >
            Teacher / Trainer Portal
          </div>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <NavLink to="/trainer/dashboard" style={linkStyle}>
              <Users size={18} />
              Cohort Overview
            </NavLink>
            <NavLink to="/trainer/integrity" style={linkStyle}>
              <ShieldAlert size={18} />
              Integrity Dashboard
            </NavLink>
            <NavLink to="/trainer/curriculum" style={linkStyle}>
              <FolderTree size={18} />
              Course & Question Bank
            </NavLink>
            <NavLink to="/trainer/repo-eval" style={linkStyle}>
              <GitBranch size={18} />
              Repo Eval & DevOps
            </NavLink>
          </nav>
        </div>
      )}

      {/* Course Context Card */}
      <div
        style={{
          marginTop: 'auto',
          backgroundColor: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: '10px',
          padding: '12px 14px',
        }}
      >
        <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>
          Active Course
        </div>
        <div style={{ fontSize: '13px', fontWeight: 800, color: '#1e293b', marginTop: '4px' }}>
          Object Oriented Programming
        </div>
        <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>
          5 Modules · 7 Concepts (DAG)
        </div>
      </div>
    </aside>
  );
}
