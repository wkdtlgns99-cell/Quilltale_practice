import os
import logging
import time
from typing import Optional
from google import genai
from dotenv import load_dotenv
from .base import BaseLLM, LLMResponse

load_dotenv()
logger = logging.getLogger(__name__)


class GeminiLLM(BaseLLM):
    def __init__(self, model: str = "gemini-3.5-flash-lite", api_key: Optional[str] = None, *args, **kwargs):
        key = api_key or kwargs.get("api_key") or os.environ.get("GEMINI_API_KEY", "")
        if key:
            os.environ["GEMINI_API_KEY"] = key
            self._client = genai.Client(api_key=key)
        else:
            try:
                self._client = genai.Client()
            except Exception:
                self._client = None
        self._model_name = model

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        if not self._client:
            raise RuntimeError("GEMINI_API_KEY is not set or client initialization failed.")
        final_prompt = f"{system}\n\n{prompt}" if system else prompt
        
        # Try primary model then fallbacks
        candidate_models = [self._model_name, "gemini-3.6-flash", "gemini-3.7-flash", "gemini-flash-latest"]
        last_error = None
        
        for m in dict.fromkeys(candidate_models):
            for attempt in range(2):
                try:
                    response = self._client.models.generate_content(
                        model=m,
                        contents=final_prompt,
                    )
                    return LLMResponse(text=response.text or "", model=m)
                except Exception as e:
                    last_error = e
                    logger.warning(f"Gemini model {m} attempt {attempt+1} failed: {e}")
                    time.sleep(1)
        raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")