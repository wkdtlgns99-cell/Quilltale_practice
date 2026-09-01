"""
Weather & Survival Physics Engine for Quilltale TRPG.
Calculates deterministic environmental elemental modifiers, visibility penalties,
hypothermia/heatstroke survival ticks, and ambush chances.
"""
import logging
from typing import Dict, Any, List, Tuple
from src.world.state import WorldState, Player

logger = logging.getLogger(__name__)


class WeatherEngine:
    """
    Evaluates realistic weather physics and physiological survival mechanics.
    """

    @classmethod
    def get_elemental_multiplier(cls, element: str, weather: str) -> Tuple[float, str]:
        """
        Returns (damage_multiplier, reason_ko) based on current weather.
        """
        elem = element.lower()
        w = weather.lower()

        if "폭우" in w or "비" in w:
            if elem in ["fire", "화염", "불꽃", "이그니스"]:
                return 0.5, "폭우로 인해 화염 마법 위력이 50% 반감됩니다."
            elif elem in ["lightning", "번개", "뇌격", "풀구르"]:
                return 2.0, "빗물로 인한 지면 전도로 뇌격 피해가 2배로 증폭되며 주변 감전(Shock)을 유발합니다."
        elif "폭설" in w or "눈" in w or "한파" in w:
            if elem in ["ice", "frost", "빙결", "냉기", "글라키에"]:
                return 1.3, "혹한의 기온으로 빙결 마법 위력이 30% 증폭됩니다."
            elif elem in ["fire", "화염", "불꽃"]:
                return 0.8, "혹한으로 인해 화염의 지속 시간이 감소합니다."
        elif "가뭄" in w or "폭염" in w or "열풍" in w:
            if elem in ["fire", "화염", "불꽃"]:
                return 1.3, "건조한 고열로 인해 화염 마법이 폭발적으로 번집니다."
            elif elem in ["ice", "빙결"]:
                return 0.6, "폭염으로 인해 얼음이 즉시 기화합니다."

        return 1.0, ""

    @classmethod
    def process_turn_survival_ticks(cls, state: WorldState) -> List[str]:
        """
        Processes physiological body temperature and weather hazards per turn.
        """
        logs = []
        weather = state.environment.weather
        temp = state.environment.temperature_celsius
        player = state.player

        # Hypothermia (Cold/Blizzard)
        if "폭설" in weather or "한파" in weather or temp <= 0:
            has_warm_clothing = bool(player.equipment.cape or player.equipment.chest)
            if not has_warm_clothing:
                player.body_temperature = max(30.0, player.body_temperature - 0.5)
                if player.body_temperature <= 34.0:
                    damage = 6
                    player.health = max(1, player.health - damage)
                    logs.append(f"🥶 [한파 저체온증] 살을 에는 추위로 체온이 {player.body_temperature:.1f}℃로 떨어져 지속 피해 {damage}를 입었습니다.")
            else:
                player.body_temperature = min(36.5, player.body_temperature + 0.2)

        # Heatstroke (Desert / Heatwave)
        elif "폭염" in weather or "열풍" in weather or temp >= 38:
            player.body_temperature = min(41.0, player.body_temperature + 0.4)
            if player.body_temperature >= 39.0:
                damage = 5
                player.fatigue = min(100, player.fatigue + 10)
                player.health = max(1, player.health - damage)
                logs.append(f"☀️ [폭염 열사병] 살인적인 더위로 체온이 {player.body_temperature:.1f}℃로 치솟아 피로도가 급증하고 피해 {damage}를 입었습니다.")

        # Heavy Fog (Visibility / Ambush)
        if "농무" in weather or "짙은 안개" in weather:
            logs.append("🌫️ [농무 시야 제한] 짙은 안개로 인해 5m 앞이 보이지 않아 원거리 명중 난이도(DC)가 +4 증가합니다.")

        return logs

    @classmethod
    def format_weather_context_for_prompt(cls, state: WorldState) -> str:
        """
        Formats concise prompt anchoring for current weather physics.
        """
        w = state.environment.weather
        temp = state.environment.temperature_celsius
        notes = []

        if "폭우" in w or "비" in w:
            notes.append("지면이 젖어 화염 위력 50% 감소 / 번개 위력 2배 및 감전 유발")
        if "폭설" in w or "한파" in w or temp <= 0:
            notes.append("혹한으로 빙결 위력 증가 / 방한구 미착용 시 저체온증 위험")
        if "농무" in w:
            notes.append("원거리 시야 차단 및 기습 위험 상승")

        notes_str = f" (물리 효과: {', '.join(notes)})" if notes else ""
        return f"[🌦️ 날씨 생존 물리 규칙] 날씨: {w} | 기온: {temp}℃{notes_str}"
