"""
Unit tests for UniversalObjectPhysicsEngine
Tests all-encompassing physical object durability, material resolution heuristics,
debris fragmentation (chairs to clubs, glass to shards, paper to ashes),
container spilling, improvised weapon stats, and LLM prompt generation.
"""
import pytest

from src.world.state import WorldState, Item, Location
from src.world.object_physics_engine import (
    UniversalObjectPhysicsEngine,
    MaterialSpec,
    ObjectInteractionResult,
    MATERIAL_REGISTRY
)


def create_test_state_with_location():
    state = WorldState()
    loc = Location(
        id="tavern_hall",
        name="주점 홀",
        description="탁자와 의자가 널브러진 시끌벅적한 주점.",
        exits={"north": "street"}
    )
    state.locations["tavern_hall"] = loc
    state.player.location = "tavern_hall"
    return state


def test_material_resolution_heuristics():
    """모든 사물의 명칭과 속성으로부터 12대 재질이 정확히 판별되는지 검증"""
    items_to_test = [
        (Item(id="i1", name="낡은 참나무 의자", description="", location="tavern_hall"), "wood"),
        (Item(id="i2", name="비밀 지령 양피지 서한", description="", location="tavern_hall"), "paper"),
        (Item(id="i3", name="투명한 유리 플라스크 포션병", description="", location="tavern_hall"), "glass"),
        (Item(id="i4", name="비단 침구 덮개", description="", location="tavern_hall"), "cloth"),
        (Item(id="i5", name="모험가 사냥 가죽 배낭", description="", location="tavern_hall"), "leather"),
        (Item(id="i6", name="모난 자연 암반 돌멩이", description="", location="tavern_hall"), "stone"),
        (Item(id="i7", name="단단한 무쇠 냄비", description="", location="tavern_hall"), "metal"),
        (Item(id="i8", name="황금 미스릴 보석 반지", description="", location="tavern_hall"), "precious_metal"),
        (Item(id="i9", name="붉은 점토 화덕", description="", location="tavern_hall"), "clay"),
        (Item(id="i10", name="구운 칠면조 고기 요리", description="", location="tavern_hall"), "flesh"),
        (Item(id="i11", name="허름한 목조 오두막", description="", location="tavern_hall"), "structure_wood"),
        (Item(id="i12", name="거대한 석조 성벽 망루", description="", location="tavern_hall"), "structure_stone"),
    ]

    for item, expected_mat in items_to_test:
        detected = UniversalObjectPhysicsEngine.resolve_material(item)
        assert detected == expected_mat, f"Item '{item.name}' should resolve to {expected_mat}, got {detected}"

    # 명시적 trait 우선 판정 검증
    custom_item = Item(id="custom_1", name="이상한 물건", description="", location="tavern_hall", traits=["mat:paper"])
    assert UniversalObjectPhysicsEngine.resolve_material(custom_item) == "paper"


def test_wood_furniture_smash_and_debris():
    """목재 의자/책상 타격 시 내구도 삭감, 완파 시 각목(즉석 무기) 및 장작 스폰 검증"""
    state = create_test_state_with_location()
    chair = Item(
        id="tavern_chair_01",
        name="주점 목재 의자",
        description="투박하지만 튼튼한 참나무 의자.",
        location="tavern_hall",
        durability=80,
        max_durability=80
    )
    state.items["tavern_chair_01"] = chair
    state.locations["tavern_hall"].items.append("tavern_chair_01")

    # 1차 타격: 35 데미지 (목재 경도 6 감쇠 -> 실피해 29)
    res1 = UniversalObjectPhysicsEngine.damage_object(state, chair, raw_damage=35.0, damage_type="blunt")
    assert res1.effective_damage == 29.0
    assert chair.durability == 51
    assert not chair.is_destroyed
    assert res1.status_transition == "intact"

    # 2차 강타: 80 데미지 -> 내구도 소진 파괴
    res2 = UniversalObjectPhysicsEngine.damage_object(state, chair, raw_damage=80.0, damage_type="blunt")
    assert chair.is_destroyed is True
    assert chair.durability == 0
    assert res2.status_transition in ["destroyed", "shattered"]
    assert res2.sound_db == 45

    # 바닥에 각목(broken club)과 땔감 장작 스폰 확인
    assert len(res2.debris_spawned) >= 2
    club = next((d for d in res2.debris_spawned if "각목" in d.name), None)
    assert club is not None
    assert club.can_wield_as_weapon is True
    assert club.damage >= 3
    assert club.id in state.locations["tavern_hall"].items


