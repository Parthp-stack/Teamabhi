from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import json

from backend.config import settings
from backend.models.session import Session as CodingSession, SessionEvent, CodeRevision
from backend.models.integrity import IntegritySignal, IntegrityEvent
from backend.models.assessment_attempt import AssessmentWarning, AssessmentAttempt
from backend.models.user import User
from backend.models.coding import CodingProblem


class IntegrityService:
    @classmethod
    def classify_event(
        cls,
        event_type: str,
        inserted_count: int,
        deleted_count: int,
        duration: Optional[float],
        metadata: Optional[Dict[str, Any]] = None,
        session_event_count: int = 0
    ) -> Tuple[str, str, str]:
        """
        Classifies an editing event into:
        (classification, review_status, reason)
        Review status is strictly one of:
        - NORMAL_RHYTHM
        - REVIEW_SUGGESTED
        - INSUFFICIENT_DATA
        """
        m = metadata or {}
        norm_type = event_type.upper()

        # 1. Observed Paste Event
        if norm_type == "PASTE":
            char_count = inserted_count or m.get("length", 0) or len(m.get("text", "")) or m.get("charCount", 0)
            if char_count >= 80:
                return (
                    "Large paste",
                    "REVIEW_SUGGESTED",
                    f"Observed paste event inserted substantial content ({char_count} characters)."
                )
            return (
                "Normal paste",
                "NORMAL_RHYTHM",
                f"Small observed paste event ({char_count} characters)."
            )

        # 2. Replacement (substantial deletion + substantial insertion)
        if norm_type == "REPLACE" or (deleted_count >= 40 and inserted_count >= 40):
            if inserted_count >= 80 or deleted_count >= 80:
                return (
                    "Replacement",
                    "REVIEW_SUGGESTED",
                    f"Substantial replacement of existing code ({deleted_count} chars removed, {inserted_count} chars added)."
                )
            return (
                "Replacement",
                "NORMAL_RHYTHM",
                f"Normal localized code replacement ({deleted_count} chars removed, {inserted_count} chars added)."
            )

        # 3. Deletion
        if norm_type == "DELETE" or (deleted_count > 0 and inserted_count == 0):
            return (
                "Deletion",
                "NORMAL_RHYTHM",
                f"Observed deletion of {deleted_count} characters."
            )

        # 4. Typing / Rapid Insertion
        if norm_type in ["TYPE", "KEYSTROKE"]:
            # If session is just starting with very few events and no history
            if session_event_count < 3 and inserted_count < 30:
                return (
                    "Normal typing",
                    "NORMAL_RHYTHM",
                    "Typing rhythm consistent with observed activity."
                )

            # Check rapid bulk insertion
            # If large amount of code appeared within very short interval (< 1.5s) or duration is 0
            if inserted_count >= 100:
                if duration is not None and duration < 1.5:
                    return (
                        "Rapid bulk insertion",
                        "REVIEW_SUGGESTED",
                        f"Insertion size ({inserted_count} characters) appeared significantly faster than observed typing rhythm."
                    )
                elif duration is None:
                    return (
                        "Rapid bulk insertion",
                        "REVIEW_SUGGESTED",
                        f"Large bulk insertion of {inserted_count} characters without established typing duration."
                    )

            return (
                "Normal typing",
                "NORMAL_RHYTHM",
                "Typing rhythm consistent with observed activity."
            )

        # 5. Execution / Run
        if norm_type == "RUN":
            return ("Code execution", "NORMAL_RHYTHM", "Student initiated test execution in sandbox.")

        # 6. Submission
        if norm_type == "SUBMIT":
            return ("Code submission", "NORMAL_RHYTHM", "Student submitted assessment solution.")

        # 7. Edit after run
        if norm_type == "EDIT_AFTER_RUN":
            return ("Iterative edit after run", "NORMAL_RHYTHM", "Normal write-run-fix cycle iteration.")

        # 8. Copy
        if norm_type == "COPY":
            return ("Internal copy", "NORMAL_RHYTHM", "Copy command observed inside editor.")

        # 9. Browser visibility & focus changes
        if norm_type in ["FOCUS", "BLUR", "WINDOW_BLUR", "VISIBILITY_CHANGE", "TAB_SWITCH"]:
            desc = "Browser focus or visibility change observed."
            if norm_type in ["TAB_SWITCH", "VISIBILITY_CHANGE"]:
                desc = "Browser tab visibility altered."
            elif norm_type in ["BLUR", "WINDOW_BLUR"]:
                desc = "Window focus moved away from active assessment."
            return ("Application visibility change", "NORMAL_RHYTHM", desc)

        # 10. Integrity detection anomalies (Split screen, fullscreen, resize, inactivity)
        if norm_type == "POSSIBLE_SPLIT_SCREEN":
            return ("Possible split screen arrangement", "REVIEW_SUGGESTED", "Window width altered to side-by-side split screen proportion.")

        if norm_type == "FULLSCREEN_EXIT":
            return ("Fullscreen exit", "REVIEW_SUGGESTED", "Assessment environment exited fullscreen mode.")

        if norm_type == "RESIZE_ANOMALY":
            return ("Window dimension change", "NORMAL_RHYTHM", "Assessment viewport resized.")

        if norm_type == "SUSPICIOUS_INACTIVITY":
            return ("Suspicious inactivity period", "REVIEW_SUGGESTED", "Prolonged inactivity without typing or editing observed.")

        # 11. Lifecycle
        if norm_type in ["SESSION_START", "SESSION_END"]:
            return ("Session lifecycle", "NORMAL_RHYTHM", f"Assessment {norm_type.lower()}.")

        return ("Uncertain activity", "INSUFFICIENT_DATA", "Insufficient data to reliably determine how content appeared.")

    @classmethod
    def save_event_batch(
        cls,
        db: Session,
        session_id: int,
        student_id: int,
        batch_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Idempotently ingest an event batch.
        Prevents duplicate events on network retry using client_event_id.
        Maintains incremental CodeRevisions.
        """
        coding_session = db.query(CodingSession).filter(CodingSession.id == session_id).first()
        if not coding_session:
            raise ValueError(f"Session {session_id} not found")

        # Security check: Ensure session belongs to calling student
        if coding_session.student_id != student_id:
            raise PermissionError("Access denied: You cannot record events for another student's session")

        # Get existing client_event_ids to deduplicate retried packets
        existing_client_ids = set()
        incoming_client_ids = [e.get("client_event_id") for e in batch_events if e.get("client_event_id")]
        if incoming_client_ids:
            existing_rows = db.query(SessionEvent.client_event_id).filter(
                SessionEvent.session_id == session_id,
                SessionEvent.client_event_id.in_(incoming_client_ids)
            ).all()
            existing_client_ids = {r[0] for r in existing_rows if r[0]}

        # Current revision count
        last_rev = db.query(CodeRevision).filter(CodeRevision.session_id == session_id).order_by(CodeRevision.revision_number.desc()).first()
        current_rev_num = last_rev.revision_number if last_rev else 0
        last_source_code = last_rev.source_code if last_rev else ""

        total_session_events = db.query(SessionEvent).filter(SessionEvent.session_id == session_id).count()

        events_to_add = []
        new_revisions_to_add = []
        recorded_count = 0
        skipped_duplicates = 0

        now_utc = datetime.now(timezone.utc)

        for item in batch_events:
            client_id = item.get("client_event_id")
            if client_id and client_id in existing_client_ids:
                skipped_duplicates += 1
                continue

            event_type = item.get("event_type", "TYPE").upper()
            ins_count = int(item.get("inserted_character_count", 0) or 0)
            del_count = int(item.get("deleted_character_count", 0) or 0)
            duration = item.get("duration")
            meta = item.get("metadata") or {}
            current_code = item.get("current_code")

            # Check timestamp
            raw_ts = item.get("timestamp") or item.get("client_timestamp")
            if isinstance(raw_ts, str):
                try:
                    ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                except Exception:
                    ts = now_utc
            elif isinstance(raw_ts, datetime):
                ts = raw_ts
            else:
                ts = now_utc

            # Classify event
            total_session_events += 1
            classification, rev_status, reason = cls.classify_event(
                event_type=event_type,
                inserted_count=ins_count,
                deleted_count=del_count,
                duration=duration,
                metadata=meta,
                session_event_count=total_session_events
            )

            # Code Revision snapshot logic:
            # Create revision when current_code is provided and different, or on PASTE, RUN, SUBMIT
            rev_obj = None
            if current_code and current_code != last_source_code:
                current_rev_num += 1
                snap_type = "MAJOR_SNAPSHOT" if event_type in ["PASTE", "SUBMIT"] else "INCREMENTAL"
                diff_summary = f"+{ins_count} / -{del_count} chars" if (ins_count or del_count) else f"Action: {event_type}"
                rev_obj = CodeRevision(
                    session_id=session_id,
                    revision_number=current_rev_num,
                    snapshot_type=snap_type,
                    source_code=current_code,
                    diff_summary=diff_summary,
                    created_at=ts
                )
                new_revisions_to_add.append(rev_obj)
                last_source_code = current_code

            ev = SessionEvent(
                session_id=session_id,
                student_id=student_id,
                assessment_id=coding_session.assessment_id,
                client_event_id=client_id,
                event_type=event_type,
                server_timestamp=now_utc,
                client_timestamp=ts,
                timestamp=ts,
                code_location=item.get("code_location"),
                inserted_character_count=ins_count,
                deleted_character_count=del_count,
                duration=duration,
                review_status=rev_status,
                classification=classification,
                classification_reason=reason,
                event_metadata=meta
            )
            events_to_add.append((ev, rev_obj))
            recorded_count += 1

        # Commit revisions and events
        for ev, rev in events_to_add:
            if rev:
                db.add(rev)
                db.flush()
                ev.revision_id = rev.id
            db.add(ev)
            db.flush()
            if rev:
                rev.event_id = ev.id

            # Save unified IntegrityEvent
            mapped_type = ev.event_type
            action_desc = ev.classification
            details_str = ev.classification_reason
            risk = "NORMAL"

            if ev.event_type == "COPY":
                mapped_type = "COPY / CTRL+C"
                action_desc = "Code copied"
                details_str = f"Code copied from editor ({ev.event_metadata.get('copied_length', 0) if ev.event_metadata else 0} chars)"
                risk = "LOW"
            elif ev.event_type == "PASTE":
                mapped_type = "PASTE / CTRL+V"
                action_desc = "Code pasted"
                details_str = f"Code pasted (+{ev.inserted_character_count} chars)"
                risk = "MEDIUM" if ev.inserted_character_count >= 80 else "LOW"
            elif ev.event_type == "CUT":
                mapped_type = "CUT / CTRL+X"
                action_desc = "Code cut"
                details_str = f"Code cut (-{ev.deleted_character_count} chars)"
                risk = "LOW"
            elif ev.event_type in ["TYPE", "KEYSTROKE"]:
                mapped_type = "CODE_TYPED" if ev.review_status != "REVIEW_SUGGESTED" else "RAPID_INSERTION"
                action_desc = "Code typed"
                details_str = f"+{ev.inserted_character_count} characters inserted"
                risk = "MEDIUM" if ev.review_status == "REVIEW_SUGGESTED" else "NORMAL"
            elif ev.event_type == "DELETE":
                mapped_type = "CODE_DELETED"
                action_desc = "Code deleted"
                details_str = f"Deleted {ev.deleted_character_count} characters"
                risk = "NORMAL"
            elif ev.event_type == "REPLACE":
                mapped_type = "CODE_REPLACED"
                action_desc = "Code replaced"
                details_str = f"Replaced -{ev.deleted_character_count}/+{ev.inserted_character_count} characters"
                risk = "MEDIUM" if ev.inserted_character_count >= 80 else "NORMAL"
            elif ev.event_type == "RUN":
                mapped_type = "CODE_RUN"
                action_desc = "Test cases executed"
                details_str = "Test cases executed in sandbox"
                risk = "NORMAL"
            elif ev.event_type == "SUBMIT":
                mapped_type = "SUBMISSION"
                action_desc = "Code submitted"
                details_str = "Final assessment solution submitted"
                risk = "NORMAL"
            elif ev.event_type == "FOCUS":
                mapped_type = "EDITOR_FOCUSED"
                action_desc = "Editor focused"
                details_str = "Editor gained focus"
                risk = "NORMAL"
            elif ev.event_type == "BLUR":
                mapped_type = "EDITOR_UNFOCUSED"
                action_desc = "Editor unfocused"
                details_str = "Editor lost focus"
                risk = "NORMAL"
            elif ev.event_type in ["TAB_SWITCH", "VISIBILITY_CHANGE"]:
                mapped_type = "TAB_SWITCH"
                is_hidden = ev.event_metadata.get("hidden", True) if ev.event_metadata else True
                action_desc = "Assessment tab hidden" if is_hidden else "Assessment tab visible"
                details_str = "Application window became hidden" if is_hidden else "Application window became visible"
                risk = "MEDIUM" if is_hidden else "LOW"
            elif ev.event_type == "WINDOW_BLUR":
                mapped_type = "WINDOW_BLUR"
                action_desc = "Window lost focus"
                details_str = "Window lost focus"
                risk = "MEDIUM"
            elif ev.event_type == "FULLSCREEN_EXIT":
                mapped_type = "FULLSCREEN_EXIT"
                action_desc = "Fullscreen exited"
                details_str = "Assessment window exited fullscreen"
                risk = "MEDIUM"
            elif ev.event_type == "POSSIBLE_SPLIT_SCREEN":
                mapped_type = "POSSIBLE_SPLIT_SCREEN"
                action_desc = "Resize anomaly"
                details_str = "Window proportion consistent with side-by-side view"
                risk = "MEDIUM"
            elif ev.event_type == "RESIZE_ANOMALY":
                mapped_type = "RESIZE_ANOMALY"
                action_desc = "Viewport resized"
                details_str = "Window dimensions changed"
                risk = "NORMAL"

            meta_json = json.dumps(ev.event_metadata) if isinstance(ev.event_metadata, dict) else str(ev.event_metadata or "")
            integ_event = IntegrityEvent(
                student_id=student_id,
                assessment_id=str(coding_session.assessment_id) if coding_session.assessment_id else None,
                session_id=session_id,
                question_id=None,
                question_number=1,
                event_type=mapped_type,
                action=action_desc,
                details=details_str,
                risk_level=risk,
                source="CODING_ASSESSMENT",
                event_metadata=meta_json,
                timestamp=ev.timestamp
            )
            db.add(integ_event)

        db.commit()

        # Update overall session status
        cls.update_session_review_status(db, session_id)

        return {
            "status": "ok",
            "recorded_count": recorded_count,
            "skipped_duplicates": skipped_duplicates
        }

    @classmethod
    def update_session_review_status(cls, db: Session, session_id: int) -> str:
        """
        Calculates and updates the overall session review status:
        - INSUFFICIENT_DATA: Session too short, < 5 events, or < 10s duration
        - REVIEW_SUGGESTED: Any suspicious signals, large paste, rapid bulk insertion, or no cycle
        - NORMAL_RHYTHM: Editing activity consistent with observed session baseline
        """
        session = db.query(CodingSession).filter(CodingSession.id == session_id).first()
        if not session:
            return "INSUFFICIENT_DATA"

        events: List[SessionEvent] = db.query(SessionEvent).filter(
            SessionEvent.session_id == session_id
        ).order_by(SessionEvent.timestamp.asc()).all()

        typing_events = [e for e in events if e.event_type.upper() in ["TYPE", "KEYSTROKE"]]

        if len(events) < 4 or (len(typing_events) < 4 and len(events) < 6):
            session.overall_review_status = "INSUFFICIENT_DATA"
            db.commit()
            return "INSUFFICIENT_DATA"

        # Check total duration
        first_t = events[0].timestamp
        last_t = events[-1].timestamp
        total_duration = (last_t - first_t).total_seconds()
        if len(typing_events) < 5 and total_duration < 3.0:
            session.overall_review_status = "INSUFFICIENT_DATA"
            db.commit()
            return "INSUFFICIENT_DATA"

        # Check if any event has REVIEW_SUGGESTED
        has_review_suggested = any(e.review_status == "REVIEW_SUGGESTED" for e in events)

        # Check if any integrity signals exist
        signals_count = db.query(IntegritySignal).filter(IntegritySignal.session_id == session_id).count()

        if has_review_suggested or signals_count > 0:
            session.overall_review_status = "REVIEW_SUGGESTED"
        else:
            session.overall_review_status = "NORMAL_RHYTHM"

        db.commit()
        return session.overall_review_status

    @classmethod
    def get_typing_rhythm_metrics(cls, db: Session, session_id: int) -> Dict[str, Any]:
        """
        Calculates rolling estimate of the student's observed typing rhythm.
        """
        events: List[SessionEvent] = db.query(SessionEvent).filter(
            SessionEvent.session_id == session_id
        ).order_by(SessionEvent.timestamp.asc()).all()

        typing_events = [e for e in events if e.event_type in ["TYPE", "KEYSTROKE"]]
        paste_events = [e for e in events if e.event_type == "PASTE"]
        rapid_events = [e for e in events if e.classification == "Rapid bulk insertion"]

        if len(typing_events) < 5:
            return {
                "baseline_cps": 0.0,
                "mean_interval_seconds": 0.0,
                "typical_insertion_range": "5 - 20 chars",
                "typical_interval_range": "0.2s - 1.5s",
                "total_typing_events": len(typing_events),
                "total_paste_events": len(paste_events),
                "rapid_insertions_count": len(rapid_events),
                "review_status": "INSUFFICIENT_DATA",
                "status_message": "Insufficient data to assess typing rhythm."
            }

        intervals = []
        for i in range(1, len(typing_events)):
            dt = (typing_events[i].timestamp - typing_events[i - 1].timestamp).total_seconds()
            if 0.05 <= dt <= 5.0:
                intervals.append(dt)

        mean_interval = float(np.mean(intervals)) if intervals else 0.5
        total_inserted = sum(e.inserted_character_count for e in typing_events)
        total_time = sum(intervals) if intervals else 1.0
        cps = round(total_inserted / max(1.0, total_time), 2)

        session = db.query(CodingSession).filter(CodingSession.id == session_id).first()
        status = session.overall_review_status if session else "NORMAL_RHYTHM"

        if status == "REVIEW_SUGGESTED":
            msg = "Unusual insertion — review suggested."
        elif status == "INSUFFICIENT_DATA":
            msg = "Insufficient data to assess typing rhythm."
        else:
            msg = "Typing rhythm consistent with observed activity."

        return {
            "baseline_cps": cps,
            "mean_interval_seconds": round(mean_interval, 2),
            "typical_insertion_range": "5 - 20 chars",
            "typical_interval_range": f"{max(0.1, round(mean_interval*0.5, 1))}s - {round(mean_interval*2.0, 1)}s",
            "total_typing_events": len(typing_events),
            "total_paste_events": len(paste_events),
            "rapid_insertions_count": len(rapid_events),
            "review_status": status,
            "status_message": msg
        }

    @classmethod
    def analyze_session_events(cls, db: Session, session_id: int) -> List[IntegritySignal]:
        """
        Deep analysis of the recorded chronological events.
        Produces evidence-based integrity signals for human review.
        NEVER outputs an automated cheating verdict.
        """
        events: List[SessionEvent] = db.query(SessionEvent).filter(
            SessionEvent.session_id == session_id
        ).order_by(SessionEvent.timestamp.asc()).all()

        if not events:
            return []

        # Clear previously generated signals for idempotent recalculation
        db.query(IntegritySignal).filter(IntegritySignal.session_id == session_id).delete()
        db.commit()

        generated_signals: List[IntegritySignal] = []

        run_count = 0
        tab_switches: List[SessionEvent] = []
        keystroke_timestamps: List[float] = []
        paste_events: List[SessionEvent] = []

        for i, ev in enumerate(events):
            m = ev.event_metadata or {}
            norm_type = ev.event_type.upper()

            # 1. Check Large Paste
            if norm_type == "PASTE":
                paste_events.append(ev)
                char_count = ev.inserted_character_count or m.get("length", 0) or len(m.get("text", "")) or m.get("charCount", 0)
                if char_count >= 100:
                    severity = "HIGH" if char_count > 350 else "MEDIUM"
                    sig = IntegritySignal(
                        session_id=session_id,
                        event_id=ev.id,
                        signal_type="LARGE_PASTE",
                        severity=severity,
                        description=f"Evidence for review: Large code paste of {char_count} characters detected at {ev.timestamp.strftime('%H:%M:%S')}.",
                        timestamp=ev.timestamp,
                        review_status="PENDING"
                    )
                    db.add(sig)
                    generated_signals.append(sig)
                    ev.review_status = "REVIEW_SUGGESTED"
                    ev.classification = "Large paste"
                    ev.classification_reason = f"Observed paste event inserted substantial content ({char_count} characters)."

            # 2. Check Tab Switches / Visibility Change
            elif norm_type in ["TAB_SWITCH", "BLUR", "VISIBILITY_CHANGE"]:
                if norm_type in ["TAB_SWITCH", "BLUR"] or m.get("hidden") is True or m.get("action") == "hidden":
                    tab_switches.append(ev)

            # 3. Check Run
            elif norm_type == "RUN":
                run_count += 1

            # 4. Keystroke timing collection
            elif norm_type in ["KEYSTROKE", "TYPE"]:
                keystroke_timestamps.append(ev.timestamp.timestamp())

            # 5. Check Rapid Bulk Insertion / Fast Code
            if i > 0 and norm_type in ["TYPE", "KEYSTROKE", "REPLACE"]:
                prev_ev = events[i - 1]
                time_diff = (ev.timestamp - prev_ev.timestamp).total_seconds()
                diff_len = ev.inserted_character_count or m.get("added_length", 0) or m.get("charCount", 0)
                if time_diff < 2.0 and diff_len >= 120 and norm_type != "PASTE":
                    sig = IntegritySignal(
                        session_id=session_id,
                        event_id=ev.id,
                        signal_type="FAST_CODE",
                        severity="MEDIUM",
                        description=f"Evidence for review: Unusually rapid code appearance (+{diff_len} chars in {time_diff:.1f}s) at {ev.timestamp.strftime('%H:%M:%S')}.",
                        timestamp=ev.timestamp,
                        review_status="PENDING"
                    )
                    db.add(sig)
                    generated_signals.append(sig)
                    ev.review_status = "REVIEW_SUGGESTED"
                    ev.classification = "Rapid bulk insertion"
                    ev.classification_reason = f"Insertion size (+{diff_len} chars) appeared significantly faster than observed typing rhythm."

        # Tab switch frequency signal
        if len(tab_switches) >= 2:
            first_switch = tab_switches[0]
            sig = IntegritySignal(
                session_id=session_id,
                event_id=first_switch.id,
                signal_type="TAB_SWITCH",
                severity="MEDIUM" if len(tab_switches) < 4 else "HIGH",
                description=f"Evidence for review: Student navigated away from editor {len(tab_switches)} times during assessment.",
                timestamp=first_switch.timestamp,
                review_status="PENDING"
            )
            db.add(sig)
            generated_signals.append(sig)

        # Write -> Run -> Fix Cycle Analysis
        submit_events = [e for e in events if e.event_type.upper() == "SUBMIT"]
        if submit_events and run_count <= 1:
            last_submit = submit_events[-1]
            sig = IntegritySignal(
                session_id=session_id,
                event_id=last_submit.id,
                signal_type="NO_CYCLE",
                severity="MEDIUM",
                description=f"Evidence for review: Solution submitted with only {run_count} execution run, lacking standard incremental debugging cycles.",
                timestamp=last_submit.timestamp,
                review_status="PENDING"
            )
            db.add(sig)
            generated_signals.append(sig)

        # Uniform Typing Interval Check
        if len(keystroke_timestamps) >= 40:
            deltas = np.diff(keystroke_timestamps)
            valid_deltas = deltas[deltas < 2.0]
            if len(valid_deltas) >= 30:
                std_dev = float(np.std(valid_deltas))
                if std_dev < 0.015: # < 15ms variance
                    sig = IntegritySignal(
                        session_id=session_id,
                        event_id=events[0].id,
                        signal_type="UNIFORM_TYPING",
                        severity="LOW",
                        description=f"Evidence for review: Keystroke interval standard deviation is suspiciously low ({std_dev*1000:.1f}ms).",
                        timestamp=events[0].timestamp,
                        review_status="PENDING"
                    )
                    db.add(sig)
                    generated_signals.append(sig)

        db.commit()

        # Update overall session status
        cls.update_session_review_status(db, session_id)

        return generated_signals

    @classmethod
    def apply_trainer_review_action(
        cls,
        db: Session,
        session_id: int,
        trainer_user_id: int,
        action: str, # MARK_REVIEWED, DISMISS, ADD_NOTE
        notes: Optional[str] = None,
        signal_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Trainer marks events/signals as reviewed, dismissed, or adds review notes.
        Does NOT automatically fail or accuse the student.
        """
        session = db.query(CodingSession).filter(CodingSession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        now_utc = datetime.now(timezone.utc)

        if signal_id:
            signal = db.query(IntegritySignal).filter(
                IntegritySignal.id == signal_id,
                IntegritySignal.session_id == session_id
            ).first()
            if signal:
                if action == "MARK_REVIEWED":
                    signal.review_status = "REVIEWED"
                elif action == "DISMISS":
                    signal.review_status = "DISMISSED"
                if notes:
                    signal.trainer_notes = notes
                signal.reviewed_by = trainer_user_id
                signal.reviewed_at = now_utc

        if action == "MARK_REVIEWED":
            session.is_reviewed = True
        elif action == "DISMISS":
            session.is_reviewed = True
            session.overall_review_status = "NORMAL_RHYTHM"

        if notes:
            existing_note = session.review_notes or ""
            timestamp_str = now_utc.strftime("%Y-%m-%d %H:%M:%S")
            session.review_notes = f"{existing_note}\n[{timestamp_str}]: {notes}".strip()

        session.reviewed_by = trainer_user_id
        session.reviewed_at = now_utc

        db.commit()
        return {
            "status": "success",
            "session_id": session_id,
            "action": action,
            "is_reviewed": session.is_reviewed,
            "overall_review_status": session.overall_review_status,
            "review_notes": session.review_notes
        }

    @classmethod
    def cleanup_expired_records(cls, db: Session, retention_days: Optional[int] = None) -> int:
        """
        Deletes old audit records exceeding the configured retention period.
        Configurable via settings.INTEGRITY_DATA_RETENTION_DAYS.
        """
        days = retention_days if retention_days is not None else settings.INTEGRITY_DATA_RETENTION_DAYS
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        expired_sessions = db.query(CodingSession).filter(
            CodingSession.started_at < cutoff,
            CodingSession.is_reviewed == True
        ).all()

        count = len(expired_sessions)
        for s in expired_sessions:
            db.delete(s)
        db.commit()
        return count

    @classmethod
    def record_warning(
        cls,
        db: Session,
        student_id: int,
        warning_type: str,
        message: str,
        severity: str = "LOW",
        session_id: Optional[int] = None,
        assessment_id: Optional[str] = None,
        attempt_id: Optional[int] = None,
        evidence: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record a progressive assessment warning.
        1st warning: Non-accusatory alert to student.
        Subsequent warnings: Escalating risk score, recorded for human review.
        """
        query = db.query(AssessmentWarning).filter(AssessmentWarning.student_id == student_id)
        if session_id:
            query = query.filter(AssessmentWarning.session_id == session_id)
        elif attempt_id:
            query = query.filter(AssessmentWarning.attempt_id == attempt_id)

        prev_warnings_count = query.count()
        warning_number = prev_warnings_count + 1

        # Escalated severity if multiple warnings
        effective_severity = severity
        if warning_number >= 3:
            effective_severity = "HIGH"
        elif warning_number >= 2 and severity == "LOW":
            effective_severity = "MEDIUM"

        warning_obj = AssessmentWarning(
            student_id=student_id,
            assessment_id=str(assessment_id) if assessment_id else None,
            attempt_id=attempt_id,
            session_id=session_id,
            warning_type=warning_type,
            warning_number=warning_number,
            message=message,
            severity=effective_severity,
            evidence=evidence,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(warning_obj)
        db.commit()
        db.refresh(warning_obj)

        # Update Session / AssessmentAttempt warnings count and risk score
        risk_score = min(100.0, warning_number * 25.0)
        risk_level = "NORMAL"
        if risk_score >= 70.0:
            risk_level = "HIGH_RISK"
        elif risk_score >= 40.0:
            risk_level = "MEDIUM_RISK"
        elif risk_score > 0.0:
            risk_level = "LOW_RISK"

        if attempt_id:
            att = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()
            if att:
                att.warnings_count = warning_number
                att.risk_score = risk_score
                att.risk_level = risk_level
                db.commit()

        if session_id:
            if warning_number >= 2 or effective_severity in ["MEDIUM", "HIGH"]:
                sig = IntegritySignal(
                    session_id=session_id,
                    signal_type=warning_type,
                    severity=effective_severity,
                    description=f"Evidence for review: Repeated environment interruption ({warning_type}, warning #{warning_number}) - {message}",
                    timestamp=datetime.now(timezone.utc),
                    review_status="PENDING"
                )
                db.add(sig)
                db.commit()
            cls.update_session_review_status(db, session_id)

        # Also save to unified IntegrityEvent table
        integ_w = IntegrityEvent(
            student_id=student_id,
            assessment_id=str(assessment_id) if assessment_id else None,
            attempt_id=attempt_id,
            session_id=session_id,
            question_number=None,
            event_type=warning_type,
            action=f"Warning #{warning_number} issued",
            details=message,
            risk_level=effective_severity,
            warning=f"Warning #{warning_number}: {message}",
            source="BROWSER" if not session_id else "CODING_ASSESSMENT",
            event_metadata=json.dumps(evidence) if isinstance(evidence, dict) else str(evidence or {}),
            timestamp=datetime.now(timezone.utc)
        )
        db.add(integ_w)
        db.commit()

        return {
            "warning_id": warning_obj.id,
            "warning_number": warning_number,
            "warning_type": warning_type,
            "severity": effective_severity,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "message": message,
            "timestamp": warning_obj.timestamp.isoformat()
        }

    @classmethod
    def record_integrity_event(
        cls,
        db: Session,
        student_id: int,
        event_type: str,
        action: Optional[str] = None,
        details: Optional[str] = None,
        risk_level: Optional[str] = None,
        warning: Optional[str] = None,
        source: str = "ASSESSMENT",
        assessment_id: Optional[str] = None,
        attempt_id: Optional[int] = None,
        session_id: Optional[int] = None,
        question_id: Optional[int] = None,
        question_number: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record any integrity event across Coding Assessment, Adaptive Assessment, or Browser Activity.
        """
        meta_dict = metadata or {}
        norm_type = event_type.upper()

        # Determine risk level if not explicitly provided
        if not risk_level:
            if "POSSIBLE_SPLIT_SCREEN" in norm_type or "FULLSCREEN_EXIT" in norm_type or "TAB_SWITCH" in norm_type or "WINDOW_BLUR" in norm_type or "PASTE" in norm_type:
                risk_level = "MEDIUM"
            elif "COPY" in norm_type or "FOCUS" in norm_type:
                risk_level = "LOW"
            else:
                risk_level = "NORMAL"

        # Determine progressive warning if applicable
        warning_msg = warning
        if risk_level in ["MEDIUM", "HIGH"] and not warning_msg:
            q_prev = db.query(IntegrityEvent).filter(
                IntegrityEvent.student_id == student_id,
                IntegrityEvent.warning.isnot(None)
            )
            if attempt_id:
                q_prev = q_prev.filter(IntegrityEvent.attempt_id == attempt_id)
            prev_w_count = q_prev.count()
            w_num = prev_w_count + 1
            if w_num == 1:
                warning_msg = f"Warning #1: Assessment environment interruption detected ({event_type}). Please remain in the assessment window."
            else:
                warning_msg = f"Warning #{w_num}: Continued environment interruptions recorded ({event_type}). Please keep the assessment tab active."

        integ_event = IntegrityEvent(
            student_id=student_id,
            assessment_id=str(assessment_id) if assessment_id else None,
            attempt_id=attempt_id,
            session_id=session_id,
            question_id=question_id,
            question_number=question_number,
            event_type=event_type,
            action=action or event_type,
            details=details or action or event_type,
            risk_level=risk_level,
            warning=warning_msg,
            source=source,
            event_metadata=json.dumps(meta_dict) if isinstance(meta_dict, dict) else str(meta_dict),
            timestamp=datetime.now(timezone.utc)
        )
        db.add(integ_event)

        # Update attempt risk score if attempt_id is provided
        if attempt_id:
            att = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()
            if att:
                att.integrity_events_count += 1
                if warning_msg:
                    att.warnings_count += 1
                att.risk_score = min(100.0, att.warnings_count * 25.0 + (10.0 if risk_level == "MEDIUM" else 25.0 if risk_level == "HIGH" else 0.0))
                if att.risk_score >= 70.0:
                    att.risk_level = "HIGH_RISK"
                elif att.risk_score >= 40.0:
                    att.risk_level = "MEDIUM_RISK"
                elif att.risk_score > 0.0:
                    att.risk_level = "LOW_RISK"

        db.commit()
        db.refresh(integ_event)

        return {
            "id": integ_event.id,
            "student_id": integ_event.student_id,
            "event_type": integ_event.event_type,
            "action": integ_event.action,
            "details": integ_event.details,
            "risk_level": integ_event.risk_level,
            "warning": integ_event.warning,
            "question_number": integ_event.question_number,
            "timestamp": integ_event.timestamp.isoformat()
        }

    @classmethod
    def get_integrity_events_table(
        cls,
        db: Session,
        student_id: Optional[int] = None,
        assessment_id: Optional[str] = None,
        attempt_id: Optional[int] = None,
        event_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        limit: int = 200,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Fetches the complete Student Integrity table and DB-computed summary cards.
        Supports sorting, filtering by student, assessment, attempt, event type, risk level, search, and chronological ordering.
        """
        query = db.query(IntegrityEvent).join(User, IntegrityEvent.student_id == User.id)

        # Filters
        if student_id:
            query = query.filter(IntegrityEvent.student_id == student_id)
        if assessment_id:
            query = query.filter(IntegrityEvent.assessment_id == str(assessment_id))
        if attempt_id:
            query = query.filter(IntegrityEvent.attempt_id == attempt_id)
        if event_type and event_type.upper() != "ALL":
            query = query.filter(IntegrityEvent.event_type.ilike(f"%{event_type}%"))
        if risk_level and risk_level.upper() != "ALL":
            query = query.filter(IntegrityEvent.risk_level == risk_level.upper())
        if search:
            s = f"%{search}%"
            query = query.filter(
                User.name.ilike(s) |
                User.email.ilike(s) |
                IntegrityEvent.details.ilike(s) |
                IntegrityEvent.action.ilike(s) |
                IntegrityEvent.event_type.ilike(s)
            )

        # Sorting
        if sort_by == "student_name":
            order_col = User.name.desc() if sort_order == "desc" else User.name.asc()
        elif sort_by == "risk_level":
            order_col = IntegrityEvent.risk_level.desc() if sort_order == "desc" else IntegrityEvent.risk_level.asc()
        elif sort_by == "event_type":
            order_col = IntegrityEvent.event_type.desc() if sort_order == "desc" else IntegrityEvent.event_type.asc()
        else:
            order_col = IntegrityEvent.timestamp.desc() if sort_order == "desc" else IntegrityEvent.timestamp.asc()

        total_filtered = query.count()
        events = query.order_by(order_col).offset(offset).limit(limit).all()

        # Summary query
        base_summary_q = db.query(IntegrityEvent)
        if student_id:
            base_summary_q = base_summary_q.filter(IntegrityEvent.student_id == student_id)
        if assessment_id:
            base_summary_q = base_summary_q.filter(IntegrityEvent.assessment_id == str(assessment_id))
        if attempt_id:
            base_summary_q = base_summary_q.filter(IntegrityEvent.attempt_id == attempt_id)

        all_evs = base_summary_q.all()

        total_events = len(all_evs)
        copy_events = sum(1 for e in all_evs if "COPY" in e.event_type.upper() or "CTRL+C" in e.event_type.upper())
        paste_events = sum(1 for e in all_evs if "PASTE" in e.event_type.upper() or "CTRL+V" in e.event_type.upper())
        tab_switches = sum(1 for e in all_evs if "TAB_SWITCH" in e.event_type.upper())
        window_blur_events = sum(1 for e in all_evs if "WINDOW_BLUR" in e.event_type.upper())
        fullscreen_exits = sum(1 for e in all_evs if "FULLSCREEN_EXIT" in e.event_type.upper())
        possible_split_screen_events = sum(1 for e in all_evs if "POSSIBLE_SPLIT_SCREEN" in e.event_type.upper())
        code_runs = sum(1 for e in all_evs if e.event_type.upper() in ["CODE_RUN", "RUN"])
        submissions = sum(1 for e in all_evs if e.event_type.upper() in ["SUBMISSION", "SUBMIT"])
        warnings_count = sum(1 for e in all_evs if e.warning is not None and len(e.warning.strip()) > 0)

        calc_risk_score = min(100.0, warnings_count * 20.0 + possible_split_screen_events * 15.0 + tab_switches * 10.0 + paste_events * 5.0)
        overall_risk = "NORMAL"
        if calc_risk_score >= 70:
            overall_risk = "HIGH"
        elif calc_risk_score >= 40:
            overall_risk = "MEDIUM"
        elif calc_risk_score > 0:
            overall_risk = "LOW"

        rows = []
        for e in events:
            q_num_str = f"Q{e.question_number}" if e.question_number else "-"
            att_no = e.attempt.attempt_number if e.attempt else (1 if e.session_id else "-")
            asst_label = e.assessment_id or "Assessment"

            rows.append({
                "id": e.id,
                "timestamp": e.timestamp.strftime("%H:%M:%S") if e.timestamp else "-",
                "timestamp_full": e.timestamp.isoformat() if e.timestamp else None,
                "student_name": e.student.name if e.student else "Student",
                "student_id": e.student_id,
                "assessment": asst_label,
                "attempt_no": att_no,
                "question_no": q_num_str,
                "event_type": e.event_type,
                "action": e.action or e.event_type,
                "details": e.details or "-",
                "risk_level": e.risk_level.title() if e.risk_level else "Normal",
                "warning": e.warning or "-",
                "source": e.source.replace("_", " ").title() if e.source else "Assessment"
            })

        return {
            "summary": {
                "total_events": total_events,
                "copy_events": copy_events,
                "paste_events": paste_events,
                "tab_switches": tab_switches,
                "window_blur_events": window_blur_events,
                "fullscreen_exits": fullscreen_exits,
                "possible_split_screen_events": possible_split_screen_events,
                "code_runs": code_runs,
                "submissions": submissions,
                "warnings": warnings_count,
                "risk_score": calc_risk_score,
                "risk_level": overall_risk
            },
            "total": total_filtered,
            "events": rows
        }

