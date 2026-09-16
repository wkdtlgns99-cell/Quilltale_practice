import os
import time
import logging
from typing import Optional, List
from .base import BaseLLM, LLMResponse

logger = logging.getLogger(__name__)

DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-6"
CANDIDATE_CLAUDE_MODELS = [
    "claude-sonnet-4-6",
    "claude-3-7-sonnet-20250219",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
]


class ClaudeLLM(BaseLLM):
    """Anthropic Claude LLM client with candidate model fallback chain."""

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        *args,
        **kwargs,
    ):
        self._model = os.environ.get(
            "ANTHROPIC_MODEL", model or DEFAULT_CLAUDE_MODEL
        )
        candidates = [self._model] + [
            m for m in CANDIDATE_CLAUDE_MODELS if m != self._model
        ]
        self._candidate_models: List[str] = list(dict.fromkeys(candidates))

        resolved_api_key = (
            api_key
            or kwargs.get("api_key")
            or os.environ.get("ANTHROPIC_API_KEY", "")
        )
        self._client = None
        if resolved_api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=resolved_api_key)
            except Exception as e:
                logger.warning("Claude 클라이언트 초기화 실패: %s", e)
        else:
            logger.warning("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")

    @property
    def candidate_models(self) -> List[str]:
        return list(self._candidate_models)

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        if not self._client:
            logger.error("Claude client가 설정되지 않았습니다 (API 키 부재).")
            return LLMResponse(
                text="[오류: Claude API 키가 설정되지 않아 응답을 생성할 수 없습니다.]",
                model=self._model,
            )

        last_err = None

        for m in self._candidate_models:
            kwargs = {
                "model": m,
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system

            # Attempt up to 2 retries per model
            for attempt in range(2):
                try:
                    msg = self._client.messages.create(**kwargs)
                    if msg and msg.content:
                        return LLMResponse(text=msg.content[0].text, model=m)
                    return LLMResponse(text="", model=m)
                except Exception as e:
                    last_err = e
                    err_str = str(e).lower()
                    logger.warning(
                        "Claude [%s] 호출 실패 (시도 %d/2): %s",
                        m,
                        attempt + 1,
                        e,
                    )
                    # If model is retired, not found, or overloaded, break immediately to next model
                    if any(kw in err_str for kw in ["not_found", "not found", "retired", "model_not_found", "overloaded", "429"]):
                        break
                    time.sleep(0.5)

            logger.info("Claude [%s] 소진/실패, 다음 후보 모델로 폴백...", m)

        logger.error("Claude 모든 후보 모델 최종 실패: %s", last_err)
        return LLMResponse(
            text=f"[오류: Claude 모든 모델 호출 실패 - {last_err}]",
            model=self._model,
        )