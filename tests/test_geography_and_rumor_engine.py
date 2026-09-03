import pytest
from src.world.state import WorldState, Player, NPC, Location
from src.world.geography import GeographyEngine, RoadConnection, RoadType
from src.world.rumor_diffusion_engine import RumorDiffusionEngine, RumorWave


@pytest.fixture
def geo_world():
    state = WorldState()
    # 1. Village A (Origin)
    loc_a = Location(
        id="village_a", name="빛의 마을", description="평화로운 시골 마을",
        exits={"east": "crossroads_b", "south": "swamp_c"},
        coordinates=(0.0, 0.0), terrain="plains"
    )
    # 2. Crossroads B (Highway node)
    loc_b = Location(
        id="crossroads_b", name="중앙 갈림길", description="가도가 만나는 곳",
        exits={"west": "village_a", "east": "city_d"},
        coordinates=(10.0, 0.0), terrain="plains"
    )
    # 3. Swamp C (Swamp node)
    loc_c = Location(
        id="swamp_c", name="검은 수렁", description="축축하고 위험한 늪지",
        exits={"north": "village_a", "east": "city_d"},
        coordinates=(5.0, -10.0), terrain="swamp"
    )
    # 4. City D (Capital node)
    loc_d = Location(
        id="city_d", name="솔리스 수도", description="거대한 대도시",
        exits={"west": "crossroads_b", "southwest": "swamp_c", "north": "remote_village_e"},
        coordinates=(30.0, 0.0), terrain="urban"
    )
    # 5. Remote Village E (Isolated remote village)
    loc_e = Location(
        id="remote_village_e", name="은둔자의 깡촌", description="첩첩산중 외딴 오지",
        exits={"south": "city_d"},
        coordinates=(30.0, 50.0), terrain="mountains"
    )

    # Roads configuration
    # A -> B: 10km paved highway
    loc_a.roads["crossroads_b"] = RoadConnection(
        destination_id="crossroads_b", distance_km=10.0, road_type=RoadType.PAVED_HIGHWAY
    )
    # B -> D: 20km paved highway
    loc_b.roads["city_d"] = RoadConnection(
        destination_id="city_d", distance_km=20.0, road_type=RoadType.PAVED_HIGHWAY
    )
    # A -> C: 15km swamp trail
    loc_a.roads["swamp_c"] = RoadConnection(
        destination_id="swamp_c", distance_km=15.0, road_type=RoadType.SWAMP_TRAIL
    )
    # C -> D: 25km swamp trail
    loc_c.roads["city_d"] = RoadConnection(
        destination_id="city_d", distance_km=25.0, road_type=RoadType.SWAMP_TRAIL
    )
    # D -> E: 50km mountain pass
    loc_d.roads["remote_village_e"] = RoadConnection(
        destination_id="remote_village_e", distance_km=50.0, road_type=RoadType.MOUNTAIN_PASS
    )

    state.locations = {
        "village_a": loc_a,
        "crossroads_b": loc_b,
        "swamp_c": loc_c,
        "city_d": loc_d,
        "remote_village_e": loc_e,
    }

    # NPCs
    npc_d = NPC(id="mayor_d", name="수도 행정관", description="수도 행정관", location="city_d")
    loc_d.npcs = ["mayor_d"]
    state.npcs["mayor_d"] = npc_d

    npc_e = NPC(id="peasant_e", name="오지 촌로", description="오지 촌로", location="remote_village_e")
    loc_e.npcs = ["peasant_e"]
    state.npcs["peasant_e"] = npc_e

    state.player.location = "village_a"
    state.player.reputation = 0
    state.player.regional_reputation = {}
    state.player.time_elapsed_minutes = 0
    state.start_minute = 480  # Day 1 08:00 AM

    return state


def test_road_types_and_speed_multipliers():
    # 10km on highway (1.25x speed, foot 4km/h -> 5 km/h) = 2.0 hours
    hours_highway = GeographyEngine.calculate_segment_travel_hours(10.0, RoadType.PAVED_HIGHWAY, "foot")
    assert hours_highway == pytest.approx(2.0, rel=1e-2)

    # 10km on swamp (0.35x speed, foot 4km/h -> 1.4 km/h) = ~7.14 hours
    hours_swamp = GeographyEngine.calculate_segment_travel_hours(10.0, RoadType.SWAMP_TRAIL, "foot")
    assert hours_swamp > hours_highway * 3  # Swamp takes more than 3x longer


