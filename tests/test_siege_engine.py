"""
Unit tests for SiegeWarfareEngine (Backlog #9)
Tests fortress multi-layer durability, siege engine damage/repair,
moat filling, 3-corps formation advantage matrix, morale rout cascades,
commando infiltration, and WorldState serialization compatibility.
"""
import pytest
from unittest.mock import patch

from src.world.state import WorldState
from src.world.infrastructure import Settlement
from src.world.siege_engine import (
    SiegeWarfareEngine,
    SiegeBattleState,
    FortressDefenseState,
    SiegeEngineInstance,
    TroopCorps,
    ArmyMoraleState,
    SIEGE_WEAPON_CATALOG,
    FORMATION_TACTICS_REGISTRY
)


def create_mock_settlement(
    wall_tier: int = 1,
    gate_type: str = "wooden_bar",
    moat_type: str = "none",
    battlement_type: str = "none",
    barrier_active: bool = False
) -> Settlement:
    return Settlement(
        id="settlement_test_citadel",
        name="바람협곡 철벽요새",
        nation_id="nation_iron_duchy",
        region_id="region_highlands",
        wall_defense_tier=wall_tier,
        gate_type=gate_type,
        moat_type=moat_type,
        battlement_type=battlement_type,
        magical_barrier_active=barrier_active,
        elevation_meters=120,
        siege_supplies_days=60,
        patrol_strength=50
    )


def test_fortress_initialization_from_settlement():
    """정주지 스탯으로부터 방어 구조물 다층 내구도가 정확히 초기화되는지 검증"""
    settlement = create_mock_settlement(
        wall_tier=2,
        gate_type="portcullis",
        moat_type="water_moat",
        battlement_type="machicolations",
        barrier_active=True
    )
    fortress = SiegeWarfareEngine.initialize_fortress_defense(settlement)

    assert fortress.settlement_id == "settlement_test_citadel"
    assert fortress.wall_tier == 2
    assert fortress.wall_durability == 3500.0
    assert fortress.max_wall_durability == 3500.0
    assert fortress.wall_hardness == 25.0
    assert not fortress.wall_breached

    assert fortress.gate_type == "portcullis"
    assert fortress.gate_durability == 1800.0
    assert fortress.gate_hardness == 20.0
    assert not fortress.gate_breached

    assert fortress.moat_type == "water_moat"
    assert fortress.moat_durability == 160.0
    assert not fortress.moat_cleared

    assert fortress.battlement_type == "machicolations"
    assert fortress.battlement_durability == 800.0

    assert fortress.barrier_active is True
    assert fortress.barrier_durability == 2500.0

    # 규칙 6 traits 탑재 확인
    assert len(fortress.traits) > 0
    assert "fortress_defense" in fortress.traits


def test_siege_engine_durability_and_fire_damage():
    """공성 병기의 내구도 삭감, 화공 취약성, 파괴 및 수리 역학 검증"""
    ram = SiegeWarfareEngine.create_siege_engine("battering_ram", "test_ram")
    assert ram.durability == 450.0
    assert ram.is_operational is True
    assert ram.is_destroyed is False
    assert len(ram.traits) > 0

    # 물리 피해 적용 (장갑치 12 경감)
    lost, destroyed = ram.take_damage(50.0, is_fire=False)
    assert lost == 38.0
    assert ram.durability == 450.0 - 38.0
    assert not destroyed

    # 화공 피해 적용 (화공 취약 배율 1.6x)
    fire_loss, _ = ram.take_damage(60.0, is_fire=True)
    # (60 - 12) * 1.6 = 48 * 1.6 = 76.8
    assert pytest.approx(fire_loss, 0.1) == 76.8

    # 수리 기능 검증
    repaired = ram.repair(50.0)
    assert repaired > 0

    # 완파 치명타 적용
    _, destroyed_now = ram.take_damage(1000.0, is_fire=True)
    assert destroyed_now is True
    assert ram.is_destroyed is True
    assert ram.is_operational is False
    assert ram.durability == 0.0


def test_moat_filling_and_ram_gate_assault():
    """해자가 메워지기 전에는 공성추가 접안 불가하고, 매립 후 성문을 파괴하는지 검증"""
    settlement = create_mock_settlement(
        wall_tier=1,
        gate_type="wooden_bar",
        moat_type="dry_ditch"
    )
    state = SiegeWarfareEngine.initialize_siege("siege_test_1", settlement)

    assert state.fortress.moat_cleared is False
    assert state.fortress.moat_durability == 100.0

    # 1턴 진행: 해자 매립 작업 시작 (아직 해자가 남아있으므로 성문은 공격받지 않음)
    logs = SiegeWarfareEngine.execute_advance_phase(state)
    assert any("해자 매립 작업" in l for l in logs)
    assert state.fortress.gate_durability == 350.0  # 성문 무피해

    # 해자를 강제로 완전 매립
    state.fortress.moat_durability = 0.0
    state.fortress.moat_cleared = True

    # 해자 매립 후 전진 페이즈 실행: 공성추가 성문을 직격해야 함
    logs2 = SiegeWarfareEngine.execute_advance_phase(state)
    assert any("충차 성문 직격" in l for l in logs2)
    assert state.fortress.gate_durability < 350.0


