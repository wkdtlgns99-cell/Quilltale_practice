"""
Faith, Deities, Miracles & Divine Mechanics Engine for Quilltale TRPG.
Pure system and mechanics framework without hardcoded deities.
Provides deterministic piety management, devotion hierarchies, dynamic miracle pipelines,
taboo violations, and settlement religious infrastructure integration.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)


# =====================================================================
# 1. Faith & Divine Data Models (Rule 5: traits list included)
# =====================================================================
@dataclass
class DivineMiracle:
    """Specification of a divine miracle granted by a deity."""
    miracle_id: str
    name: str
    piety_cost: int = 50
    effect_type: str = "blessing"  # heal, ward, smite, cleanse, fortune, blessing
    magnitude: float = 30.0
    duration_turns: int = 3
    description: str = ""
    traits: List[str] = field(default_factory=list)  # System Rule 5

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DivineMiracle":
        clean = dict(data)
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


@dataclass
class DeityProfile:
    """Dynamic deity profile representing a god, ancient spirit, or cosmic patron."""
    deity_id: str
    name: str
    domain: str = "holy"  # holy, nature, war, knowledge, shadow, craft, astral, abyss
    pantheon_title: str = "숭배받는 신격"
    commandments: List[str] = field(default_factory=list)
    taboos: List[str] = field(default_factory=list)  # ["necromancy", "arson", "poison", "oathbreak"]
    favored_offerings: List[str] = field(default_factory=list)  # ["gold", "herb", "iron", "gem"]
    miracles: Dict[str, DivineMiracle] = field(default_factory=dict)
    traits: List[str] = field(default_factory=list)  # System Rule 5

    def to_dict(self) -> dict:
        d = asdict(self)
        d["miracles"] = {
            k: (v.to_dict() if hasattr(v, "to_dict") else v)
            for k, v in self.miracles.items()
        }
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "DeityProfile":
        clean = dict(data)
        m_dict = {}
        for k, v in data.get("miracles", {}).items():
            if isinstance(v, dict):
                m_dict[k] = DivineMiracle.from_dict(v)
            elif isinstance(v, DivineMiracle):
                m_dict[k] = v
        clean["miracles"] = m_dict
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


@dataclass
class PlayerFaithState:
    """Player faith tracking, devotion rank, blessings, and heresy level."""
    deity_id: Optional[str] = None
    deity_name: str = "무신론자 / 방랑자"
    piety: int = 0  # 0 ~ 1000
    devotion_tier: int = 0  # 0: 불신자, 1: 신도, 2: 헌신자, 3: 사제, 4: 사도
    active_blessings: List[Dict[str, Any]] = field(default_factory=list)
    active_curses: List[Dict[str, Any]] = field(default_factory=list)
    heresy_level: int = 0  # 0 ~ 100
    prayers_count: int = 0
    sacrifices_count: int = 0
    traits: List[str] = field(default_factory=list)  # System Rule 5

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PlayerFaithState":
        clean = dict(data)
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


@dataclass
class FaithTurnSummary:
    """Deterministic snapshot of a single turn faith progression."""
    turn: int
    piety_delta: int = 0
    current_piety: int = 0
    miracles_triggered: List[str] = field(default_factory=list)
    curses_triggered: List[str] = field(default_factory=list)
    events_triggered: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)  # System Rule 5

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FaithTurnSummary":
        clean = dict(data)
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


# =====================================================================
# 2. Faith & Divine Mechanics Engine (Pure System Framework)
# =====================================================================
class FaithEngine:
    """
    Pure deterministic faith, prayer, sacrifice, miracle, and taboo engine.
    Does not hardcode deities; manages dynamic registries and universal divine pipelines.
    """

    DEVOTION_TIER_NAMES = [
        (0, "불신자 / 방관자"),
        (1, "입문 신도"),
        (2, "경건한 헌신자"),
        (3, "성스러운 사제"),
        (4, "신의 사도"),
    ]

    @classmethod
    def ensure_deities_db(cls, state: Any) -> Dict[str, DeityProfile]:
        """Ensures state.deities_db exists and is mapped to DeityProfile instances."""
        if not hasattr(state, "deities_db") or state.deities_db is None:
            state.deities_db = {}
        for k, v in list(state.deities_db.items()):
            if isinstance(v, dict):
                state.deities_db[k] = DeityProfile.from_dict(v)
        return state.deities_db

    @classmethod
    def get_faith_state(cls, state: Any) -> PlayerFaithState:
        """Retrieves or creates PlayerFaithState from state.faith_state."""
        if not hasattr(state, "faith_state") or state.faith_state is None:
            state.faith_state = PlayerFaithState(traits=["무신자"])
        elif isinstance(state.faith_state, dict):
            state.faith_state = PlayerFaithState.from_dict(state.faith_state)
        return state.faith_state

    @classmethod
    def register_deity(cls, state: Any, deity: DeityProfile) -> DeityProfile:
        """Registers a deity into the world state database dynamically."""
        db = cls.ensure_deities_db(state)
        db[deity.deity_id] = deity
        logger.info(f"Deity registered: {deity.name} ({deity.deity_id}) in domain {deity.domain}")
        return deity

    @classmethod
    def create_custom_deity(
        cls,
        state: Any,
        deity_id: str,
        name: str,
        domain: str = "holy",
        pantheon_title: str = "수호신",
        commandments: Optional[List[str]] = None,
        taboos: Optional[List[str]] = None,
        favored_offerings: Optional[List[str]] = None,
        miracles: Optional[List[DivineMiracle]] = None,
        traits: Optional[List[str]] = None,
    ) -> DeityProfile:
        """
        Factory to instantiate and register a custom deity dynamically.
        Creates default domain-appropriate miracles if none are supplied.
        """
        miracle_map: Dict[str, DivineMiracle] = {}
        if miracles:
            for m in miracles:
                miracle_map[m.miracle_id] = m
        else:
            # Auto-generate baseline miracles for the domain
            miracle_map[f"{deity_id}_heal"] = DivineMiracle(
                miracle_id=f"{deity_id}_heal",
                name=f"{name}의 은총 (치유)",
                piety_cost=30,
                effect_type="heal",
                magnitude=40.0,
                duration_turns=1,
                description=f"{name}의 거룩한 빛이 깃들어 치명상을 즉시 치료합니다.",
                traits=["치유", domain],
            )
            miracle_map[f"{deity_id}_ward"] = DivineMiracle(
                miracle_id=f"{deity_id}_ward",
                name=f"{name}의 성스러운 보호막",
                piety_cost=50,
                effect_type="ward",
                magnitude=25.0,
                duration_turns=3,
                description=f"{name}의 신성 결계가 시전자를 감싸 적의 물리/마법 피해를 흡수합니다.",
                traits=["보호막", domain],
            )
            miracle_map[f"{deity_id}_smite"] = DivineMiracle(
                miracle_id=f"{deity_id}_smite",
                name=f"{name}의 천벌 (심판)",
                piety_cost=60,
                effect_type="smite",
                magnitude=50.0,
                duration_turns=1,
                description=f"신앙의 힘을 담은 신벌의 일격으로 적을 강타합니다.",
                traits=["성벌", domain],
            )
            miracle_map[f"{deity_id}_cleanse"] = DivineMiracle(
                miracle_id=f"{deity_id}_cleanse",
                name=f"{name}의 정화",
                piety_cost=40,
                effect_type="cleanse",
                magnitude=1.0,
                duration_turns=1,
                description=f"모든 부정적 상태이상, 저주, 중독을 성수로 씻어내듯 정화합니다.",
                traits=["정화", domain],
            )

        profile = DeityProfile(
            deity_id=deity_id,
            name=name,
            domain=domain,
            pantheon_title=pantheon_title,
            commandments=commandments or ["계율을 지키고 공물을 바치라"],
            taboos=taboos or ["necromancy", "arson"],
            favored_offerings=favored_offerings or ["gold", "herb"],
            miracles=miracle_map,
            traits=traits or ["신격", domain],
        )
        return cls.register_deity(state, profile)

    @classmethod
    def choose_deity(cls, state: Any, deity_id: str) -> Dict[str, Any]:
        """Switches or devotes the player to a registered deity."""
        db = cls.ensure_deities_db(state)
        deity = db.get(deity_id)
        if not deity:
            return {"success": False, "reason": f"신격 [{deity_id}]가 존재하지 않습니다."}

        fstate = cls.get_faith_state(state)
        old_deity_name = fstate.deity_name

        # If switching from another deity, small heresy penalty
        if fstate.deity_id and fstate.deity_id != deity_id:
            fstate.piety = max(0, int(fstate.piety * 0.3))
            fstate.heresy_level = min(100, fstate.heresy_level + 15)

        fstate.deity_id = deity.deity_id
        fstate.deity_name = deity.name
        fstate.devotion_tier = cls.calculate_devotion_tier(fstate.piety)[0]
        if "신앙인" not in fstate.traits:
            fstate.traits.append("신앙인")

        tier_title = cls.calculate_devotion_tier(fstate.piety)[1]
        return {
            "success": True,
            "deity_name": deity.name,
            "devotion_title": tier_title,
            "piety": fstate.piety,
            "message": f"[{deity.name}]을(를) 주신으로 모시기로 맹세했습니다! (신심 등급: {tier_title}, 현재 신앙도: {fstate.piety})",
        }

    @classmethod
    def calculate_devotion_tier(cls, piety: int) -> Tuple[int, str]:
        """Computes devotion tier and Korean title based on piety threshold."""
        if piety >= 700:
            return 4, "신의 사도 (Apostle)"
        elif piety >= 350:
            return 3, "성스러운 사제 (Priest)"
        elif piety >= 150:
            return 2, "경건한 헌신자 (Devotee)"
        elif piety >= 50:
            return 1, "입문 신도 (Believer)"
        return 0, "불신자 / 방관자 (Layperson)"

    @classmethod
    def pray(cls, state: Any, prayer_intensity: str = "normal") -> Dict[str, Any]:
        """
        Offers prayer to the current deity, recovering mental fatigue and gaining piety.
        """
        fstate = cls.get_faith_state(state)
        if not fstate.deity_id:
            return {"success": False, "reason": "모시는 신격이 없습니다. 먼저 신앙을 선택해 주십시오."}

        db = cls.ensure_deities_db(state)
        deity = db.get(fstate.deity_id)
        d_name = deity.name if deity else fstate.deity_name

        piety_gain = 15 if prayer_intensity == "fervent" else 8
        fstate.piety = min(1000, fstate.piety + piety_gain)
        fstate.prayers_count += 1
        fstate.devotion_tier, tier_title = cls.calculate_devotion_tier(fstate.piety)

        # Relieve player fatigue or minor mana heal
        if hasattr(state.player, "fatigue"):
            state.player.fatigue = max(0, state.player.fatigue - 5)
        if hasattr(state.player, "mana"):
            state.player.mana = min(state.player.max_mana_effective, state.player.mana + 10)

        return {
            "success": True,
            "deity_name": d_name,
            "piety_gained": piety_gain,
            "current_piety": fstate.piety,
            "devotion_title": tier_title,
            "message": f"[{d_name}]의 성호를 읊으며 경건한 기도를 올렸습니다. (신앙도 +{piety_gain}, 현재: {fstate.piety} [{tier_title}])",
        }

    @classmethod
    def offer_sacrifice(
        cls,
        state: Any,
        offering_type: str,
        offering_name: str = "",
        value: int = 0,
    ) -> Dict[str, Any]:
        """
        Burns an offering (gold, item, holy relic) on an altar for massive piety gain.
        """
        fstate = cls.get_faith_state(state)
        if not fstate.deity_id:
            return {"success": False, "reason": "공물을 바칠 제단이나 모시는 신격이 없습니다."}

        db = cls.ensure_deities_db(state)
        deity = db.get(fstate.deity_id)
        d_name = deity.name if deity else fstate.deity_name

        piety_gained = 0
        consumed_desc = ""

        if offering_type == "gold":
            gold_amt = max(10, value or 50)
            if state.player.gold < gold_amt:
                return {"success": False, "reason": f"공물로 바칠 금화가 부족합니다. (필요: {gold_amt}G, 보유: {state.player.gold}G)"}
            state.player.gold -= gold_amt
            piety_gained = int(gold_amt * 0.5)
            consumed_desc = f"금화 {gold_amt}G"
        else:
            # Item offering from inventory
            matched_id = None
            for it_id in list(state.player.inventory):
                it = state.items.get(it_id) if hasattr(state, "items") else None
                it_n = it.name if it else it_id
                if offering_name.lower() in it_n.lower():
                    matched_id = it_id
                    consumed_desc = f"[{it_n}]"
                    break

            if matched_id:
                state.player.inventory.remove(matched_id)
                piety_gained = 35
                if deity and any(fav in matched_id.lower() or fav in offering_name.lower() for fav in deity.favored_offerings):
                    piety_gained = 60  # Bonus for favored offering
            else:
                return {"success": False, "reason": f"인벤토리에 공물로 바칠 [{offering_name}]이(가) 없습니다."}

        fstate.piety = min(1000, fstate.piety + piety_gained)
        fstate.sacrifices_count += 1
        fstate.devotion_tier, tier_title = cls.calculate_devotion_tier(fstate.piety)

        return {
            "success": True,
            "deity_name": d_name,
            "consumed": consumed_desc,
            "piety_gained": piety_gained,
            "current_piety": fstate.piety,
            "devotion_title": tier_title,
            "message": f"제단에 {consumed_desc}을(를) 정성껏 번제로 바쳤습니다! [{d_name}]이(가) 기쁘게 흠향합니다. (신앙도 +{piety_gained}, 현재: {fstate.piety})",
        }

    @classmethod
    def invoke_miracle(cls, state: Any, miracle_key: str) -> Dict[str, Any]:
        """
        Invokes a divine miracle by consuming piety through the universal effect pipeline.
        Supports: heal, ward, smite, cleanse, fortune.
        """
        fstate = cls.get_faith_state(state)
        if not fstate.deity_id:
            return {"success": False, "reason": "기적을 내려줄 신격과의 교감이 없습니다."}

        db = cls.ensure_deities_db(state)
        deity = db.get(fstate.deity_id)
        if not deity:
            return {"success": False, "reason": f"신격 [{fstate.deity_id}] 정보를 찾을 수 없습니다."}

        # Find matching miracle in deity's miracles dictionary
        miracle = deity.miracles.get(miracle_key)
        if not miracle:
            # Fallback search by name or effect_type
            for m in deity.miracles.values():
                if miracle_key.lower() in m.name.lower() or miracle_key.lower() in m.effect_type.lower():
                    miracle = m
                    break

        if not miracle:
            return {"success": False, "reason": f"해당 신격에게서 [{miracle_key}] 기적을 찾을 수 없습니다."}

        if fstate.piety < miracle.piety_cost:
            return {
                "success": False,
                "reason": f"신앙도(Piety) 부족! (필요: {miracle.piety_cost}, 현재: {fstate.piety})",
            }

        # Deduct piety
        fstate.piety -= miracle.piety_cost
        fstate.devotion_tier, _ = cls.calculate_devotion_tier(fstate.piety)

        # Execute universal miracle effect pipeline
        effect_msg = ""
        e_type = miracle.effect_type

        if e_type == "heal":
            heal_amt = int(miracle.magnitude)
            state.player.health = min(state.player.max_health, state.player.health + heal_amt)
            effect_msg = f"신성한 생명력이 혈맥을 채우며 체력 {heal_amt}를 즉시 회복했습니다! (현재 HP: {state.player.health}/{state.player.max_health})"

        elif e_type == "ward":
            fstate.active_blessings.append({
                "name": miracle.name,
                "type": "ward",
                "shield_amount": int(miracle.magnitude),
                "turns_remaining": miracle.duration_turns,
            })
            effect_msg = f"눈부신 신성 보호막이 전신을 감쌉니다! (피해 흡수: {int(miracle.magnitude)}, 지속: {miracle.duration_turns}턴)"

        elif e_type == "smite":
            smite_dmg = int(miracle.magnitude)
            effect_msg = f"하늘에서 신성한 벼락과 광휘의 창이 내리꽂혀 적에게 {smite_dmg}의 강력한 천벌 피해를 입혔습니다!"

        elif e_type == "cleanse":
            # Remove player negative status effects
            if hasattr(state.player, "active_statuses"):
                state.player.active_statuses.clear()
            fstate.active_curses.clear()
            effect_msg = f"몸을 옥죄던 모든 사악한 저주와 독소, 질병이 완벽히 정화되었습니다!"

        elif e_type == "fortune":
            fstate.active_blessings.append({
                "name": miracle.name,
                "type": "fortune",
                "turns_remaining": miracle.duration_turns,
            })
            effect_msg = f"운명의 별빛이 함께하며 모든 주사위 판정에 신의 축복이 깃듭니다! (지속: {miracle.duration_turns}턴)"

        else:
            effect_msg = f"[{miracle.name}] 기적이 시전되어 주위의 어둠을 걷어냈습니다."

        return {
            "success": True,
            "miracle_name": miracle.name,
            "piety_cost": miracle.piety_cost,
            "remaining_piety": fstate.piety,
            "effect_message": effect_msg,
            "message": f"✨ [신성 기적 발현]: [{miracle.name}]! {effect_msg} (소모 신앙도: {miracle.piety_cost})",
        }

    @classmethod
    def check_taboo_violation(cls, state: Any, action_tags: List[str]) -> Optional[Dict[str, Any]]:
        """
        Evaluates player actions against deity taboos.
        Inflicts divine retribution (curse, piety drop, heresy increase) on violation.
        """
        fstate = cls.get_faith_state(state)
        if not fstate.deity_id:
            return None

        db = cls.ensure_deities_db(state)
        deity = db.get(fstate.deity_id)
        if not deity:
            return None

        violated = []
        for tag in action_tags:
            if tag.lower() in [t.lower() for t in deity.taboos]:
                violated.append(tag)

        if not violated:
            return None

        # Inflict divine retribution
        piety_penalty = 50
        fstate.piety = max(0, fstate.piety - piety_penalty)
        fstate.heresy_level = min(100, fstate.heresy_level + 20)
        fstate.devotion_tier, _ = cls.calculate_devotion_tier(fstate.piety)

        curse_name = f"{deity.name}의 진노 (금기 위반)"
        fstate.active_curses.append({
            "name": curse_name,
            "violated_taboos": violated,
            "turns_remaining": 5,
            "penalty_desc": "체력 및 마나 재생 불가, 불운",
        })

        return {
            "violated": True,
            "deity_name": deity.name,
            "taboos": violated,
            "piety_lost": piety_penalty,
            "current_piety": fstate.piety,
            "curse_name": curse_name,
            "message": f"⚡ [신벌 발동]: 금기({', '.join(violated)})를 어겨 [{deity.name}]의 무서운 진노를 샀습니다! (신앙도 -{piety_penalty}, 신벌 저주 부여)",
        }

    @classmethod
    def advance_faith_tick(cls, state: Any) -> FaithTurnSummary:
        """
        Deterministically ticks down active blessings/curses and integrates settlement faith yields.
        """
        current_turn = getattr(state, "current_day", 1)
        fstate = cls.get_faith_state(state)
        miracles_expired: List[str] = []
        curses_expired: List[str] = []
        events: List[str] = []

        # 1. Tick Blessings
        surviving_blessings = []
        for b in fstate.active_blessings:
            b["turns_remaining"] -= 1
            if b["turns_remaining"] <= 0:
                miracles_expired.append(b["name"])
            else:
                surviving_blessings.append(b)
        fstate.active_blessings = surviving_blessings

        # 2. Tick Curses
        surviving_curses = []
        for c in fstate.active_curses:
            c["turns_remaining"] -= 1
            if c["turns_remaining"] <= 0:
                curses_expired.append(c["name"])
            else:
                surviving_curses.append(c)
        fstate.active_curses = surviving_curses

        # 3. Synchronize settlement faith yields if player has domain
        piety_delta = 0
        if hasattr(state, "pioneering_domains") and state.pioneering_domains:
            reg = getattr(state, "infrastructure", None)
            if reg and hasattr(reg, "settlements"):
                for s_id in state.pioneering_domains.keys():
                    settlement = reg.settlements.get(s_id)
                    if settlement and settlement.yields.faith > 0:
                        faith_income = max(1, int(settlement.yields.faith * 0.2))
                        fstate.piety = min(1000, fstate.piety + faith_income)
                        piety_delta += faith_income
                        events.append(f"영지 사원 신앙 유입: [{settlement.name}]의 성소에서 신앙도 +{faith_income} 축적.")

        # 4. Inquisitor alert if heresy is critical
        if fstate.heresy_level >= 75:
            events.append("⚠️ [이단 심문관 경보]: 이단도가 극에 달해 정통 교단의 처형자 순찰대가 당신의 뒤를 쫓고 있습니다!")

        fstate.devotion_tier, _ = cls.calculate_devotion_tier(fstate.piety)

        return FaithTurnSummary(
            turn=current_turn,
            piety_delta=piety_delta,
            current_piety=fstate.piety,
            miracles_triggered=miracles_expired,
            curses_triggered=curses_expired,
            events_triggered=events,
            traits=["정기정산", f"신앙도_{fstate.piety}"],
        )

    @classmethod
    def get_faith_status_summary(cls, state: Any) -> str:
        """Generates a concise Korean deterministic status briefing string."""
        fstate = cls.get_faith_state(state)
        tier_idx, tier_name = cls.calculate_devotion_tier(fstate.piety)

        blessings_str = ", ".join([f"{b['name']}({b['turns_remaining']}턴)" for b in fstate.active_blessings]) if fstate.active_blessings else "없음"
        curses_str = ", ".join([f"{c['name']}({c['turns_remaining']}턴)" for c in fstate.active_curses]) if fstate.active_curses else "없음"

        db = cls.ensure_deities_db(state)
        deity = db.get(fstate.deity_id) if fstate.deity_id else None
        miracles_str = ", ".join([m.name for m in deity.miracles.values()]) if deity else "없음"

        lines = [
            f"=== 🕊️ 종교 신앙 브리핑: {fstate.deity_name} ===",
            f"- 신심 등급: {tier_name} (제{tier_idx}위계)",
            f"- 신앙도(Piety): {fstate.piety} / 1000 P | 이단도: {fstate.heresy_level}/100",
            f"- 누적 기도: {fstate.prayers_count}회 | 제단 공물: {fstate.sacrifices_count}회",
            f"- 사용 가능 기적: {miracles_str}",
            f"- 활성 신성 가호: {blessings_str}",
            f"- 신벌 저주 상태: {curses_str}",
        ]
        return "\n".join(lines)
