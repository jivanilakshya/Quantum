"""
Vexa AI Client for Meeting Bot Management and Transcription
Handles all interactions with the Vexa AI API
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Retry configuration for transcript fetching.
# Vexa bots take time to join and begin transcribing after being dispatched.
# Without retries, an immediate request after dispatch often returns HTTP 200 with
# an empty body shape — the transcript only appears after the bot captures audio.
TRANSCRIPT_RETRY_COUNT = 5
TRANSCRIPT_RETRY_DELAY_SECONDS = 15

# HTTP client timeout: distinguish connection vs read vs write failures in logs.
_VEXA_TIMEOUT = httpx.Timeout(30.0, connect=10.0)

# If ``transcript`` exists but is empty/null, Vexa may still populate ``segments`` — keep parsing.
_TRANSCRIPT_FALLTHROUGH_REASONS = frozenset(
    {
        "transcript_null",
        "transcript_empty_list",
        "transcript_empty_string",
        "transcript_bad_type",
    }
)


@dataclass(frozen=True)
class TranscriptExtractionResult:
    """Normalized output from extract_transcript (plain text + optional segment rows)."""

    text: str
    segments: Tuple[Dict[str, Any], ...]
    structure_type: str
    reason: str

    @property
    def segment_count(self) -> int:
        return len(self.segments)


def extract_transcript(data: Any, *, log_context: str = "") -> TranscriptExtractionResult:
    """
    Reusable extraction of human-readable transcript text from heterogeneous Vexa payloads.

    Why structures vary: Vexa serves multiple platforms and API revisions. Some endpoints
    return a flat ``transcript`` string, others nest under ``data``, and many live pipelines
    emit time-ordered ``segments`` with ``speaker`` / ``text`` instead of a single string.
    Segment parsing is required because that is often the only populated field when the
    meeting is still active or when the gateway normalizes streaming output into segments.

    Reconstruction: non-empty segment texts are concatenated in order, one utterance per
    line; when ``speaker`` is present, lines are prefixed as ``Speaker: text`` for readability.
    """
    prefix = f"[{log_context}] " if log_context else ""

    if data is None:
        logger.warning("%sVexa transcript payload is null", prefix)
        return TranscriptExtractionResult("", (), "none", "empty_response")

    if not isinstance(data, dict):
        logger.warning(
            "%sVexa transcript payload has unexpected type: %s",
            prefix,
            type(data).__name__,
        )
        return TranscriptExtractionResult("", (), "none", "malformed_not_dict")

    # Always log the raw payload at INFO so production issues are diagnosable without DEBUG.
    try:
        raw_preview = json.dumps(data, default=str)[:8000]
    except (TypeError, ValueError):
        raw_preview = str(data)[:8000]
    logger.info("%sRaw Vexa transcript JSON (truncated if long): %s", prefix, raw_preview)

    nested_data = data.get("data")

    # --- 1) Top-level transcript (string or list of entries) ---
    if "transcript" in data:
        result = _extract_from_transcript_value(data["transcript"], prefix, source="direct_transcript")
        if result.reason == "ok" or result.text:
            logger.info(
                "%sTranscript extraction OK: structure=%s segment_count=%s length=%s",
                prefix,
                result.structure_type,
                result.segment_count,
                len(result.text),
            )
            return result
        if result.reason not in _TRANSCRIPT_FALLTHROUGH_REASONS:
            return result

    # --- 2) Nested data.transcript ---
    if isinstance(nested_data, dict) and "transcript" in nested_data:
        result = _extract_from_transcript_value(
            nested_data["transcript"], prefix, source="nested_data_transcript"
        )
        if result.reason == "ok" or result.text:
            logger.info(
                "%sTranscript extraction OK: structure=%s segment_count=%s length=%s",
                prefix,
                result.structure_type,
                result.segment_count,
                len(result.text),
            )
            return result
        if result.reason not in _TRANSCRIPT_FALLTHROUGH_REASONS:
            return result

    # --- 3) results.transcript (older gateways) ---
    results = data.get("results")
    if isinstance(results, dict) and "transcript" in results:
        result = _extract_from_transcript_value(
            results["transcript"], prefix, source="nested_results_transcript"
        )
        if result.reason == "ok" or result.text:
            logger.info(
                "%sTranscript extraction OK: structure=%s segment_count=%s length=%s",
                prefix,
                result.structure_type,
                result.segment_count,
                len(result.text),
            )
            return result
        if result.reason not in _TRANSCRIPT_FALLTHROUGH_REASONS:
            return result

    # --- 4) Plural transcripts key ---
    if "transcripts" in data:
        result = _extract_from_transcript_value(data["transcripts"], prefix, source="transcripts_key")
        if result.reason == "ok" or result.text:
            logger.info(
                "%sTranscript extraction OK: structure=%s segment_count=%s length=%s",
                prefix,
                result.structure_type,
                result.segment_count,
                len(result.text),
            )
            return result
        if result.reason not in _TRANSCRIPT_FALLTHROUGH_REASONS:
            return result

    # --- 5) segments (top-level or under data) ---
    segs = None
    if isinstance(data.get("segments"), list):
        segs = data["segments"]
        src = "segments_top_level"
    elif isinstance(nested_data, dict) and isinstance(nested_data.get("segments"), list):
        segs = nested_data["segments"]
        src = "nested_data_segments"

    if segs is not None:
        text, norm = _normalize_segment_list(segs)
        if text:
            logger.info(
                "%sTranscript extraction OK: structure=%s segment_count=%s length=%s",
                prefix,
                src,
                len(norm),
                len(text),
            )
            return TranscriptExtractionResult(text, tuple(norm), src, "ok")
        logger.warning(
            "%sSegments present but all empty or invalid (count=%s)", prefix, len(segs)
        )
        return TranscriptExtractionResult("", (), src, "segments_all_empty")

    logger.warning(
        "%sUnrecognized Vexa transcript shape. Top-level keys: %s",
        prefix,
        list(data.keys()),
    )
    return TranscriptExtractionResult("", (), "unknown", "unknown_format")


def _extract_from_transcript_value(
    value: Any, prefix: str, *, source: str
) -> TranscriptExtractionResult:
    if value is None:
        logger.warning("%s'%s': transcript field is null", prefix, source)
        return TranscriptExtractionResult("", (), source, "transcript_null")

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return TranscriptExtractionResult("", (), f"{source}_string", "transcript_empty_string")
        seg = {"speaker": None, "text": stripped, "timestamp": None}
        return TranscriptExtractionResult(stripped, (seg,), f"{source}_string", "ok")

    if isinstance(value, list):
        if len(value) == 0:
            logger.info("%s'%s': transcript list is empty", prefix, source)
            return TranscriptExtractionResult("", (), f"{source}_list", "transcript_empty_list")
        text, norm = _normalize_segment_list(value)
        if text:
            return TranscriptExtractionResult(text, tuple(norm), f"{source}_list", "ok")
        return TranscriptExtractionResult("", (), f"{source}_list", "transcript_empty_list")

    # dict transcript (rare) — try common nested keys
    if isinstance(value, dict):
        inner = (
            value.get("text")
            or value.get("content")
            or value.get("transcript")
            or value.get("segments")
        )
        if isinstance(inner, list):
            text, norm = _normalize_segment_list(inner)
            if text:
                return TranscriptExtractionResult(text, tuple(norm), f"{source}_dict", "ok")
        if isinstance(inner, str) and inner.strip():
            s = inner.strip()
            seg = {"speaker": value.get("speaker"), "text": s, "timestamp": value.get("timestamp")}
            line = f"{seg['speaker']}: {s}" if seg.get("speaker") else s
            return TranscriptExtractionResult(line, (seg,), f"{source}_dict", "ok")

    logger.warning("%s'%s': transcript field has unsupported type %s", prefix, source, type(value).__name__)
    return TranscriptExtractionResult("", (), source, "transcript_bad_type")


def _normalize_segment_list(raw_segments: List[Any]) -> Tuple[str, List[Dict[str, Any]]]:
    """Build readable multiline text and normalized segment dicts; skip empties safely."""
    lines: List[str] = []
    norm: List[Dict[str, Any]] = []

    for seg in raw_segments:
        if not isinstance(seg, dict):
            continue
        text_raw = seg.get("text") if "text" in seg else seg.get("content")
        if text_raw is None:
            continue
        if not isinstance(text_raw, str):
            text_raw = str(text_raw)
        text_clean = text_raw.strip()
        if not text_clean:
            continue

        speaker = seg.get("speaker") or seg.get("name") or seg.get("user")
        ts = seg.get("timestamp") or seg.get("time")

        norm.append({
            "speaker": speaker if isinstance(speaker, str) else None,
            "text": text_clean,
            "timestamp": ts if isinstance(ts, str) else None,
        })

        if speaker:
            lines.append(f"{speaker}: {text_clean}")
        else:
            lines.append(text_clean)

    return "\n".join(lines), norm


def normalize_bots_status_payload(raw: Any) -> List[Dict[str, Any]]:
    """
    Vexa /bots/status may return a bare list, or a wrapper object such as
    ``{"bots": [...]}``, ``{"data": [...]}``, or occasionally a single bot dict.
    This normalizes everything into a list of dicts for downstream iteration.
    """
    if raw is None:
        return []

    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]

    if isinstance(raw, dict):
        for key in ("bots", "data", "results", "items"):
            inner = raw.get(key)
            if isinstance(inner, list):
                return [x for x in inner if isinstance(x, dict)]

        # Single-bot object
        if any(k in raw for k in ("native_meeting_id", "meeting_id", "platform", "status")):
            return [raw]

    logger.warning(
        "Could not normalize bot status payload type=%s repr=%s",
        type(raw).__name__,
        str(raw)[:500],
    )
    return []


class BotRequest(BaseModel):
    """Request model for creating a bot"""

    platform: str  # "google_meet" or "teams"
    native_meeting_id: str
    passcode: Optional[str] = None  # Required for Teams
    language: Optional[str] = "en"
    bot_name: Optional[str] = "Quantum AI Bot"


class VexaClient:
    """Client for interacting with Vexa AI API"""

    def __init__(self, api_key: str, base_url: str = "https://api.cloud.vexa.ai"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    async def verify_bot_joined(self, platform: str, native_meeting_id: str) -> Tuple[bool, str]:
        """
        Check whether a Vexa bot is present for this meeting before spending retry budget.

        Returns:
            (bot_active: bool, reason: str)
        """
        try:
            raw = await self.get_bot_status()
            bots = normalize_bots_status_payload(raw)

            if not bots:
                logger.warning(
                    "[%s] Bot status returned no parseable bot list — allowing transcript fetch (best effort)",
                    native_meeting_id,
                )
                return True, "status_empty_unverified"

            for bot in bots:
                bot_meeting_id = (
                    bot.get("native_meeting_id") or bot.get("meeting_id") or bot.get("id")
                )
                bot_platform = str(bot.get("platform", "") or "")

                if str(bot_meeting_id) == str(native_meeting_id) and bot_platform == platform:
                    status = bot.get("status") or "unknown"
                    logger.info("[%s] Bot found — status: %s", native_meeting_id, status)

                    if status in ("failed", "stopped", "error"):
                        return False, f"bot_status_{status}"
                    return True, str(status)

            logger.warning(
                "[%s] No bot found for platform=%s meeting_id=%s", native_meeting_id, platform, native_meeting_id
            )
            return False, "no_bot_found"

        except Exception as e:
            logger.warning(
                "[%s] Bot status verification failed (non-critical): %s", native_meeting_id, e
            )
            return True, "verification_failed"

    async def request_bot(self, bot_request: BotRequest) -> Dict[str, Any]:
        """Request a bot to join a meeting"""
        url = f"{self.base_url}/bots"
        payload = bot_request.model_dump(exclude_none=True)

        async with httpx.AsyncClient(timeout=_VEXA_TIMEOUT) as client:
            try:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                logger.info("Bot requested successfully for meeting %s", bot_request.native_meeting_id)
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 409:
                    logger.warning("Bot already exists for meeting %s", bot_request.native_meeting_id)
                    return {"message": "Bot already exists for this meeting", "already_running": True}

                logger.error("HTTP error requesting bot: %s - Response: %s", e, e.response.text)
                raise Exception(f"Failed to request bot: {str(e)}") from e
            except httpx.RequestError as e:
                logger.error("Request error requesting bot: %s", e)
                raise Exception(f"Failed to request bot: {str(e)}") from e

    async def get_transcript(
        self, platform: str, native_meeting_id: str, with_retry: bool = False
    ) -> Dict[str, Any]:
        """
        Fetch the transcript for a meeting from the Vexa API.

        Retries (15s spacing, max 5) apply when ``with_retry=True`` until non-empty transcript
        text is extracted or attempts are exhausted. This covers bot warm-up and slow audio paths.

        Returns:
            dict with transcript_text (str), transcript_segments (list), message (str), reason (str).
        """
        url = f"{self.base_url}/transcripts/{platform}/{native_meeting_id}"
        max_attempts = TRANSCRIPT_RETRY_COUNT if with_retry else 1

        for attempt in range(1, max_attempts + 1):
            logger.info(
                "[%s] Transcript fetch attempt %s/%s",
                native_meeting_id,
                attempt,
                max_attempts,
            )

            async with httpx.AsyncClient(timeout=_VEXA_TIMEOUT) as client:
                try:
                    response = await client.get(url, headers=self.headers)
                    logger.info(
                        "[%s] Vexa transcript HTTP %s",
                        native_meeting_id,
                        response.status_code,
                    )
                    response.raise_for_status()

                    try:
                        data = response.json()
                    except json.JSONDecodeError as je:
                        logger.error(
                            "[%s] Invalid JSON from Vexa transcript endpoint (attempt %s): %s body=%s",
                            native_meeting_id,
                            attempt,
                            je,
                            response.text[:1000],
                        )
                        reason = "malformed_json"
                        if with_retry and attempt < max_attempts:
                            await asyncio.sleep(TRANSCRIPT_RETRY_DELAY_SECONDS)
                            continue
                        return {
                            "transcript_text": "",
                            "transcript_segments": [],
                            "message": "Vexa returned invalid JSON",
                            "reason": reason,
                        }

                    extracted = extract_transcript(data, log_context=native_meeting_id)

                    logger.info(
                        "[%s] Extraction structured: type=%s reason=%s seg_count=%s len=%s success=%s",
                        native_meeting_id,
                        extracted.structure_type,
                        extracted.reason,
                        extracted.segment_count,
                        len(extracted.text),
                        bool(extracted.text.strip()),
                    )

                    if extracted.text.strip():
                        logger.info(
                            "[%s] Transcript extracted successfully on attempt %s",
                            native_meeting_id,
                            attempt,
                        )
                        return {
                            "transcript_text": extracted.text,
                            "transcript_segments": list(extracted.segments),
                            "message": "Transcript retrieved successfully",
                            "reason": "ok",
                        }

                    reason_messages = {
                        "transcript_null": "Bot joined but has not captured any speech yet",
                        "transcript_empty_list": "Transcript is empty — meeting may have just started",
                        "transcript_empty_string": "Transcript field is blank",
                        "transcript_bad_type": "Transcript field has an unexpected type",
                        "segments_all_empty": "Segment entries are empty",
                        "unknown_format": "Vexa returned an unrecognized response structure",
                        "empty_response": "Vexa returned an empty response body",
                        "malformed_not_dict": "Vexa returned a non-object JSON body",
                        "malformed_json": "Malformed JSON from Vexa",
                    }
                    human_reason = reason_messages.get(
                        extracted.reason, f"Transcript unavailable ({extracted.reason})"
                    )
                    logger.warning(
                        "[%s] Attempt %s: extraction failed (%s) — %s",
                        native_meeting_id,
                        attempt,
                        extracted.reason,
                        human_reason,
                    )

                    if with_retry and attempt < max_attempts:
                        logger.info(
                            "[%s] Retrying in %ss (no transcript text yet)...",
                            native_meeting_id,
                            TRANSCRIPT_RETRY_DELAY_SECONDS,
                        )
                        await asyncio.sleep(TRANSCRIPT_RETRY_DELAY_SECONDS)
                        continue

                    return {
                        "transcript_text": "",
                        "transcript_segments": [],
                        "message": human_reason,
                        "reason": extracted.reason,
                    }

                except httpx.HTTPStatusError as e:
                    status_code = e.response.status_code
                    body = e.response.text

                    if status_code == 404:
                        logger.warning(
                            "[%s] 404 from Vexa — no bot joined or invalid meeting ID",
                            native_meeting_id,
                        )
                        return {
                            "transcript_text": "",
                            "transcript_segments": [],
                            "message": "No bot joined this meeting or meeting ID is incorrect",
                            "reason": "not_found",
                        }

                    logger.error(
                        "[%s] HTTP %s on attempt %s: %s",
                        native_meeting_id,
                        status_code,
                        attempt,
                        body[:2000],
                    )
                    if with_retry and attempt < max_attempts:
                        await asyncio.sleep(TRANSCRIPT_RETRY_DELAY_SECONDS)
                        continue

                    return {
                        "transcript_text": "",
                        "transcript_segments": [],
                        "message": f"Vexa API error HTTP {status_code}",
                        "reason": f"http_{status_code}",
                    }

                except httpx.TimeoutException as e:
                    logger.error("[%s] Timeout on attempt %s: %s", native_meeting_id, attempt, e)
                    if with_retry and attempt < max_attempts:
                        await asyncio.sleep(TRANSCRIPT_RETRY_DELAY_SECONDS)
                        continue
                    return {
                        "transcript_text": "",
                        "transcript_segments": [],
                        "message": "Request to Vexa timed out",
                        "reason": "timeout",
                    }

                except httpx.RequestError as e:
                    logger.error("[%s] Network error on attempt %s: %s", native_meeting_id, attempt, e)
                    if with_retry and attempt < max_attempts:
                        await asyncio.sleep(TRANSCRIPT_RETRY_DELAY_SECONDS)
                        continue
                    return {
                        "transcript_text": "",
                        "transcript_segments": [],
                        "message": f"Network error contacting Vexa: {e}",
                        "reason": "network_error",
                    }

        logger.error(
            "[%s] Transcript unavailable after %s attempts", native_meeting_id, max_attempts
        )
        return {
            "transcript_text": "",
            "transcript_segments": [],
            "message": f"Transcript unavailable after {max_attempts} attempts",
            "reason": "max_retries_exceeded",
        }

    async def get_bot_status(self) -> Any:
        """Get status of all running bots (raw payload; may be list or dict)."""
        url = f"{self.base_url}/bots/status"

        async with httpx.AsyncClient(timeout=_VEXA_TIMEOUT) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error("Failed to get bot status: %s", e)
                raise Exception(f"Failed to get bot status: {str(e)}") from e

    async def update_bot_config(
        self, platform: str, native_meeting_id: str, language: str
    ) -> Dict[str, Any]:
        """Update bot configuration (e.g., change language)"""
        url = f"{self.base_url}/bots/{platform}/{native_meeting_id}/config"
        payload = {"language": language}

        async with httpx.AsyncClient(timeout=_VEXA_TIMEOUT) as client:
            try:
                response = await client.put(url, headers=self.headers, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error("Failed to update bot config: %s", e)
                raise Exception(f"Failed to update bot config: {str(e)}") from e

    async def stop_bot(self, platform: str, native_meeting_id: str) -> Dict[str, Any]:
        """Stop a bot and remove it from the meeting"""
        url = f"{self.base_url}/bots/{platform}/{native_meeting_id}"

        async with httpx.AsyncClient(timeout=_VEXA_TIMEOUT) as client:
            try:
                response = await client.delete(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error("Failed to stop bot: %s", e)
                raise Exception(f"Failed to stop bot: {str(e)}") from e

    async def list_meetings(self) -> List[Dict[str, Any]]:
        """List all meetings associated with the API key"""
        url = f"{self.base_url}/meetings"

        async with httpx.AsyncClient(timeout=_VEXA_TIMEOUT) as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                return data if isinstance(data, list) else []
            except Exception as e:
                logger.error("Failed to list meetings: %s", e)
                raise Exception(f"Failed to list meetings: {str(e)}") from e

    async def update_meeting_data(
        self,
        platform: str,
        native_meeting_id: str,
        name: Optional[str] = None,
        participants: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update meeting metadata"""
        url = f"{self.base_url}/meetings/{platform}/{native_meeting_id}"
        data_body: Dict[str, Any] = {}

        if name:
            data_body["name"] = name
        if participants:
            data_body["participants"] = participants
        if languages:
            data_body["languages"] = languages
        if notes:
            data_body["notes"] = notes

        payload = {"data": data_body}

        async with httpx.AsyncClient(timeout=_VEXA_TIMEOUT) as client:
            try:
                response = await client.patch(url, headers=self.headers, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error("Failed to update meeting data: %s", e)
                raise Exception(f"Failed to update meeting data: {str(e)}") from e

    async def delete_meeting_transcripts(self, platform: str, native_meeting_id: str) -> Dict[str, Any]:
        """Delete meeting transcripts and anonymize data"""
        url = f"{self.base_url}/meetings/{platform}/{native_meeting_id}"

        async with httpx.AsyncClient(timeout=_VEXA_TIMEOUT) as client:
            try:
                response = await client.delete(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error("Failed to delete meeting transcripts: %s", e)
                raise Exception(f"Failed to delete meeting transcripts: {str(e)}") from e
