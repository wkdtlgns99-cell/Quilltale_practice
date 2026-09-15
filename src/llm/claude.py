import os
import time
import logging
from typing import Optional
from .base import BaseLLM, LLMResponse

logger = logging.getLogger(__name__)


class ClaudeLLM(BaseLLM):
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        *args,
        **kwargs,
    ):
        self._model = os.environ.get(
            "ANTHROPIC_MODEL", model or "claude-3-5-sonnet-latest"
        )
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

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        if not self._client:
            logger.error("Claude client가 설정되지 않았습니다 (API 키 부재).")
            return LLMResponse(
                text="[오류: Claude API 키가 설정되지 않아 응답을 생성할 수 없습니다.]",
                model=self._model,
            )

        kwargs = {
            "model": self._model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        max_retries = 3
        backoff = 1.0
        last_err = None
        for attempt in range(max_retries):
            try:
                msg = self._client.messages.create(**kwargs)
                if msg and msg.content:
                    return LLMResponse(text=msg.content[0].text, model=self._model)
                return LLMResponse(text="", model=self._model)
            except Exception as e:
                last_err = e
                logger.warning(
                    "Claude API 호출 재시도 %d/%d 실패: %s",
                    attempt + 1,
                    max_retries,
                    e,
                )
                if attempt < max_retries - 1:
                    time.sleep(backoff)
                    backoff *= 2.0

        logger.error("Claude API 최종 실패: %s", last_err)
        return LLMResponse(
            text=f"[오류: Claude API 호출 실패 - {last_err}]",
            model=self._model,
        )