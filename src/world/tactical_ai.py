"""
Monster Tactical AI / Behavior Tree Engine for Quilltale TRPG.
Deterministic FSM/Behavior-Tree-based tactical decision engine for hostile NPCs:
1. Self-Preservation & Call for Help (HP ≤ 25%, courage < 40 → flee/heal/call_help)
2. Ranged Kiting & Tank Cover (archer/mage archetype → move_away, take_cover behind melee ally)
3. Exploit Vulnerability (player stunned/bleeding/blinded → crit-boosted focus fire)
4. Vanguard Guard & Intercept (tank/shieldbearer → shield wall / intercept for wounded ally)
5. Standard Fallback (default skill/melee attack)

Pure Python, 0-token, 0-GPU, 100% deterministic.
"""
import logging
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from src.world.state import WorldState, NPC
from src.world.status_engine import StatusEffectEngine

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 1. Tactical Archetype Classification
# ──────────────────────────────────────────────

class TacticalArchetype(Enum):
    """NPC tactical role classification based on job, skills, and equipment."""
    ARCHER_MAGE = "archer_mage"           # 궁수/마법사/투척수 — 원거리 카이팅, 거리 벌리기
    VANGUARD_TANK = "vanguard_tank"       # 방패병/수호자/탱커 — 아군 보호, 경로 차단
    BERSERKER_BRUTE = "berserker_brute"   # 광전사/맹수/광폭화 — 체력 낮아도 돌진
    COWARD_MINION = "coward_minion"       # 비열한 부하/졸개 — 도주 우선, 지원 요청
    SKIRMISHER = "skirmisher"             # 척후병/암살자/도적 — 취약점 급소 점사
    GENERALIST = "generalist"             # 기본 전투 패턴


# Job/keyword → archetype mapping tables
_ARCHER_MAGE_KEYWORDS = frozenset([
    "궁수", "마법사", "사수", "저격", "원거리", "투척", "주술사", "치유사", "힐러",
    "archer", "mage", "wizard", "ranged", "caster", "shaman", "healer",
])
_VANGUARD_TANK_KEYWORDS = frozenset([
    "방패", "수호자", "탱커", "경비", "기사", "중갑", "전위", "파수꾼",
    "guardian", "tank", "shield", "knight", "sentinel", "vanguard",
])
_BERSERKER_BRUTE_KEYWORDS = frozenset([
    "광전사", "맹수", "버서커", "야수", "광폭", "거인", "트롤", "오우거",
    "berserker", "brute", "beast", "ogre", "troll",
])
_COWARD_MINION_KEYWORDS = frozenset([
    "졸개", "고블린", "하수인", "부하", "도망자", "겁쟁이", "약탈자", "쥐",
    "minion", "goblin", "coward", "lackey", "rat",
])
_SKIRMISHER_KEYWORDS = frozenset([
    "척후", "암살자", "도적", "살수", "자객", "독사", "그림자", "레인저",
    "assassin", "rogue", "scout", "shadow", "ranger", "stalker",
])


# ──────────────────────────────────────────────
# 2. Tactical Decision Result
# ──────────────────────────────────────────────

@dataclass
class TacticalDecision:
    """Result of the behavior tree evaluation for a single NPC turn."""
    action_type: str       # flee, call_help, kite_away, take_cover, exploit_status,
                           # guard_ally, heal_self, skill_attack, melee_attack, cc_stunned
    npc_id: str
    npc_name: str
    summary_ko: str
    damage: int = 0
    is_success: bool = True
    extra: Dict[str, Any] = field(default_factory=dict)
    traits: List[str] = field(default_factory=list)


# ──────────────────────────────────────────────
# 3. Monster Tactics Engine (Behavior Tree)
# ──────────────────────────────────────────────

# Exploitable debuffs that trigger focus fire
_EXPLOITABLE_STATUSES = frozenset([
    "stun", "sleep", "freeze", "bleed", "blind", "paralysis",
    "기절", "수면", "빙결", "출혈", "실명", "마비",
])


