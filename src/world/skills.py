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
    def parse_skill_template(raw: dict) -> Skill:
        """Parse a 14-domain raw JSON dict into a canonical Skill object."""
        d1 = raw.get("1_기본식별_계통", {})
        d2 = raw.get("2_기술위계_합체기", {})
        d3 = raw.get("3_소모자원_대가", {})
        d4 = raw.get("4_시전방식_쿨다운", {})
        d5 = raw.get("5_명중_사거리_범위", {})
        d6 = raw.get("6_피해수치_물리연산", {})
        d7 = raw.get("7_처형_조건부폭딜", {})
        d8 = raw.get("8_위치이동_군중제어", {})
        d9 = raw.get("9_원소_환경_날씨연계", {})
        d10 = raw.get("10_치명타_자원흡수", {})
        d11 = raw.get("11_지속시간_스택중첩", {})
        d12 = raw.get("12_숙련도_경지", {})
        d13 = raw.get("13_소음도_사회적금기", {})
        d14 = raw.get("14_서사_연출", {})

        return Skill(
            id=raw.get("id", ""),
            name=raw.get("name", ""),
            # 1
            category=d1.get("category", "physical"),
            skill_type=d1.get("skill_type", "active"),
            role_type=d1.get("role_type", "single_attack"),
            tier=d1.get("tier", "common"),
            acquire_difficulty=d1.get("tier", "common"),
            is_unique=d1.get("is_unique", False),
            owner_npc_id=d1.get("owner_npc_id", ""),
            # 2
            rank_type=d2.get("rank_type", "normal"),
            joint_partner_id=d2.get("joint_partner_id", ""),
            joint_requirements=d2.get("joint_requirements", {}),
            # 3
            resource_type=d3.get("resource_type", "mana"),
            resource_cost=d3.get("resource_cost", 0),
            mana_cost=d3.get("resource_cost", 0) if d3.get("resource_type") == "mana" else 0,
            catalyst_required=d3.get("catalyst_required", ""),
            recoil_or_side_effect=d3.get("recoil_or_side_effect", ""),
            backfire_risk=d3.get("backfire_risk", 0.0),
            backfire_description=d3.get("backfire_description", ""),
            # 4
            cast_behavior=d4.get("cast_behavior", "instant"),
            cast_time_turns=d4.get("cast_time_turns", 0),
            cooldown_turns=d4.get("cooldown_turns", 0),
            current_cooldown=d4.get("current_cooldown", 0),
            required_weapon=d4.get("required_weapon", "무관"),
            required_stance=d4.get("required_stance", ""),
            # 5
            hit_type=d5.get("hit_type", "dice_roll"),
            target_type=d5.get("target_type", "single_enemy"),
            range=d5.get("range", "melee"),
            area_shape=d5.get("area_shape", "single"),
            area_radius_meters=d5.get("area_radius_meters", 0.0),
            # 6
            damage_delivery=d6.get("damage_delivery", "single_burst"),
            hit_count=d6.get("hit_count", 1),
            base_value=d6.get("base_value", 0),
            scaling_stat=d6.get("scaling_stat", "str"),
            scaling_factor=d6.get("scaling_factor", 1.0),
            element=d6.get("element", "물리"),
            armor_penetration=d6.get("armor_penetration", 0.0),
            # 7
            execution_condition=d7.get("execution_condition", {}),
            # 8
            displacement=d8.get("displacement", {}),
            inflicted_status=d8.get("inflicted_status", []),
            # 9
            synergy_tags=d9.get("synergy_tags", []),
            environmental_gimmick=d9.get("environmental_gimmick", ""),
            weather_terrain_synergy=d9.get("weather_terrain_synergy", {}),
            # 10
            crit_multiplier_bonus=d10.get("crit_multiplier_bonus", 0.0),
            guaranteed_crit_condition=d10.get("guaranteed_crit_condition", ""),
            lifesteal_pct=d10.get("lifesteal_pct", 0.0),
            mana_drain_pct=d10.get("mana_drain_pct", 0.0),
            # 11
            duration_turns=d11.get("duration_turns", 0),
            max_stacks=d11.get("max_stacks", 1),
            current_stacks=d11.get("current_stacks", 0),
            # 12
            mastery_level=d12.get("mastery_level", 1),
            mastery_exp=d12.get("mastery_exp", 0),
            max_mastery_level=d12.get("max_mastery_level", 4),
            # 13
            noise_level=d13.get("noise_level", "normal"),
            is_forbidden=d13.get("is_forbidden", False),
            taboo_reason=d13.get("taboo_reason", ""),
            # 14
            description=d14.get("description", ""),
            incantation_or_formula=d14.get("incantation_or_formula", ""),
            visual_fx_description=d14.get("visual_fx_description", ""),
            color=(
                raw.get("color") or d14.get("color") or
                {
                    "화염": "#ef4444", "빙결": "#38bdf8", "전격": "#eab308",
                    "산성": "#22c55e", "독": "#10b981", "신성": "#fbbf24",
                    "암흑": "#a855f7", "사령": "#9333ea", "비전": "#818cf8"
                }.get(d6.get("element", "물리")) or
                {
                    "martial_qi": "#f97316", "alchemy": "#14b8a6", "subterfuge": "#64748b",
                    "holy_miracle": "#fbbf24", "necromancy": "#a855f7", "curse_voodoo": "#d946ef",
                    "psionics": "#ec4899", "taming": "#84cc16"
                }.get(d1.get("category", "physical")) or "#94a3b8"
            )
        )

    @staticmethod
    def load_skill_templates(file_path: str = "data/templates/skill_templates.json") -> dict[str, Skill]:
        """Load and parse skill templates JSON into a dictionary of Skill objects."""
        import json
        from pathlib import Path
        
        path = Path(file_path)
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_list = json.load(f)
            skills_dict = {}
            for item in raw_list:
                skill = SkillSystem.parse_skill_template(item)
                if skill.id:
                    skills_dict[skill.id] = skill
            return skills_dict
        except Exception as e:
            logger.error(f"Failed to load skill templates from {file_path}: {e}")
            return {}

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

