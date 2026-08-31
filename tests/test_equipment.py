import pytest
import json
from src.world.state import WorldState, Player, EquipmentSlots, Item
from src.core.config import MAX_RINGS, MAX_EARRINGS


@pytest.fixture
def test_state():
    from src.world.state import Location
    state = WorldState()
    state.locations = {'start': Location(id='start', name='시작 지점', description='테스트 위치', exits={})}
    state.player.location = 'start'

    state.items = {
        'dagger': Item(id='dagger', name='단검', description='', location='inventory', item_type='weapon', damage=5),
        'ring1': Item(id='ring1', name='반지1', description='', location='inventory', item_type='misc'),
        'earring1': Item(id='earring1', name='귀걸이1', description='', location='inventory', item_type='misc')
    }
    state.player.inventory = ['dagger', 'ring1', 'earring1']
    return state


def test_apply_update_equip_weapon(test_state):
    update = {'equip_slot': {'item_id': 'dagger', 'slot': 'weapon'}}
    test_state.apply_update(update)
    assert test_state.player.equipment.weapon == 'dagger'

def test_max_rings(test_state):
    # Fill rings
    for i in range(MAX_RINGS):
        item_id = f'ring_test_{i}'
        test_state.items[item_id] = Item(id=item_id, name=f'반지{i}', description='', location='inventory', item_type='misc')
        test_state.player.inventory.append(item_id)
        test_state.player.equipment.rings.append(item_id)
    
    update = {'equip_slot': {'item_id': 'ring1', 'slot': 'ring'}}
    test_state.apply_update(update)
    assert len(test_state.player.equipment.rings) == MAX_RINGS
    assert 'ring1' not in test_state.player.equipment.rings

def test_max_earrings(test_state):
    # Fill earrings
    for i in range(MAX_EARRINGS):
        item_id = f'earring_test_{i}'
        test_state.items[item_id] = Item(id=item_id, name=f'귀걸이{i}', description='', location='inventory', item_type='misc')
        test_state.player.inventory.append(item_id)
        test_state.player.equipment.earrings.append(item_id)
    
    update = {'equip_slot': {'item_id': 'earring1', 'slot': 'earring'}}
    test_state.apply_update(update)
    assert len(test_state.player.equipment.earrings) == MAX_EARRINGS
    assert 'earring1' not in test_state.player.equipment.earrings

def test_equipment_serialization(test_state):
    test_state.player.equipment.weapon = 'dagger'
    test_state.player.equipment.rings.append('ring1')
    
    json_data = test_state.to_json()
    new_state = WorldState.from_json(json_data)
    
    assert new_state.player.equipment.weapon == 'dagger'
    assert 'ring1' in new_state.player.equipment.rings

def test_player_summary_shows_equipment(test_state):
    test_state.player.equipment.weapon = 'dagger'
    output = test_state.to_player_summary()
    assert '무기' in output
    assert '단검' in output

