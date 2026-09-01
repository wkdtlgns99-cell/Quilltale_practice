"""
Deterministic Party & Companion Management Engine for Quilltale TRPG.
Handles recruitment, companion independent AI combat turns, formation,
loyalty/betrayal thresholds, bond milestones, camp roles, and combo techniques.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
import copy

from src.core.config import TEMPLATES_DIR
from src.world.dice import DiceEngine


@dataclass
class CompanionStats:
    level: int = 10
    health: int = 100
    max_health: int = 100
    mana: int = 40
    max_mana: int = 40
    strength: int = 10
    agility: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    luck: int = 10
    defense: int = 10
    attack_power: int = 20

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "health": self.health,
            "max_health": self.max_health,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "strength": self.strength,
            "agility": self.agility,
            "constitution": self.constitution,
            "intelligence": self.intelligence,
            "wisdom": self.wisdom,
            "luck": self.luck,
            "defense": self.defense,
            "attack_power": self.attack_power,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CompanionStats":
        return cls(
            level=int(data.get("level", 10)),
            health=int(data.get("health", 100)),
            max_health=int(data.get("max_health", 100)),
            mana=int(data.get("mana", 40)),
            max_mana=int(data.get("max_mana", 40)),
            strength=int(data.get("strength", 10)),
            agility=int(data.get("agility", 10)),
            constitution=int(data.get("constitution", 10)),
            intelligence=int(data.get("intelligence", 10)),
            wisdom=int(data.get("wisdom", 10)),
            luck=int(data.get("luck", 10)),
            defense=int(data.get("defense", 10)),
            attack_power=int(data.get("attack_power", 20)),
        )


@dataclass
class CompanionSkill:
    skill_id: str
    name_ko: str
    mana_cost: int = 10
    cooldown_turns: int = 2
    current_cooldown: int = 0
    effect_type: str = "damage"
    description_ko: str = ""

    def to_dict(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "name_ko": self.name_ko,
            "mana_cost": self.mana_cost,
            "cooldown_turns": self.cooldown_turns,
            "current_cooldown": self.current_cooldown,
            "effect_type": self.effect_type,
            "description_ko": self.description_ko,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CompanionSkill":
        return cls(
            skill_id=str(data.get("skill_id", "")),
            name_ko=str(data.get("name_ko", "")),
            mana_cost=int(data.get("mana_cost", 10)),
            cooldown_turns=int(data.get("cooldown_turns", 2)),
            current_cooldown=int(data.get("current_cooldown", 0)),
            effect_type=str(data.get("effect_type", "damage")),
            description_ko=str(data.get("description_ko", "")),
        )


@dataclass
class CompanionUltimate:
    skill_id: str
    name_ko: str
    charge_type: str = "damage_accumulated"
    charge_required: int = 100
    current_charge: int = 0
    mana_cost: int = 25
    activation_voice_line: str = ""
    effects: Dict[str, Any] = field(default_factory=dict)
    cinematic_description: str = ""

    def to_dict(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "name_ko": self.name_ko,
            "charge_type": self.charge_type,
            "charge_required": self.charge_required,
            "current_charge": self.current_charge,
            "mana_cost": self.mana_cost,
            "activation_voice_line": self.activation_voice_line,
            "effects": self.effects,
            "cinematic_description": self.cinematic_description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CompanionUltimate":
        return cls(
            skill_id=str(data.get("skill_id", "")),
            name_ko=str(data.get("name_ko", "궁극기")),
            charge_type=str(data.get("charge_type", "damage_accumulated")),
            charge_required=int(data.get("charge_required", 100)),
            current_charge=int(data.get("current_charge", 0)),
            mana_cost=int(data.get("mana_cost", 25)),
            activation_voice_line=str(data.get("activation_voice_line", "")),
            effects=dict(data.get("effects", {})),
            cinematic_description=str(data.get("cinematic_description", "")),
        )


@dataclass
class CompanionBond:
    tier: int = 1
    current_points: int = 10
    tier_bonuses: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "current_points": self.current_points,
            "tier_bonuses": self.tier_bonuses,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CompanionBond":
        return cls(
            tier=int(data.get("tier", 1)),
            current_points=int(data.get("current_points", 10)),
            tier_bonuses=dict(data.get("tier_bonuses", {})),
        )


@dataclass
class CompanionDownedState:
    is_downed: bool = False
    death_saving_turns: int = 3
    downed_cry: str = ""
    death_trauma_to_party: str = ""

    def to_dict(self) -> dict:
        return {
            "is_downed": self.is_downed,
            "death_saving_turns": self.death_saving_turns,
            "downed_cry": self.downed_cry,
            "death_trauma_to_party": self.death_trauma_to_party,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CompanionDownedState":
        return cls(
            is_downed=bool(data.get("is_downed", False)),
            death_saving_turns=int(data.get("death_saving_turns", 3)),
            downed_cry=str(data.get("downed_cry", "")),
            death_trauma_to_party=str(data.get("death_trauma_to_party", "")),
        )


@dataclass
class Companion:
    companion_id: str
    name_ko: str
    title_ko: str
    role: str = "tank"                     # tank | dps_melee | dps_ranged | healer_support | arcane_blaster | scout_rogue
    formation: str = "frontline"           # frontline | midline | backline
    speech_style: str = "rough_mercenary"  # rough_mercenary | archaic_noble | stoic_veteran | timid_scholar | whimsical_trickster
    stats: CompanionStats = field(default_factory=CompanionStats)
    personality: Dict[str, Any] = field(default_factory=dict)
    moral_branching: Dict[str, Any] = field(default_factory=dict)
    phobias_and_flaws: Dict[str, Any] = field(default_factory=dict)
    base_dispatch_mission: Dict[str, Any] = field(default_factory=dict)
    ai_tactical_priority: Dict[str, Any] = field(default_factory=dict)
    inventory_quirks: Dict[str, Any] = field(default_factory=dict)
    exclusive_bond_pact: Dict[str, Any] = field(default_factory=dict)
    bond: CompanionBond = field(default_factory=CompanionBond)
    recruitment: Dict[str, Any] = field(default_factory=dict)
    loot_demands: Dict[str, Any] = field(default_factory=dict)
    camp_role: str = "scout"               # cook | scout | medic | scholar | blacksmith
    exploration_talents: List[str] = field(default_factory=list)
    companion_relations: Dict[str, Any] = field(default_factory=dict)
    combat_skills: List[CompanionSkill] = field(default_factory=list)
    combo_technique: Dict[str, Any] = field(default_factory=dict)
    ultimate_ability: Optional[CompanionUltimate] = None
    party_passive: Dict[str, Any] = field(default_factory=dict)
    equipment: Dict[str, str] = field(default_factory=dict)
    downed_state: CompanionDownedState = field(default_factory=CompanionDownedState)
    dialogue_lines: Dict[str, str] = field(default_factory=dict)
    is_active_party: bool = True

    def to_dict(self) -> dict:
        return {
            "companion_id": self.companion_id,
            "name_ko": self.name_ko,
            "title_ko": self.title_ko,
            "role": self.role,
            "formation": self.formation,
            "speech_style": self.speech_style,
            "stats": self.stats.to_dict(),
            "personality": self.personality,
            "moral_branching": self.moral_branching,
            "phobias_and_flaws": self.phobias_and_flaws,
            "base_dispatch_mission": self.base_dispatch_mission,
            "ai_tactical_priority": self.ai_tactical_priority,
            "inventory_quirks": self.inventory_quirks,
            "exclusive_bond_pact": self.exclusive_bond_pact,
            "bond": self.bond.to_dict(),
            "recruitment": self.recruitment,
            "loot_demands": self.loot_demands,
            "camp_role": self.camp_role,
            "exploration_talents": self.exploration_talents,
            "companion_relations": self.companion_relations,
            "combat_skills": [s.to_dict() for s in self.combat_skills],
            "combo_technique": self.combo_technique,
            "ultimate_ability": self.ultimate_ability.to_dict() if self.ultimate_ability else None,
            "party_passive": self.party_passive,
            "equipment": self.equipment,
            "downed_state": self.downed_state.to_dict(),
            "dialogue_lines": self.dialogue_lines,
            "is_active_party": self.is_active_party,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Companion":
        skills = [CompanionSkill.from_dict(s) for s in data.get("combat_skills", []) if isinstance(s, dict)]
        ult_data = data.get("ultimate_ability")
        ult = CompanionUltimate.from_dict(ult_data) if isinstance(ult_data, dict) else None
        stats_obj = CompanionStats.from_dict(data.get("stats", {})) if isinstance(data.get("stats"), dict) else CompanionStats()
        bond_obj = CompanionBond.from_dict(data.get("bond", {})) if isinstance(data.get("bond"), dict) else CompanionBond()
        downed_obj = CompanionDownedState.from_dict(data.get("downed_state", {})) if isinstance(data.get("downed_state"), dict) else CompanionDownedState()

        return cls(
            companion_id=str(data.get("companion_id", "")),
            name_ko=str(data.get("name_ko", "이름 모를 동료")),
            title_ko=str(data.get("title_ko", "방랑자")),
            role=str(data.get("role", "tank")),
            formation=str(data.get("formation", "frontline")),
            speech_style=str(data.get("speech_style", "rough_mercenary")),
            stats=stats_obj,
            personality=dict(data.get("personality", {})),
            moral_branching=dict(data.get("moral_branching", {})),
            phobias_and_flaws=dict(data.get("phobias_and_flaws", {})),
            base_dispatch_mission=dict(data.get("base_dispatch_mission", {})),
            ai_tactical_priority=dict(data.get("ai_tactical_priority", {})),
            inventory_quirks=dict(data.get("inventory_quirks", {})),
            exclusive_bond_pact=dict(data.get("exclusive_bond_pact", {})),
            bond=bond_obj,
            recruitment=dict(data.get("recruitment", {})),
            loot_demands=dict(data.get("loot_demands", {})),
            camp_role=str(data.get("camp_role", "scout")),
            exploration_talents=list(data.get("exploration_talents", [])),
            companion_relations=dict(data.get("companion_relations", {})),
            combat_skills=skills,
            combo_technique=dict(data.get("combo_technique", {})),
            ultimate_ability=ult,
            party_passive=dict(data.get("party_passive", {})),
            equipment=dict(data.get("equipment", {})),
            downed_state=downed_obj,
            dialogue_lines=dict(data.get("dialogue_lines", {})),
            is_active_party=bool(data.get("is_active_party", True)),
        )


class PartyEngine:
    """
    Pure Python Deterministic Party Management Engine.
    Executes recruitment, dismissal, autonomous companion combat actions,
    cooldown management, loyalty / betrayal thresholds, camp bonuses, and combo attacks.
    """

    MAX_PARTY_COMPANIONS = 3
    _templates_cache: Optional[Dict[str, Companion]] = None

    @classmethod
    def load_templates(cls, path: Optional[Path] = None) -> Dict[str, Companion]:
        """Loads companion definitions from companion_templates.json."""
        target_path = path or (TEMPLATES_DIR / "companion_templates.json")
        if not target_path.exists():
            return {}

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                raw_list = json.load(f)
            comps = {}
            for c_data in raw_list:
                c = Companion.from_dict(c_data)
                if c.companion_id:
                    comps[c.companion_id] = c
            cls._templates_cache = comps
            return comps
        except Exception:
            return {}

    @classmethod
    def get_companion_template(cls, companion_id: str) -> Optional[Companion]:
        if cls._templates_cache is None:
            cls.load_templates()
        if cls._templates_cache and companion_id in cls._templates_cache:
            return copy.deepcopy(cls._templates_cache[companion_id])
        return None

    @classmethod
    def recruit_companion(cls, state: Any, companion_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Recruits a companion into player party if conditions are met."""
        if not hasattr(state, "party"):
            state.party = {}

        if companion_id in state.party:
            return False, f"이미 파티에 합류한 동료입니다: [{state.party[companion_id].name_ko}]", {}

        active_count = len([c for c in state.party.values() if c.is_active_party])
        if active_count >= cls.MAX_PARTY_COMPANIONS:
            return False, f"파티 인원이 가득 찼습니다 (최대 동료 {cls.MAX_PARTY_COMPANIONS}명).", {}

        comp = cls.get_companion_template(companion_id)
        if not comp:
            return False, f"동료 정보를 찾을 수 없습니다: {companion_id}", {}

        # Check recruitment cost & requirements
        rec = comp.recruitment
        cost = rec.get("hire_cost_gold", 0)
        if state.player.gold < cost:
            return False, f"고용 비용 부족 (필요: {cost}G, 보유: {state.player.gold}G)", {}

        # Deduct gold
        if cost > 0:
            state.player.gold -= cost

        state.party[companion_id] = comp
        dialogue = rec.get("dialogue_recruit", comp.dialogue_lines.get("greeting", "함께 가겠습니다."))
        msg = f"🤝 **[새로운 동료 합류!]** [{comp.name_ko} ({comp.title_ko})]가 파티에 합류했습니다!\n- 대사: \"{dialogue}\""
        return True, msg, {"companion": comp.to_dict()}

    @classmethod
    def dismiss_companion(cls, state: Any, companion_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Dismisses a companion from the party."""
        if not hasattr(state, "party") or companion_id not in state.party:
            return False, "파티에 해당 동료가 존재하지 않습니다.", {}

        comp = state.party[companion_id]
        dialogue = comp.dialogue_lines.get("dismissal", "인연이 닿는다면 다시 뵙지요.")
        del state.party[companion_id]

        msg = f"👋 **[동료 파티 탈퇴]** [{comp.name_ko}]이(가) 파티를 떠났습니다.\n- 마지막 한마디: \"{dialogue}\""
        return True, msg, {"dismissed_id": companion_id}

    @classmethod
    def modify_loyalty_and_affinity(
        cls,
        state: Any,
        companion_id: str,
        loyalty_delta: int,
        affinity_delta: int = 0,
        reason: str = ""
    ) -> Tuple[str, bool]:
        """
        Modifies companion loyalty & affinity. Triggers betrayal or desertion if loyalty <= 0!
        Returns (log_message, is_betrayed_or_deserted).
        """
        if not hasattr(state, "party") or companion_id not in state.party:
            return "", False

        comp = state.party[companion_id]
        curr_loyalty = comp.personality.get("loyalty_score", 50) + loyalty_delta
        curr_loyalty = max(0, min(100, curr_loyalty))
        comp.personality["loyalty_score"] = curr_loyalty

        curr_aff = comp.personality.get("affinity", 0) + affinity_delta
        curr_aff = max(-100, min(100, curr_aff))
        comp.personality["affinity"] = curr_aff

        # Check Bond Tier progression
        bond = comp.bond
        bond.current_points = max(0, bond.current_points + max(0, loyalty_delta))
        if bond.current_points >= 40 and bond.tier < 2:
            bond.tier = 2
        elif bond.current_points >= 70 and bond.tier < 3:
            bond.tier = 3
        elif bond.current_points >= 100 and bond.tier < 4:
            bond.tier = 4

        # Desertion / Betrayal Trigger
        if curr_loyalty <= 0:
            betrayal_text = comp.dialogue_lines.get("traitor_reveal", "더 이상 당신과 함께할 이유가 없습니다. 여기서 끝냅시다!")
            del state.party[companion_id]
            log = f"⚠️💥 **[동료 충성도 붕괴 및 파티 이탈!]** [{comp.name_ko}]의 충성도가 바닥나 파티를 배신하고 떠났습니다!\n- 외침: \"{betrayal_text}\""
            return log, True

        log_lines = []
        if loyalty_delta != 0:
            change_sym = f"+{loyalty_delta}" if loyalty_delta > 0 else f"{loyalty_delta}"
            log_lines.append(f"⚖️ [{comp.name_ko}] 충성도 {change_sym} (현재: {curr_loyalty}/100) {f'[{reason}]' if reason else ''}")
        if curr_loyalty <= 20 and loyalty_delta < 0:
            warn = comp.dialogue_lines.get("low_loyalty_warning", "당신의 행동이 선을 넘고 있습니다.")
            log_lines.append(f"⚡ [동료 경고] \"{warn}\"")

        return "\n".join(log_lines), False

    @classmethod
    def process_companion_combat_turns(
        cls,
        state: Any,
        target_npc: Optional[Any] = None
    ) -> List[str]:
        """
        Autonomous deterministic combat resolution for all active companions in party.
        Executes skills, ultimate abilities, damage, and tactical heals.
        """
        if not hasattr(state, "party") or not state.party:
            return []

        combat_logs: List[str] = []

        for comp_id, comp in state.party.items():
            if not comp.is_active_party or comp.downed_state.is_downed:
                continue

            # 1. Tick Cooldowns
            for skill in comp.combat_skills:
                if skill.current_cooldown > 0:
                    skill.current_cooldown -= 1

            # 2. Check Ultimate Ability Ready
            ult = comp.ultimate_ability
            if ult and ult.current_charge >= ult.charge_required and comp.stats.mana >= ult.mana_cost:
                comp.stats.mana -= ult.mana_cost
                ult.current_charge = 0
                voice = ult.activation_voice_line
                base_dmg = ult.effects.get("base_damage", 60)
                scaling = ult.effects.get("stat_scaling", 2.0)
                tot_dmg = int(base_dmg + (comp.stats.strength if comp.role == "tank" else comp.stats.intelligence) * scaling)

                if target_npc and hasattr(target_npc, "health"):
                    target_npc.health = max(0, target_npc.health - tot_dmg)

                log = f"⚡🔥 **[동료 궁극기 발동!]** [{comp.name_ko}]의 [{ult.name_ko}]!\n- 대사: \"{voice}\"\n- 효과: 적 전체에 {tot_dmg} 치명적 피해 가함!"
                combat_logs.append(log)
                continue

            # 3. Tactical Action Selection
            acted = False

            # Healer role check: Heal lowest HP party member or player
            if comp.role in ["healer_support", "medic"]:
                heal_skill = next((s for s in comp.combat_skills if "heal" in s.effect_type and s.current_cooldown == 0 and comp.stats.mana >= s.mana_cost), None)
                if heal_skill and (state.player.health < state.player.max_health * 0.6):
                    comp.stats.mana -= heal_skill.mana_cost
                    heal_skill.current_cooldown = heal_skill.cooldown_turns
                    heal_amt = 35 + (comp.stats.wisdom // 2)
                    state.player.health = min(state.player.max_health, state.player.health + heal_amt)
                    combat_logs.append(f"💚 [{comp.name_ko}]이(가) [{heal_skill.name_ko}]을(를) 시전하여 플레이어의 HP를 +{heal_amt} 회복시켰습니다! (현재 HP: {state.player.health}/{state.player.max_health})")
                    acted = True

            # DPS or Tank offensive skills
            if not acted:
                attack_skill = next((s for s in comp.combat_skills if s.current_cooldown == 0 and comp.stats.mana >= s.mana_cost), None)
                if attack_skill:
                    comp.stats.mana -= attack_skill.mana_cost
                    attack_skill.current_cooldown = attack_skill.cooldown_turns
                    dmg = comp.stats.attack_power + 10
                    if target_npc and hasattr(target_npc, "health"):
                        target_npc.health = max(0, target_npc.health - dmg)
                    if ult:
                        ult.current_charge = min(ult.charge_required, ult.current_charge + 25)
                    combat_logs.append(f"⚔️ [{comp.name_ko}]이(가) 전술 스킬 [{attack_skill.name_ko}]을(를) 사용하여 적에게 {dmg} 피해를 입혔습니다!")
                    acted = True

            # Basic Attack
            if not acted and target_npc:
                dmg = comp.stats.attack_power
                if hasattr(target_npc, "health"):
                    target_npc.health = max(0, target_npc.health - dmg)
                if ult:
                    ult.current_charge = min(ult.charge_required, ult.current_charge + 15)
                combat_logs.append(f"🗡️ [{comp.name_ko}]의 일반 공격 적중! 적에게 {dmg} 물리 피해를 입혔습니다.")

        return combat_logs

    @classmethod
    def process_camp_rest_effects(cls, state: Any) -> List[str]:
        """Applies camp role perks when taking a short or long rest."""
        if not hasattr(state, "party") or not state.party:
            return []

        rest_logs: List[str] = []
        for comp in state.party.values():
            if not comp.is_active_party:
                continue

            # Recover companion HP/Mana on camp
            comp.stats.health = comp.stats.max_health
            comp.stats.mana = comp.stats.max_mana

            if comp.camp_role == "cook":
                state.player.health = min(state.player.max_health, state.player.health + 20)
                rest_logs.append(f"🍲 [{comp.name_ko}]이(가) 정성스러운 야영 식사를 대접하여 파티 전원 사기 회복 및 추가 체력 +20 회복!")
            elif comp.camp_role == "medic":
                state.player.injuries = []
                rest_logs.append(f"🩹 [{comp.name_ko}]이(가) 부상자를 치료하여 모든 가벼운 외상 및 출혈/중독 상태를 완치했습니다.")
            elif comp.camp_role == "scout":
                rest_logs.append(f"👁️ [{comp.name_ko}]이(가) 외곽 불침번을 완벽히 수행하여 밤샘 기습 위험을 100% 차단했습니다.")

            # Camp dialogue line
            banter = comp.dialogue_lines.get("camp_rest")
            if banter:
                rest_logs.append(f"💬 [{comp.name_ko}]: \"{banter}\"")

        return rest_logs

    @classmethod
    def format_party_html(cls, state: Any) -> str:
        """Renders rich UI for active party members with stats, formation, and bond levels."""
        if not hasattr(state, "party") or not state.party:
            return """
            <div class='qt-panel-content' style='color:#a0aec0; padding:10px;'>
              <b>현재 동행 중인 동료가 없습니다.</b><br>
              <small>마을의 선술집, 성당, 투기장 등에서 뜻이 맞는 동료를 영입하세요.</small>
            </div>
            """

        html_parts = ["<div class='qt-party-panel' style='padding:8px;'>"]
        html_parts.append("""
        <div style="background:#1a202c; color:#ffffff; padding:10px 14px; border-radius:6px; margin-bottom:10px;">
          <b style="font-size:15px;">👥 원정대 동료 파티</b>
          <p style="font-size:12px; color:#cbd5e0; margin:4px 0 0 0;">함께 피를 흘리며 모험하는 동료들의 생체 신호와 충성도 상태입니다.</p>
        </div>
        """)

        role_labels = {
            "tank": "🛡️ 방어 전사", "dps_melee": "⚔️ 근접 딜러", "dps_ranged": "🏹 원거리 사수",
            "healer_support": "💚 치유 지원", "arcane_blaster": "✨ 비전 마법사", "scout_rogue": "🗡️ 정찰 도적"
        }
        formation_labels = {"frontline": "전열", "midline": "중열", "backline": "후열"}

        for comp_id, comp in state.party.items():
            role_str = role_labels.get(comp.role, comp.role)
            form_str = formation_labels.get(comp.formation, comp.formation)
            loyalty = comp.personality.get("loyalty_score", 50)
            loyalty_color = "#38a169" if loyalty >= 50 else ("#d69e2e" if loyalty >= 25 else "#e53e3e")

            hp_pct = max(0, min(100, int((comp.stats.health / max(1, comp.stats.max_health)) * 100)))
            mp_pct = max(0, min(100, int((comp.stats.mana / max(1, comp.stats.max_mana)) * 100)))

            html_parts.append(f"""
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:4px solid #3182ce; border-radius:4px; padding:8px 10px; margin-bottom:8px; box-shadow:0 1px 2px rgba(0,0,0,0.04);">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <b style="font-size:13px; color:#2d3748;">{comp.name_ko} <small style="color:#718096; font-weight:normal;">({comp.title_ko})</small></b>
                <span style="font-size:11px; background:#edf2f7; color:#4a5568; padding:2px 6px; border-radius:3px;">{form_str} · {role_str}</span>
              </div>
              
              <div style="margin:6px 0;">
                <div style="display:flex; justify-content:space-between; font-size:11px; color:#4a5568;">
                  <span>HP {comp.stats.health}/{comp.stats.max_health}</span>
                  <span>MP {comp.stats.mana}/{comp.stats.max_mana}</span>
                </div>
                <div style="background:#edf2f7; border-radius:3px; height:6px; width:100%; margin-top:2px; overflow:hidden;">
                  <div style="background:#e53e3e; height:100%; width:{hp_pct}%;"></div>
                </div>
                <div style="background:#edf2f7; border-radius:3px; height:4px; width:100%; margin-top:2px; overflow:hidden;">
                  <div style="background:#3182ce; height:100%; width:{mp_pct}%;"></div>
                </div>
              </div>

              <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px; color:#4a5568; margin-top:4px;">
                <span>❤️ 유대감 <b>{comp.bond.tier}단계</b></span>
                <span>충성도: <b style="color:{loyalty_color};">{loyalty}/100</b></span>
                <span>⛺ 역할: <b>{comp.camp_role}</b></span>
              </div>
            </div>
            """)

        html_parts.append("</div>")
        return "".join(html_parts)

    @classmethod
    def format_party_context_for_prompt(cls, state: Any) -> str:
        """Formats active party composition and speech tone instructions for GM prompt."""
        if not hasattr(state, "party") or not state.party:
            return ""

        lines = ["[👥 현재 동행 중인 원정대 동료 목록 & 화법 규칙]"]
        for comp in state.party.values():
            if not comp.is_active_party:
                continue
            loyalty = comp.personality.get("loyalty_score", 50)
            lines.append(
                f"- {comp.name_ko} ({comp.title_ko} | 진형: {comp.formation} | 역할: {comp.role} | HP: {comp.stats.health}/{comp.stats.max_health} | 충성도: {loyalty}/100 | 어조: '{comp.speech_style}')"
            )

        return "\n".join(lines)
