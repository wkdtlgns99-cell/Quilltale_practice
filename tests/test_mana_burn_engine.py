"""
Unit tests for ManaBurnEngine in Quilltale TRPG.
Tests mana circuit damage, overchanneling restrictions (blood/sacrifice only),
backlash mechanics, dual-nature ether mutations, and circuit restoration.
"""
import pytest
from src.world.state import WorldState, Player, NPC
from src.world.mana_burn_engine import (
    ManaBurnEngine, ManaCircuitState, EtherMutationSpec, ETHER_MUTATIONS_REGISTRY
)


def test_mana_burn_specs_and_traits():
    """Verifies all ether mutations have traits and dual-nature effects."""
    assert len(ETHER_MUTATIONS_REGISTRY) >= 8
    for m_id, spec in ETHER_MUTATIONS_REGISTRY.items():
        assert isinstance(spec, EtherMutationSpec)
        assert len(spec.traits) > 0
        assert "ether_mutation" in spec.traits
        # Dual-nature check: must have both positive and negative effects
        assert len(spec.positive_effects) > 0
        assert len(spec.negative_effects) > 0

    circuit = ManaCircuitState()
    assert len(circuit.traits) > 0
    assert circuit.vein_integrity_pct == 100.0


def test_can_use_life_as_mana_restriction():
    """User Rule 4: Normal wizards CANNOT use HP for MP. Only blood/dark/sacrifice can."""
    normal_mage = Player(
        name="일반 마법사 엘민스터",
        location="arcane_tower",
        traits=["학구파", "원소학"],
        skills=["화염구", "빙결 화살"]
    )
    can_convert, msg = ManaBurnEngine.can_use_life_as_mana(normal_mage)
    assert not can_convert
    assert "일반 마법사는 생명력을 마나로 치환할 수 없습니다" in msg

    blood_mage = Player(
        name="혈마법사 블라디미르",
        location="blood_altar",
        traits=["혈마법", "금기의 탐구자"],
        skills=["혈액 창"]
    )
    can_convert_blood, blood_msg = ManaBurnEngine.can_use_life_as_mana(blood_mage)
    assert can_convert_blood
    assert "혈맥" in blood_msg


def test_evaluate_overchannel_and_hp_burn():
    """Tests evaluating overchanneling when mana is short."""
    blood_mage = Player(
        name="대가 마법사",
        location="dungeon",
        health=50,
        max_health=50,
        mana=5,
        max_mana=30,
        traits=["대가마법"]
    )

    # 1. Normal sufficient mana
    res_normal = ManaBurnEngine.evaluate_overchannel(blood_mage, required_mp=5, available_mp=5)
    assert res_normal["success"]
    assert res_normal["hp_cost"] == 0

    # 2. Overchanneling 10 MP shortage -> 20 HP cost (2x multiplier)
    res_over = ManaBurnEngine.evaluate_overchannel(blood_mage, required_mp=15, available_mp=5)
    assert res_over["success"]
    assert res_over["hp_cost"] == 20
    assert res_over["shortage"] == 10

    # 3. Fatal HP cost check (shortage requiring 60 HP when only having 50 HP)
    res_fatal = ManaBurnEngine.evaluate_overchannel(blood_mage, required_mp=40, available_mp=5)
    assert not res_fatal["success"]
    assert res_fatal["reason"] == "fatal_hp_cost"


def test_mana_backlash_circuit_damage():
    """User Rule 3: Mana backlash damages mana circuits, causes max MP penalty, and burns out."""
    caster = Player(
        name="과열된 마법사",
        location="sanctum",
        health=40,
        max_health=40,
        traits=["흑마법"]
    )
    state = WorldState()
    state.player = caster

    circuit = ManaBurnEngine.get_circuit_state(caster)
    assert circuit.vein_integrity_pct == 100.0
    assert circuit.scarred_veins == 0

    # Trigger backlash with severity 10
    logs = ManaBurnEngine.trigger_mana_backlash(caster, severity=10, state=state)
    assert len(logs) > 0
    assert circuit.vein_integrity_pct < 100.0
    assert circuit.scarred_veins >= 1
    assert circuit.max_mp_penalty > 0
    assert circuit.burnout_turns >= 2
    assert caster.health < 40  # Direct backlash damage

    # Trying to overchannel while burnt out is rejected
    res_burnt = ManaBurnEngine.evaluate_overchannel(caster, required_mp=20, available_mp=0)
    assert not res_burnt["success"]
    assert res_burnt["reason"] == "burnout"


def test_ether_contamination_and_dual_mutation():
    """Accumulating ether contamination up to 100 triggers an ether mutation."""
    target = Player(
        name="에테르 피폭자",
        location="rift",
        traits=[]
    )
    circuit = ManaBurnEngine.get_circuit_state(target)
    assert circuit.ether_contamination == 0.0
    assert len(circuit.active_mutations) == 0

    # Accumulate 60
    logs1 = ManaBurnEngine.accumulate_contamination(target, 60.0)
    assert circuit.ether_contamination == 60.0
    assert len(circuit.active_mutations) == 0

    # Accumulate 45 -> exceeds 100 -> triggers mutation
    logs2 = ManaBurnEngine.accumulate_contamination(target, 45.0)
    assert len(circuit.active_mutations) == 1
    assert circuit.ether_contamination == 0.0  # Reset on mutate

    mut_id = circuit.active_mutations[0]
    assert mut_id in ETHER_MUTATIONS_REGISTRY
    mut_spec = ETHER_MUTATIONS_REGISTRY[mut_id]
    # Check target traits updated
    assert any(t in target.traits for t in mut_spec.traits)


def test_circuit_repair_and_stabilizer():
    """Tests recovering damaged circuits via remedies."""
    patient = Player(name="부상당한 술사", location="clinic")
    circuit = ManaBurnEngine.get_circuit_state(patient)
    circuit.vein_integrity_pct = 50.0
    circuit.burnout_turns = 3
    circuit.ether_contamination = 50.0

    # 1. Stabilizer
    ok, msg = ManaBurnEngine.repair_circuit(patient, "mana_stabilizer")
    assert ok
    assert circuit.vein_integrity_pct == 75.0
    assert circuit.burnout_turns == 1

    # 2. Holy water
    ok2, msg2 = ManaBurnEngine.repair_circuit(patient, "holy_water_purge")
    assert ok2
    assert circuit.ether_contamination == 15.0
