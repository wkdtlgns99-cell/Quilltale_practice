"""
Puzzle & Mechanism Engine for Quilltale TRPG.
Deterministically resolves ancient incantation ciphers, weight pressure plates,
beam reflectors, and valve sequences in dungeons and ruins.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from src.world.state import WorldState, Item

logger = logging.getLogger(__name__)

PUZZLE_TEMPLATES_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "templates" / "puzzle_templates.json"


class PuzzleEngine:
    _templates_cache: Optional[Dict[str, Any]] = None

    @classmethod
    def load_templates(cls, path: Optional[Path] = None) -> Dict[str, Any]:
        target = path or PUZZLE_TEMPLATES_PATH
        if cls._templates_cache is not None and path is None:
            return cls._templates_cache

        if not os.path.exists(target):
            logger.warning(f"Puzzle templates not found at {target}.")
            return {"puzzles": []}

        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
                cls._templates_cache = data
                return data
        except Exception as e:
            logger.error(f"Failed to load puzzle templates: {e}")
            return {"puzzles": []}

    @classmethod
    def get_puzzle_for_location(cls, location_id: str, state: Optional[WorldState] = None) -> Optional[Dict[str, Any]]:
        """Finds active, unsolved puzzle for the given location."""
        templates = cls.load_templates()
        for p in templates.get("puzzles", []):
            if p["location_id"] == location_id:
                # Check if already solved in state
                if state and state.puzzles.get(p["id"], {}).get("solved"):
                    continue
                return p
        return None

    @classmethod
    def evaluate_puzzle_action(cls, state: WorldState, action: str) -> Optional[Dict[str, Any]]:
        """
        Evaluates player's action against the puzzle in the current location.
        """
        puzzle = cls.get_puzzle_for_location(state.player.location, state)
        if not puzzle:
            return None

        p_type = puzzle.get("puzzle_type")
        p_id = puzzle["id"]
        action_lower = action.lower()
        is_solved = False
        solve_msg = ""

        if p_type == "incantation_cipher":
            req_words = puzzle.get("required_words", [])
            # Check if all required words are in the incantation action
            if all(w.lower() in action_lower for w in req_words):
                is_solved = True
                solve_msg = f"✨ [고유 기믹 해제] 고대어 비문 [{puzzle['name_ko']}]의 암호가 공명하며 육중한 석문이 열립니다!"

        elif p_type == "weight_pressure_plate":
            req_weight = puzzle.get("required_weight_kg", 50.0)
            req_str = puzzle.get("required_strength", 14)
            # Check strength or heavy item placement
            if state.player.strength >= req_str and any(k in action_lower for k in ["밀어", "밟아", "누른다", "힘으로", "올린다"]):
                is_solved = True
                solve_msg = f"⚙️ [장치 작동] 강력한 완력으로 [{puzzle['name_ko']}]을 짓눌러 비밀 통로를 개방했습니다!"
            elif any(k in action_lower for k in ["바위", "무거운", "가방", "짐을", "올려놓는다"]):
                is_solved = True
                solve_msg = f"⚙️ [장치 작동] 충분한 무게를 얹어 [{puzzle['name_ko']}]의 잠금을 해제했습니다!"

        elif p_type == "beam_reflector":
            req_angles = puzzle.get("required_angles", [45, 90, 135])
            if all(str(a) in action_lower for a in req_angles) or any(k in action_lower for k in ["거울을 맞춘다", "각도를 정렬", "광선을 유도"]):
                is_solved = True
                solve_msg = f"💎 [광선 굴절 성공] 회전 거울의 각도가 일치하며 마력 광선이 제단 중앙에 집중되어 봉인이 풀립니다!"

        elif p_type == "valve_sequence":
            req_seq = puzzle.get("required_sequence", [])
            if all(v.lower() in action_lower for v in req_seq) or any(k in action_lower for k in ["밸브 순서대로", "3, 1, 2", "순서대로 잠근다"]):
                is_solved = True
                solve_msg = f"🔧 [밸브 차단 완료] 올바른 순서로 압력을 제어하여 치명적인 독가스 살포가 멈췄습니다!"

        if is_solved:
            # Update state puzzles DB
            state.puzzles[p_id] = {"solved": True, "turn_solved": state.turn}
            reward_items = puzzle.get("reward_items", [])
            reward_exp = puzzle.get("reward_exp", 100)
            state.player.exp += reward_exp

            # Add reward items to player or location
            for r_item_id in reward_items:
                if r_item_id not in state.items:
                    state.items[r_item_id] = Item(
                        id=r_item_id,
                        name=f"고대 유물 [{puzzle['name_ko']}의 보상]",
                        description="퍼즐을 풀고 획득한 신비로운 보상 아이템",
                        location="inventory",
                        item_type="key" if "key" in r_item_id else "misc",
                        value=200
                    )
                if r_item_id not in state.player.inventory:
                    state.player.inventory.append(r_item_id)

            return {
                "puzzle_id": p_id,
                "puzzle_name": puzzle["name_ko"],
                "is_solved": True,
                "solve_message": solve_msg,
                "reward_exp": reward_exp,
                "reward_items": reward_items
            }

        return None

    @classmethod
    def format_puzzle_context_for_prompt(cls, state: WorldState) -> str:
        """Formats active puzzle hints for GM narration."""
        puzzle = cls.get_puzzle_for_location(state.player.location, state)
        if not puzzle:
            return ""
        return (
            f"[🧩 고대 유적 퍼즐 기믹: {puzzle['name_ko']}]\n"
            f"- 상황: {puzzle['description_ko']}\n"
            f"- 힌트: {puzzle['hint_ko']}"
        )
