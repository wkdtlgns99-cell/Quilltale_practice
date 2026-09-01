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
    def __init__(self, model: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if key:
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
        for attempt in range(3):
            try:
                response = self._client.models.generate_content(
                    model=self._model_name,
                    contents=final_prompt,
                )
                return LLMResponse(text=response.text or "", model=self._model_name)
            except Exception as e:
                logger.error(f"Gemini API attempt {attempt+1} failed: {e}")
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)