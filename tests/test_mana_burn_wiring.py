"""
Integration tests for ManaBurnEngine wiring in TwoPassEngine and ActionValidator.
Verifies deterministic Pass 1 overchanneling, burnout silence, circuit damage,
remedy repairs, and prompt context serialization.
"""
from src.world.state import WorldState, Location, Skill
from src.world.two_pass_engine import TwoPassEngine
from src.world.mana_burn_engine import ManaBurnEngine


def setup_world():
    state = WorldState()
    loc = Location(
        id="sanctum",
        name="비전 성소",
        description="마력의 흐름이 교차하는 지하 성소.",
        exits={},
        npcs=[],
        traits=["성소", "실내"]
    )
    state.locations["sanctum"] = loc
    state.player.location = "sanctum"

    # Ensure test skill exists (generic elemental spell)
    fireball = Skill(
        id="sk_fireball",
        name="화염구",
        resource_type="mana",
        resource_cost=20,
        base_value=25,
        scaling_stat="int",
        scaling_factor=1.5,
        category="elemental",
        cooldown_turns=1
    )
    state.skills_db["sk_fireball"] = fireball
    state.player.skills.append("sk_fireball")
    return state


def test_mana_burnout_silence_blocks_magic():
    """회로 과열(Burnout) 시 마법 영창이 물리적으로 차단되는지 검증."""
    state = setup_world()
    circuit = ManaBurnEngine.get_circuit_state(state.player)
    circuit.burnout_turns = 2
    state.player.mana_burn_state = circuit.to_dict()

    action = "화염구 시전하여 적을 공격한다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert not fact_sheet.is_valid
    assert "마나 회로 과열" in fact_sheet.rejection_reason
    # Turn tick reduces 2 -> 1
    assert "잔여 침묵: 1턴" in fact_sheet.rejection_reason


def test_unqualified_caster_cannot_overchannel():
    """대가/혈마법 지식이 없는 일반 마법사는 마나 부족 시 생명력 연소가 불가능함을 검증."""
    state = setup_world()
    state.player.mana = 5  # Cost is 20, shortage = 15
    state.player.traits = ["scholar", "curious"]  # No sacrifice / blood traits

    action = "화염구 시전하여 공격한다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert not fact_sheet.is_valid
    assert "일반 마법사는 생명력을 마나로 치환할 수 없습니다" in fact_sheet.rejection_reason


def test_blood_mage_overchannel_executes_in_pass1():
    """혈마법 특성 보유자는 마나 부족 시 생명력을 연소하여 과충전 영창에 성공하는지 검증."""
    state = setup_world()
    state.player.mana = 0  # 0 mana available
    state.player.health = 80
    state.player.traits = ["blood_magic"]  # Qualified sacrifice trait

    circuit = ManaBurnEngine.get_circuit_state(state.player)
    initial_integrity = circuit.vein_integrity_pct

    action = "화염구 시전하여 공격한다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid
    assert fact_sheet.mana_burn_summary is not None
    assert "생명력" in fact_sheet.mana_burn_summary

    # Player HP must have been consumed (20 shortage * 2 HP base = 40 HP cost or similar)
    assert state.player.health < 80

    # Circuit integrity must have suffered strain
    updated_circuit = ManaBurnEngine.get_circuit_state(state.player)
    assert updated_circuit.vein_integrity_pct < initial_integrity

    # Prompt context must include GM narrative directives
    prompt_ctx = fact_sheet.to_prompt_context()
    assert "마나 과부하 및 회로 상태" in prompt_ctx
    assert "생명력 연소 과충전" in prompt_ctx


def test_circuit_burnout_tick_cooling():
    """턴 경과 시 마나 과열 침묵이 자연 냉각되는지 검증."""
    state = setup_world()
    circuit = ManaBurnEngine.get_circuit_state(state.player)
    circuit.burnout_turns = 1
    state.player.mana_burn_state = circuit.to_dict()

    action = "주변을 조용히 관찰한다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    updated_circuit = ManaBurnEngine.get_circuit_state(state.player)
    assert updated_circuit.burnout_turns == 0
    assert any("마나 회로 냉각" in log for log in fact_sheet.status_tick_logs)


def test_max_mp_penalty_deterministic_reader():
    """회로 파열 영구 흉터로 인한 max_mp_penalty가 유효 최대 마나에 결정론적으로 감산 반영되는지 검증."""
    state = setup_world()
    state.player.max_mana = 60
    base_eff_mana = state.player.max_mana_effective

    circuit = ManaBurnEngine.get_circuit_state(state.player)
    circuit.max_mp_penalty = 15
    state.player.mana_burn_state = circuit.to_dict()

    assert state.player.max_mana_effective == base_eff_mana - 15


def test_mana_circuit_remedy_repair():
    """마나 안정제 복용 시 회로 건전도가 복구되는지 검증."""
    state = setup_world()
    circuit = ManaBurnEngine.get_circuit_state(state.player)
    circuit.vein_integrity_pct = 50.0
    circuit.burnout_turns = 2
    state.player.mana_burn_state = circuit.to_dict()

    action = "가방에서 마나 안정제를 꺼내 마시며 회로를 진정시킨다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    updated_circuit = ManaBurnEngine.get_circuit_state(state.player)
    assert updated_circuit.vein_integrity_pct == 75.0
    assert updated_circuit.burnout_turns == 0
    assert any("마나 안정제" in log for log in fact_sheet.quest_progress_logs)
