"""
Integration tests for CampsiteRestEngine wiring into TwoPassEngine and WorldState.
Verifies campsite setup, campfire lighting, sentry shifts, peaceful sleep recovery,
night ambush enemy spawning, and combat prevention.
"""
import pytest
from src.world.state import WorldState, Player, NPC, Location, Item
from src.world.two_pass_engine import TwoPassEngine
from src.world.campsite_engine import CampsiteRestEngine


@pytest.fixture
def base_camp_world():
    state = WorldState()
    loc = Location(
        id="wild_forest",
        name="깊은 안개 숲",
        description="인적이 드문 깊은 숲속 공터다.",
        exits={},
        items=[]
    )
    state.locations["wild_forest"] = loc
    state.player = Player(
        name="탐험가 로렌",
        location="wild_forest",
        health=50,
        max_health=100,
        mana=30,
        max_mana=60,
        fatigue=70,
        strength=12,
        agility=14,
        perception=14,
        inventory=[]
    )
    return state


def test_campsite_setup_wiring(base_camp_world):
    """야영지 구축 행동 시 Pass 1 FactSheet 및 야영지 상태 반영 검증."""
    tent_item = Item(id="travel_tent", name="휴대용 야영 텐트", description="야외 숙영용 텐트", location="inventory")
    base_camp_world.items["travel_tent"] = tent_item
    base_camp_world.player.inventory.append("travel_tent")

    fact = TwoPassEngine.compute_pass1("주변에 텐트를 치고 경보 덫을 설치하여 안전한 야영지를 구축한다.", base_camp_world)

    assert fact.is_valid is True
    assert fact.campsite_summary is not None
    assert "야영지 구축 완료" in fact.campsite_summary
    assert "방풍/방수 야영 텐트" in fact.campsite_summary
    assert "외곽 방어 덫" in fact.campsite_summary
    assert "⛺ [야영지 및 야간 숙영 판정" in fact.to_prompt_context()

    camp = CampsiteRestEngine.get_campsite(base_camp_world)
    assert camp.has_tent is True
    assert camp.has_perimeter_traps is True


def test_campfire_lighting_wiring(base_camp_world):
    """모닥불 점화 행동 시 열원 확보, 어그로 위험도 증가 및 장작 소모 검증."""
    firewood = Item(id="dry_firewood", name="마른 참나무 장작", description="잘 마른 장작", location="inventory")
    base_camp_world.items["dry_firewood"] = firewood
    base_camp_world.player.inventory.append("dry_firewood")

    camp = CampsiteRestEngine.get_campsite(base_camp_world)
    initial_aggro = camp.aggro_risk

    fact = TwoPassEngine.compute_pass1("마른 참나무 장작을 모아 모닥불을 피운다.", base_camp_world)

    assert fact.is_valid is True
    assert fact.campsite_summary is not None
    assert "모닥불 점화" in fact.campsite_summary
    assert camp.campfire_active is True
    assert camp.aggro_risk > initial_aggro
    assert base_camp_world.environment.has_heat_source is True


def test_sentry_shift_assignment_wiring(base_camp_world):
    """불침번 배정 행동 시 동료 감각 스탯 보정치 연산 및 교대 등록 검증."""
    companion = NPC(
        id="companion_kael",
        name="용병 카엘",
        description="듬직한 용병 동료",
        location="wild_forest",
        alive=True,
        disposition="friendly",
        perception=16
    )
    base_camp_world.npcs["companion_kael"] = companion
    base_camp_world.locations["wild_forest"].npcs.append("companion_kael")

    fact = TwoPassEngine.compute_pass1("오늘 밤의 불침번을 배정하고 교대로 경계를 선다.", base_camp_world)

    assert fact.is_valid is True
    assert fact.campsite_summary is not None
    assert "불침번 편성 완료" in fact.campsite_summary
    assert "용병 카엘" in fact.campsite_summary

    camp = CampsiteRestEngine.get_campsite(base_camp_world)
    assert len(camp.sentry_shifts) >= 2
    assert camp.sentry_shifts[0].companion_id == "player"
    assert camp.sentry_shifts[1].companion_id == "companion_kael"
    assert camp.sentry_shifts[1].perception_bonus == 3  # (16 - 10) // 2


def test_campsite_peaceful_rest_wiring(base_camp_world, monkeypatch):
    """안전 야영 휴식 시 8시간 경과, 피로도 회복 및 체력/마나 회복 검증."""
    monkeypatch.setattr("random.random", lambda: 0.99)

    init_hp = base_camp_world.player.health
    init_mp = base_camp_world.player.mana

    fact = TwoPassEngine.compute_pass1("모닥불 곁에서 침낭을 펴고 야영지에서 잠을 잔다.", base_camp_world)

    assert fact.is_valid is True
    assert fact.campsite_summary is not None
    assert "평화로운 밤" in fact.campsite_summary
    assert "수면 완료" in fact.campsite_summary

    assert base_camp_world.player.fatigue < 70
    assert base_camp_world.player.health > init_hp
    assert base_camp_world.player.mana > init_mp


def test_campsite_ambush_spawns_enemies(base_camp_world, monkeypatch):
    """야간 기습 발생 시 침입자 몬스터 실제 스폰 및 전투 돌입 검증."""
    monkeypatch.setattr("random.random", lambda: 0.01)

    initial_npc_count = len(base_camp_world.npcs)

    fact = TwoPassEngine.compute_pass1("야영지에서 잠을 청하며 밤을 보낸다.", base_camp_world)

    assert fact.is_valid is True
    assert fact.campsite_summary is not None
    assert "야간 기습 발생" in fact.campsite_summary

    current_npcs = base_camp_world.npcs
    assert len(current_npcs) > initial_npc_count
    ambush_npcs = [n for n in current_npcs.values() if "ambush" in n.id]
    assert len(ambush_npcs) >= 1
    for an in ambush_npcs:
        assert an.alive is True
        assert an.disposition == "hostile"
        assert an.location == "wild_forest"
        assert an.id in base_camp_world.locations["wild_forest"].npcs


def test_campsite_combat_prevention(base_camp_world):
    """적대적 몬스터가 있는 교전 상황에서 야영/수면 시도 시 사전 차단 검증."""
    hostile_goblin = NPC(
        id="hostile_goblin",
        name="사나운 고블린 척후병",
        description="날카로운 단도를 든 고블린",
        location="wild_forest",
        alive=True,
        disposition="hostile"
    )
    base_camp_world.npcs["hostile_goblin"] = hostile_goblin
    base_camp_world.locations["wild_forest"].npcs.append("hostile_goblin")

    fact = TwoPassEngine.compute_pass1("모닥불을 피우고 텐트를 쳐서 야영한다.", base_camp_world)

    assert fact.is_valid is False
    assert "교전 중에는 야영지를 구축하거나 잠에 들 수 없습니다" in fact.rejection_reason