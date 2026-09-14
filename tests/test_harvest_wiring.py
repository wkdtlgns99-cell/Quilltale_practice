"""
Integration tests for harvest_engine.py wiring into TwoPassEngine and ActionValidator.
Verifies monster part targeting, hitzone multipliers, physical tail severing,
field butchering/carving, broken part ruin penalties, and prompt context serialization.
"""
import pytest
from src.world.state import WorldState, Location, NPC, Item
from src.world.two_pass_engine import TwoPassEngine
from src.world.validator import ActionValidator
from src.world.harvest_engine import MonsterPart, AnatomyHarvestEngine


def setup_harvest_world():
    state = WorldState()
    loc = Location(
        id="hunting_ground",
        name="사냥터 평원",
        description="풀숲이 무성한 거수들의 사냥터.",
        exits={},
        npcs=[],
        items=[]
    )
    state.locations["hunting_ground"] = loc
    state.player.location = "hunting_ground"

    # Butchering knife in inventory
    knife = Item(
        id="hunting_knife_01",
        name="사냥꾼의 도축 단검",
        description="사체를 가르고 가죽을 벗겨내기에 적합한 예리한 단검.",
        location="inventory",
        item_type="tool",
        durability=50,
        max_durability=50,
        physics_tags=["slash", "blade"]
    )
    state.items["hunting_knife_01"] = knife
    state.player.inventory.append("hunting_knife_01")

    # Equipped sword
    sword = Item(
        id="iron_sword_01",
        name="강철 직검",
        description="날이 잘 선 강철검.",
        location="equipped",
        item_type="weapon",
        damage=20,
        durability=100,
        max_durability=100,
        properties={"weapon_type": "sword"}
    )
    state.items["iron_sword_01"] = sword
    state.player.equipment.weapon = "iron_sword_01"

    # Monster with anatomy parts
    monster = NPC(
        id="thunder_catfish",
        name="뇌격 메기",
        description="전신에 푸른 번개를 두른 거대 늪지 수룡.",
        location="hunting_ground",
        health=150,
        max_health=150,
        disposition="hostile"
    )

    tail = MonsterPart(
        part_id="lightning_tail",
        name_ko="뇌전 꼬리",
        max_hp=20,
        current_hp=20,
        severable=True,
        hitzone_slash=1.2,
        hitzone_blunt=0.6,
        hitzone_shot=0.8,
        material_item_id="mat_thunder_tail",
        material_name_ko="【뇌격 메기의 번개 꼬리】",
        material_description_ko="농축된 전격 주머니가 온전히 보존된 꼬리.",
        ruined_item_id="ruined_thunder_tail",
        ruined_name_ko="【파손된 꼬리 파편】",
        ruined_description_ko="전격 주머니가 터져버린 꼬리 잔해.",
        ruin_chance_if_broken=0.5,
        break_effect_ko="번개 방전 마법 무력화"
    )
    horn = MonsterPart(
        part_id="head_horn",
        name_ko="통전 뇌각",
        max_hp=30,
        current_hp=30,
        severable=False,
        hitzone_slash=0.8,
        hitzone_blunt=1.5,
        hitzone_shot=0.5,
        material_item_id="mat_head_horn",
        material_name_ko="【통전성 뇌각】",
        material_description_ko="극상의 전도성을 지닌 뇌각.",
        ruined_item_id="ruined_head_horn",
        ruined_name_ko="【부서진 뇌각 파편】",
        ruined_description_ko="산산조각 난 뇌각 조각.",
        ruin_chance_if_broken=1.0,
        break_effect_ko="돌진 들이받기 저지"
    )

    monster.anatomy_parts = {
        "lightning_tail": tail,
        "head_horn": horn
    }
    state.npcs["thunder_catfish"] = monster
    loc.npcs.append("thunder_catfish")

    return state