def test_artillery_bombardment_and_wall_breach():
    """투석기 포격으로 마도 결계가 먼저 피해를 흡수하고, 성벽이 붕괴되는지 검증"""
    settlement = create_mock_settlement(
        wall_tier=0,  # 목책 (내구도 400)
        barrier_active=True
    )
    state = SiegeWarfareEngine.initialize_siege("siege_test_2", settlement)
    state.fortress.barrier_durability = 100.0  # 결계를 약하게 설정

    # 1차 포격: 결계 파괴
    logs = SiegeWarfareEngine.execute_artillery_phase(state)
    assert any("마도 결계" in l for l in logs)

    # 성벽 내구도를 10으로 낮추고 포격 시 성벽 완파 검증
    state.fortress.wall_durability = 10.0
    state.fortress.barrier_active = False
    state.fortress.barrier_durability = 0.0

    logs2 = SiegeWarfareEngine.execute_artillery_phase(state)
    assert state.fortress.wall_breached is True
    assert any("성벽 완파" in l or "성벽" in l for l in logs2)


def test_formation_tactics_cavalry_vs_shieldwall():
    """3군 진형 상성 검증: 쐐기 기병 돌격이 장창 방패벽에 격돌 시 기병 자멸"""
    atk_cavalry = TroopCorps(
        corps_id="atk_cav",
        corps_name="기사단 쐐기 돌격대",
        troop_type="cavalry",
        current_count=300,
        initial_count=300,
        current_formation="wedge_charge"
    )
    def_infantry = TroopCorps(
        corps_id="def_inf",
        corps_name="근위대 장창 방패벽",
        troop_type="infantry",
        current_count=600,
        initial_count=600,
        current_formation="shield_wall"
    )
    settlement = create_mock_settlement()
    fortress = SiegeWarfareEngine.initialize_fortress_defense(settlement)

    atk_loss, def_loss, logs = SiegeWarfareEngine.resolve_formation_clash(
        atk_cavalry, def_infantry, fortress, in_breach=False
    )

    # 방패벽에 막힌 기병의 사상자가 보병 사상자보다 현저히 많아야 함
    assert atk_loss > def_loss
    assert any("장창 방패벽 저지" in l for l in logs)


def test_formation_tactics_cavalry_vs_unprepared():
    """3군 진형 상성 검증: 쐐기 기병이 산개/무방비 보병 상대로 압도적 돌파"""
    atk_cavalry = TroopCorps(
        corps_id="atk_cav",
        corps_name="기사단 쐐기 돌격대",
        troop_type="cavalry",
        current_count=300,
        initial_count=300,
        current_formation="wedge_charge"
    )
    def_infantry = TroopCorps(
        corps_id="def_inf",
        corps_name="동요하는 보병대",
        troop_type="infantry",
        current_count=400,
        initial_count=400,
        current_formation="loose_skirmish"
    )
    settlement = create_mock_settlement()
    fortress = SiegeWarfareEngine.initialize_fortress_defense(settlement)

    atk_loss, def_loss, logs = SiegeWarfareEngine.resolve_formation_clash(
        atk_cavalry, def_infantry, fortress, in_breach=True
    )

    # 기병의 일방적인 돌파 학살
    assert def_loss > atk_loss
    assert any("기병 전열 돌파" in l for l in logs)


def test_formation_tactics_archers_vs_shieldwall():
    """3군 진형 상성 검증: 일제 사격 화살비가 방패벽에 70% 차단됨"""
    atk_archers = TroopCorps(
        corps_id="atk_arc",
        corps_name="궁병대",
        troop_type="ranged",
        current_count=500,
        initial_count=500,
        current_formation="volley_rain"
    )
    def_infantry = TroopCorps(
        corps_id="def_inf",
        corps_name="방패벽 보병대",
        troop_type="infantry",
        current_count=500,
        initial_count=500,
        current_formation="shield_wall"
    )
    settlement = create_mock_settlement()
    fortress = SiegeWarfareEngine.initialize_fortress_defense(settlement)

    atk_loss, def_loss, logs = SiegeWarfareEngine.resolve_formation_clash(
        atk_archers, def_infantry, fortress, in_breach=False
    )

    assert any("방패벽 화살 차단" in l for l in logs)
    assert atk_loss == 0


