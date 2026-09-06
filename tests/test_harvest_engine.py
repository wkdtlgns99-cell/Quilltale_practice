"""
Unit tests for AnatomyHarvestEngine and Equipment Set Bonuses.
Tests:
1. Hitzone physics multipliers (slash, blunt, shot) on different monster anatomical parts.
2. Tactical part break effects & monster stagger.
3. Physical tail severing with slashing attacks and field floor item dropping.
4. Clean vital kill harvesting (100% guaranteed pristine material yield).
5. Broken part ruin penalty (~50% ruin chance yielding damaged scrap vs pristine material).
6. Field carving of severed limbs on the ground.
7. Equipment set bonuses for rare/epic general gear (Royal Guard, Shadow Assassin, Ancient Arcanist).
8. Equipment set bonuses for monster material gear (Thunder Catfish, Dread Wyvern).
9. Save/load backwards compatibility with anatomy fields.
"""
import pytest
from src.world.state import WorldState, Player, NPC, Location, Item, EquipmentSlots
from src.world.harvest_engine import (
    AnatomyHarvestEngine, MonsterPart, PartAttackResult, HarvestOutcome
)
from src.world.equipment import EquipmentEngine


@pytest.fixture
def harvest_world():
    state = WorldState()
    loc = Location(id="swamp_shallows", name="뇌운의 늪지대", description="전류가 흐르는 얕은 여울", exits={})
    state.locations["swamp_shallows"] = loc
    state.player.location = "swamp_shallows"
    state.player.inventory = []
    
    # Give player a carving knife
    knife = Item(
        id="carving_knife",
        name="무쇠 도축용 단검",
        description="가죽을 벗기고 뼈를 바르는 데 쓰이는 날렵한 칼",
        location="inventory",
        item_type="tool",
        durability=50,
        max_durability=50
    )
    state.items["carving_knife"] = knife
    state.player.inventory.append("carving_knife")

    # Create Copper-Scaled Thunder Catfish NPC
    anatomy = AnatomyHarvestEngine.create_standard_monster_anatomy("copper_scaled_thunder_catfish")
    catfish = NPC(
        id="boss_thunder_catfish",
        name="동판 비늘의 벼락 메기",
        description="청록색 구리 비늘로 덮인 거대 담수어 마수",
        location="swamp_shallows",
        level=5,
        health=150,
        max_health=150,
        alive=True,
        anatomy_parts=anatomy,
        harvested_parts=[]
    )
    state.npcs["boss_thunder_catfish"] = catfish
    loc.npcs.append("boss_thunder_catfish")

    return state


def test_hitzone_multipliers(harvest_world):
    monster = harvest_world.npcs["boss_thunder_catfish"]
    
    # 1. Blunt attack against hard horn (head_horn hitzone_blunt is 1.4, hitzone_slash is 0.7)
    res_blunt = AnatomyHarvestEngine.attack_targeted_part(
        monster, part_id="head_horn", raw_damage=20, attack_tags=["blunt"]
    )
    # 20 * 1.4 = 28
    assert res_blunt.effective_damage == 28
    assert res_blunt.hitzone_multiplier == 1.4

    # 2. Slash attack against hard horn
    res_slash = AnatomyHarvestEngine.attack_targeted_part(
        monster, part_id="head_horn", raw_damage=20, attack_tags=["slash"]
    )
    # 20 * 0.7 = 14
    assert res_slash.effective_damage == 14
    assert res_slash.hitzone_multiplier == 0.7

    # 3. Shot attack against soft electric sac (electric_sac hitzone_shot is 1.5)
    res_shot = AnatomyHarvestEngine.attack_targeted_part(
        monster, part_id="electric_sac", raw_damage=10, attack_tags=["shot"]
    )
    # 10 * 1.5 = 15
    assert res_shot.effective_damage == 15
    assert res_shot.hitzone_multiplier == 1.5


def test_part_breaking_and_stagger(harvest_world):
    monster = harvest_world.npcs["boss_thunder_catfish"]
    horn = monster.anatomy_parts["head_horn"]
    assert horn.current_hp == 35
    assert not horn.is_broken

    # Attack with blunt weapon for 30 raw * 1.4 = 42 damage -> exceeds 35 max HP
    result = AnatomyHarvestEngine.attack_targeted_part(
        monster, part_id="head_horn", raw_damage=30, attack_tags=["blunt"]
    )
    assert result.is_now_broken is True
    assert result.stagger_inflicted is True
    assert horn.is_broken is True
    assert horn.current_hp == 0
    assert "부위 파괴" in result.combat_log_ko


