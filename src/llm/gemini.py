import os
import logging
import time
from typing import Optional, List
from google import genai
from dotenv import load_dotenv
from .base import BaseLLM, LLMResponse

load_dotenv()
logger = logging.getLogger(__name__)


class GeminiLLM(BaseLLM):
    def __init__(self, model: str = "gemini-3.7-flash", api_key: Optional[str] = None, *args, **kwargs):
        keys: List[str] = []
        if api_key:
            keys.append(api_key)
        if kwargs.get("api_key"):
            keys.append(kwargs["api_key"])
            
        env_keys = [
            os.environ.get("GEMINI_API_KEY", ""),
            os.environ.get("GEMINI_API_KEY_1", ""),
            os.environ.get("GEMINI_API_KEY_2", ""),
            os.environ.get("GEMINI_API_KEY_3", ""),
            os.environ.get("WARRIOR_API_KEY", ""),
            os.environ.get("MAGE_API_KEY", ""),
            os.environ.get("ROGUE_API_KEY", "")
        ]
        for k in env_keys:
            if k and k not in keys:
                keys.append(k)

        self._clients: List[genai.Client] = []
        for k in keys:
            try:
                self._clients.append(genai.Client(api_key=k))
            except Exception:
                pass

        if not self._clients:
            try:
                self._clients.append(genai.Client())
            except Exception:
                pass

        self._client_idx = 0
        self._model_name = model

    @property
    def current_client(self) -> Optional[genai.Client]:
        if not self._clients:
            return None
        return self._clients[self._client_idx % len(self._clients)]

    def rotate_client(self) -> None:
        if self._clients:
            self._client_idx = (self._client_idx + 1) % len(self._clients)

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        if not self._clients:
            raise RuntimeError("GEMINI_API_KEY is not set or client initialization failed.")
        final_prompt = f"{system}\n\n{prompt}" if system else prompt

        candidate_models = [self._model_name, "gemini-3.6-flash", "gemini-3.7-flash", "gemini-flash-latest"]
        candidate_models = list(dict.fromkeys(candidate_models))

        last_error = None
        # Phase 1: Try all available clients and candidate models immediately
        for _ in range(len(self._clients) or 1):
            client = self.current_client
            for m in candidate_models:
                try:
                    response = client.models.generate_content(
                        model=m,
                        contents=final_prompt,
                    )
                    return LLMResponse(text=response.text or "", model=m)
                except Exception as e:
                    last_error = e
                    err_str = str(e)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        logger.warning(f"Model {m} quota exhausted (429). Rotating to next model/key...")
                        continue
                    else:
                        logger.warning(f"Gemini {m} error: {e}")
                        time.sleep(0.5)
            self.rotate_client()

        # Phase 2: If all returned 429 (exceeded 15 requests/min), cooldown for 15s and retry
        err_str = str(last_error or "")
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            for cooldown_attempt in range(3):
                wait_time = 15 + (cooldown_attempt * 5)
                print(f"\n⏳ [Google 무료 분당 15회 쿼터 보호: {wait_time}초 대기 후 자동 재개...]")
                time.sleep(wait_time)
                for client in self._clients:
                    for m in candidate_models:
                        try:
                            response = client.models.generate_content(
                                model=m,
                                contents=final_prompt,
                            )
                            return LLMResponse(text=response.text or "", model=m)
                        except Exception as e:
                            last_error = e
                            continue

        raise RuntimeError(f"All Gemini models and API keys exhausted. Last error: {last_error}")