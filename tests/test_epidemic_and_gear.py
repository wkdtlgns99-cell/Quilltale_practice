"""
Unit tests for EpidemicEngine (6 deadly diseases, infection checks, incubation, stages, remedies, quarantine),
Realistic Backpack Storage Specs & Overload Tear Mechanics, and Skill Visual Aesthetics.
"""
import pytest
from src.world.state import WorldState, Location, Player, NPC, Item, Skill
from src.world.disease_engine import (
    EpidemicEngine,
    EPIDEMIC_SYSTEM,
    DISEASE_REGISTRY,
    DiseaseSpec,
    DiseaseStageSpec,
    ActiveInfection,
    InfectionAttemptResult
)
from src.world.outfit_engine import (
    OutfitMechanicsEngine,
    BackpackSpec,
    BackpackStorageStatus,
    BACKPACK_SPECS
)
from src.world.two_pass_engine import TwoPassEngine


@pytest.fixture
def epidemic_world():
    state = WorldState()
    state.player.location = "town_square"
    state.player.health = 100
    state.player.max_health = 100
    state.player.constitution = 14  # +2 modifier
    state.player.stamina = 100
    state.player.max_stamina = 100
    state.player.mana_color = "푸른빛 에테르"
    state.player.mana_color_hex = "#38bdf8"
    state.player.active_infections = {}

    loc = Location(
        id="town_square",
        name="역병이 번진 마을 광장",
        description="음산한 안개와 악취가 감도는 마을 광장입니다.",
        exits={},
        traits=["quarantine_zone", "plague_risk"]
    )
    state.locations["town_square"] = loc
    return state


def test_master_disease_registries_and_traits():
    """Verify all 6 master diseases and their stages have traits."""
    assert len(DISEASE_REGISTRY) == 6
    expected_ids = [
        "black_plague", "dysentery", "corpse_decay_fever",
        "cave_spore_mycosis", "blood_leech_parasite", "rabies_madness"
    ]
    for d_id in expected_ids:
        assert d_id in DISEASE_REGISTRY
        spec = DISEASE_REGISTRY[d_id]
        assert spec.name_ko
        assert len(spec.traits) > 0
        assert spec.con_save_dc > 0
        assert len(spec.stages) == 3
        for st_id, st_spec in spec.stages.items():
            assert st_spec.name_ko
            assert st_spec.duration_turns > 0
            assert len(st_spec.traits) > 0


def test_infection_saving_throw_and_modifiers(epidemic_world):
    """Test CON save DC, critical outcomes, and exposure modifiers."""
    player = epidemic_world.player
    # player CON 14 (+2 mod)

    # 1. Critical success (roll 20) -> Immune
    res_crit = EpidemicEngine.attempt_infection(player, "black_plague", epidemic_world, fixed_roll=20)
    assert res_crit.infected is False
    assert res_crit.is_critical_success is True

    # 2. Critical failure (roll 1) -> Immediate Stage 1 onset
    res_fail = EpidemicEngine.attempt_infection(player, "black_plague", epidemic_world, fixed_roll=1)
    assert res_fail.infected is True
    assert res_fail.is_critical_failure is True
    assert res_fail.stage == "stage_1"
    assert "black_plague" in player.active_infections
    assert player.active_infections["black_plague"].current_stage == "stage_1"

    # Reset
    player.active_infections.clear()

    # 3. Normal success vs dysentery (DC 13, roll 11 + 2 = 13 -> Success)
    res_save = EpidemicEngine.attempt_infection(player, "dysentery", epidemic_world, fixed_roll=11)
    assert res_save.infected is False

    # 4. Normal failure vs dysentery (roll 10 + 2 = 12 < DC 13 -> Failure, incubation begins)
    res_inc = EpidemicEngine.attempt_infection(player, "dysentery", epidemic_world, fixed_roll=10)
    assert res_inc.infected is True
    assert res_inc.stage == "incubating"
    assert "dysentery" in player.active_infections
    assert player.active_infections["dysentery"].is_incubating is True

    # 5. Shared bedding penalty (+4 DC)
    # dysentery DC 13 + 4 = 17. Roll 13 + 2 = 15 < 17 -> Fails
    res_bed = EpidemicEngine.attempt_infection(player, "dysentery", epidemic_world, is_shared_bedding=True, fixed_roll=13)
    assert res_bed.dc == 13 + 4 + 2 + 2  # base 13 + bedding 4 + immune 2 + multi-exposure 2


