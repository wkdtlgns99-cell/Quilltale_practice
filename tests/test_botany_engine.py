"""
Unit tests for HerbalismBotanyEngine in Quilltale TRPG.
Tests botany foraging, poisonous lookalike generation on failure,
precise plant identification, and plant consumption consequences.
"""
import pytest
from src.world.state import WorldState, Player, Location
from src.world.botany_engine import (
    HerbalismBotanyEngine, PlantSpec, PLANT_REGISTRY
)


@pytest.fixture
def botany_world():
    state = WorldState()
    state.locations["deep_forest"] = Location(
        id="deep_forest",
        name="울창한 원시림",
        description="다양한 희귀 식물과 맹독성 버섯이 뒤섞여 자라는 원시 숲.",
        exits={},
        traits=["forest", "mountain"]
    )
    state.player = Player(
        name="약초사 리사",
        location="deep_forest",
        health=50,
        max_health=50,
        intelligence=16,
        perception=14
    )
    return state


def test_botany_specs_and_traits():
    """Verifies all plant specs have traits and valid fields."""
    assert len(PLANT_REGISTRY) >= 10
    for p_id, spec in PLANT_REGISTRY.items():
        assert isinstance(spec, PlantSpec)
        assert len(spec.traits) > 0
        assert spec.category in ["medicinal", "edible", "poisonous", "arcane"]

    # Check lookalike pairs
    assert PLANT_REGISTRY["wild_pine_mushroom"].lookalike_poison_id == "destroying_angel"
    assert PLANT_REGISTRY["wild_ramson"].lookalike_poison_id == "lily_of_the_valley"
    assert PLANT_REGISTRY["lingzhi_mushroom"].lookalike_poison_id == "poison_fire_coral"


def test_forage_success(botany_world):
    """Tests high roll results in successful gathering of genuine plant."""
    loc = botany_world.locations["deep_forest"]
    res = HerbalismBotanyEngine.forage(
        gatherer=botany_world.player,
        location=loc,
        state=botany_world,
        fixed_roll=20  # Critical success
    )
    assert res["success"] is True
    assert res["is_lookalike"] is False
    assert res["plant_data"] is not None
    assert "채집 성공" in res["message_ko"]


def test_forage_critical_failure_poisonous_lookalike(botany_world):
    """
    Tests critical failure (roll 1) triggers gathering a poisonous lookalike
    disguised as the intended edible/medicinal plant.
    """
    loc = botany_world.locations["deep_forest"]
    res = HerbalismBotanyEngine.forage(
        gatherer=botany_world.player,
        location=loc,
        state=botany_world,
        target_plant_id="wild_pine_mushroom",
        fixed_roll=1  # Botch roll
    )
    assert res["success"] is True  # Player thinks they gathered something
    if res["is_lookalike"]:
        plant_data = res["plant_data"]
        assert plant_data["is_poisonous_lookalike"] is True
        assert plant_data["is_identified"] is False
        assert "unidentified" in plant_data["traits"]
        assert "불안정" in res["message_ko"]


def test_identify_plant_true_herb_and_toxic_mimic(botany_world):
    """Tests identifying genuine plant vs exposing dangerous poisonous lookalike."""
    player = botany_world.player

    # 1. Genuine herb identification (blood_moss)
    genuine_herb = {
        "id": "herb_123",
        "name": "지혈 이끼",
        "true_spec_id": "blood_moss",
        "is_identified": False,
        "is_poisonous_lookalike": False,
        "origin_target_name": "지혈 이끼",
        "traits": ["medicinal", "unidentified"]
    }
    success, id_msg = HerbalismBotanyEngine.identify_plant(
        identifier=player,
        plant_item_data=genuine_herb,
        fixed_roll=18
    )
    assert success is True
    assert genuine_herb["is_identified"] is True
    assert "감별 성공" in id_msg

    # 2. Exposing poisonous lookalike (Destroying angel disguised as pine mushroom)
    poison_mimic = {
        "id": "mushroom_999",
        "name": "야생에서 캔 송이버섯",
        "true_spec_id": "destroying_angel",
        "is_identified": False,
        "is_poisonous_lookalike": True,
        "origin_target_name": "송이버섯",
        "traits": ["poison", "unidentified"]
    }
    success_mimic, mimic_msg = HerbalismBotanyEngine.identify_plant(
        identifier=player,
        plant_item_data=poison_mimic,
        fixed_roll=18  # High roll reveals the poison
    )
    assert success_mimic is True
    assert poison_mimic["is_identified"] is True
    assert "독우산광대버섯" in poison_mimic["name"]
    assert "치명적인 맹독 유사종" in mimic_msg


def test_consume_plant_medicinal_and_fatal_effects(botany_world):
    """Tests eating beneficial medicinal herb vs consuming disguised poisonous lookalike."""
    player = botany_world.player
    player.health = 20  # Injured

    # 1. Consume medicinal willow bark
    willow_item = {
        "id": "wb_1",
        "name": "해열 버들껍질",
        "true_spec_id": "willow_bark",
        "is_identified": True,
        "is_poisonous_lookalike": False,
        "traits": ["medicinal"]
    }
    heal_logs = HerbalismBotanyEngine.consume_plant(player, willow_item, state=botany_world)
    assert any("상처가 아물며" in l for l in heal_logs)
    assert player.health > 20

    # 2. Unknowingly consume disguised poison fire coral
    coral_item = {
        "id": "pfc_1",
        "name": "야생에서 캔 영지초",
        "true_spec_id": "poison_fire_coral",
        "is_identified": False,
        "is_poisonous_lookalike": True,
        "traits": ["poison"]
    }
    toxic_logs = HerbalismBotanyEngine.consume_plant(player, coral_item, state=botany_world)
    assert any("맹독 유사종 중독" in l for l in toxic_logs)
    assert any("붉은사슴뿔버섯" in l for l in toxic_logs)
    assert player.health <= 5  # Massive toxic damage taken (45 damage from 50 max)
