import pytest
from src.world.state import WorldState, Location, NPC, Item, Skill, NPCPersonality
from src.world.npc_skill_engine import NPCSkillEngine
from src.world.two_pass_engine import TwoPassEngine
from src.world.status_engine import StatusEffectEngine


@pytest.fixture
def test_world():
    state = WorldState()
    state.player.location = "town_square"
    state.player.health = 50
    state.player.max_health = 50
    state.player.gold = 50
    state.player.armor_class = 12
    state.player.wisdom = 10
    state.player.inventory = ["iron_dagger", "potion_heal"]

    loc = Location(id="town_square", name="중앙 광장", description="북적이는 광장", exits={})
    state.locations["town_square"] = loc

    # Items
    state.items["iron_dagger"] = Item(id="iron_dagger", name="철 단검", description="", location="inventory", item_type="weapon", damage=5)
    state.items["potion_heal"] = Item(id="potion_heal", name="회복 물약", description="", location="inventory", item_type="consumable", value=15)

    # Skills
    state.skills_db["skill_slash"] = Skill(
        id="skill_slash",
        name="강타 베기",
        category="physical",
        skill_type="active",
        role_type="single_attack",
        tier="uncommon",
        resource_type="mana",
        resource_cost=10,
        cooldown_turns=2,
        current_cooldown=0,
        base_value=12,
        scaling_stat="str",
        scaling_factor=1.2,
        inflicted_status=[{"status": "bleeding", "duration_turns": 2, "dot_damage_per_turn": 3}]
    )

    return state


def test_npc_combat_skill_execution(test_world):
    # Hostile Orc Warrior with skill_slash
    orc = NPC(
        id="orc_01",
        name="오크 전사",
        description="도끼를 든 흉포한 오크",
        location="town_square",
        disposition="hostile",
        health=40,
        max_health=40,
        mana=20,
        strength=16,
        agility=12,
        skills=["skill_slash"]
    )
    test_world.npcs["orc_01"] = orc
    test_world.locations["town_square"].npcs.append("orc_01")

    # Force d20 roll to 15 to ensure hit
    import random
    orig_randint = random.randint
    random.randint = lambda a, b: 15
    try:
        outcome = NPCSkillEngine.process_npc_combat_turn(orc, test_world, player_ac=12)
        assert outcome is not None
        assert outcome["is_success"] is True
        assert outcome["damage"] > 0
        assert test_world.player.health < 50
        assert orc.mana == 10  # 20 - 10
        assert test_world.skills_db["skill_slash"].current_cooldown == 2
        assert StatusEffectEngine.has_status(test_world.player, "bleeding")
    finally:
        random.randint = orig_randint


def test_npc_combat_cc_prevention(test_world):
    orc = NPC(
        id="orc_02",
        name="기절한 오크",
        description="",
        location="town_square",
        disposition="hostile",
        health=40,
        skills=["skill_slash"]
    )
    StatusEffectEngine.apply_status(orc, "stun", duration=1)
    outcome = NPCSkillEngine.process_npc_combat_turn(orc, test_world, player_ac=12)
    assert outcome is not None
    assert outcome["action_type"] == "cc_stunned"
    assert outcome["damage"] == 0
    assert test_world.player.health == 50


def test_npc_opportunistic_theft_success(test_world):
    thief = NPC(
        id="thief_01",
        name="골목길 소매치기",
        description="눈빛이 교활한 부랑아",
        location="town_square",
        job="소매치기",
        disposition="neutral",
        personality=NPCPersonality(greed=80),
        desire="손쉬운 금화 털기",
        agility=16
    )
    test_world.npcs["thief_01"] = thief
    test_world.locations["town_square"].npcs.append("thief_01")

    # Force stealth roll to 18 (beats player passive wis 10)
    import random
    orig_randint = random.randint
    orig_random = random.random
    random.randint = lambda a, b: 18 if b == 20 else 15
    random.random = lambda: 0.1  # Pick gold theft
    try:
        outcome = NPCSkillEngine.process_npc_opportunistic_turn(thief, test_world, "광장의 잡화점 가판대를 호기심 어린 눈으로 살핀다")
        assert outcome is not None
        assert outcome["action_type"] == "opportunistic_theft_success"
        assert outcome["player_noticed"] is False
        assert test_world.player.gold < 50
        assert thief.gold > 0
    finally:
        random.randint = orig_randint
        random.random = orig_random


def test_npc_opportunistic_theft_failure(test_world):
    thief = NPC(
        id="thief_02",
        name="어설픈 소매치기",
        description="",
        location="town_square",
        job="도적",
        disposition="neutral",
        personality=NPCPersonality(greed=80),
        agility=8
    )
    test_world.npcs["thief_02"] = thief
    test_world.locations["town_square"].npcs.append("thief_02")

    # Force stealth roll to 1 (crit failure)
    import random
    orig_randint = random.randint
    random.randint = lambda a, b: 1
    try:
        outcome = NPCSkillEngine.process_npc_opportunistic_turn(thief, test_world, "광장의 시계탑을 올려다보며 둘러본다")
        assert outcome is not None
        assert outcome["action_type"] == "opportunistic_theft_failed"
        assert outcome["player_noticed"] is True
        assert thief.disposition == "wary"
        assert test_world.player.gold == 50
    finally:
        random.randint = orig_randint


def test_npc_opportunistic_ambush(test_world):
    assassin = NPC(
        id="assassin_01",
        name="수상한 용병",
        description="",
        location="town_square",
        disposition="wary",
        personality=NPCPersonality(aggression=85),
    )
    test_world.npcs["assassin_01"] = assassin
    test_world.locations["town_square"].npcs.append("assassin_01")

    outcome = NPCSkillEngine.process_npc_opportunistic_turn(assassin, test_world, "용병을 무시하고 뒤돌아서 골목으로 발걸음을 옮긴다")
    assert outcome is not None
    assert outcome["action_type"] == "opportunistic_ambush"
    assert assassin.disposition == "hostile"


def test_tick_all_skill_cooldowns(test_world):
    skill = test_world.skills_db["skill_slash"]
    skill.current_cooldown = 3
    NPCSkillEngine.tick_all_skill_cooldowns(test_world)
    assert skill.current_cooldown == 2
    NPCSkillEngine.tick_all_skill_cooldowns(test_world)
    assert skill.current_cooldown == 1
    NPCSkillEngine.tick_all_skill_cooldowns(test_world)
    assert skill.current_cooldown == 0
    NPCSkillEngine.tick_all_skill_cooldowns(test_world)
    assert skill.current_cooldown == 0


def test_two_pass_engine_integration_with_npc_skills(test_world):
    orc = NPC(
        id="orc_boss",
        name="오크 부두목",
        description="",
        location="town_square",
        disposition="hostile",
        health=50,
        max_health=50,
        mana=30,
        skills=["skill_slash"]
    )
    test_world.npcs["orc_boss"] = orc
    test_world.locations["town_square"].npcs.append("orc_boss")

    # Player attacks orc
    fact_sheet = TwoPassEngine.compute_pass1("철 단검으로 오크 부두목을 찌른다", test_world)
    assert fact_sheet.is_valid is True
    # Verify NPC combat action was logged
    assert len(fact_sheet.npc_skill_logs) > 0
    prompt_context = fact_sheet.to_prompt_context()
    assert "현장 NPC 자율 스킬 및 기회주의적 행동 확정 연산" in prompt_context
