"""
Deterministic Perception and Theft Discovery Engine for Quilltale TRPG.
Compares thief stealth against victim's Perception (감각) stat.
Differentiates 3 narrative tiers based on perception margin:
1. IMPERCEPTIBLE (Margin >= 5): Victim is completely oblivious. No foreshadowing or hints permitted.
2. SUBTLE_HINT (Margin 0 ~ 4): Victim's keen senses detect a subtle tactile/auditory discrepancy.
3. CAUGHT (Margin < 0): Victim's perception catches the thief in the act.

Delayed Discovery:
Unnoticed thefts are only discovered through physical, causal triggers (e.g. opening bags, paying merchants,
adjusting belts, or physical jolts), never through arbitrary turn timers.
"""
from typing import Dict, Any, List, Optional
import random
from src.world.dice import DiceEngine
from src.world.state import WorldState, Player, NPC


class PerceptionEngine:
    # Physical/contextual triggers that reveal stolen goods to the victim
    DISCOVERY_TRIGGERS: Dict[str, List[str]] = {
        "bag_access": [
            "가방", "배낭", "인벤토리", "소지품", "주머니를 뒤적", "꺼내", "열어", "확인", "뒤적", "찾아", "inventory", "bag"
        ],
        "transaction": [
            "지불", "산다", "사고", "구매", "골드를 내", "돈을 내", "동전을 건넨", "가격을 묻", "값을 치", "결제", "pay", "buy"
        ],
        "body_tactile": [
            "주머니에 손", "허리띠", "벨트", "고쳐 매", "짐을 풀", "내려놓", "짐을 내", "외투를 벗", "옷을 갈아"
        ],
        "physical_jolt": [
            "구르", "도약", "낙하", "부딪", "충돌", "밀쳐", "달려", "전력 질주"
        ]
    }

    @classmethod
    def evaluate_theft_vs_perception(
        cls,
        thief: Any,
        victim: Any,
        is_distracted: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates stealth vs perception contest.
        Thief: d20 + Agility modifier (+2 if victim is distracted).
        Victim: Passive Perception = 10 + Perception modifier.
        """
        thief_roll = DiceEngine.roll_d20()
        thief_mod = DiceEngine.stat_modifier(getattr(thief, "agility", 10))
        distraction_bonus = 2 if is_distracted else 0
        total_stealth = thief_roll + thief_mod + distraction_bonus

        victim_per = getattr(victim, "perception_stat", getattr(victim, "perception", 10))
        victim_passive_per = 10 + DiceEngine.stat_modifier(victim_per)

        margin = total_stealth - victim_passive_per

        if margin >= 5:
            tier = "imperceptible"
            success = True
            noticed = False
            hint_desc = ""
            gm_directive = (
                f"피해자의 감각({victim_per})으로는 {thief.name}의 손길을 전혀 인지하지 못했습니다. "
                "도난 사실은 물론 어떠한 위화감이나 복선도 절대 서사에 누설하지 마십시오. 평화로운 일상처럼 서술하십시오."
            )
        elif margin >= 0:
            tier = "subtle_hint"
            success = True
            noticed = False
            hint_desc = "가방 끈이 스치는 서늘한 마찰감과 스쳐 지나간 인물의 미묘한 위화감"
            gm_directive = (
                f"피해자의 감각({victim_per})이 예민하여 무언가 어긋난 기운을 감지했습니다. "
                f"도난 사실을 직접 발설하지 말고, '스치는 서늘한 바람, 가방 끈의 미세한 마찰감' 등 오감 복선만 은밀히 묘사하십시오."
            )
        else:
            tier = "caught"
            success = False
            noticed = True
            hint_desc = "현장 적발"
            gm_directive = (
                f"피해자의 날카로운 감각({victim_per})이 {thief.name}의 은밀한 손길을 포착했습니다! "
                f"소지품에 손을 뻗던 {thief.name}의 손목이 낚아채이거나 현장에서 들통난 긴장감 넘치는 대치 상황을 서술하십시오."
            )

        return {
            "tier": tier,
            "success": success,
            "player_noticed": noticed,
            "total_stealth": total_stealth,
            "victim_passive_per": victim_passive_per,
            "margin": margin,
            "hint_desc": hint_desc,
            "gm_directive": gm_directive,
        }

    @classmethod
    def record_unnoticed_theft(
        cls,
        state: WorldState,
        thief_npc: NPC,
        stolen_desc: str,
        stolen_type: str,
        amount: int = 0,
        item_id: str = ""
    ) -> Dict[str, Any]:
        """Records an unnoticed theft entry into player's state."""
        entry = {
            "thief_id": thief_npc.id,
            "thief_name": thief_npc.name,
            "stolen_desc": stolen_desc,
            "stolen_type": stolen_type,
            "amount": amount,
            "item_id": item_id,
            "turn": state.turn
        }
        state.player.unnoticed_thefts.append(entry)
        return entry

    @classmethod
    def check_delayed_theft_discovery(cls, state: WorldState, action: str) -> List[Dict[str, Any]]:
        """
        Checks if player's natural language action triggers the delayed discovery of stolen goods.
        Returns a list of discovered theft events, clearing them from unnoticed_thefts.
        """
        if not state.player.unnoticed_thefts:
            return []

        action_lower = action.lower()
        matched_trigger = None
        for trig_type, kws in cls.DISCOVERY_TRIGGERS.items():
            if any(k in action_lower for k in kws):
                matched_trigger = trig_type
                break

        if not matched_trigger:
            return []

        discovered_events = []
        for entry in list(state.player.unnoticed_thefts):
            thief_name = entry.get("thief_name", "미상의 괴한")
            stolen_desc = entry.get("stolen_desc", "물품")

            if matched_trigger == "transaction":
                reason = f"거래 대금을 지불하기 위해 허리춤의 지갑을 더듬던 중 {stolen_desc}이(가) 사라진 것을 깨달았습니다"
            elif matched_trigger == "bag_access":
                reason = f"가방을 열어 소지품을 확인하는 순간 {stolen_desc}이(가) 감쪽같이 사라진 것을 발견했습니다"
            elif matched_trigger == "body_tactile":
                reason = f"허리춤을 매만지다 매달려 있어야 할 {stolen_desc}이(가) 허전하게 비어있음을 알아차렸습니다"
            else:
                reason = f"몸을 움직이던 중 허리춤의 무게 중심이 비정상적으로 가벼워진 위화감에 확인해보니 {stolen_desc}을(를) 도난당했습니다"

            disc_info = {
                "stolen_desc": stolen_desc,
                "thief_name": thief_name,
                "reason_ko": reason,
                "log_ko": f"🚨 [도난 발각!] {reason}! (용의자: 일전에 마주쳤던 [{thief_name}])",
                "gm_directive": (
                    f"플레이어가 비로소 {stolen_desc}을(를) 도난당한 사실을 확인하고 경악했습니다! "
                    f"최근 스쳐 지나갔던 용의자 [{thief_name}]의 수상했던 태도를 떠올리며 배신감과 추적의 의지를 서사에 부여하십시오."
                )
            }
            discovered_events.append(disc_info)

        # Clear discovered thefts
        state.player.unnoticed_thefts.clear()
        return discovered_events
