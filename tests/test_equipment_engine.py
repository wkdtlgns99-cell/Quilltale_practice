import pytest
from src.world.state import WorldState, Player, EquipmentSlots, Item
from src.world.equipment import EquipmentEngine
from src.core.config import MAX_RINGS, MAX_EARRINGS


@pytest.fixture
def equip_state():
    from src.world.state import Location
    state = WorldState()
    state.locations = {'start': Location(id='start', name='시작 지점', description='테스트 위치', exits={})}
    state.player.location = 'start'
    state.player.strength = 10
    state.player.agility = 10
    state.player.intelligence = 10
    state.player.base_armor_class = 10

    # Armor pieces
    state.items["helm_iron"] = Item(
        id="helm_iron", name="강철 투구", description="", location="inventory",
        item_type="armor", defense=3, properties={"stat_bonuses": {"con": 2}}, durability=100
    )
    state.items["plate_chest"] = Item(
        id="plate_chest", name="강철 흉갑", description="", location="inventory",
        item_type="armor", defense=8, properties={"stat_bonuses": {"str": 4}}, durability=100
    )
    state.items["boots_speed"] = Item(
        id="boots_speed", name="신속의 부츠", description="", location="inventory",
        item_type="armor", defense=2, properties={"stat_bonuses": {"dex": 3}}, durability=100
    )
    state.items["ring_ruby"] = Item(
        id="ring_ruby", name="루비 반지", description="", location="inventory",
        item_type="ring", defense=0, properties={"stat_bonuses": {"str": 2, "crit": 5}}
    )
    state.items["ring_sapphire"] = Item(
        id="ring_sapphire", name="사파이어 반지", description="", location="inventory",
        item_type="ring", defense=0, properties={"stat_bonuses": {"int": 3, "mana": 20}}
    )

    state.player.inventory = ["helm_iron", "plate_chest", "boots_speed", "ring_ruby", "ring_sapphire"]
    return state


def test_equipment_defense_and_ac_calculation(equip_state):
    # Initially, player has only base AC 10
    assert equip_state.player.armor_class == 10

    # Equip helmet and chest
    equip_state.apply_update({"equip_slot": {"item_id": "helm_iron", "slot": "head"}})
    equip_state.apply_update({"equip_slot": {"item_id": "plate_chest", "slot": "chest"}})

    # Total defense should be 3 + 8 = 11
    # AC should be base 10 + agi_mod 0 + defense 11 = 21
    assert equip_state.player.equipment_defense == 11
    assert equip_state.player.armor_class == 21

    # Equip boots (defense 2, dex +3 -> agility becomes 13 -> agi_mod (13-10)//2 = 1)
    equip_state.apply_update({"equip_slot": {"item_id": "boots_speed", "slot": "boots"}})
    # Total defense: 11 + 2 = 13
    # Effective agility: 10 + 3 = 13 (mod +1)
    # AC: 10 + 1 + 13 = 24
    assert equip_state.player.equipment_defense == 13
    assert equip_state.player.effective_agility == 13
    assert equip_state.player.armor_class == 24


def test_ring_and_accessory_stat_bonuses(equip_state):
    # Equip chest (str +4), ring_ruby (str +2, crit +5), ring_sapphire (int +3)
    equip_state.apply_update({"equip_slot": {"item_id": "plate_chest", "slot": "chest"}})
    equip_state.apply_update({"equip_slot": {"item_id": "ring_ruby", "slot": "ring"}})
    equip_state.apply_update({"equip_slot": {"item_id": "ring_sapphire", "slot": "ring"}})

    # Base strength was 10, should now be 10 + 4 + 2 = 16
    assert equip_state.player.effective_strength == 16
    # Base intelligence was 10, should now be 10 + 3 = 13
    assert equip_state.player.effective_intelligence == 13
    # Effective crit rate increased by 5 points
    assert equip_state.player.equipment_stat_bonuses["crit_rate"] == 5


def test_unequip_on_drop_recalculates_stats(equip_state):
    equip_state.apply_update({"equip_slot": {"item_id": "helm_iron", "slot": "head"}})
    assert equip_state.player.equipment_defense == 3
    assert equip_state.player.armor_class == 13

    # Drop helmet
    equip_state.apply_update({"drop_item": "helm_iron"})
    assert equip_state.player.equipment.head is None
    assert equip_state.player.equipment_defense == 0
    assert equip_state.player.armor_class == 10


def test_armor_durability_and_mitigation(equip_state):
    equip_state.apply_update({"equip_slot": {"item_id": "helm_iron", "slot": "head"}})
    equip_state.apply_update({"equip_slot": {"item_id": "plate_chest", "slot": "chest"}})

    # Attack to head
    mitigated, logs = EquipmentEngine.apply_armor_durability_and_mitigation(
        equip_state, equip_state.player, incoming_damage=20, target_part="머리"
    )
    # Helm defense is 3 -> mitigated = 20 - (3//2) = 19
    assert mitigated == 19
    # Helm durability reduced from 100 to 99
    assert equip_state.items["helm_iron"].durability == 99


def test_body_part_slot_mapping():
    assert EquipmentEngine.get_slot_for_body_part("머리") == "head"
    assert EquipmentEngine.get_slot_for_body_part("눈") == "face"
    assert EquipmentEngine.get_slot_for_body_part("가슴") == "chest"
    assert EquipmentEngine.get_slot_for_body_part("다리") == "legs"
    assert EquipmentEngine.get_slot_for_body_part("발") == "boots"
    assert EquipmentEngine.get_slot_for_body_part("손") == "gloves"
