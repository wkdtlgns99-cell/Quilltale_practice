"""
Universal Object Durability & Material Physics Engine for Quilltale TRPG.
Deterministic physical destruction, material categorization (12 major classes),
hardness/brittleness/flammability dynamics, debris fragmentation, container spilling,
improvised weapon utilization, and external LLM narrative generation for EVERY physical object
(chairs, desks, books, paper, glass, stones, trees, houses, metals, fabrics, and structures).
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import random
import logging

from src.world.state import WorldState, Item, Location

logger = logging.getLogger(__name__)

# ============================================================
# 12 Major Material Physical Profiles
# ============================================================
@dataclass
class MaterialSpec:
    """재질별 고유 물리 역학 스펙"""
    material_id: str
    name_ko: str
    description: str
    base_hardness: float                  # 장갑치 (피해 감쇠치)
    base_durability: float                # 기본 내구도
    flammability: float                   # 화재 인화율 (0.0 = 불연성, 1.0 = 표준, 3.5 = 초인화)
    brittleness: float                    # 취성/충격 파쇄율 (타격 피해 배율)
    break_sound_db: int                   # 파손 시 방출 소음 데시벨
    water_sensitive: bool = False         # 물/습기에 침식/훼손되는지
    sharp_hazard: bool = False            # 파괴 시 밟으면 출혈을 일으키는 날카로운 파편 장판을 형성하는지
    collapse_hazard: bool = False         # 대형 붕괴로 주변 인원에게 낙하 매몰 피해를 주는지
    debris_specs: List[Dict[str, Any]] = field(default_factory=list) # 파괴 시 스폰될 잔해 템플릿
    traits: List[str] = field(default_factory=list)


MATERIAL_REGISTRY: Dict[str, MaterialSpec] = {
    "paper": MaterialSpec(
        material_id="paper",
        name_ko="종이/양피지",
        description="식물 섬유나 가죽을 얇게 뜬 문서 재질. 화염에 즉각 전소되며 물에 닿으면 먹물이 번지고 찢어진다.",
        base_hardness=0.0,
        base_durability=10.0,
        flammability=3.5,
        brittleness=0.2,
        break_sound_db=10,
        water_sensitive=True,
        debris_specs=[
            {"id_suffix": "_ashes", "name": "잿더미", "desc": "불타서 검게 그을린 종이의 타고 남은 재.", "type": "misc", "weight": 0.05, "damage": 0, "traits": ["ashes", "ruined"]},
            {"id_suffix": "_scraps", "name": "찢어진 종이 부스러기", "desc": "갈기갈기 찢겨나간 양피지 조각.", "type": "misc", "weight": 0.05, "damage": 0, "traits": ["scrap_paper", "torn"]}
        ],
        traits=["mat:paper", "flammable", "water_sensitive", "fragile"]
    ),
    "glass": MaterialSpec(
        material_id="glass",
        name_ko="유리/도자기/수정",
        description="투명하거나 광택을 띤 취성 물질. 충격과 낙하에 극도로 취약하며 깨질 때 날카로운 파편과 굉음을 발생시킨다.",
        base_hardness=1.5,
        base_durability=15.0,
        flammability=0.0,
        brittleness=3.5,
        break_sound_db=65,
        sharp_hazard=True,
        debris_specs=[
            {"id_suffix": "_shards", "name": "날카로운 유리 파편", "desc": "바닥에 흩뿌려진 서슬 퍼런 유리 파편. 즉석 단검으로 쓰거나 밟으면 발바닥에 자상을 입는다.", "type": "weapon", "weight": 0.4, "damage": 3, "traits": ["glass_shards", "sharp_hazard", "improvised_dagger"]}
        ],
        traits=["mat:glass", "brittle", "sharp_hazard", "loud_break"]
    ),
    "cloth": MaterialSpec(
        material_id="cloth",
        name_ko="천/비단/직물",
        description="실과 직조물로 짜인 유연한 섬유 재질. 참격에 쉽게 찢어지며 화재 확산의 매개체가 된다.",
        base_hardness=0.5,
        base_durability=25.0,
        flammability=2.2,
        brittleness=0.1,
        break_sound_db=8,
        debris_specs=[
            {"id_suffix": "_rags", "name": "찢어진 헝겊 조각", "desc": "갈기갈기 찢어진 천 조각. 지혈용 붕대나 불쏘시개로 재활용할 수 있다.", "type": "misc", "weight": 0.2, "damage": 0, "traits": ["cloth_rags", "tinder"]}
        ],
        traits=["mat:cloth", "flexible", "flammable", "cuttable"]
    ),
    "leather": MaterialSpec(
        material_id="leather",
        name_ko="가죽/모피",
        description="무두질된 동물의 질긴 가죽. 방수성과 유연성이 뛰어나며 화염에 서서히 그을린다.",
        base_hardness=4.0,
        base_durability=60.0,
        flammability=0.8,
        brittleness=0.2,
        break_sound_db=12,
        debris_specs=[
            {"id_suffix": "_leather_scraps", "name": "질긴 가죽 조각", "desc": "찢어진 장비에서 떨어진 무두질 가죽 조각. 끈이나 덧댐 수리에 유용하다.", "type": "misc", "weight": 0.4, "damage": 0, "traits": ["leather_scrap", "crafting_material"]}
        ],
        traits=["mat:leather", "tough", "water_resistant"]
    ),
    "wood": MaterialSpec(
        material_id="wood",
        name_ko="목재/가구/목책",
        description="의자, 책상, 침대, 문, 통나무 등 전천후 목질 재질. 둔기나 도끼로 부수면 각목과 땔감 장작으로 분해된다.",
        base_hardness=6.0,
        base_durability=80.0,
        flammability=1.6,
        brittleness=1.0,
        break_sound_db=45,
        debris_specs=[
            {"id_suffix": "_club", "name": "깨진 각목", "desc": "가구가 부서지며 떨어져 나온 단단한 각목. 손에 쥐고 즉석 둔기로 휘두르기 좋다.", "type": "weapon", "weight": 2.0, "damage": 4, "traits": ["improvised_club", "wooden_weapon", "blunt"]},
            {"id_suffix": "_firewood", "name": "땔감용 나무 장작", "desc": "쪼개진 목재 파편. 모닥불의 훌륭한 땔감이 된다.", "type": "misc", "weight": 1.5, "damage": 1, "traits": ["firewood", "fuel"]}
        ],
        traits=["mat:wood", "splinterable", "combustible", "furniture_base"]
    ),
    "stone": MaterialSpec(
        material_id="stone",
        name_ko="석재/돌/벽돌",
        description="자연 암반, 석재 기둥, 돌멩이 등 단단한 무기질. 불에 타지 않으며 분쇄 시 날카로운 투척석과 자갈을 남긴다.",
        base_hardness=18.0,
        base_durability=250.0,
        flammability=0.0,
        brittleness=1.5,
        break_sound_db=52,
        debris_specs=[
            {"id_suffix": "_stone", "name": "투척용 모난 돌멩이", "desc": "손에 쥐고 던져서 적의 이마를 깨뜨리기 좋은 날카로운 석재 조각.", "type": "weapon", "weight": 1.0, "damage": 3, "traits": ["throwing_stone", "projectile"]},
            {"id_suffix": "_rubble", "name": "석재 파편과 자갈", "desc": "부서진 바위에서 쏟아진 돌무더기.", "type": "misc", "weight": 3.0, "damage": 0, "traits": ["rubble", "construction_debris"]}
        ],
        traits=["mat:stone", "heavy", "fireproof", "high_hardness"]
    ),
    "metal": MaterialSpec(
        material_id="metal",
        name_ko="철재/강철/청동",
        description="검, 갑옷, 주방 냄비, 쇠사슬, 자물쇠 등 단단한 금속. 경도가 매우 높으며 파괴 시 찌그러진 고철 덩어리가 된다.",
        base_hardness=25.0,
        base_durability=400.0,
        flammability=0.0,
        brittleness=0.4,
        break_sound_db=62,
        debris_specs=[
            {"id_suffix": "_scrap", "name": "찌그러진 고철 덩어리", "desc": "부서진 금속 물체의 잔해. 대장간에서 녹여 재련할 수 있다.", "type": "misc", "weight": 3.5, "damage": 2, "traits": ["scrap_metal", "smelting_material"]}
        ],
        traits=["mat:metal", "conductive", "high_durability", "acid_weak"]
    ),
    "precious_metal": MaterialSpec(
        material_id="precious_metal",
        name_ko="귀금속/보석/미스릴",
        description="금, 은, 백금, 보석, 미스릴 등 가치 있고 부식되지 않는 희귀 재질. 파손되어도 고유 환금 가치를 유지한다.",
        base_hardness=14.0,
        base_durability=250.0,
        flammability=0.0,
        brittleness=0.8,
        break_sound_db=35,
        debris_specs=[
            {"id_suffix": "_precious_scrap", "name": "손상된 귀금속 파편", "desc": "금이 박힌 깨진 장신구 조각. 상인에게 상당한 액수로 매각할 수 있다.", "type": "misc", "weight": 0.3, "damage": 0, "traits": ["precious_scrap", "valuable"]}
        ],
        traits=["mat:precious_metal", "valuable", "non_corrosive"]
    ),
    "clay": MaterialSpec(
        material_id="clay",
        name_ko="점토/벽돌/도기",
        description="구운 점토, 토기 그릇, 화덕, 붉은 벽돌. 충격에 깨지며 붉은 흙먼지와 날카로운 도기 조각을 남긴다.",
        base_hardness=7.0,
        base_durability=50.0,
        flammability=0.0,
        brittleness=2.8,
        break_sound_db=38,
        debris_specs=[
            {"id_suffix": "_pottery_shards", "name": "깨진 점토 도기 파편", "desc": "붉은 찰흙을 구워 만든 도기의 조각.", "type": "misc", "weight": 0.7, "damage": 1, "traits": ["clay_shards"]}
        ],
        traits=["mat:clay", "earthen", "brittle"]
    ),
    "flesh": MaterialSpec(
        material_id="flesh",
        name_ko="생체/고기/유기물",
        description="동물의 생고기, 빵, 과일, 시체 등 유기 생체 조직. 경도가 거의 없으며 썩거나 불에 탄다.",
        base_hardness=1.0,
        base_durability=35.0,
        flammability=1.2,
        brittleness=0.1,
        break_sound_db=14,
        debris_specs=[
            {"id_suffix": "_remains", "name": "짓이겨진 고기 찌꺼기", "desc": "형체를 알아볼 수 없게 뭉개진 유기 잔해.", "type": "misc", "weight": 0.8, "damage": 0, "traits": ["decaying_matter", "filth"]}
        ],
        traits=["mat:flesh", "organic", "perishable", "soft"]
    ),
    "structure_wood": MaterialSpec(
        material_id="structure_wood",
        name_ko="목조 가옥/오두막/마구간",
        description="목조 기둥과 판자로 지어진 대형 거주 및 방어 시설. 화재 시 통째로 전소되며 붕괴 시 내부 인원을 덮친다.",
        base_hardness=14.0,
        base_durability=1200.0,
        flammability=2.2,
        brittleness=1.0,
        break_sound_db=78,
        collapse_hazard=True,
        debris_specs=[
            {"id_suffix": "_ruins", "name": "무너진 목조 폐허 잔해", "desc": "불타 무너져 내린 목조 건축물의 시커먼 대들보와 판자더미.", "type": "structure", "weight": 60.0, "damage": 0, "traits": ["wooden_ruins", "hazard"]}
        ],
        traits=["mat:structure_wood", "large_structure", "collapse_danger", "burnable"]
    ),
    "structure_stone": MaterialSpec(
        material_id="structure_stone",
        name_ko="석조 건물/성벽/망루/석조 가옥",
        description="단단한 화강암과 회반죽으로 축조된 거대 건축물. 일반적인 손질로는 흠집조차 나지 않으나 공성 병기에 무너질 수 있다.",
        base_hardness=32.0,
        base_durability=3500.0,
        flammability=0.0,
        brittleness=1.2,
        break_sound_db=88,
        collapse_hazard=True,
        debris_specs=[
            {"id_suffix": "_rubble_ruins", "name": "석조 붕괴 잔해", "desc": "거대한 석벽과 기둥이 붕괴하여 길을 가로막은 석재 더미.", "type": "structure", "weight": 120.0, "damage": 0, "traits": ["stone_ruins", "obstacle"]}
        ],
        traits=["mat:structure_stone", "massive_structure", "fireproof", "siege_target"]
    )
}


# ============================================================
# Object Interaction Results & Data Models
# ============================================================
@dataclass
class ObjectInteractionResult:
    """사물과의 물리적 상호작용 결과 모델 (DoD & 규칙 6 준수)"""
    target_item_id: str
    target_name: str
    material: str
    initial_durability: float
    raw_damage: float
    effective_damage: float
    remaining_durability: float
    is_destroyed: bool
    status_transition: str                  # "intact", "damaged", "shattered", "incinerated", "collapsed"
    sound_db: int
    debris_spawned: List[Item] = field(default_factory=list)
    spilled_items: List[str] = field(default_factory=list)
    narrative_log: str = ""
    traits: List[str] = field(default_factory=list)


# ============================================================
# Master Universal Object Physics Engine
# ============================================================
class UniversalObjectPhysicsEngine:
    """
    Quilltale TRPG 만물 사물 내구도 & 물리 파괴 엔진.
    게임 내 모든 사물(의자, 책상, 책, 종이, 돌, 나무, 집, 유리병 등)의 재질 태그를 판정하고,
    타격/방화/파쇄 시 결정론적 내구도 삭감과 잔해(파편, 각목, 잿더미) 생성을 전담한다.
    """

    @classmethod
    def resolve_material(cls, item: Item) -> str:
        """
        사물의 재질을 결정론적으로 판별한다.
        1. item.material 명시 확인
        2. item.traits 내 'mat:' 태그 확인
        3. 이름, 설명, 분류 키워드 지능형 휴리스틱 매핑
        """
        # A. traits 우선 검사
        for t in getattr(item, "traits", []):
            if t.startswith("mat:"):
                mat_key = t.split("mat:", 1)[1]
                if mat_key in MATERIAL_REGISTRY:
                    return mat_key

        # B. 명시된 material 필드 검사
        explicit_mat = getattr(item, "material", "wood")
        if explicit_mat in MATERIAL_REGISTRY and explicit_mat != "wood":
            return explicit_mat

        # C. 키워드 기반 스마트 추론 (이름, 분류, 설명)
        name_l = (item.name or "").lower()
        desc_l = (item.description or "").lower()
        type_l = (getattr(item, "item_type", "") or "").lower()
        combined = f"{name_l} {desc_l} {type_l}"

        # 1. 문서/서적류
        if any(kw in combined for kw in ["종이", "양피지", "서적", "문서", "편지", "지도", "스크롤", "계약서", "전단", "벽보", "일기", "paper", "book", "scroll", "document"]):
            return "paper"

        # 2. 유리/도자기류
        if any(kw in combined for kw in ["유리", "도자기", "포션", "물약", "플라스크", "유리병", "창문", "거울", "찻잔", "수정", "크리스탈", "glass", "potion", "flask", "mirror"]):
            return "glass"

        # 3. 목재/가구류 (우선 매칭: 의자, 책상, 침대 등)
        if any(kw in combined for kw in ["의자", "책상", "침대", "가구", "목재", "원목", "참나무", "자작나무", "단풍나무", "통나무", "장작", "궤짝", "문짝", "나무통", "수레", "wood", "timber", "furniture", "chair", "desk", "table"]):
            return "wood"

        # 4. 건축/구조물류
        if any(kw in combined for kw in ["석조 건물", "성채", "석조 가옥", "석벽", "성벽", "망루", "stone_structure", "citadel", "fortress"]):
            return "structure_stone"
        if any(kw in combined for kw in ["오두막", "목조", "판자집", "마구간", "초소", "창고", "structure", "shack", "cabin", "stable"]):
            return "structure_wood"

        # 5. 직물/의복류
        if any(kw in combined for kw in ["직물", "비단", "천조각", "헝겊", "원단", "양탄자", "커튼", "로브", "망토", "침구", "이불", "붕대", "의복", "cloth", "fabric", "robe", "curtain"]):
            return "cloth"

        # 6. 가죽류
        if any(kw in combined for kw in ["가죽", "모피", "배낭", "자루", "마구", "부츠", "신발", "leather", "fur", "pouch", "bag"]):
            return "leather"

        # 7. 석재/암반류
        if any(kw in combined for kw in ["돌멩이", "자갈", "바위", "석벽", "비석", "석재", "벽돌", "암반", "돌기둥", "대리석", "stone", "rock", "boulder", "pebble"]):
            return "stone"

        # 8. 귀금속/보석류 (주의: '은'/'금' 1글자 단독 매칭 금지)
        if any(kw in combined for kw in ["황금", "순금", "금화", "금제", "금도금", "순은", "은화", "은제", "은도금", "은빛", "미스릴", "백금", "아다만티움", "보석", "반지", "목걸이", "귀걸이", "골드", "gold", "silver", "mithril", "jewel", "gem"]):
            return "precious_metal"

        # 9. 일반 금속류
        if any(kw in combined for kw in ["강철", "무쇠", "청동", "황동", "구리", "철제", "쇠사슬", "자물쇠", "철창", "냄비", "못", "식기", "단검", "장검", "도끼", "갑옷", "투구", "metal", "steel", "iron", "chain", "lock"]):
            return "metal"

        # 10. 점토/도기류
        if any(kw in combined for kw in ["찰흙", "점토", "토기", "화덕", "clay", "brick", "earthen"]):
            return "clay"

        # 11. 생체/음식/고기류
        if any(kw in combined for kw in ["생고기", "고기", "구이", "빵", "과일", "시체", "사체", "유기체", "meat", "bread", "food", "corpse", "flesh"]):
            return "flesh"

        # 기본값: 목재 (나무, 가구 등)
        return "wood"

    @classmethod
    def get_material_spec(cls, material_id: str) -> MaterialSpec:
        """재질 스펙 객체를 반환한다."""
        return MATERIAL_REGISTRY.get(material_id, MATERIAL_REGISTRY["wood"])

    @classmethod
    def damage_object(
        cls,
        state: WorldState,
        item_or_id: Any,
        raw_damage: float,
        damage_type: str = "blunt",
        is_fire: bool = False,
        is_acid: bool = False,
        attacker_name: str = "플레이어"
    ) -> ObjectInteractionResult:
        """
        세상의 모든 사물에 대한 물리적/화공적 타격 및 내구도 삭감, 파괴 처리.
        """
        # 아이템 객체 확보
        if isinstance(item_or_id, str):
            item = state.items.get(item_or_id)
            if not item:
                # 더미 객체 생성 후 반환
                return ObjectInteractionResult(
                    target_item_id=item_or_id,
                    target_name="알 수 없는 사물",
                    material="wood",
                    initial_durability=0.0,
                    raw_damage=raw_damage,
                    effective_damage=0.0,
                    remaining_durability=0.0,
                    is_destroyed=True,
                    status_transition="destroyed",
                    sound_db=0,
                    narrative_log="대상을 찾을 수 없습니다."
                )
        else:
            item = item_or_id

        mat_id = cls.resolve_material(item)
        spec = cls.get_material_spec(mat_id)
        item.material = mat_id

        # 경도(Hardness) 결정: 아이템 자체 경도가 있으면 우선, 없으면 재질 기본값
        hardness = getattr(item, "hardness", 0.0)
        if hardness <= 0.0:
            hardness = spec.base_hardness

        initial_dur = float(item.durability)

        # 유효 피해 계산
        eff_damage = max(1.0, raw_damage - hardness)

        # A. 화공(Fire) 배율
        if is_fire:
            flam_mult = getattr(item, "flammability", 1.0) * spec.flammability
            eff_damage *= flam_mult
            if flam_mult == 0.0:
                eff_damage = 0.0  # 불연성

        # B. 산성(Acid) 부식 배율 (금속/암석 취약)
        if is_acid:
            if mat_id in ["metal", "stone"]:
                eff_damage *= 2.5
            elif mat_id in ["glass", "precious_metal"]:
                eff_damage *= 0.2  # 내산성 유리/귀금속

        # C. 타격 유형(Damage Type) 상성
        if damage_type == "blunt" and spec.brittleness > 1.5:
            # 둔기에 의한 취성 분쇄 (유리, 도자기, 석재)
            eff_damage *= spec.brittleness
        elif damage_type == "slash" and mat_id in ["cloth", "paper", "flesh"]:
            # 참격에 찢어짐
            eff_damage *= 1.6
        elif damage_type == "pierce" and mat_id in ["cloth", "leather", "paper"]:
            # 관통
            eff_damage *= 1.2

        actual_lost = min(item.durability, eff_damage)
        item.durability = max(0, int(item.durability - actual_lost))

        is_dest = (item.durability <= 0)
        item.is_destroyed = is_dest

        # 사물 상태 전이 결정
        if item.durability == 0:
            if is_fire and spec.flammability > 0:
                status_transition = "incinerated"  # 전소
            elif spec.brittleness > 2.0:
                status_transition = "shattered"    # 산산조각
            elif spec.collapse_hazard:
                status_transition = "collapsed"    # 붕괴
            else:
                status_transition = "destroyed"    # 파괴
        elif item.durability < (item.max_durability * 0.5):
            status_transition = "damaged"          # 균열/손상
        else:
            status_transition = "intact"

        debris_list: List[Item] = []
        spilled_list: List[str] = []
        log_parts = []

        # 사물이 완전히 파괴되었을 때의 후속 처리
        if is_dest:
            sound_db = spec.break_sound_db

            # 1. 문서/서적 전소 시 내용 소멸
            if mat_id == "paper" and status_transition == "incinerated":
                item.document_text = ""
                log_parts.append(f"🔥 [{item.name}]이(가) 불길에 휩싸여 검은 잿더미로 타버렸습니다. (기록 영구 소멸)")
            elif mat_id == "glass":
                log_parts.append(f"💥 [{item.name}]이(가) 산산조각 깨지며 사방으로 날카로운 유리 파편이 튀었습니다! (소음 {sound_db}dB)")
            elif mat_id == "wood":
                log_parts.append(f"🪵 [{item.name}]이(가) 굉음과 함께 박살 나며 각목과 나무 장작으로 부서졌습니다! (소음 {sound_db}dB)")
            elif mat_id in ["structure_wood", "structure_stone"]:
                log_parts.append(f"🏚️🚨 [{item.name}]의 기둥과 벽이 무너지며 자욱한 분진과 함께 완전히 붕괴했습니다! (소음 {sound_db}dB)")
            else:
                log_parts.append(f"⚡ [{item.name}]이(가) 내구도를 다해 완전히 파괴되었습니다.")

            # 2. 잔해(Debris) 아이템 스폰 (바닥에 배치)
            loc_id = item.location
            for d_spec in spec.debris_specs:
                d_id = f"debris_{item.id}{d_spec['id_suffix']}_{random.randint(100, 999)}"
                d_item = Item(
                    id=d_id,
                    name=d_spec["name"],
                    description=d_spec["desc"],
                    location=loc_id,
                    item_type=d_spec["type"],
                    weight=d_spec["weight"],
                    damage=d_spec.get("damage", 0),
                    durability=50,
                    max_durability=50,
                    can_wield_as_weapon=(d_spec["type"] == "weapon"),
                    improvised_damage=d_spec.get("damage", 2),
                    traits=list(d_spec.get("traits", [])) + [f"source_{item.id}", "debris"]
                )
                state.items[d_id] = d_item
                debris_list.append(d_item)

                # 현재 장소의 바닥 아이템 목록에 등록
                if loc_id in state.locations:
                    if d_id not in state.locations[loc_id].items:
                        state.locations[loc_id].items.append(d_id)

            # 3. 보관함(상자, 서랍, 옷장) 내부 수납물 바닥에 쏟아짐
            stored = getattr(item, "stored_items", [])
            if stored and loc_id in state.locations:
                for s_id in stored:
                    if s_id in state.items:
                        state.items[s_id].location = loc_id
                        if s_id not in state.locations[loc_id].items:
                            state.locations[loc_id].items.append(s_id)
                        spilled_list.append(state.items[s_id].name)
                item.stored_items = []
                log_parts.append(f"📦 [수납물 유출] 파괴된 [{item.name}] 내부에서 [{', '.join(spilled_list)}]이(가) 바닥으로 쏟아져 나왔습니다!")

            # 4. 파괴된 원본 사물 위치 정리 (인벤토리 또는 바닥에서 제거/폐허 표기)
            item.traits.append("destroyed_object")
            if loc_id in state.locations and item.id in state.locations[loc_id].items:
                state.locations[loc_id].items.remove(item.id)
            if item.id in state.player.inventory:
                state.player.inventory.remove(item.id)

        else:
            sound_db = int(spec.break_sound_db * 0.4)
            log_parts.append(f"🔨 [{attacker_name}]의 공격으로 [{item.name}]이(가) 피해 {actual_lost:.1f}를 입었습니다. (잔여 내구도: {item.durability}/{item.max_durability})")
            if status_transition == "damaged":
                log_parts.append(f"⚠️ [{item.name}]의 표면에 굵은 균열이 가며 삐걱거립니다!")

        narrative = " ".join(log_parts)

        return ObjectInteractionResult(
            target_item_id=item.id,
            target_name=item.name,
            material=mat_id,
            initial_durability=initial_dur,
            raw_damage=raw_damage,
            effective_damage=actual_lost,
            remaining_durability=float(item.durability),
            is_destroyed=is_dest,
            status_transition=status_transition,
            sound_db=sound_db,
            debris_spawned=debris_list,
            spilled_items=spilled_list,
            narrative_log=narrative,
            traits=list(item.traits)
        )

    @classmethod
    def ignite_object(cls, state: WorldState, item_or_id: Any, fire_intensity: float = 1.0) -> ObjectInteractionResult:
        """
        사물에 불을 지른다 (방화).
        """
        raw_fire_damage = 30.0 * fire_intensity
        return cls.damage_object(
            state=state,
            item_or_id=item_or_id,
            raw_damage=raw_fire_damage,
            damage_type="fire",
            is_fire=True,
            is_acid=False,
            attacker_name="화염"
        )

    @classmethod
    def improvise_weapon_stats(cls, item: Item) -> Dict[str, Any]:
        """
        의자, 촛대, 부러진 각목, 돌멩이 등 임의의 사물을 즉석 무기로 사용할 때의 전투 스탯 산출.
        """
        mat_id = cls.resolve_material(item)
        spec = cls.get_material_spec(mat_id)

        base_dmg = getattr(item, "improvised_damage", 2)
        weight = getattr(item, "weight", 1.0)

        # 무게 및 재질 경도 반영 공격력
        calc_dmg = base_dmg + int(weight * 0.8) + int(spec.base_hardness * 0.3)
        calc_dmg = max(1, min(25, calc_dmg))

        # 저지력 (Poise / Stagger)
        stagger = weight * 1.5 + (4.0 if mat_id in ["stone", "metal", "wood"] else 1.0)

        # 타격당 내구도 소모량 (돌/금속은 적게 소모, 유리/도기는 일격 파쇄)
        dur_loss = 2
        if mat_id in ["glass", "clay"]:
            dur_loss = 20  # 한 번 치면 바로 박살
        elif mat_id in ["paper", "cloth"]:
            dur_loss = 10
        elif mat_id in ["stone", "metal"]:
            dur_loss = 1

        return {
            "item_id": item.id,
            "item_name": item.name,
            "material": mat_id,
            "damage": calc_dmg,
            "stagger_power": round(stagger, 1),
            "durability_loss_per_hit": dur_loss,
            "sound_on_hit_db": spec.break_sound_db,
            "traits": ["improvised_weapon", f"mat:{mat_id}"]
        }

    @classmethod
    def repair_object(
        cls,
        state: WorldState,
        item_id: str,
        tool_item: Optional[Item] = None,
        repair_materials: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """
        손상된 사물을 적합한 도구와 재료로 수리한다.
        """
        item = state.items.get(item_id)
        if not item:
            return False, "수리할 사물을 찾을 수 없습니다."

        if item.is_destroyed:
            return False, f"[{item.name}]은(는) 이미 완전히 파괴되어 잔해만 남아있어 일반 수리가 불가능합니다."

        if item.durability >= item.max_durability:
            return False, f"[{item.name}]은(는) 이미 완벽한 상태입니다."

        mat_id = cls.resolve_material(item)
        repair_amount = int(item.max_durability * 0.5)
        item.durability = min(item.max_durability, item.durability + repair_amount)

        tool_name = tool_item.name if tool_item else "간이 도구"
        return True, f"🛠️ [{tool_name}]을(를) 사용하여 [{item.name}]을(를) 수리했습니다! (내구도: {item.durability}/{item.max_durability})"

    @classmethod
    def generate_external_llm_prompt(cls, result: ObjectInteractionResult) -> str:
        """
        규칙 8 준수: 외부 대형 LLM(GPT/Claude) 연동을 위한 사물 물리 파괴 서사 묘사 프롬프트 생성.
        """
        prompt = f"""[시스템 컨텍스트: Quilltale TRPG 만물 물리 파괴 시뮬레이션 결과]
