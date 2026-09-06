import pytest
from src.world.state import WorldState, Player, NPC, Skill, Location
from src.world.skills import SkillSystem
from src.world.validator import ActionValidator
from src.world.two_pass_engine import TwoPassEngine
from src.world.status_engine import StatusEffectEngine


@pytest.fixture
def magic_world():
    state = WorldState()
    state.player.location = "mage_chamber"
    state.player.health = 100
    state.player.max_health = 100
    state.player.mana = 100
    state.player.max_mana = 100
    state.player.wisdom = 14
    state.player.intelligence = 16
    state.player.mage_circle = 1  # 1st-circle mage (max 2 ancient words)
    state.player.known_magic_words = [
        "이그니스", "사기타", "볼란스", "막시마", "스타티오", "프락투라"
    ]

    loc = Location(id="mage_chamber", name="대마도사의 방", description="", exits={})
    state.locations["mage_chamber"] = loc

    # Target Dummy
    target = NPC(
        id="target_dummy",
        name="바르그라트",
        description="",
        location="mage_chamber",
        health=80,
        max_health=80,
        armor_class=12,
        wisdom=10,
        tier="commoner"
    )
    state.npcs["target_dummy"] = target
    loc.npcs.append("target_dummy")

    # Bystander Goblin
    bystander = NPC(
        id="bystander_goblin",
        name="구경꾼 고블린",
        description="",
        location="mage_chamber",
        health=30,
        max_health=30,
        armor_class=10,
        wisdom=8,
        tier="commoner"
    )
    state.npcs["bystander_goblin"] = bystander
    loc.npcs.append("bystander_goblin")

    # Load templates into db
    state.skills_db = SkillSystem.load_skill_templates()
    return state


def test_load_all_magic_school_templates():
    skills = SkillSystem.load_skill_templates()
    assert len(skills) >= 60

    # Test distinct categories exist
    categories = {s.category for s in skills.values()}
    assert "elemental_magic" in categories or "arcane_magic" in categories
    assert "logos_word" in categories
    assert "spatiotemporal" in categories
    assert "conceptual" in categories
    assert "causality" in categories
    assert "celestial" in categories
    assert "sacrifice_toll" in categories
    assert "shamanic_curse" in categories
    assert "divine_arts" in categories
    assert "blood_magic" in categories

    # Test Korean display names for all categories
    for cat in categories:
        disp_name = SkillSystem.get_category_display_name(cat)
        assert disp_name != ""
        assert isinstance(disp_name, str)


def test_player_mage_circle_word_scaling(magic_world):
    p = magic_world.player
    p.mage_circle = 1
    assert p.max_incantation_words == 2

    p.mage_circle = 2
    assert p.max_incantation_words == 3

    p.mage_circle = 5
    assert p.max_incantation_words == 6

    p.mage_circle = 10
    assert p.max_incantation_words == 10


def test_elemental_magic_two_word_basic_cast(magic_world):
    # 1-circle player casts 2-word spell "이그니스 볼란스"
    action = "손끝으로 이그니스 볼란스를 바르그라트에게 날린다!"
    is_valid, msg, dice_res, flags = ActionValidator.pre_validate_action(action, magic_world)
    assert is_valid is True
    assert dice_res is not None
    assert flags.get("circle_overflow") is not True


def test_elemental_magic_circle_word_overflow_penalty(magic_world):
    # 1-circle player tries to cast 3 words: exceeds circle limit of 2!
    action = "이그니스 사기타 볼란스를 시전한다!"
    is_valid, msg, dice_res, flags = ActionValidator.pre_validate_action(action, magic_world)
    assert is_valid is True
    assert flags.get("circle_overflow") is True
    assert flags.get("circle_overflow_count") == 1
    assert flags.get("backfire_risk") is True


def test_overcharged_incantation_multiplier(magic_world):
    # Player uses modifier "막시마"
    magic_world.player.mage_circle = 3  # Allow 4 words
    action = "이그니스 사기타 볼란스 막시마를 전방에 폭발시킨다!"
    is_valid, msg, dice_res, flags = ActionValidator.pre_validate_action(action, magic_world)
    assert is_valid is True
    assert flags.get("is_overcharged") is True
    assert "과부하" in dice_res.action_type


