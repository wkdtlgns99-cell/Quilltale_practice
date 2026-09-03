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
        '머리': ['머리', '두개골', '이마'],
        '목': ['목을', '목덜미', '목에', '목 '],
        '눈': ['눈을', '시야', '안구'],
        '급소': ['급소'],
        '심장': ['심장'],
        '가슴': ['가슴', '흉부', '배를', '복부'],
        '등': ['등을', '등에'],
        '팔': ['팔을', '팔에', '어깨', '팔꿈치'],
        '손': ['손을', '손목'],
        '다리': ['다리', '허벅지', '정강이'],
        '관절': ['관절', '무릎'],
        '발': ['발을', '발에', '발목'],
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

        usage_verbs = ["사용", "찌른", "열", "먹", "휘두", "버린", "착용", "장착", "입는", "입어", "쓴다", "써", "낀다", "끼어", "차다", "찬다", "쥔다", "use", "unlock", "drop", "equip"]
        if any(verb in action_lower for verb in usage_verbs):
            for item_id, item in state.items.items():
                if item.name.lower() in action_lower or item_id in action_lower:
                    if item.name.lower() not in accessible_item_names and item_id not in accessible_item_ids:
                        return (
                            False,
                            f"가방이나 주변에 존재하지 않는 [{item.name}]을(를) 착용하거나 사용할 수 없습니다.",
                            None,
                            extra_flags
                        )

        # 2.5 Equipment Equip / Unequip Intent Detection
        equip_verbs = ["착용", "장착", "입는", "입어", "쓴다", "써", "낀다", "끼어", "차다", "찬다", "쥔다", "equip", "wield", "wear"]
        unequip_verbs = ["벗는다", "벗어", "뺀다", "빼어", "해제", "집어넣", "unequip", "remove"]
        is_equip = any(v in action_lower for v in equip_verbs)
        is_unequip = any(v in action_lower for v in unequip_verbs)

        if is_equip or is_unequip:
            found_item = None
            for item_id in (state.player.inventory if is_equip else list(dict.fromkeys(state.player.inventory + list(state.items.keys())))):
                if item_id in state.items:
                    item = state.items[item_id]
                    if item.name.lower() in action_lower or item_id in action_lower:
                        found_item = item
                        break

            slot = "chest"
            if found_item:
                itype = found_item.item_type.lower()
                iname = found_item.name.lower()
                if itype == "weapon" or any(w in iname for w in ["검", "단검", "도끼", "지팡이", "창", "활", "둔기", "메이스"]):
                    slot = "weapon"
                elif any(h in iname for h in ["투구", "모자", "서클릿", "헬름"]):
                    slot = "head"
                elif any(f in iname for f in ["가면", "안경", "안대"]):
                    slot = "face"
                elif any(c in iname for c in ["갑옷", "흉갑", "로브", "상의", "코트", "조끼"]):
                    slot = "chest"
                elif any(l in iname for l in ["바지", "각반", "그리브", "하의"]):
                    slot = "legs"
                elif any(b in iname for b in ["부츠", "신발", "장화"]):
                    slot = "boots"
                elif any(g in iname for g in ["장갑", "건틀릿"]):
                    slot = "gloves"
                elif any(cp in iname for cp in ["망토", "케이프"]):
                    slot = "cape"
                elif itype == "ring" or "반지" in iname:
                    slot = "ring"
                elif itype == "earring" or "귀걸이" in iname:
                    slot = "earring"
            elif is_unequip:
                # Slot-based unequip if specific item name wasn't stated
                if any(h in action_lower for h in ["투구", "모자", "헬름"]):
                    slot = "head"
                    found_item = state.items.get(state.player.equipment.head)
                elif any(c in action_lower for c in ["갑옷", "흉갑", "로브"]):
                    slot = "chest"
                    found_item = state.items.get(state.player.equipment.chest)
                elif any(w in action_lower for w in ["무기", "검", "단검"]):
                    slot = "weapon"
                    found_item = state.items.get(state.player.equipment.weapon)
                elif "반지" in action_lower:
                    slot = "ring"
                    found_item = state.items.get(state.player.equipment.rings[0]) if state.player.equipment.rings else None
                elif "귀걸이" in action_lower:
                    slot = "earring"
                    found_item = state.items.get(state.player.equipment.earrings[0]) if state.player.equipment.earrings else None

            if found_item or is_unequip:
                extra_flags["equip_intent"] = {
                    "action": "equip" if is_equip else "unequip",
                    "item_id": found_item.id if found_item else "",
                    "item_name": found_item.name if found_item else slot,
                    "slot": slot
                }

        # 2.6 Medical Treatment & Injury Compatibility Check (Anti-Yes-Man)
        treatment_verbs = ["치료", "수술", "봉합", "정골", "붕대", "부목", "소독", "바른", "바르고", "감싼", "감싸", "고정", "heal", "treat", "cure", "surgery"]
        if any(v in action_lower for v in treatment_verbs):
            from src.world.injury_engine import InjuryEngine
            # Find item mentioned (exact match first)
            med_item = None
            for item_id in state.player.inventory:
                if item_id in state.items:
                    it = state.items[item_id]
                    if it.name.lower() in action_lower or it.id in action_lower:
                        med_item = it
                        break

            # Specific keyword fallback if not exact match
            if not med_item:
                for kw in ["부목", "붕대", "연고", "약초", "포션", "물약"]:
                    if kw in action_lower:
                        for item_id in state.player.inventory:
                            if item_id in state.items:
                                it = state.items[item_id]
                                if kw in it.name.lower():
                                    med_item = it
                                    break
                        if med_item:
                            break

            # Find matching player injury
            target_injury = None
            if state.player.injuries:
                for inj in state.player.injuries:
                    part = inj.split()[0]
                    if part in action_lower or inj in action_lower:
                        target_injury = inj
                        break
                if not target_injury and any(v in action_lower for v in ["부상", "골절", "상처", "통증", "아픈"]):
                    target_injury = state.player.injuries[0]

            # Check item treatment legality
            if med_item and target_injury:
                can_treat, reject_msg = InjuryEngine.can_treat_with_item(target_injury, med_item)
                if not can_treat:
                    return (
                        False,
                        reject_msg,
                        None,
                        extra_flags
                    )
                extra_flags["treatment_intent"] = {
                    "type": "item",
                    "item_id": med_item.id,
                    "item_name": med_item.name,
                    "injury_name": target_injury
                }
            elif any(d in action_lower for d in ["의사", "치료사", "외과의", "약제사", "doctor", "surgeon"]):
                doc_npc = None
                if curr_loc:
                    for nid in curr_loc.npcs:
                        if nid in state.npcs:
                            npc = state.npcs[nid]
                            if any(k in npc.name.lower() or k in npc.description.lower() for k in ["의사", "치료사", "외과의", "약제사", "doctor"]):
                                doc_npc = npc
                                break
                if doc_npc and target_injury:
                    extra_flags["treatment_intent"] = {
                        "type": "doctor",
                        "doctor_id": doc_npc.id,
                        "doctor_name": doc_npc.name,
                        "injury_name": target_injury,
                        "fee": 50
                    }

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

        # Target NPC detection
        target_ac = 12
        target_npc_id = None
        if curr_loc:
            loc_npcs = state.npcs_in_location(curr_loc.id)
            for n in loc_npcs:
                if n.name.lower() in action_lower or n.id in action_lower:
                    target_ac = n.armor_class
                    target_npc_id = n.id
                    break
            if not target_npc_id and loc_npcs:
                hostiles = [n for n in loc_npcs if n.alive and n.disposition == "hostile"]
                if hostiles:
                    target_ac = hostiles[0].armor_class
                    target_npc_id = hostiles[0].id
                elif len(loc_npcs) == 1:
                    target_ac = loc_npcs[0].armor_class
                    target_npc_id = loc_npcs[0].id

        # Check if player declared a specific learned skill
        matched_player_skill = None
        if state.player.skills:
            for s_id in state.player.skills:
                sk = state.skills_db.get(s_id)
                if not sk:
                    continue
                s_name_clean = sk.name.lower().replace("(", " ").replace(")", " ").replace(":", " ")
                keywords = [w for w in s_name_clean.split() if len(w) >= 2]
                if sk.name.lower() in action_lower or any(kw in action_lower for kw in keywords):
                    matched_player_skill = sk
                    break

        # S. Player Specific Skill Execution Branch
        if matched_player_skill:
            if getattr(matched_player_skill, "current_cooldown", 0) > 0:
                return (
                    False,
                    f"[{matched_player_skill.name}]은(는) 아직 재사용 대기시간입니다. (남은 쿨다운: {matched_player_skill.current_cooldown}턴)",
                    None,
                    extra_flags
                )
            if matched_player_skill.resource_type == "mana" and state.player.mana < matched_player_skill.resource_cost:
                return (
                    False,
                    f"마나가 부족하여 [{matched_player_skill.name}]을(를) 시전할 수 없습니다. (필요: {matched_player_skill.resource_cost}, 현재: {state.player.mana})",
                    None,
                    extra_flags
                )
            if matched_player_skill.resource_type == "hp" and state.player.health <= matched_player_skill.resource_cost:
                return (
                    False,
                    f"체력이 부족하여 [{matched_player_skill.name}]의 생명력 대가를 감당할 수 없습니다. (필요: {matched_player_skill.resource_cost}, 현재: {state.player.health})",
                    None,
                    extra_flags
                )

            stat_key = matched_player_skill.scaling_stat
            stat_val = state.player.str_stat
            if stat_key == "int":
                stat_val = state.player.int_stat
            elif stat_key == "dex":
                stat_val = state.player.dex_stat
            elif stat_key == "wis":
                stat_val = state.player.wis_stat
            elif stat_key == "con":
                stat_val = state.player.con_stat

            extra_flags['player_skill_used'] = {
                'skill_id': matched_player_skill.id,
                'skill_name': matched_player_skill.name,
                'resource_type': matched_player_skill.resource_type,
                'resource_cost': matched_player_skill.resource_cost,
                'cooldown_turns': matched_player_skill.cooldown_turns,
                'inflicted_status': matched_player_skill.inflicted_status,
                'displacement': matched_player_skill.displacement,
                'armor_penetration': matched_player_skill.armor_penetration,
            }

            effective_dc = max(5, int(target_ac * (1.0 - getattr(matched_player_skill, "armor_penetration", 0.0))))

            dice_result = DiceEngine.perform_check(
                action_type=f"스킬: {matched_player_skill.name}",
                stat_value=stat_val,
                dc=effective_dc,
                base_damage=matched_player_skill.base_value,
                scaling=matched_player_skill.scaling_factor,
                target_npc_id=target_npc_id,
                target_part=target_part,
                fatigue=fatigue_val,
            )
            if dice_result.interrupt_counter:
                extra_flags['interrupt_counter'] = True

        # A. Generic Magic Attack Check (0 mana fallback or generic spell)
        elif any(v in action_lower for v in ["파이어", "화염", "마법", "볼트", "빙결", "뇌전", "주문", "영창하여", "시전"]):
            has_incant_speech = bool(parsed["dialogue"]) or ("영창" in action_lower)
            is_no_incant = not has_incant_speech
            extra_flags['is_no_incantation'] = is_no_incant

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

        # B. Generic Physical Combat Attack (0 mana standard attack to conserve resources)
        elif any(v in action_lower for v in ["공격", "찌르", "베", "벤", "찍", "내려치", "후려", "타격", "때리", "칼로", "검으", "단검으", "도끼", "attack", "strike", "stab", "slash"]):
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

