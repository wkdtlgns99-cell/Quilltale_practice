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

    @classmethod
    def evaluate_sensory_awareness(
        cls,
        perception_stat: int,
        faculty: str,
        dc: int = 12
    ) -> Dict[str, Any]:
        """
        Evaluates superhuman sensory faculties (premonition, gaze detection, kinesic anticipation, etc.).
        Returns dictionary containing success status, roll details, and atmospheric sensory clue.
        """
        mod = DiceEngine.stat_modifier(perception_stat)
        roll = DiceEngine.roll_d20()
        total = roll + mod
        is_success = total >= dc

        clues = {
            "premonition": {
                "success": "발을 내딛으려는 찰나, 목덜미를 타고 서늘한 전율이 흘러내리며 심장이 쿵 내려앉습니다. 1보 앞에 치명적인 함정이 숨겨져 있습니다.",
                "failure": "아무런 위화감도 느끼지 못했습니다."
            },
            "gaze_detection": {
                "success": "어둠 속에서 당신의 관자놀이를 집요하게 겨누는 서늘한 시선의 무게가 피부를 따끔거리게 찌릅니다.",
                "failure": "주변에 누군가 지켜보고 있다는 낌새를 알아채지 못했습니다."
            },
            "intuitive_insight": {
                "success": "상대의 입가는 웃고 있으나, 허리춤을 쥔 손가락의 미세한 경련과 불협화음을 내는 호흡에서 노골적인 배신의 살의를 간파했습니다.",
                "failure": "상대의 겉모습에 감춰진 진의를 꿰뚫어보지 못했습니다."
            },
            "structural_flaw": {
                "success": "적의 육중한 장갑 틈새, 가죽 끈이 마모되어 살점이 드러난 치명적인 방어의 결이 한눈에 들어옵니다. (방어력 -2 판정 관통)",
                "failure": "적의 빈틈이나 약점을 직관하지 못했습니다."
            },
            "kinesic_anticipation": {
                "success": "적이 칼을 뻗기 직전, 어깨 근육의 미세한 수축과 발뒤꿈치로 실리는 무게 중심의 이동을 읽었습니다. 다음 턴 전력 찌르기가 들어옵니다!",
                "failure": "적의 다음 예비 동작을 읽어내지 못했습니다."
            },
            "acoustic_spatial": {
                "success": "칠흑 같은 어둠 속에서도 발소리의 울림과 서늘한 공기 저항으로 3보 앞에 깎아지른 수직 구덩이가 있음을 알아챘습니다.",
                "failure": "어둠 속에서 지형의 굴곡을 파악하지 못해 발을 헛디딜 위험이 큽니다."
            },
            "heartbeat_hearing": {
                "success": "벽 너머 축축한 공기 사이로 얕고 거친 두 사람의 숨소리와 불규칙한 심장 박동이 또렷하게 귓전에 닿습니다.",
                "failure": "벽 너머의 기척을 잡아내지 못했습니다."
            },
            "mana_resonance": {
                "success": "공기 중에 감도는 미세한 정전기와 비릿한 유황 냄새, 그리고 피부를 간질이는 파동으로 은폐된 고대 마법진의 결을 포착했습니다.",
                "failure": "주변에 마나의 흐름이나 비전 흔적이 있는지 느끼지 못했습니다."
            }
        }

        faculty_data = clues.get(faculty, clues["premonition"])
        narrative = faculty_data["success"] if is_success else faculty_data["failure"]

        return {
            "faculty": faculty,
            "perception_stat": perception_stat,
            "roll": roll,
            "modifier": mod,
            "total": total,
            "dc": dc,
            "is_success": is_success,
            "sensory_clue_ko": narrative
        }
