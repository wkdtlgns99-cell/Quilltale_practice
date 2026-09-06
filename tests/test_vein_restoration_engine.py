"""
Unit tests for ManaVeinRestorationEngine in Quilltale TRPG.
Tests circuit surgery specs, silver needle acupuncture, arcane dialysis scar removal,
User Decision Q2 Option B backlash shock on failure (-15 HP and burnout), and tonic brewing.
"""
import pytest
from src.world.state import WorldState, Player, NPC, Location
from src.world.vein_restoration_engine import (
    ManaVeinRestorationEngine, VeinSurgerySpec, VEIN_SURGERY_REGISTRY
)


@pytest.fixture
def surgery_world():
    state = WorldState()
    state.locations["sanctuary_clinic"] = Location(
        id="sanctuary_clinic",
        name="성역 비전 의무관",
        description="마나 과부하 환자들을 치료하는 전문 의원.",
        exits={},
        traits=["clinic", "urban", "magic"]
    )
    # Injured mage patient
    state.player = Player(
        name="마법사 세라",
        location="sanctuary_clinic",
        health=40,
        max_health=50,
        mana=10,
        max_mana=30,  # 20 penalty from scars
        gold=100
    )
    # Give patient damaged circuits
    circuit = ManaVeinRestorationEngine.get_circuit_state(state.player)
    circuit["vein_integrity_pct"] = 40.0
    circuit["scarred_veins"] = 2
    circuit["burnout_turns"] = 2
    circuit["max_mp_penalty"] = 20

    # Skilled doctor NPC
    state.npcs["dr_lucas"] = NPC(
        id="dr_lucas",
        name="외과의 루카스",
        description="노련한 비전 외과의사.",
        location="sanctuary_clinic",
        intelligence=18,
        wisdom=16
    )

    # Incompetent quack doctor
    state.npcs["quack_bob"] = NPC(
        id="quack_bob",
        name="야매 의사 밥",
        description="약초도 구별 못하는 돌팔이 의사.",
        location="sanctuary_clinic",
        intelligence=8,
        wisdom=7
    )

    return state


def test_vein_surgery_specs_and_traits():
    """Verifies all surgery specs have traits and valid fields."""
    assert len(VEIN_SURGERY_REGISTRY) >= 4
    for s_id, spec in VEIN_SURGERY_REGISTRY.items():
        assert isinstance(spec, VeinSurgerySpec)
        assert len(spec.traits) > 0
        assert "vein_surgery" in spec.traits
        assert spec.backlash_damage_on_fail >= 10


def test_silver_needle_acupuncture_success(surgery_world):
    """Tests emergency needle acupuncture restores integrity and clears burnout."""
    patient = surgery_world.player
    doc = surgery_world.npcs["dr_lucas"]

    success, msg, data = ManaVeinRestorationEngine.perform_surgery(
        state=surgery_world,
        patient=patient,
        practitioner=doc,
        surgery_id="silver_needle_acupuncture",
        fixed_roll=15  # High roll -> Success
    )
    assert success is True
    assert "회로 복구 수술 성공" in msg
    circuit = ManaVeinRestorationEngine.get_circuit_state(patient)
    assert circuit["vein_integrity_pct"] == 55.0  # 40 + 15
    assert circuit["burnout_turns"] == 0  # Burnout cleared!
    assert patient.gold == 85  # 100 - 15


def test_arcane_dialysis_surgery_scars_and_mp_recovery(surgery_world):
    """Tests high-tier dialysis removes permanent scars and restores max MP."""
    patient = surgery_world.player
    doc = surgery_world.npcs["dr_lucas"]

    initial_max_mp = patient.max_mana
    success, msg, data = ManaVeinRestorationEngine.perform_surgery(
        state=surgery_world,
        patient=patient,
        practitioner=doc,
        surgery_id="arcane_dialysis_surgery",
        fixed_roll=16  # Success vs DC 15
    )
    assert success is True
    assert "에테르 투석 수술" in msg
    circuit = ManaVeinRestorationEngine.get_circuit_state(patient)
    assert circuit["vein_integrity_pct"] == 80.0  # 40 + 40
    assert circuit["scarred_veins"] == 1  # 2 - 1
    assert patient.max_mana > initial_max_mp  # MP restored!


def test_vein_surgery_failure_backlash_option_b(surgery_world):
    """
    User Decision Q2: Option B!
    Failure causes severe Arcane Backlash Shock (-15 HP and mana spasm/burnout).
    """
    patient = surgery_world.player
    quack = surgery_world.npcs["quack_bob"]
    initial_hp = patient.health

    # Attempt difficult dialysis with low-skill quack
    success, msg, data = ManaVeinRestorationEngine.perform_surgery(
        state=surgery_world,
        patient=patient,
        practitioner=quack,
        surgery_id="arcane_dialysis_surgery",
        fixed_roll=2  # Total 2 + (-1) = 1 vs DC 15 -> Disastrous failure!
    )
    assert success is False
    assert "수술 실패: 마나 역류 충격파" in msg
    assert "급성 마나 발작" in msg

    # Backlash damage applied
    spec = VEIN_SURGERY_REGISTRY["arcane_dialysis_surgery"]
    assert patient.health == initial_hp - spec.backlash_damage_on_fail
    circuit = ManaVeinRestorationEngine.get_circuit_state(patient)
    assert circuit["burnout_turns"] > 2  # Spasm extends burnout


def test_insufficient_gold_rejection(surgery_world):
    """Verifies surgery is refused if patient lacks the required surgery gold fee."""
    patient = surgery_world.player
    patient.gold = 5
    doc = surgery_world.npcs["dr_lucas"]

    success, msg, data = ManaVeinRestorationEngine.perform_surgery(
        state=surgery_world,
        patient=patient,
        practitioner=doc,
        surgery_id="silver_needle_acupuncture"
    )
    assert success is False
    assert "비용 부족" in msg


def test_brew_vein_tonic(surgery_world):
    """Tests herbalist brewing botanic plant into restorative circuit tonic."""
    brewer = surgery_world.npcs["dr_lucas"]
    success, msg, tonic_data = ManaVeinRestorationEngine.brew_vein_tonic(
        state=surgery_world,
        brewer=brewer,
        plant_id="lingzhi_mushroom",
        fixed_roll=18
    )
    assert success is True
    assert "탕약 조제 성공" in msg
    assert tonic_data["surgery_id"] == "herbal_vein_decoction"
    assert "traits" in tonic_data
