import { useEffect, useRef, useCallback } from 'react';
import { sessionService } from '../services/codingService';

function generateEventId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'ev-' + Date.now() + '-' + Math.random().toString(36).substring(2, 9);
}

export function useSessionRecorder(sessionId) {
  const eventBufferRef = useRef([]);
  const flushTimerRef = useRef(null);
  const isFlushingRef = useRef(false);
  const lastEventTimestampRef = useRef(Date.now());

  // Function to flush buffer to backend with retry on failure
  const flushEvents = useCallback(async () => {
    if (!sessionId || eventBufferRef.current.length === 0 || isFlushingRef.current) return;
    
    isFlushingRef.current = true;
    const batch = [...eventBufferRef.current];

    try {
      await sessionService.recordEventsBatch(sessionId, batch);
      // Remove successfully submitted batch items (comparing by client_event_id)
      const submittedIds = new Set(batch.map((b) => b.client_event_id));
      eventBufferRef.current = eventBufferRef.current.filter((e) => !submittedIds.has(e.client_event_id));
    } catch (err) {
      console.warn('[SessionRecorder] Transient network issue transmitting event batch, will retry:', err);
      // Retain buffer intact for retry on next periodic timer or manual flush
    } finally {
      isFlushingRef.current = false;
    }
  }, [sessionId]);

  // Method to record an activity event
  const recordEvent = useCallback((eventType, options = {}) => {
    if (!sessionId) return;

    const now = Date.now();
    const durationSinceLast = lastEventTimestampRef.current ? (now - lastEventTimestampRef.current) / 1000 : null;
    lastEventTimestampRef.current = now;

    const {
      codeLocation = null,
      insertedCount = 0,
      deletedCount = 0,
      duration = durationSinceLast,
      currentCode = null,
      metadata = {},
    } = options;

    const event = {
      client_event_id: generateEventId(),
      event_type: eventType,
      timestamp: new Date().toISOString(),
      client_timestamp: new Date().toISOString(),
      code_location: codeLocation,
      inserted_character_count: insertedCount,
      deleted_character_count: deletedCount,
      duration: duration,
      current_code: currentCode,
      metadata: metadata,
    };

    eventBufferRef.current.push(event);

    // If buffer exceeds threshold, flush early
    if (eventBufferRef.current.length >= 15) {
      flushEvents();
    }
  }, [sessionId, flushEvents]);

  // Setup periodic buffer flusher and browser focus/visibility listeners
  useEffect(() => {
    if (!sessionId) return;

    // Periodic flush every 3 seconds
    flushTimerRef.current = setInterval(() => {
      flushEvents();
    }, 3000);

    // Browser visibility change listener
    const handleVisibilityChange = () => {
      if (document.hidden) {
        recordEvent('VISIBILITY_CHANGE', {
          metadata: { hidden: true, action: 'hidden', detail: 'Application window became hidden' },
        });
      } else {
        recordEvent('VISIBILITY_CHANGE', {
          metadata: { hidden: false, action: 'visible', detail: 'Application window became visible' },
        });
      }
    };

    // Window blur/focus listeners
    const handleWindowBlur = () => {
      recordEvent('BLUR', {
        metadata: { action: 'blur', detail: 'Application lost focus' },
      });
    };

    const handleWindowFocus = () => {
      recordEvent('FOCUS', {
        metadata: { action: 'focus', detail: 'Application gained focus' },
      });
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleWindowBlur);
    window.addEventListener('focus', handleWindowFocus);

    return () => {
      if (flushTimerRef.current) clearInterval(flushTimerRef.current);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleWindowBlur);
      window.removeEventListener('focus', handleWindowFocus);
      // Final flush
      flushEvents();
    };
  }, [sessionId, recordEvent, flushEvents]);

  return {
    recordEvent,
    flushEvents,
  };
}
