"""
Unit tests for PartyEngine, Companion recruitment, autonomous combat actions,
loyalty & betrayal thresholds, camp roles, and serialization.
"""
import pytest
from src.world.state import WorldState, Player, NPC
from src.world.party_engine import PartyEngine, Companion, CompanionStats, CompanionSkill, CompanionUltimate


def test_load_companion_templates():
    comps = PartyEngine.load_templates()
    assert len(comps) >= 4
    assert "companion_elena_valerius" in comps
    assert "companion_vane_shadowfang" in comps
    assert "companion_ira_clockwork" in comps


def test_recruit_and_dismiss_companion():
    state = WorldState()
    state.player.gold = 500

    # Recruit Elena (0 gold)
    success, msg, data = PartyEngine.recruit_companion(state, "companion_elena_valerius")
    assert success is True
    assert "companion_elena_valerius" in state.party
    assert state.party["companion_elena_valerius"].name_ko == "엘레나 발레리우스"

    # Recruit Vane (costs 150G)
    success2, msg2, data2 = PartyEngine.recruit_companion(state, "companion_vane_shadowfang")
    assert success2 is True
    assert "companion_vane_shadowfang" in state.party
    assert state.player.gold == 350

    # Dismiss Vane
    success3, d_msg, _ = PartyEngine.dismiss_companion(state, "companion_vane_shadowfang")
    assert success3 is True
    assert "companion_vane_shadowfang" not in state.party


def test_max_party_limit():
    state = WorldState()
    state.player.gold = 1000

    PartyEngine.recruit_companion(state, "companion_elena_valerius")
    PartyEngine.recruit_companion(state, "companion_vane_shadowfang")
    PartyEngine.recruit_companion(state, "companion_ira_clockwork")

    # 4th companion recruitment should fail
    success, msg, _ = PartyEngine.recruit_companion(state, "companion_bram_ironbelly")
    assert success is False
    assert "가득 찼습니다" in msg


def test_modify_loyalty_and_betrayal():
    state = WorldState()
    state.player.gold = 500
    PartyEngine.recruit_companion(state, "companion_vane_shadowfang")

    # Increase loyalty and bond points
    PartyEngine.modify_loyalty_and_affinity(state, "companion_vane_shadowfang", 30, reason="전리품 공평 분배")
    assert state.party["companion_vane_shadowfang"].personality["loyalty_score"] == 70
    assert state.party["companion_vane_shadowfang"].bond.tier >= 2

    # Drop loyalty to 0 -> Betrayal & desertion!
    log, is_betrayed = PartyEngine.modify_loyalty_and_affinity(state, "companion_vane_shadowfang", -80, reason="배신 행위 방조")
    assert is_betrayed is True
    assert "companion_vane_shadowfang" not in state.party
    assert "이탈" in log or "배신" in log


def test_companion_combat_turns():
    state = WorldState()
    state.player.health = 40
    state.player.max_health = 100
    PartyEngine.recruit_companion(state, "companion_elena_valerius")

    target = NPC(id="goblin_boss", name="고블린 족장", description="보스", location="cave", health=100, max_health=100)

    # Autonomous turn resolution: Elena heals or attacks
    logs = PartyEngine.process_companion_combat_turns(state, target_npc=target)
    assert len(logs) > 0
    # Either healed player or attacked target
    assert (state.player.health > 40) or (target.health < 100)


def test_companion_ultimate_ability():
    state = WorldState()
    PartyEngine.recruit_companion(state, "companion_elena_valerius")

    comp = state.party["companion_elena_valerius"]
    assert comp.ultimate_ability is not None
    # Force charge ultimate
    comp.ultimate_ability.current_charge = 100
    comp.stats.mana = 40

    target = NPC(id="orc_warlord", name="오크 워로드", description="워로드", location="field", health=150, max_health=150)

    logs = PartyEngine.process_companion_combat_turns(state, target_npc=target)
    assert any("궁극기" in l for l in logs)
    assert comp.ultimate_ability.current_charge == 0
    assert target.health < 150


def test_camp_rest_effects():
    state = WorldState()
    state.player.gold = 500
    state.player.health = 50
    state.player.max_health = 100
    PartyEngine.recruit_companion(state, "companion_bram_ironbelly") # Cook
    PartyEngine.recruit_companion(state, "companion_elena_valerius") # Medic

    rest_logs = PartyEngine.process_camp_rest_effects(state)
    assert len(rest_logs) >= 2
    # Cook healed extra HP
    assert state.player.health > 50


def test_world_state_apply_update_party():
    state = WorldState()
    state.player.gold = 500

    state.apply_update({
        "recruit_companion": "companion_elena_valerius"
    })
    assert "companion_elena_valerius" in state.party

    state.apply_update({
        "modify_companion_loyalty": {
            "companion_id": "companion_elena_valerius",
            "delta": 10,
            "reason": "정의로운 행동"
        }
    })
    assert state.party["companion_elena_valerius"].personality["loyalty_score"] == 60


def test_serialization_round_trip():
    state = WorldState()
    PartyEngine.recruit_companion(state, "companion_elena_valerius")

    json_str = state.to_json()
    loaded = WorldState.from_json(json_str)

    assert "companion_elena_valerius" in loaded.party
    assert loaded.party["companion_elena_valerius"].name_ko == "엘레나 발레리우스"
    assert loaded.party["companion_elena_valerius"].stats.health == 140


def test_party_html_and_prompt_formatting():
    state = WorldState()
    empty_html = state.to_party_html()
    assert "동행 중인 동료가 없습니다" in empty_html

    PartyEngine.recruit_companion(state, "companion_elena_valerius")
    party_html = state.to_party_html()
    assert "엘레나 발레리우스" in party_html
    assert "전열" in party_html

    prompt_ctx = PartyEngine.format_party_context_for_prompt(state)
    assert "엘레나 발레리우스" in prompt_ctx
    assert "stoic_veteran" in prompt_ctx
