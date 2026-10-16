import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { CheckCircle2, TrendingUp, AlertTriangle, Lock } from 'lucide-react';

const statusConfig = {
  STRONG: {
    bg: '#ecfdf5',
    border: '#10b981',
    text: '#065f46',
    icon: CheckCircle2,
    label: 'Strong',
  },
  DEVELOPING: {
    bg: '#eff6ff',
    border: '#3b82f6',
    text: '#1e40af',
    icon: TrendingUp,
    label: 'Developing',
  },
  WEAK: {
    bg: '#fffbeb',
    border: '#f59e0b',
    text: '#92400e',
    icon: AlertTriangle,
    label: 'Weak',
  },
  LOCKED: {
    bg: '#f3f4f6',
    border: '#9ca3af',
    text: '#4b5563',
    icon: Lock,
    label: 'Locked',
  },
};

function ConceptNode({ data, selected }) {
  const normalizedStatus = (data.status || 'WEAK').toUpperCase();
  const cfg = statusConfig[normalizedStatus] || statusConfig.WEAK;
  const IconComponent = cfg.icon;

  return (
    <div
      style={{
        padding: '14px 18px',
        borderRadius: '12px',
        backgroundColor: cfg.bg,
        border: `2px solid ${selected ? '#6366f1' : cfg.border}`,
        boxShadow: selected ? '0 0 0 4px rgba(99, 102, 241, 0.25)' : '0 4px 6px -1px rgba(0, 0, 0, 0.08)',
        minWidth: '190px',
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
              fontWeight: 700,
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
            fontWeight: 800,
            color: cfg.text,
          }}
        >
          {data.mastery !== undefined ? Number(data.mastery).toFixed(0) : 0}%
        </span>
      </div>

      <div style={{ fontWeight: 800, fontSize: '15px', color: '#0f172a', marginBottom: '8px' }}>
        {data.name}
      </div>

      {/* Progress Bar */}
      <div
        style={{
          width: '100%',
          height: '6px',
          backgroundColor: '#e2e8f0',
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

      <div style={{ fontSize: '11px', color: '#64748b', display: 'flex', justifyContent: 'space-between' }}>
        <span>{data.attempts || 0} attempts</span>
        <span>{data.accuracy || 0}% acc</span>
      </div>

      <Handle type="source" position={Position.Right} style={{ background: cfg.border }} />
    </div>
  );
}

export default memo(ConceptNode);
