"""
Audio Trigger and Sound System for Quilltale TRPG.
Deterministically computes contextual BGM and SFX cues based on WorldState,
DiceEngine, Combat outcome, Environment, and Quests.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.world.state import WorldState

logger = logging.getLogger(__name__)

AUDIO_TEMPLATES_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "templates" / "audio_templates.json"


class AudioEngine:
    _templates_cache: Optional[Dict[str, Any]] = None

    @classmethod
    def load_templates(cls, path: Optional[Path] = None) -> Dict[str, Any]:
        target = path or AUDIO_TEMPLATES_PATH
        if cls._templates_cache is not None and path is None:
            return cls._templates_cache

        if not os.path.exists(target):
            logger.warning(f"Audio templates not found at {target}. Using defaults.")
            return {"bgm_tracks": [], "sfx_cues": []}

        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
                cls._templates_cache = data
                return data
        except Exception as e:
            logger.error(f"Failed to load audio templates: {e}")
            return {"bgm_tracks": [], "sfx_cues": []}

    @classmethod
    def determine_turn_audio(
        cls,
        state: WorldState,
        fact_sheet: Any = None,
        action: str = ""
    ) -> Dict[str, Any]:
        """
        Evaluates the current turn context and returns appropriate BGM and triggered SFX cues.
        """
        templates = cls.load_templates()
        bgm_tracks = templates.get("bgm_tracks", [])
        sfx_cues = templates.get("sfx_cues", [])

        # 1. Determine BGM Track
        curr_loc = state.current_location()
        loc_name = curr_loc.name if curr_loc else ""
        loc_desc = curr_loc.description if curr_loc else ""
        loc_text = (loc_name + " " + loc_desc).lower()

        present_npcs = state.npcs_in_location(state.player.location)
        has_hostile = any(n.alive and n.disposition == "hostile" for n in present_npcs)
        has_boss = any(n.alive and (n.tier == "legend" or "보스" in n.name or "거수" in n.name) for n in present_npcs)

        action_lower = action.lower()
        is_combat = (
            has_hostile or
            (fact_sheet and fact_sheet.dice_result and fact_sheet.dice_result.get("action_type") in ["combat", "magic_attack"]) or
            any(k in action_lower for k in ["공격", "베기", "찌르기", "사격", "마법", "전투"])
        )

        selected_bgm_id = "bgm_wilderness_journey"
        if has_boss:
            selected_bgm_id = "bgm_boss_apocalypse"
        elif is_combat:
            selected_bgm_id = "bgm_combat_blades"
        elif any(k in action_lower for k in ["야영", "휴식", "모닥불", "잠을", "쉰다"]):
            selected_bgm_id = "bgm_camp_bonfire"
        elif any(k in loc_text for k in ["선술집", "여관", "마을", "주점", "도시", "상점", "거리"]):
            selected_bgm_id = "bgm_tavern_warmth"
        elif any(k in loc_text for k in ["던전", "동굴", "지하", "감옥", "폐허", "묘지", "수로"]):
            selected_bgm_id = "bgm_dungeon_shadows"
        elif "비" in state.environment.weather or "폭우" in state.environment.weather:
            selected_bgm_id = "bgm_rainy_ruins"

        # Find BGM metadata
        current_bgm = next((b for b in bgm_tracks if b["id"] == selected_bgm_id), None)
        if not current_bgm and bgm_tracks:
            current_bgm = bgm_tracks[0]

        # 2. Determine Triggered SFX Cues
        triggered_sfx = []
        triggered_sfx_ids = set()

        def add_sfx(sfx_id: str):
            if sfx_id not in triggered_sfx_ids:
                sfx_obj = next((s for s in sfx_cues if s["id"] == sfx_id), None)
                if sfx_obj:
                    triggered_sfx.append(sfx_obj)
                    triggered_sfx_ids.add(sfx_id)

        # Dice Check Trigger
        if fact_sheet and fact_sheet.dice_result:
            add_sfx("sfx_dice_roll")
            if fact_sheet.dice_result.get("is_critical_success"):
                add_sfx("sfx_critical_hit")

        # Combat Outcome & Kill Trigger
        if fact_sheet and fact_sheet.combat_outcome:
            co = fact_sheet.combat_outcome
            if co.get("killed"):
                add_sfx("sfx_death_groan")
            if co.get("damage_dealt", 0) > 0:
                if any(k in action_lower for k in ["둔기", "방패", "망치", "강타"]):
                    add_sfx("sfx_blunt_smash")
                else:
                    add_sfx("sfx_sword_slash")

        # Magic Elemental Triggers
        if any(k in action_lower for k in ["화염", "불꽃", "이그니스", "폭발", "용암"]):
            add_sfx("sfx_fireball_cast")
        if any(k in action_lower for k in ["빙결", "냉기", "얼음", "동상", "글라키에"]):
            add_sfx("sfx_ice_freeze")
        if any(k in action_lower for k in ["번개", "뇌격", "감전", "풀구르"]):
            add_sfx("sfx_lightning_bolt")
        if any(k in action_lower for k in ["치유", "회복", "정화", "완치", "포션"]):
            add_sfx("sfx_heal_chime")

        # Items, Gold & Quests
        if any(k in action_lower for k in ["골드", "금화", "구매", "판매", "돈", "흥정"]):
            add_sfx("sfx_gold_coins")
        if any(k in action_lower for k in ["줍기", "획득", "가방에", "보관", "채취"]):
            add_sfx("sfx_item_pickup")
        if fact_sheet and fact_sheet.quest_progress_logs:
            add_sfx("sfx_quest_update")
        if fact_sheet and not fact_sheet.is_valid:
            add_sfx("sfx_danger_alert")

        return {
            "current_bgm": current_bgm,
            "triggered_sfx": triggered_sfx,
            "has_hostile": has_hostile,
            "has_boss": has_boss,
        }

    @classmethod
    def format_audio_html(cls, audio_result: Dict[str, Any]) -> str:
        """
        Renders a responsive, sleek sound controller widget for Gradio UI.
        """
        bgm = audio_result.get("current_bgm") or {}
        sfx_list = audio_result.get("triggered_sfx", [])

        bgm_name = bgm.get("name_ko", "배경음악 없음")
        bgm_desc = bgm.get("description_ko", "")
        bgm_path = bgm.get("asset_path", "")
        volume = bgm.get("default_volume", 0.5)

        sfx_badges_html = ""
        if sfx_list:
            badges = [
                f'<span style="display: inline-block; background: rgba(59, 130, 246, 0.2); border: 1px solid #3b82f6; color: #93c5fd; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-right: 4px; margin-bottom: 4px;">🔊 {s.get("name_ko", "")}</span>'
                for s in sfx_list
            ]
            sfx_badges_html = "".join(badges)
        else:
            sfx_badges_html = '<span style="color: #64748b; font-size: 11px;">(이번 턴 발생 효과음 없음)</span>'

        html = f"""
        <div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 10px 14px; margin-top: 6px; font-family: sans-serif; color: #f8fafc;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 16px;">🎵</span>
              <div>
                <strong style="color: #38bdf8; font-size: 13px;">{bgm_name}</strong>
                <span style="font-size: 11px; color: #94a3b8; margin-left: 6px;">{bgm_desc}</span>
              </div>
            </div>
            <div style="font-size: 11px; color: #64748b;">
              기본 볼륨: {int(volume * 100)}%
            </div>
          </div>
          <div style="border-top: 1px solid #1e293b; padding-top: 6px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
            <span style="font-size: 11px; color: #cbd5e1; font-weight: bold;">트리거된 SFX:</span>
            {sfx_badges_html}
          </div>
        </div>
        """
        return html
