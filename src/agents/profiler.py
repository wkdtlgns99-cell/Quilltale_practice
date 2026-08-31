import json
import logging
from src.llm import get_llm
from src.core.config import LLM_NAME
from src.world.state import WorldState

logger = logging.getLogger(__name__)

def update_combat_profiles(state: WorldState, combat_log: str, participants: list[str]):
    if not combat_log or len(participants) < 2:
        return
    llm = get_llm(LLM_NAME)
    prompt = f'''
다음은 방금 일어난 전투의 로그입니다:
{combat_log}

참가자 목록: {', '.join(participants)}

각 참가자별로 전투 로그에서 드러난 1) 강점, 2) 약점, 3) 선호 전술을 분석하고, 다른 참가자들이 이 대상에 대해 알게 된 정보(파훼법 등)를 요약해주세요.
반드시 다음 형식의 JSON만 출력하세요:
{{
  "participant_id": {{
    "strengths": "...",
    "weaknesses": "...",
    "preferred_tactics": "...",
    "intel_for_others": "이 대상을 상대할 때의 팁"
  }}
}}
'''
    try:
        resp = llm.generate(prompt, "당신은 TRPG 전투 프로파일러입니다. 오직 JSON만 반환합니다.")
        text = resp.text.strip()
        if text.startswith("`json"): text = text[7:]
        if text.endswith("`"): text = text[:-3]
        data = json.loads(text.strip())
        for pid, pdata in data.items():
            entity = None
            if pid == state.player.name or pid == "Player":
                entity = state.player
                pid = "Player"
            elif pid in state.npcs:
                entity = state.npcs[pid]
            if entity:
                cp = entity.combat_profile
                if pdata.get("strengths"): cp.strengths = pdata["strengths"]
                if pdata.get("weaknesses"): cp.weaknesses = pdata["weaknesses"]
                if pdata.get("preferred_tactics"): cp.preferred_tactics = pdata["preferred_tactics"]
                for other_id in participants:
                    norm_other = "Player" if other_id == state.player.name else other_id
                    if norm_other != pid:
                        other_entity = state.player if norm_other == "Player" else state.npcs.get(norm_other)
                        if other_entity:
                            other_entity.combat_profile.intel_book[pid] = pdata.get("intel_for_others", "")
        logger.info("Combat profiles successfully updated.")
    except Exception as e:
        logger.error(f"Failed to update combat profiles: {e}")
