"""
Deterministic Hidden Boss & Elite Monster Encounter Engine for Quilltale TRPG.
Triggers elusive, high-risk gimmick boss encounters based on strict physical and environmental conditions:
1. Temporal & Scent: Midnight (23:00~04:00) + Low Hygiene (<=30 scent/blood) -> The Abyssal Stalker (심연의 도살자)
2. Extreme Weather & Geography: Blizzard/Sub-zero (<= -5°C) + Icy Mountain Pass -> Frost Wraith of the Fjord (빙식 협곡의 서리 망령)
3. Thunderstorm & Waterside: Downpour + Swamp/Water Crossing -> Copper-Scaled Thunder Catfish (동판 비늘의 벼락 메기)
4. Black Market & Contraband: Possessing Illicit Goods or Debt Default + Ruins/Alleys -> Slaughterhouse Hook Scale Merchant (도살장 갈고리의 저울상인)
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import logging

from src.world.state import WorldState, NPC, Item, Skill, CombatProfile, NPCPersonality, NPCNeeds, NPCVisualDetails
from src.world.geography import RoadType, RoadCondition

logger = logging.getLogger(__name__)


@dataclass
class HiddenBossSpec:
    id: str
    name: str
    tier: str = "boss"                     # "elite" | "boss" | "mythic"
    trigger_type: str = "environmental"
    # Trigger conditions
    min_hour: Optional[int] = None         # e.g., 23
    max_hour: Optional[int] = None         # e.g., 4 (midnight cross-over)
    weather_keywords: List[str] = field(default_factory=list)
    max_temperature_celsius: Optional[float] = None
    min_temperature_celsius: Optional[float] = None
    max_player_hygiene: Optional[int] = None
    required_road_types: List[RoadType] = field(default_factory=list)
    required_terrains: List[str] = field(default_factory=list)
    requires_contraband: bool = False
    requires_debt: bool = False

    # Boss Stats & Profile
    health: int = 150
    max_health: int = 150
    mana: int = 80
    max_mana: int = 80
    armor_class: int = 15
    strength: int = 16
    agility: int = 14
    intelligence: int = 14
    constitution: int = 16
    wisdom: int = 12
    perception: int = 16
    gold: int = 150
    job: str = "고대 이형체"
    description: str = ""
    weakness_exploit: str = ""
    appearance_narration: str = ""
    extractable_skill_id: str = ""
    extractable_skill_name: str = ""


# Pre-configured deterministic Hidden Boss Registry
HIDDEN_BOSS_REGISTRY: Dict[str, HiddenBossSpec] = {
    "hidden_abyssal_stalker": HiddenBossSpec(
        id="hidden_abyssal_stalker",
        name="심연을 걷는 도살자",
        tier="boss",
        trigger_type="midnight_blood_scent",
        min_hour=23,
        max_hour=4,
        max_player_hygiene=30,  # Extreme blood/dirt scent
        required_terrains=["forest", "plains", "swamp", "mountains", "urban"],
        health=140,
        max_health=140,
        mana=60,
        max_mana=60,
        armor_class=14,
        strength=18,
        agility=15,
        intelligence=10,
        constitution=16,
        perception=18,
        gold=120,
        job="피에 굶주린 심연 괴수",
        description="칠흑빛 가죽과 솟구친 뼈 가시를 지닌 이형의 포식자. 피비린내와 오염된 체취를 수 킬로미터 밖에서 맡고 추적해온다.",
        weakness_exploit="강렬한 빛(횃불, 섬광, 신성 화염)에 노출되면 망막이 타들어가며 2턴간 명중률과 회피율이 급감함.",
        appearance_narration="짙은 어둠 속, 바람을 타고 풍기는 당신의 땀과 핏자국 냄새를 맡고 [심연을 걷는 도살자]가 침묵 속에 모습을 드러냈습니다! 등 뒤의 가시가 곤두서며 붉은 안광이 번뜩입니다.",
        extractable_skill_id="skill_abyssal_rend",
        extractable_skill_name="【비기: 심연의 열상격】"
    ),
    "hidden_frost_wraith": HiddenBossSpec(
        id="hidden_frost_wraith",
        name="빙식 협곡의 서리 망령",
        tier="elite",
        trigger_type="subzero_mountain_pass",
        weather_keywords=["폭설", "눈보라", "대설"],
        max_temperature_celsius=0.0,
        required_road_types=[RoadType.MOUNTAIN_PASS],
        required_terrains=["mountains"],
        health=110,
        max_health=110,
        mana=100,
        max_mana=100,
        armor_class=13,
        strength=10,
        agility=16,
        intelligence=18,
        constitution=12,
        perception=14,
        gold=90,
        job="혹한의 빙결 원혼",
        description="얼어붙은 고갯길에서 조난당한 이들의 영혼이 혹한의 마나와 뒤엉켜 탄생한 푸른빛의 부유 망령.",
        weakness_exploit="화염 및 열기 피해에 극도로 취약(화염 피해 1.5배). 모닥불이나 횃불 근처에서는 형체가 녹아내리며 방어력 급락.",
        appearance_narration="살을 에는 눈보라 속에서 얼어붙은 산길 노면이 파랗게 발광하더니, 날카로운 비명과 함께 [빙식 협곡의 서리 망령]이 냉기 폭풍을 몰고 강림했습니다!",
        extractable_skill_id="skill_frost_shiver",
        extractable_skill_name="【비기: 극한의 빙결 룬】"
    ),
    "hidden_thunder_catfish": HiddenBossSpec(
        id="hidden_thunder_catfish",
        name="동판 비늘의 벼락 메기",
        tier="elite",
        trigger_type="downpour_swamp_waterside",
        weather_keywords=["폭우", "호우", "장대비", "뇌우"],
        required_road_types=[RoadType.SWAMP_TRAIL],
        required_terrains=["swamp", "coastal_port"],
        health=130,
        max_health=130,
        mana=70,
        max_mana=70,
        armor_class=14,
        strength=17,
        agility=12,
        intelligence=12,
        constitution=16,
        perception=15,
        gold=110,
        job="고압 통전성 수룡",
        description="청록색 구리 비늘로 덮여 있으며, 꼬리에 피뢰침 심봉을 지닌 채 폭우의 번개를 흡수하는 거대 수중 괴수.",
        weakness_exploit="꼬리의 피뢰침 접지를 타격/둔기 공격으로 파괴하면 체내 전압이 자폭 과부하(3턴간 행동불능 및 매턴 자해 피해)를 일으킴.",
        appearance_narration="폭우로 범람한 수로에서 지지직거리는 고압 스파크가 튀더니, 거대한 [동판 비늘의 벼락 메기]가 흙탕물을 가르며 솟구쳐 올랐습니다!",
        extractable_skill_id="skill_ground_discharge",
        extractable_skill_name="【비기: 강제 접지 요격】"
    ),
    "hidden_scale_merchant": HiddenBossSpec(
        id="hidden_scale_merchant",
        name="도살장 갈고리의 저울상인",
        tier="boss",
        trigger_type="illicit_contraband_debt",
        requires_contraband=True,
        required_terrains=["urban", "capital_metropolis", "subterranean"],
        health=160,
        max_health=160,
        mana=90,
        max_mana=90,
        armor_class=16,
        strength=17,
        agility=13,
        intelligence=16,
        constitution=18,
        perception=17,
        gold=250,
        job="인과율의 집행자",
        description="등뼈를 관통한 거대 황동 천칭과 양손의 녹슨 쇠갈고리로 부채와 밀수품의 인과를 저울질하는 악덕 상인의 원혼.",
        weakness_exploit="공격당할 때마다 저울 접시가 기우는데, 반대편 접시에 중량물을 던져 균형을 무너뜨리면 인과율 반사 스킬이 불발됨.",
        appearance_narration="그늘진 골목길 모퉁이에서 둔중한 황동 천칭의 삐걱거림과 쇠사슬 끄는 소리가 울려 퍼집니다. 밀수품의 냄새를 맡은 [도살장 갈고리의 저울상인]이 갈고리를 겨누며 나타났습니다!",
        extractable_skill_id="skill_karmic_retribution",
        extractable_skill_name="【비기: 등가 참수형】"
    )
}


class HiddenEncounterEngine:
    """Pure Python Deterministic Hidden Boss Encounter & Trigger Engine."""

    @classmethod
    def is_boss_defeated(cls, state: WorldState, boss_id: str) -> bool:
        """Checks if the hidden boss has already been encountered and killed."""
        # 1. Check if NPC exists in state and is dead
        if boss_id in state.npcs and not state.npcs[boss_id].alive:
            return True

        # 2. Check world_facts for defeat records
        for fact in state.world_facts:
            if boss_id in fact or (boss_id in HIDDEN_BOSS_REGISTRY and HIDDEN_BOSS_REGISTRY[boss_id].name in fact and "처치" in fact):
                return True

        return False

    @classmethod
    def has_contraband(cls, state: WorldState) -> bool:
        """Checks if player carries any restricted or illicit contraband in inventory."""
        for item_id in state.player.inventory:
            if item_id in state.items:
                item = state.items[item_id]
                props = getattr(item, "properties", {}) or {}
                if props.get("contraband_tier", 0) > 0 or props.get("is_contraband", False):
                    return True
                name = item.name.lower()
                if any(k in name for k in ["밀수", "금지", "마약", "암흑", "도물", "독주", "사기"]):
                    return True
        return False

    @classmethod
    def evaluate_encounter(
        cls,
        state: WorldState,
        action: str = "",
        is_movement: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates whether current environmental, temporal, physical, and behavioral conditions
        trigger a hidden boss or elite monster spawn.
        Returns encounter packet dict if triggered, otherwise None.
        """
        curr_loc = state.current_location()
        if not curr_loc:
            return None

        # If location already has a living hostile boss, do not trigger another one simultaneously
        for nid in curr_loc.npcs:
            if nid in state.npcs:
                n = state.npcs[nid]
                if n.alive and n.disposition == "hostile" and getattr(n, "tier", "") in ["boss", "elite"]:
                    return None

        current_hour = state.current_hour
        weather = getattr(state.environment, "weather", "맑음")
        temp = getattr(state.environment, "temperature_celsius", 20.0)
        hygiene = getattr(state.player, "hygiene_level", 100)
        terrain = getattr(curr_loc, "terrain", "plains")

        # Find road connection if moving or present
        current_road_type = None
        if hasattr(curr_loc, "roads") and curr_loc.roads:
            current_road_type = list(curr_loc.roads.values())[0].road_type

        has_illicit = cls.has_contraband(state)

        for boss_id, spec in HIDDEN_BOSS_REGISTRY.items():
            if cls.is_boss_defeated(state, boss_id):
                continue

            # If boss already spawned in this location and alive, return existing encounter
            if boss_id in curr_loc.npcs and boss_id in state.npcs and state.npcs[boss_id].alive:
                continue

            # 1. Hour check (supports midnight wrap-around: e.g. min 23, max 4)
            if spec.min_hour is not None and spec.max_hour is not None:
                if spec.min_hour > spec.max_hour:
                    if not (current_hour >= spec.min_hour or current_hour <= spec.max_hour):
                        continue
                else:
                    if not (spec.min_hour <= current_hour <= spec.max_hour):
                        continue

            # 2. Weather check
            if spec.weather_keywords:
                if not any(k in weather for k in spec.weather_keywords):
                    continue

            # 3. Temperature check
            if spec.max_temperature_celsius is not None and temp > spec.max_temperature_celsius:
                continue
            if spec.min_temperature_celsius is not None and temp < spec.min_temperature_celsius:
                continue

            # 4. Hygiene / Scent check
            if spec.max_player_hygiene is not None and hygiene > spec.max_player_hygiene:
                continue

            # 5. Road type check
            if spec.required_road_types and current_road_type:
                if current_road_type not in spec.required_road_types:
                    continue

            # 6. Terrain check
            if spec.required_terrains and terrain not in spec.required_terrains:
                continue

            # 7. Contraband check
            if spec.requires_contraband and not has_illicit:
                continue

            # --- ALL CONDITIONS MET! Spawn Hidden Boss ---
            spawned_npc = cls._spawn_hidden_boss_npc(state, spec, curr_loc.id)
            cls._register_boss_skills_and_items(state, spec)

            logger.info(f"⚡ [Hidden Boss Triggered] {spec.name} spawned at {curr_loc.name}")
            return {
                "triggered": True,
                "boss_id": spec.id,
                "boss_name": spec.name,
                "tier": spec.tier,
                "appearance_narration": spec.appearance_narration,
                "encounter_log": f"🚨 [히든 {spec.tier.upper()} 조우!] {spec.name}이(가) 특수 조건을 충족하여 출현했습니다!",
                "weakness": spec.weakness_exploit,
                "extractable_skill": spec.extractable_skill_name
            }

        return None

    @classmethod
    def _spawn_hidden_boss_npc(cls, state: WorldState, spec: HiddenBossSpec, loc_id: str) -> NPC:
        """Instantiates and places the hidden boss into WorldState.npcs and location."""
        npc = NPC(
            id=spec.id,
            name=spec.name,
            description=spec.description,
            location=loc_id,
            tier=spec.tier,
            job=spec.job,
            disposition="hostile",
            alive=True,
            health=spec.health,
            max_health=spec.max_health,
            mana=spec.mana,
            max_mana=spec.max_mana,
            armor_class=spec.armor_class,
            gold=spec.gold,
            strength=spec.strength,
            agility=spec.agility,
            intelligence=spec.intelligence,
            constitution=spec.constitution,
            wisdom=spec.wisdom,
            perception=spec.perception,
            stats_revealed=True,
            name_revealed=True,
            weakness=spec.weakness_exploit,
            combat_profile=CombatProfile(
                strengths="치명적인 특수 기믹과 강력한 광역 공격",
                weaknesses=spec.weakness_exploit,
                preferred_tactics="상대의 허점을 노린 일격필살"
            ),
            personality=NPCPersonality(aggression=90, courage=85, suspicion=70)
        )

        # Add boss skill to skills list
        if spec.extractable_skill_id:
            npc.skills.append(spec.extractable_skill_id)

        state.npcs[spec.id] = npc
        if loc_id in state.locations and spec.id not in state.locations[loc_id].npcs:
            state.locations[loc_id].npcs.append(spec.id)

        return npc

    @classmethod
    def _register_boss_skills_and_items(cls, state: WorldState, spec: HiddenBossSpec):
        """Registers the boss's extractable unique skill into state.skills_db."""
        if spec.extractable_skill_id and spec.extractable_skill_id not in state.skills_db:
            skill = Skill(
                id=spec.extractable_skill_id,
                name=spec.extractable_skill_name,
                category="martial_qi" if spec.id == "hidden_abyssal_stalker" else "arcane_magic",
                role_type="single_attack",
                tier="epic",
                is_unique=True,
                owner_npc_id=spec.id,
                resource_type="mana",
                resource_cost=25,
                cooldown_turns=3,
                base_value=22,
                scaling_stat="str" if spec.strength > spec.intelligence else "int",
                scaling_factor=1.8,
                element="암흑" if "심연" in spec.name else ("빙결" if "서리" in spec.name else ("전격" if "벼락" in spec.name else "물리")),
                armor_penetration=0.25,
                description=f"{spec.name}의 정수를 흡수하여 시전하는 강력한 고유 비기.",
                visual_fx_description=f"시전자의 손끝에서 {spec.name}의 형상이 일렁이며 파괴적인 기운을 방출합니다."
            )
            state.skills_db[spec.extractable_skill_id] = skill
