import React from 'react';
import { X, CheckCircle, AlertCircle, ArrowRight, BookOpen, Clock } from 'lucide-react';

export default function ConceptDetailModal({ concept, onClose, onStartPractice }) {
  if (!concept) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        bottom: 0,
        width: '420px',
        backgroundColor: '#ffffff',
        boxShadow: '-4px 0 25px rgba(0,0,0,0.15)',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        animation: 'slideIn 0.25s ease-out',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '20px 24px',
          borderBottom: '1px solid #e5e7eb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#f9fafb',
        }}
      >
        <div>
          <span
            style={{
              fontSize: '11px',
              textTransform: 'uppercase',
              fontWeight: 700,
              color: '#6366f1',
              letterSpacing: '0.05em',
            }}
          >
            Concept Deep Dive
          </span>
          <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#111827', margin: '4px 0 0 0' }}>
            {concept.name}
          </h2>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '6px',
            color: '#6b7280',
            borderRadius: '6px',
          }}
        >
          <X size={20} />
        </button>
      </div>

      {/* Body */}
      <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
        {/* Description */}
        <p style={{ color: '#4b5563', fontSize: '14px', lineHeight: '1.6', margin: '0 0 20px 0' }}>
          {concept.description || 'Fundamental building block of the object model.'}
        </p>

        {/* Mastery Metric Card */}
        <div
          style={{
            backgroundColor: '#f3f4f6',
            borderRadius: '12px',
            padding: '16px',
            marginBottom: '20px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: '#374151' }}>Mastery Competency</span>
            <span style={{ fontSize: '16px', fontWeight: 800, color: '#111827' }}>
              {concept.mastery?.toFixed(1)}%
            </span>
          </div>
          <div
            style={{
              width: '100%',
              height: '8px',
              backgroundColor: '#e5e7eb',
              borderRadius: '4px',
              overflow: 'hidden',
              marginBottom: '12px',
            }}
          >
            <div
              style={{
                width: `${Math.min(100, Math.max(0, concept.mastery || 0))}%`,
                height: '100%',
                backgroundColor: concept.mastery >= 75 ? '#10b981' : concept.mastery >= 50 ? '#3b82f6' : '#f59e0b',
                borderRadius: '4px',
              }}
            />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px', color: '#4b5563' }}>
            <div>Attempts: <strong>{concept.attempts || 0}</strong></div>
            <div>Correct: <strong>{concept.correct_attempts || 0}</strong></div>
            <div>Accuracy: <strong>{concept.accuracy || 0}%</strong></div>
            <div>Status: <strong>{concept.status}</strong></div>
          </div>
        </div>

        {/* Prerequisites */}
        <div style={{ marginBottom: '20px' }}>
          <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#374151', textTransform: 'uppercase', marginBottom: '10px' }}>
            Prerequisites Required
          </h4>
          {concept.prerequisites && concept.prerequisites.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {concept.prerequisites.map((p) => (
                <div
                  key={p.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 12px',
                    backgroundColor: '#fafafa',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    fontSize: '13px',
                  }}
                >
                  <CheckCircle size={16} color="#10b981" />
                  <span style={{ fontWeight: 600, color: '#1f2937' }}>{p.name}</span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ fontSize: '13px', color: '#6b7280' }}>No prior prerequisites (Foundational Concept)</div>
          )}
        </div>

        {/* Dependents */}
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#374151', textTransform: 'uppercase', marginBottom: '10px' }}>
            Unlocks Subsequent Concepts
          </h4>
          {concept.dependents && concept.dependents.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {concept.dependents.map((d) => (
                <div
                  key={d.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 12px',
                    backgroundColor: '#fafafa',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    fontSize: '13px',
                  }}
                >
                  <ArrowRight size={16} color="#6366f1" />
                  <span style={{ fontWeight: 600, color: '#1f2937' }}>{d.name}</span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ fontSize: '13px', color: '#6b7280' }}>Capstone topic in this module</div>
          )}
        </div>

        {/* Recent Attempts History */}
        {concept.recent_attempts && concept.recent_attempts.length > 0 && (
          <div style={{ marginBottom: '20px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#374151', textTransform: 'uppercase', marginBottom: '10px' }}>
              Recent Practice Attempts
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {concept.recent_attempts.map((att) => (
                <div
                  key={att.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '8px 12px',
                    backgroundColor: att.correct ? '#f0fdf4' : '#fef2f2',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                >
                  <span style={{ fontWeight: 500, color: '#111827', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '240px' }}>
                    {att.question_title}
                  </span>
                  <span style={{ fontWeight: 700, color: att.correct ? '#16a34a' : '#dc2626' }}>
                    {att.correct ? 'PASSED' : 'MISSED'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={{ padding: '16px 24px', borderTop: '1px solid #e5e7eb', backgroundColor: '#f9fafb' }}>
        <button
          onClick={() => onStartPractice && onStartPractice(concept.id)}
          style={{
            width: '100%',
            padding: '12px',
            backgroundColor: '#4f46e5',
            color: '#ffffff',
            border: 'none',
            borderRadius: '8px',
            fontWeight: 700,
            fontSize: '14px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
          }}
        >
          <BookOpen size={16} />
          Practice Adaptive Questions
        </button>
      </div>
    </div>
  );
}
