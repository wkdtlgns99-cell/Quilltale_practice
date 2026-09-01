"""
Local Ollama LLM Provider for Quilltale TRPG.
Allows 100% free, zero-token, private local AI inference via Ollama (e.g. Llama 3.1 8B).
"""
import os
import json
import logging
import requests
from typing import Optional

from .base import BaseLLM, LLMResponse

logger = logging.getLogger(__name__)


class OllamaLLM(BaseLLM):
    def __init__(self, model: str = "qwen2.5:7b", base_url: str = "http://localhost:11434"):
        self._model_name = model
        self._base_url = base_url.rstrip("/")

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        url = f"{self._base_url}/api/generate"
        payload = {
            "model": self._model_name,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 384
            }
        }

        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            text = data.get("response", "").strip()
            return LLMResponse(text=text, model=self._model_name)
        except Exception as e:
            logger.error(f"Ollama local inference failed: {e}")
            raise RuntimeError(f"Ollama local inference failed: {e}")