def test_disease_incubation_and_stage_transitions(epidemic_world):
    """Test turn ticks advancing disease from incubation to stage 1, 2, 3 and applying effects."""
    state = epidemic_world
    player = state.player

    # Set up rabies madness with 1 turn incubation
    inf = ActiveInfection(
        disease_id="rabies_madness",
        current_stage="incubating",
        turns_in_stage=0,
        incubation_turns_remaining=1,
        is_incubating=True
    )
    player.active_infections["rabies_madness"] = inf

    # Turn 1: Incubation finishes -> Stage 1
    logs = EpidemicEngine.process_turn_infections(state)
    assert inf.is_incubating is False
    assert inf.current_stage == "stage_1"
    assert any("발병" in log for log in logs)

    # Fast forward through stage 1 duration (3 turns)
    spec = DISEASE_REGISTRY["rabies_madness"]
    stage_1_duration = spec.stages["stage_1"].duration_turns
    for _ in range(stage_1_duration):
        EpidemicEngine.process_turn_infections(state)

    # Now should be stage 2
    assert inf.current_stage == "stage_2"

    # Fast forward through stage 2 duration (4 turns)
    stage_2_duration = spec.stages["stage_2"].duration_turns
    for _ in range(stage_2_duration):
        EpidemicEngine.process_turn_infections(state)

    # Now should be stage 3 (fatal/critical)
    assert inf.current_stage == "stage_3"

    # Turn in Stage 3 deals 15 hp loss per turn
    player.health = 50
    logs = EpidemicEngine.process_turn_infections(state)
    assert player.health == 35  # 50 - 15


def test_remedies_and_quarantine(epidemic_world):
    """Test holy purification, herbs, alcohol disinfection, and corpse burning."""
    state = epidemic_world
    player = state.player

    # Infect with black plague in stage 2
    inf = ActiveInfection(
        disease_id="black_plague",
        current_stage="stage_2",
        turns_in_stage=1,
        is_incubating=False
    )
    player.active_infections["black_plague"] = inf

    # 1. Herb decoction reduces stage 2 -> stage 1
    success, msg = EpidemicEngine.apply_remedy(player, "black_plague", "herbs", herb_name="역병초 달인물", fixed_roll=18)
    assert success is True
    assert inf.current_stage == "stage_1"

    # 2. Holy purification completely cures it
    success, msg = EpidemicEngine.apply_remedy(player, "black_plague", "holy_purification", fixed_roll=18)
    assert success is True
    assert "black_plague" not in player.active_infections

    # 3. Cauterization on fresh bite
    inf_rabies = ActiveInfection(
        disease_id="rabies_madness",
        current_stage="incubating",
        is_incubating=True
    )
    player.active_infections["rabies_madness"] = inf_rabies
    player.health = 50
    success, msg = EpidemicEngine.apply_remedy(player, "rabies_madness", "cauterization")
    assert success is True
    assert "rabies_madness" not in player.active_infections
    assert player.health == 42  # 50 - 8 damage

    # 4. Corpse burning
    b_success, b_msg = EpidemicEngine.burn_corpses(state, "town_square")
    assert b_success is True
    assert "시체 소각 방역" in b_msg