당신은 현장감과 촉각적 디테일이 극대화된 물리 엔진 연출을 담당하는 마스터 스토리텔러(GM)입니다.
아래의 결정론적 파이썬 물리 연산 결과를 바탕으로, 사물이 파괴되거나 손상되는 순간의 시각, 청각(소음 dB), 파편 비산의 역학을 1~2문장의 강렬한 서사로 묘사하십시오.

### 1. 사물 물리 상태
- 대상 사물: [{result.target_name}] (재질: {result.material})
- 피해량: {result.effective_damage:.1f} (잔여 내구도: {result.remaining_durability:.1f})
- 상태 전이: [{result.status_transition}]
- 발생 소음도: {result.sound_db} dB
- 생성된 파편/잔해: {", ".join(d.name for d in result.debris_spawned) if result.debris_spawned else "없음"}
- 쏟아진 내용물: {", ".join(result.spilled_items) if result.spilled_items else "없음"}

### 2. 서사 작성 지침
1. 결정론적 결과(잔여 내구도, 파괴 여부, 쏟아진 아이템)를 정확히 반영하십시오.
2. 유리면 찢어지는 굉음과 날카로운 파편, 종이면 잿더미, 목재면 각목과 톱밥의 냄새를 오감으로 묘사하십시오.
3. 소음이 50dB 이상일 경우 주변의 시선이나 경비병의 주의를 끌 수 있는 긴장감을 함께 서술하십시오.
"""
        return prompt
