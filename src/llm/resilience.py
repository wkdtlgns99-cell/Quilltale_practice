"""
LLM Resilience & JSON Auto-Repair Engine for Quilltale TRPG.
Handles network timeouts, 429 quota retries with exponential backoff,
and auto-repairs broken JSON responses (missing braces, markdown ticks, trailing commas).
"""
import re
import json
import time
import logging
from typing import Any, Dict, Optional, Callable

logger = logging.getLogger(__name__)


class JSONRepairEngine:
    """Repairs malformed JSON outputs from LLMs and guarantees human-readable prose."""

    @staticmethod
    def extract_clean_prose(data: Any) -> str:
        """Extracts pure narrative prose from parsed dict or malformed json text."""
        if isinstance(data, dict):
            # 1. Primary standard narration key
            if "narration" in data and isinstance(data["narration"], str) and not data["narration"].strip().startswith("{"):
                return data["narration"].strip()

            parts = []
            for key in ["scene_description", "description", "story", "text", "content", "response", "npc_action", "dialogue"]:
                if key in data:
                    val = data[key]
                    if isinstance(val, str) and val.strip() and not val.strip().startswith("{"):
                        parts.append(val.strip())
                    elif isinstance(val, dict):
                        sub = JSONRepairEngine.extract_clean_prose(val)
                        if sub:
                            parts.append(sub)
            if parts:
                return "\n\n".join(parts)

            # Fallback: scan all string values
            ignore = {"state_update", "image_prompt", "scene_changed", "character_gender", "character_status", "character_age"}
            strings = []
            for k, v in data.items():
                if k not in ignore and isinstance(v, str) and len(v.strip()) > 3 and not v.strip().startswith("{"):
                    strings.append(v.strip())
            if strings:
                return "\n\n".join(strings)

        # Process raw string if it has JSON artifacts
        s = str(data).strip()
        if s.startswith("{") or s.endswith("}") or '"scene_description"' in s or '"character"' in s or '"npc_action"' in s:
            # 1. Regex find quoted descriptive strings
            found = []
            for m in re.finditer(r'"(?:scene_description|npc_action|narration|story|description|dialogue|text)"\s*:\s*"([^"]+)"', s):
                val = m.group(1).replace(r'\"', '"').replace(r'\n', '\n').strip()
                if val and val not in found:
                    found.append(val)
            if found:
                return "\n\n".join(found)

            # 2. Strip JSON code syntax
            cleaned = re.sub(r'[{}\[\]"]', '', s)
            cleaned = re.sub(r'^[a-zA-Z_0-9\s]+:\s*', '', cleaned, flags=re.MULTILINE)
            lines = [l.strip() for l in cleaned.splitlines() if l.strip() and not l.strip().endswith(":") and len(l.strip()) > 2]
            return "\n".join(lines)

        return s

    @staticmethod
    def repair_and_parse(raw_text: str) -> Dict[str, Any]:
        text = raw_text.strip()
        # 1. Strip markdown code fences
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)

        # 2. Extract outer JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end+1]

        # 3. Fix trailing commas before closing braces/brackets
        text = re.sub(r",\s*([\]}])", r"\1", text)

        parsed_dict = None
        try:
            parsed_dict = json.loads(text)
        except json.JSONDecodeError:
            # Replace unescaped newlines inside strings
            text_cleaned = re.sub(r'(?<!\\)\n', r'\\n', text)
            try:
                parsed_dict = json.loads(text_cleaned)
            except Exception:
                pass

        if parsed_dict and isinstance(parsed_dict, dict):
            clean_narration = JSONRepairEngine.extract_clean_prose(parsed_dict)
            return {
                "narration": clean_narration or "주변의 공기가 무겁게 내려앉으며, 당신은 상황을 면밀히 살핍니다.",
                "state_update": parsed_dict.get("state_update", {}) if isinstance(parsed_dict.get("state_update"), dict) else {},
                "scene_changed": bool(parsed_dict.get("scene_changed", False)),
                "image_prompt": parsed_dict.get("image_prompt"),
                "npc_action": parsed_dict.get("npc_action")
            }

        # Fallback if json parsing completely failed
        clean_narration = JSONRepairEngine.extract_clean_prose(raw_text)
        return {
            "narration": clean_narration or "주변의 공기가 무겁게 내려앉으며, 당신은 상황을 면밀히 살핍니다.",
            "state_update": {},
            "scene_changed": False
        }


class ResilientLLMRunner:
    """Executes LLM calls with exponential backoff retry and repair."""

    @staticmethod
    def execute_with_retry(
        call_fn: Callable[[], str],
        max_retries: int = 3,
        backoff_factor: float = 1.5
    ) -> Dict[str, Any]:
        last_err = None
        for attempt in range(1, max_retries + 1):
            try:
                raw_response = call_fn()
                return JSONRepairEngine.repair_and_parse(raw_response)
            except Exception as e:
                last_err = e
                wait_time = backoff_factor ** attempt
                logger.warning(f"LLM call failed (attempt {attempt}/{max_retries}): {e}. Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)

        logger.error(f"All LLM retries exhausted: {last_err}")
        return {
            "narration": f"⚠️ [통신 장애] 외부 신호가 불안정하여 상황을 기록할 수 없습니다. (사유: {last_err})",
            "state_update": {},
            "scene_changed": False
        }
