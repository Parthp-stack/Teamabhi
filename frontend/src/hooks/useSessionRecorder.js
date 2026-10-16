import { useEffect, useRef, useCallback } from 'react';
import { sessionService } from '../services/codingService';

export function useSessionRecorder(sessionId) {
  const eventBufferRef = useRef([]);
  const flushTimerRef = useRef(null);

  // Function to flush buffer to backend
  const flushEvents = useCallback(async () => {
    if (!sessionId || eventBufferRef.current.length === 0) return;
    
    const batch = [...eventBufferRef.current];
    eventBufferRef.current = [];

    try {
      await sessionService.recordEventsBatch(sessionId, batch);
    } catch (err) {
      console.warn('[SessionRecorder] Failed to transmit event batch:', err);
      // Re-queue events if network failed temporarily
      eventBufferRef.current = [...batch, ...eventBufferRef.current];
    }
  }, [sessionId]);

  // Method to record an event
  const recordEvent = useCallback((eventType, metadata = {}) => {
    if (!sessionId) return;

    const event = {
      event_type: eventType,
      timestamp: new Date().toISOString(),
      metadata: metadata,
    };

    eventBufferRef.current.push(event);

    // If buffer exceeds threshold, flush early
    if (eventBufferRef.current.length >= 25) {
      flushEvents();
    }
  }, [sessionId, flushEvents]);

  // Setup periodic buffer flusher and browser focus/visibility listeners
  useEffect(() => {
    if (!sessionId) return;

    // Periodic flush every 4 seconds
    flushTimerRef.current = setInterval(() => {
      flushEvents();
    }, 4000);

    // Browser visibility change listener
    const handleVisibilityChange = () => {
      if (document.hidden) {
        recordEvent('TAB_SWITCH', { action: 'hidden', detail: 'User switched away from active browser tab' });
      } else {
        recordEvent('FOCUS', { action: 'visible', detail: 'User returned to active browser tab' });
      }
    };

    // Window blur/focus listeners
    const handleWindowBlur = () => {
      recordEvent('BLUR', { action: 'blur', detail: 'Editor window lost focus' });
    };

    const handleWindowFocus = () => {
      recordEvent('FOCUS', { action: 'focus', detail: 'Editor window gained focus' });
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
