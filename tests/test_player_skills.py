import pytest
from src.world.state import WorldState, Location, NPC, Item, Skill, NPCPersonality
from src.world.validator import ActionValidator
from src.world.two_pass_engine import TwoPassEngine
from src.world.npc_skill_engine import NPCSkillEngine
from src.world.status_engine import StatusEffectEngine


@pytest.fixture
def skill_test_world():
    state = WorldState()
    state.player.location = "arena"
    state.player.health = 50
    state.player.max_health = 50
    state.player.mana = 40
    state.player.max_mana = 40
    state.player.gold = 30
    state.player.intelligence = 16
    state.player.strength = 14
    state.player.inventory = ["steel_sword"]

    loc = Location(id="arena", name="결투장", description="모래 바닥의 결투장", exits={})
    state.locations["arena"] = loc

    # Equipped weapon
    state.items["steel_sword"] = Item(
        id="steel_sword", name="강철검", description="", location="inventory",
        item_type="weapon", damage=6, scaling_factor=1.2
    )
    state.player.equipment.weapon = "steel_sword"

    # Register skills in DB
    state.skills_db["skill_fireball"] = Skill(
        id="skill_fireball",
        name="작열 화염구 (이그니스 스페라)",
        category="arcane_magic",
        skill_type="active",
        resource_type="mana",
        resource_cost=25,
        cooldown_turns=2,
        current_cooldown=0,
        base_value=35,
        scaling_stat="int",
        scaling_factor=1.4,
        inflicted_status=[{"status": "burning", "duration_turns": 3, "dot_damage_per_turn": 8}]
    )

    state.skills_db["skill_cleave"] = Skill(
        id="skill_cleave",
        name="모트하우 중장갑 파쇄",
        category="physical",
        skill_type="active",
        resource_type="mana",
        resource_cost=15,
        cooldown_turns=1,
        current_cooldown=0,
        base_value=25,
        scaling_stat="str",
        scaling_factor=1.5
    )

    # Player has learned fireball and cleave
    state.player.skills = ["skill_fireball", "skill_cleave"]

    # Target goblin dummy
    dummy = NPC(
        id="goblin_01",
        name="고블린 척후병",
        description="",
        location="arena",
        disposition="hostile",
        health=50,
        max_health=50,
        armor_class=10
    )
    state.npcs["goblin_01"] = dummy
    loc.npcs.append("goblin_01")

    return state


def test_player_skill_execution_success(skill_test_world):
    # Player declares skill by name with fixed hit roll
    import random
    orig_randint = random.randint
    random.randint = lambda a, b: 15
    try:
        fact_sheet = TwoPassEngine.compute_pass1("작열 화염구를 고블린에게 투척한다!", skill_test_world)
        assert fact_sheet.is_valid is True
        # Mana deducted
        assert skill_test_world.player.mana == 15  # 40 - 25
        # Cooldown set
        assert skill_test_world.skills_db["skill_fireball"].current_cooldown == 2
        # Target took damage in combat outcome
        assert fact_sheet.combat_outcome is not None
        assert fact_sheet.combat_outcome["damage_dealt"] > 0
        skill_test_world.apply_update(fact_sheet.pre_computed_state_delta)
        goblin = skill_test_world.npcs["goblin_01"]
        assert goblin.health < 50
        assert StatusEffectEngine.has_status(goblin, "burning")
    finally:
        random.randint = orig_randint


def test_player_skill_cooldown_rejection(skill_test_world):
    # Set skill on cooldown
    skill_test_world.skills_db["skill_fireball"].current_cooldown = 2
    is_valid, msg, dice, extra = ActionValidator.pre_validate_action("작열 화염구 시전", skill_test_world)
    assert is_valid is False
    assert "재사용 대기시간" in msg


def test_player_skill_mana_deficiency_rejection(skill_test_world):
    # Set player mana lower than skill cost (25)
    skill_test_world.player.mana = 10
    is_valid, msg, dice, extra = ActionValidator.pre_validate_action("작열 화염구 시전", skill_test_world)
    assert is_valid is False
    assert "마나가 부족하여" in msg


def test_player_basic_attack_conserves_mana(skill_test_world):
    # Player simply says basic attack without naming the skill
    initial_mana = skill_test_world.player.mana
    fact_sheet = TwoPassEngine.compute_pass1("강철검으로 고블린 척후병을 찌른다", skill_test_world)
    assert fact_sheet.is_valid is True
    # Mana is NOT deducted!
    assert skill_test_world.player.mana == initial_mana
    # Skill cooldown was NOT applied!
    assert skill_test_world.skills_db["skill_fireball"].current_cooldown == 0


def test_smart_npc_conserves_mana_on_weak_target(skill_test_world):
    # Set player HP very low (<= 15)
    skill_test_world.player.health = 10
    # Smart NPC (int 14, wis 14, aggro 50)
    smart_npc = NPC(
        id="smart_mage",
        name="현명한 마법사",
        description="",
        location="arena",
        disposition="hostile",
        health=40,
        mana=30,
        intelligence=14,
        wisdom=14,
        personality=NPCPersonality(aggression=50),
        skills=["skill_fireball"]
    )
    outcome = NPCSkillEngine.process_npc_combat_turn(smart_npc, skill_test_world, player_ac=10)
    assert outcome is not None
    # Smart NPC conserved mana with basic attack!
    assert smart_npc.mana == 30
    assert outcome["action_type"] != "cc_stunned"


def test_sadistic_npc_overkills_weak_target(skill_test_world):
    # Set player HP very low (<= 15)
    skill_test_world.player.health = 10
    # Sadistic NPC (int 14, aggro 90)
    sadistic_npc = NPC(
        id="sadistic_orc",
        name="광폭한 오크",
        description="",
        location="arena",
        disposition="hostile",
        health=40,
        mana=30,
        intelligence=14,
        personality=NPCPersonality(aggression=90),
        skills=["skill_fireball"]
    )
    outcome = NPCSkillEngine.process_npc_combat_turn(sadistic_npc, skill_test_world, player_ac=10)
    assert outcome is not None
    # Sadistic NPC spent 25 mana to overkill!
    assert sadistic_npc.mana == 5
    assert outcome["skill_name"] == "작열 화염구 (이그니스 스페라)"
