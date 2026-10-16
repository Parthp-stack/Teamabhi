import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { sessionService } from '../services/codingService';
import IntegritySignalBadge from '../components/IntegritySignalBadge';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Clock,
  AlertTriangle,
  ArrowLeft,
  ShieldCheck,
  CheckCircle2,
  FileCode,
} from 'lucide-react';

export default function SessionReplayPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [replayData, setReplayData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentEventIndex, setCurrentEventIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playSpeed, setPlaySpeed] = useState(1);
  const [selectedSignalId, setSelectedSignalId] = useState(null);

  const timerRef = useRef(null);

  useEffect(() => {
    async function loadReplay() {
      try {
        const data = await sessionService.getReplay(sessionId);
        setReplayData(data);
        if (data.events && data.events.length > 0) {
          setCurrentEventIndex(0);
        }
      } catch (err) {
        console.error('Failed to load session replay:', err);
      } finally {
        setLoading(false);
      }
    }
    loadReplay();
  }, [sessionId]);

  // Replay playback loop
  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setInterval(() => {
        setCurrentEventIndex((prev) => {
          if (!replayData?.events || prev >= replayData.events.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 800 / playSpeed);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, playSpeed, replayData]);

  // Jump to specific event index
  const handleSeek = (index) => {
    if (!replayData?.events) return;
    const bounded = Math.max(0, Math.min(index, replayData.events.length - 1));
    setCurrentEventIndex(bounded);
  };

  // Jump to signal's specific event
  const handleSignalClick = (signal) => {
    setSelectedSignalId(signal.id);
    if (!signal.event_id || !replayData?.events) return;
    const targetIdx = replayData.events.findIndex((e) => e.id === signal.event_id);
    if (targetIdx !== -1) {
      setCurrentEventIndex(targetIdx);
      setIsPlaying(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: '#64748b' }}>
        Loading session replay timeline...
      </div>
    );
  }

  if (!replayData) {
    return (
      <div style={{ padding: '40px', backgroundColor: '#ffffff', borderRadius: '12px', textAlign: 'center' }}>
        <h3>Session Not Found</h3>
        <button onClick={() => navigate('/trainer/dashboard')}>Back to Dashboard</button>
      </div>
    );
  }

  const events = replayData.events || [];
  const signals = replayData.signals || [];
  const currentEvent = events[currentEventIndex] || null;

  // Reconstruct code slice preview based on progress
  const totalEvents = events.length;
  const progressPercent = totalEvents > 1 ? currentEventIndex / (totalEvents - 1) : 1;
  const finalCode = replayData.final_source_code || '# No final code submitted';
  // Slice lines proportional to replay progress or show full code if past halfway
  const codeLines = finalCode.split('\n');
  const linesToShow = Math.max(1, Math.round(codeLines.length * progressPercent));
  const reconstructedCode = codeLines.slice(0, linesToShow).join('\n');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 100px)', gap: '14px' }}>
      {/* Top Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#ffffff',
          padding: '14px 20px',
          borderRadius: '12px',
          border: '1px solid #e5e7eb',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={() => navigate('/trainer/dashboard')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              background: '#f3f4f6',
              border: 'none',
              borderRadius: '6px',
              padding: '6px 10px',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            <ArrowLeft size={14} /> Back
          </button>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '16px', fontWeight: 800, color: '#0f172a' }}>
                Session #{replayData.session_id} Replay: {replayData.student_name}
              </span>
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  backgroundColor: '#fee2e2',
                  color: '#991b1b',
                  padding: '2px 8px',
                  borderRadius: '12px',
                }}
              >
                {signals.length} Integrity Signals
              </span>
            </div>
            <div style={{ fontSize: '12px', color: '#64748b' }}>
              Assessment: {replayData.problem_title} · Total Events: {totalEvents}
            </div>
          </div>
        </div>

        {/* Disclaimer Badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            backgroundColor: '#fffbeb',
            border: '1px solid #fef3c7',
            padding: '6px 12px',
            borderRadius: '8px',
            fontSize: '12px',
            color: '#92400e',
            fontWeight: 600,
          }}
        >
          <ShieldCheck size={16} color="#d97706" />
          <span>Evidence for Human Review (No automatic cheating verdict)</span>
        </div>
      </div>

      {/* 3-Column Body Layout */}
      <div style={{ display: 'flex', gap: '14px', flex: 1, overflow: 'hidden' }}>
        {/* LEFT COLUMN: Event Timeline */}
        <div
          style={{
            width: '280px',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            border: '1px solid #e5e7eb',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #e5e7eb', backgroundColor: '#f8fafc' }}>
            <span style={{ fontSize: '12px', fontWeight: 700, color: '#475569', textTransform: 'uppercase' }}>
              Chronological Timeline
            </span>
          </div>
          <div style={{ padding: '12px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {events.map((ev, idx) => {
              const isCurrent = idx === currentEventIndex;
              const hasSignal = !!ev.signal;
              return (
                <div
                  key={ev.id}
                  onClick={() => handleSeek(idx)}
                  style={{
                    padding: '8px 10px',
                    borderRadius: '6px',
                    backgroundColor: isCurrent ? '#e0e7ff' : hasSignal ? '#fef2f2' : '#ffffff',
                    border: isCurrent
                      ? '1.5px solid #4f46e5'
                      : hasSignal
                      ? '1.5px solid #fca5a5'
                      : '1px solid #f1f5f9',
                    cursor: 'pointer',
                    fontSize: '12px',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                    <span style={{ fontWeight: 700, color: hasSignal ? '#b91c1c' : '#1e293b' }}>
                      #{idx + 1} {ev.event_type}
                    </span>
                    <span style={{ fontSize: '10px', color: '#94a3b8' }}>
                      {new Date(ev.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  {ev.metadata?.charCount && (
                    <div style={{ fontSize: '11px', color: '#64748b' }}>
                      +{ev.metadata.charCount} characters
                    </div>
                  )}
                  {ev.metadata?.action && (
                    <div style={{ fontSize: '11px', color: '#64748b' }}>
                      Action: {ev.metadata.action}
                    </div>
                  )}
                  {hasSignal && (
                    <div style={{ fontSize: '10px', fontWeight: 700, color: '#dc2626', marginTop: '2px' }}>
                      ⚠ Signal: {ev.signal.signal_type}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* CENTER COLUMN: Monaco Replay Editor with Playback Controls */}
        <div
          style={{
            flex: 1,
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            border: '1px solid #e5e7eb',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Playback Controls Bar */}
          <div
            style={{
              padding: '10px 18px',
              backgroundColor: '#1e293b',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid #334155',
            }}
          >
            {/* Play / Pause / Skip */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                onClick={() => handleSeek(currentEventIndex - 1)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
                title="Previous Event"
              >
                <SkipBack size={18} />
              </button>

              <button
                onClick={() => setIsPlaying(!isPlaying)}
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  backgroundColor: '#4f46e5',
                  color: '#ffffff',
                  border: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                }}
              >
                {isPlaying ? <Pause size={16} /> : <Play size={16} />}
              </button>

              <button
                onClick={() => handleSeek(currentEventIndex + 1)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
                title="Next Event"
              >
                <SkipForward size={18} />
              </button>

              <div style={{ marginLeft: '12px', fontSize: '12px', color: '#cbd5e1' }}>
                Event <strong>{currentEventIndex + 1}</strong> of <strong>{totalEvents}</strong>
              </div>
            </div>

            {/* Scrubber Slider */}
            <div style={{ flex: 1, margin: '0 20px', display: 'flex', alignItems: 'center' }}>
              <input
                type="range"
                min={0}
                max={Math.max(0, totalEvents - 1)}
                value={currentEventIndex}
                onChange={(e) => handleSeek(parseInt(e.target.value))}
                style={{ width: '100%', accentColor: '#4f46e5', cursor: 'pointer' }}
              />
            </div>

            {/* Playback Speed Switcher */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {[1, 2, 5].map((spd) => (
                <button
                  key={spd}
                  onClick={() => setPlaySpeed(spd)}
                  style={{
                    backgroundColor: playSpeed === spd ? '#4f46e5' : '#334155',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '4px',
                    padding: '2px 8px',
                    fontSize: '11px',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  {spd}x
                </button>
              ))}
            </div>
          </div>

          {/* Current Event Indicator Bar */}
          {currentEvent && (
            <div
              style={{
                padding: '6px 16px',
                backgroundColor: currentEvent.signal ? '#fee2e2' : '#f1f5f9',
                borderBottom: '1px solid #e2e8f0',
                fontSize: '12px',
                color: currentEvent.signal ? '#991b1b' : '#334155',
                display: 'flex',
                justifyContent: 'space-between',
              }}
            >
              <span>
                Active Event: <strong>{currentEvent.event_type}</strong>{' '}
                {currentEvent.metadata?.preview && `("${currentEvent.metadata.preview}")`}
              </span>
              <span>Timestamp: {new Date(currentEvent.timestamp).toLocaleTimeString()}</span>
            </div>
          )}

          {/* Monaco Editor Showing Reconstructed Code */}
          <div style={{ flex: 1 }}>
            <Editor
              height="100%"
              language="python"
              theme="vs-dark"
              value={reconstructedCode}
              options={{
                readOnly: true,
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                automaticLayout: true,
              }}
            />
          </div>
        </div>

        {/* RIGHT COLUMN: Integrity Signals Requiring Review */}
        <div
          style={{
            width: '320px',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            border: '1px solid #e5e7eb',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #e5e7eb', backgroundColor: '#f8fafc' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <AlertTriangle size={15} color="#ea580c" />
              <span style={{ fontSize: '12px', fontWeight: 700, color: '#475569', textTransform: 'uppercase' }}>
                Integrity Evidence ({signals.length})
              </span>
            </div>
          </div>

          <div style={{ padding: '14px', overflowY: 'auto', flex: 1 }}>
            {signals.length === 0 ? (
              <div style={{ color: '#16a34a', fontSize: '13px', textAlign: 'center', padding: '20px 0' }}>
                <CheckCircle2 size={32} style={{ margin: '0 auto 8px auto', display: 'block' }} />
                No integrity signals flagged. Session followed normal write-run-fix patterns.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {signals.map((sig) => (
                  <IntegritySignalBadge
                    key={sig.id}
                    signal={sig}
                    onClick={() => handleSignalClick(sig)}
                    isSelected={selectedSignalId === sig.id}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
