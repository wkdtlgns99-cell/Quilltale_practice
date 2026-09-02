"""
Autonomous AI Player Bot for Quilltale TRPG.
Emulates human player decision-making with distinct archetypes/personas:
(e.g., Cautious Scholar, Aggressive Warrior, Shadow Rogue, Curious Explorer).
"""
import random
import logging
from typing import Optional, Dict, Any, List
from src.world.state import WorldState
from src.llm.base import BaseLLM

logger = logging.getLogger(__name__)

PLAYER_PERSONA_PROMPT = """
당신은 TRPG 판타지 세계를 모험하는 살아 숨쉬는 플레이어 캐릭터 [{player_name}]입니다.
성향 및 플레이 스타일: [{persona_style}]

[현재 상황 정보]
- 현재 장소: {location_name} ({location_desc})
- 신체 상태: ❤️ 체력 {health}/{max_health} | 💧 마나 {mana}/{max_mana} | 🪙 골드 {gold}G
- 주변 인물: {present_npcs}
- 이동 가능한 출구: {exits}
- 실제 보유 아이템: {inventory}
- 보유 스킬 및 주문: {skills}
- 진행 중인 모험 과제: {active_quests}
- 당신의 최근 행동 이력 (중복/실패 반복 절대 금지):
{recent_actions}
- 직전 상황 서사: {recent_narration}

[행동 선언 지침]
현재 상황과 분위기에 맞춰 아래의 유형 중 가장 자연스럽고 개연성 있는 1가지를 선택하여 구체적으로 행동하십시오:
1. [전투 상황 전술]: 적과 대치/교전 중일 때는 반드시 승리를 목표로 효율적으로 전술을 펼치십시오. 당신의 성향에 따라 적의 약점을 찌를지, 거리를 벌릴지, 혹은 자신이 다치더라도 위험에 처한 동료를 먼저 구할지 결단하십시오.
2. [지형/사물 탐색]: '{location_name}'의 묘사된 기물, 바닥의 흔적, 건축물의 문양을 직접 만지거나 조사하기
3. [인물 상호작용]: '{present_npcs}'에게 말을 걸어 단서/소문을 묻거나 표정/소지품을 관찰하기
4. [아이템/마법 응용]: 가방 속 '{inventory}'을 사용하거나 마법 '{skills}'을 현재 상황에 맞게 시전하기
5. [구역 이동]: 현재 구역의 탐색이 끝났다면 출구({exits}) 중 한 곳으로 전진하기

[⚠️ 억지 행동 방지 및 절대 수칙]
1. **없는 물건 사용 금지**: 가방({inventory})이나 주변 장소에 실제로 없는 허구의 아이템을 꺼내 쓰지 마십시오.
2. **거절당한 행동 반복 금지**: 최근 이력에서 시스템에 막히거나 거절당한 행동은 다른 창의적인 방법이 아닌 한 그대로 다시 시도하지 마십시오.
3. **스탯/신체 한계 준수**: 자신의 근력이나 마나 수치를 무시하고 억지로 바위를 들거나 무리한 행동을 선언하지 마십시오.
4. **1턴 1행동 원칙**: 한 번에 여러 개의 행동을 나열하지 말고, 명확하고 단호한 1가지 행동만 자연스러운 한국어 문장 1줄로 선언하십시오.
"""


