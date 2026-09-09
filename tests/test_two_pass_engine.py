import json
import pytest
from unittest.mock import MagicMock

from src.world.state import WorldState, Location, NPC, Player, Item
from src.world.two_pass_engine import TwoPassEngine, DeterministicFactSheet
from src.agents.game_master import GameMasterAgent
from src.llm.base import BaseLLM, LLMResponse


class MockLLM(BaseLLM):
    def __init__(self, json_response: dict):
        self.json_response = json_response

    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        return LLMResponse(content=json.dumps(self.json_response))

    def generate_json(self, prompt: str, system: str = "") -> str:
        return json.dumps(self.json_response)


def create_test_state() -> WorldState:
    loc = Location(
        id="loc_arena",
        name="원형 투기장",
        description="모래먼지가 날리는 결투장",
        exits={"north": "loc_gate"},
        npcs=["npc_gladiator"]
    )
    npc = NPC(
        id="npc_gladiator",
        name="검투사 바르카",
        description="거친 흉터가 가득한 투기장의 베테랑 검투사",
        location="loc_arena",
        health=50,
        max_health=50,
        armor_class=10,
        disposition="hostile",
        alive=True
    )
    player = Player(
        name="테스트용병",
        titles=["방랑자"],
        active_title="방랑자",
        location="loc_arena",
        health=100,
        max_health=100,
        mana=50,
        max_mana=50,
        inventory=["item_iron_sword"],
        strength=16,
        agility=14,
        constitution=14,
        intelligence=10,
        wisdom=10,
        luck=10,
        reputation=0
    )
    sword = Item(
        id="item_iron_sword",
        name="강철검",
        description="날이 선 강철제 롱소드",
        location="inventory",
        item_type="weapon",
        damage=12,
        value=50
    )
    state = WorldState(
        session_id="test_two_pass_session",
        player=player,
        locations={"loc_arena": loc},
        npcs={"npc_gladiator": npc},
        items={"item_iron_sword": sword}
    )
    return state


def test_two_pass_engine_fact_sheet_generation():
    state = create_test_state()
    action = "강철검으로 검투사 바르카를 강하게 베어버린다"

    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid is True
    assert fact_sheet.dice_result is not None
    assert fact_sheet.dice_result["target_npc_id"] == "npc_gladiator"
    assert "주사위" in fact_sheet.dice_result["summary_ko"]
    
    # Prompt context check
    ctx = fact_sheet.to_prompt_context()
    assert "IMMUTABLE FACT SHEET" in ctx


def test_two_pass_engine_validation_rejection():
    state = create_test_state()
    # Attempt an impossible action (Anti-Yes-Man check)
    action = "신적인 권능으로 우주를 파괴하고 절대 불사의 신이 된다"

    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid is False
    assert fact_sheet.rejection_reason is not None
    ctx = fact_sheet.to_prompt_context()
    assert "행동 거부" in ctx


def test_two_pass_engine_sanitization_overrides_llm_hallucination():
    state = create_test_state()
    target_npc = state.npcs["npc_gladiator"]
    target_npc.health = 10  # Low HP
    
    # Pass 1: compute lethal damage
    action = "강철검으로 검투사 바르카의 목을 베어 쓰러뜨린다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    # Simulate LLM hallucination in Pass 2:
    # LLM hallucinates that the NPC is completely fine with 100 HP
    fake_llm_result = {
        "narration": "검투사는 여유롭게 칼을 튕겨내고 상처 하나 입지 않았습니다.",
        "state_update": {
            "npc_state": {
                "npc_gladiator": {
                    "health": 100,  # Hallucination!
                    "alive": True
                }
            },
            "npc_memory": {
                "npc_gladiator": {
                    "description": "플레이어의 검을 가볍게 피했다고 착각함",
                    "significance": 2
                }
            }
        },
        "scene_changed": False
    }

    sanitized = TwoPassEngine.sanitize_pass2_result(fake_llm_result, fact_sheet, state)

    # Deterministic Pass 1 truth must override the hallucinated health
    if fact_sheet.combat_outcome:
        expected_hp = fact_sheet.combat_outcome["hp_after"]
        assert sanitized["state_update"]["npc_state"]["npc_gladiator"]["health"] == expected_hp
        assert sanitized["state_update"]["npc_state"]["npc_gladiator"]["alive"] == (expected_hp > 0)
    
    # Safe memory update should be preserved
    assert "npc_memory" in sanitized["state_update"]


