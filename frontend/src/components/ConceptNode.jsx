import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Award, BookOpen, AlertTriangle, Lock } from 'lucide-react';

const statusConfig = {
  MASTERED: {
    bg: '#ecfdf5',
    border: '#10b981',
    text: '#065f46',
    badgeBg: '#10b981',
    icon: Award,
    label: 'Mastered',
  },
  LEARNING: {
    bg: '#eff6ff',
    border: '#3b82f6',
    text: '#1e40af',
    badgeBg: '#3b82f6',
    icon: BookOpen,
    label: 'Learning',
  },
  WEAK: {
    bg: '#fffbeb',
    border: '#f59e0b',
    text: '#92400e',
    badgeBg: '#f59e0b',
    icon: AlertTriangle,
    label: 'Needs Practice',
  },
  LOCKED: {
    bg: '#f3f4f6',
    border: '#9ca3af',
    text: '#4b5563',
    badgeBg: '#6b7280',
    icon: Lock,
    label: 'Locked',
  },
};

function ConceptNode({ data, selected }) {
  const cfg = statusConfig[data.status] || statusConfig.LEARNING;
  const IconComponent = cfg.icon;

  return (
    <div
      style={{
        padding: '14px 18px',
        borderRadius: '12px',
        backgroundColor: cfg.bg,
        border: `2px solid ${selected ? '#6366f1' : cfg.border}`,
        boxShadow: selected ? '0 0 0 4px rgba(99, 102, 241, 0.2)' : '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        minWidth: '180px',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: cfg.border }} />

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <IconComponent size={16} color={cfg.text} />
          <span
            style={{
              fontSize: '11px',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              color: cfg.text,
            }}
          >
            {cfg.label}
          </span>
        </div>
        <span
          style={{
            fontSize: '14px',
            fontWeight: 700,
            color: cfg.text,
          }}
        >
          {data.mastery?.toFixed(0)}%
        </span>
      </div>

      <div style={{ fontWeight: 700, fontSize: '15px', color: '#111827', marginBottom: '6px' }}>
        {data.name}
      </div>

      {/* Progress Bar */}
      <div
        style={{
          width: '100%',
          height: '6px',
          backgroundColor: '#e5e7eb',
          borderRadius: '3px',
          overflow: 'hidden',
          marginBottom: '6px',
        }}
      >
        <div
          style={{
            width: `${Math.min(100, Math.max(0, data.mastery || 0))}%`,
            height: '100%',
            backgroundColor: cfg.border,
            borderRadius: '3px',
            transition: 'width 0.4s ease',
          }}
        />
      </div>

      <div style={{ fontSize: '11px', color: '#6b7280', display: 'flex', justifyContent: 'space-between' }}>
        <span>{data.attempts || 0} attempts</span>
        <span>{data.accuracy || 0}% accuracy</span>
      </div>

      <Handle type="source" position={Position.Right} style={{ background: cfg.border }} />
    </div>
  );
}

export default memo(ConceptNode);