def test_tail_severing_and_ground_item_drop(harvest_world):
    monster = harvest_world.npcs["boss_thunder_catfish"]
    tail = monster.anatomy_parts["lightning_rod_tail"]
    assert tail.severable is True
    assert not tail.is_severed

    # Slash attack for 40 raw * 1.3 = 52 damage -> drops tail HP to 0 and severs it
    result = AnatomyHarvestEngine.attack_targeted_part(
        monster, part_id="lightning_rod_tail", raw_damage=40, attack_tags=["slash"], state=harvest_world
    )
    assert result.is_now_severed is True
    assert tail.is_severed is True
    assert result.dropped_severed_item_id == "severed_lightning_rod_tail_boss_thunder_catfish"
    assert "신체 절단" in result.combat_log_ko

    # Check that severed tail item exists on the location floor
    loc = harvest_world.locations["swamp_shallows"]
    assert "severed_lightning_rod_tail_boss_thunder_catfish" in loc.items
    severed_item = harvest_world.items["severed_lightning_rod_tail_boss_thunder_catfish"]
    assert "잘려나간 피뢰침 꼬리" in severed_item.name


def test_harvest_intact_part_clean_kill(harvest_world):
    monster = harvest_world.npcs["boss_thunder_catfish"]
    player = harvest_world.player

    # Living monster cannot be harvested
    valid, reason = AnatomyHarvestEngine.can_harvest(player, monster, "copper_scales", harvest_world)
    assert not valid
    assert "살아있는" in reason

    # Monster killed cleanly via vitals (parts intact)
    monster.alive = False
    scales_part = monster.anatomy_parts["copper_scales"]
    assert not scales_part.is_broken

    # Harvest intact scales
    outcome = AnatomyHarvestEngine.harvest_part(
        player, monster, "copper_scales", harvest_world, knife_item_id="carving_knife"
    )
    assert outcome.success is True
    assert outcome.is_ruined is False
    assert outcome.item_id == "copper_plate_scales"
    assert outcome.item_name_ko == "【통전성 구리 비늘】"
    assert "copper_plate_scales" in player.inventory
    assert "copper_scales" in monster.harvested_parts

    # Carving knife lost 1 durability
    knife = harvest_world.items["carving_knife"]
    assert knife.durability == 49

    # Cannot harvest the same part twice
    outcome_again = AnatomyHarvestEngine.harvest_part(
        player, monster, "copper_scales", harvest_world
    )
    assert outcome_again.success is False
    assert "이미 온전히" in outcome_again.narration_ko


def test_harvest_broken_part_ruin_penalty(harvest_world):
    monster = harvest_world.npcs["boss_thunder_catfish"]
    player = harvest_world.player
    monster.alive = False

    horn = monster.anatomy_parts["head_horn"]
    horn.is_broken = True

    # 1. Unlucky roll (0.2 < 0.50) -> material is ruined and yields scrap
    outcome_ruined = AnatomyHarvestEngine.harvest_part(
        player, monster, "head_horn", harvest_world, rng_roll=0.2
    )
    assert outcome_ruined.success is True
    assert outcome_ruined.is_ruined is True
    assert outcome_ruined.item_id == "broken_horn_fragment"
    assert "금 간 뇌각 조각" in outcome_ruined.item_name_ko
    assert "broken_horn_fragment" in player.inventory

    # Reset for lucky test on electric sac
    sac = monster.anatomy_parts["electric_sac"]
    sac.is_broken = True

    # 2. Lucky roll (0.8 >= 0.50) -> salvages pristine material despite part being broken
    outcome_lucky = AnatomyHarvestEngine.harvest_part(
        player, monster, "electric_sac", harvest_world, rng_roll=0.8
    )
    assert outcome_lucky.success is True
    assert outcome_lucky.is_ruined is False
    assert outcome_lucky.item_id == "high_voltage_organ"
    assert outcome_lucky.item_name_ko == "【고전압 발전낭】"
    assert "high_voltage_organ" in player.inventory


def test_harvest_severed_limb_from_ground(harvest_world):
    monster = harvest_world.npcs["boss_thunder_catfish"]
    player = harvest_world.player

    # Sever tail during combat
    AnatomyHarvestEngine.attack_targeted_part(
        monster, part_id="lightning_rod_tail", raw_damage=40, attack_tags=["slash"], state=harvest_world
    )
    severed_id = "severed_lightning_rod_tail_boss_thunder_catfish"
    loc = harvest_world.locations["swamp_shallows"]
    assert severed_id in loc.items

    # Player carves the severed tail directly from the ground
    outcome = AnatomyHarvestEngine.harvest_severed_object(
        player, severed_id, harvest_world, knife_item_id="carving_knife"
    )
    assert outcome.success is True
    assert "copper_catfish_tail" in player.inventory
    # The severed chunk is now consumed and removed from the floor
    assert severed_id not in loc.items


