"""
Unit tests for CorpseEcologyEngine (Battlefield Corpse Ecology, Decay & Scavenger System).
Verifies User Decision Q1 (Hybrid Option A + B):
- Decay stages: fresh -> bloated -> rotting -> skeleton
- Rotting stage spoils organic loot and attracts terrestrial scavengers (wolves/ghouls)
- Scavengers damage/scatter loot and gold
- Disease warning vector for corpse decay fever
- Looting mechanics and sanitary disposal (burn / bury)
"""
import pytest
import random
from src.world.state import WorldState, Player, NPC, Location
from src.world.corpse_ecology_engine import CorpseEcologyEngine, CorpseInstance


@pytest.fixture
def base_world():
    ws = WorldState()
    loc = Location(
        id="battleground_plains",
        name="피로 물든 격전 평원",
        description="전투의 상흔이 짙게 남은 황량한 평원.",
        exits={},
        traits=["전장", "황무지"]
    )
    ws.locations[loc.id] = loc
    ws.player.location = loc.id
    ws.player.inventory = []
    ws.player.gold = 10
    return ws


def test_corpse_registration(base_world):
    victim = NPC(
        id="goblin_scout_01",
        name="고블린 척후병",
        description="초라한 고블린 척후병",
        location="battleground_plains",
        gold=25,
        inventory=["dried_meat", "rusty_dagger"]
    )
    corpse = CorpseEcologyEngine.register_corpse_from_killed_actor(base_world, victim, killer=base_world.player)

    assert corpse.corpse_id in base_world.active_corpses
    assert corpse.origin_name == "고블린 척후병"
    assert corpse.decay_stage == "fresh"
    assert corpse.gold == 25
    assert len(corpse.inventory_loot) == 2
    assert not corpse.is_looted
    assert not corpse.is_burned
    assert not corpse.is_buried


def test_corpse_decay_stages_progression(base_world):
    victim = NPC(
        id="bandit_01",
        name="산적 졸개",
        description="평원의 산적 졸개",
        location="battleground_plains",
        gold=50,
        inventory=[]
    )
    corpse = CorpseEcologyEngine.register_corpse_from_killed_actor(base_world, victim)

    # 1. 30 min tick -> still fresh
    logs = CorpseEcologyEngine.process_turn_corpse_decay(base_world, delta_minutes=30)
    c_data = CorpseInstance.from_dict(base_world.active_corpses[corpse.corpse_id])
    assert c_data.decay_stage == "fresh"

    # 2. Advance to 90 min -> bloated stage, crow scavengers
    logs = CorpseEcologyEngine.process_turn_corpse_decay(base_world, delta_minutes=60)
    c_data = CorpseInstance.from_dict(base_world.active_corpses[corpse.corpse_id])
    assert c_data.decay_stage == "bloated"
    assert "검은 까마귀 떼" in c_data.attracted_scavengers
    assert any("까마귀" in l for l in logs)

    # 3. Advance to 210 min -> rotting stage (User Q1: rotting 3~6 hours)
    logs = CorpseEcologyEngine.process_turn_corpse_decay(base_world, delta_minutes=120)
    c_data = CorpseInstance.from_dict(base_world.active_corpses[corpse.corpse_id])
    assert c_data.decay_stage == "rotting"
    assert c_data.decay_fever_spread is True
    assert any("Rotting" in l or "부패" in l for l in logs)

    # 4. Advance to 400 min -> skeleton stage
    logs = CorpseEcologyEngine.process_turn_corpse_decay(base_world, delta_minutes=190)
    c_data = CorpseInstance.from_dict(base_world.active_corpses[corpse.corpse_id])
    assert c_data.decay_stage == "skeleton"
    assert any("백골화" in l for l in logs)