class MonsterTacticsEngine:
    """
    Behavior-tree-based tactical AI for hostile NPCs.
    Evaluation order (priority):
      0. CC check (stunned/paralyzed → skip turn)
      1. Self-Preservation (HP ≤ 25% → flee / call_help / heal_self)
      2. Ranged Kiting (ARCHER_MAGE near melee → move_away / take_cover)
      3. Exploit Vulnerability (player debuffed → focus fire with crit bonus)
      4. Vanguard Guard (VANGUARD_TANK → intercept / shield ally)
      5. Standard Attack (fallback → delegate to NPCSkillEngine)
    """

    # ── Archetype classification ──

    @classmethod
    def determine_archetype(cls, npc: NPC) -> TacticalArchetype:
        """Classify NPC into a tactical archetype based on job, skills, traits, and preferred_tactics."""
        job_lower = npc.job.lower()
        tactics_lower = getattr(npc.combat_profile, "preferred_tactics", "").lower()
        npc_traits = [t.lower() for t in getattr(npc, "traits", [])]
        combined = f"{job_lower} {tactics_lower} {' '.join(npc_traits)}"

        if any(kw in combined for kw in _BERSERKER_BRUTE_KEYWORDS):
            return TacticalArchetype.BERSERKER_BRUTE
        if any(kw in combined for kw in _ARCHER_MAGE_KEYWORDS):
            return TacticalArchetype.ARCHER_MAGE
        if any(kw in combined for kw in _VANGUARD_TANK_KEYWORDS):
            return TacticalArchetype.VANGUARD_TANK
        if any(kw in combined for kw in _SKIRMISHER_KEYWORDS):
            return TacticalArchetype.SKIRMISHER
        if any(kw in combined for kw in _COWARD_MINION_KEYWORDS):
            return TacticalArchetype.COWARD_MINION

        # Fallback heuristic: low courage + low HP → coward; high aggression → berserker
        courage = getattr(npc.personality, "courage", 50)
        aggression = getattr(npc.personality, "aggression", 50)
        if courage < 30:
            return TacticalArchetype.COWARD_MINION
        if aggression >= 80:
            return TacticalArchetype.BERSERKER_BRUTE

        return TacticalArchetype.GENERALIST

    # ── Main behavior tree entry ──

    @classmethod
    def evaluate_tactical_turn(
        cls,
        npc: NPC,
        state: WorldState,
        player_ac: int = 10,
    ) -> Optional[TacticalDecision]:
        """
        Top-level behavior tree evaluation.
        Returns a TacticalDecision if a *tactical* action (non-standard) was chosen,
        or None if the NPC should fall through to the standard NPCSkillEngine attack.
        """
        if not npc.alive or npc.disposition != "hostile":
            return None

        # Node 0: CC check — stunned/paralyzed → forced skip
        if StatusEffectEngine.has_status(npc, "stun") or StatusEffectEngine.has_status(npc, "paralysis"):
            return TacticalDecision(
                action_type="cc_stunned",
                npc_id=npc.id,
                npc_name=npc.name,
                summary_ko=f"[{npc.name}]은(는) 기절/마비 상태로 인해 이번 턴에 행동할 수 없습니다.",
                damage=0,
                is_success=False,
                traits=["tactical_ai", "cc_blocked"],
            )

        archetype = cls.determine_archetype(npc)

        # Node 1: Self-Preservation (HP ≤ 25%)
        decision = cls._node_self_preservation(npc, state, archetype)
        if decision is not None:
            return decision

        # Node 2: Ranged Kiting (archer/mage too close)
        decision = cls._node_ranged_kiting(npc, state, archetype)
        if decision is not None:
            return decision

        # Node 3: Exploit Vulnerability (player debuffed)
        decision = cls._node_exploit_vulnerability(npc, state, archetype, player_ac)
        if decision is not None:
            return decision

        # Node 4: Vanguard Guard (tank protect wounded ally)
        decision = cls._node_vanguard_guard(npc, state, archetype)
        if decision is not None:
            return decision

        # Node 5: Standard Attack → return None to delegate to NPCSkillEngine
        return None

    # ── Node 1: Self-Preservation ──

    @classmethod
    def _node_self_preservation(
        cls, npc: NPC, state: WorldState, archetype: TacticalArchetype
    ) -> Optional[TacticalDecision]:
        """HP ≤ 25% → flee / call_help / heal_self. Berserkers refuse to flee."""
        max_hp = max(npc.max_health, 1)
        hp_ratio = npc.health / max_hp

        if hp_ratio > 0.25:
            return None

        # Berserkers never flee — they rage instead
        if archetype == TacticalArchetype.BERSERKER_BRUTE:
            return TacticalDecision(
                action_type="berserker_rage",
                npc_id=npc.id,
                npc_name=npc.name,
                summary_ko=(
                    f"[{npc.name}]의 눈이 핏빛으로 물듭니다! "
                    f"치명상에도 불구하고 광전사의 광폭화가 발동하여 공격력이 50% 증가합니다! "
                    f"(체력: {npc.health}/{max_hp})"
                ),
                damage=0,
                is_success=True,
                extra={"rage_bonus_pct": 50},
                traits=["tactical_ai", "berserker_rage", "self_preservation"],
            )

        courage = getattr(npc.personality, "courage", 50)

        # Try self-heal first: check if NPC has a healing consumable
        heal_decision = cls._try_heal_self(npc, state)
        if heal_decision is not None:
            return heal_decision

        # Call for help: allies present in same location?
        curr_loc = state.current_location()
        allies_present: List[NPC] = []
        if curr_loc:
            for loc_npc in state.npcs_in_location(curr_loc.id):
                if loc_npc.id != npc.id and loc_npc.alive and loc_npc.disposition == "hostile":
                    allies_present.append(loc_npc)

        if allies_present and courage < 60:
            ally_names = ", ".join(a.name for a in allies_present[:3])
            return TacticalDecision(
                action_type="call_help",
                npc_id=npc.id,
                npc_name=npc.name,
                summary_ko=(
                    f"[{npc.name}]이(가) 비명을 지르며 동료들에게 지원을 요청합니다! "
                    f"\"도와줘!\" (동료: {ally_names}) (체력: {npc.health}/{max_hp})"
                ),
                damage=0,
                is_success=True,
                extra={"ally_ids": [a.id for a in allies_present[:3]]},
                traits=["tactical_ai", "call_help", "self_preservation"],
            )

        # Flee attempt (courage < 40 or coward minion)
        if courage < 40 or archetype == TacticalArchetype.COWARD_MINION:
            # Attempt to increase distance via CombatDistanceManager
            flee_distance = 0.0
            try:
                from src.world.combat_time_track_engine import CombatDistanceManager
                from src.world.stat_engine import StatEngine
                speed_mps = StatEngine.sprint_speed(npc.agility)
                flee_distance = CombatDistanceManager.move_away(
                    state, npc.id, "player", speed_mps=speed_mps, seconds=3.0
                )
            except Exception:
                flee_distance = 15.0  # fallback estimate

            return TacticalDecision(
                action_type="flee",
                npc_id=npc.id,
                npc_name=npc.name,
                summary_ko=(
                    f"[{npc.name}]이(가) 공포에 질려 전투에서 이탈을 시도합니다! "
                    f"뒤도 돌아보지 않고 필사적으로 도주합니다. "
                    f"(체력: {npc.health}/{max_hp}, 이탈 거리: {flee_distance:.1f}m)"
                ),
                damage=0,
                is_success=True,
                extra={"flee_distance_m": flee_distance},
                traits=["tactical_ai", "flee", "self_preservation"],
            )

        return None

    @classmethod
    def _try_heal_self(cls, npc: NPC, state: WorldState) -> Optional[TacticalDecision]:
        """Check NPC inventory for a healing consumable and use it."""
        for item_id in list(npc.inventory):
            item = state.items.get(item_id)
            if not item:
                continue
            item_name_lower = item.name.lower()
            item_type = getattr(item, "item_type", "")
            item_traits = [t.lower() for t in getattr(item, "traits", [])]
            is_heal = (
                item_type == "consumable"
                and any(kw in item_name_lower or kw in " ".join(item_traits) for kw in [
                    "치유", "회복", "포션", "체력", "heal", "potion", "health", "bandage", "붕대",
                ])
            )
            if is_heal:
                heal_amount = getattr(item, "value", 0) or getattr(item, "base_value", 0) or getattr(item, "heal_amount", 20)
                if heal_amount <= 0:
                    heal_amount = 20
                hp_before = npc.health
                npc.health = min(npc.max_health, npc.health + heal_amount)
                hp_after = npc.health
                # Consume the item
                npc.inventory.remove(item_id)
                return TacticalDecision(
                    action_type="heal_self",
                    npc_id=npc.id,
                    npc_name=npc.name,
                    summary_ko=(
                        f"[{npc.name}]이(가) [{item.name}]을(를) 꺼내 급히 들이킵니다! "
                        f"체력이 {heal_amount}만큼 회복됩니다. "
                        f"(체력: {hp_before} → {hp_after}/{npc.max_health})"
                    ),
                    damage=0,
                    is_success=True,
                    extra={"healed": heal_amount, "item_used": item.name},
                    traits=["tactical_ai", "heal_self", "self_preservation"],
                )
        return None

    # ── Node 2: Ranged Kiting ──

    @classmethod
    def _node_ranged_kiting(
        cls, npc: NPC, state: WorldState, archetype: TacticalArchetype
    ) -> Optional[TacticalDecision]:
        """Archer/mage kites away when player is too close (≤ 8m)."""
        if archetype != TacticalArchetype.ARCHER_MAGE:
            return None

        try:
            from src.world.combat_time_track_engine import CombatDistanceManager
            distance = CombatDistanceManager.get_distance(state, npc.id, "player", default=15.0)
        except Exception:
            return None

        if distance > 8.0:
            return None  # Already at safe range

        # Check if there's a melee ally to hide behind
        curr_loc = state.current_location()
        cover_ally: Optional[NPC] = None
        if curr_loc:
            for loc_npc in state.npcs_in_location(curr_loc.id):
                if loc_npc.id == npc.id or not loc_npc.alive or loc_npc.disposition != "hostile":
                    continue
                ally_archetype = cls.determine_archetype(loc_npc)
                if ally_archetype in (TacticalArchetype.VANGUARD_TANK, TacticalArchetype.BERSERKER_BRUTE, TacticalArchetype.GENERALIST):
                    cover_ally = loc_npc
                    break

        if cover_ally:
            return TacticalDecision(
                action_type="take_cover",
                npc_id=npc.id,
                npc_name=npc.name,
                summary_ko=(
                    f"[{npc.name}]이(가) 아군 [{cover_ally.name}]의 등 뒤로 재빠르게 엄폐합니다! "
                    f"회피 보너스 +2 획득. (현재 교전 거리: {distance:.1f}m)"
                ),
                damage=0,
                is_success=True,
                extra={"cover_ally_id": cover_ally.id, "evasion_bonus": 2},
                traits=["tactical_ai", "take_cover", "ranged_kiting"],
            )
        else:
            # No cover ally → kite away
            try:
                from src.world.stat_engine import StatEngine
                speed_mps = StatEngine.sprint_speed(npc.agility)
            except Exception:
                speed_mps = 5.0
            try:
                from src.world.combat_time_track_engine import CombatDistanceManager
                new_dist = CombatDistanceManager.move_away(
                    state, npc.id, "player", speed_mps=speed_mps, seconds=2.0
                )
            except Exception:
                new_dist = distance + 10.0

            return TacticalDecision(
                action_type="kite_away",
                npc_id=npc.id,
                npc_name=npc.name,
                summary_ko=(
                    f"[{npc.name}]이(가) 플레이어로부터 거리를 벌리며 후퇴합니다! "
                    f"({distance:.1f}m → {new_dist:.1f}m)"
                ),
                damage=0,
                is_success=True,
                extra={"distance_before": distance, "distance_after": new_dist},
                traits=["tactical_ai", "kite_away", "ranged_kiting"],
            )

    # ── Node 3: Exploit Vulnerability ──

    @classmethod
    def _node_exploit_vulnerability(
        cls, npc: NPC, state: WorldState, archetype: TacticalArchetype, player_ac: int
    ) -> Optional[TacticalDecision]:
        """Player has exploitable debuff → crit-boosted focus fire."""
        player = state.player

        # Detect active debuffs on the player
        active_debuffs: List[str] = []
        if hasattr(player, "status_effects") and player.status_effects:
            for s_id, s_obj in player.status_effects.items():
                if getattr(s_obj, "duration_turns", 0) > 0:
                    if s_id in _EXPLOITABLE_STATUSES or getattr(s_obj, "id", "") in _EXPLOITABLE_STATUSES:
                        active_debuffs.append(s_id)

        if not active_debuffs:
            return None

        # Skirmishers get the strongest bonus; others still exploit but less
        crit_bonus = 30 if archetype == TacticalArchetype.SKIRMISHER else 15
        penetration_bonus = 20 if archetype == TacticalArchetype.SKIRMISHER else 10

        from src.world.dice import DiceEngine

        # Roll d20 for hit
        d20 = DiceEngine.roll_d20()
        stat_val = max(npc.strength, npc.agility)  # use best physical stat
        modifier = DiceEngine.stat_modifier(stat_val)
        total_hit = d20 + modifier
        is_hit = (total_hit >= player_ac) or (d20 == 20)

        if not is_hit and d20 != 1:
            debuff_names = ", ".join(active_debuffs[:3])
            return TacticalDecision(
                action_type="exploit_status_miss",
                npc_id=npc.id,
                npc_name=npc.name,
                summary_ko=(
                    f"[{npc.name}]이(가) [{debuff_names}] 상태의 플레이어 급소를 노리지만 빗나갑니다! "
                    f"(판정: {total_hit} vs AC {player_ac})"
                ),
                damage=0,
                is_success=False,
                extra={"exploited_debuffs": active_debuffs, "crit_bonus": crit_bonus},
                traits=["tactical_ai", "exploit_vulnerability", "miss"],
            )

        # Calculate boosted damage
        base_dmg = max(npc.strength, 5)
        calculated_dmg = DiceEngine.calculate_skill_damage(
            base_damage=base_dmg,
            stat_value=stat_val,
            scaling=1.2,
            target_defense=max(0, (player_ac - 10) // 2),
        )
        # Apply crit bonus
        is_crit = (d20 == 20) or (random.randint(1, 100) <= crit_bonus + getattr(npc, "crit_rate_bonus", 0))
        if is_crit:
            calculated_dmg = int(calculated_dmg * 1.5)

        # Apply armor mitigation
        from src.world.equipment import EquipmentEngine
        mitigated_dmg, armor_logs = EquipmentEngine.apply_armor_durability_and_mitigation(
            state, player, calculated_dmg, target_part=""
        )

        hp_before = player.health
        player.health = max(0, player.health - mitigated_dmg)
        hp_after = player.health

        debuff_names = ", ".join(active_debuffs[:3])
        crit_text = " **치명타!**" if is_crit else ""
        return TacticalDecision(
            action_type="exploit_status",
            npc_id=npc.id,
            npc_name=npc.name,
            summary_ko=(
                f"[{npc.name}]이(가) [{debuff_names}] 상태의 플레이어 급소를 무자비하게 점사합니다!{crit_text} "
                f"{mitigated_dmg} 피해 적중! (체력: {hp_before} → {hp_after}/{state.player.max_health})"
            ),
            damage=mitigated_dmg,
            is_success=True,
            extra={
                "exploited_debuffs": active_debuffs,
                "crit_bonus": crit_bonus,
                "is_crit": is_crit,
                "penetration_bonus": penetration_bonus,
                "d20_roll": d20,
                "player_hp_before": hp_before,
                "player_hp_after": hp_after,
            },
            traits=["tactical_ai", "exploit_vulnerability", "focus_fire"],
        )

    # ── Node 4: Vanguard Guard ──

    @classmethod
    def _node_vanguard_guard(
        cls, npc: NPC, state: WorldState, archetype: TacticalArchetype
    ) -> Optional[TacticalDecision]:
        """Tank/vanguard interposes to protect a wounded or ranged ally."""
        if archetype != TacticalArchetype.VANGUARD_TANK:
            return None

        curr_loc = state.current_location()
        if not curr_loc:
            return None

        # Find a wounded or ranged ally that needs protection
        ward_target: Optional[NPC] = None
        for loc_npc in state.npcs_in_location(curr_loc.id):
            if loc_npc.id == npc.id or not loc_npc.alive or loc_npc.disposition != "hostile":
                continue
            ally_hp_ratio = loc_npc.health / max(loc_npc.max_health, 1)
            ally_archetype = cls.determine_archetype(loc_npc)
            if ally_hp_ratio <= 0.30 or ally_archetype == TacticalArchetype.ARCHER_MAGE:
                ward_target = loc_npc
                break

        if ward_target is None:
            return None

        return TacticalDecision(
            action_type="guard_ally",
            npc_id=npc.id,
            npc_name=npc.name,
            summary_ko=(
                f"[{npc.name}]이(가) 방패를 들어올리며 [{ward_target.name}]을(를) 보호하는 방어 태세를 취합니다! "
                f"플레이어의 [{ward_target.name}] 공격 시 [{npc.name}]이(가) 대신 피격됩니다. "
                f"(방어 보너스: AC +2)"
            ),
            damage=0,
            is_success=True,
            extra={"ward_target_id": ward_target.id, "ac_bonus": 2},
            traits=["tactical_ai", "guard_ally", "vanguard_intercept"],
        )