def test_backpack_specs_and_tear_physics(epidemic_world):
    """Test realistic backpack specs, volume limits, and overweight tear risk."""
    state = epidemic_world
    player = state.player

    # 1. Test specs
    assert len(BACKPACK_SPECS) >= 3
    daypack = BACKPACK_SPECS["small_daypack"]
    assert daypack.volume_liters == 18.0
    assert daypack.safe_weight_limit_kg == 12.0
    assert daypack.tear_weight_limit_kg == 18.0

    military = BACKPACK_SPECS["military_full_rucksack"]
    assert military.volume_liters == 75.0
    assert military.safe_weight_limit_kg == 45.0
    assert military.tear_weight_limit_kg == 60.0

    # 2. Equip small daypack
    pack_item = Item(id="small_pack_1", name="소형 전술 슬링백", description="가벼운 슬링백", location="inventory", item_type="armor")
    state.items["small_pack_1"] = pack_item
    player.equipment.storage = "small_pack_1"

    # Add items within limit
    potion = Item(id="potion_1", name="치유 물약", description="물약", location="inventory", weight=0.5, size="small")
    state.items["potion_1"] = potion
    player.inventory = ["potion_1"]

    status = OutfitMechanicsEngine.evaluate_backpack_storage(player, state)
    assert status.backpack_name == "소형 전술 배낭"
    assert status.is_overweight is False
    assert status.is_torn is False

    # 3. Overweight and trigger tear
    heavy_rock = Item(id="heavy_rock_1", name="무거운 철광석", description="돌", location="inventory", weight=25.0, size="small")
    state.items["heavy_rock_1"] = heavy_rock
    player.inventory.append("heavy_rock_1")

    # Evaluate with forced tear
    status_over = OutfitMechanicsEngine.evaluate_backpack_storage(player, state, trigger_action="sprint", force_tear=True)
    assert status_over.is_overweight is True
    assert status_over.is_torn is True
    assert "무거운 철광석" in status_over.spilled_item_names
    # Item was spilled onto ground
    assert "heavy_rock_1" in state.locations["town_square"].items


def test_skill_visual_aesthetics(epidemic_world):
    """Test skill visual descriptions for physical, mana, dark, and blood magic."""
    player = epidemic_world.player
    player.mana_color = "찬란한 청록빛 에테르"
    player.mana_color_hex = "#2dd4bf"

    # 1. Pure Physical Skill: Grey/Silver/White
    slash = Skill(
        id="iron_slash",
        name="강철 베기",
        description="단순하고 정갈한 검격",
        category="physical",
        element="physical",
        resource_type="stamina",
        resource_cost=15,
        mana_cost=0
    )
    desc_phys = slash.get_visual_description(player)
    assert "은백색" in desc_phys
    assert slash.color == "#e2e8f0"

    # 2. Mana-infused Physical Skill: Caster Mana Color
    desc_infused = slash.get_visual_description(player, infused_with_mana=True)
    assert "찬란한 청록빛 에테르" in desc_infused
    assert slash.color == "#2dd4bf"

    # 3. Dark Magic: Strictly Black
    dark_orb = Skill(
        id="shadow_orb",
        name="칠흑의 암흑구",
        description="심연의 암흑탄",
        category="dark_magic",
        element="dark",
        resource_type="mana",
        mana_cost=20
    )
    desc_dark = dark_orb.get_visual_description(player)
    assert "칠흑빛" in desc_dark or "흑색" in desc_dark
    assert dark_orb.color == "#0f172a"

    # 4. Blood Magic: Strictly Red
    blood_spike = Skill(
        id="blood_spike",
        name="선혈의 가시",
        description="혈액을 응결시킨 송곳",
        category="blood_magic",
        element="blood",
        resource_type="mana",
        mana_cost=25
    )
    desc_blood = blood_spike.get_visual_description(player)
    assert "선홍빛" in desc_blood or "빨간색" in desc_blood
    assert blood_spike.color == "#dc2626"

    # 5. Elemental Magic (Fire): Element Color + Caster Mana Aura
    fireball = Skill(
        id="fireball_1",
        name="작열구",
        description="화염 마법",
        category="elemental_magic",
        element="fire",
        resource_type="mana",
        mana_cost=15
    )
    desc_fire = fireball.get_visual_description(player)
    assert "주황빛과 진홍빛 불꽃" in desc_fire
    assert "찬란한 청록빛 에테르" in desc_fire
    assert fireball.color == "#f97316"
