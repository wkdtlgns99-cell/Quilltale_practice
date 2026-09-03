"""
Two-Pass GM Engine for Quilltale TRPG.
Pass 1: Deterministic Truth Computation (Dice, Combat, HP, Status, Quests, Party, Economy).
Pass 2: Literary Narration Validation and State Delta Reconciliation.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import logging

from src.world.state import WorldState
from src.world.validator import ActionValidator
from src.world.skills import SkillSystem
from src.world.incantation import IncantationSystem
from src.world.status_engine import StatusEffectEngine
from src.world.physics_matrix import PhysicsMatrixEngine
from src.world.quest_engine import QuestEngine
from src.world.economy_engine import EconomyEngine
from src.world.crafting_engine import CraftingEngine
from src.world.party_engine import PartyEngine
from src.world.graph_engine import EcologicalFeedbackLoop
from src.world.weather_engine import WeatherEngine
from src.world.bounty_engine import BountyEngine
from src.world.puzzle_engine import PuzzleEngine
from src.world.celestial_engine import CelestialEngine
from src.world.enchant_engine import EnchantEngine

logger = logging.getLogger(__name__)


@dataclass
class DeterministicFactSheet:
    """Immutable truth computed by Python engine during Pass 1."""
    action: str
    is_valid: bool = True
    rejection_reason: Optional[str] = None
    extra_flags: Dict[str, Any] = field(default_factory=dict)
    
    # 1. Status Ticks & Timers
    status_tick_logs: List[str] = field(default_factory=list)
    quest_timer_logs: List[str] = field(default_factory=list)
    
    # 2. Dice & Combat
    dice_result: Optional[Dict[str, Any]] = None
    combat_outcome: Optional[Dict[str, Any]] = None
    
    # 3. Physics & Chemistry Reactions
    physics_reactions: List[str] = field(default_factory=list)
    
    # 4. Quests & Progress
    quest_progress_logs: List[str] = field(default_factory=list)
    
    # 5. Party & Companions
    companion_combat_logs: List[str] = field(default_factory=list)
    
    # 6. Ecology & World Feedback
    eco_feedback: Dict[str, Any] = field(default_factory=dict)
    
    # 7. Extended World Mechanics (5 Engines)
    weather_logs: List[str] = field(default_factory=list)
    celestial_logs: List[str] = field(default_factory=list)
    puzzle_logs: List[str] = field(default_factory=list)
    bounty_logs: List[str] = field(default_factory=list)
    enchant_logs: List[str] = field(default_factory=list)

    # 8. Pre-computed State Delta (Single Source of Truth)
    pre_computed_state_delta: Dict[str, Any] = field(default_factory=dict)
    dropped_skill_name: Optional[str] = None
    npc_skill_logs: List[str] = field(default_factory=list)

    def to_prompt_context(self) -> str:
        """Serializes the fact sheet into a high-priority prompt section for the LLM."""
        if not self.is_valid:
            return (
                f"[❌ 행동 거부/불가 판정 (CRITICAL FAILURE)]\n"
                f"시스템 사유: {self.rejection_reason}\n"
                f"⚠️ [절대 규칙]: 플레이어의 행동은 물리적/논리적으로 가로막혔습니다. "
                f"당신은 이 실패를 100% 반영하여 길막힘, 거절, 문턱 걸림 등 참담하게 실패한 상황만을 묘사해야 합니다. "
                f"절대 목적지에 도착했다고 긍정적으로 묘사하거나, 막힌 문을 뚫고 지나갔다는 억지 소설을 쓰지 마십시오."
            )

        lines = [
            "=================================================================",
            "⚡ [확정된 100% 물리/규칙적 진실 (IMMUTABLE FACT SHEET - PASS 1)]",
            "당신은 아래의 확정 연산 팩트를 단 1의 오차도 없이 문학적 서사로 묘사해야 합니다.",
            "팩트를 왜곡, 번복, 날조(사망하지 않은 적을 사망 처리, 실패를 성공으로 변경 등)하는 것은 엄격히 금지됩니다.",
            "=================================================================",
        ]

        if self.celestial_logs:
            lines.append("🌌 [천문 이변 및 대륙 축제 이벤트]")
            for clog in self.celestial_logs:
                lines.append(f"- {clog}")

        if self.weather_logs:
            lines.append("🌦️ [날씨 환경 물리 및 생존 틱]")
            for wlog in self.weather_logs:
                lines.append(f"- {wlog}")

        if self.status_tick_logs:
            lines.append("🩸 [턴 시작 상태이상 및 지속 피해/회복 연산]")
            for log in self.status_tick_logs:
                lines.append(f"- {log}")

        if self.puzzle_logs:
            lines.append("🧩 [고대 유적 퍼즐 기믹 해결]")
            for plog in self.puzzle_logs:
                lines.append(f"- {plog}")

        if self.bounty_logs:
            lines.append("📜 [현상수배 및 사냥꾼 추적]")
            for blog in self.bounty_logs:
                lines.append(f"- {blog}")

        if self.dice_result:
            res = self.dice_result
            status_str = "성공 (SUCCESS)" if res.get("is_success") else "실패 (FAILURE)"
            lines.append(f"🎲 [주사위 판정]: {res.get('summary_ko', '')} -> 결과: [{status_str}]")

        if self.combat_outcome:
            co = self.combat_outcome
            t_name = co.get("target_name", "대상")
            lines.append(f"⚔️ [전투 피해 연산]: {t_name}에게 {co.get('damage_dealt', 0)} 피해 적용.")
            lines.append(f"   - {t_name} 남은 체력: {co.get('hp_after', 0)}/{co.get('max_hp', 0)} (생존: {'생존함' if co.get('target_alive') else '☠️ 사망함'})")
            if co.get("killed"):
                lines.append(f"   - ☠️ {t_name}(이)가 치명상을 입고 쓰러져 사망했습니다.")
                if self.dropped_skill_name:
                    lines.append(f"   - ✨ [고유 스킬 전리품 발생]: '{self.dropped_skill_name}' 스킬 획득.")

        if self.npc_skill_logs:
            lines.append("⚡ [현장 NPC 자율 스킬 및 기회주의적 행동 확정 연산]")
            for nlog in self.npc_skill_logs:
                lines.append(f"- {nlog}")
            lines.append("*GM 절대 서사 강제 지침*: 당신은 위 NPC의 행동 결과(반격 피해, 소매치기 성공/실패, 기습 등)를 100% 반영하여 서사를 작성해야 합니다.")

        if self.enchant_logs:
            lines.append("✨ [장비 룬 인챈트 및 내구도 효과]")
            for elog in self.enchant_logs:
                lines.append(f"- {elog}")

        if self.companion_combat_logs:
            lines.append("👥 [동료 자율 전투 및 지원 행동]")
            for clog in self.companion_combat_logs:
                lines.append(f"- {clog}")

        if self.physics_reactions:
            lines.append("⚗️ [환경 물리/화학 상호작용]")
            for pr in self.physics_reactions:
                lines.append(f"- {pr}")

        if self.quest_progress_logs:
            lines.append("📜 [퀘스트 진행 갱신]")
            for qlog in self.quest_progress_logs:
                lines.append(f"- {qlog}")

        if self.eco_feedback:
            ef = self.eco_feedback
            if ef.get("terraforming"):
                lines.append(f"🌍 [지형 변화]: {ef['terraforming']}")
            if ef.get("world_news"):
                lines.append(f"📢 [소문/뉴스]: {ef['world_news']}")

        lines.append("=================================================================")
        return "\n".join(lines)


class TwoPassEngine:
    """
    Executes Pass 1 (Deterministic Truth Computation)
    and validates Pass 2 (Narrative & State Delta Reconciliation).
    """

    @classmethod
    def compute_pass1(cls, action: str, state: WorldState) -> DeterministicFactSheet:
        """
        Pass 1: Computes all deterministic mechanics in strict logical order.
        """
        fact_sheet = DeterministicFactSheet(action=action)
        state_delta: Dict[str, Any] = {}

        # 1. Status Ticks, Weather Survival & Celestial Cycles
        from src.world.npc_skill_engine import NPCSkillEngine
        NPCSkillEngine.tick_all_skill_cooldowns(state)

        tick_result = StatusEffectEngine.process_turn_ticks(state)
        fact_sheet.status_tick_logs = tick_result.get("logs", [])
        
        # Weather survival ticks (Hypothermia / Heatstroke)
        weather_ticks = WeatherEngine.process_turn_survival_ticks(state)
        fact_sheet.weather_logs = weather_ticks
        fact_sheet.status_tick_logs.extend(weather_ticks)

        # Celestial & Festival cycle turns
        celestial_logs = CelestialEngine.advance_celestial_turn(state)
        fact_sheet.celestial_logs = celestial_logs

        # Advance quest timers (30 mins per standard turn)
        quest_timer_logs = QuestEngine.check_turn_time_limits(state, delta_minutes=30)
        fact_sheet.status_tick_logs.extend(quest_timer_logs)
        fact_sheet.quest_timer_logs = quest_timer_logs

        # Economy shop restock
        EconomyEngine.restock_turn_ticks(state, delta_turns=1)

        # Advance world simulation
        state.advance_world_simulation()
        state.advance_information_waves()
        state.check_and_publish_periodicals()

        # 2. Action Pre-validation & Dice check
        is_valid, error_msg, dice_res, extra_flags = ActionValidator.pre_validate_action(action, state)
        fact_sheet.is_valid = is_valid
        fact_sheet.rejection_reason = error_msg
        fact_sheet.extra_flags = extra_flags or {}

        if not is_valid:
            fact_sheet.pre_computed_state_delta = {}
            return fact_sheet

        # 2.2 Delayed Theft Discovery Check (PerceptionEngine)
        from src.world.perception_engine import PerceptionEngine
        discovered_thefts = PerceptionEngine.check_delayed_theft_discovery(state, action)
        if discovered_thefts:
            for d_info in discovered_thefts:
                fact_sheet.quest_progress_logs.append(d_info["log_ko"])
                if d_info.get("gm_directive"):
                    fact_sheet.npc_skill_logs.append(f"   * [도난 발각 서사 지침]: {d_info['gm_directive']}")

        # 2.5 Deterministic Movement Resolution (Guarantees actual location change)
        curr_loc = state.current_location()
        if curr_loc and curr_loc.exits:
            action_lower = action.lower()
            direction_keywords = {
                "north": ["북쪽", "북", "north", "앞으로", "정면"],
                "south": ["남쪽", "남", "south", "뒤로", "남문"],
                "east": ["동쪽", "동", "east", "오른쪽"],
                "west": ["서쪽", "서", "west", "왼쪽"],
                "upstairs": ["2층", "계단", "위층", "upstairs", "올라"],
                "downstairs": ["지하", "아래층", "지하실", "downstairs", "내려"]
            }
            is_move_action = any(v in action_lower for v in ["이동", "걸어", "향해", "달려", "들어", "나선", "오르", "내려", "나간", "떠난", "발걸음", "move", "go", "enter", "exit"])
            if is_move_action:
                for exit_dir, target_loc_id in curr_loc.exits.items():
                    keywords = direction_keywords.get(exit_dir.lower(), [exit_dir.lower()])
                    target_loc = state.locations.get(target_loc_id)
                    loc_name_match = bool(target_loc and target_loc.name.lower() in action_lower)
                    dir_match = any(k in action_lower for k in keywords)
                    if dir_match or loc_name_match:
                        if target_loc_id in state.locations:
                            if "player" not in state_delta:
                                state_delta["player"] = {}
                            state_delta["player"]["location"] = target_loc_id
                            target_name = target_loc.name if target_loc else target_loc_id

                            from src.world.geography import GeographyEngine
                            road = GeographyEngine.get_road(state, curr_loc.id, target_loc_id)
                            dist_km = road.distance_km if road else 1.0
                            r_type = road.road_type if road else "dirt_road"
                            hours = GeographyEngine.calculate_segment_travel_hours(dist_km, r_type, travel_mode="foot")
                            mins = max(5, int(hours * 60))
                            state_delta["time_minutes"] = mins
                            fatigue_inc = max(1, int(mins / 30))
                            state_delta["fatigue_delta"] = fatigue_inc

                            fact_sheet.quest_progress_logs.append(f"장소 이동 완료: [{target_name}]에 도착함 ({dist_km:.1f}km 이동, {mins}분 소요)")
                            break

        # 2.5 Equipment Equip / Unequip Intent Execution
        equip_intent = fact_sheet.extra_flags.get("equip_intent")
        if equip_intent:
            e_act = equip_intent.get("action")
            e_item_id = equip_intent.get("item_id")
            e_item_name = equip_intent.get("item_name")
            e_slot = equip_intent.get("slot")
            if e_act == "equip":
                state_delta["equip_slot"] = {"item_id": e_item_id, "slot": e_slot}
                fact_sheet.quest_progress_logs.append(f"장비 착용: [{e_item_name}]을(를) {e_slot} 부위에 장착했습니다.")
            elif e_act == "unequip":
                state_delta["unequip_slot"] = {"item_id": e_item_id, "slot": e_slot}
                fact_sheet.quest_progress_logs.append(f"장비 해제: [{e_item_name}]을(를) {e_slot} 부위에서 해제했습니다.")

        # 2.7 Medical Treatment Execution
        treatment_intent = fact_sheet.extra_flags.get("treatment_intent")
        if treatment_intent:
            from src.world.injury_engine import InjuryEngine
            t_type = treatment_intent.get("type")
            inj_name = treatment_intent.get("injury_name")

            if t_type == "item":
                i_id = treatment_intent.get("item_id")
                if i_id and i_id in state.items:
                    item_obj = state.items[i_id]
                    success, msg, d_mod = InjuryEngine.apply_item_treatment(state, state.player, inj_name, item_obj)
                    if success:
                        fact_sheet.quest_progress_logs.append(msg)
                        if "player" not in state_delta:
                            state_delta["player"] = {}
                        if "inventory" not in state_delta["player"]:
                            new_inv = list(state.player.inventory)
                            if i_id in new_inv:
                                new_inv.remove(i_id)
                            state_delta["player"]["inventory"] = new_inv

                        if d_mod.get("cured"):
                            state_delta["remove_player_injury"] = inj_name
                        elif d_mod.get("splinted"):
                            state_delta["splint_player_injury"] = {
                                "injury_name": inj_name,
                                "turns_needed": d_mod.get("turns_needed", 2)
                            }
            elif t_type == "doctor":
                doc_id = treatment_intent.get("doctor_id")
                fee = treatment_intent.get("fee", 50)
                if doc_id and doc_id in state.npcs:
                    doc_npc = state.npcs[doc_id]
                    success, msg, d_mod = InjuryEngine.apply_doctor_surgery(state, doc_npc, state.player, inj_name, fee=fee)
                    fact_sheet.quest_progress_logs.append(msg)
                    if success:
                        if "player" not in state_delta:
                            state_delta["player"] = {}
                        state_delta["player"]["gold"] = max(0, state.player.gold - fee)
                        state_delta["remove_player_injury"] = inj_name

        # 3. Environmental Puzzles & Mechanisms
        puzzle_res = PuzzleEngine.evaluate_puzzle_action(state, action)
        if puzzle_res and puzzle_res.get("is_solved"):
            fact_sheet.puzzle_logs.append(puzzle_res["solve_message"])
            fact_sheet.quest_progress_logs.append(f"퍼즐 해결: {puzzle_res['puzzle_name']} (경험치 +{puzzle_res['reward_exp']})")

        # 4. Bounty Hunter Ambushes
        ambush_info = BountyEngine.check_bounty_hunter_ambush(state, action)
        if ambush_info:
            fact_sheet.bounty_logs.append(ambush_info["summary_ko"])

        # 5. Physics & Chemistry Matrix evaluation
        curr_loc = state.current_location()
        loc_desc = f"{curr_loc.name} {curr_loc.description}" if curr_loc else ""
        inv_item_names = [state.items[i].name for i in state.player.inventory if i in state.items]
        physics_reactions = PhysicsMatrixEngine.evaluate(action, loc_desc, inv_item_names)
        fact_sheet.physics_reactions = [getattr(rx, "description", getattr(rx, "description_ko", str(rx))) for rx in physics_reactions]

        for rx in physics_reactions:
            if rx.status_to_apply:
                target_obj = state.npcs[dice_res.target_npc_id] if (dice_res and dice_res.target_npc_id and dice_res.target_npc_id in state.npcs) else state.player
                StatusEffectEngine.apply_status(target_obj, rx.status_to_apply, duration=rx.status_duration, potency=rx.status_potency)

        # 6. Dice & Combat Mechanics
        target_npc = None
        if dice_res:
            fact_sheet.dice_result = {
                "action_type": dice_res.action_type,
                "d20_roll": dice_res.d20_roll,
                "modifier": dice_res.modifier,
                "total": dice_res.total,
                "dc": dice_res.dc,
                "is_success": dice_res.is_success,
                "damage_dealt": dice_res.damage_dealt,
                "target_npc_id": dice_res.target_npc_id,
                "summary_ko": dice_res.summary_ko,
            }

            if dice_res.target_npc_id and dice_res.target_npc_id in state.npcs:
                target_npc = state.npcs[dice_res.target_npc_id]
                target_npc.stats_revealed = True
                
                # Combat damage computation
                if dice_res.is_success and dice_res.damage_dealt > 0:
                    raw_damage = dice_res.damage_dealt
                    target_part = fact_sheet.extra_flags.get("target_part", "")

                    # Check if AoE skill or whole-body attack
                    skill_info = fact_sheet.extra_flags.get("player_skill_used")
                    is_aoe = False
                    sk_obj = None
                    if skill_info:
                        sk_id = skill_info.get("skill_id")
                        sk_obj = state.skills_db.get(sk_id)
                        if sk_obj and (sk_obj.area_shape in ["circle", "cone", "line", "sphere"] or getattr(sk_obj, "area_radius_meters", 0) > 0):
                            is_aoe = True

                    from src.world.equipment import EquipmentEngine
                    # If AoE: cannot pinpoint specific anatomy, hits full body (chest/cape)
                    if is_aoe:
                        actual_part = "chest"
                        mitigated_dmg, armor_logs = EquipmentEngine.apply_armor_durability_and_mitigation(
                            state, target_npc, raw_damage, target_part="chest"
                        )
                        elem = sk_obj.element if sk_obj else "물리"
                        injury_name = "전신 화상" if "화염" in elem else ("폭압 타박상" if "대지" in elem or "충격" in elem else "파편 열상")
                        if injury_name not in target_npc.injuries:
                            target_npc.injuries.append(injury_name)
                        target_npc.morale = max(0, target_npc.morale - 20)
                    elif target_part:
                        actual_part = target_part
                        mitigated_dmg, armor_logs = EquipmentEngine.apply_armor_durability_and_mitigation(
                            state, target_npc, raw_damage, target_part=target_part
                        )
                        injury_map = {
                            "머리": ("머리 충격(뇌진탕)", 20),
                            "목": ("경추 손상", 25),
                            "눈": ("안구 손상(시력 감퇴)", 30),
                            "가슴": ("흉부 관통상", 25),
                            "심장": ("흉부 치명상", 35),
                            "팔": ("팔 관절 손상", 15),
                            "손": ("손목 골절", 15),
                            "다리": ("다리 골절/힘줄 파열", 20),
                            "발": ("발목 부상", 15),
                        }
                        inj_name, morale_loss = injury_map.get(target_part, (f"{target_part} 부상", 15))
                        if inj_name not in target_npc.injuries:
                            target_npc.injuries.append(inj_name)
                        target_npc.morale = max(0, target_npc.morale - morale_loss)
                    else:
                        actual_part = "chest"
                        mitigated_dmg, armor_logs = EquipmentEngine.apply_armor_durability_and_mitigation(
                            state, target_npc, raw_damage, target_part="chest"
                        )

                    hp_before = target_npc.health
                    hp_after = max(0, hp_before - mitigated_dmg)
                    is_alive = hp_after > 0
                    killed = (hp_before > 0 and hp_after <= 0)

                    fact_sheet.combat_outcome = {
                        "target_id": target_npc.id,
                        "target_name": target_npc.name,
                        "damage_dealt": mitigated_dmg,
                        "raw_damage": raw_damage,
                        "target_part": actual_part,
                        "is_aoe": is_aoe,
                        "target_injuries": list(target_npc.injuries),
                        "hp_before": hp_before,
                        "hp_after": hp_after,
                        "max_hp": target_npc.max_health,
                        "target_alive": is_alive,
                        "killed": killed,
                    }

                    if "npc_state" not in state_delta:
                        state_delta["npc_state"] = {}
                    state_delta["npc_state"][target_npc.id] = {
                        "health": hp_after,
                        "alive": is_alive,
                        "disposition": "hostile",
                        "stats_revealed": True,
                        "injuries": list(target_npc.injuries),
                        "morale": target_npc.morale,
                    }

                    # Equipment Wear & Rune Effects on Weapon
                    eq_wep = state.get_equipped_weapon_item()
                    if eq_wep:
                        dur_warn = EnchantEngine.consume_durability(eq_wep, loss=1)
                        if dur_warn:
                            fact_sheet.enchant_logs.append(dur_warn)
                        rune_logs = EnchantEngine.evaluate_rune_combat_effects(state, eq_wep, dice_res.damage_dealt, target_npc=target_npc)
                        fact_sheet.enchant_logs.extend(rune_logs)

                    # Kill events & Unique skill drops
                    if killed:
                        QuestEngine.progress_event(state, "kill", target_npc.id)
                        from src.world.rumor_diffusion_engine import RumorDiffusionEngine
                        sig = 3 if getattr(target_npc, "tier", "commoner") in ["elite", "boss", "noble", "legendary"] else 2
                        rep_delta = 15 if target_npc.disposition == "hostile" else -20
                        r_wave = RumorDiffusionEngine.dispatch_event_rumor(
                            state=state,
                            origin_loc=state.player.location,
                            event_text=f"플레이어가 [{target_npc.name}]을(를) 치명적 결투 끝에 처치함",
                            significance=sig,
                            reputation_delta=rep_delta,
                            carrier="merchant"
                        )
                        fact_sheet.quest_progress_logs.append(f"소문 확산 시작: [{target_npc.name}] 처치 소식이 상단 가도를 타고 퍼져나갑니다. (파급력 Lv.{sig})")
                        dropped_skill_id = SkillSystem.roll_unique_skill_drop(target_npc, state.player)
                        if dropped_skill_id:
                            sk_obj = state.skills_db.get(dropped_skill_id)
                            fact_sheet.dropped_skill_name = sk_obj.name if sk_obj else dropped_skill_id
                            if "grant_skill" not in state_delta:
                                state_delta["grant_skill"] = {}
                            state_delta["grant_skill"]["player"] = dropped_skill_id

        # 6.5 Player Skill Resource Deduction & Cooldown Application
        skill_info = fact_sheet.extra_flags.get("player_skill_used")
        if skill_info:
            sk_id = skill_info.get("skill_id")
            sk_name = skill_info.get("skill_name", "스킬")
            sk_res_type = skill_info.get("resource_type", "mana")
            sk_cost = skill_info.get("resource_cost", 0)
            sk_cd = skill_info.get("cooldown_turns", 0)

            if sk_res_type == "mana":
                state.player.mana = max(0, state.player.mana - sk_cost)
                if "player" not in state_delta:
                    state_delta["player"] = {}
                state_delta["player"]["mana"] = state.player.mana
            elif sk_res_type == "hp":
                state.player.health = max(1, state.player.health - sk_cost)
                if "player" not in state_delta:
                    state_delta["player"] = {}
                state_delta["player"]["health"] = state.player.health

            if sk_id in state.skills_db:
                state.skills_db[sk_id].current_cooldown = sk_cd

            # If attack hit living target, apply inflicted status effects
            if dice_res and dice_res.is_success and target_npc and target_npc.alive:
                inflicted = skill_info.get("inflicted_status", [])
                for st in inflicted:
                    s_name = st.get("status")
                    dur = st.get("duration_turns", st.get("duration", 2))
                    pot = st.get("dot_damage_per_turn", st.get("potency", 5))
                    if s_name:
                        StatusEffectEngine.apply_status(target_npc, s_name, duration=dur, potency=pot)
                        fact_sheet.status_tick_logs.append(f"적 [{target_npc.name}]에게 [{sk_name}] 효과로 상태이상 [{s_name}]({dur}턴) 부여")

        # 7. Quest Progress Hooks (location reach)
        QuestEngine.progress_event(state, "reach", state.player.location)

        # 8. Party & Companion Autonomous Turns
        is_combat = (dice_res is not None and any(k in getattr(dice_res, "action_type", "") for k in ["combat", "magic", "공격", "전투", "스킬"]))
        if is_combat and target_npc:
            companion_logs = PartyEngine.process_companion_combat_turns(state, target_npc=target_npc)
            fact_sheet.companion_combat_logs = companion_logs

        # 8.5 Hostile NPC Combat Counter-Attack / Skill Turns
        if is_combat:
            curr_loc = state.current_location()
            if curr_loc:
                loc_npcs = state.npcs_in_location(curr_loc.id)
                for h_npc in loc_npcs:
                    if h_npc.alive and h_npc.disposition == "hostile":
                        if target_npc and h_npc.id == target_npc.id and not target_npc.alive:
                            continue
                        npc_outcome = NPCSkillEngine.process_npc_combat_turn(h_npc, state, player_ac=getattr(state.player, "armor_class", 10))
                        if npc_outcome:
                            fact_sheet.npc_skill_logs.append(npc_outcome["summary_ko"])
                            if "player" not in state_delta:
                                state_delta["player"] = {}
                            state_delta["player"]["health"] = state.player.health

        # 8.6 Opportunistic / Desire-driven Non-Combat NPC Actions
        elif curr_loc:
            loc_npcs = state.npcs_in_location(curr_loc.id)
            for o_npc in loc_npcs:
                if o_npc.alive and o_npc.disposition != "hostile":
                    opp_outcome = NPCSkillEngine.process_npc_opportunistic_turn(o_npc, state, action)
                    if opp_outcome:
                        fact_sheet.npc_skill_logs.append(opp_outcome["summary_ko"])
                        if opp_outcome.get("gm_directive"):
                            fact_sheet.npc_skill_logs.append(f"   * [서사 지침]: {opp_outcome['gm_directive']}")
                        if "player" not in state_delta:
                            state_delta["player"] = {}
                        state_delta["player"]["gold"] = state.player.gold
                        state_delta["player"]["inventory"] = list(state.player.inventory)
                        if "npc_state" not in state_delta:
                            state_delta["npc_state"] = {}
                        state_delta["npc_state"][o_npc.id] = {
                            "gold": o_npc.gold,
                            "inventory": list(o_npc.inventory),
                            "disposition": o_npc.disposition
                        }
                        break  # Limit to 1 opportunistic action per turn

        # 9. Ecological Feedback
        loc_name = curr_loc.name if curr_loc else "미지의 지대"
        dice_success = dice_res.is_success if dice_res else True
        eco_feedback = EcologicalFeedbackLoop.calculate_feedback(action, dice_success, loc_name, state)
        fact_sheet.eco_feedback = eco_feedback

        if eco_feedback.get("terraforming"):
            state.world_facts.append(f"[지형 변형] {eco_feedback['terraforming']}")
        if eco_feedback.get("world_news"):
            state.pending_breaking_news.append(eco_feedback["world_news"])
        if eco_feedback.get("reputation_delta"):
            state.player.reputation = max(-100, min(100, state.player.reputation + eco_feedback["reputation_delta"]))

        fact_sheet.pre_computed_state_delta = state_delta
        return fact_sheet

    @classmethod
    def sanitize_pass2_result(
        cls,
        raw_llm_result: Dict[str, Any],
        fact_sheet: DeterministicFactSheet,
        state: WorldState
    ) -> Dict[str, Any]:
        """
        Pass 2: Reconciles LLM output with deterministic Pass 1 truth.
        Ensures state updates and narration adhere 100% to deterministic mechanics.
        """
        narration = raw_llm_result.get("narration", "").strip()
        llm_state_update = raw_llm_result.get("state_update", {})
        final_state_update = dict(fact_sheet.pre_computed_state_delta)

        # Allow safe/benign LLM updates (e.g. npc_memory, clues, environment notes, reveal_npc_name)
        safe_keys = ["npc_memory", "record_clue", "update_environment", "reveal_npc_name", "world_ended"]
        for k in safe_keys:
            if k in llm_state_update:
                final_state_update[k] = llm_state_update[k]

        # Merge grant_skill / grant_title if present
        if "grant_skill" in llm_state_update:
            if "grant_skill" not in final_state_update:
                final_state_update["grant_skill"] = {}
            final_state_update["grant_skill"].update(llm_state_update["grant_skill"])

        if "grant_title" in llm_state_update:
            final_state_update["grant_title"] = llm_state_update["grant_title"]

        # Ensure unique skill drop notice is appended to narration if generated in Pass 1
        if fact_sheet.dropped_skill_name and fact_sheet.dropped_skill_name not in narration:
            narration += f"\n\n✨ **[고유 스킬 획득]** '{fact_sheet.dropped_skill_name}' 스킬을 빼앗았습니다!"

        # Sanitize NPC state: Pass 1 deterministic HP and alive status ALWAYS override LLM
        if "npc_state" in final_state_update and "npc_state" in llm_state_update:
            for npc_id, npc_data in llm_state_update["npc_state"].items():
                if npc_id not in final_state_update["npc_state"]:
                    # Benign disposition/memory update
                    final_state_update["npc_state"][npc_id] = npc_data

        # Process skills / titles acquisition via SkillSystem
        if "grant_skill" in final_state_update:
            for target_id, skill_id in final_state_update["grant_skill"].items():
                if target_id == "player":
                    SkillSystem.acquire_skill(state, skill_id)

        if "grant_title" in final_state_update:
            for target_id, title_id in final_state_update["grant_title"].items():
                if target_id == "player":
                    SkillSystem.grant_title(state, title_id)

        return {
            "narration": narration,
            "state_update": final_state_update,
            "scene_changed": raw_llm_result.get("scene_changed", False),
            "image_prompt": raw_llm_result.get("image_prompt"),
            "npc_action": raw_llm_result.get("npc_action"),
        }
