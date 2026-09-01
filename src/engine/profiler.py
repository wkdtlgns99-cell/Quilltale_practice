"""
Telemetry, Latency Profiler & Token Cost Calculator for Quilltale TRPG.
"""
from dataclasses import dataclass, field


@dataclass
class TurnTelemetry:
    turn: int
    pass1_duration_ms: float = 0.0
    llm_duration_ms: float = 0.0
    pass2_duration_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost_krw: float = 0.0


class EngineProfiler:
    GEMINI_FLASH_INPUT_COST_PER_M = 0.075   # $0.075 per 1M tokens
    GEMINI_FLASH_OUTPUT_COST_PER_M = 0.30   # $0.30 per 1M tokens
    USD_TO_KRW = 1400.0

    @classmethod
    def calculate_cost(cls, prompt_tokens: int, completion_tokens: int) -> float:
        usd = (prompt_tokens * cls.GEMINI_FLASH_INPUT_COST_PER_M / 1_000_000) + \
              (completion_tokens * cls.GEMINI_FLASH_OUTPUT_COST_PER_M / 1_000_000)
        return usd * cls.USD_TO_KRW

    @classmethod
    def format_telemetry_hud(cls, telemetry: TurnTelemetry) -> str:
        total_time = telemetry.pass1_duration_ms + telemetry.llm_duration_ms + telemetry.pass2_duration_ms
        return (
            f"⚡ [지연 시간] 총 {total_time:.1f}ms (Pass1: {telemetry.pass1_duration_ms:.1f}ms | "
            f"LLM: {telemetry.llm_duration_ms:.1f}ms | Pass2: {telemetry.pass2_duration_ms:.1f}ms) | "
            f"🪙 [토큰/비용] {telemetry.prompt_tokens + telemetry.completion_tokens} 토큰 (약 {telemetry.estimated_cost_krw:.3f}원)"
        )