def test_morale_cascade_and_rout():
    """사상자 누적 및 식량 고갈로 사기가 붕괴되고 패주(Rout)가 발생하는지 검증"""
    settlement = create_mock_settlement()
    state = SiegeWarfareEngine.initialize_siege("siege_test_rout", settlement)

    # 수비군 군량을 1로 만들어 다음 턴 고갈 유도
    state.fortress.supplies_remaining_days = 1
    # 수비군 병력의 60%를 사상 처리
    def_inf = state.defender_corps[0]
    def_inf.current_count = int(def_inf.initial_count * 0.3)

    logs = SiegeWarfareEngine.execute_morale_and_logistics_phase(state)
    assert state.fortress.supplies_remaining_days == 0
    assert any("농성 식량 고갈" in l for l in logs)

    # 사기를 15로 강제 저하시키고 재검사 시 전면 패주 판정
    state.defender_morale.morale = 15
    logs2 = SiegeWarfareEngine.execute_morale_and_logistics_phase(state)
    assert state.battle_concluded is True
    assert state.winner_side == "attacker"
    assert any("전면 패주" in l for l in logs2)


def test_commando_special_infiltration():
    """특공대 야간 침투 공작 (투석기 방화, 성문 개방) 검증"""
    settlement = create_mock_settlement()
    state = SiegeWarfareEngine.initialize_siege("siege_test_commando", settlement)

    # 주사위 20 고정 (대성공)
    with patch("src.world.dice.DiceEngine.roll_d20", return_value=20):
        res = SiegeWarfareEngine.execute_commando_action(state, "burn_catapult", infiltrator_stealth_mod=5)
        assert res["success"] is True
        assert any(e.is_destroyed for e in state.attacker_engines)

        res_gate = SiegeWarfareEngine.execute_commando_action(state, "open_gate", infiltrator_stealth_mod=5)
        assert res_gate["success"] is True
        assert state.fortress.gate_breached is True

    # 주사위 1 고정 (실패)
    with patch("src.world.dice.DiceEngine.roll_d20", return_value=1):
        res_fail = SiegeWarfareEngine.execute_commando_action(state, "open_gate", infiltrator_stealth_mod=0)
        assert res_fail["success"] is False
        assert "특공 실패" in res_fail["log"]


def test_full_advance_siege_turn_flow():
    """advance_siege_turn 전체 4단계 파이프라인 통합 흐름 검증"""
    settlement = create_mock_settlement(moat_type="dry_ditch")
    state = SiegeWarfareEngine.initialize_siege("siege_test_flow", settlement)

    assert state.day_count == 1
    turn_logs = SiegeWarfareEngine.advance_siege_turn(state)

    assert state.day_count == 2
    assert len(turn_logs) > 0
    assert any("1일차 작전 전개" in l for l in turn_logs)


def test_external_llm_prompt_generation():
    """규칙 8 준수 외부 대형 LLM(GPT/Claude) 서사 묘사 프롬프트 생성기 검증"""
    settlement = create_mock_settlement()
    state = SiegeWarfareEngine.initialize_siege("siege_test_llm", settlement)
    logs = ["성벽에 투석탄이 명중하여 석재 파편이 비산했습니다."]

    prompt = SiegeWarfareEngine.generate_external_llm_prompt(state, logs)
    assert "[시스템 컨텍스트: Quilltale TRPG 대규모 성벽 공성전 시뮬레이션 결과]" in prompt
    assert "바람협곡 철벽요새" in prompt
    assert "성벽 내구도" in prompt
    assert "사기:" in prompt
    assert "석재 파편이 비산했습니다." in prompt


def test_worldstate_serialization_compatibility():
    """WorldState의 active_sieges 저장/로드 및 세이브 하위 호환성 검증"""
    state = WorldState()
    assert hasattr(state, "active_sieges")
    assert isinstance(state.active_sieges, dict)

    settlement = create_mock_settlement()
    siege = SiegeWarfareEngine.initialize_siege("siege_save_01", settlement)
    state.active_sieges["siege_save_01"] = {
        "siege_id": siege.siege_id,
        "settlement_id": siege.settlement_id,
        "day_count": siege.day_count,
        "wall_durability": siege.fortress.wall_durability,
        "traits": siege.traits
    }

    raw = state.to_dict()
    assert "active_sieges" in raw
    assert "siege_save_01" in raw["active_sieges"]

    loaded_state = WorldState.from_dict(raw)
    assert "siege_save_01" in loaded_state.active_sieges
    assert loaded_state.active_sieges["siege_save_01"]["wall_durability"] == 1500.0