def test_corpse_hybrid_loot_decay_and_scavengers(base_world):
    """Verifies User Q1: Perishables rot (A) + Scavengers scatter/damage loot (B)."""
    victim = NPC(
        id="orc_warrior_01",
        name="오크 전사",
        description="전장의 오크 전사",
        location="battleground_plains",
        gold=100,
        inventory=[
            {"id": "orc_ration", "name": "보존 식량 고기", "type": "food", "spoiled": False},
            {"id": "steel_axe", "name": "강철 손도끼", "type": "weapon", "spoiled": False}
        ]
    )
    corpse = CorpseEcologyEngine.register_corpse_from_killed_actor(base_world, victim)

    # Deterministic RNG to guarantee scavenger spawn
    class MockRng:
        def random(self):
            return 0.1
        def randint(self, a, b):
            return 0

    mock_rng = MockRng()
    # Fast-forward directly into rotting stage (200 minutes)
    corpse_data = CorpseInstance.from_dict(base_world.active_corpses[corpse.corpse_id])
    corpse_data.time_since_death_minutes = 180
    base_world.active_corpses[corpse.corpse_id] = corpse_data.to_dict()

    logs = CorpseEcologyEngine.process_turn_corpse_decay(base_world, delta_minutes=30, rng=mock_rng)
    c_after = CorpseInstance.from_dict(base_world.active_corpses[corpse.corpse_id])

    assert c_after.decay_stage == "rotting"
    # Option A check: organic food spoiled
    food_item = next(it for it in c_after.inventory_loot if "식량" in it["name"] or "고기" in it["name"])
    assert food_item["spoiled"] is True
    assert "썩어문드러진" in food_item["name"]

    # Option B check: scavenger wolves attracted, gold scattered
    assert "굶주린 들개 및 늑대 무리" in c_after.attracted_scavengers
    assert c_after.gold < 100
    assert any("청소 야수 유인" in l for l in logs)


def test_loot_corpse_mechanics(base_world):
    victim = NPC(
        id="fallen_knight",
        name="쓰러진 기사",
        description="전투 중 쓰러진 기사",
        location="battleground_plains",
        gold=60,
        inventory=[{"id": "iron_sword", "name": "기사의 강철검", "type": "weapon", "spoiled": False}]
    )
    corpse = CorpseEcologyEngine.register_corpse_from_killed_actor(base_world, victim)

    # Player loots corpse
    success, msg, items = CorpseEcologyEngine.loot_corpse(base_world, base_world.player, corpse.corpse_id)
    assert success is True
    assert base_world.player.gold == 10 + 60
    assert "iron_sword" in base_world.player.inventory
    assert len(items) == 1

    # Second looting attempt fails
    success2, msg2, items2 = CorpseEcologyEngine.loot_corpse(base_world, base_world.player, corpse.corpse_id)
    assert success2 is False
    assert "이미 누군가에 의해" in msg2


def test_dispose_corpse_burn_and_bury(base_world):
    v1 = NPC(id="plague_corpse_1", name="역병 감염자 A", description="감염된 시체", location="battleground_plains")
    v2 = NPC(id="plague_corpse_2", name="역병 감염자 B", description="감염된 시체", location="battleground_plains")
    c1 = CorpseEcologyEngine.register_corpse_from_killed_actor(base_world, v1)
    c2 = CorpseEcologyEngine.register_corpse_from_killed_actor(base_world, v2)

    # Burn c1
    b_success, b_msg = CorpseEcologyEngine.dispose_corpse(base_world, base_world.player, c1.corpse_id, method="burn")
    assert b_success is True
    assert "시신 소각 화장" in b_msg
    c1_after = CorpseInstance.from_dict(base_world.active_corpses[c1.corpse_id])
    assert c1_after.is_burned is True
    assert c1_after.decay_stage == "ashes"

    # Bury c2
    m_success, m_msg = CorpseEcologyEngine.dispose_corpse(base_world, base_world.player, c2.corpse_id, method="bury")
    assert m_success is True
    assert "경건한 가매장" in m_msg
    c2_after = CorpseInstance.from_dict(base_world.active_corpses[c2.corpse_id])
    assert c2_after.is_buried is True