def test_equipment_set_bonuses_rare_general(harvest_world):
    state = harvest_world
    player = state.player
    player.strength = 10
    player.constitution = 10
    player.base_armor_class = 10

    # Create 4 pieces of Royal Guard set
    pieces = [
        ("rg_head", "왕실 근위대의 투구", "head", 4),
        ("rg_chest", "왕실 근위대의 흉갑", "chest", 8),
        ("rg_gloves", "왕실 근위대의 건틀릿", "gloves", 3),
        ("rg_boots", "왕실 근위대의 판금화", "boots", 3),
    ]
    for p_id, p_name, slot, def_val in pieces:
        state.items[p_id] = Item(
            id=p_id, name=p_name, description="", location="inventory",
            item_type="armor", defense=def_val, properties={"set_id": "set_royal_guard"}
        )
        state.player.inventory.append(p_id)

    # 1. Equip 2 pieces (head + chest)
    state.apply_update({"equip_slot": {"item_id": "rg_head", "slot": "head"}})
    state.apply_update({"equip_slot": {"item_id": "rg_chest", "slot": "chest"}})
    
    # 2-piece bonus: defense +6, con +2, str +1, trait "경직 저항"
    # Base defense from items: 4 + 8 = 12. Set bonus defense: 6. Total = 18.
    bonuses_2 = EquipmentEngine.calculate_equipment_bonuses(state, player)
    assert bonuses_2["total_defense"] == 18
    assert bonuses_2["stat_bonuses"]["constitution"] == 2
    assert bonuses_2["stat_bonuses"]["strength"] == 1
    assert "경직 저항" in bonuses_2["active_traits"]
    assert len(bonuses_2["active_set_bonuses"]) == 1

    # 2. Equip 4 pieces (gloves + boots)
    state.apply_update({"equip_slot": {"item_id": "rg_gloves", "slot": "gloves"}})
    state.apply_update({"equip_slot": {"item_id": "rg_boots", "slot": "boots"}})

    # 4-piece bonus activates threshold 2 AND threshold 4!
    # Threshold 2: def +6, con +2, str +1
    # Threshold 4: def +16, con +5, str +3
    # Total set def bonus = 22. Items defense = 4 + 8 + 3 + 3 = 18. Total def = 40!
    bonuses_4 = EquipmentEngine.calculate_equipment_bonuses(state, player)
    assert bonuses_4["total_defense"] == 40
    assert bonuses_4["stat_bonuses"]["constitution"] == 7
    assert bonuses_4["stat_bonuses"]["strength"] == 4
    assert "넉백 완전 면역" in bonuses_4["active_traits"]
    assert len(bonuses_4["active_set_bonuses"]) == 2


def test_equipment_set_bonuses_monster_materials(harvest_world):
    state = harvest_world
    player = state.player

    # Create 2 pieces of Thunder Catfish set
    state.items["tc_helm"] = Item(
        id="tc_helm", name="뇌각 절연 투구", description="", location="inventory",
        item_type="armor", defense=4, properties={"set_id": "set_thunder_catfish"}
    )
    state.items["tc_robe"] = Item(
        id="tc_robe", name="동판 비늘 로브", description="", location="inventory",
        item_type="armor", defense=6, properties={"set_id": "set_thunder_catfish"}
    )
    state.player.inventory.extend(["tc_helm", "tc_robe"])

    state.apply_update({"equip_slot": {"item_id": "tc_helm", "slot": "head"}})
    state.apply_update({"equip_slot": {"item_id": "tc_robe", "slot": "chest"}})

    bonuses = EquipmentEngine.calculate_equipment_bonuses(state, player)
    # Items def 10 + set 2-pc def 4 = 14
    assert bonuses["total_defense"] == 14
    assert bonuses["stat_bonuses"]["max_mana"] == 20
    assert "전격 저항 50%" in bonuses["active_traits"]
    assert any(b["bonus_name_ko"] == "전격 저항 및 축전" for b in bonuses["active_set_bonuses"])


def test_save_load_backwards_compatibility_with_anatomy(harvest_world):
    # Test that WorldState can serialize and deserialize with anatomy_parts and harvested_parts
    json_str = harvest_world.to_json()
    loaded_state = WorldState.from_json(json_str)

    loaded_monster = loaded_state.npcs["boss_thunder_catfish"]
    assert hasattr(loaded_monster, "anatomy_parts")
    assert "head_horn" in loaded_monster.anatomy_parts
    assert hasattr(loaded_monster, "harvested_parts")

    # Also test that a legacy state without anatomy_parts safely initializes with defaults
    legacy_raw = {
        "world_id": "legacy_world",
        "npcs": {
            "old_npc": {
                "id": "old_npc",
                "name": "옛날 NPC",
                "health": 30
            }
        }
    }
    legacy_state = WorldState.from_dict(legacy_raw)
    assert "old_npc" in legacy_state.npcs
    assert legacy_state.npcs["old_npc"].anatomy_parts == {}
    assert legacy_state.npcs["old_npc"].harvested_parts == []
