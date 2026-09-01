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
- 이동 가능한 통로: {exits}
- 실제 보유 아이템: {inventory}
- 보유 스킬 및 주문: {skills}
- 진행 중인 모험 과제: {active_quests}
- 직전 상황 서사: {recent_narration}

[플레이어 행동 수칙]
1. [실제 아이템만 사용]: '실제 보유 아이템' 목록({inventory})에 없는 물건은 절대 사용할 수 없습니다. 없는 아이템을 날조하지 마십시오.
2. [능동적 탐험과 모험 전개]:
   - 이미 대화한 장소나 같은 NPC에게 똑같은 질문을 반복하지 마십시오.
   - 단서를 얻었거나 할 일이 끝났다면 새로운 출구({exits})를 통해 숲길, 지하실, 던전으로 즉시 이동하십시오.
   - 주변의 수상한 기물 조사, 잠입, 전투, 마법 영창, 협상 등 상황에 맞게 대담하고 몰입감 있는 행동을 취하십시오.
3. [출력 형식]: 다른 생각, 인사, 설명, 따옴표 없이 오직 플레이어의 행동 선언 1줄만 한국어로 출력하십시오.
"""


class PlayerBotAgent:
    PERSONAS = {
        "curious_scholar": "호기심 많은 학자 (주변 단서를 조사하고, 고대어를 해독하며, 사람들과 대화하여 비밀을 캐내는 신중한 탐험가)",
        "aggressive_warrior": "호쾌한 돌격 전사 (적대적 존재를 보면 물러서지 않고 칼날을 휘두르며, 위험을 정면 돌파하는 용맹한 모험가)",
        "cautious_mage": "원소 마법사 (위험 시 후방에서 화염/빙결 영창을 구사하며, 체력이 낮아지면 치유 포션을 마시는 지적인 영창술사)",
        "shadow_rogue": "은밀한 도적 (함정을 경계하고, 보물 상자를 락픽하며, 기습과 협상을 적절히 섞어 생존을 꾀하는 방랑자)"
    }

    def __init__(self, llm: Optional[BaseLLM] = None, persona_key: str = "curious_scholar"):
        self.llm = llm
        self.persona_key = persona_key
        self.persona_description = self.PERSONAS.get(persona_key, self.PERSONAS["curious_scholar"])

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
                exits_str = ", ".join(f"{d}({lid})" for d, lid in (curr_loc.exits.items() if curr_loc else {})) or "없음"
                
                present_npcs = state.npcs_in_location(state.player.location)
                npcs_str = ", ".join(f"{n.name}({n.job or '인물'}, {n.disposition})" for n in present_npcs) or "주변에 사람 없음"
                inv_str = ", ".join(state.items[i].name for i in state.player.inventory if i in state.items) or "비어있음"
                skills_str = ", ".join(state.skills_db[s].name for s in state.player.skills if s in state.skills_db) or "기본 공격"
                active_quests_str = ", ".join(f"[{q.title} - 진행도: {q.progress}%]" for q in state.quests if not q.completed) or "주변 탐색 및 새로운 의뢰/단서 발굴"

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
                    recent_narration=recent_narration[-300:] if recent_narration else "막 모험을 시작했습니다."
                )

                response = self.llm.generate(prompt)
                resp_text = getattr(response, "text", getattr(response, "content", str(response)))
                action = resp_text.strip().strip('"').strip("'")
                if action and len(action) > 2:
                    return action
            except Exception as e:
                logger.warning(f"PlayerBot LLM decision failed, fallback to heuristic: {e}")

        # Smart Contextual Heuristics (0-Token Mode)
        return self._heuristic_decision(state)

    def _heuristic_decision(self, state: WorldState) -> str:
        """Smart rule-based decision fallback without LLM tokens."""
        curr_loc = state.current_location()
        present_npcs = state.npcs_in_location(state.player.location)
        hostiles = [n for n in present_npcs if n.alive and n.disposition == "hostile"]
        neutrals = [n for n in present_npcs if n.alive and n.disposition != "hostile"]

        # 1. Low HP: Drink potion or rest
        if state.player.health < state.player.max_health * 0.35:
            potion_ids = [i for i in state.player.inventory if "potion" in i or "포션" in state.items.get(i, Item(id="", name="", description="", location="")).name]
            if potion_ids:
                return "가방에서 체력 회복 포션을 꺼내 급히 들이킨다."
            return "숨을 헐떡이며 방어 태세를 취하고 뒤로 물러선다."

        # 2. Hostile NPC present: Combat attack
        if hostiles:
            target = hostiles[0]
            if "scholar" in self.persona_key or "mage" in self.persona_key:
                if state.player.known_magic_words:
                    return f"손을 뻗어 '이그니스 사기타 볼란스' 주문을 영창하여 {target.name}에게 불꽃 화살을 발사한다."
                return f"마력을 집중하여 {target.name}을 향해 원거리 마력탄을 쏜다."
            return f"강철검을 단단히 쥐고 {target.name}의 빈틈을 노려 날카롭게 베어버린다."

        # 3. Friendly/Neutral NPC present: Talk/Inquire
        if neutrals and random.random() < 0.6:
            target = random.choice(neutrals)
            queries = [
                f"{target.name}에게 다가가 이 주변의 소문과 위험 지역에 대해 묻는다.",
                f"{target.name}에게 가벼운 인사를 건네며 일거리나 퀘스트가 있는지 묻는다.",
                f"{target.name}의 안색과 손에 든 물건을 조심스럽게 살핀다."
            ]
            return random.choice(queries)

        # 4. Explore/Move to adjacent location
        if curr_loc and curr_loc.exits:
            direction, dest_id = random.choice(list(curr_loc.exits.items()))
            return f"{direction} 방향 통로로 발걸음을 옮겨 이동한다."

        return "주변의 기물과 바닥의 흔적을 면밀히 조사한다."
