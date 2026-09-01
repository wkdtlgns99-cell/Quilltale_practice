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
