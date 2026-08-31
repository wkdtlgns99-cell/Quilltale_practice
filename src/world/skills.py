"""
Skill System for Quilltale TRPG Engine.
Handles passive/active/unique skill management, acquisition, and passive effect calculation.
Individual divergence: same magic word = different skill depending on personality.
"""
import random
import logging
from typing import Optional, Tuple
from src.world.state import Player, NPC, Skill, WorldState

logger = logging.getLogger(__name__)

ACQUISITION_SOURCES = [
    'levelup', 'event', 'npc_teach', 'kill_npc', 
    'awakening', 'episode_clear', 'item_effect', 'unknown'
]

class SkillSystem:
    @staticmethod
    def can_player_acquire(player: Player, skill: Skill, state: WorldState) -> Tuple[bool, str]:
        """Check if player can acquire a skill. Returns (can_acquire, reason_ko)."""
        if skill.id in player.skills:
            return False, f'이미 [{skill.name}]을(를) 보유하고 있습니다.'
        
        if skill.acquire_difficulty == 'legendary':
            # Legendary skills require specific conditions
            if skill.is_unique and skill.owner_npc_id:
                owner_alive = state.npcs.get(skill.owner_npc_id)
                if owner_alive and owner_alive.alive:
                    return False, f'[{skill.name}]의 원본 보유자가 아직 살아있어 이 고유 스킬을 습득할 수 없습니다.'
            if player.level < 10:
                return False, f'[{skill.name}]을(를) 습득하기엔 아직 역량이 부족합니다.'
        
        return True, ''
    
    @staticmethod
    def calculate_unique_skill_drop_chance(npc: NPC, player: Player) -> float:
        """Unique skill drop probability after defeating NPC. Based on luck + context."""
        base = 0.15  # 15% base
        luck_bonus = max(0, player.luck - 10) * 0.01
        # Named/boss NPCs with titles get reduced drop rate
        if npc.titles:
            base *= 0.7
        return min(0.9, base + luck_bonus)
    
    @staticmethod
    def roll_unique_skill_drop(npc: NPC, player: Player) -> Optional[str]:
        """Roll for unique skill drop from NPC. Returns skill_id or None."""
        if not npc.skills:
            return None
        unique_skills = [s for s in npc.skills if s]
        if not unique_skills:
            return None
        chance = SkillSystem.calculate_unique_skill_drop_chance(npc, player)
        if random.random() < chance:
            return random.choice(unique_skills)
        return None
    
    @staticmethod
    def acquire_skill(player: Player, skill_id: str, state: WorldState, source: str = 'unknown') -> Tuple[bool, str]:
        """Grant a skill to player. Returns (success, message_ko)."""
        if skill_id not in state.skills_db:
            return False, f'스킬 [{skill_id}]이(가) 이 세계에 존재하지 않습니다.'
        skill = state.skills_db[skill_id]
        can, reason = SkillSystem.can_player_acquire(player, skill, state)
        if not can:
            return False, reason
        player.skills.append(skill_id)
        source_ko = {
            'levelup': '레벨업', 'event': '이벤트', 'npc_teach': 'NPC 가르침',
            'kill_npc': 'NPC 처치', 'awakening': '각성', 'episode_clear': '에피소드 완료',
            'item_effect': '아이템 효과', 'unknown': '미상'
        }.get(source, source)
        return True, f'✨ 새 스킬 [{skill.name}] 획득! (원천: {source_ko})'
    
    @staticmethod
    def apply_passive_bonuses(player: Player, state: WorldState) -> dict:
        """Calculate total stat bonuses from all passive skills."""
        bonuses = {}
        for skill_id in player.skills:
            skill = state.skills_db.get(skill_id)
            if skill and skill.skill_type == 'passive':
                effect = skill.effect
                for stat, val in effect.get('stat_bonuses', {}).items():
                    bonuses[stat] = bonuses.get(stat, 0) + val
        return bonuses
    
    @staticmethod
    def diverge_skill_from_magic_word(player: Player, magic_word: str) -> dict:
        """
        Same magic word -> different skill based on player personality/stats.
        Returns suggested skill effect dict.
        """
        # Aggressive profile -> offensive application
        if player.strength > player.intelligence:
            return {'variant': 'offensive', 'damage_bonus': 1.3, 'description': '파괴적인 힘의 발현'}
        # Intelligent profile -> utility/control application  
        elif player.intelligence > player.strength:
            return {'variant': 'utility', 'control': True, 'description': '정밀한 마법적 제어'}
        else:
            return {'variant': 'balanced', 'description': '균형 잡힌 마법 발현'}
    
    @staticmethod
    def grant_title(player: Player, title_id: str, state: WorldState) -> Tuple[bool, str]:
        """Grant a title to player. Titles are unique - only one holder per world."""
        if title_id not in state.titles_db:
            return False, f'칭호 [{title_id}]이(가) 이 세계에 존재하지 않습니다.'
        title = state.titles_db[title_id]
        if title_id in player.titles:
            return False, f'이미 [{title.name}] 칭호를 보유하고 있습니다.'
        # Check uniqueness: no other NPC should hold it
        for npc in state.npcs.values():
            if title_id in npc.titles:
                return False, f'[{title.name}] 칭호는 이미 다른 자가 보유하고 있습니다.'
        player.titles.append(title_id)
        bonuses_str = ', '.join(f'{k}+{v}' for k, v in title.stat_bonuses.items())
        return True, f'🏆 새 칭호 [{title.name}] 획득! 능력치 보너스: {bonuses_str if bonuses_str else "없음"}'
