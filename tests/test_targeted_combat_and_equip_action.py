import pytest
from src.world.state import WorldState, Player, NPC, Item, Location, Skill
from src.world.validator import ActionValidator
from src.world.two_pass_engine import TwoPassEngine
from src.world.status_engine import StatusEffectEngine


@pytest.fixture
def action_state():
    state = WorldState()
    loc = Location(id="field", name="벌판", description="황량한 벌판", exits={})
    state.locations["field"] = loc
    state.player.location = "field"

    # Player stats
    state.player.strength = 10
    state.player.agility = 10
    state.player.base_armor_class = 10

    # Items
    state.items["helm_iron"] = Item(
        id="helm_iron", name="강철 투구", description="", location="inventory",
        item_type="armor", defense=4, durability=100
    )
    state.items["sword_iron"] = Item(
        id="sword_iron", name="강철 검", description="", location="inventory",
        item_type="weapon", damage=10, durability=100
    )
    state.items["ring_gold"] = Item(
        id="ring_gold", name="황금 반지", description="", location="inventory",
        item_type="ring", properties={"stat_bonuses": {"str": 3}}
    )

    # World item NOT owned by player
    state.items["legendary_armor"] = Item(
        id="legendary_armor", name="용비늘 갑옷", description="", location="dungeon",
        item_type="armor", defense=20
    )

    state.player.inventory = ["helm_iron", "sword_iron", "ring_gold"]
    loc.items = []

    # NPC Goblin
    goblin = NPC(
        id="goblin_01", name="고블린 척후병", description="", location="field",
        health=50, max_health=50, armor_class=10, morale=80
    )
    # Goblin has a helmet
    state.items["goblin_cap"] = Item(
        id="goblin_cap", name="가죽 모자", description="", location="goblin_01",
        item_type="armor", defense=2, durability=10
    )
    goblin.equipment.head = "goblin_cap"
    state.npcs["goblin_01"] = goblin
    loc.npcs = ["goblin_01"]

    # AoE Skill Fireball
    fireball = Skill(
        id="skill_fireball", name="작열 화염구", element="화염",
        area_shape="circle", area_radius_meters=4.0, base_value=20, mana_cost=10
    )
    state.skills_db["skill_fireball"] = fireball
    state.player.skills = ["skill_fireball"]

    return state


def test_natural_language_equip(action_state):
    # Player says: "강철 투구를 쓴다"
    valid, msg, _, flags = ActionValidator.pre_validate_action("강철 투구를 머리에 쓴다", action_state)
    assert valid is True
    assert flags.get("equip_intent") is not None
    assert flags["equip_intent"]["action"] == "equip"
    assert flags["equip_intent"]["slot"] == "head"

    fact_sheet = TwoPassEngine.compute_pass1("강철 투구를 머리에 쓴다", action_state)
    assert fact_sheet.is_valid is True
    assert "equip_slot" in fact_sheet.pre_computed_state_delta
    action_state.apply_update(fact_sheet.pre_computed_state_delta)

    # Equipment updated
    assert action_state.player.equipment.head == "helm_iron"
    assert action_state.player.equipment_defense == 4
    assert action_state.player.armor_class == 14


def test_equip_unowned_item_rejected_anti_yes_man(action_state):
    # Player tries to equip legendary armor they don't own
    valid, msg, _, _ = ActionValidator.pre_validate_action("용비늘 갑옷을 몸에 입는다", action_state)
    assert valid is False
    assert "존재하지 않는" in msg or "소지" in msg


def test_natural_language_unequip(action_state):
    # Equip helmet first
    action_state.player.equipment.head = "helm_iron"
    action_state.recalculate_equipment_stats(action_state.player)
    assert action_state.player.armor_class == 14

    # Player says: "투구를 벗는다"
    valid, msg, _, flags = ActionValidator.pre_validate_action("투구를 벗는다", action_state)
    assert valid is True
    assert flags.get("equip_intent") is not None
    assert flags["equip_intent"]["action"] == "unequip"

    fact_sheet = TwoPassEngine.compute_pass1("투구를 벗는다", action_state)
    action_state.apply_update(fact_sheet.pre_computed_state_delta)

    assert action_state.player.equipment.head is None
    assert action_state.player.armor_class == 10


def test_targeted_leg_strike_inflicts_injury_and_lowers_morale(action_state):
    import random
    orig_randint = random.randint
    random.randint = lambda a, b: 18  # Fixed hit
    try:
        fact_sheet = TwoPassEngine.compute_pass1("고블린 척후병의 다리를 노려 검으로 벤다!", action_state)
        assert fact_sheet.is_valid is True
        assert fact_sheet.combat_outcome is not None
        assert fact_sheet.combat_outcome["target_part"] == "다리"
        assert any("다리" in inj for inj in fact_sheet.combat_outcome["target_injuries"])

        action_state.apply_update(fact_sheet.pre_computed_state_delta)
        goblin = action_state.npcs["goblin_01"]
        assert any("다리" in inj for inj in goblin.injuries)
        assert goblin.morale < 80
    finally:
        random.randint = orig_randint


def test_targeted_head_strike_damages_enemy_helmet_durability(action_state):
    import random
    orig_randint = random.randint
    random.randint = lambda a, b: 18  # Fixed hit
    try:
        fact_sheet = TwoPassEngine.compute_pass1("고블린 척후병의 머리를 노려 찍는다!", action_state)
        assert fact_sheet.is_valid is True
        assert fact_sheet.combat_outcome["target_part"] == "머리"

        # Goblin's cap took 1 durability damage (from 10 to 9)
        assert action_state.items["goblin_cap"].durability == 9
    finally:
        random.randint = orig_randint


def test_aoe_attack_cannot_pinpoint_body_part(action_state):
    import random
    orig_randint = random.randint
    random.randint = lambda a, b: 18
    try:
        # Player tries to pinpoint the leg with an explosive AoE fireball
        fact_sheet = TwoPassEngine.compute_pass1("작열 화염구로 고블린 척후병의 다리를 조준해 폭격한다!", action_state)
        assert fact_sheet.is_valid is True
        # AoE cannot pinpoint: forced to whole-body (chest)
        assert fact_sheet.combat_outcome["is_aoe"] is True
        assert fact_sheet.combat_outcome["target_part"] == "chest"
        # Full-body injury inflicted
        assert any("화상" in inj for inj in fact_sheet.combat_outcome["target_injuries"])
    finally:
        random.randint = orig_randint


def test_curse_dot_drains_hp_and_mp_and_requires_holy_cure(action_state):
    StatusEffectEngine.apply_status(action_state.player, "curse")
    curse = action_state.player.status_effects.get("curse")
    assert curse is not None
    assert curse.damage_per_turn == 5
    assert curse.mana_drain_per_turn == 5

    hp_start = action_state.player.health
    mp_start = action_state.player.mana

    # Process 1 turn tick
    logs = StatusEffectEngine.process_turn_ticks(action_state)
    assert action_state.player.health == hp_start - 5
    assert action_state.player.mana == mp_start - 5

    # Cannot be cured by bandage or water
    cured = StatusEffectEngine.cure_by_condition(action_state.player, "붕대")
    assert len(cured) == 0
    assert "curse" in action_state.player.status_effects

    # Cured by holy water
    cured_holy = StatusEffectEngine.cure_by_condition(action_state.player, "성수")
    assert len(cured_holy) > 0
    assert "curse" not in action_state.player.status_effects
