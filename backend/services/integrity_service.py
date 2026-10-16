from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from backend.config import settings
from backend.models.session import Session as CodingSession, SessionEvent, CodeRevision
from backend.models.integrity import IntegritySignal
from backend.models.user import User

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
        if norm_type in ["FOCUS", "BLUR", "VISIBILITY_CHANGE", "TAB_SWITCH"]:
            return ("Application visibility change", "NORMAL_RHYTHM", "Browser focus or visibility change observed.")

        # 10. Lifecycle
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