def test_dijkstra_shortest_travel_and_distance(geo_world):
    # Travel from village_a to city_d via highway (A->B 10km + B->D 20km = 30km)
    hours, km, path = GeographyEngine.dijkstra_shortest_travel(
        geo_world, "village_a", "city_d", travel_mode="carriage"
    )
    assert km == 30.0
    assert path == ["village_a", "crossroads_b", "city_d"]
    # Carriage 10km/h on highway (12.5 km/h) = 30 / 12.5 = 2.4 hours
    assert hours == pytest.approx(2.4, rel=1e-2)


def test_global_reputation_75_percent_remote_recognition(geo_world):
    # Player becomes a legendary hero (global reputation 100)
    geo_world.player.reputation = 100
    assert geo_world.player.regional_reputation.get("remote_village_e", 0) == 0

    # Even in an isolated remote village with 0 local reputation, recognition is >= 75%
    effective_rep = RumorDiffusionEngine.get_effective_reputation(geo_world, "remote_village_e")
    assert effective_rep >= 75  # 0 + int(100 * 0.75) = 75!


def test_in_game_time_based_rumor_diffusion(geo_world):
    # Dispatch significance 3 rumor from village_a by carriage (10 km/h)
    # A -> B -> D is 30km highway. Travel time = 2.4 hours = 144 minutes.
    wave = RumorDiffusionEngine.dispatch_event_rumor(
        state=geo_world,
        origin_loc="village_a",
        event_text="용병이 암흑 교단 보스를 처치함",
        significance=3,
        reputation_delta=20,
        carrier="merchant"
    )
    assert "city_d" in wave.scheduled_arrivals
    arr_min = wave.scheduled_arrivals["city_d"]
    assert arr_min == 480 + 144  # 624 minutes

    # 1. Advance time by 60 minutes: city_d has NOT heard the rumor yet!
    geo_world.player.time_elapsed_minutes = 60
    logs_early = RumorDiffusionEngine.advance_time_tick(geo_world, elapsed_minutes=60)
    assert not any("솔리스 수도" in log for log in logs_early)
    assert geo_world.player.regional_reputation.get("city_d", 0) == 0
    assert not any("암흑 교단" in b for b in geo_world.npcs["mayor_d"].beliefs)

    # 2. Advance time to 150 minutes (arrival time passed!): Rumor delivered!
    geo_world.player.time_elapsed_minutes = 150
    logs_arrival = RumorDiffusionEngine.advance_time_tick(geo_world, elapsed_minutes=90)
    assert any("솔리스 수도" in log for log in logs_arrival)
    assert geo_world.player.regional_reputation.get("city_d", 0) > 0
    assert any("암흑 교단" in b for b in geo_world.npcs["mayor_d"].beliefs)


def test_significance_radius_barrier(geo_world):
    # Significance 1 rumor (max range 3km) created at village_a
    # city_d is 30km away
    wave = RumorDiffusionEngine.dispatch_event_rumor(
        state=geo_world,
        origin_loc="village_a",
        event_text="골목 소매치기 제압",
        significance=1,
        reputation_delta=5,
        carrier="refugee"
    )
    # City D exceeds 3km max range, so it is never scheduled
    assert "city_d" not in wave.scheduled_arrivals

    # Advance 10,000 minutes into the future
    geo_world.player.time_elapsed_minutes = 10000
    RumorDiffusionEngine.advance_time_tick(geo_world, elapsed_minutes=10000)
    assert geo_world.player.regional_reputation.get("city_d", 0) == 0


def test_whisper_distortion_levels(geo_world):
    wave = RumorWave(
        rumor_id="test_rumor",
        origin_location="village_a",
        event_text="고블린 군단을 홀로 처치함"
    )
    # 0 hops: Fact
    t0 = wave.get_distorted_text_for_hops(0, 0.0)
    assert "[목격 팩트]" in t0

    # 1 hop: Neighbor rumor
    t1 = wave.get_distorted_text_for_hops(1, 10.0)
    assert "[인근 소문]" in t1

    # 2 hops: Heroic/monstrous legend
    t2 = wave.get_distorted_text_for_hops(2, 35.0)
    assert "[원정 영웅담/괴담]" in t2

    # 3+ hops: Myth
    t3 = wave.get_distorted_text_for_hops(3, 80.0)
    assert "[대륙 전설]" in t3
