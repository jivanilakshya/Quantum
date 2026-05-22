"""
Gemini AI summary generation service.

Requirements addressed:
- Structured JSON output (short/detailed summary, key points, decisions, action items, sentiment, outcome)
- Prompt engineering + schema constraints
- Robust parsing with retries (Gemini sometimes returns markdown fences or near-JSON)
- Large transcript chunking (summarize chunks, then synthesize final)
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.gemini_api_key)


def _strip_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        # Remove ```json / ``` and trailing ```
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"\n?```$", "", t)
    return t.strip()


def _safe_json_loads(text: str) -> Dict[str, Any]:
    t = _strip_code_fences(text)
    return json.loads(t)


def _chunk_text(text: str, max_chars: int = 12000) -> List[str]:
    """
    Conservative chunking by characters.
    For long meetings, we chunk to stay within model input limits without needing tokenizers.
    """
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        # try to split on newline boundary
        nl = text.rfind("\n", start, end)
        if nl > start + int(max_chars * 0.6):
            end = nl
        chunks.append(text[start:end].strip())
        start = end
    return [c for c in chunks if c]


class GeminiService:
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        # keep model configurable for future upgrades
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)

    def generate_meeting_summary(
        self,
        *,
        transcript_text: str,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.5,
    ) -> Dict[str, Any]:
        if not transcript_text or not transcript_text.strip():
            raise ValueError("Empty transcript")

        chunks = _chunk_text(transcript_text)
        logger.info("Gemini summary generation: transcript_len=%s chunks=%s", len(transcript_text), len(chunks))

        if len(chunks) == 1:
            return self._generate_structured_summary(chunks[0], max_retries=max_retries, retry_delay_seconds=retry_delay_seconds)

        # Chunk summaries then final synthesis
        partials: List[Dict[str, Any]] = []
        for idx, c in enumerate(chunks, start=1):
            logger.info("Gemini chunk summary %s/%s len=%s", idx, len(chunks), len(c))
            partials.append(
                self._generate_structured_summary(
                    c,
                    max_retries=max_retries,
                    retry_delay_seconds=retry_delay_seconds,
                    mode="chunk",
                )
            )

        synthesis_prompt = (
            "You are consolidating multiple chunk-level meeting analyses into ONE final meeting summary.\n"
            "Merge and deduplicate items. Preserve factual consistency.\n"
            "Return ONLY valid JSON matching the schema.\n\n"
            "Schema:\n"
            "{\n"
            '  "short_summary": string,\n'
            '  "detailed_summary": string,\n'
            '  "key_points": string[],\n'
            '  "decisions": string[],\n'
            '  "action_items": [{"task": string, "owner": string|null, "due_date": string|null, "priority": "high"|"medium"|"low"|null}],\n'
            '  "sentiment": {"overall": "positive"|"neutral"|"negative", "confidence": number, "notes": string},\n'
            '  "meeting_outcome": string\n'
            "}\n\n"
            "Chunk analyses JSON array:\n"
            f"{json.dumps(partials, ensure_ascii=False)}\n"
        )

        return self._call_json(synthesis_prompt, max_retries=max_retries, retry_delay_seconds=retry_delay_seconds)

    def _generate_structured_summary(
        self,
        transcript_chunk: str,
        *,
        max_retries: int,
        retry_delay_seconds: float,
        mode: str = "full",
    ) -> Dict[str, Any]:
        prompt = (
            "You are an expert meeting analyst.\n"
            "Extract a structured meeting summary from the transcript.\n"
            "The transcript may contain speaker labels like 'Name: text'.\n"
            "If information is missing, use null (not empty string) for unknown fields.\n"
            "Return ONLY valid JSON matching the schema.\n\n"
            "Schema:\n"
            "{\n"
            '  "short_summary": string,\n'
            '  "detailed_summary": string,\n'
            '  "key_points": string[],\n'
            '  "decisions": string[],\n'
            '  "action_items": [{"task": string, "owner": string|null, "due_date": string|null, "priority": "high"|"medium"|"low"|null}],\n'
            '  "sentiment": {"overall": "positive"|"neutral"|"negative", "confidence": number, "notes": string},\n'
            '  "meeting_outcome": string\n'
            "}\n\n"
            f"Mode: {mode}\n\n"
            "Transcript:\n"
            f"{transcript_chunk}\n"
        )

        return self._call_json(prompt, max_retries=max_retries, retry_delay_seconds=retry_delay_seconds)

    def _call_json(self, prompt: str, *, max_retries: int, retry_delay_seconds: float) -> Dict[str, Any]:
        last_err: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            logger.info("Gemini request attempt %s/%s model=%s", attempt, max_retries, self.model_name)
            try:
                resp = self.model.generate_content(prompt)
                text = (resp.text or "").strip()
                logger.info("Gemini response chars=%s", len(text))
                parsed = _safe_json_loads(text)
                _validate_summary_shape(parsed)
                return parsed
            except Exception as e:
                last_err = e
                logger.warning("Gemini JSON parse/validation failed attempt %s: %s", attempt, e)
                if attempt < max_retries:
                    time.sleep(retry_delay_seconds)
                    continue
                break

        raise RuntimeError(f"Gemini failed to return valid JSON after {max_retries} attempts: {last_err}")


def _validate_summary_shape(obj: Dict[str, Any]) -> None:
    required = ["short_summary", "detailed_summary", "key_points", "decisions", "action_items", "sentiment", "meeting_outcome"]
    for k in required:
        if k not in obj:
            raise ValueError(f"Missing key: {k}")
    if not isinstance(obj["key_points"], list) or not isinstance(obj["decisions"], list) or not isinstance(obj["action_items"], list):
        raise ValueError("Invalid list fields")
    if not isinstance(obj["sentiment"], dict) or "overall" not in obj["sentiment"]:
        raise ValueError("Invalid sentiment field")

