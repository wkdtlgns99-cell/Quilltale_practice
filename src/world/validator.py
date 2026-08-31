"""
Strict Action & Reality Validation Engine for Quilltale.
Prevents Yes-Man AI compliance, enforces physical logic, and triggers deterministic dice rolls.
"""
import re
from typing import Tuple, Optional, Dict, Any
from .state import WorldState
from .dice import DiceEngine, DiceCheckResult


IMPOSSIBLE_POWER_PATTERNS = [
    r"지구.*파괴", r"행성.*폭", r"전부.*즉사", r"모두.*죽", r"시간.*정지",
    r"신이\s*된다", r"신으로\s*각성", r"손가락.*튕겨", r"우주.*창조", r"무적",
    r"destroy.*world", r"instant.*kill", r"become.*god"
]

RELEASE_KEYWORDS = ["풀어주", "방생", "은퇴", "여정을 마치", "release", "retire"]


class ActionValidator:
    """
    Validates player actions before GM LLM prompt generation.
    Enforces deterministic inventory checks, dead NPC interaction limits,
    and resolves dice challenges.
    """

    WEAK_POINT_KEYWORDS = {
        '머리': ['머리를', '두개골', '이마를'],
        '목': ['목을', '목덜미'],
        '눈': ['눈을', '시야를'],
        '급소': ['급소를', '급소에'],
        '심장': ['심장을', '심장에'],
        '등': ['등을', '등에'],
        '관절': ['관절을', '무릎을', '팔꿈치'],
    }

    @staticmethod
    def detect_target_part(action: str) -> str:
        """Detect if action targets a specific body part."""
        for part, keywords in ActionValidator.WEAK_POINT_KEYWORDS.items():
            if any(k in action for k in keywords):
                return part
        return ''

    @classmethod
    def is_release_action(cls, action: str) -> bool:
        action_lower = action.lower()
        return any(k in action_lower for k in RELEASE_KEYWORDS)

    @staticmethod
    def parse_action_components(raw_input: str) -> dict:
        """
        Parses player input into dialogue ("..."), monologue/thoughts ('...'), and physical action.
        "..." -> Spoken dialogue
        '...' -> Internal monologue, thoughts, telepathy
        plain -> Physical action / intent
        """
        dialogues = re.findall(r'"([^"]*)"', raw_input)
        monologues = re.findall(r"'([^']*)'", raw_input)
        
        # Remove quotes to isolate physical action
        clean_action = re.sub(r'"[^"]*"', '', raw_input)
        clean_action = re.sub(r"'[^']*'", '', clean_action).strip()
        
        return {
            "dialogue": dialogues[0] if dialogues else "",
            "monologue": monologues[0] if monologues else "",
            "action": clean_action or raw_input.strip(),
            "raw": raw_input.strip(),
        }

    @classmethod
    def pre_validate_action(
        cls,
        action: str,
        state: WorldState,
    ) -> Tuple[bool, str, Optional[DiceCheckResult], Dict[str, Any]]:
        """
        Validates action legality and triggers deterministic dice rolls when needed.
        Returns: (is_valid, failure_message_ko, dice_check_result_or_none, extra_flags)
        """
        parsed = cls.parse_action_components(action)
        action_clean = parsed["action"]
        action_lower = action.lower()
        curr_loc = state.current_location()
        extra_flags: Dict[str, Any] = {
            'incantation_cancel_risk': False,
            'interrupt_counter': False,
            'target_part': '',
            'parsed_components': parsed,
            'is_no_incantation': False,
            'spatial_jam_risk': False,
            'suffocation_risk': False,
        }

        # 1. Anti-Yes-Man Reality Check: Reject power-scaling absurdity
        for pattern in IMPOSSIBLE_POWER_PATTERNS:
            if re.search(pattern, action_lower):
                return (
                    False,
                    "인간의 한계를 벗어난 불가능한 행동입니다. 거대한 힘에 짓눌려 행동이 무위로 돌아갑니다.",
                    None,
                    extra_flags
                )

        # 2. Inventory check: Cannot use or drop items not owned
        for item_id, item in state.items.items():
            if item.name.lower() in action_lower or item_id in action_lower:
                if (
                    item_id not in state.player.inventory
                    and (not curr_loc or item_id not in curr_loc.items)
                ):
                    # Check if action verb implies usage/drop
                    if any(
                        verb in action_lower
                        for verb in ["사용", "찌른", "열", "먹", "휘두", "버린", "use", "unlock", "drop"]
                    ):
                        return (
                            False,
                            f"가방이나 주변에 존재하지 않는 [{item.name}]을(를) 사용할 수 없습니다.",
                            None,
                            extra_flags
                        )

        # 3. Dead NPC check
        for npc_id, npc in state.npcs.items():
            if (npc.name.lower() in action_lower or npc_id in action_lower) and not npc.alive:
                if any(v in action_lower for v in ["대화", "말을", "물어", "talk", "ask", "speak"]):
                    return (
                        False,
                        f"이미 싸늘하게 식어버린 [{npc.name}]의 시신은 대답하지 않습니다.",
                        None,
                        extra_flags
                    )

        # 4.1 Spatial Ergonomics Check (Narrow Space & Long Weapons)
        loc_desc = (curr_loc.name + " " + curr_loc.description).lower() if curr_loc else ""
        if any(k in loc_desc for k in ["동굴", "석실", "환풍구", "비좁은", "밀실", "통로"]):
            if any(w in action_lower for w in ["대검", "장창", "창을", "할버드", "양손검", "크게 휘둘"]):
                extra_flags['spatial_jam_risk'] = True

        # 4.2 Suffocation & Inhalation Risk (Water / Toxic Smoke Incantation)
        env_weather = getattr(state.environment, 'weather', '').lower()
        if any(k in loc_desc or k in env_weather for k in ["수중", "물속", "유독가스", "화재", "유황", "농연"]):
            if any(k in action_lower for k in ["영창", "주문", "외운", "소리쳐", "발성", "시전"]):
                extra_flags['suffocation_risk'] = True

        # 4. Physical Object & Weight/Strength / Bag Capacity Check
        if any(v in action_lower for v in ["줍", "집어", "가방에", "넣", "획득", "챙긴", "pick", "take", "들"]):
            for item_id, item in state.items.items():
                if item.name.lower() in action_lower or item_id in action_lower:
                    if curr_loc and item_id in curr_loc.items:
                        # Strength requirement check
                        if state.player.strength < item.required_strength:
                            return (
                                False,
                                f"[{item.name}]은(는) 너무 무겁습니다. (요구 근력: {item.required_strength}, 현재 근력: {state.player.strength})",
                                None,
                                extra_flags
                            )
                        # Bag storage vs Hand-held check
                        if not item.can_store_in_bag and any(v in action_lower for v in ["가방에", "인벤토리에", "넣"]):
                            return (
                                False,
                                f"[{item.name}]은(는) 부피가 너무 커서 가방에 들어가지 않습니다. 대신 손에 들거나 즉석 무기로 사용할 수 있습니다.",
                                None,
                                extra_flags
                            )


        target_part = cls.detect_target_part(action_lower)
        extra_flags['target_part'] = target_part

        # Check incantation cancel risk
        incantation_verbs = ["영창", "주문", "캐스팅", "마법", "incant", "cast", "spell"]
        if any(v in action_lower for v in incantation_verbs) and curr_loc:
            loc_npcs = state.npcs_in_location(curr_loc.id)
            for n in loc_npcs:
                if n.alive and getattr(n, 'attitude', '중립') in ['적대적', '경계']:
                    extra_flags['incantation_cancel_risk'] = True
                    break

        # 4. Trigger Deterministic Dice Rolls for Challenges
        dice_result = None

        # A. Magic Attack Check
        magic_verbs = ["파이어", "화염", "마법", "볼트", "빙결", "뇌전", "주문", "영창하여", "시전"]
        is_magic_action = any(v in action_lower for v in magic_verbs)

        if is_magic_action:
            # Check if incantation dialogue is present
            has_incant_speech = bool(parsed["dialogue"]) or ("영창" in action_lower)
            is_no_incant = not has_incant_speech
            extra_flags['is_no_incantation'] = is_no_incant

            target_ac = 12
            target_npc_id = None
            if curr_loc:
                loc_npcs = state.npcs_in_location(curr_loc.id)
                for n in loc_npcs:
                    if n.name.lower() in action_lower or n.id in action_lower:
                        target_ac = n.armor_class
                        target_npc_id = n.id
                        break

            dice_result = DiceEngine.perform_check(
                action_type="마법 공격",
                stat_value=state.player.intelligence,
                dc=target_ac,
                base_damage=12,
                scaling=1.8,
                target_npc_id=target_npc_id,
                target_part=target_part,
                is_no_incantation=is_no_incant,
            )
            if dice_result.interrupt_counter:
                extra_flags['interrupt_counter'] = True

        # B. Physical Combat attack check
        elif any(v in action_lower for v in ["공격", "찌르", "베", "후려치", "칼로", "단검으", "attack", "strike", "stab", "slash"]):
            target_ac = 12
            target_npc_id = None
            if curr_loc:
                loc_npcs = state.npcs_in_location(curr_loc.id)
                for n in loc_npcs:
                    if n.name.lower() in action_lower or n.id in action_lower:
                        target_ac = n.armor_class
                        target_npc_id = n.id
                        break

            eq_wep = state.get_equipped_weapon_item()
            base_dmg = eq_wep.damage if eq_wep else 3
            scaling = eq_wep.scaling_factor if eq_wep else 1.0

            dice_result = DiceEngine.perform_check(
                action_type="전투 공격",
                stat_value=state.player.str_stat,
                dc=target_ac,
                base_damage=base_dmg,
                scaling=scaling,
                target_npc_id=target_npc_id,
                target_part=target_part
            )

            
            if dice_result.interrupt_counter:
                extra_flags['interrupt_counter'] = True

        # C. Stealth / Steal check
        elif any(v in action_lower for v in ["훔치", "소매치기", "몰래", "steal", "pickpocket", "sneak"]):
            dice_result = DiceEngine.perform_check(
                action_type="은신 / 절도",
                stat_value=state.player.dex_stat,
                dc=13,
            )

        # D. Intimidation / Persuasion check
        elif any(v in action_lower for v in ["협박", "설득", "속이", "위협", "intimidate", "persuade", "threaten"]):
            dice_result = DiceEngine.perform_check(
                action_type="화술 / 위협",
                stat_value=state.player.cha_stat,
                dc=13,
            )

        # E. Lockpicking / Chest unlocking check
        elif any(v in action_lower for v in ["자물쇠", "따기", "궤짝을 부수", "pick lock", "force open"]):
            dice_result = DiceEngine.perform_check(
                action_type="자물쇠 해제 / 기계 조작",
                stat_value=state.player.dex_stat,
                dc=13,
            )

        return True, "", dice_result, extra_flags

