import { useEffect, useRef, useCallback } from 'react';
import { sessionService } from '../services/codingService';

function generateEventId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'ev-' + Date.now() + '-' + Math.random().toString(36).substring(2, 9);
}

export function useSessionRecorder(sessionId, onIntegrityWarning = null) {
  const eventBufferRef = useRef([]);
  const flushTimerRef = useRef(null);
  const inactivityTimerRef = useRef(null);
  const isFlushingRef = useRef(false);
  const lastEventTimestampRef = useRef(Date.now());
  const lastActivityTimestampRef = useRef(Date.now());
  const hasWarnedSplitScreenRef = useRef(false);
  const onWarningRef = useRef(onIntegrityWarning);

  useEffect(() => {
    onWarningRef.current = onIntegrityWarning;
  }, [onIntegrityWarning]);

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
    } finally {
      isFlushingRef.current = false;
    }
  }, [sessionId]);

  // Method to record an activity event
  const recordEvent = useCallback(
    (eventType, options = {}) => {
      if (!sessionId) return;

      const now = Date.now();
      const durationSinceLast = lastEventTimestampRef.current ? (now - lastEventTimestampRef.current) / 1000 : null;
      lastEventTimestampRef.current = now;
      lastActivityTimestampRef.current = now;

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

      // If buffer exceeds threshold or priority integrity event, flush early
      if (
        eventBufferRef.current.length >= 10 ||
        ['POSSIBLE_SPLIT_SCREEN', 'FULLSCREEN_EXIT', 'TAB_SWITCH', 'WINDOW_BLUR', 'COPY', 'PASTE', 'SUBMIT', 'RUN'].includes(eventType)
      ) {
        flushEvents();
      }
    },
    [sessionId, flushEvents]
  );

  // Setup periodic buffer flusher and browser focus/visibility/integrity listeners
  useEffect(() => {
    if (!sessionId) return;

    // Periodic flush every 3 seconds
    flushTimerRef.current = setInterval(() => {
      flushEvents();
    }, 3000);

    // Suspicious inactivity monitor (triggers if no activity for > 60s)
    inactivityTimerRef.current = setInterval(() => {
      const idleTime = (Date.now() - lastActivityTimestampRef.current) / 1000;
      if (idleTime >= 60) {
        recordEvent('SUSPICIOUS_INACTIVITY', {
          metadata: { idle_seconds: Math.round(idleTime), note: 'Prolonged inactivity observed.' },
        });
        lastActivityTimestampRef.current = Date.now(); // reset idle timer
      }
    }, 15000);

    // Browser tab visibility change listener
    const handleVisibilityChange = () => {
      if (document.hidden) {
        recordEvent('TAB_SWITCH', {
          metadata: { hidden: true, action: 'tab_hidden', detail: 'Application window became hidden' },
        });
        if (onWarningRef.current) {
          onWarningRef.current({
            warning_type: 'TAB_SWITCH',
            message: 'Your assessment environment was interrupted. Please remain in the assessment window.',
            severity: 'LOW',
            evidence: { action: 'tab_hidden', timestamp: new Date().toISOString() },
          });
        }
      } else {
        recordEvent('VISIBILITY_CHANGE', {
          metadata: { hidden: false, action: 'tab_visible', detail: 'Application window became visible' },
        });
      }
    };

    // Window blur/focus listeners
    const handleWindowBlur = () => {
      recordEvent('WINDOW_BLUR', {
        metadata: { action: 'blur', detail: 'Application window lost focus' },
      });
      if (onWarningRef.current) {
        onWarningRef.current({
          warning_type: 'WINDOW_BLUR',
          message: 'Assessment window lost focus. Continued interruptions may be recorded as integrity events.',
          severity: 'LOW',
          evidence: { action: 'window_blur', timestamp: new Date().toISOString() },
        });
      }
    };

    const handleWindowFocus = () => {
      recordEvent('FOCUS', {
        metadata: { action: 'focus', detail: 'Application gained focus' },
      });
    };

    // Fullscreen change listener
    const handleFullscreenChange = () => {
      if (!document.fullscreenElement) {
        recordEvent('FULLSCREEN_EXIT', {
          metadata: { action: 'fullscreen_exit', detail: 'Assessment window exited fullscreen mode' },
        });
        if (onWarningRef.current) {
          onWarningRef.current({
            warning_type: 'FULLSCREEN_EXIT',
            message: 'Assessment window exited fullscreen. Please remain in the assessment window.',
            severity: 'LOW',
            evidence: { fullscreen: false, timestamp: new Date().toISOString() },
          });
        }
      }
    };

    // Window resize & possible split screen heuristic listener
    let resizeTimeout = null;
    const handleResize = () => {
      if (resizeTimeout) clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        const availWidth = window.screen.availWidth || 1200;
        const currentWidth = window.innerWidth;
        const widthRatio = currentWidth / availWidth;

        // Evidence package
        const evidence = {
          window_width: window.innerWidth,
          window_height: window.innerHeight,
          screen_width: availWidth,
          screen_height: window.screen.availHeight || 800,
          visibility: !document.hidden,
          fullscreen: !!document.fullscreenElement,
        };

        if (widthRatio < 0.65 && !document.fullscreenElement) {
          recordEvent('POSSIBLE_SPLIT_SCREEN', {
            metadata: {
              ...evidence,
              width_ratio: roundDec(widthRatio, 2),
              detail: 'Window width proportion consistent with side-by-side view',
            },
          });
          if (onWarningRef.current && !hasWarnedSplitScreenRef.current) {
            hasWarnedSplitScreenRef.current = true;
            onWarningRef.current({
              warning_type: 'POSSIBLE_SPLIT_SCREEN',
              message:
                'Notice: Assessment window appears resized to a split-screen view. Please keep the window full size for optimal integrity scoring.',
              severity: 'LOW',
              evidence: evidence,
            });
          }
        } else {
          hasWarnedSplitScreenRef.current = false;
          recordEvent('RESIZE_ANOMALY', {
            metadata: evidence,
          });
        }
      }, 500);
    };

    // Document-level clipboard copy listener
    const handleDocumentCopy = () => {
      const selected = window.getSelection ? window.getSelection().toString() : '';
      recordEvent('COPY', {
        metadata: {
          action: 'clipboard_copy',
          copied_length: selected ? selected.length : 0,
          preview: selected ? selected.slice(0, 50) : '',
        },
      });
    };

    // Check initial window proportion on session start
    const initialResizeTimer = setTimeout(() => {
      handleResize();
    }, 600);

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleWindowBlur);
    window.addEventListener('focus', handleWindowFocus);
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    window.addEventListener('resize', handleResize);
    document.addEventListener('copy', handleDocumentCopy);

    return () => {
      if (flushTimerRef.current) clearInterval(flushTimerRef.current);
      if (inactivityTimerRef.current) clearInterval(inactivityTimerRef.current);
      if (resizeTimeout) clearTimeout(resizeTimeout);
      if (initialResizeTimer) clearTimeout(initialResizeTimer);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleWindowBlur);
      window.removeEventListener('focus', handleWindowFocus);
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      window.removeEventListener('resize', handleResize);
      document.removeEventListener('copy', handleDocumentCopy);
      // Final flush
      flushEvents();
    };
  }, [sessionId, recordEvent, flushEvents]);

  return {
    recordEvent,
    flushEvents,
  };
}

function roundDec(val, dec = 2) {
  const factor = Math.pow(10, dec);
  return Math.round(val * factor) / factor;
}
