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

        # 1.5 Status Effect Action Block Check (Stun, Freeze, Paralysis)
        from src.world.status_engine import StatusEffectEngine
        can_act, block_reason = StatusEffectEngine.can_act(state.player)
        if not can_act and action_clean:
            return (
                False,
                f"⚠️ {block_reason}",
                None,
                extra_flags
            )

        # 1.6 Physical Injury Action Block Check (Fractures, Arm/Leg Disabilities)
        if state.player.injuries and action_clean:
            injuries_text = " ".join(state.player.injuries)
            if any(k in injuries_text for k in ["팔", "손목", "어깨"]) and any(k in action_lower for k in ["양손검", "대검", "활을", "장궁", "암벽", "매달려"]):
                return (
                    False,
                    f"신체 부상({injuries_text})으로 인해 양손을 사용하는 무리한 행동을 할 수 없습니다.",
                    None,
                    extra_flags
                )
            if any(k in injuries_text for k in ["다리", "발목", "무릎"]) and any(k in action_lower for k in ["전력 질주", "도약", "높이 뛰어", "달려"]):
                return (
                    False,
                    f"신체 부상({injuries_text})으로 인해 무리하게 질주하거나 도약할 수 없습니다.",
                    None,
                    extra_flags
                )

        # 1.7 Distance & Line-of-Sight Check (Cannot interact/attack across rooms/walls)
        combat_or_social_verbs = ["공격", "찌르", "베", "대화", "말을", "물어", "훔치", "소매치기", "attack", "talk", "steal"]
        if any(v in action_lower for v in combat_or_social_verbs):
            for npc_id, npc in state.npcs.items():
                if (npc.name.lower() in action_lower or npc_id in action_lower):
                    if curr_loc and npc_id not in curr_loc.npcs and npc.location != curr_loc.id:
                        return (
                            False,
                            f"[{npc.name}]은(는) 현재 장소({curr_loc.name})의 시야 내에 없습니다. 다른 방이나 벽 너머의 대상을 조작할 수 없습니다.",
                            None,
                            extra_flags
                        )

        # 1.8 Social/Recruitment Context Flag (Passed down to dynamic DC check rather than hard-blocking)
        recruitment_verbs = ["동료가", "파티에", "합류", "따라와", "recruit", "join party"]
        if any(v in action_lower for v in recruitment_verbs):
            extra_flags['is_recruitment_attempt'] = True

        # 2. Inventory check: Cannot use or drop items not owned
        accessible_item_ids = set(state.player.inventory) | (set(curr_loc.items) if curr_loc else set())
        accessible_item_names = {state.items[i].name.lower() for i in accessible_item_ids if i in state.items}

        usage_verbs = ["사용", "찌른", "열", "먹", "휘두", "버린", "use", "unlock", "drop"]
        if any(verb in action_lower for verb in usage_verbs):
            for item_id, item in state.items.items():
                if item.name.lower() in action_lower or item_id in action_lower:
                    if item.name.lower() not in accessible_item_names and item_id not in accessible_item_ids:
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

        # 4. Trigger Deterministic Dice Rolls for Challenges with Fatigue Modifiers
        dice_result = None
        fatigue_val = state.player.fatigue

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
                fatigue=fatigue_val,
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
                target_part=target_part,
                fatigue=fatigue_val,
            )

            if dice_result.interrupt_counter:
                extra_flags['interrupt_counter'] = True

        # C. Stealth / Steal check
        elif any(v in action_lower for v in ["훔치", "소매치기", "몰래", "steal", "pickpocket", "sneak"]):
            dice_result = DiceEngine.perform_check(
                action_type="은신 / 절도",
                stat_value=state.player.dex_stat,
                dc=13,
                fatigue=fatigue_val,
            )

        # D. Dialogue Negotiation / Intimidation / Persuasion / Recruitment with Psychological Leverage
        elif any(v in action_lower for v in ["협박", "설득", "속이", "위협", "동료", "합류", "비밀", "부탁", "요구", "말을", "대화", "intimidate", "persuade", "threaten", "recruit"]):
            target_npc = None
            if curr_loc:
                loc_npcs = state.npcs_in_location(curr_loc.id)
                for n in loc_npcs:
                    if n.name.lower() in action_lower or n.id in action_lower:
                        target_npc = n
                        break
                if not target_npc and loc_npcs:
                    target_npc = loc_npcs[0]

            speech = parsed.get("dialogue", "") or action_clean
            speech_lower = speech.lower()
            
            # Psychological Leverage Evaluation
            psy_bonus = 0
            feedback_logs = []
            
            if target_npc:
                # 1. Check Taboo / Trauma Trigger (-10 Penalty / Negotiation Collapse)
                taboo_str = getattr(target_npc, "taboo", "").lower()
                trauma_str = getattr(target_npc, "trauma", "").lower()
                if taboo_str and any(k in speech_lower for k in ["부모", "모욕", "천박", "겁쟁이", "패배자", "배신자"]):
                    psy_bonus -= 10
                    feedback_logs.append(f"⚠️ [역린/금기 촉발: {target_npc.name} 극노 (-10 패널티)]")
                
                # 2. Check Desire Alignment (+6 Bonus)
                desire_str = getattr(target_npc, "desire", "").lower()
                if desire_str:
                    if any(k in desire_str for k in ["골드", "돈", "치료", "빚"]) and any(k in speech_lower for k in ["골드", "돈", "치료", "갚아", "보상", "금화"]):
                        psy_bonus += 6
                        feedback_logs.append(f"✨ [욕망 자극: {target_npc.name}의 금전/생계 욕망 공략 (+6 보너스)]")
                    elif any(k in desire_str for k in ["명예", "가보", "검"]) and any(k in speech_lower for k in ["명예", "가문", "되찾", "가보", "기사"]):
                        psy_bonus += 6
                        feedback_logs.append(f"✨ [욕망 자극: {target_npc.name}의 명예 회복 욕망 공략 (+6 보너스)]")
                    elif any(k in desire_str for k in ["탈출", "자유"]) and any(k in speech_lower for k in ["탈출", "나가", "안전", "자유", "살려"]):
                        psy_bonus += 6
                        feedback_logs.append(f"✨ [욕망 자극: {target_npc.name}의 탈출 이해관계 일치 (+6 보너스)]")

                # 3. Check Weakness / Secret Exploitation (+8 Bonus)
                weakness_str = getattr(target_npc, "weakness", "").lower()
                secret_str = getattr(target_npc, "blackmail_secret", "").lower()
                if weakness_str and any(k in speech_lower for k in ["가족", "동생", "술", "비밀", "약점", "칭찬", "대단"]):
                    psy_bonus += 8
                    feedback_logs.append(f"🎯 [치명적 약점 공략: {target_npc.name} 심리 동요 (+8 보너스)]")
                if secret_str and any(k in speech_lower for k in ["수배", "횡령", "첩자", "스파이", "과거", "비리"]):
                    psy_bonus += 8
                    feedback_logs.append(f"🎯 [숨겨진 치부 레버리지: {target_npc.name} 압박 (+8 보너스)]")

            base_dc = 15 if not any(v in action_lower for v in recruitment_verbs) else 18
            effective_dc = max(5, base_dc - psy_bonus)
            
            dice_result = DiceEngine.perform_check(
                action_type="화술 / 심리 설득",
                stat_value=state.player.cha_stat,
                dc=effective_dc,
                target_npc_id=target_npc.id if target_npc else None,
                fatigue=fatigue_val,
            )
            
            if feedback_logs:
                dice_result.summary_ko += " | " + " ".join(feedback_logs)

        # E. Lockpicking / Chest unlocking check
        elif any(v in action_lower for v in ["자물쇠", "따기", "궤짝을 부수", "pick lock", "force open"]):
            dice_result = DiceEngine.perform_check(
                action_type="자물쇠 해제 / 기계 조작",
                stat_value=state.player.dex_stat,
                dc=13,
                fatigue=fatigue_val,
            )

        return True, "", dice_result, extra_flags

