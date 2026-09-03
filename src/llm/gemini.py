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

        candidate_models = ["gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.1-pro-preview", self._model_name]
        candidate_models = list(dict.fromkeys([m for m in candidate_models if m]))

        last_error = None
        total_keys = len(self._clients)
        
        # Phase 1: Seamless Key Rotation (Instantly jump to next API key on 429/quota error)
        for attempt in range(total_keys):
            client = self.current_client
            for m in candidate_models:
                for retry in range(2):
                    try:
                        response = client.models.generate_content(
                            model=m,
                            contents=final_prompt,
                        )
                        return LLMResponse(text=response.text or "", model=m)
                    except Exception as e:
                        last_error = e
                        err_str = str(e).upper()
                        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "QUOTA" in err_str:
                            logger.warning(f"Key #{self._client_idx + 1} quota limit hit. Instantly rotating to next key...")
                            break  # Break inner model loop, switch to next API key immediately!
                        elif "503" in err_str or "UNAVAILABLE" in err_str:
                            logger.warning(f"Gemini {m} temporary 503 unavailable, retrying in 1s...")
                            time.sleep(1.0)
                        else:
                            logger.warning(f"Gemini {m} error: {e}")
                            time.sleep(0.3)
                            break
            
            # Rotate to next key immediately
            if total_keys > 1:
                old_idx = self._client_idx
                self.rotate_client()
                print(f"🔑 [Google API 키 자동 교체]: {old_idx + 1}번 키 소진 ➔ {self._client_idx + 1}번 키로 즉시 우회 (대기시간 0초)")

        # Phase 2: If ALL registered keys exhausted free per-minute quota, cooldown and retry
        err_str = str(last_error or "").upper()
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "QUOTA" in err_str:
            for cooldown_attempt in range(3):
                wait_time = 15 + (cooldown_attempt * 5)
                print(f"\n⏳ [모든 등록된 API 키 쿼터 일시 소진: {wait_time}초 대기 후 자동 재개...]")
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