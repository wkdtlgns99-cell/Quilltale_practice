import pytest
from src.world.state import WorldState, Player, NPC, Skill, Title
from src.world.skills import SkillSystem

@pytest.fixture
def test_state():
    state = WorldState()
    state.skills_db = {
        'skill1': Skill(id='skill1', name='스킬1', skill_type='passive', effect={'stat_bonuses': {'strength': 2}}),
        'skill2': Skill(id='skill2', name='스킬2', skill_type='active'),
    }
    state.titles_db = {
        'title1': Title(id='title1', name='타이틀1', description='타이틀1입니다.')
    }
    return state

@pytest.fixture
def test_player():
    return Player()

def test_can_player_acquire(test_player, test_state):
    test_player.skills.append('skill1')
    can, _ = SkillSystem.can_player_acquire(test_player, test_state.skills_db['skill1'], test_state)
    assert can is False
    
    can, _ = SkillSystem.can_player_acquire(test_player, test_state.skills_db['skill2'], test_state)
    assert can is True

def test_acquire_skill(test_player, test_state):
    success, _ = SkillSystem.acquire_skill(test_player, 'skill2', test_state)
    assert success is True
    assert 'skill2' in test_player.skills
    
def test_apply_passive_bonuses(test_player, test_state):
    test_player.skills.append('skill1')
    bonuses = SkillSystem.apply_passive_bonuses(test_player, test_state)
    assert bonuses.get('strength') == 2
    
def test_roll_unique_skill_drop(test_player):
    npc = NPC(id='npc1', name='NPC', description='', location='')
    npc.skills = ['skill1']
    
    # luck 10
    test_player.luck = 10
    count_10 = 0
    for _ in range(200):
        if SkillSystem.roll_unique_skill_drop(npc, test_player):
            count_10 += 1
            
    # luck 20
    test_player.luck = 20
    count_20 = 0
    for _ in range(200):
        if SkillSystem.roll_unique_skill_drop(npc, test_player):
            count_20 += 1
            
    assert count_20 > count_10
    
def test_grant_title_not_in_db(test_player, test_state):
    success, _ = SkillSystem.grant_title(test_player, 'invalid_title', test_state)
    assert success is False
    
def test_grant_title_already_has(test_player, test_state):
    test_player.titles.append('title1')
    success, _ = SkillSystem.grant_title(test_player, 'title1', test_state)
    assert success is False


def test_load_skill_templates():
    skills = SkillSystem.load_skill_templates()
    assert len(skills) >= 10

    # Test Fireball (arcane_magic)
    fireball = skills.get("skill_arcane_fireball_01")
    assert fireball is not None
    assert fireball.name == "작열 화염구 (이그니스 스페라)"
    assert fireball.category == "arcane_magic"
    assert fireball.resource_type == "mana"
    assert fireball.resource_cost == 25
    assert fireball.element == "화염"
    assert fireball.area_shape == "circle"
    assert fireball.area_radius_meters == 4.0
    assert fireball.is_forbidden is False

    # Test Shadow Sever (stealth / taboo)
    shadow_sever = skills.get("skill_stealth_shadow_sever_01")
    assert shadow_sever is not None
    assert "그림자 목긋기" in shadow_sever.name
    assert shadow_sever.resource_type == "stamina"
    assert shadow_sever.is_forbidden is True
    assert "암살단" in shadow_sever.taboo_reason

    # Test Bone Spike (necromancy / hp cost)
    bone_spike = skills.get("skill_forbidden_bone_spike_01")
    assert bone_spike is not None
    assert bone_spike.category == "necromancy"
    assert bone_spike.resource_type == "hp"
    assert bone_spike.resource_cost == 15
    assert bone_spike.is_forbidden is True

