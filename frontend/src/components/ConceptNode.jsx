import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { CheckCircle2, TrendingUp, AlertTriangle, Lock } from 'lucide-react';

const statusConfig = {
  STRONG: {
    bg: '#ecfdf5',
    border: '#10b981',
    text: '#065f46',
    badgeBg: '#d1fae5',
    icon: CheckCircle2,
    label: 'Mastered',
  },
  DEVELOPING: {
    bg: '#eff6ff',
    border: '#3b82f6',
    text: '#1e40af',
    badgeBg: '#dbeafe',
    icon: TrendingUp,
    label: 'Learning',
  },
  WEAK: {
    bg: '#fffbeb',
    border: '#f59e0b',
    text: '#92400e',
    badgeBg: '#fef3c7',
    icon: AlertTriangle,
    label: 'Needs Review',
  },
  LOCKED: {
    bg: '#f8fafc',
    border: '#94a3b8',
    text: '#475569',
    badgeBg: '#e2e8f0',
    icon: Lock,
    label: 'Locked',
  },
};

function ConceptNode({ data, selected }) {
  const normalizedStatus = (data.status || 'WEAK').toUpperCase();
  const cfg = statusConfig[normalizedStatus] || statusConfig.WEAK;
  const IconComponent = cfg.icon;
  const masteryScore = data.mastery !== undefined ? Number(data.mastery).toFixed(0) : 0;

  return (
    <div
      style={{
        width: '138px',
        height: '138px',
        borderRadius: '16px',
        backgroundColor: cfg.bg,
        border: `2px solid ${selected ? '#6366f1' : cfg.border}`,
        boxShadow: selected
          ? '0 0 0 3px rgba(99, 102, 241, 0.35), 0 10px 18px -3px rgba(99, 102, 241, 0.25)'
          : '0 4px 10px -2px rgba(15, 23, 42, 0.08), 0 2px 4px -1px rgba(15, 23, 42, 0.04)',
        padding: '10px 10px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        boxSizing: 'border-box',
        cursor: 'pointer',
        position: 'relative',
        userSelect: 'none',
        transition: 'all 0.18s ease-in-out',
      }}
      title={`${data.name} (${masteryScore}% - ${cfg.label})`}
    >
      {/* 4-way Connection Handles for clean multi-directional routing */}
      <Handle
        type="target"
        position={Position.Left}
        id="target-left"
        style={{ background: cfg.border, width: 8, height: 8, border: '2px solid #ffffff' }}
      />
      <Handle
        type="target"
        position={Position.Top}
        id="target-top"
        style={{ background: cfg.border, width: 8, height: 8, border: '2px solid #ffffff' }}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="source-right"
        style={{ background: cfg.border, width: 8, height: 8, border: '2px solid #ffffff' }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="source-bottom"
        style={{ background: cfg.border, width: 8, height: 8, border: '2px solid #ffffff' }}
      />

      {/* Top Header: Status Icon + Percentage Badge */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '4px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <IconComponent size={14} color={cfg.text} strokeWidth={2.5} />
          <span
            style={{
              fontSize: '10px',
              fontWeight: 800,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              color: cfg.text,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              maxWidth: '52px',
            }}
          >
            {cfg.label}
          </span>
        </div>
        <span
          style={{
            fontSize: '12px',
            fontWeight: 800,
            color: cfg.text,
            backgroundColor: cfg.badgeBg,
            padding: '1px 5px',
            borderRadius: '6px',
            lineHeight: 1.2,
          }}
        >
          {masteryScore}%
        </span>
      </div>

      {/* Center Body: Module Subtitle + Concept Name */}
      <div style={{ textAlign: 'center', margin: 'auto 0' }}>
        {data.module_title && (
          <div
            style={{
              fontSize: '9px',
              fontWeight: 700,
              color: '#64748b',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              marginBottom: '2px',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {data.module_title}
          </div>
        )}
        <div
          style={{
            fontWeight: 800,
            fontSize: '12px',
            color: '#0f172a',
            lineHeight: '1.25',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
            wordBreak: 'break-word',
          }}
        >
          {data.name}
        </div>
      </div>

      {/* Footer: Progress Bar + Attempts / Accuracy stats */}
      <div>
        <div
          style={{
            width: '100%',
            height: '4px',
            backgroundColor: '#e2e8f0',
            borderRadius: '2px',
            overflow: 'hidden',
            marginBottom: '4px',
          }}
        >
          <div
            style={{
              width: `${Math.min(100, Math.max(0, Number(data.mastery || 0)))}%`,
              height: '100%',
              backgroundColor: cfg.border,
              borderRadius: '2px',
              transition: 'width 0.4s ease',
            }}
          />
        </div>

        <div
          style={{
            fontSize: '9.5px',
            color: '#64748b',
            display: 'flex',
            justifyContent: 'space-between',
            fontWeight: 600,
          }}
        >
          <span>{data.attempts || 0} att</span>
          <span>{data.accuracy !== undefined ? data.accuracy : 0}% acc</span>
        </div>
      </div>
    </div>
  );
}

export default memo(ConceptNode);
