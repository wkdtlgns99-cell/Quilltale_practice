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

    def to_prompt_context(self) -> str:
        """Serializes the fact sheet into a high-priority prompt section for the LLM."""
        if not self.is_valid:
            return f"[❌ 행동 거부/불가 판정]\n사유: {self.rejection_reason}"

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
                            fact_sheet.quest_progress_logs.append(f"장소 이동 완료: [{target_name}]에 도착함")
                            break

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
                    hp_before = target_npc.health
                    hp_after = max(0, hp_before - dice_res.damage_dealt)
                    is_alive = hp_after > 0
                    killed = (hp_before > 0 and hp_after <= 0)

                    fact_sheet.combat_outcome = {
                        "target_id": target_npc.id,
                        "target_name": target_npc.name,
                        "damage_dealt": dice_res.damage_dealt,
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
                        state.pending_breaking_news.append(f"주요 인물 [{target_npc.name}]의 치명적 부상/사망 사건")
                        dropped_skill = SkillSystem.roll_unique_skill_drop(state, target_npc.id)
                        if dropped_skill:
                            fact_sheet.dropped_skill_name = dropped_skill.name
                            if "grant_skill" not in state_delta:
                                state_delta["grant_skill"] = {}
                            state_delta["grant_skill"]["player"] = dropped_skill.id

        # 7. Quest Progress Hooks (location reach)
        QuestEngine.progress_event(state, "reach", state.player.location)

        # 8. Party & Companion Autonomous Turns
        is_combat = (dice_res is not None and dice_res.action_type in ["combat", "magic_attack"])
        if is_combat and target_npc:
            companion_logs = PartyEngine.process_companion_combat_turns(state, target_npc=target_npc)
            fact_sheet.companion_combat_logs = companion_logs

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