def test_paper_document_incineration():
    """종이 서적/양피지에 불이 붙으면 즉각 전소되어 잿더미로 변하고 본문이 소멸하는지 검증"""
    state = create_test_state_with_location()
    secret_doc = Item(
        id="secret_ledger",
        name="영주의 비밀 탈세 장부",
        description="횡령 내역이 적힌 얇은 양피지 문서.",
        location="tavern_hall",
        durability=10,
        max_durability=10,
        document_text="3월 15일: 국고 50,000 골드 비밀 은닉 완료."
    )
    state.items["secret_ledger"] = secret_doc
    state.locations["tavern_hall"].items.append("secret_ledger")

    # 횃불 화염 공격
    res = UniversalObjectPhysicsEngine.ignite_object(state, secret_doc, fire_intensity=1.0)
    assert secret_doc.is_destroyed is True
    assert secret_doc.durability == 0
    assert res.status_transition == "incinerated"
    assert secret_doc.document_text == ""  # 텍스트 영구 소멸

    # 바닥에 잿더미 스폰 확인
    ashes = next((d for d in res.debris_spawned if "잿더미" in d.name), None)
    assert ashes is not None
    assert "ashes" in ashes.traits


def test_glass_brittleness_and_sharp_shards():
    """유리병 타격 시 높은 취성으로 즉각 박살 나며 65dB 소음 및 날카로운 유리 파편 생성 검증"""
    state = create_test_state_with_location()
    potion_bottle = Item(
        id="empty_potion_flask",
        name="빈 유리 물약병",
        description="투명한 유리로 만들어진 작고 둥근 플라스크.",
        location="tavern_hall",
        durability=15,
        max_durability=15
    )
    state.items["empty_potion_flask"] = potion_bottle
    state.locations["tavern_hall"].items.append("empty_potion_flask")

    # 둔기 10 피해 (취성 3.5배 적용 -> 즉시 박살)
    res = UniversalObjectPhysicsEngine.damage_object(state, potion_bottle, raw_damage=10.0, damage_type="blunt")
    assert potion_bottle.is_destroyed is True
    assert res.status_transition == "shattered"
    assert res.sound_db == 65

    # 날카로운 유리 파편 스폰 확인
    shards = next((d for d in res.debris_spawned if "유리 파편" in d.name), None)
    assert shards is not None
    assert "sharp_hazard" in shards.traits
    assert shards.can_wield_as_weapon is True


def test_metal_acid_corrosion():
    """금속 사물은 일반 타격에 단단하지만 산성(acid)에 급격히 부식되는지 검증"""
    state = create_test_state_with_location()
    iron_pot = Item(
        id="heavy_iron_pot",
        name="무쇠 주물 냄비",
        description="두꺼운 주철로 만든 냄비.",
        location="tavern_hall",
        durability=100,
        max_durability=100
    )
    state.items["iron_pot"] = iron_pot

    # 일반 타격: 경도 25로 인해 피해 1만 받음
    res_blunt = UniversalObjectPhysicsEngine.damage_object(state, iron_pot, raw_damage=20.0, damage_type="blunt")
    assert res_blunt.effective_damage == 1.0

    # 산성 부식액 공격: 산성 2.5배 배율 적용
    res_acid = UniversalObjectPhysicsEngine.damage_object(state, iron_pot, raw_damage=40.0, is_acid=True)
    assert res_acid.effective_damage > 30.0


def test_container_spilling_on_destruction():
    """보관함(상자, 서랍)이 파괴되면 수납된 아이템들이 바닥으로 쏟아지는지 검증"""
    state = create_test_state_with_location()
    # 수납될 내용물 아이템 생성
    state.items["gold_pouch"] = Item(id="gold_pouch", name="금화 주머니", description="반짝이는 금화.", location="chest_storage")
    state.items["iron_dagger"] = Item(id="iron_dagger", name="강철 단검", description="예리한 단검.", location="chest_storage")

    chest = Item(
        id="wooden_storage_chest",
        name="참나무 보물 궤짝",
        description="단단히 잠긴 보관용 상자.",
        location="tavern_hall",
        durability=40,
        max_durability=40,
        stored_items=["gold_pouch", "iron_dagger"]
    )
    state.items["wooden_storage_chest"] = chest
    state.locations["tavern_hall"].items.append("wooden_storage_chest")

    # 궤짝을 박살냄
    res = UniversalObjectPhysicsEngine.damage_object(state, chest, raw_damage=80.0, damage_type="blunt")
    assert chest.is_destroyed is True
    assert len(res.spilled_items) == 2
    assert "금화 주머니" in res.spilled_items
    assert "강철 단검" in res.spilled_items

    # 바닥에 아이템들이 쏟아져 나와있는지 확인
    assert "gold_pouch" in state.locations["tavern_hall"].items
    assert "iron_dagger" in state.locations["tavern_hall"].items
    assert state.items["gold_pouch"].location == "tavern_hall"