def test_game_master_agent_two_pass_turn_flow():
    state = create_test_state()
    
    mock_response = {
        "narration": "당신의 강철검이 모래바람을 가르며 검투사의 어깨를 깊게 벱니다.",
        "state_update": {
            "record_clue": "검투사의 검술 패턴을 파악했다."
        },
        "scene_changed": False,
        "image_prompt": "A gladiator duel in dusty arena, cinematic lighting",
        "npc_action": {
            "npc_id": "npc_gladiator",
            "summary_ko": "검투사가 이를 악물고 방패로 맞받아치려 합니다."
        }
    }

    mock_llm = MockLLM(mock_response)
    gm = GameMasterAgent(llm=mock_llm)

    result = gm.process_turn("강철검으로 검투사 바르카를 공격한다", state)

    assert "검투사" in result["narration"]
    assert state.last_dice_result is not None
    assert state.last_npc_action is not None
    assert result["dice_result"] is not None
    assert len(state.history) > 0


def test_gm_prompts_xml_structure_and_formatting():
    from src.agents.prompts import GM_SYSTEM_PROMPT, GM_TURN_PROMPT_TEMPLATE, MAGIC_SYSTEM_PROMPT

    # 1. Verify GM_SYSTEM_PROMPT semantic XML sections and core rules
    assert "<System_Guardrails>" in GM_SYSTEM_PROMPT
    assert "<Anti_Hallucination>" in GM_SYSTEM_PROMPT
    assert "<Anti_Melodrama>" in GM_SYSTEM_PROMPT
    assert "<Localization_and_Atmosphere>" in GM_SYSTEM_PROMPT
    assert "<Combat_and_Action_Mechanics>" in GM_SYSTEM_PROMPT
    assert "<Turn_Economy>" in GM_SYSTEM_PROMPT
    assert "<Speed_and_Interruption>" in GM_SYSTEM_PROMPT
    assert "<Ecosystem_and_BDI_Cognition>" in GM_SYSTEM_PROMPT
    assert "<Sensory_Focalization_and_Survival>" in GM_SYSTEM_PROMPT
    assert "<Response_Format>" in GM_SYSTEM_PROMPT

    # Verify Korean output requirement and Fog of War
    assert "100% Korean Output" in GM_SYSTEM_PROMPT
    assert "NameKnownToPlayer: NO" in GM_SYSTEM_PROMPT
    assert "Strict Fog of War" in GM_SYSTEM_PROMPT

    # 2. Verify MAGIC_SYSTEM_PROMPT structure and ancient word phonetic rule
    assert "<Incantation_System>" in MAGIC_SYSTEM_PROMPT
    assert "<Modular_Grammar_Structure>" in MAGIC_SYSTEM_PROMPT
    assert "<Power_and_Penalties>" in MAGIC_SYSTEM_PROMPT
    assert "바르(발화/열에너지)" in MAGIC_SYSTEM_PROMPT
    assert "고대어 한글 발음 표기 원칙" in MAGIC_SYSTEM_PROMPT

    # 3. Verify GM_TURN_PROMPT_TEMPLATE formatting with all 22 required placeholders
    placeholders = {
        "environmental_anchoring": "어두운 던전 입구",
        "deterministic_fact_sheet": "FACT: Locked gate",
        "npc_bdi_context": "BDI: hostile guard",
        "world_context": "WORLD: dark fantasy",
        "map_context": "MAP: dungeon",
        "off_screen_context": "OFFSCREEN: patrols moving",
        "skills_context": "SKILLS: none",
        "titles_context": "TITLES: adventurer",
        "rag_memory_context": "MEMORY: none",
        "graph_context": "GRAPH: empty",
        "quest_context": "QUEST: find key",
        "shop_context": "SHOP: closed",
        "crafting_context": "CRAFTING: available",
        "party_context": "PARTY: solo",
        "status_ticks_context": "STATUS: normal",
        "physics_reaction_context": "PHYSICS: cold iron",
        "dice_roll_context": "DICE: roll 15 vs DC 12 SUCCESS",
        "interrupt_context": "INTERRUPT: none",
        "incant_context": "INCANT: none",
        "recent_history": "Turn 0: Started",
        "parsed_action_summary": "[대사]: 없음 | [행동]: 열쇠로 문을 연다",
        "action": "열쇠로 문을 연다",
    }
    formatted = GM_TURN_PROMPT_TEMPLATE.format(**placeholders)
    assert "<Turn_Execution>" in formatted
    assert "<Environmental_Anchoring>" in formatted
    assert "어두운 던전 입구" in formatted
    assert "<Player_Action>" in formatted
    assert "열쇠로 문을 연다" in formatted
    assert "<Generation_Instructions>" in formatted
    assert "narration" in formatted


