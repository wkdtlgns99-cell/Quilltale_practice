"""
Trap & Mechanism Hazard Engine for Quilltale TRPG.
Deterministically manages contextual traps for Surface, Dungeon, and Hidden Realm maps:
1. Surface: Terrain-specific natural & hunter traps (Bear trap, Pitfall, Tripwire alarm, Quicksand).
2. Dungeon: Lethal mechanical & elemental traps (Crushing ceiling, Poison gas vent, Wall crossbow, Arcane mine).
3. Hidden Realm: Esoteric reality-bending traps (Void displacement, Abyssal hysteria mist, Life siphon glyph).

Enforces Perception detection, Agility/Intelligence disarming, tool consumption, and reflex saving throws.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import random
import logging

from src.world.dice import DiceEngine
from src.world.status_engine import StatusEffectEngine

logger = logging.getLogger(__name__)


@dataclass
class TrapSpec:
    id: str
    name_ko: str
    category: str                   # "surface" | "dungeon" | "hidden_realm"
    terrains: List[str]             # Applicable terrains: forest, mountains, swamp, desert, plains, urban, all
    detect_dc: int                  # Difficulty Class for Perception detection
    disarm_dc: int                  # Difficulty Class for Agility/Intelligence disarming
    damage: int                     # Direct health damage on trigger
    damage_type: str                # physical, piercing, blunt, poison, fire, arcane, void
    inflicted_status: List[Dict[str, Any]] = field(default_factory=list) # [{"status": "bleeding", "duration": 3, "potency": 1}]
    noise_db: int = 25              # Acoustic signature in dB (triggers monster aggro)
    description: str = ""
    trigger_message_ko: str = ""
    disarm_message_ko: str = ""
    fail_disarm_trigger: bool = True # If disarm fails, does trap trigger immediately?
    special_effect: Optional[str] = None # "void_teleport_entrance", "mana_drain", "hysteria_panic"
    # Mandatory traits tag list (Rule 6)
    traits: List[str] = field(default_factory=list)


@dataclass
class TrapInstance:
    instance_id: str
    spec_id: str
    location_id: str
    spec: TrapSpec
    status: str = "hidden"          # "hidden", "revealed", "disarmed", "triggered"
    # Mandatory traits tag list (Rule 6)
    traits: List[str] = field(default_factory=list)


# Contextual Trap Registry by Map Category and Terrain
TRAP_REGISTRY: Dict[str, TrapSpec] = {
    # -------------------------------------------------------------
    # 1. Surface Traps (지상 일반 맵 지형별 컨셉 함정)
    # -------------------------------------------------------------
    "surface_bear_trap": TrapSpec(
        id="surface_bear_trap",
        name_ko="사냥꾼의 강철 덫",
        category="surface",
        terrains=["forest", "plains"],
        detect_dc=12,
        disarm_dc=12,
        damage=16,
        damage_type="piercing",
        inflicted_status=[
            {"status": "bleeding", "duration": 3, "potency": 2}
        ],
        noise_db=25,
        description="마른 잎사귀 아래 은폐된 거치형 톱니 강철 덫입니다.",
        trigger_message_ko="찰칵! 마른 잎사귀 아래 숨겨진 강철 톱니 덫이 발목을 물어뜯으며 깊은 열상과 출혈을 일으킵니다!",
        disarm_message_ko="조심스럽게 지렛대 원리를 이용해 강철 덫의 용수철 힌지를 안전하게 젖혀 무력화했습니다.",
        traits=["자연 은폐", "출혈 유발", "사냥 도구", "물리 함정"]
    ),
    "surface_falling_log": TrapSpec(
        id="surface_falling_log",
        name_ko="낙하 통나무 트랩",
        category="surface",
        terrains=["forest", "mountains"],
        detect_dc=13,
        disarm_dc=13,
        damage=22,
        damage_type="blunt",
        noise_db=45,
        description="나뭇가지 사이에 굵은 덩굴줄로 매달린 거대한 참나무 통나무입니다.",
        trigger_message_ko="쿠구궁! 팽팽하던 덩굴이 풀리며 육중한 통나무가 덮쳐와 둔탁한 충격으로 몸을 강타합니다!",
        disarm_message_ko="나무 상단으로 이어진 유인 장력 줄을 조심스럽게 절단하여 통나무를 안전한 방향으로 떨구었습니다.",
        traits=["둔기 충격", "낙하 충돌", "산림 부비트랩", "고소음"]
    ),
    "surface_tripwire_alarm": TrapSpec(
        id="surface_tripwire_alarm",
        name_ko="방울 경보 인계철선",
        category="surface",
        terrains=["plains", "urban", "forest"],
        detect_dc=11,
        disarm_dc=10,
        damage=0,
        damage_type="physical",
        noise_db=65, # High noise triggers monster/bandit ambush
        description="지면 위 5cm 높이로 팽팽하게 엮인 낚싯줄과 청동 방울 뭉치입니다.",
        trigger_message_ko="딸랑딸랑! 보이지 않는 인계철선을 건드리자 청동 방울이 시끄럽게 울려 퍼지며 주변의 적과 야수들에게 위치가 발각되었습니다!",
        disarm_message_ko="인계철선에 달린 청동 방울을 손으로 감싸 쥐고 낚싯줄의 장력을 조심스럽게 해제했습니다.",
        traits=["인계철선", "경보 장치", "고소음 어그로", "비살상"]
    ),
    "surface_crevasse_pit": TrapSpec(
        id="surface_crevasse_pit",
        name_ko="빙판 균열 크레바스",
        category="surface",
        terrains=["mountains", "plains"],
        detect_dc=14,
        disarm_dc=12,
        damage=18,
        damage_type="blunt",
        inflicted_status=[
            {"status": "hypothermia", "duration": 3, "potency": 1}
        ],
        noise_db=30,
        description="살얼음과 신설로 위장된 산악 빙하 틈새 구덩이입니다.",
        trigger_message_ko="우지끈! 살얼음판이 무너지며 깊은 얼음 틈새로 미끄러져 떨어져 타박상과 한기 오한을 입습니다!",
        disarm_message_ko="등산용 로프와 쐐기로 붕괴 위험이 있는 얼음 덮개를 고정하고 안전한 우회로를 확보했습니다.",
        traits=["빙하 균열", "추락 피해", "저체온증", "환경 함정"]
    ),
    "surface_bog_quicksand": TrapSpec(
        id="surface_bog_quicksand",
        name_ko="늪지 진흙 유사(Quicksand)",
        category="surface",
        terrains=["swamp"],
        detect_dc=13,
        disarm_dc=11,
        damage=10,
        damage_type="physical",
        inflicted_status=[
            {"status": "poison", "duration": 2, "potency": 1}
        ],
        noise_db=15,
        description="수초와 녹조류 아래 숨겨진 끈적한 수렁 늪구덩이입니다.",
        trigger_message_ko="철퍽! 발이 닿는 순간 끈적한 유사 진흙이 하반신을 집어삼키며 진흙 속 유독 가스와 수생 기생충이 피부를 자극합니다!",
        disarm_message_ko="튼튼한 나뭇가지를 걸쳐 수렁의 위험 반경을 표시하고 안전 발판을 만들었습니다.",
        traits=["늪지 수렁", "이동 구속", "질식 위험", "유독 환경"]
    ),

    # -------------------------------------------------------------
    # 2. Dungeon Traps (던전/지하 유적용 치명적 기계·물리·마법 함정)
    # -------------------------------------------------------------
    "dungeon_crushing_ceiling": TrapSpec(
        id="dungeon_crushing_ceiling",
        name_ko="천장 압축 화강암 슬래브",
        category="dungeon",
        terrains=["all", "urban", "mountains"],
        detect_dc=16,
        disarm_dc=16,
        damage=35,
        damage_type="blunt",
        inflicted_status=[
            {"status": "stun", "duration": 1, "potency": 1},
            {"status": "exhaustion", "duration": 2, "potency": 1}
        ],
        noise_db=75,
        description="지하 석실 천장에 매달린 수 톤 무게의 가시 박힌 화강암 압축 판입니다.",
        trigger_message_ko="콰아아앙! 바닥 압력판이 눌리며 천장에서 거대한 화강암 슬래브가 내리꽂혀 뼈마디를 으스러뜨리는 파괴적인 충격을 가합니다!",
        disarm_message_ko="벽면 석조 틈새의 기계식 톱니 기어에 쐐기 못을 박아 낙하 래칫 메커니즘을 영구히 물림 정지시켰습니다.",
        traits=["즉사급 압축", "석조 기계", "체간 붕괴", "지하 던전"]
    ),
    "dungeon_poison_gas_vent": TrapSpec(
        id="dungeon_poison_gas_vent",
        name_ko="밀폐실 독가스 분출구",
        category="dungeon",
        terrains=["all"],
        detect_dc=15,
        disarm_dc=15,
        damage=14,
        damage_type="poison",
        inflicted_status=[
            {"status": "poison", "duration": 4, "potency": 2}
        ],
        noise_db=20,
        description="청동 배관을 통해 황화수소와 신경독 가스를 뿜어내는 은폐 노즐입니다.",
        trigger_message_ko="쉬이익! 석조 바닥 틈새의 노즐에서 짙은 황록색 신경독 가스가 치솟아 호흡기를 태우고 시야를 흐립니다!",
        disarm_message_ko="도적의 도구 렌치를 사용해 벽면 제어 밸브의 황동 급기 차단판을 닫아 독가스 공급관을 봉쇄했습니다.",
        traits=["신경독 분출", "산소 결핍", "지속 피해", "도구 필수"]
    ),
    "dungeon_wall_crossbow": TrapSpec(
        id="dungeon_wall_crossbow",
        name_ko="벽면 연발 강철 석궁",
        category="dungeon",
        terrains=["all"],
        detect_dc=14,
        disarm_dc=14,
        damage=24,
        damage_type="piercing",
        inflicted_status=[
            {"status": "bleeding", "duration": 3, "potency": 2}
        ],
        noise_db=40,
        description="석벽 틈새에 매립되어 도르래 와이어로 장전되는 4연발 강철 쇠뇌입니다.",
        trigger_message_ko="피슝! 텅! 석벽 홈에서 연발 쇠뇌살 4발이 맹렬한 속도로 튀어나와 갑옷을 뚫고 깊숙이 박힙니다!",
        disarm_message_ko="격발 와이어의 중심 축 핀을 가볍게 뽑아내어 석궁 격발 공이치를 불발 상태로 전환했습니다.",
        traits=["방어 관통", "연발 쇠뇌", "깊은 자상", "기계식 함정"]
    ),
    "dungeon_arcane_flame_rune": TrapSpec(
        id="dungeon_arcane_flame_rune",
        name_ko="고대 마력 지뢰 룬",
        category="dungeon",
        terrains=["all"],
        detect_dc=16,
        disarm_dc=17,
        damage=28,
        damage_type="fire",
        inflicted_status=[
            {"status": "burn", "duration": 3, "potency": 2}
        ],
        noise_db=60,
        special_effect="mana_drain",
        description="바닥 석판 위에 붉은빛으로 희미하게 맥동하는 고대 발화 마법진입니다.",
        trigger_message_ko="쾅! 마법 룬이 침입자의 체온을 감지하고 맹렬한 마력 폭염을 터뜨리며 화염 화상과 함께 마력을 강제 증발시킵니다!",
        disarm_message_ko="정밀한 단검 끝으로 지면의 룬 마나 도관 획을 긁어 절단하여 마력 순환 회로를 소멸시켰습니다.",
        traits=["마법 지뢰", "화염 폭발", "마나 소실", "고난도 해체"]
    ),

    # -------------------------------------------------------------
    # 3. Hidden Realm Traps (히든 맵 / 아공간 / 심연 전용 현실 왜곡 함정)
    # -------------------------------------------------------------
    "hidden_void_displacement": TrapSpec(
        id="hidden_void_displacement",
        name_ko="공간 왜곡 강제 전이 함정",
        category="hidden_realm",
        terrains=["all"],
        detect_dc=18,
        disarm_dc=19,
        damage=12,
        damage_type="void",
        special_effect="void_teleport_entrance",
        noise_db=50,
        description="공간이 일렁이며 허공에 은은한 은빛 균열을 드러내는 시공간 간섭 균열입니다.",
        trigger_message_ko="우우웅! 발밑의 공간이 비틀려 접히며 시야가 반전되고, 강제적인 차원 왜곡 충격과 함께 맵의 입구로 강제 텔레포트됩니다!",
        disarm_message_ko="시공간 간섭 균열의 반발력 중심점에 마력 핵을 접촉시켜 일그러진 차원 축을 원래대로 복구했습니다.",
        traits=["공간 왜곡", "입구 강제 송환", "차원 간섭", "초월 함정"]
    ),
    "hidden_abyssal_hysteria": TrapSpec(
        id="hidden_abyssal_hysteria",
        name_ko="심연 착란 안개 분출구",
        category="hidden_realm",
        terrains=["all"],
        detect_dc=17,
        disarm_dc=18,
        damage=15,
        damage_type="void",
        inflicted_status=[
            {"status": "confusion", "duration": 3, "potency": 2},
            {"status": "exhaustion", "duration": 2, "potency": 1}
        ],
        special_effect="hysteria_panic",
        noise_db=10,
        description="허공의 틈에서 새어 나오는 검붉은 심연의 환각성 영혼 증기입니다.",
        trigger_message_ko="스스스... 검붉은 심연의 안개가 귓가를 갉아먹으며 알 수 없는 비명 소리와 환각이 뇌리를 헤집어 극심한 공황과 혼란을 일으킵니다!",
        disarm_message_ko="정화의 소금을 틈새에 뿌리고 고대 봉인식 제어 매듭을 묶어 심연의 영혼 누출을 차단했습니다.",
        traits=["정신 오염", "공황 발작", "심연 안개", "광기 유발"]
    ),
    "hidden_life_siphon_altar": TrapSpec(
        id="hidden_life_siphon_altar",
        name_ko="생명 갈취 인장 제단",
        category="hidden_realm",
        terrains=["all"],
        detect_dc=18,
        disarm_dc=19,
        damage=25,
        damage_type="arcane",
        special_effect="life_drain",
        noise_db=30,
        description="생명체의 혈액과 활력을 원격으로 빨아들이는 칠흑빛 석조 제단 인장입니다.",
        trigger_message_ko="번쩍! 검은 마력 사슬이 사지를 휘감으며 신체의 생체 활력과 혈기를 순식간에 강탈하여 제단 핵으로 전송합니다!",
        disarm_message_ko="제단 핵에 흐르는 혈액 마나 역류 방향을 반전시켜 생명 갈취 마법진의 동력을 영구히 정지시켰습니다.",
        traits=["생명 갈취", "혈액 결계", "신체 흡수", "금기 주술"]
    ),
}


class TrapEngine:
    """
    Deterministic management engine for map-contextual traps.
    Handles perception detection, tool-based disarming, reflex saves, and penalty execution.
    """

    @classmethod
    def get_contextual_trap_specs(cls, category: str, terrain: str = "plains") -> List[TrapSpec]:
        """
        Filters trap specs matching the map's category (surface, dungeon, hidden_realm)
        and terrain concept.
        """
        matched: List[TrapSpec] = []
        for spec in TRAP_REGISTRY.values():
            if spec.category != category:
                continue
            if "all" in spec.terrains or terrain in spec.terrains:
                matched.append(spec)
        return matched

    @classmethod
    def spawn_trap_for_location(
        cls,
        state: Any,
        location_id: str,
        trap_spec_id: Optional[str] = None
    ) -> Optional[TrapInstance]:
        """
        Creates and mounts a contextual trap instance inside the target location.
        """
        loc = state.locations.get(location_id)
        if not loc:
            return None

        cat = getattr(loc, "location_category", "surface")
        terrain = getattr(loc, "terrain", "plains")

        spec: Optional[TrapSpec] = None
        if trap_spec_id and trap_spec_id in TRAP_REGISTRY:
            spec = TRAP_REGISTRY[trap_spec_id]
        else:
            candidates = cls.get_contextual_trap_specs(cat, terrain)
            if candidates:
                # Deterministic selection based on location id hash
                idx = abs(hash(location_id + str(len(getattr(loc, "traps", []))))) % len(candidates)
                spec = candidates[idx]

        if not spec:
            return None

        inst_id = f"trap_{location_id}_{len(getattr(loc, 'traps', [])) + 1}"
        instance = TrapInstance(
            instance_id=inst_id,
            spec_id=spec.id,
            location_id=location_id,
            spec=spec,
            status="hidden",
            traits=list(spec.traits)
        )

        if not hasattr(loc, "traps") or loc.traps is None:
            loc.traps = []
        loc.traps.append(inst_id)

        # Store in global state traps registry if available
        if not hasattr(state, "active_traps"):
            state.active_traps = {}
        state.active_traps[inst_id] = instance

        return instance

    @classmethod
    def detect_traps_in_location(
        cls,
        entity: Any,
        location_id: str,
        state: Any,
        is_active_search: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Checks if entity's perception detects any hidden traps in the current location.
        Active search gives +4 bonus to perception.
        """
        loc = state.locations.get(location_id)
        if not loc or not getattr(loc, "traps", None):
            return []

        active_traps = getattr(state, "active_traps", {})
        results: List[Dict[str, Any]] = []

        # Entity perception check
        per_val = getattr(entity, "effective_perception", getattr(entity, "perception", 10))
        roll = DiceEngine.roll_d20()
        search_bonus = 4 if is_active_search else 0
        total_per = roll + DiceEngine.stat_modifier(per_val) + search_bonus

        for trap_id in loc.traps:
            t_inst = active_traps.get(trap_id)
            if not t_inst or t_inst.status != "hidden":
                continue

            if total_per >= t_inst.spec.detect_dc or roll == 20:
                t_inst.status = "revealed"
                results.append({
                    "trap_id": t_inst.instance_id,
                    "trap_name": t_inst.spec.name_ko,
                    "status": "revealed",
                    "roll": roll,
                    "total_score": total_per,
                    "dc": t_inst.spec.detect_dc,
                    "message_ko": f"🔍 [함정 발견] 예리한 감각으로 숨겨진 [{t_inst.spec.name_ko}]을(를) 포착했습니다! (판정: {total_per} vs DC {t_inst.spec.detect_dc})"
                })

        return results

    @classmethod
    def disarm_trap(
        cls,
        entity: Any,
        trap_instance_id: str,
        state: Any,
        tool_item_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Attempts to disarm a revealed trap.
        Uses higher of Agility or Intelligence.
        Having 'thieves_tools' grants +3 bonus.
        """
        active_traps = getattr(state, "active_traps", {})
        t_inst = active_traps.get(trap_instance_id)
        if not t_inst:
            return {"success": False, "message_ko": "해당 함정을 찾을 수 없습니다."}

        if t_inst.status == "disarmed":
            return {"success": True, "message_ko": "이미 해체된 안전한 함정입니다."}
        if t_inst.status == "triggered":
            return {"success": False, "message_ko": "이미 격발되어 파손된 함정입니다."}

        # Check tools
        inv = getattr(entity, "inventory", [])
        has_tool = ("thieves_tools" in inv) or (tool_item_id == "thieves_tools")
        tool_bonus = 3 if has_tool else 0

        # Choose best stat between Agility and Intelligence
        agi = getattr(entity, "effective_agility", getattr(entity, "agility", 10))
        intel = getattr(entity, "effective_intelligence", getattr(entity, "intelligence", 10))
        chosen_stat = max(agi, intel)

        roll = DiceEngine.roll_d20()
        total_roll = roll + DiceEngine.stat_modifier(chosen_stat) + tool_bonus

        if total_roll >= t_inst.spec.disarm_dc or roll == 20:
            t_inst.status = "disarmed"
            return {
                "success": True,
                "triggered": False,
                "message_ko": f"🛠️ [해체 성공] {t_inst.spec.disarm_message_ko} (판정: {total_roll} vs DC {t_inst.spec.disarm_dc})"
            }
        else:
            # Failure: Trigger immediately if spec dictates
            triggered_result = None
            if t_inst.spec.fail_disarm_trigger:
                triggered_result = cls.trigger_trap(entity, trap_instance_id, state)

            return {
                "success": False,
                "triggered": t_inst.spec.fail_disarm_trigger,
                "trigger_result": triggered_result,
                "message_ko": f"💥 [해체 실패] 손끝이 미끄러지며 장치가 오작동했습니다! (판정: {total_roll} vs DC {t_inst.spec.disarm_dc})"
            }

    @classmethod
    def trigger_trap(
        cls,
        entity: Any,
        trap_instance_id: str,
        state: Any
    ) -> Dict[str, Any]:
        """
        Triggers trap onto the entity.
        Rolls Reflex saving throw (Agility DC 12) for half damage.
        Applies status effects, damage, noise signature, and special effects.
        """
        active_traps = getattr(state, "active_traps", {})
        t_inst = active_traps.get(trap_instance_id)
        if not t_inst:
            return {"triggered": False, "message_ko": "함정이 존재하지 않습니다."}

        spec = t_inst.spec
        t_inst.status = "triggered"

        # Reflex Save (Dodge/Brace)
        agi = getattr(entity, "effective_agility", getattr(entity, "agility", 10))
        d20 = DiceEngine.roll_d20()
        save_dc = 12 + (spec.detect_dc - 10) // 2
        is_dodged = (d20 + DiceEngine.stat_modifier(agi)) >= save_dc

        base_dmg = spec.damage
        actual_dmg = max(1, base_dmg // 2) if is_dodged else base_dmg

        # Apply damage
        curr_hp = getattr(entity, "health", 100)
        new_hp = max(0, curr_hp - actual_dmg)
        entity.health = new_hp

        # Apply status effects
        inflicted_names: List[str] = []
        if not is_dodged:
            for eff_data in spec.inflicted_status:
                s_id = eff_data.get("status")
                dur = eff_data.get("duration", 2)
                pot = eff_data.get("potency", 1)
                StatusEffectEngine.apply_status(entity, s_id, duration=dur, potency=pot)
                inflicted_names.append(s_id)

        # Handle Special Effects
        special_logs: List[str] = []
        if spec.special_effect == "void_teleport_entrance":
            # Force teleport to entrance or start
            loc_obj = state.locations.get(entity.location)
            dungeon_root = getattr(loc_obj, "dungeon_id", "start")
            entity.location = dungeon_root or "start"
            special_logs.append("🌌 [공간 왜곡] 차원 균열에 휩쓸려 던전 입구로 강제 송환되었습니다!")
        elif spec.special_effect == "mana_drain":
            curr_mana = getattr(entity, "mana", 50)
            entity.mana = max(0, curr_mana - 20)
            special_logs.append("⚡ [마나 소실] 마력 20이 대기 중으로 강제 증발했습니다.")

        dodge_text = " (민첩한 반사신경으로 피해를 절반 경감!)" if is_dodged else ""
        full_msg = f"{spec.trigger_message_ko}{dodge_text} [피해: {actual_dmg}, 소음: {spec.noise_db}dB]"

        return {
            "triggered": True,
            "trap_id": t_inst.instance_id,
            "trap_name": spec.name_ko,
            "damage_dealt": actual_dmg,
            "is_dodged": is_dodged,
            "inflicted_status": inflicted_names,
            "noise_db": spec.noise_db,
            "special_logs": special_logs,
            "message_ko": full_msg
        }