def test_monster_part_targeting_and_tail_severing():
    """참격 무기로 꼬리 부위 조준 타격 시 육질 배율 적용 및 꼬리 절단 필드 드랍 검증."""
    state = setup_harvest_world()
    action = "강철 직검을 크게 휘둘러 뇌격 메기의 꼬리를 베어버린다"

    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid
    monster = state.npcs["thunder_catfish"]
    tail = monster.anatomy_parts["lightning_tail"]

    # Tail should be broken and severed
    assert tail.is_broken
    assert tail.is_severed

    # Dropped severed tail item must exist in current location
    curr_loc = state.current_location()
    severed_item_id = f"severed_lightning_tail_{monster.id}"
    assert severed_item_id in state.items
    assert severed_item_id in curr_loc.items
    assert state.items[severed_item_id].properties.get("severed_part") is True

    # Prompt context check
    prompt_ctx = fact_sheet.to_prompt_context()
    assert "신체 절단" in prompt_ctx or "부위 파괴" in prompt_ctx


def test_field_harvest_pristine_part():
    """처치된 마수 사체에서 온전한 부위 갈무리 시 100% 최상급 완제품 획득 및 도축 칼 내구도 -1 검증."""
    state = setup_harvest_world()
    monster = state.npcs["thunder_catfish"]
    monster.alive = False  # Slain
    monster.health = 0

    action = "사체 옆에 무릎을 꿇고 도축 단검으로 뇌격 메기의 뇌각 부위를 조심스럽게 갈무리한다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid
    assert fact_sheet.harvest_summary is not None
    assert "【통전성 뇌각】" in fact_sheet.harvest_summary

    # Material item in player inventory
    assert "mat_head_horn" in state.player.inventory

    # Knife durability consumed
    knife = state.items["hunting_knife_01"]
    assert knife.durability == 49

    # Part marked as harvested
    assert "head_horn" in monster.harvested_parts


def test_field_harvest_broken_part_ruin_penalty():
    """파괴된 부위 갈무리 시 100% 확률로 짓이겨진 파편 잔해로 열화되는지 검증."""
    state = setup_harvest_world()
    monster = state.npcs["thunder_catfish"]
    monster.alive = False
    monster.health = 0
    # Mark horn as broken (ruin_chance_if_broken = 1.0)
    monster.anatomy_parts["head_horn"].is_broken = True

    action = "도축 단검으로 뇌격 메기의 뇌각을 갈무리한다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid
    assert "【부서진 뇌각 파편】" in fact_sheet.harvest_summary
    assert "ruined_head_horn" in state.player.inventory


def test_field_harvest_severed_ground_object():
    """필드 바닥에 떨어진 절단 꼬리 아이템을 직접 해체하여 소재 획득 검증."""
    state = setup_harvest_world()
    curr_loc = state.current_location()

    # Pre-spawn a severed tail item on the ground
    severed_id = "severed_lightning_tail_drop"
    severed_item = Item(
        id=severed_id,
        name="【뇌격 메기의 잘려나간 뇌전 꼬리】",
        description="바닥에 뒹구는 거대한 꼬리 잔해.",
        location=curr_loc.id,
        item_type="material",
        properties={
            "severed_part": True,
            "material_item_id": "mat_thunder_tail",
            "material_name_ko": "【뇌격 메기의 번개 꼬리】"
        }
    )
    state.items[severed_id] = severed_item
    curr_loc.items.append(severed_id)

    action = "바닥에 떨어진 꼬리를 도축 단검으로 해체하여 소재를 떼어낸다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid
    assert "mat_thunder_tail" in state.player.inventory
    assert state.items["hunting_knife_01"].durability == 49


def test_cannot_harvest_living_monster():
    """살아있는 몬스터를 상대로 갈무리/도축 시도 시 사전 차단 검증."""
    state = setup_harvest_world()
    monster = state.npcs["thunder_catfish"]
    assert monster.alive is True

    action = "살아있는 뇌격 메기를 칼로 도축하고 갈무리한다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert not fact_sheet.is_valid
    assert "살아있는 채로 해체하거나 갈무리할 수는 없습니다" in fact_sheet.rejection_reason


def test_cannot_harvest_without_knife():
    """도축용 단검/칼붙이가 없을 때 사체 갈무리 실패 검증."""
    state = setup_harvest_world()
    monster = state.npcs["thunder_catfish"]
    monster.alive = False
    monster.health = 0

    # Remove all knives/slashing weapons
    state.player.inventory.clear()
    state.player.equipment.weapon = None

    action = "뇌격 메기의 뇌각을 갈무리한다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert not fact_sheet.is_valid or (fact_sheet.harvest_summary and "도축용 단검이나 날붙이" in fact_sheet.harvest_summary)
