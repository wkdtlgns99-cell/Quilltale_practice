"""
Dynasty Lineage & Heir Succession Engine for Quilltale TRPG.
Provides deterministic bloodline traits, family tree genealogy, active heir grooming,
and player-driven succession/headship transfer without mandatory death/retirement.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
import logging
import random

logger = logging.getLogger(__name__)


# =====================================================================
# 1. Lineage Data Models (Rule 5: traits list included)
# =====================================================================
@dataclass
class BloodlineTrait:
    """Represents an inheritable genetic or supernatural bloodline trait."""
    trait_id: str
    name: str
    trait_type: str = "virtue"  # virtue, flaw, neutral, apex
    stat_modifiers: Dict[str, Any] = field(default_factory=dict)
    inheritance_chance: float = 0.60
    description: str = ""
    traits: List[str] = field(default_factory=list)  # System Rule 5

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "BloodlineTrait":
        clean = dict(data)
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


@dataclass
class FamilyMember:
    """Represents a member of the noble dynasty in the family tree."""
    member_id: str
    name: str
    generation: int = 1
    role: str = "heir"  # head, heir, elder, cadet
    gender: str = "남성"
    age: int = 20
    class_archetype: str = "전사"
    bloodline_traits: List[BloodlineTrait] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)
    skills: List[str] = field(default_factory=list)
    assigned_domain_id: Optional[str] = None
    is_active_player: bool = False
    traits: List[str] = field(default_factory=list)  # System Rule 5

    def to_dict(self) -> dict:
        d = asdict(self)
        d["bloodline_traits"] = [
            t.to_dict() if hasattr(t, "to_dict") else t for t in self.bloodline_traits
        ]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "FamilyMember":
        clean = dict(data)
        bt_list = []
        for t in data.get("bloodline_traits", []):
            if isinstance(t, dict):
                bt_list.append(BloodlineTrait.from_dict(t))
            elif isinstance(t, BloodlineTrait):
                bt_list.append(t)
        clean["bloodline_traits"] = bt_list
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


@dataclass
class DynastyLineageState:
    """State tracking the overarching dynasty, family tree, and ancestral vault."""
    dynasty_name: str
    motto: str = "불꽃은 결코 꺼지지 않는다"
    dynasty_prestige: int = 100
    current_head_id: str = "head_1"
    current_generation: int = 1
    family_tree: Dict[str, FamilyMember] = field(default_factory=dict)
    designated_heir_id: Optional[str] = None
    ancestral_heirlooms: List[Dict[str, Any]] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)  # System Rule 5

    def to_dict(self) -> dict:
        d = asdict(self)
        d["family_tree"] = {
            k: (v.to_dict() if hasattr(v, "to_dict") else v)
            for k, v in self.family_tree.items()
        }
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "DynastyLineageState":
        clean = dict(data)
        tree = {}
        for k, v in data.get("family_tree", {}).items():
            if isinstance(v, dict):
                tree[k] = FamilyMember.from_dict(v)
            elif isinstance(v, FamilyMember):
                tree[k] = v
        clean["family_tree"] = tree
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


@dataclass
class InheritanceReport:
    """Deterministic summary of a voluntary or natural headship succession."""
    predecessor_name: str
    successor_name: str
    new_generation: int
    inherited_domains: List[str] = field(default_factory=list)
    inherited_gold: int = 0
    inherited_heirlooms: List[str] = field(default_factory=list)
    inherited_traits: List[str] = field(default_factory=list)
    prestige_change: int = 20
    summary_ko: str = ""
    traits: List[str] = field(default_factory=list)  # System Rule 5

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "InheritanceReport":
        clean = dict(data)
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


# =====================================================================
# 2. Master Bloodline Trait Registry
# =====================================================================
BLOODLINE_TRAITS_CATALOG: Dict[str, Dict[str, Any]] = {
    "dragon_blood": {
        "name": "고대 용의 혈통",
        "trait_type": "virtue",
        "stat_modifiers": {"max_health": 30, "strength": 2, "fire_res": 25},
        "inheritance_chance": 0.70,
        "description": "용의 숨결을 품은 뜨거운 혈맥. 체력과 화염 저항이 크게 상승합니다.",
        "traits": ["용족", "체력증가", "화염면역"],
    },
    "titan_physique": {
        "name": "거인의 골격",
        "trait_type": "virtue",
        "stat_modifiers": {"strength": 3, "constitution": 2, "max_health": 20},
        "inheritance_chance": 0.65,
        "description": "선천적으로 단단한 골격과 체구. 완력과 근육 내구도가 뛰어납니다.",
        "traits": ["골격강화", "근력증가"],
    },
    "arcane_affinity": {
        "name": "고대 비전 친화",
        "trait_type": "virtue",
        "stat_modifiers": {"intelligence": 3, "max_mana": 40},
        "inheritance_chance": 0.60,
        "description": "마나 회로가 선천적으로 넓고 투명하여 비전 마법의 위력이 상승합니다.",
        "traits": ["마력친화", "비전지능"],
    },
    "indomitable_will": {
        "name": "불굴의 정신력",
        "trait_type": "virtue",
        "stat_modifiers": {"wisdom": 2, "fatigue_res": 30},
        "inheritance_chance": 0.60,
        "description": "어떤 공포와 절망 속에서도 흔들리지 않는 가문의 강철 같은 정신.",
        "traits": ["정신력", "피로저항"],
    },
    "hawk_eye": {
        "name": "매의 천리안",
        "trait_type": "virtue",
        "stat_modifiers": {"perception": 3, "crit_rate": 10},
        "inheritance_chance": 0.60,
        "description": "먼 거리의 표적과 미세한 암살자의 기척을 꿰뚫어 보는 시력.",
        "traits": ["원거리시야", "치명타"],
    },
    "iron_liver": {
        "name": "철의 간",
        "trait_type": "virtue",
        "stat_modifiers": {"poison_res": 30, "alcohol_res": 40},
        "inheritance_chance": 0.55,
        "description": "체내 독소와 독주를 신속히 중화시키는 강인한 해독 능력.",
        "traits": ["독소저항", "주량"],
    },
    "golden_touch": {
        "name": "황금의 감각",
        "trait_type": "virtue",
        "stat_modifiers": {"gold_income_mult": 0.15},
        "inheritance_chance": 0.50,
        "description": "돈 냄새를 기가 막히게 맡으며 거래마다 큰 이익을 남기는 상재.",
        "traits": ["상업", "부의축적"],
    },
    "mana_hypersensitivity": {
        "name": "마나 과민증",
        "trait_type": "flaw",
        "stat_modifiers": {"max_mana": 25, "mana_burn_vuln": 15},
        "inheritance_chance": 0.40,
        "description": "마나에 너무 민감하여 에테르 역류와 두통을 앓기 쉬운 체질적 결함.",
        "traits": ["결함", "마나불안"],
    },
    "near_sighted": {
        "name": "선천적 근시",
        "trait_type": "flaw",
        "stat_modifiers": {"perception": -2, "intelligence": 2},
        "inheritance_chance": 0.40,
        "description": "먼 시야가 흐릿한 대신 서책 연구와 세밀한 사물 관찰에 능합니다.",
        "traits": ["결함", "시야저하"],
    },
    "noble_pride": {
        "name": "가문의 자긍심",
        "trait_type": "neutral",
        "stat_modifiers": {"prestige_bonus": 15},
        "inheritance_chance": 0.80,
        "description": "가문의 명예를 목숨보다 소중히 여기는 긍지와 자부심.",
        "traits": ["가문명예", "긍지"],
    },
}


# =====================================================================
# 3. Dynasty Lineage Engine
# =====================================================================
class LineageEngine:
    """
    Pure deterministic dynasty and bloodline management engine.
    Manages genealogy, bloodline traits, heir grooming, and voluntary headship transfers.
    """

    @classmethod
    def get_lineage_state(cls, state: Any) -> Optional[DynastyLineageState]:
        """Retrieves or parses DynastyLineageState from state.dynasty_lineage."""
        if not hasattr(state, "dynasty_lineage") or state.dynasty_lineage is None:
            return None
        if isinstance(state.dynasty_lineage, dict):
            state.dynasty_lineage = DynastyLineageState.from_dict(state.dynasty_lineage)
        return state.dynasty_lineage

    @classmethod
    def initialize_dynasty(
        cls,
        state: Any,
        dynasty_name: str,
        motto: str = "불꽃은 결코 꺼지지 않는다",
        starter_trait_keys: Optional[List[str]] = None,
    ) -> DynastyLineageState:
        """
        Founds a new noble dynasty led by the current player character (1st Generation Head).
        Applies bloodline traits to the founder.
        """
        player_name = getattr(state.player, "name", "초대 가주") or "초대 가주"
        head_id = "member_gen1_head"

        # Resolve starter traits
        traits_list: List[BloodlineTrait] = []
        keys = starter_trait_keys or ["titan_physique", "noble_pride"]
        for k in keys:
            t_data = BLOODLINE_TRAITS_CATALOG.get(k)
            if t_data:
                traits_list.append(BloodlineTrait(
                    trait_id=k,
                    name=t_data["name"],
                    trait_type=t_data["trait_type"],
                    stat_modifiers=t_data["stat_modifiers"],
                    inheritance_chance=t_data["inheritance_chance"],
                    description=t_data["description"],
                    traits=list(t_data["traits"]),
                ))

        founder = FamilyMember(
            member_id=head_id,
            name=player_name,
            generation=1,
            role="head",
            gender="남성",
            age=25,
            class_archetype="기사",
            bloodline_traits=traits_list,
            stats={"strength": 14, "agility": 12, "constitution": 14, "intelligence": 10, "wisdom": 11, "perception": 10},
            is_active_player=True,
            traits=["가문창설자", "1대가주"],
        )

        dynasty = DynastyLineageState(
            dynasty_name=dynasty_name,
            motto=motto,
            dynasty_prestige=150,
            current_head_id=head_id,
            current_generation=1,
            family_tree={head_id: founder},
            traits=["명문가문", "혈통각성"],
        )

        state.dynasty_lineage = dynasty

        # Apply stat modifiers to current player
        cls._apply_bloodline_effects_to_player(state.player, traits_list)

        logger.info(f"Dynasty founded: {dynasty_name} (Founder: {player_name})")
        return dynasty

    @classmethod
    def generate_heir_candidates(
        cls,
        state: Any,
        count: int = 3,
    ) -> List[FamilyMember]:
        """
        Deterministically generates successor candidates (children/relatives).
        Rolls trait inheritance from the current head with potential mutations.
        """
        dynasty = cls.get_lineage_state(state)
        if not dynasty:
            return []

        head = dynasty.family_tree.get(dynasty.current_head_id)
        if not head:
            return []

        next_gen = dynasty.current_generation + 1
        archetypes = [
            ("검술사", "전사", {"strength": 15, "agility": 13, "constitution": 14}),
            ("비전술사", "마법사", {"intelligence": 16, "wisdom": 13, "agility": 11}),
            ("정찰대원", "도적", {"agility": 16, "perception": 15, "strength": 11}),
        ]
        genders = ["남성", "여성", "남성"]
        names_pool = ["에단", "엘레나", "카엘", "로완", "아이린", "레오릭"]

        candidates: List[FamilyMember] = []
        seed_base = dynasty.current_generation * 100 + len(dynasty.family_tree)

        for i in range(count):
            arch_title, arch_class, base_stats = archetypes[i % len(archetypes)]
            c_gender = genders[i % len(genders)]
            c_name = f"{names_pool[(seed_base + i) % len(names_pool)]} {dynasty.dynasty_name}"
            c_id = f"member_gen{next_gen}_{i+1}"

            # Trait inheritance
            inherited_traits: List[BloodlineTrait] = []
            for pt in head.bloodline_traits:
                # Deterministic inheritance roll based on index & seed
                roll_val = ((seed_base + i * 37 + hash(pt.trait_id)) % 100) / 100.0
                if roll_val <= pt.inheritance_chance:
                    inherited_traits.append(BloodlineTrait(
                        trait_id=pt.trait_id,
                        name=pt.name,
                        trait_type=pt.trait_type,
                        stat_modifiers=pt.stat_modifiers,
                        inheritance_chance=pt.inheritance_chance,
                        description=pt.description,
                        traits=list(pt.traits),
                    ))

            # Potential mutation (add a new trait if room)
            if len(inherited_traits) < 3:
                cand_keys = [k for k in BLOODLINE_TRAITS_CATALOG.keys() if k not in [t.trait_id for t in inherited_traits]]
                if cand_keys:
                    mut_key = cand_keys[(seed_base + i * 19) % len(cand_keys)]
                    m_data = BLOODLINE_TRAITS_CATALOG[mut_key]
                    inherited_traits.append(BloodlineTrait(
                        trait_id=mut_key,
                        name=m_data["name"],
                        trait_type=m_data["trait_type"],
                        stat_modifiers=m_data["stat_modifiers"],
                        inheritance_chance=m_data["inheritance_chance"],
                        description=m_data["description"],
                        traits=list(m_data["traits"]),
                    ))

            member = FamilyMember(
                member_id=c_id,
                name=c_name,
                generation=next_gen,
                role="heir",
                gender=c_gender,
                age=18 + (i * 2),
                class_archetype=arch_class,
                bloodline_traits=inherited_traits,
                stats=base_stats,
                is_active_player=False,
                traits=["후계자후보", arch_title],
            )
            dynasty.family_tree[c_id] = member
            candidates.append(member)

        # Auto-designate first candidate if none set
        if not dynasty.designated_heir_id and candidates:
            dynasty.designated_heir_id = candidates[0].member_id

        return candidates

    @classmethod
    def designate_heir(cls, state: Any, member_id: str) -> Dict[str, Any]:
        """Designates a specific family member as official heir to the headship."""
        dynasty = cls.get_lineage_state(state)
        if not dynasty:
            return {"success": False, "reason": "가문이 창설되지 않았습니다."}

        member = dynasty.family_tree.get(member_id)
        if not member:
            return {"success": False, "reason": f"가문 구성원 [{member_id}]을(를) 찾을 수 없습니다."}

        dynasty.designated_heir_id = member_id
        member.role = "heir"

        return {
            "success": True,
            "heir_name": member.name,
            "generation": member.generation,
            "message": f"[{dynasty.dynasty_name}]의 차기 공식 후계자로 [{member.name}] (제{member.generation}대)을(를) 지명했습니다!",
        }

    @classmethod
    def transfer_headship(
        cls,
        state: Any,
        successor_id: Optional[str] = None,
    ) -> InheritanceReport:
        """
        Transfers family headship to the designated heir voluntarily.
        No player death or retirement is required!
        - Previous head becomes an honored family elder/advisor (stays alive in tree).
        - Successor becomes the active player character, inheriting domain titles and ancestral gear.
        """
        dynasty = cls.get_lineage_state(state)
        if not dynasty:
            return InheritanceReport(
                predecessor_name="미지",
                successor_name="미지",
                new_generation=1,
                summary_ko="가문 정보가 없어 승계를 진행할 수 없습니다.",
            )

        target_id = successor_id or dynasty.designated_heir_id
        if not target_id or target_id not in dynasty.family_tree:
            # Generate candidates if tree has none
            candidates = cls.generate_heir_candidates(state, count=2)
            target_id = candidates[0].member_id if candidates else None

        if not target_id or target_id not in dynasty.family_tree:
            return InheritanceReport(
                predecessor_name="미지",
                successor_name="미지",
                new_generation=dynasty.current_generation,
                summary_ko="승계할 후계자를 찾을 수 없습니다.",
            )

        old_head = dynasty.family_tree.get(dynasty.current_head_id)
        successor = dynasty.family_tree[target_id]

        old_head_name = old_head.name if old_head else state.player.name
        if old_head:
            old_head.role = "elder"
            old_head.is_active_player = False
            if "원로" not in old_head.traits:
                old_head.traits.append("원로")

        # Set new head
        successor.role = "head"
        successor.is_active_player = True
        dynasty.current_head_id = successor.member_id
        dynasty.current_generation = successor.generation
        dynasty.designated_heir_id = None
        dynasty.dynasty_prestige += 30

        # Transfer Domain sovereignty (domain_engine integration)
        inherited_domains: List[str] = []
        if hasattr(state, "pioneering_domains") and state.pioneering_domains:
            reg = getattr(state, "infrastructure", None)
            for s_id, pstate in state.pioneering_domains.items():
                pstate.pioneer_leader_id = successor.name
                if reg and hasattr(reg, "settlements") and s_id in reg.settlements:
                    reg.settlements[s_id].lord_npc_id = successor.name
                    reg.settlements[s_id].lord_dynasty = dynasty.dynasty_name
                inherited_domains.append(pstate.settlement_name)

        # Update active player character identity
        state.player.name = successor.name
        if hasattr(state.player, "character_class"):
            state.player.character_class = successor.class_archetype

        # Re-apply heir's bloodline traits to active player
        cls._apply_bloodline_effects_to_player(state.player, successor.bloodline_traits)

        heirloom_names = [h.get("name", "가보") for h in dynasty.ancestral_heirlooms]
        trait_names = [t.name for t in successor.bloodline_traits]

        summary = (
            f"👑 [{dynasty.dynasty_name}]의 가주 이양이 완수되었습니다!\n"
            f"- 신임 가주: 제{successor.generation}대 가주 [{successor.name}]\n"
            f"- 선대 가주 [{old_head_name}]은(는) 가문의 원로이자 최고 고문으로 추대되었습니다.\n"
            f"- 승계 영지: {', '.join(inherited_domains) if inherited_domains else '없음'}\n"
            f"- 계승 혈통 특성: {', '.join(trait_names)}\n"
            f"- 가문 명성: {dynasty.dynasty_prestige} (+30)"
        )

        report = InheritanceReport(
            predecessor_name=old_head_name,
            successor_name=successor.name,
            new_generation=successor.generation,
            inherited_domains=inherited_domains,
            inherited_gold=state.player.gold,
            inherited_heirlooms=heirloom_names,
            inherited_traits=trait_names,
            prestige_change=30,
            summary_ko=summary,
            traits=["가주이양", f"제{successor.generation}대"],
        )

        logger.info(f"Headship transferred in {dynasty.dynasty_name}: {old_head_name} -> {successor.name}")
        return report

    @classmethod
    def add_ancestral_heirloom(cls, state: Any, item_name: str) -> Dict[str, Any]:
        """Registers a rare weapon or relic as a permanent ancestral heirloom."""
        dynasty = cls.get_lineage_state(state)
        if not dynasty:
            return {"success": False, "reason": "가문이 창설되지 않았습니다."}

        # Check inventory
        matched_item = None
        for it_id in state.player.inventory:
            it = state.items.get(it_id) if hasattr(state, "items") else None
            it_name = it.name if it else it_id
            if item_name.lower() in it_name.lower():
                matched_item = {"id": it_id, "name": it_name}
                break

        if not matched_item:
            # Fallback mock item name if text matched
            matched_item = {"id": f"heirloom_{len(dynasty.ancestral_heirlooms)+1}", "name": item_name}

        dynasty.ancestral_heirlooms.append(matched_item)
        dynasty.dynasty_prestige += 15

        return {
            "success": True,
            "heirloom_name": matched_item["name"],
            "prestige_bonus": 15,
            "message": f"[{matched_item['name']}]을(를) [{dynasty.dynasty_name}]의 공식 가문 가보(Heirloom)로 등록했습니다! (가문 명성 +15)",
        }

    @classmethod
    def _apply_bloodline_effects_to_player(cls, player: Any, bloodline_traits: List[BloodlineTrait]) -> None:
        """Applies trait stat modifiers to Player instance."""
        for t in bloodline_traits:
            mods = t.stat_modifiers
            if "max_health" in mods:
                player.max_health = max(player.max_health, player.max_health + mods["max_health"])
                player.health = min(player.max_health, player.health + mods["max_health"])
            if "strength" in mods and hasattr(player, "strength"):
                player.strength += mods["strength"]
            if "intelligence" in mods and hasattr(player, "intelligence"):
                player.intelligence += mods["intelligence"]
            if "perception" in mods and hasattr(player, "perception"):
                player.perception += mods["perception"]

    @classmethod
    def get_lineage_status_summary(cls, state: Any) -> str:
        """Generates a concise Korean deterministic status briefing string."""
        dynasty = cls.get_lineage_state(state)
        if not dynasty:
            return "[가문 미창설: '가문 창설 [가문명]' 명령으로 가문을 설립할 수 있습니다]"

        head = dynasty.family_tree.get(dynasty.current_head_id)
        head_name = head.name if head else "공석"
        heir = dynasty.family_tree.get(dynasty.designated_heir_id) if dynasty.designated_heir_id else None
        heir_name = f"{heir.name} (제{heir.generation}대)" if heir else "미지명 (후계자 지명 필요)"

        # Trait list
        head_traits_str = ", ".join([t.name for t in head.bloodline_traits]) if head else "없음"
        heirlooms_str = ", ".join([h.get("name", "가보") for h in dynasty.ancestral_heirlooms]) if dynasty.ancestral_heirlooms else "없음"

        # Count elders and family members
        total_members = len(dynasty.family_tree)
        elders = [m.name for m in dynasty.family_tree.values() if m.role == "elder"]
        elders_str = ", ".join(elders) if elders else "없음"

        lines = [
            f"=== 🛡️ 가문 혈통 브리핑: {dynasty.dynasty_name} ===",
            f"- 가훈: \"{dynasty.motto}\"",
            f"- 가문 명성: {dynasty.dynasty_prestige}점 | 현재 세대: 제{dynasty.current_generation}대",
            f"- 현직 가주: {head_name} (활성 플레이어)",
            f"- 가문 원로: {elders_str}",
            f"- 공식 후계자: {heir_name}",
            f"- 혈통 고유 특성: {head_traits_str}",
            f"- 가문 보관 가보: {heirlooms_str}",
            f"- 등록 가문원: 총 {total_members}명",
        ]
        return "\n".join(lines)
