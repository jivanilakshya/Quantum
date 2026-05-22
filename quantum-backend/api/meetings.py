"""
Meeting Management API Endpoints
Handles meeting data and transcripts
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

from config import settings
from database import Meeting, Transcript, get_db
from services.security import get_current_user
from services.vexa_client import VexaClient
from services.transcript_store import store_transcript_segments

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Vexa client
vexa_client = VexaClient(api_key=settings.vexa_api_key, base_url=settings.vexa_base_url)


def _db_transcripts_to_plain_text(rows: List[Transcript]) -> str:
    """Join stored rows into one string consistent with Vexa line format (Speaker: text)."""
    lines: List[str] = []
    for t in rows:
        text = (t.text or "").strip()
        if not text:
            continue
        sp = (t.speaker or "").strip()
        lines.append(f"{sp}: {text}" if sp else text)
    return "\n".join(lines)

def _ensure_owner_access(db: Session, meeting_id: str, owner_email: str) -> None:
    meeting = db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()
    if meeting is None:
        return
    if meeting.owner_email and meeting.owner_email != owner_email:
        raise HTTPException(status_code=403, detail="You do not have access to this meeting")

def _rows_to_segments(rows: List[Transcript]) -> List[Dict[str, Any]]:
    segs: List[Dict[str, Any]] = []
    for t in rows:
        segs.append(
            {
                "transcript_id": t.transcript_id or t.id,
                "meeting_id": t.meeting_id,
                "speaker_name": (t.speaker_name or t.speaker),
                "timestamp": t.timestamp,
                "text": t.text,
                "created_at": t.created_at.isoformat() if getattr(t, "created_at", None) else None,
            }
        )
    return segs


class UpdateMeetingRequest(BaseModel):
    """Request to update meeting metadata"""

    name: Optional[str] = None
    participants: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    notes: Optional[str] = None


@router.get("/")
async def list_meetings():
    """
    List all meetings
    """
    try:
        meetings = await vexa_client.list_meetings()

        return {
            "success": True,
            "count": len(meetings) if isinstance(meetings, list) else 0,
            "meetings": meetings,
        }

    except Exception as e:
        logger.error("Failed to list meetings: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{platform}/{meeting_id}/transcript")
async def get_transcript(
    platform: str,
    meeting_id: str,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get transcript for a meeting. Can be called during or after the meeting.

    Fetch order:
      1. Verify a Vexa bot was dispatched (skips pointless retries when no bot exists).
      2. Fetch from Vexa with retry logic (5 attempts, 15s apart) until text is available.
      3. Fall back to local DB if Vexa has no data (meeting already processed and stored).

    Response contract (always JSON, never silent failure):
      ``{"success": true, "transcript": "<full text>"}`` or
      ``{"success": false, "error": "<message>"}``.
    """
    try:
        owner_email = str(user.get("sub"))
        _ensure_owner_access(db, meeting_id, owner_email)

        # --- Step 1: Bot presence (handles dict or list Vexa /bots/status payloads) ---
        bot_active, bot_reason = await vexa_client.verify_bot_joined(platform, meeting_id)

        if not bot_active:
            reason_map = {
                "no_bot_found": "No bot was requested for this meeting. Please start a bot first.",
                "bot_status_failed": "The bot failed to join this meeting.",
                "bot_status_stopped": "The bot has already left this meeting.",
                "bot_status_error": "The bot encountered an error joining this meeting.",
            }
            human_message = reason_map.get(
                bot_reason, f"Bot is not active for this meeting ({bot_reason})"
            )
            logger.warning("[%s] Skipping Vexa fetch — %s", meeting_id, human_message)

            db_transcripts = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).all()
            db_text = _db_transcripts_to_plain_text(db_transcripts)
            if db_text:
                logger.info("[%s] Served transcript from database after bot inactive", meeting_id)
                return {"success": True, "transcript": db_text}

            logger.warning("[%s] No transcript: bot inactive and DB empty", meeting_id)
            return {"success": False, "error": human_message}

        # --- Step 2: Vexa with retries (see vexa_client.TRANSCRIPT_*) ---
        transcript_result = await vexa_client.get_transcript(platform, meeting_id, with_retry=True)

        text = (transcript_result.get("transcript_text") or "").strip()
        segments = transcript_result.get("transcript_segments") or []

        # Store segments incrementally. This supports live updates and avoids duplicates.
        try:
            if segments:
                store_transcript_segments(
                    db,
                    platform=platform,
                    meeting_id=meeting_id,
                    segments=segments,
                    owner_email=owner_email,
                )
        except Exception as store_err:
            # Never fail silently: transcript can still be returned even if DB insert fails.
            logger.exception("[%s] Failed to persist transcript segments: %s", meeting_id, store_err)

        if text:
            logger.info(
                "[%s] Transcript from Vexa (len=%s reason=%s)",
                meeting_id,
                len(text),
                transcript_result.get("reason"),
            )
            return {"success": True, "transcript": text}

        # --- Step 3: DB fallback ---
        vexa_reason = transcript_result.get("reason", "unknown")
        vexa_message = transcript_result.get("message", "Vexa returned no transcript")
        logger.info(
            "[%s] Vexa transcript empty after retries (reason=%s) — checking local DB",
            meeting_id,
            vexa_reason,
        )

        db_transcripts = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).all()
        db_text = _db_transcripts_to_plain_text(db_transcripts)
        if db_text:
            logger.info("[%s] Served transcript from database", meeting_id)
            return {"success": True, "transcript": db_text}

        # Map internal reasons to user-facing guidance (explicit, not silent).
        detail = (
            vexa_message
            if vexa_reason
            not in (
                "empty_response",
                "unknown_format",
                "malformed_json",
                "malformed_not_dict",
            )
            else f"{vexa_message} (code: {vexa_reason})"
        )
        logger.warning("[%s] No transcript in Vexa or DB: %s", meeting_id, detail)
        return {"success": False, "error": detail}

    except Exception as e:
        logger.exception("[%s] Unexpected error fetching transcript", meeting_id)

        try:
            db_transcripts = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).all()
            db_text = _db_transcripts_to_plain_text(db_transcripts)
            if db_text:
                logger.info("[%s] Recovered transcript from DB after exception", meeting_id)
                return {"success": True, "transcript": db_text}
        except Exception as db_err:
            logger.error("[%s] DB recovery failed: %s", meeting_id, db_err)

        return {
            "success": False,
            "error": f"Failed to retrieve transcript: {e!s}",
        }