def test_logos_word_true_name_single_target(magic_world):
    # Caster addresses the target's true name "바르그라트, 스타티오!"
    action = "바르그라트, 스타티오!"
    is_valid, msg, dice_res, flags = ActionValidator.pre_validate_action(action, magic_world)
    assert is_valid is True
    assert flags.get("is_logos_word") is True
    assert flags.get("logos_mode") == "true_name_single"
    assert flags.get("is_friendly_fire_aoe") is False


def test_logos_word_indiscriminate_aoe_and_friendly_fire(magic_world):
    # Caster roars the word without addressing a target: "[스타티오]!"
    action = "모든 것을 멈추어라! [스타티오]!"
    fact_sheet = TwoPassEngine.compute_pass1(action, magic_world)
    assert fact_sheet.is_valid is True
    assert fact_sheet.extra_flags.get("is_logos_word") is True
    assert fact_sheet.extra_flags.get("logos_mode") == "indiscriminate_aoe"
    assert fact_sheet.extra_flags.get("is_friendly_fire_aoe") is True

    # If roll succeeded, bystander goblin should also have received stun/damage!
    dice_dict = fact_sheet.dice_result if isinstance(fact_sheet.dice_result, dict) else (fact_sheet.dice_result.__dict__ if fact_sheet.dice_result else {})
    if dice_dict.get("is_success"):
        bystander = magic_world.npcs["bystander_goblin"]
        assert StatusEffectEngine.has_status(bystander, "stun")
        assert bystander.health < 30


def test_logos_word_backlash_on_strong_target(magic_world):
    # Force failure to test backlash (성대 파열 / 침묵)
    import random
    orig_randint = random.randint
    random.randint = lambda a, b: 1  # Critical fail
    try:
        fact_sheet = TwoPassEngine.compute_pass1("스타티오!", magic_world)
        assert fact_sheet.is_valid is True
        dice_dict = fact_sheet.dice_result if isinstance(fact_sheet.dice_result, dict) else (fact_sheet.dice_result.__dict__ if fact_sheet.dice_result else {})
        assert dice_dict.get("is_success") is False
        # Backlash applied: silence (성대 파열)
        assert StatusEffectEngine.has_status(magic_world.player, "silence")
        # Self-damage took place
        assert magic_world.player.health < 100
    finally:
        random.randint = orig_randint


def test_conceptual_magic_distance_null(magic_world):
    # Register distance null skill
    sk_id = "skill_conceptual_distance_null_01"
    magic_world.player.skills.append(sk_id)

    action = "개념마법 거리 소멸을 바르그라트에게 발동한다!"
    fact_sheet = TwoPassEngine.compute_pass1(action, magic_world)
    assert fact_sheet.is_valid is True
    assert fact_sheet.extra_flags.get("conceptual_distance_zero") is True


def test_conceptual_magic_wound_erase(magic_world):
    sk_id = "skill_conceptual_wound_erase_01"
    # Create fake wound erase skill
    magic_world.skills_db[sk_id] = Skill(
        id=sk_id,
        name="개념마법: 상처 말소",
        category="conceptual",
        resource_type="mana",
        resource_cost=10
    )
    magic_world.player.skills.append(sk_id)
    magic_world.player.injuries = ["오른팔 골절", "늑골 타박상"]

    action = "개념마법 상처 말소를 시전한다"
    fact_sheet = TwoPassEngine.compute_pass1(action, magic_world)
    assert fact_sheet.is_valid is True
    assert fact_sheet.extra_flags.get("conceptual_wound_erase") is True
    assert len(magic_world.player.injuries) == 0


def test_spatiotemporal_space_cleave_ignores_armor(magic_world):
    sk_id = "skill_spatiotemporal_space_cleave_01"
    magic_world.player.skills.append(sk_id)

    action = "공간 단절로 바르그라트를 베어낸다"
    is_valid, msg, dice_res, flags = ActionValidator.pre_validate_action(action, magic_world)
    assert is_valid is True
    assert flags.get("spatiotemporal_space_severance") is True
    # Effective DC was computed with 100% armor penetration (dc=5)
    assert dice_res.dc == 5
