import React from 'react';
import { AlertCircle, AlertTriangle, Info, Clock } from 'lucide-react';

const severityStyles = {
  HIGH: {
    bg: '#fef2f2',
    border: '#f87171',
    text: '#991b1b',
    badge: '#ef4444',
    icon: AlertCircle,
  },
  MEDIUM: {
    bg: '#fffbeb',
    border: '#fcd34d',
    text: '#92400e',
    badge: '#f59e0b',
    icon: AlertTriangle,
  },
  LOW: {
    bg: '#f0fdf4',
    border: '#86efac',
    text: '#166534',
    badge: '#22c55e',
    icon: Info,
  },
};

export default function IntegritySignalBadge({ signal, onClick, isSelected }) {
  const style = severityStyles[signal.severity] || severityStyles.MEDIUM;
  const IconComponent = style.icon;

  const timeStr = signal.timestamp ? new Date(signal.timestamp).toLocaleTimeString() : '';

  return (
    <div
      onClick={onClick}
      style={{
        padding: '12px 14px',
        backgroundColor: style.bg,
        border: `1.5px solid ${isSelected ? '#4f46e5' : style.border}`,
        borderRadius: '10px',
        cursor: onClick ? 'pointer' : 'default',
        boxShadow: isSelected ? '0 0 0 3px rgba(79, 70, 229, 0.2)' : 'none',
        transition: 'all 0.15s ease',
        marginBottom: '10px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <IconComponent size={15} color={style.text} />
          <span style={{ fontSize: '12px', fontWeight: 700, color: style.text, textTransform: 'uppercase' }}>
            {signal.signal_type.replace('_', ' ')}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: '#6b7280' }}>
          <Clock size={12} />
          <span>{timeStr}</span>
        </div>
      </div>

      <div style={{ fontSize: '13px', color: '#1f2937', lineHeight: '1.4', marginBottom: '6px' }}>
        {signal.description}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span
          style={{
            fontSize: '10px',
            fontWeight: 700,
            color: style.badge,
            backgroundColor: 'rgba(255, 255, 255, 0.8)',
            padding: '2px 6px',
            borderRadius: '4px',
            textTransform: 'uppercase',
          }}
        >
          {signal.severity} Severity Evidence
        </span>
        {signal.event_id && (
          <span style={{ fontSize: '11px', color: '#4f46e5', fontWeight: 600 }}>
            Jump to Event #{signal.event_id} →
          </span>
        )}
      </div>
    </div>
  );
}