@router.get("/{meeting_id}/transcripts")
async def get_transcripts(
    meeting_id: str,
    limit: int = Query(200, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Paginated transcript segments history (persistent storage)."""
    owner_email = str(user.get("sub"))
    _ensure_owner_access(db, meeting_id, owner_email)
    rows = (
        db.query(Transcript)
        .filter(Transcript.meeting_id == meeting_id)
        .order_by(Transcript.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"success": True, "items": _rows_to_segments(rows), "limit": limit, "offset": offset}


@router.get("/{meeting_id}/transcript/full")
async def get_transcript_full(
    meeting_id: str,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Full merged transcript text (persistent storage)."""
    owner_email = str(user.get("sub"))
    _ensure_owner_access(db, meeting_id, owner_email)
    rows = (
        db.query(Transcript)
        .filter(Transcript.meeting_id == meeting_id)
        .order_by(Transcript.id.asc())
        .all()
    )
    return {"success": True, "transcript": _db_transcripts_to_plain_text(rows)}


@router.delete("/{meeting_id}/transcripts")
async def delete_transcripts(
    meeting_id: str,
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Optional: delete stored transcripts for a meeting."""
    owner_email = str(user.get("sub"))
    _ensure_owner_access(db, meeting_id, owner_email)
    deleted = db.query(Transcript).filter(Transcript.meeting_id == meeting_id).delete()
    db.commit()
    return {"success": True, "deleted": deleted}


@router.patch("/{platform}/{meeting_id}")
async def update_meeting(platform: str, meeting_id: str, request: UpdateMeetingRequest):
    """
    Update meeting metadata
    """
    try:
        result = await vexa_client.update_meeting_data(
            platform=platform,
            native_meeting_id=meeting_id,
            name=request.name,
            participants=request.participants,
            languages=request.languages,
            notes=request.notes,
        )

        return {
            "success": True,
            "message": "Meeting updated successfully",
            "data": result,
        }

    except Exception as e:
        logger.error("Failed to update meeting: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{platform}/{meeting_id}")
async def delete_meeting_transcripts(platform: str, meeting_id: str):
    """
    Delete meeting transcripts and anonymize data
    Only works for completed or failed meetings
    """
    try:
        result = await vexa_client.delete_meeting_transcripts(platform, meeting_id)

        return {
            "success": True,
            "message": "Meeting transcripts deleted and data anonymized",
            "data": result,
        }

    except Exception as e:
        logger.error("Failed to delete meeting transcripts: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