def test_improvised_weapon_mechanics():
    """임의의 사물을 즉석 무기로 사용할 때의 스탯 계산 검증"""
    chair = Item(id="c1", name="원목 의자", description="", location="loc", weight=6.0, improvised_damage=3)
    stats = UniversalObjectPhysicsEngine.improvise_weapon_stats(chair)
    assert stats["damage"] >= 8  # 기본 3 + 무게 6*0.8(4) + 경도(1) = 8
    assert stats["stagger_power"] > 10.0
    assert stats["material"] == "wood"

    flask = Item(id="f1", name="물약병", description="", location="loc", weight=0.5, improvised_damage=1)
    f_stats = UniversalObjectPhysicsEngine.improvise_weapon_stats(flask)
    assert f_stats["durability_loss_per_hit"] == 20  # 유리병은 한 번 치면 박살남


def test_repair_damaged_object():
    """손상된 사물의 수리 및 완파된 사물의 수리 거부 검증"""
    state = create_test_state_with_location()
    table = Item(id="table", name="주점 탁자", description="", location="loc", durability=30, max_durability=100)
    state.items["table"] = table

    ok, msg = UniversalObjectPhysicsEngine.repair_object(state, "table")
    assert ok is True
    assert table.durability == 80  # 30 + 50%
    assert "수리했습니다" in msg

    # 완파된 경우 수리 불가
    table.is_destroyed = True
    ok2, msg2 = UniversalObjectPhysicsEngine.repair_object(state, "table")
    assert ok2 is False
    assert "일반 수리가 불가능합니다" in msg2


def test_external_llm_prompt_generation():
    """규칙 8 준수 외부 대형 LLM 프롬프트 생성기 검증"""
    result = ObjectInteractionResult(
        target_item_id="glass_window",
        target_name="주점 스테인드글라스 창문",
        material="glass",
        initial_durability=15.0,
        raw_damage=25.0,
        effective_damage=15.0,
        remaining_durability=0.0,
        is_destroyed=True,
        status_transition="shattered",
        sound_db=65,
        narrative_log="창문이 박살 나며 날카로운 유리 파편이 비산했습니다."
    )

    prompt = UniversalObjectPhysicsEngine.generate_external_llm_prompt(result)
    assert "[시스템 컨텍스트: Quilltale TRPG 만물 물리 파괴 시뮬레이션 결과]" in prompt
    assert "스테인드글라스 창문" in prompt
    assert "65 dB" in prompt
    assert "shattered" in prompt


def test_tree_felling_and_stone_quarrying():
    """벌목 및 채석으로 사물이 파괴되며 자원 파편으로 분해되는지 검증"""
    state = create_test_state_with_location()
    tree = Item(
        id="tall_oak_tree",
        name="거대한 참나무",
        description="울창하게 솟은 참나무.",
        location="tavern_hall",
        durability=100,
        max_durability=100,
        material="wood"
    )
    boulder = Item(
        id="granite_boulder",
        name="거대한 화강암 바위",
        description="단단한 자연 바위.",
        location="tavern_hall",
        durability=200,
        max_durability=200,
        material="stone",
        hardness=15.0
    )
    state.items["tall_oak_tree"] = tree
    state.items["granite_boulder"] = boulder
    state.locations["tavern_hall"].items.extend(["tall_oak_tree", "granite_boulder"])

    # 벌목 (도끼 참격 120 피해)
    tree_res = UniversalObjectPhysicsEngine.damage_object(state, tree, raw_damage=120.0, damage_type="slash", attacker_name="벌목꾼")
    assert tree.is_destroyed is True
    assert any("장작" in d.name for d in tree_res.debris_spawned)

    # 채석 (곡괭이 250 피해)
    stone_res = UniversalObjectPhysicsEngine.damage_object(state, boulder, raw_damage=250.0, damage_type="blunt", attacker_name="광부")
    assert boulder.is_destroyed is True
    assert any("돌멩이" in d.name for d in stone_res.debris_spawned)


def test_worldstate_serialization_compatibility_with_materials():
    """Item의 material, hardness, stored_items가 WorldState 직렬화 시 완벽히 보존되는지 검증"""
    state = create_test_state_with_location()
    desk = Item(
        id="study_desk_01",
        name="서재 책상",
        description="마호가니 책상.",
        location="tavern_hall",
        material="wood",
        hardness=8.0,
        flammability=1.5,
        durability=90,
        max_durability=90,
        stored_items=["quill_pen", "inkpot"]
    )
    state.items["study_desk_01"] = desk

    raw = state.to_dict()
    assert "items" in raw
    assert "study_desk_01" in raw["items"]
    assert raw["items"]["study_desk_01"]["material"] == "wood"
    assert raw["items"]["study_desk_01"]["hardness"] == 8.0

    loaded = WorldState.from_dict(raw)
    loaded_desk = loaded.items["study_desk_01"]
    assert loaded_desk.material == "wood"
    assert loaded_desk.hardness == 8.0
    assert loaded_desk.flammability == 1.5
    assert loaded_desk.stored_items == ["quill_pen", "inkpot"]
