from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import numpy as np
from backend.models.session import SessionEvent, Session as CodingSession
from backend.models.integrity import IntegritySignal

class IntegrityService:
    @classmethod
    def analyze_session_events(cls, db: Session, session_id: int) -> List[IntegritySignal]:
        """
        Analyze the recorded chronological events of a coding assessment session.
        Generates evidence-based integrity signals for human review.
        NEVER outputs an automated cheating verdict.
        """
        events: List[SessionEvent] = db.query(SessionEvent).filter(
            SessionEvent.session_id == session_id
        ).order_by(SessionEvent.timestamp).all()

        if not events:
            return []

        # Clear previously generated signals for this session to keep idempotent
        db.query(IntegritySignal).filter(IntegritySignal.session_id == session_id).delete()
        db.commit()

        generated_signals: List[IntegritySignal] = []

        # 1. Track stats
        run_count = 0
        tab_switches = []
        keystroke_timestamps = []
        paste_events = []

        for i, ev in enumerate(events):
            m = ev.event_metadata or {}

            # Check LARGE_PASTE
            if ev.event_type == "PASTE":
                paste_events.append(ev)
                char_count = m.get("length", 0) or len(m.get("text", "")) or m.get("charCount", 0)
                if char_count >= 120:
                    severity = "HIGH" if char_count > 350 else "MEDIUM"
                    sig = IntegritySignal(
                        session_id=session_id,
                        event_id=ev.id,
                        signal_type="LARGE_PASTE",
                        severity=severity,
                        description=f"Evidence for review: Large code paste of {char_count} characters detected at {ev.timestamp.strftime('%H:%M:%S')}.",
                        timestamp=ev.timestamp
                    )
                    db.add(sig)
                    generated_signals.append(sig)

            # Check TAB_SWITCH
            elif ev.event_type in ["TAB_SWITCH", "BLUR"]:
                tab_switches.append(ev)

            # Check RUN
            elif ev.event_type == "RUN":
                run_count += 1

            # Keystroke timings for uniform typing check
            elif ev.event_type == "KEYSTROKE":
                keystroke_timestamps.append(ev.timestamp.timestamp())

            # Check FAST_CODE appearance (large diff between consecutive events within < 2 seconds)
            if i > 0:
                prev_ev = events[i - 1]
                time_diff = (ev.timestamp - prev_ev.timestamp).total_seconds()
                diff_len = m.get("added_length", 0) or m.get("charCount", 0)
                if time_diff < 2.0 and diff_len > 150 and ev.event_type != "PASTE":
                    sig = IntegritySignal(
                        session_id=session_id,
                        event_id=ev.id,
                        signal_type="FAST_CODE",
                        severity="MEDIUM",
                        description=f"Evidence for review: Unusually rapid code appearance (+{diff_len} chars in {time_diff:.1f}s) at {ev.timestamp.strftime('%H:%M:%S')}.",
                        timestamp=ev.timestamp
                    )
                    db.add(sig)
                    generated_signals.append(sig)

        # 2. Check TAB_SWITCH frequency
        if len(tab_switches) >= 2:
            first_switch = tab_switches[0]
            sig = IntegritySignal(
                session_id=session_id,
                event_id=first_switch.id,
                signal_type="TAB_SWITCH",
                severity="MEDIUM" if len(tab_switches) < 4 else "HIGH",
                description=f"Evidence for review: Student navigated away from editor {len(tab_switches)} times during assessment.",
                timestamp=first_switch.timestamp
            )
            db.add(sig)
            generated_signals.append(sig)

        # 3. Check NO_CYCLE (Absence of write -> run -> fix cycle)
        # If there are code events and a submission, but 0 or only 1 test run occurred
        submit_events = [e for e in events if e.event_type == "SUBMIT"]
        if submit_events and run_count <= 1:
            last_submit = submit_events[-1]
            sig = IntegritySignal(
                session_id=session_id,
                event_id=last_submit.id,
                signal_type="NO_CYCLE",
                severity="MEDIUM",
                description=f"Evidence for review: Solution submitted with only {run_count} execution run, lacking standard incremental debugging cycles.",
                timestamp=last_submit.timestamp
            )
            db.add(sig)
            generated_signals.append(sig)

        # 4. Check UNIFORM_TYPING (Weak evidence check)
        if len(keystroke_timestamps) >= 40:
            deltas = np.diff(keystroke_timestamps)
            # Filter reasonable typing intervals (< 2.0s)
            valid_deltas = deltas[deltas < 2.0]
            if len(valid_deltas) >= 30:
                std_dev = np.std(valid_deltas)
                if std_dev < 0.015: # < 15ms variance
                    sig = IntegritySignal(
                        session_id=session_id,
                        event_id=events[0].id,
                        signal_type="UNIFORM_TYPING",
                        severity="LOW",
                        description=f"Evidence for review: Keystroke interval standard deviation is suspiciously low ({std_dev*1000:.1f}ms).",
                        timestamp=events[0].timestamp
                    )
                    db.add(sig)
                    generated_signals.append(sig)

        db.commit()
        return generated_signals