class PlayerBotAgent:
    PERSONAS = {
        "curious_scholar": "호기심 많은 학자 (주변 단서를 조사하고 약점을 파악하며, 위험 시 거리를 벌리고 지능적으로 대처하는 신중한 탐험가)",
        "aggressive_warrior": "호쾌한 돌격 전사 (전투 시 승리를 위해 전방에서 적의 약점을 분쇄하고 닥돌하는 용맹한 모험가)",
        "guardian_knight": "수호 기사 (전투 시 효율적으로 싸우되, 자신이 조금 다치더라도 위험에 처한 동료나 아군을 최우선으로 구출하고 방패가 되어주는 헌신자)",
        "cautious_mage": "원소 마법사 (후방에서 치명적인 원소 주문을 시전하며, 적의 접근을 통제하고 아군을 엄호하는 지적인 영창술사)",
        "shadow_rogue": "은밀한 도적 (함정을 경계하고 적의 사각지대에서 기습하며, 전황이 극도로 불리하면 연막을 치고 생존을 도모하는 현실주의자)"
    }

    def __init__(self, llm: Optional[BaseLLM] = None, persona_key: str = "curious_scholar"):
        self.llm = llm
        self.persona_key = persona_key
        self.persona_description = self.PERSONAS.get(persona_key, self.PERSONAS["curious_scholar"])
        self._action_cycle_counter = 0

    def decide_action(self, state: WorldState, recent_narration: str = "") -> str:
        """
        Decides the next turn action. If LLM is available, uses generative AI thinking.
        Otherwise, uses smart contextual heuristics (0-token mode).
        """
        if self.llm:
            try:
                curr_loc = state.current_location()
                loc_name = curr_loc.name if curr_loc else "미지의 장소"
                loc_desc = curr_loc.description if curr_loc else ""
                
                direction_ko = {
                    "north": "북쪽", "south": "남쪽", "east": "동쪽", "west": "서쪽",
                    "upstairs": "2층 계단", "downstairs": "지하 통로"
                }
                exit_descriptions = []
                for d, lid in (curr_loc.exits.items() if curr_loc else {}):
                    d_ko = direction_ko.get(d.lower(), d)
                    target_loc = state.locations.get(lid)
                    loc_display = target_loc.name if target_loc else "미지의 구역"
                    exit_descriptions.append(f"{d_ko}({loc_display} 방향)")
                exits_str = ", ".join(exit_descriptions) or "더 이상 이어진 통로 없음"
                
                present_npcs = state.npcs_in_location(state.player.location)
                npcs_str = ", ".join(f"{n.name}({n.job or '인물'}, {n.disposition})" for n in present_npcs) or "주변에 사람 없음"
                inv_str = ", ".join(state.items[i].name for i in state.player.inventory if i in state.items) or "비어있음"
                skills_str = ", ".join(state.skills_db[s].name for s in state.player.skills if s in state.skills_db) or "기본 공격"
                active_quests_str = ", ".join(f"[{q.title} - 진행도: {q.progress}%]" for q in state.quests if not q.completed) or "주변 탐색 및 새로운 의뢰/단서 발굴"

                past_actions = [f"- {h.get('turn')}턴: {h.get('action')}" for h in state.history[-3:] if h.get("action")]
                past_actions_str = "\n".join(past_actions) if past_actions else "- 모험의 첫 턴입니다."

                prompt = PLAYER_PERSONA_PROMPT.format(
                    player_name=state.player.name,
                    persona_style=self.persona_description,
                    location_name=loc_name,
                    location_desc=loc_desc,
                    health=state.player.health,
                    max_health=state.player.max_health,
                    mana=state.player.mana,
                    max_mana=state.player.max_mana,
                    gold=state.player.gold,
                    present_npcs=npcs_str,
                    exits=exits_str,
                    inventory=inv_str,
                    skills=skills_str,
                    active_quests=active_quests_str,
                    recent_actions=past_actions_str,
                    recent_narration=recent_narration[-300:] if recent_narration else "막 모험을 시작했습니다."
                )

                response = self.llm.generate(prompt)
                resp_text = getattr(response, "text", getattr(response, "content", str(response)))
                action = resp_text.strip().strip('"').strip("'")
                
                past_action_texts = [h.get('action', '').strip() for h in state.history[-4:] if h.get("action")]
                is_verbatim_repeat = any(action == past or (len(past) > 5 and past in action) for past in past_action_texts if past)

                if action and len(action) > 2 and not is_verbatim_repeat:
                    return action
            except Exception as e:
                logger.warning(f"PlayerBot LLM decision failed, fallback to heuristic: {e}")

        # Smart Contextual Heuristics (0-Token Mode)
        return self._heuristic_decision(state)

    def _heuristic_decision(self, state: WorldState) -> str:
        """Smart rule-based decision fallback with diverse roleplay actions."""
        self._action_cycle_counter += 1
        curr_loc = state.current_location()
        present_npcs = state.npcs_in_location(state.player.location)
        hostiles = [n for n in present_npcs if n.alive and n.disposition == "hostile"]
        neutrals = [n for n in present_npcs if n.alive and n.disposition != "hostile"]

        # 1. Low HP: Drink potion or take defensive stance
        if state.player.health < state.player.max_health * 0.35:
            potion_ids = [i for i in state.player.inventory if "potion" in i or "포션" in state.items.get(i, Item(id="", name="", description="", location="")).name]
            if potion_ids:
                return "가방에서 체력 회복 포션을 꺼내 급히 들이킨다."
            return "숨을 헐떡이며 방어 태세를 취하고 신중하게 뒤로 물러선다."

        # 2. Hostile NPC present: Combat attack
        if hostiles:
            target = hostiles[0]
            if "scholar" in self.persona_key or "mage" in self.persona_key:
                if state.player.known_magic_words:
                    return f"손을 뻗어 '이그니스' 주문을 외우며 {target.name}에게 화염 마법을 투사한다."
                return f"마력을 집중하여 {target.name}을 향해 날카로운 비전 탄환을 발사한다."
            return f"손질된 단검을 강하게 쥐고 {target.name}의 빈틈을 노려 정면으로 베어낸다."

        # 3. Neutral NPC present: Dialogue and investigation
        if neutrals and (self._action_cycle_counter % 2 == 1):
            target = random.choice(neutrals)
            queries = [
                f"{target.name}에게 다가가 이 지역에 숨겨진 비밀이나 위험에 대해 은밀히 묻는다.",
                f"{target.name}에게 인사를 건네며 최근 발견된 단서나 유물에 대한 정보를 요청한다.",
                f"{target.name}의 옷차림과 손에 쥔 물건을 유심히 관찰하며 의도를 파악한다."
            ]
            return random.choice(queries)

        # 4. In-depth Room Investigation & Item Use (Cycle: Inspect -> Read -> Move)
        cycle_mod = self._action_cycle_counter % 3
        if cycle_mod == 1:
            inv_items = [state.items[i].name for i in state.player.inventory if i in state.items]
            if "낡은 여행 일지" in inv_items:
                return "낡은 여행 일지를 펼쳐 현재 위치의 지형 스케치와 단서를 꼼꼼히 대조해본다."
            return "현재 구역의 바닥과 기둥에 새겨진 마력의 흐름과 기이한 흔적을 손으로 쓸어내리며 면밀히 조사한다."
        elif cycle_mod == 2:
            return "주변의 부서진 석조 제단과 수상한 균열 틈새에 숨겨진 장치나 유물이 있는지 탐색한다."

        # 5. Move to adjacent location when ready
        if curr_loc and curr_loc.exits:
            direction_ko = {
                "north": "북쪽", "south": "남쪽", "east": "동쪽", "west": "서쪽",
                "upstairs": "2층 계단", "downstairs": "지하 통로"
            }
            direction, dest_id = random.choice(list(curr_loc.exits.items()))
            d_ko = direction_ko.get(direction.lower(), direction)
            target_loc = state.locations.get(dest_id)
            loc_name = target_loc.name if target_loc else "다음 구역"
            return f"{d_ko} 통로를 통해 {loc_name} 방향으로 신중하게 발걸음을 옮긴다."

        return "주변의 지형지물을 살피며 다음 행동을 신중하게 가늠한다."
