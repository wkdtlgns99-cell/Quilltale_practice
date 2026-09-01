"""
Unit tests for StatusEffectEngine and WorldState status integration.
Verifies tick damage, healing, duration decay, stacking, stat modifiers, action blocking, and cure conditions.
"""
import pytest
from src.world.state import WorldState, Player, NPC, Location
from src.world.status_engine import StatusEffectEngine, StatusEffect
from src.world.validator import ActionValidator


def test_status_apply_and_stack():
    player = Player(health=100, max_health=100)
    msg1 = StatusEffectEngine.apply_status(player, "poison", duration=3, potency=5)
    assert "poison" in player.status_effects
    assert player.status_effects["poison"].stacks == 1
    assert player.status_effects["poison"].duration_turns == 3

    # Stack poison
    msg2 = StatusEffectEngine.apply_status(player, "poison", duration=3, potency=5)
    assert player.status_effects["poison"].stacks == 2
    assert "중첩" in msg2


def test_status_tick_damage_and_decay():
    state = WorldState()
    state.player.health = 50
    state.player.max_health = 100
    StatusEffectEngine.apply_status(state.player, "poison", duration=2, potency=10)

    # Turn 1 tick
    res1 = StatusEffectEngine.process_turn_ticks(state)
    assert state.player.health == 40
    assert state.player.status_effects["poison"].duration_turns == 1
    assert len(res1["logs"]) == 1

    # Turn 2 tick (expires at end of turn 2)
    res2 = StatusEffectEngine.process_turn_ticks(state)
    assert state.player.health == 30
    assert "poison" not in state.player.status_effects  # expired and cleaned up
    assert any("만료" in l for l in res2["logs"])


def test_status_heal_tick():
    state = WorldState()
    state.player.health = 50
    state.player.max_health = 100
    StatusEffectEngine.apply_status(state.player, "regen", duration=2, potency=15)

    res = StatusEffectEngine.process_turn_ticks(state)
    assert state.player.health == 65
    assert res["player_healed"] == 15


def test_action_block_stun_and_validator():
    state = WorldState()
    loc = Location(id="start", name="시작의 방", description="방", exits={})
    state.locations["start"] = loc
    state.player.location = "start"

    # Initially can act
    can_act, _ = StatusEffectEngine.can_act(state.player)
    assert can_act is True

    # Apply Stun
    StatusEffectEngine.apply_status(state.player, "stun", duration=1)
    can_act, reason = StatusEffectEngine.can_act(state.player)
    assert can_act is False
    assert "기절" in reason

    # Pre-validate physical action should fail
    is_valid, err_msg, dice_res, _ = ActionValidator.pre_validate_action("검을 뽑아 돌진한다", state)
    assert is_valid is False
    assert "기절" in err_msg


def test_stat_modifiers():
    player = Player(strength=14, agility=14)
    assert player.str_mod == 2
    assert player.agi_mod == 2

    # Apply fracture (strength -3, agility -3)
    StatusEffectEngine.apply_status(player, "fracture", duration=3)
    assert player.effective_strength == 11
    assert player.effective_agility == 11
    assert player.str_mod == 0  # (11-10)//2 = 0
    assert player.agi_mod == 0

    # Apply empower (strength +4)
    StatusEffectEngine.apply_status(player, "empower", duration=3)
    assert player.effective_strength == 15  # 14 - 3 + 4 = 15
    assert player.str_mod == 2  # (15-10)//2 = 2


def test_cure_condition():
    player = Player()
    StatusEffectEngine.apply_status(player, "poison")
    StatusEffectEngine.apply_status(player, "bleed")
    assert len(player.status_effects) == 2

    # Cure with antidote
    cured = StatusEffectEngine.cure_by_condition(player, "해독제")
    assert "맹독" in cured
    assert "poison" not in player.status_effects
    assert "bleed" in player.status_effects

    # Cure bleed with bandage
    cured2 = StatusEffectEngine.cure_by_condition(player, "붕대")
    assert "과다출혈" in cured2
    assert len(player.status_effects) == 0


def test_world_state_apply_update_status():
    state = WorldState()
    update = {
        "apply_status": {
            "player": {"status_id": "burn", "duration": 3, "potency": 7}
        }
    }
    changes = state.apply_update(update)
    assert "burn" in state.player.status_effects
    assert state.player.status_effects["burn"].damage_per_turn == 7

    # Remove status via update
    remove_update = {
        "remove_status": {
            "player": ["burn"]
        }
    }
    changes2 = state.apply_update(remove_update)
    assert "burn" not in state.player.status_effects


def test_serialization_round_trip():
    state = WorldState()
    StatusEffectEngine.apply_status(state.player, "poison", duration=3, potency=8)
    npc = NPC(id="goblin", name="고블린", description="괴물", location="start")
    StatusEffectEngine.apply_status(npc, "burn", duration=2, potency=4)
    state.npcs["goblin"] = npc

    json_data = state.to_json()
    loaded = WorldState.from_json(json_data)

    assert "poison" in loaded.player.status_effects
    assert loaded.player.status_effects["poison"].damage_per_turn == 8
    assert "burn" in loaded.npcs["goblin"].status_effects
    assert loaded.npcs["goblin"].status_effects["burn"].damage_per_turn == 4