def test_two_pass_engine_anti_yes_man_hypothesis_and_leakage():
    state = create_test_state()
    # Add an off-screen NPC
    off_npc = NPC(
        id="npc_alchemist",
        name="연금술사 카인",
        description="약초를 달이는 은둔 연금술사",
        location="loc_other_lab",
        health=40,
        max_health=40,
        alive=True
    )
    state.npcs["npc_alchemist"] = off_npc

    # 1. Test Hypothesis Validation (C1)
    action_hypo = "검투사 바르카가 날 독살하려는 거 아니야? 수상한 기색이 있는 것 같다"
    fact_sheet_hypo = TwoPassEngine.compute_pass1(action_hypo, state)

    assert fact_sheet_hypo.anti_yesman_verdict is not None
    assert fact_sheet_hypo.anti_yesman_verdict["target_npc_name"] == "검투사 바르카"
    assert "안티 예스맨" in fact_sheet_hypo.to_prompt_context()

    # 2. Test Off-screen NPC autonomous next intent prediction (C2)
    assert len(off_npc.off_screen_logs) > 0
    assert len(off_npc.get_recent_off_screen_logs()) > 0
    assert off_npc.intention != ""

    # 3. Test Micro-leakage & NPC observation (C3)
    action_obs = "검투사 바르카의 굳은 표정과 속내를 날카롭게 관찰한다"
    fact_sheet_obs = TwoPassEngine.compute_pass1(action_obs, state)
    logs_str = " ".join(fact_sheet_obs.npc_skill_logs)
    assert "인물 관찰 및 속내 간파" in logs_str


def test_two_pass_engine_object_physics_destruction_and_burning():
    """Verify UniversalObjectPhysicsEngine integration in TwoPassEngine live Pass 1 loop."""
    state = create_test_state()
    # Add a wooden chair to current location
    chair = Item(
        id="item_wooden_chair",
        name="낡은 참나무 의자",
        description="투박하지만 튼튼한 참나무 의자",
        location="loc_arena",
        durability=40,
        max_durability=40,
    )
    state.items["item_wooden_chair"] = chair
    state.locations["loc_arena"].items.append("item_wooden_chair")

    # Smash chair action
    action = "낡은 참나무 의자를 힘껏 내리쳐 박살낸다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    # Verify physics reaction logged and item destroyed / debris spawned
    assert any("박살" in pr or "파괴" in pr for pr in fact_sheet.physics_reactions)
    assert chair.is_destroyed is True
    assert chair.durability == 0
    assert "destroyed_items" in fact_sheet.pre_computed_state_delta
    assert "item_wooden_chair" in fact_sheet.pre_computed_state_delta["destroyed_items"]

    # Verify debris spawned into location
    loc = state.locations["loc_arena"]
    debris_in_loc = [it_id for it_id in loc.items if it_id.startswith("debris_")]
    assert len(debris_in_loc) > 0

    # Test burning paper scroll
    scroll = Item(
        id="item_parchment_letter",
        name="비밀 지령 양피지 서한",
        description="비밀 지령이 적힌 종이",
        location="loc_arena",
        durability=10,
        max_durability=10,
    )
    state.items["item_parchment_letter"] = scroll
    state.locations["loc_arena"].items.append("item_parchment_letter")

    burn_action = "비밀 지령 양피지 서한을 횃불로 불태운다"
    fact_sheet_burn = TwoPassEngine.compute_pass1(burn_action, state)
    assert any("잿더미" in pr or "소멸" in pr or "불길" in pr for pr in fact_sheet_burn.physics_reactions)
    assert scroll.is_destroyed is True


