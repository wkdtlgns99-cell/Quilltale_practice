"""
Celestial & Festival Event Engine for Quilltale TRPG.
Deterministically advances global astronomical cycles (Blood Moon, Solar Eclipse)
and continental festivals (Harvest Festival, Night of the Dead).
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.world.state import WorldState

logger = logging.getLogger(__name__)

CELESTIAL_TEMPLATES_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "templates" / "celestial_templates.json"


class CelestialEngine:
    _templates_cache: Optional[Dict[str, Any]] = None

    @classmethod
    def load_templates(cls, path: Optional[Path] = None) -> Dict[str, Any]:
        target = path or CELESTIAL_TEMPLATES_PATH
        if cls._templates_cache is not None and path is None:
            return cls._templates_cache

        if not os.path.exists(target):
            logger.warning(f"Celestial templates not found at {target}.")
            return {"celestial_events": [], "festivals": []}

        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
                cls._templates_cache = data
                return data
        except Exception as e:
            logger.error(f"Failed to load celestial templates: {e}")
            return {"celestial_events": [], "festivals": []}

    @classmethod
    def advance_celestial_turn(cls, state: WorldState) -> List[str]:
        """
        Advances astronomical cycles and festival durations per turn.
        """
        templates = cls.load_templates()
        events = templates.get("celestial_events", [])
        festivals = templates.get("festivals", [])
        logs = []

        # 1. Advance active celestial event countdown
        if state.celestial_phase != "normal" and state.celestial_phase_turns > 0:
            state.celestial_phase_turns -= 1
            if state.celestial_phase_turns <= 0:
                logs.append(f"🌕 [천문 현상 종료] {state.celestial_phase} 현상이 잦아들고 하늘이 본래의 모습을 되찾았습니다.")
                state.celestial_phase = "normal"

        # 2. Advance active festival countdown
        if state.active_festival and state.active_festival_turns > 0:
            state.active_festival_turns -= 1
            if state.active_festival_turns <= 0:
                logs.append(f"🎪 [축제 종료] {state.active_festival} 축제 기간이 끝나고 도시가 일상으로 돌아갑니다.")
                state.active_festival = None

        # 3. Check for new cyclical celestial events
        if state.celestial_phase == "normal" and state.turn > 0:
            for ev in events:
                interval = ev.get("cycle_interval_turns", 25)
                if state.turn % interval == 0:
                    state.celestial_phase = ev["id"]
                    state.celestial_phase_turns = ev.get("duration_turns", 3)
                    announcement = ev.get("announcement_ko", f"천문 이변 [{ev['name_ko']}] 발생!")
                    logs.append(announcement)
                    state.pending_breaking_news.append(announcement)
                    break

        # 4. Check for new cyclical festivals
        if not state.active_festival and state.turn > 0:
            for f in festivals:
                interval = f.get("cycle_interval_turns", 30)
                if state.turn % interval == 0:
                    state.active_festival = f["id"]
                    state.active_festival_turns = f.get("duration_turns", 5)
                    announcement = f.get("announcement_ko", f"대륙 축제 [{f['name_ko']}] 개막!")
                    logs.append(announcement)
                    state.pending_breaking_news.append(announcement)
                    break

        return logs

    @classmethod
    def get_active_modifiers(cls, state: WorldState) -> Dict[str, Any]:
        """Returns consolidated modifiers for combat, magic, and economy."""
        templates = cls.load_templates()
        mods = {
            "monster_attack_mult": 1.0,
            "magic_damage_mult": 1.0,
            "dark_magic_mult": 1.0,
            "holy_magic_mult": 1.0,
            "shop_discount": 0.0,
            "mana_regen_bonus": 0
        }

        # Celestial event effects
        if state.celestial_phase != "normal":
            for ev in templates.get("celestial_events", []):
                if ev["id"] == state.celestial_phase:
                    eff = ev.get("effects", {})
                    for k, v in eff.items():
                        if k in mods:
                            mods[k] = v

        # Festival effects
        if state.active_festival:
            for f in templates.get("festivals", []):
                if f["id"] == state.active_festival:
                    eff = f.get("effects", {})
                    if "shop_price_discount" in eff:
                        mods["shop_discount"] = max(mods["shop_discount"], eff["shop_price_discount"])

        return mods

    @classmethod
    def format_celestial_context_for_prompt(cls, state: WorldState) -> str:
        """Formats active astronomical and festival status for prompt context."""
        templates = cls.load_templates()
        lines = []

        if state.celestial_phase != "normal":
            for ev in templates.get("celestial_events", []):
                if ev["id"] == state.celestial_phase:
                    lines.append(f"🌌 [천문 이변 활성화: {ev['name_ko']}] (남은 기간: {state.celestial_phase_turns}턴) - {ev['description_ko']}")

        if state.active_festival:
            for f in templates.get("festivals", []):
                if f["id"] == state.active_festival:
                    lines.append(f"🎉 [대륙 축제 진행 중: {f['name_ko']}] (남은 기간: {state.active_festival_turns}턴) - {f['description_ko']}")

        return "\n".join(lines)
