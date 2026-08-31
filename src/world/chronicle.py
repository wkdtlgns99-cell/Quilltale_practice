"""
World Chronicle System for Quilltale TRPG Engine.
Generates an epic in-game chronicle (영웅 일대기) when a world ends.
Chronicles are stored permanently and can be discovered in future worlds' libraries.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from src.core.config import CHRONICLES_DIR

logger = logging.getLogger(__name__)

CHRONICLE_SYSTEM_PROMPT = """
당신은 고대 전기(傳記) 작가입니다. 플레이어의 모험 기록을 영웅 일대기 형식으로 서술합니다.
반드시 다음 규칙을 따르십시오:
- 3인칭 시점, 고풍스럽고 서사적인 한국어 문체
- 책 한 면 분량 (600~800자)
- 세계관 이름, 주인공 이름, 그 인물의 출신과 성격 암시
- 핵심 동료/적 NPC 1~2명 언급
- 중요 사건 2~3개 서술 (직접 겪은 일 위주)
- 결말: 어떻게 이 이야기가 끝났는지 (사망/방생/은퇴/완결)
- 마치 실제 역사서나 소설의 한 챕터처럼 작성
"""

CHRONICLE_PROMPT_TEMPLATE = """
다음 모험 기록을 바탕으로 영웅 일대기를 작성하십시오.

[세계관 정보]
세계 이름: {world_name}
장르: {world_genre}

[주인공]
이름: {player_name}
최종 레벨: {level}
최종 평판: {reputation}
획득한 칭호: {titles}

[주요 NPC 목록]
{npc_summary}

[핵심 사건 기록 (중요도 4~5 기억)]
{key_events}

[최근 10턴 행동 요약]
{recent_history}

[결말 유형]
{ending_type}

위 내용을 바탕으로 600~800자의 한국어 영웅 일대기를 작성하십시오.
응답 형식: {{"chronicle": "일대기 텍스트"}}
"""

class ChronicleManager:
    @classmethod
    def generate_chronicle(cls, state, llm, ending_type: str = '사망') -> str:
        """
        Generate a heroic chronicle for the ended world.
        ending_type: '사망' | '방생' | '은퇴' | '완결'
        """
        # Gather key events from high-significance NPC memories
        key_events = []
        for npc in state.npcs.values():
            for mem in npc.memories:
                if mem.significance >= 4:
                    key_events.append(f'- (턴 {mem.turn}) {mem.description}')
        
        # NPC summary (alive + important)
        npc_summary_lines = []
        for npc in list(state.npcs.values())[:6]:  # Max 6 NPCs
            status = '살아있음' if npc.alive else '사망'
            npc_summary_lines.append(f'{npc.name} ({npc.description[:30]}...) [{status}]')
        
        # Player titles
        title_names = []
        for t_id in state.player.titles:
            t = state.titles_db.get(t_id)
            if t:
                title_names.append(t.name)
        
        # Recent history (last 10 turns)
        recent = state.history[-10:]
        recent_str = '\n'.join(
            f'턴 {h.get("turn","?")}: {h.get("action","")} → {h.get("narration","")[:60]}...'
            for h in recent
        )
        
        prompt = CHRONICLE_PROMPT_TEMPLATE.format(
            world_name=state.world_name,
            world_genre=getattr(state, 'world_genre', '다크 판타지'),
            player_name=state.player.name,
            level=state.player.level,
            reputation=state.player.reputation,
            titles=', '.join(title_names) if title_names else '없음',
            npc_summary='\n'.join(npc_summary_lines) if npc_summary_lines else '없음',
            key_events='\n'.join(key_events) if key_events else '기록된 중요 사건 없음',
            recent_history=recent_str if recent_str else '없음',
            ending_type=ending_type,
        )
        
        try:
            import json
            raw = llm.generate_json(prompt, CHRONICLE_SYSTEM_PROMPT)
            result = json.loads(raw)
            chronicle_text = result.get('chronicle', '')
        except Exception as e:
            logger.error(f'Chronicle generation failed: {e}')
            chronicle_text = (
                f'[{state.world_name}의 기록] {state.player.name}은(는) '
                f'레벨 {state.player.level}에 이 세계를 떠났다. ({ending_type})'
            )
        
        return chronicle_text
    
    @classmethod
    def save_chronicle(cls, world_id: str, world_name: str, player_name: str, chronicle_text: str, state) -> Path:
        """Save chronicle to disk and index into RAG lore."""
        CHRONICLES_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            'world_id': world_id,
            'world_name': world_name,
            'player_name': player_name,
            'world_genre': getattr(state, 'world_genre', ''),
            'ending_turn': state.turn,
            'chronicle': chronicle_text,
            'created_at': datetime.now().isoformat(),
        }
        save_path = CHRONICLES_DIR / f'{world_id}.json'
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f'Chronicle saved: {save_path}')
        return save_path
    
    @classmethod
    def load_chronicles_for_world(cls, world_id: str) -> list[dict]:
        """Load all chronicles associated with a world ID prefix (same world lineage)."""
        results = []
        if not CHRONICLES_DIR.exists():
            return results
        for p in CHRONICLES_DIR.glob('*.json'):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                results.append(data)
            except Exception:
                pass
        return results
    
    @classmethod
    def get_library_entries(cls) -> list[str]:
        """Get all chronicles formatted as library book entries for RAG lore injection."""
        chronicles = cls.load_chronicles_for_world('')  # Load all
        entries = []
        for c in chronicles:
            entry = (
                f'[고대 기록: {c.get("world_name", "알 수 없는 세계")}의 {c.get("player_name", "방랑자")}] '
                f'{c.get("chronicle", "")}'
            )
            entries.append(entry)
        return entries
