"""
The Game Master Agent for Quilltale TRPG Engine.
Integrates WorldState validation, deterministic DiceEngine, Local RAG MemoryManager,
Autonomous NPC turns, Fog of War, and Legacy character archiving.
"""
import json
import logging
from typing import Optional, Dict, Any, List, Tuple

from src.llm.base import BaseLLM
from src.world.state import WorldState
from src.world.validator import ActionValidator
from src.world.dice import DiceCheckResult
from src.world.persistence import PersistenceManager
from src.world.legacy import LegacyManager
from src.world.generator import WorldGenerator
from src.world.skills import SkillSystem
from src.world.incantation import IncantationSystem
from src.world.chronicle import ChronicleManager
from src.world.scenario_manager import ScenarioManager
from src.memory.memory_manager import MemoryManager
from .prompts import GM_SYSTEM_PROMPT, GM_TURN_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class GameMasterAgent:
    def __init__(self, llm: BaseLLM, memory_manager: Optional[MemoryManager] = None):
        self._llm = llm
        self._memory = memory_manager or MemoryManager()
        self._scenario_manager = ScenarioManager()

    def process_turn(self, action: str, state: WorldState) -> Dict[str, Any]:
        """
        6-Step Deterministic Turn Pipeline:
        - Step 1: Status Effect Ticks & Environment Updates (Weather/Living world)
        - Step 2: Action Pre-Validation & Deterministic Logic (DiceEngine, PhysicsMatrixEngine)
        - Step 3: WorldState State Pre-Finalization (Damage, Stun, Status Applied)
        - Step 4: Dynamic Lego-Block Context Assembly
        - Step 5: LLM Literary Narration Generation (Adhering 100% to confirmed state)
        - Step 6: WorldState Delta Synchronization & Vector Memory Persistence
        """
        from src.world.status_engine import StatusEffectEngine
        from src.world.physics_matrix import PhysicsMatrixEngine

        # Step 0: Handle Character Release / Retirement
        if ActionValidator.is_release_action(action):
            reason = "retired" if "은퇴" in action or "마치" in action else "released"
            legacy_data = LegacyManager.archive_character(state, reason=reason)
            lore_entries = LegacyManager.convert_to_lore_and_index(legacy_data, self._memory)

            farewell_narration = (
                f"🕊️ **[캐릭터 {'은퇴' if reason == 'retired' else '방생'}]**\n\n"
                f"'{state.player.name}'(은)는 배낭을 정리하고 길게 숨을 내쉬며, 자신만의 길을 향해 유유히 떠나갑니다.\n"
                f"당신이 이룬 모든 행적과 기억은 이 세계의 전설과 소문으로 영원히 박제되었습니다.\n\n"
                f"*(다음 모험가로 시작할 때, 이 세계 어딘가에서 은퇴한 {state.player.name}을(를) NPC로 다시 조우할 수 있습니다.)*"
            )

            state.history.append({
                "turn": state.turn,
                "action": action,
                "narration": farewell_narration,
            })
            PersistenceManager.save_session(state)

            return {
                "narration": farewell_narration,
                "state_update": {},
                "scene_changed": True,
                "image_prompt": "A lone traveler walking towards the distant misty horizon at sunset, cinematic fantasy art",
                "changes_applied": [f"Character archived as legacy ID: {legacy_data['legacy_id']}"],
                "dice_result": None,
                "is_released": True,
            }

        # -------------------------------------------------------------
        # PASS 1: DETERMINISTIC TRUTH COMPUTATION
        # (Dice, HP deduction, Combat, Status Ticks, Quests, Party, Ecology)
        # -------------------------------------------------------------
        from src.world.two_pass_engine import TwoPassEngine
        from src.world.quest_engine import QuestEngine
        from src.world.economy_engine import EconomyEngine
        from src.world.crafting_engine import CraftingEngine
        from src.world.party_engine import PartyEngine

        fact_sheet = TwoPassEngine.compute_pass1(action, state)

        # Handle validation rejection (Anti-Yes-Man, missing item, illegal action)
        if not fact_sheet.is_valid:
            state.last_dice_result = None
            state.last_npc_action = None
            narration = fact_sheet.rejection_reason or "그 행동은 현재 상황에서 불가능합니다."
            state.history.append({
                "turn": state.turn,
                "action": action,
                "narration": narration,
            })
            PersistenceManager.save_session(state)
            return {
                "narration": narration,
                "state_update": {},
                "scene_changed": False,
                "image_prompt": None,
                "changes_applied": ["Action rejected by reality validator"],
                "dice_result": None,
            }

        # Save dice result in state
        dice_res_dict = fact_sheet.dice_result
        if dice_res_dict:
            state.last_dice_result = dice_res_dict
            dice_context = f"[🎲 주사위 판정 결과 (DETERMINISTIC RESULT)]\n{dice_res_dict.get('summary_ko', '')}\n*주의: 당신은 이 판정 결과를 절대 번복할 수 없으며, 결과에 걸맞은 서사를 작성해야 합니다.*"
        else:
            state.last_dice_result = None
            dice_context = ""

        # Context construction for Pass 2 (RAG, Graph, BDI, Environment)
        curr_loc = state.current_location()
        present_npcs = curr_loc.npcs if curr_loc else []
        rag_context = self._memory.retrieve_context(
            session_id=state.session_id,
            current_action=action,
            current_location=state.player.location,
            current_npcs=present_npcs,
            top_k=4,
        )

        inv_item_names = [state.items[i].name for i in state.player.inventory if i in state.items]
        graph_context = self._memory.retrieve_graph_context(
            action=action,
            location_name=curr_loc.name if curr_loc else "",
            location_id=state.player.location,
            inventory_items=inv_item_names,
            monsters=present_npcs,
        )

        off_screen_context = state.get_off_screen_context_for_location(state.player.location)
        environmental_anchoring = state.environment.to_anchoring_text()
        npc_bdi_context = self._format_bdi_context(state, present_npcs)

        # Update last_seen_turn for present NPCs
        for npc_id in present_npcs:
            if npc_id in state.npcs:
                state.npcs[npc_id].last_seen_turn = state.turn

        recent_history_str = self._format_history(state.history[-5:])

        extra_flags = fact_sheet.extra_flags
        parsed = extra_flags.get("parsed_components", {}) if extra_flags else {}
        parsed_summary_lines = []
        if parsed.get("dialogue"):
            parsed_summary_lines.append(f'- [직접 발화 대사]: "{parsed["dialogue"]}"')
        if parsed.get("monologue"):
            parsed_summary_lines.append(f"- [내면 독백/생각/텔레파시]: '{parsed['monologue']}'")
        if parsed.get("action"):
            parsed_summary_lines.append(f'- [신체 물리 행동]: {parsed["action"]}')
        parsed_action_summary = "\n".join(parsed_summary_lines) if parsed_summary_lines else f'- [행동]: {action}'

        # Dynamic context pruning
        action_str = action.lower() if action else ""
        skill_names = [s.name.lower() for s in state.player.skills] if state.player.skills else []
        uses_skill = any(sn in action_str for sn in skill_names) or any(k in action_str for k in ["공격", "마법", "스킬", "사용", "영창", "주문", "때린다", "베기", "쏜다"])
        dyn_skills = self._format_skills_context(state) if uses_skill else ""

        social_keywords = ["대화", "인사", "위협", "묻다", "질문", "말한다", "설득", "다가간다", "바라본다", "npc"]
        is_social = any(k in action_str for k in social_keywords)
        dyn_titles = self._format_titles_context(state) if is_social else ""

        lore_keywords = ["소문", "역사", "흔적", "조사", "책", "문자", "묻다", "주변", "기록", "살핀다", "단서"]
        is_lore = any(k in action_str for k in lore_keywords)
        dyn_world = state.to_context_summary() if is_lore else ""

        is_travel = any(k in action_str for k in ["이동", "간다", "도착", "들어간다", "나간다"])
        dyn_off_screen = off_screen_context if (is_social or is_travel) else ""

        graph_keywords = ["이동", "지도", "세력", "생태", "흔적", "주변", "탐색", "관찰"]
        is_graph = any(k in action_str for k in graph_keywords)
        dyn_graph = graph_context if is_graph else ""

        status_ticks_context = ""
        if fact_sheet.status_tick_logs:
            status_ticks_context = "[🩸 턴 시작 상태이상 및 지속 피해/회복 확정 연산]\n" + "\n".join(f"- {l}" for l in fact_sheet.status_tick_logs)

        physics_reaction_context = ""
        if fact_sheet.physics_reactions:
            physics_reaction_context = "[⚗️ 환경 물리/화학 상호작용]\n" + "\n".join(f"- {l}" for l in fact_sheet.physics_reactions)

        interrupt_context = ""
        if extra_flags and extra_flags.get("interrupt_counter"):
            interrupt_context = "[⚠️ 인터럽트 경고]\n플레이어가 약점을 노리다 실패하여 빈틈을 보였습니다. 적대적 NPC는 이번 턴에 즉시 강력한 반격(인터럽트)을 가할 수 있습니다."

        incant_context = ""
        if extra_flags and extra_flags.get("incantation_cancel_risk"):
            hostiles = [n for n in state.npcs_in_location(state.player.location) if n.alive and n.disposition == "hostile"]
            if hostiles:
                cancel_risk = IncantationSystem.check_incantation_cancel(state, action, hostiles)
                if cancel_risk:
                    incant_context = "[⚠️ 영창 방해 경고]\n적대적 NPC의 방해로 인해 플레이어의 마법 영창이 취소될 위기에 처했습니다. 캐스팅 실패 또는 오발 상황을 나레이션에 반영하십시오."

        if extra_flags and extra_flags.get("incantation_char_limit_exceeded"):
            limit = extra_flags.get("incantation_limit", 0)
            incant_context += f"\n[⚠️ 영창 길이 초과 경고]\n플레이어가 1턴 제한({limit}자)을 초과하는 긴 영창을 시도했습니다. 영창은 다음 턴까지 이어지거나, 무리한 시도로 인해 실패할 수 있습니다."

        quest_context = QuestEngine.format_prompt_context(state)
        shop_context = EconomyEngine.format_shop_context_for_prompt(state)
        crafting_context = CraftingEngine.format_crafting_context_for_prompt(state)
        party_context = PartyEngine.format_party_context_for_prompt(state)

        prompt = GM_TURN_PROMPT_TEMPLATE.format(
            environmental_anchoring=environmental_anchoring,
            deterministic_fact_sheet=fact_sheet.to_prompt_context(),
            npc_bdi_context=npc_bdi_context,
            world_context=dyn_world,
            map_context=state.to_map_summary(),
            off_screen_context=dyn_off_screen,
            skills_context=dyn_skills,
            titles_context=dyn_titles,
            rag_memory_context=rag_context,
            graph_context=dyn_graph,
            quest_context=quest_context,
            shop_context=shop_context,
            crafting_context=crafting_context,
            party_context=party_context,
            status_ticks_context=status_ticks_context,
            physics_reaction_context=physics_reaction_context,
            dice_roll_context=dice_context,
            interrupt_context=interrupt_context,
            incant_context=incant_context,
            recent_history=recent_history_str,
            parsed_action_summary=parsed_action_summary,
            action=action,
        )

        # -------------------------------------------------------------
        # PASS 2: NARRATIVE GENERATION & CONSISTENCY SANITIZATION
        # -------------------------------------------------------------
        try:
            dynamic_system_prompt = GM_SYSTEM_PROMPT + "\n" + self._scenario_manager.get_prompt_injection(state)
            try:
                action_text = action if "action" in locals() else ""
                magic_keywords = ["마법", "영창", "주문", "캐스팅", "마나", "원소", "형태", "기동"]
                if any(k in action_text for k in magic_keywords):
                    from src.agents.prompts import MAGIC_SYSTEM_PROMPT
                    dynamic_system_prompt += "\n\n" + MAGIC_SYSTEM_PROMPT
            except Exception:
                pass

            from src.llm.resilience import JSONRepairEngine
            raw = self._llm.generate_json(prompt, dynamic_system_prompt)
            raw_result = JSONRepairEngine.repair_and_parse(raw)

        except Exception as e:
            logger.error(f"GM Generation/Parse error: {e}")
            from src.llm.resilience import JSONRepairEngine
            raw_result = JSONRepairEngine.repair_and_parse(str(e))
            if not raw_result.get("narration"):
                raw_result["narration"] = "당신은 주변을 둘러보며 다음 행동을 신중하게 가늠합니다."

        # Sanitize and reconcile Pass 2 output with Pass 1 deterministic truth
        result = TwoPassEngine.sanitize_pass2_result(raw_result, fact_sheet, state)

        # Process NPC autonomous action
        npc_action = result.get("npc_action")
        if npc_action and isinstance(npc_action, dict) and npc_action.get("summary_ko"):
            state.last_npc_action = npc_action
        else:
            state.last_npc_action = None

        # Apply reconciled state update
        state_update = result.get("state_update", {})
        changes = state.apply_update(state_update)
        narration = result.get("narration", "")

        # Check for world ending
        if state_update.get("world_ended"):
            chronicle = ChronicleManager.generate_chronicle(state, self._llm)
            ChronicleManager.save_chronicle(state, chronicle)
            narration += f"\n\n📜 **[세계의 연대기 기록됨]**\n{chronicle[:200]}..."

        # Index turn into Vector RAG Memory
        max_significance = 1
        emotional_tone = "neutral"
        if "npc_memory" in state_update:
            for npc_id, m_data in state_update["npc_memory"].items():
                sig = int(m_data.get("significance", 1))
                if sig >= 4:
                    desc = m_data.get("description", "")
                    if desc:
                        state.pending_breaking_news.append(desc)
                if sig > max_significance:
                    max_significance = sig
                    emotional_tone = m_data.get("emotional_tone", "neutral")

        self._memory.record_turn_memory(
            session_id=state.session_id,
            turn=state.turn,
            action=action,
            narration=narration,
            location_id=state.player.location,
            npc_ids=present_npcs,
            significance=max_significance,
            emotional_tone=emotional_tone,
        )

        # Log history
        state.history.append({
            "turn": state.turn,
            "action": action,
            "narration": narration,
        })

        # Auto-persist session to disk
        scene_changed = result.get("scene_changed", False)
        if scene_changed:
            self._scenario_manager.advance_scenario(state)

        PersistenceManager.save_session(state)

        # Audio triggers evaluation (BGM & SFX)
        from src.world.audio_engine import AudioEngine
        audio_data = AudioEngine.determine_turn_audio(state, fact_sheet=fact_sheet, action=action)
        audio_html = AudioEngine.format_audio_html(audio_data)

        return {
            "narration": narration,
            "state_update": state_update,
            "scene_changed": scene_changed,
            "image_prompt": result.get("image_prompt"),
            "changes_applied": changes,
            "dice_result": state.last_dice_result,
            "npc_action": state.last_npc_action,
            "audio": audio_data,
            "audio_html": audio_html,
        }

    def _format_history(self, history: list) -> str:
        if not history:
            return "아직 기록된 이전 행동이 없습니다."
        return "\n".join(
            f"턴 {h.get('turn', '?')}: [행동: {h.get('action', '')}] → {h.get('narration', '')}"
            for h in history
        )

    def _format_skills_context(self, state: WorldState) -> str:
        if not state.player.skills:
            return 'PLAYER SKILLS: None'
        lines = ['PLAYER SKILLS:']
        for skill_id in state.player.skills:
            skill = state.skills_db.get(skill_id)
            if skill:
                lines.append(f'  [{skill.skill_type.upper()}] {skill.name}: {skill.description}')
        return '\n'.join(lines)

    def _format_titles_context(self, state: WorldState) -> str:
        if not state.player.titles:
            return 'PLAYER TITLES: None'
        lines = ['PLAYER TITLES:']
        for title_id in state.player.titles:
            title = state.titles_db.get(title_id)
            if title:
                bonuses = ', '.join(f'{k}+{v}' for k, v in title.stat_bonuses.items())
                lines.append(f'  [{title.name}]: {title.description} (보너스: {bonuses})')
        return '\n'.join(lines)

    def _format_bdi_context(self, state: WorldState, present_npc_ids: List[str]) -> str:
        """Format present NPCs' BDI (Belief-Desire-Intention) & Attitude Matrix context for GM."""
        if not present_npc_ids:
            return "[현장 인물 BDI 심리 상태]: 주변에 조우 중인 인물 없음."

        lines = ["[🎭 현장 인물 BDI 인지 상태 & 3대 태도 매트릭스]:"]
        for nid in present_npc_ids:
            npc = state.npcs.get(nid)
            if not npc:
                continue
            beliefs_str = ", ".join(f"'{b}'" for b in npc.beliefs) if npc.beliefs else "특이 오해/풍문 없음"
            injuries_str = ", ".join(npc.injuries) if npc.injuries else "외상 없음"
            lines.append(f"  - [{npc.name}] (직업: {npc.job})")
            lines.append(f"    * 3대 태도: 친밀도({npc.affinity}/100) | 공포({npc.fear}/100) | 부채감({npc.debt:+d})")
            lines.append(f"    * BDI 인지: 믿고 있는 정보=[{beliefs_str}] | 절박한 욕망/동기=[{npc.desire or '생존'}] | 이번 턴 의도=[{npc.intention or '현장 주시'}]")
            if injuries_str != "외상 없음":
                lines.append(f"    * 신체 상태: {injuries_str}")
            if hasattr(npc, "combat_profile") and npc.combat_profile.intel_book:
                intel_str = " | ".join(f"[{k}]에 대해: {v}" for k, v in npc.combat_profile.intel_book.items())
                if intel_str:
                    lines.append(f"    * 전술 지식(Intel): {intel_str}")
        return "\n".join(lines)


    def generate_opening(self, state: WorldState) -> Dict[str, Any]:
        """Generate the opening scene for a new session using the world's intro structure."""
        from src.world.generator import INTRO_STRUCTURES
        LegacyManager.spawn_legacy_npcs_to_world(state)
        
        if not state.current_scenario_id:
            self._scenario_manager.start_random_scenario(state)

        loc = state.current_location()
        present_npcs = state.npcs_in_location(state.player.location)
        npc_descriptors = []
        for n in present_npcs:
            if n.name_revealed:
                npc_descriptors.append(f"{n.name} ({n.job or '인물'})")
            else:
                role_alias = n.job or "선술집 주인"
                npc_descriptors.append(f"미지의 인물 [호칭: '{role_alias}'] (⚠️ 플레이어가 아직 이름을 모르므로 서사 본문에서 실명 '{n.name}'을 절대 부르지 말고 '{role_alias}' 등 겉모습 호칭으로만 서술할 것)")

        # Find intro key from world facts or default to A
        chosen_key = "A"
        for f in state.world_facts:
            if f.startswith("[도입 설정 코드] "):
                chosen_key = f.replace("[도입 설정 코드] ", "").strip()
                break
        
        intro_info = INTRO_STRUCTURES.get(chosen_key, INTRO_STRUCTURES["A"])
        chosen_structure = intro_info["detail"]

        prompt = f"""
{state.to_context_summary()}

당신은 이 TRPG의 오프닝 연출을 담당하는 마스터입니다.
현재 세계의 시작 장소는 [{loc.name if loc else '미지의 장소'}] (설명: {loc.description if loc else ''})입니다.
현장에 있는 인물: {', '.join(npc_descriptors) if npc_descriptors else '주변에 다른 인물 없음'}

반드시 아래 오프닝 연출 구조를 따라 현재 시작 장소 [{loc.name if loc else ''}]의 상황을 순서대로 서술하십시오:

{chosen_structure}

[★ 분량 및 서술 디테일 필수 규칙 (엄격 준수)]
1. [분량 고정]: **공백을 제외한 순수 한글 600~800자 (공백 포함 약 900~1,200자)** 분량으로 충실하고 깊이 있게 작성하십시오. 짧게 요약하거나 400자 이하로 끝내지 마십시오.
2. [장면 연출 밀도]: 4단계(원경→중경→근경→줌인) 연출 단계마다 장면의 공기, 소리, 온도, 냄새, 빛과 그림자, 주변의 구체적인 소품과 기물, 인물의 시선과 호흡, 손끝의 감각을 영화처럼 생생하고 유려한 문학적 필체로 묘사하십시오.
3. [절대 서사 일관성 & 자유도 규칙]:
   - 오프닝의 사건과 배경은 위 WORLD STATE에 명시된 시작 장소 [{loc.name if loc else ''}] 및 현장 인물들과 100% 일치해야 합니다.
   - 다른 가상의 장소를 지어내지 말고, 플레이어가 서 있는 [{loc.name if loc else ''}] 현장에서 벌어진 사건으로 묘사하십시오.
4. [미지의 인물 실명 발설 절대 금지 & 생생한 묘사]:
   - 플레이어가 아직 통성명하지 않은 모르는 인물은 서사에서 실명을 부르지 마십시오.
   - 대상의 성별, 연령, 착장, 분위기(예: 카운터를 닦는 여주인, 수염을 만지는 노인 등)를 자연스럽게 관찰하여 묘사하십시오.
   - 상투적인 클리셰 단어(기름 묻은 앞치마, 0.5초 등)를 무의미하게 반복하지 마십시오.
5. [선택지 목록 절대 금지]:
   - 서사의 마지막에 인위적인 객관식 선택지(▶ 선택지 A/B/C 등)를 나열하지 마십시오.
   - 플레이어가 오롯이 스스로의 의지로 행동을 결정할 수 있도록, 현장의 분위기와 긴장감 넘치는 상황 묘사로만 서사를 마무리하십시오.
6. narration 필드에 전체 오프닝 서사를 담으십시오.

응답 형식: {{"narration": "오프닝 전체 서사 (한국어, 공백 제외 600~800자 분량, 미지 인물 실명 없음, 선택지 목록 없음)", "image_prompt": "cinematic fantasy scene (영문)"}}
"""



        try:
            dynamic_system_prompt = GM_SYSTEM_PROMPT + "\n" + self._scenario_manager.get_prompt_injection(state)
            try:
                action_text = action if "action" in locals() else ""
                magic_keywords = ["마법", "영창", "주문", "캐스팅", "마나", "원소", "형태", "기동"]
                if any(k in action_text for k in magic_keywords):
                    from src.agents.prompts import MAGIC_SYSTEM_PROMPT
                    dynamic_system_prompt += "\n\n" + MAGIC_SYSTEM_PROMPT
            except Exception:
                pass

            from src.llm.resilience import JSONRepairEngine
            raw = self._llm.generate_json(prompt, dynamic_system_prompt)
            result = JSONRepairEngine.repair_and_parse(raw)
            narration = result.get("narration", f"당신은 {loc.name if loc else '알 수 없는 곳'}에 서 있습니다.")
            image_prompt = result.get("image_prompt")
        except Exception as e:
            logger.error(f"GM Opening generation error: {e}")
            narration = f"축축하고 차가운 공기가 폐부를 찌릅니다. 당신은 {loc.name if loc else '알 수 없는 장소'}에 서 있습니다."
            image_prompt = None

        # 1. Store opening narrative as Turn 0 in state.history so turn 1 knows what happened!
        state.history = [{
            "turn": 0,
            "action": "[모험의 시작 / 오프닝 연출]",
            "narration": narration
        }]

        # 2. Add as top world fact so subsequent turns strictly remember opening
        state.world_facts.insert(0, f"[오프닝 도입 상황]: {narration[:120]}...")

        # 3. Record in RAG memory
        self._memory.record_turn_memory(
            session_id=state.session_id,
            turn=0,
            action="[모험의 시작]",
            narration=narration,
            location_id=state.player.location,
            npc_ids=[n.id for n in present_npcs],
            significance=5,
            emotional_tone="neutral"
        )

        PersistenceManager.save_session(state)
        return {
            "narration": narration,
            "image_prompt": image_prompt,
            "scene_changed": True,
        }

    def generate_new_game(self) -> WorldState:
        """Generate a completely new random world using LLM and Qdrant RAG."""
        # Only index lean region templates & monster templates for CPU performance
        try:
            self._memory.index_region_templates()
            self._memory.index_monster_templates()
        except Exception as e:
            logger.warning(f"Templates vector indexing failed: {e}")


        generator = WorldGenerator(self._llm, self._memory)
        world_data, intro_key = generator.generate_new_world()

        state = WorldState.from_json(json.dumps(world_data, ensure_ascii=False))
        state.world_facts.append(f"[도입 설정 코드] {intro_key}")
        LegacyManager.spawn_legacy_npcs_to_world(state)
        # Index any chronicle entries into RAG
        library_entries = ChronicleManager.get_library_entries()
        for i, entry in enumerate(library_entries):
            self._memory.index_lore(
                lore_id=f'chronicle_{i}',
                title='고대 도서관 기록',
                content=entry,
                location_id='library',
                tags=['chronicle', 'legacy', 'history'],
            )
        PersistenceManager.save_session(state)
        return state

    def expand_region(self, state: WorldState, target_query: str) -> Optional[dict]:
        """
        Dynamically generate and connect a new region using Qdrant RAG.
        Returns the new Location dictionary if created.
        """
        generator = WorldGenerator(self._llm, self._memory)
        new_loc = generator.generate_dynamic_region(state, target_query)
        if new_loc and "id" in new_loc:
            loc_id = new_loc["id"]
            # Attach to current state locations
            from src.world.state import Location
            loc_obj = Location.from_dict(new_loc) if hasattr(Location, 'from_dict') else Location(
                id=loc_id,
                name=new_loc.get("name", "미지의 지역"),
                description=new_loc.get("description", ""),
                exits=new_loc.get("exits", {}),
                environmental_hazards=new_loc.get("environmental_hazards", []),
            )
            state.locations[loc_id] = loc_obj
            # Connect current location exit to new location
            current_loc = state.locations.get(state.player.location)
            if current_loc:
                current_loc.exits[new_loc.get("name", "새로운 지대")] = loc_id
            PersistenceManager.save_session(state)
            return new_loc
        return None


    def generate_world_news_tick(self, state: WorldState) -> Optional[str]:
        """
        Batched 10-turn World News: synthesizes off-screen NPC activities and rumors into a 1-2 line rumor/news.
        """
        recent_logs = []
        for npc in state.npcs.values():
            if npc.off_screen_logs:
                recent_logs.extend(npc.off_screen_logs[-2:])
        
        if not recent_logs:
            return None

        prompt = f"""세계관: {state.world_name} ({state.world_genre})
현재 턴: {state.turn}
최근 인물들의 활동 기록:
{chr(10).join('- ' + l for l in recent_logs[:6])}

위 사건들을 바탕으로, 모험가들이 선술집이나 광장에서 수군거릴 만한 흥미로운 '세계 소식/소문' 1~2줄을 한국어로 간결하게 요약하십시오.
JSON 형식: {{"news": "요약된 소식"}}"""

        try:
            raw = self._llm.generate_json(prompt, "당신은 TRPG 세계관의 소식통입니다. 흥미롭고 생생한 1~2줄 소문을 작성합니다.")
            result = json.loads(raw)
            news = result.get("news", "")
            if news:
                state.world_news_feed.append(f"(턴 {state.turn}) {news}")
                if news not in state.world_facts:
                    state.world_facts.append(f"[소문] {news}")
                return news

        except Exception as e:
            logger.error(f"World news generation failed: {e}")
        return None