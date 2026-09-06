"""
Deterministic Monster Part Breaking & Field Harvesting/Carving Engine for Quilltale TRPG.
Features:
1. Realistic monster anatomical parts (MonsterPart) with hitzone damage multipliers (slash, blunt, shot).
2. Tactical part break effects: breaking parts staggers the monster and disrupts combat abilities.
3. Physical tail severing: severing with slashing attacks drops the severed limb directly onto the battlefield floor.
4. Field butchering & carving without arbitrary carve counts or mobile-style gacha percentages.
5. Broken part ruin penalty: damaging/shattering parts incurs a ruin chance resulting in damaged scrap,
   whereas cleanly subduing monsters preserves parts for 100% guaranteed pristine material yields.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import random
import logging

from src.world.state import WorldState, Item, Player, NPC
from src.world.enchant_engine import EnchantEngine

logger = logging.getLogger(__name__)


@dataclass
class MonsterPart:
    part_id: str                                        # 고유 부위 ID (예: "lightning_rod_tail", "head_horn")
    name_ko: str                                        # 부위 명칭 (예: "피뢰침 꼬리", "통전 뇌각")
    max_hp: int                                         # 부위 내구도/파괴 임계치 (Part HP)
    current_hp: int                                     # 현재 남은 부위 체력
    is_broken: bool = False                             # 파괴 여부
    is_severed: bool = False                            # 물리적 절단 여부 (꼬리 등)
    severable: bool = False                             # 절단 가능 여부 (참격 데미지로만 절단)
    hitzone_slash: float = 1.0                          # 참격 육질 배율 (0.2 ~ 1.5)
    hitzone_blunt: float = 1.0                          # 타격/둔기 육질 배율 (0.2 ~ 1.5)
    hitzone_shot: float = 1.0                           # 사격/관통 육질 배율 (0.2 ~ 1.5)
    material_item_id: str = ""                          # 온전할 때 수확되는 최상급 소재 ID
    material_name_ko: str = ""                          # 온전한 소재 한글명 (예: "【통전성 뇌각】")
    material_description_ko: str = ""                   # 온전한 소재 설명
    ruined_item_id: str = ""                            # 파괴되어 손상되었을 때의 저급 잔해 ID
    ruined_name_ko: str = ""                            # 손상된 잔해 한글명 (예: "부서진 뇌각 파편")
    ruined_description_ko: str = ""                     # 손상된 잔해 설명
    ruin_chance_if_broken: float = 0.50                 # 부위 파괴된 상태에서 갈무리 시 손상 잔해로 열화될 확률 (50%)
    break_effect_ko: str = ""                           # 부위 파괴 시 몬스터에게 발생하는 약화 기믹
    traits: List[str] = field(default_factory=lambda: ["몬스터 신체 부위", "부위 파괴 가능"])

    def to_dict(self) -> dict:
        return {
            "part_id": self.part_id,
            "name_ko": self.name_ko,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "is_broken": self.is_broken,
            "is_severed": self.is_severed,
            "severable": self.severable,
            "hitzone_slash": self.hitzone_slash,
            "hitzone_blunt": self.hitzone_blunt,
            "hitzone_shot": self.hitzone_shot,
            "material_item_id": self.material_item_id,
            "material_name_ko": self.material_name_ko,
            "material_description_ko": self.material_description_ko,
            "ruined_item_id": self.ruined_item_id,
            "ruined_name_ko": self.ruined_name_ko,
            "ruined_description_ko": self.ruined_description_ko,
            "ruin_chance_if_broken": self.ruin_chance_if_broken,
            "break_effect_ko": self.break_effect_ko,
            "traits": list(self.traits)
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MonsterPart":
        return cls(
            part_id=str(data.get("part_id", "")),
            name_ko=str(data.get("name_ko", "")),
            max_hp=int(data.get("max_hp", 30)),
            current_hp=int(data.get("current_hp", data.get("max_hp", 30))),
            is_broken=bool(data.get("is_broken", False)),
            is_severed=bool(data.get("is_severed", False)),
            severable=bool(data.get("severable", False)),
            hitzone_slash=float(data.get("hitzone_slash", 1.0)),
            hitzone_blunt=float(data.get("hitzone_blunt", 1.0)),
            hitzone_shot=float(data.get("hitzone_shot", 1.0)),
            material_item_id=str(data.get("material_item_id", "")),
            material_name_ko=str(data.get("material_name_ko", "")),
            material_description_ko=str(data.get("material_description_ko", "")),
            ruined_item_id=str(data.get("ruined_item_id", "")),
            ruined_name_ko=str(data.get("ruined_name_ko", "")),
            ruined_description_ko=str(data.get("ruined_description_ko", "")),
            ruin_chance_if_broken=float(data.get("ruin_chance_if_broken", 0.50)),
            break_effect_ko=str(data.get("break_effect_ko", "")),
            traits=list(data.get("traits", ["몬스터 신체 부위", "부위 파괴 가능"]))
        )


@dataclass
class PartAttackResult:
    part_id: str
    part_name_ko: str
    raw_damage: int
    effective_damage: int
    hitzone_multiplier: float
    part_hp_remaining: int
    is_now_broken: bool
    is_now_severed: bool
    stagger_inflicted: bool
    dropped_severed_item_id: Optional[str] = None
    combat_log_ko: str = ""
    traits: List[str] = field(default_factory=lambda: ["부위 타격 판정", "육질 배율 연산"])


@dataclass
class HarvestOutcome:
    success: bool
    part_id: str
    part_name_ko: str
    item_id: str
    item_name_ko: str
    is_ruined: bool
    knife_durability_lost: int
    remaining_knife_durability: int
    narration_ko: str
    traits: List[str] = field(default_factory=lambda: ["해체 갈무리 결과", "전리품 획득"])


class AnatomyHarvestEngine:
    TRAITS: List[str] = [
        "몬스터 해부학 부위 파괴",
        "무기 육질 물리 판정",
        "꼬리 절단 및 필드 드랍",
        "부위 파손 페널티 해체 도축",
        "갈무리 칼 내구도 소모"
    ]
    traits: List[str] = field(default_factory=lambda: [
        "몬스터 해부학 부위 파괴",
        "무기 육질 물리 판정",
        "꼬리 절단 및 필드 드랍",
        "부위 파손 페널티 해체 도축",
        "갈무리 칼 내구도 소모"
    ])

    @classmethod
    def get_or_create_part(cls, monster: NPC, part_id: str) -> Optional[MonsterPart]:
        """Ensures MonsterPart instance exists in monster.anatomy_parts."""
        if not hasattr(monster, "anatomy_parts") or monster.anatomy_parts is None:
            monster.anatomy_parts = {}

        raw_part = monster.anatomy_parts.get(part_id)
        if raw_part is None:
            return None

        if isinstance(raw_part, MonsterPart):
            return raw_part
        elif isinstance(raw_part, dict):
            part_obj = MonsterPart.from_dict(raw_part)
            monster.anatomy_parts[part_id] = part_obj
            return part_obj
        return None

    @classmethod
    def attack_targeted_part(
        cls,
        monster: NPC,
        part_id: str,
        raw_damage: int,
        attack_tags: Optional[List[str]] = None,
        state: Optional[WorldState] = None
    ) -> PartAttackResult:
        """
        몬스터의 특정 부위를 조준 공격하여 육질 배율(Hitzone)을 적용하고 부위 파괴/절단을 판정.
        - 참격(slash): severable 부위 절단 가능
        - 둔기(blunt): 단단한 부위(외골격/뿔) 파괴에 높은 배율
        - 관통/사격(shot): 비행 피막이나 내장 연약 부위에 높은 배율
        """
        part = cls.get_or_create_part(monster, part_id)
        tags = [t.lower() for t in (attack_tags or [])]

        if not part:
            effective_dmg = max(1, raw_damage)
            monster.health = max(0, monster.health - effective_dmg)
            if monster.health <= 0:
                monster.alive = False
            return PartAttackResult(
                part_id=part_id,
                part_name_ko="몸통",
                raw_damage=raw_damage,
                effective_damage=effective_dmg,
                hitzone_multiplier=1.0,
                part_hp_remaining=monster.health,
                is_now_broken=False,
                is_now_severed=False,
                stagger_inflicted=False,
                combat_log_ko=f"[{monster.name}]의 몸통에 일반 타격 피해 {effective_dmg}를 입혔습니다."
            )

        # 육질 배율 계산
        if "slash" in tags or "참격" in tags:
            hitzone = part.hitzone_slash
            atk_type_ko = "날카로운 참격"
        elif any(t in tags for t in ["blunt", "strike", "둔기", "타격"]):
            hitzone = part.hitzone_blunt
            atk_type_ko = "묵직한 둔기 타격"
        elif any(t in tags for t in ["shot", "thrust", "projectile", "관통", "사격"]):
            hitzone = part.hitzone_shot
            atk_type_ko = "정밀한 관통 사격"
        else:
            hitzone = 1.0
            atk_type_ko = "일반 공격"

        effective_dmg = max(1, int(round(raw_damage * hitzone)))
        was_broken = part.is_broken
        was_severed = part.is_severed

        # 부위 및 본체 체력 차감
        part.current_hp = max(0, part.current_hp - effective_dmg)
        monster.health = max(0, monster.health - effective_dmg)
        if monster.health <= 0:
            monster.alive = False

        is_now_broken = False
        is_now_severed = False
        stagger_inflicted = False
        dropped_item_id = None
        logs = [f"{atk_type_ko}이(가) [{monster.name}]의 [{part.name_ko}]에 적중! (육질 배율 x{hitzone:.1f} -> 유효 피해 {effective_dmg})"]

        # 부위 파괴 또는 절단 판정
        if part.current_hp <= 0:
            if not was_broken:
                part.is_broken = True
                is_now_broken = True
                stagger_inflicted = True

            # 꼬리/사지 참격 절단 판정
            if part.severable and ("slash" in tags or "참격" in tags) and not was_severed:
                part.is_severed = True
                is_now_severed = True
                dropped_item_id = f"severed_{part.part_id}_{monster.id}"

                # 필드 바닥에 잘려나간 꼬리/신체 부위 아이템 생성 및 투하
                if state:
                    loc_id = monster.location
                    severed_item = Item(
                        id=dropped_item_id,
                        name=f"【{monster.name}의 잘려나간 {part.name_ko}】",
                        description=f"전투 중 날카로운 참격에 의해 동강 나 바닥에 뒹구는 거대한 잔해입니다. 현장에서 해체하여 소재를 갈무리할 수 있습니다.",
                        location=loc_id,
                        item_type="material",
                        weight=5.0,
                        properties={
                            "severed_part": True,
                            "source_npc_id": monster.id,
                            "part_id": part.part_id,
                            "material_item_id": part.material_item_id or f"mat_{part.part_id}",
                            "material_name_ko": part.material_name_ko or f"【{part.name_ko}】",
                            "material_description_ko": part.material_description_ko
                        }
                    )
                    state.items[dropped_item_id] = severed_item
                    if loc_id in state.locations and dropped_item_id not in state.locations[loc_id].items:
                        state.locations[loc_id].items.append(dropped_item_id)

                logs.append(f"💥【신체 절단!】 거센 일격에 [{monster.name}]의 [{part.name_ko}]이(가) 뜯겨져 나가 둔탁한 소리를 내며 바닥에 떨어졌습니다! ({part.break_effect_ko})")
            elif is_now_broken:
                logs.append(f"💥【부위 파괴!】 강력한 충격으로 [{monster.name}]의 [{part.name_ko}]이(가) 완전히 산산조각 났습니다! 거수가 고통에 비틀거리며 큰 경직에 빠집니다. ({part.break_effect_ko})")

        return PartAttackResult(
            part_id=part.part_id,
            part_name_ko=part.name_ko,
            raw_damage=raw_damage,
            effective_damage=effective_dmg,
            hitzone_multiplier=hitzone,
            part_hp_remaining=part.current_hp,
            is_now_broken=is_now_broken,
            is_now_severed=is_now_severed,
            stagger_inflicted=stagger_inflicted,
            dropped_severed_item_id=dropped_item_id,
            combat_log_ko=" ".join(logs)
        )

    @classmethod
    def can_harvest(cls, player: Player, monster: NPC, part_id: str, state: WorldState) -> Tuple[bool, str]:
        """해체 및 갈무리 실행 가능 여부 정밀 검증."""
        if monster.alive:
            return False, "아직 숨이 붙어 날뛰는 마수를 살아있는 채로 해체할 수는 없습니다."

        if not hasattr(monster, "anatomy_parts") or part_id not in monster.anatomy_parts:
            return False, f"[{monster.name}]에게는 '{part_id}' 부위가 존재하지 않습니다."

        part = cls.get_or_create_part(monster, part_id)
        if not part:
            return False, f"'{part_id}' 부위 정보를 찾을 수 없습니다."

        if hasattr(monster, "harvested_parts") and part_id in monster.harvested_parts:
            return False, f"[{part.name_ko}] 부위는 이미 온전히 도축 및 갈무리가 끝났습니다."

        if part.is_severed:
            return False, f"[{part.name_ko}]은(는) 전투 중 절단되어 필드 바닥에 떨어졌습니다. 떨어진 잔해를 직접 해체해야 합니다."

        knife = cls._find_suitable_knife(player, state)
        if not knife:
            return False, "사체를 가르고 가죽을 벗겨낼 도축용 단검이나 날붙이 도구가 소지품에 없습니다."

        return True, "갈무리 가능"

    @classmethod
    def _find_suitable_knife(cls, player: Player, state: WorldState, preferred_knife_id: Optional[str] = None) -> Optional[Item]:
        """소지품 또는 장착 장비 중 도축/해체에 적합한 칼붙이 탐색."""
        if preferred_knife_id and preferred_knife_id in state.items:
            return state.items[preferred_knife_id]

        # 1. Check weapon slot
        wep_id = getattr(player.equipment, "weapon", None)
        if wep_id and wep_id in state.items:
            wep = state.items[wep_id]
            wep_name = wep.name.lower()
            if any(k in wep_name for k in ["검", "단검", "나이프", "칼", "도"]) or "slash" in getattr(wep, "physics_tags", []):
                return wep

        # 2. Check inventory
        for i_id in player.inventory:
            if i_id in state.items:
                item = state.items[i_id]
                i_name = item.name.lower()
                if any(k in i_name for k in ["나이프", "단검", "칼", "도축", "갈무리", "단도"]):
                    return item

        # 3. Fallback: Any weapon with cutting physics tag or item_type == "weapon"
        for i_id in player.inventory:
            if i_id in state.items:
                item = state.items[i_id]
                if item.item_type in ["weapon", "tool"]:
                    return item

        return None

    @classmethod
    def harvest_part(
        cls,
        player: Player,
        monster: NPC,
        part_id: str,
        state: WorldState,
        knife_item_id: Optional[str] = None,
        rng_roll: Optional[float] = None
    ) -> HarvestOutcome:
        """
        사체에서 지정된 신체 부위를 현실적으로 도축 및 갈무리.
        - 파괴되지 않은 온전한 부위: 100% 최상급 완제품 소재 획득
        - 파괴되어 손상된 부위: 50% 확률로 짓이겨져 '깨진 잔해/파편'으로 열화
        - 해체 도구 내구도 1 소모
        """
        valid, reason = cls.can_harvest(player, monster, part_id, state)
        if not valid:
            return HarvestOutcome(
                success=False,
                part_id=part_id,
                part_name_ko=part_id,
                item_id="",
                item_name_ko="",
                is_ruined=False,
                knife_durability_lost=0,
                remaining_knife_durability=100,
                narration_ko=reason
            )

        part = cls.get_or_create_part(monster, part_id)
        knife = cls._find_suitable_knife(player, state, knife_item_id)
        knife_dur_lost = 1
        rem_dur = 100

        if knife:
            EnchantEngine.consume_durability(knife, loss=1)
            rem_dur = getattr(knife, "durability", 100)

        is_ruined = False
        roll = rng_roll if rng_roll is not None else random.random()

        # 부위 파손 페널티 계산
        if part.is_broken and roll < part.ruin_chance_if_broken:
            is_ruined = True
            item_id = part.ruined_item_id or f"ruined_{part.part_id}"
            item_name = part.ruined_name_ko or f"【짓이겨진 {part.name_ko} 파편】"
            item_desc = part.ruined_description_ko or f"전투 중 가해진 거센 충격으로 심하게 파손된 {part.name_ko} 잔해입니다. 온전한 원자재로는 쓸 수 없으나 합금이나 가루로 분쇄해 쓸 수 있습니다."
            narration = (
                f"전투 중 타격으로 심하게 훼손된 [{part.name_ko}]을(를) 조심스레 도축했으나, "
                f"골격과 조직이 바스러져 온전한 형태를 보존하지 못했습니다. "
                f"저급 부산물인 [{item_name}]만을 수습했습니다. (도축 칼 내구도 -1)"
            )
        else:
            is_ruined = False
            item_id = part.material_item_id or f"mat_{part.part_id}"
            item_name = part.material_name_ko or f"【온전한 {part.name_ko}】"
            item_desc = part.material_description_ko or f"흠집 하나 없이 극상의 선도를 유지한 {monster.name}의 핵심 소재입니다."
            if part.is_broken:
                narration = (
                    f"파손된 흔적이 남은 [{part.name_ko}]이었으나, 능숙하고 섬세한 칼놀림으로 "
                    f"망가지지 않은 핵심부를 온전히 분리해 내어 [{item_name}]을(를) 기적적으로 수확했습니다! (도축 칼 내구도 -1)"
                )
            else:
                narration = (
                    f"공격에 손상되지 않고 온전하게 보존된 [{part.name_ko}]에서 "
                    f"최상급 원자재인 [{item_name}]을(를) 완벽하게 도축 및 갈무리했습니다. (도축 칼 내구도 -1)"
                )

        # 아이템 생성 및 인벤토리 지급
        if item_id not in state.items:
            state.items[item_id] = Item(
                id=item_id,
                name=item_name,
                description=item_desc,
                location="inventory",
                item_type="material",
                value=20 if is_ruined else 80,
                weight=1.5,
                properties={"source_monster": monster.id, "part_id": part_id, "is_ruined": is_ruined}
            )

        if item_id not in player.inventory:
            player.inventory.append(item_id)

        # 갈무리 완료 부위 등록
        if not hasattr(monster, "harvested_parts") or monster.harvested_parts is None:
            monster.harvested_parts = []
        monster.harvested_parts.append(part_id)

        return HarvestOutcome(
            success=True,
            part_id=part.part_id,
            part_name_ko=part.name_ko,
            item_id=item_id,
            item_name_ko=item_name,
            is_ruined=is_ruined,
            knife_durability_lost=knife_dur_lost,
            remaining_knife_durability=rem_dur,
            narration_ko=narration
        )

    @classmethod
    def harvest_severed_object(
        cls,
        player: Player,
        severed_item_id: str,
        state: WorldState,
        knife_item_id: Optional[str] = None
    ) -> HarvestOutcome:
        """필드 바닥에 떨어진 절단된 꼬리/신체 부위를 직접 해체."""
        if severed_item_id not in state.items:
            return HarvestOutcome(
                success=False,
                part_id="",
                part_name_ko="",
                item_id="",
                item_name_ko="",
                is_ruined=False,
                knife_durability_lost=0,
                remaining_knife_durability=100,
                narration_ko="현장에 존재하지 않는 신체 잔해입니다."
            )

        severed_item = state.items[severed_item_id]
        props = getattr(severed_item, "properties", {}) or {}
        if not props.get("severed_part"):
            return HarvestOutcome(
                success=False,
                part_id="",
                part_name_ko=severed_item.name,
                item_id="",
                item_name_ko="",
                is_ruined=False,
                knife_durability_lost=0,
                remaining_knife_durability=100,
                narration_ko="이 물체는 해체 가능한 절단 부위가 아닙니다."
            )

        knife = cls._find_suitable_knife(player, state, knife_item_id)
        if not knife:
            return HarvestOutcome(
                success=False,
                part_id="",
                part_name_ko=severed_item.name,
                item_id="",
                item_name_ko="",
                is_ruined=False,
                knife_durability_lost=0,
                remaining_knife_durability=100,
                narration_ko="도축용 칼붙이가 없어 떨어진 잔해를 해체할 수 없습니다."
            )

        EnchantEngine.consume_durability(knife, loss=1)
        rem_dur = getattr(knife, "durability", 100)

        # 소재 추출
        yield_id = props.get("material_item_id", f"mat_{severed_item_id}")
        yield_name = props.get("material_name_ko", f"【정제된 {severed_item.name}】")
        yield_desc = props.get("material_description_ko", "절단된 부위에서 깔끔하게 적출해 낸 최상급 고기 및 가죽 소재입니다.")

        if yield_id not in state.items:
            state.items[yield_id] = Item(
                id=yield_id,
                name=yield_name,
                description=yield_desc,
                location="inventory",
                item_type="material",
                value=90,
                weight=2.0
            )

        if yield_id not in player.inventory:
            player.inventory.append(yield_id)

        # 필드에서 잘려나간 잔해 제거
        loc_id = player.location
        if loc_id in state.locations and severed_item_id in state.locations[loc_id].items:
            state.locations[loc_id].items.remove(severed_item_id)

        return HarvestOutcome(
            success=True,
            part_id=props.get("part_id", "severed_part"),
            part_name_ko=severed_item.name,
            item_id=yield_id,
            item_name_ko=yield_name,
            is_ruined=False,
            knife_durability_lost=1,
            remaining_knife_durability=rem_dur,
            narration_ko=f"바닥에 떨어진 거대한 [{severed_item.name}]을(를) 해체하여 최상급 부위 소재인 [{yield_name}]을(를) 획득했습니다! (도축 칼 내구도 -1)"
        )

    @classmethod
    def create_standard_monster_anatomy(cls, monster_id_or_type: str) -> Dict[str, MonsterPart]:
        """
        대표적인 몬스터 해부학 부위 프리셋 생성.
        - 뇌격 흑액 메기 (동판 비늘의 벼락 메기): 피뢰침 꼬리(절단 가능), 통전 뇌각(둔기 약점), 동판 비늘, 고전압 발전낭
        - 비룡 (와이번): 머리 뿔, 날개 피막, 가시 꼬리(절단 가능), 복부 비늘
        - 심해 갑각수: 두꺼운 등껍질, 파쇄 집게발, 심해 핵
        """
        m_type = monster_id_or_type.lower()

        if any(k in m_type for k in ["catfish", "메기", "thunder"]):
            return {
                "lightning_rod_tail": MonsterPart(
                    part_id="lightning_rod_tail",
                    name_ko="피뢰침 꼬리",
                    max_hp=40,
                    current_hp=40,
                    severable=True,
                    hitzone_slash=1.3,
                    hitzone_blunt=1.4,
                    hitzone_shot=1.0,
                    material_item_id="copper_catfish_tail",
                    material_name_ko="【동판 메기의 피뢰침 꼬리】",
                    material_description_ko="황동 피뢰침이 일체화된 메기의 거대한 꼬리. 번개 공격을 지면으로 접지 유도하는 장비 제작 소재.",
                    ruined_item_id="crushed_tail_remains",
                    ruined_name_ko="부러진 피뢰침과 찢긴 꼬리지느러미",
                    ruined_description_ko="파괴된 충격으로 피뢰침이 꺾이고 살점이 뜯겨나간 잔해입니다.",
                    ruin_chance_if_broken=0.50,
                    break_effect_ko="접지가 끊어져 체내 전하가 방출되지 못하고 3턴간 자멸성 전기 과부하 상태에 빠짐",
                    traits=["피뢰침 접지", "절단 가능", "약점 부위"]
                ),
                "head_horn": MonsterPart(
                    part_id="head_horn",
                    name_ko="통전 뇌각",
                    max_hp=35,
                    current_hp=35,
                    severable=False,
                    hitzone_slash=0.7,
                    hitzone_blunt=1.4,
                    hitzone_shot=0.9,
                    material_item_id="conductive_thunder_horn",
                    material_name_ko="【통전성 뇌각】",
                    material_description_ko="청록색 구리 피막으로 덮여 파란 전광을 내뿜는 단단한 뿔.",
                    ruined_item_id="broken_horn_fragment",
                    ruined_name_ko="금 간 뇌각 조각",
                    ruined_description_ko="망치에 부서져 전도율이 떨어진 뿔 파편입니다.",
                    ruin_chance_if_broken=0.50,
                    break_effect_ko="전방 번개 발사 사거리 및 공격력 50% 약화",
                    traits=["단단한 육질", "둔기 약점", "전격 방전 기관"]
                ),
                "copper_scales": MonsterPart(
                    part_id="copper_scales",
                    name_ko="동판 비늘",
                    max_hp=50,
                    current_hp=50,
                    severable=False,
                    hitzone_slash=0.8,
                    hitzone_blunt=1.2,
                    hitzone_shot=0.8,
                    material_item_id="copper_plate_scales",
                    material_name_ko="【통전성 구리 비늘】",
                    material_description_ko="녹슨 구리 합금으로 단단하게 경화된 비늘. 전격 저항 방어구의 핵심 원자재.",
                    ruined_item_id="chipped_copper_scale",
                    ruined_name_ko="깨진 구리 비늘 부스러기",
                    ruined_description_ko="충격에 깨져 가루가 섞인 비늘 조각입니다.",
                    ruin_chance_if_broken=0.50,
                    break_effect_ko="전체 방어력 30% 저하",
                    traits=["갑각 방어", "전기 전도", "방어구 소재"]
                ),
                "electric_sac": MonsterPart(
                    part_id="electric_sac",
                    name_ko="고전압 발전낭",
                    max_hp=25,
                    current_hp=25,
                    severable=False,
                    hitzone_slash=1.4,
                    hitzone_blunt=1.1,
                    hitzone_shot=1.5,
                    material_item_id="high_voltage_organ",
                    material_name_ko="【고전압 발전낭】",
                    material_description_ko="체내에서 고압 전류를 응축하는 희귀한 내부 마력 장기.",
                    ruined_item_id="ruptured_electric_sac",
                    ruined_name_ko="터져버린 발전낭 찌꺼기",
                    ruined_description_ko="체액과 마나가 누출되어 검게 탄 장기 잔해입니다.",
                    ruin_chance_if_broken=0.50,
                    break_effect_ko="광역 뇌전 방전 공격 원천 봉쇄",
                    traits=["치명적 약점", "관통 약점", "희귀 내장"]
                )
            }

        # 기본 야수/와이번 형태
        return {
            "head_horn": MonsterPart(
                part_id="head_horn",
                name_ko="머리 뿔",
                max_hp=30,
                current_hp=30,
                severable=False,
                hitzone_slash=0.8,
                hitzone_blunt=1.3,
                hitzone_shot=0.9,
                material_item_id="beast_sharp_horn",
                material_name_ko="【맹수의 단단한 뿔】",
                ruined_item_id="shattered_horn_shard",
                ruined_name_ko="부서진 뿔 조각",
                ruin_chance_if_broken=0.50,
                break_effect_ko="돌진 공격력 40% 저하",
                traits=["타격 약점"]
            ),
            "tail": MonsterPart(
                part_id="tail",
                name_ko="가시 꼬리",
                max_hp=35,
                current_hp=35,
                severable=True,
                hitzone_slash=1.3,
                hitzone_blunt=0.8,
                hitzone_shot=1.0,
                material_item_id="beast_spiked_tail",
                material_name_ko="【맹수의 가시 꼬리】",
                ruined_item_id="torn_tail_scrap",
                ruined_name_ko="찢겨진 꼬리 살점",
                ruin_chance_if_broken=0.50,
                break_effect_ko="꼬리 휘두르기 사거리 및 공격 반경 50% 축소",
                traits=["절단 가능", "참격 약점"]
            ),
            "hide": MonsterPart(
                part_id="hide",
                name_ko="두꺼운 가죽",
                max_hp=45,
                current_hp=45,
                severable=False,
                hitzone_slash=1.1,
                hitzone_blunt=1.1,
                hitzone_shot=1.2,
                material_item_id="pristine_thick_pelt",
                material_name_ko="【최상급 원피】",
                ruined_item_id="shredded_leather_scrap",
                ruined_name_ko="너덜너덜한 가죽 조각",
                ruin_chance_if_broken=0.50,
                break_effect_ko="방어력 감소",
                traits=["가죽 소재", "전신"]
            )
        }
