"""
Unit tests for CraftingEngine, Recipe management, ingredient consumption,
catalysts, quality outcomes, salvaging, and blind experimentation.
"""
import pytest
from src.world.state import WorldState, Player, Location, NPC, Item
from src.world.crafting_engine import CraftingEngine, Recipe, RecipeIngredient, RecipeOutcome


def test_load_recipe_templates():
    recipes = CraftingEngine.load_templates()
    assert len(recipes) >= 5
    assert "recipe_gravity_anchor_boots" in recipes
    assert "recipe_bloodless_healing_salve" in recipes
    assert "recipe_storm_catcher" in recipes


def test_check_recipe_prerequisites():
    state = WorldState()
    state.player.level = 5
    state.player.strength = 10

    recipe = CraftingEngine.get_recipe_template("recipe_gravity_anchor_boots")
    assert recipe is not None

    # Level 5 < 12, STR 10 < 15
    ok, reason = CraftingEngine.check_recipe_prerequisites(recipe, state)
    assert ok is False
    assert "레벨" in reason or "스탯" in reason

    # Raise player level and stats
    state.player.level = 15
    state.player.strength = 16
    state.player.constitution = 14
    state.quests["quest_fallen_sky_fortress"] = type("MockQuest", (), {"status": "completed"})()

    ok2, _ = CraftingEngine.check_recipe_prerequisites(recipe, state)
    assert ok2 is True


def test_check_recipe_ingredients():
    state = WorldState()
    recipe = CraftingEngine.get_recipe_template("recipe_dragon_slayer_oil")
    assert recipe is not None

    # Initially empty inventory
    has_ings, _, reason = CraftingEngine.check_recipe_ingredients(recipe, state)
    assert has_ings is False
    assert "재료 부족" in reason

    # Add required items
    state.player.inventory.extend(["dragon_scale", "dragon_scale", "dragon_scale", "fire_oil", "fire_oil", "silver_thistle"])
    has_ings2, to_consume, _ = CraftingEngine.check_recipe_ingredients(recipe, state)
    assert has_ings2 is True
    assert len(to_consume) == 6


def test_craft_item_success():
    import random
    random.seed(42)
    state = WorldState()
    state.player.level = 15
    state.player.intelligence = 40
    state.player.mana = 50
    state.player.inventory.extend(["dragon_scale", "dragon_scale", "dragon_scale", "fire_oil", "fire_oil", "silver_thistle"])

    success, log_msg, data = CraftingEngine.craft_item(state, "recipe_dragon_slayer_oil")
    assert success is True
    assert state.player.mana < 50
    # Ingredients consumed
    assert "dragon_scale" not in state.player.inventory
    assert "silver_thistle" not in state.player.inventory
    # Output item created
    assert any("dragon" in i for i in state.player.inventory)


def test_craft_salvage():
    state = WorldState()
    state.player.inventory.append("dragon_slayer_oil")
    state.items["dragon_slayer_oil"] = Item(id="dragon_slayer_oil", name="용살자의 기름", description="기름", value=50, location="inventory")

    success, msg, data = CraftingEngine.salvage_item(state, "dragon_slayer_oil")
    assert success is True
    assert "dragon_slayer_oil" not in state.player.inventory
    assert "dragon_scale" in state.player.inventory


def test_blind_experimentation():
    state = WorldState()
    state.player.inventory.extend(["strange_grass", "unknown_rock"])
    state.player.health = 50

    # Blind craft invalid combination
    success, msg, _ = CraftingEngine.experiment_blind_craft(state, ["strange_grass", "unknown_rock"])
    assert success is False
    assert "toxic_sludge" in state.player.inventory
    assert state.player.health < 50


def test_world_state_apply_update_crafting():
    import random
    random.seed(42)
    state = WorldState()
    state.player.level = 15
    state.player.intelligence = 40
    state.player.mana = 50
    state.player.inventory.extend(["dragon_scale", "dragon_scale", "dragon_scale", "fire_oil", "fire_oil", "silver_thistle"])

    state.apply_update({
        "craft_item": {
            "recipe_id": "recipe_dragon_slayer_oil"
        }
    })
    assert any("dragon" in i for i in state.player.inventory)


def test_serialization_round_trip():
    state = WorldState()
    recipe = CraftingEngine.get_recipe_template("recipe_dragon_slayer_oil")
    state.recipes["recipe_dragon_slayer_oil"] = recipe

    json_str = state.to_json()
    loaded = WorldState.from_json(json_str)

    assert "recipe_dragon_slayer_oil" in loaded.recipes
    assert loaded.recipes["recipe_dragon_slayer_oil"].name_ko == "용살자의 기름"


def test_crafting_html_and_prompt_formatting():
    state = WorldState()
    html = state.to_crafting_html()
    assert "공방 및 연금술 조합소" in html
    assert "중력닻 장화" in html

    state.player.inventory.extend(["dragon_scale", "dragon_scale", "dragon_scale", "fire_oil", "fire_oil", "silver_thistle"])
    prompt_ctx = CraftingEngine.format_crafting_context_for_prompt(state)
    assert "용살자의 기름" in prompt_ctx
