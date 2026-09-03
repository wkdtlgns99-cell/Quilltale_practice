"""
Unit tests for Deterministic Hidden Boss & Elite Monster Encounter Engine.
Tests:
1. Abyssal Stalker spawn on midnight + low hygiene (scent).
2. Frost Wraith spawn on blizzard + subzero temperature on mountain pass.
3. Thunder Catfish spawn on downpour + swamp road.
4. Scale Merchant spawn on carrying contraband items in urban alley.
5. Defeated boss suppression (no duplicate spawns).
6. TwoPassEngine integration and Pass 1 fact sheet reporting.
"""
import pytest
from src.world.state import WorldState, Location, Player, NPC, Item, EnvironmentalMetrics
from src.world.geography import RoadType, RoadConnection
from src.world.hidden_encounter_engine import HiddenEncounterEngine, HIDDEN_BOSS_REGISTRY
from src.world.two_pass_engine import TwoPassEngine


def test_abyssal_stalker_midnight_scent_trigger():
    """Midnight + player hygiene <= 30 triggers Abyssal Stalker."""
    state = WorldState()
    loc = Location(id="dark_forest", name="검은 숲", description="", exits={}, terrain="forest")
    state.locations = {"dark_forest": loc}
    state.player.location = "dark_forest"

    # Set time to 01:00 AM (midnight)
    # total_minutes: start_minute is 480 (08:00 AM). 01:00 next day is 25 hours = 1500 mins (or elapsed = 1020 mins)
    state.player.time_elapsed_minutes = 1020  # 480 + 1020 = 1500 mins -> 25 hours -> hour 1
    assert state.current_hour == 1

    # High hygiene: Should NOT trigger
    state.player.hygiene_level = 90
    enc = HiddenEncounterEngine.evaluate_encounter(state, "주변을 살핀다")
    assert enc is None

    # Low hygiene (blood scent <= 30): SHOULD trigger
    state.player.hygiene_level = 20
    enc = HiddenEncounterEngine.evaluate_encounter(state, "주변을 살핀다")
    assert enc is not None
    assert enc["triggered"] is True
    assert enc["boss_id"] == "hidden_abyssal_stalker"
    assert "심연을 걷는 도살자" in enc["boss_name"]

    # NPC successfully spawned in location
    assert "hidden_abyssal_stalker" in state.npcs
    stalker = state.npcs["hidden_abyssal_stalker"]
    assert stalker.alive is True
    assert stalker.disposition == "hostile"
    assert stalker.health == 140
    assert "hidden_abyssal_stalker" in loc.npcs
    assert "skill_abyssal_rend" in state.skills_db


def test_frost_wraith_subzero_mountain_trigger():
    """Blizzard + subzero temp on mountain pass road triggers Frost Wraith."""
    state = WorldState()
    loc = Location(id="snow_peak", name="서리 고개", description="", exits={}, terrain="mountains")
    loc.roads = {
        "dest": RoadConnection(destination_id="dest", distance_km=5.0, road_type=RoadType.MOUNTAIN_PASS)
    }
    state.locations = {"snow_peak": loc}
    state.player.location = "snow_peak"

    state.environment.weather = "폭설"
    state.environment.temperature_celsius = -8.0

    enc = HiddenEncounterEngine.evaluate_encounter(state, "전진한다")
    assert enc is not None
    assert enc["boss_id"] == "hidden_frost_wraith"
    assert "서리 망령" in enc["boss_name"]
    assert "hidden_frost_wraith" in state.npcs
    assert "skill_frost_shiver" in state.skills_db


def test_thunder_catfish_downpour_swamp_trigger():
    """Downpour on swamp road triggers Thunder Catfish."""
    state = WorldState()
    loc = Location(id="marsh_crossing", name="늪지 여울목", description="", exits={}, terrain="swamp")
    loc.roads = {
        "dest": RoadConnection(destination_id="dest", distance_km=5.0, road_type=RoadType.SWAMP_TRAIL)
    }
    state.locations = {"marsh_crossing": loc}
    state.player.location = "marsh_crossing"

    state.environment.weather = "폭우"

    enc = HiddenEncounterEngine.evaluate_encounter(state, "여울목을 건넌다")
    assert enc is not None
    assert enc["boss_id"] == "hidden_thunder_catfish"
    assert "벼락 메기" in enc["boss_name"]
    assert "hidden_thunder_catfish" in state.npcs
    assert "skill_ground_discharge" in state.skills_db


def test_scale_merchant_contraband_trigger():
    """Possessing illicit contraband in urban setting triggers Scale Merchant."""
    state = WorldState()
    loc = Location(id="back_alley", name="어두운 뒷골목", description="", exits={}, terrain="urban")
    state.locations = {"back_alley": loc}
    state.player.location = "back_alley"

    # Without contraband: No encounter
    enc = HiddenEncounterEngine.evaluate_encounter(state, "골목길을 걷는다")
    assert enc is None

    # Give player contraband item
    c_item = Item(
        id="darkweed_pack",
        name="【암시장 금지 약초 (밀수품)】",
        description="제국에서 금지된 환각성 밀수품.",
        location="inventory",
        properties={"contraband_tier": 2, "is_contraband": True}
    )
    state.items["darkweed_pack"] = c_item
    state.player.inventory.append("darkweed_pack")

    enc = HiddenEncounterEngine.evaluate_encounter(state, "골목길을 걷는다")
    assert enc is not None
    assert enc["boss_id"] == "hidden_scale_merchant"
    assert "도살장 갈고리의 저울상인" in enc["boss_name"]
    assert "skill_karmic_retribution" in state.skills_db


def test_defeated_boss_no_duplicate_spawns():
    """Defeated bosses never re-spawn even if trigger conditions remain active."""
    state = WorldState()
    loc = Location(id="dark_forest", name="검은 숲", description="", exits={}, terrain="forest")
    state.locations = {"dark_forest": loc}
    state.player.location = "dark_forest"
    state.player.time_elapsed_minutes = 1020
    state.player.hygiene_level = 10

    # 1. First trigger
    enc1 = HiddenEncounterEngine.evaluate_encounter(state, "탐색한다")
    assert enc1 is not None
    boss = state.npcs["hidden_abyssal_stalker"]

    # 2. Boss is defeated
    boss.alive = False
    boss.health = 0
    state.world_facts.append("플레이어가 [심연을 걷는 도살자]를 처치함")

    # 3. Next turn with same condition: Must NOT spawn again
    enc2 = HiddenEncounterEngine.evaluate_encounter(state, "다시 탐색한다")
    assert enc2 is None


def test_two_pass_engine_hidden_encounter_integration():
    """TwoPassEngine Pass 1 detects hidden boss and injects encounter into fact sheet."""
    state = WorldState()
    loc = Location(id="dark_forest", name="검은 숲", description="", exits={}, terrain="forest")
    state.locations = {"dark_forest": loc}
    state.player.location = "dark_forest"
    state.player.time_elapsed_minutes = 1020
    state.player.hygiene_level = 15

    fact_sheet = TwoPassEngine.compute_pass1("어둠 속에서 발소리를 죽이며 이동한다", state)
    assert fact_sheet.is_valid

    # Check that boss encounter was reported
    quest_logs = " ".join(fact_sheet.quest_progress_logs)
    npc_logs = " ".join(fact_sheet.npc_skill_logs)

    assert "히든 BOSS 조우" in quest_logs or "히든" in quest_logs
    assert "심연을 걷는 도살자" in quest_logs or "심연을 걷는 도살자" in npc_logs
    assert "약점 공략 힌트" in npc_logs
