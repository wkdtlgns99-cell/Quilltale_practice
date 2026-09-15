"""Integration tests: ManaVeinRestorationEngine wired via TwoPassEngine.compute_pass1().
DoD Gate: AGENTS.md Wiring rule 5.
"""
import pytest
from src.world.state import WorldState, Player, NPC, Location
from src.world.two_pass_engine import TwoPassEngine, DeterministicFactSheet
from src.world.mana_burn_engine import ManaBurnEngine
from src.world.vein_restoration_engine import ManaVeinRestorationEngine


@pytest.fixture
def damaged_state():
    state = WorldState()
    state.locations["arcane_clinic"] = Location(
        id="arcane_clinic", name="비전 의무관",
        description="마나 회로 전문 치료소", exits={},
        traits=["clinic", "magic"]
    )
    state.player = Player(
        name="마법사 카이", location="arcane_clinic",
        health=40, max_health=50, mana=5, max_mana=30, gold=200,
        intelligence=10, wisdom=10,
    )
    circuit = ManaBurnEngine.get_circuit_state(state.player)
    circuit.vein_integrity_pct = 35.0
    circuit.scarred_veins = 2
    circuit.burnout_turns = 3
    circuit.max_mp_penalty = 20
    state.npcs["surgeon"] = NPC(
        id="surgeon", name="비전 외과의", description="집도의",
        location="arcane_clinic", intelligence=18, wisdom=16,
        traits=["doctor", "arcane_surgeon"]
    )
    return state


def test_surgery_triggers_via_compute_pass1(damaged_state):
    """에테르 투석 수술이 compute_pass1()을 통해 vein_restoration_summary를 채워야 한다."""
    state = damaged_state
    gold_before = state.player.gold
    fs = TwoPassEngine.compute_pass1("비전 의사에게 에테르 투석 수술을 받는다", state)
    assert fs.vein_restoration_summary is not None
    assert state.player.gold <= gold_before
    assert any("수술" in lg or "회로" in lg for lg in fs.quest_progress_logs)


def test_surgery_divine_path(damaged_state):
    """성령 기적 봉합 키워드가 divine_artery_miracle 경로를 타야 한다."""
    state = damaged_state
    state.npcs["priest"] = NPC(
        id="priest", name="사제", description="신전 고위 사제",
        location="arcane_clinic", intelligence=16, wisdom=20,
        traits=["priest", "사제"]
    )
    gold_before = state.player.gold
    fs = TwoPassEngine.compute_pass1("사제에게 성맥 재건의 기적 봉합을 부탁한다", state)
    assert fs.vein_restoration_summary is not None
    assert state.player.gold <= gold_before


def test_surgery_no_gold_logs_failure(damaged_state):
    """골드 부족 시 quest_progress_logs에 실패 메시지가 기록되어야 한다."""
    state = damaged_state
    state.player.gold = 5
    fs = TwoPassEngine.compute_pass1("비전 의사에게 에테르 투석 수술을 받는다", state)
    assert any("부족" in lg or "골드" in lg or "수술" in lg for lg in fs.quest_progress_logs)
    assert state.player.gold == 5


def test_circuit_dict_compat():
    """ManaBurnEngine(ManaCircuitState)을 VeinRestorationEngine이 dict로 읽어야 한다."""
    player = Player(name="테스트 마법사")
    circuit_obj = ManaBurnEngine.get_circuit_state(player)
    circuit_obj.vein_integrity_pct = 55.0
    circuit_obj.scarred_veins = 1
    circuit_dict = ManaVeinRestorationEngine.get_circuit_state(player)
    assert isinstance(circuit_dict, dict)
    assert circuit_dict["vein_integrity_pct"] == 55.0
    assert circuit_dict["scarred_veins"] == 1


def test_prompt_context_includes_surgery_section():
    """vein_restoration_summary 세팅 시 to_prompt_context()에 마나 혈맥 수술 섹션 포함."""
    fs = DeterministicFactSheet(action="수술")
    fs.vein_restoration_summary = "수술 성공: 회로 건전도 35pct to 75pct"
    ctx = fs.to_prompt_context()
    assert "마나 혈맥 수술" in ctx
    assert "Mana Vein Restoration" in ctx
