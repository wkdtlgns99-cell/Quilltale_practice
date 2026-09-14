"""
Integration tests for HerbalismBotanyEngine wiring into TwoPassEngine, WorldState, and ActionValidator.
Verifies wild plant foraging, disguised poisonous lookalike generation on botch roll,
precise plant identification revealing mimics, genuine herb healing vs toxic mushroom poisoning on consumption,
and combat/indoor validation rules.
"""
import pytest
from src.world.state import WorldState, Player, NPC, Location, Item
from src.world.two_pass_engine import TwoPassEngine
from src.world.validator import ActionValidator


@pytest.fixture
def botany_forest_world():
    state = WorldState()
    loc = Location(
        id="misty_forest",
        name="안개 낀 고대 솔숲",
        description="울창한 침엽수림과 축축한 이끼 바위가 가득한 야생 숲이다.",
        exits={},
        items=[],
        traits=["forest", "mountain", "wild"]
    )
    state.locations["misty_forest"] = loc
    state.player = Player(
        name="약초사 린",
        location="misty_forest",
        gold=30,
        health=40,
        max_health=50,
        mana=30,
        stamina=60,
        fatigue=20,
        intelligence=15,
        wisdom=14,
        perception=14,
        inventory=[]
    )
    return state


from unittest.mock import patch


def test_botany_forage_success_inventory_and_pass1(botany_forest_world):
    """야생 약초 채집 성공 시 인벤토리 등록, 아이템 생성 및 Pass 1 FactSheet 연동 검증."""
    init_inv_len = len(botany_forest_world.player.inventory)

    with patch("random.randint", return_value=18):
        fact = TwoPassEngine.compute_pass1(
            "주변 숲속 바위틈에서 지혈 이끼를 채집한다.", botany_forest_world
        )

    assert fact.is_valid is True
    assert fact.botany_summary is not None
    assert "채집 성공" in fact.botany_summary
    assert "지혈 이끼" in fact.botany_summary
    assert "🌿 [야생 식물학 채집/감별/섭취 판정" in fact.to_prompt_context()

    # 인벤토리 및 WorldState 등록 검증
    assert len(botany_forest_world.player.inventory) == init_inv_len + 1
    new_item_id = botany_forest_world.player.inventory[-1]
    assert new_item_id in botany_forest_world.items
    created_item = botany_forest_world.items[new_item_id]
    assert created_item.name == "지혈 이끼"
    assert created_item.true_spec_id == "blood_moss"
    assert created_item.is_identified is True
    assert created_item.is_poisonous_lookalike is False
    assert "botany_foraged" in created_item.traits


def test_botany_forage_lookalike_critical_failure(botany_forest_world):
    """채집 대실패(주사위 1) 시 외형 위장 맹독 유사종(독우산광대버섯) 채집 검증."""
    botany_res = TwoPassEngine.resolve_action_botany(
        "자연산 송이버섯을 조심스럽게 채집한다.", botany_forest_world, fixed_forage_roll=1
    )

    assert botany_res is not None
    assert botany_res["success"] is True
    assert botany_res["is_lookalike"] is True
    assert "식물학 판정 불안정" in botany_res["summary"]

    item_id = botany_res["created_item_id"]
    item = botany_forest_world.items[item_id]
    # 플레이어 눈에는 송이버섯으로 보이지만, 실제 스펙은 독우산광대버섯
    assert "자연산 송이버섯" in item.name
    assert item.true_spec_id == "destroying_angel"
    assert item.is_poisonous_lookalike is True
    assert item.is_identified is False
    assert "unidentified" in item.traits


def test_botany_identify_reveals_lookalike(botany_forest_world):
    """정밀 감별 성공 시 위장된 맹독 유사종의 정체 폭로 및 아이템 갱신 검증."""
    # 미감별 위장 송이버섯 인벤토리에 수동 준비
    fake_mushroom = Item(
        id="mimic_mushroom_1",
        name="야생에서 캔 자연산 송이버섯",
        description="희귀한 송이버섯처럼 보인다.",
        location="inventory",
        traits=["fungus", "unidentified", "botany_foraged"],
        true_spec_id="destroying_angel",
        is_identified=False,
        is_poisonous_lookalike=True,
        origin_target_name="자연산 송이버섯"
    )
    botany_forest_world.items["mimic_mushroom_1"] = fake_mushroom
    botany_forest_world.player.inventory.append("mimic_mushroom_1")

    # fixed_id_roll=20으로 정밀 감별 수행
    botany_res = TwoPassEngine.resolve_action_botany(
        "가방에 든 버섯 표본을 정밀 감별한다.", botany_forest_world, fixed_id_roll=20
    )

    assert botany_res is not None
    assert botany_res["type"] == "identify"
    assert botany_res["success"] is True
    assert "맹독 유사종" in botany_res["summary"]
    assert "독우산광대버섯" in botany_res["summary"]

    # 실제 아이템 상태 변경 확인
    assert fake_mushroom.is_identified is True
    assert "맹독 식물" in fake_mushroom.name
    assert "독우산광대버섯" in fake_mushroom.name
    assert "poison" in fake_mushroom.traits
    assert "unidentified" not in fake_mushroom.traits


def test_botany_consume_genuine_herb_heals(botany_forest_world):
    """진짜 약초(지혈 이끼) 섭취 시 체력 회복, 피로/허기 개선 및 인벤토리 소모 검증."""
    botany_forest_world.player.health = 20  # 부상 상태
    herb_item = Item(
        id="real_blood_moss",
        name="지혈 이끼",
        description="붉은빛 이끼",
        location="inventory",
        traits=["herb", "medicinal", "botany_foraged"],
        true_spec_id="blood_moss",
        is_identified=True,
        is_poisonous_lookalike=False
    )
    botany_forest_world.items["real_blood_moss"] = herb_item
    botany_forest_world.player.inventory.append("real_blood_moss")

    fact = TwoPassEngine.compute_pass1("가방에서 지혈 이끼를 꺼내 먹는다.", botany_forest_world)

    assert fact.is_valid is True
    assert fact.botany_summary is not None
    assert "지혈 이끼 복용" in fact.botany_summary
    assert "체력이 12 회복" in fact.botany_summary

    # 인벤토리에서 소모되어 사라졌는지 확인
    assert "real_blood_moss" not in botany_forest_world.player.inventory
    # 체력 회복 반영: 20 -> 32
    assert botany_forest_world.player.health == 32


def test_botany_consume_poisonous_lookalike_damages(botany_forest_world):
    """미감별 맹독 유사종 섭취 시 치명적 독성 피해(30) 및 중독 상태 격발 검증."""
    botany_forest_world.player.health = 45
    mimic_item = Item(
        id="deadly_angel_food",
        name="야생에서 캔 자연산 송이버섯",
        description="겉보기엔 맛있는 버섯",
        location="inventory",
        traits=["fungus", "botany_foraged"],
        true_spec_id="destroying_angel",
        is_identified=False,
        is_poisonous_lookalike=True
    )
    botany_forest_world.items["deadly_angel_food"] = mimic_item
    botany_forest_world.player.inventory.append("deadly_angel_food")

    fact = TwoPassEngine.compute_pass1("가방에 든 송이버섯을 씹어 먹는다.", botany_forest_world)

    assert fact.is_valid is True
    assert fact.botany_summary is not None
    assert "맹독 유사종 중독" in fact.botany_summary
    assert "독우산광대버섯" in fact.botany_summary

    # 소모 확인
    assert "deadly_angel_food" not in botany_forest_world.player.inventory
    # 30 피해 적용: 45 -> 15
    assert botany_forest_world.player.health == 15


def test_botany_validator_combat_and_indoor_prevention(botany_forest_world):
    """ActionValidator 사전 검증: 교전 중 채집 차단, 비식생 실내 채집 차단, 미소지 감별 차단."""
    # 1. 교전 중 채집 차단
    hostile_goblin = NPC(
        id="goblin_ambusher",
        name="숲 고블린",
        description="무기를 들고 날뛰는 약탈자",
        location="misty_forest",
        alive=True,
        disposition="hostile"
    )
    botany_forest_world.npcs["goblin_ambusher"] = hostile_goblin
    botany_forest_world.locations["misty_forest"].npcs.append("goblin_ambusher")

    valid, reason, _, _ = ActionValidator.pre_validate_action(
        "풀숲에서 약초를 채집한다.", botany_forest_world
    )
    assert valid is False
    assert "교전 중에는 약초나 식물을 한가롭게 채집할 수 없습니다" in reason

    # 고블린 처치 후 채집 가능
    hostile_goblin.alive = False
    valid_after, _, _, _ = ActionValidator.pre_validate_action(
        "풀숲에서 약초를 채집한다.", botany_forest_world
    )
    assert valid_after is True

    # 2. 비식생 실내(선술집) 채집 차단
    tavern_loc = Location(
        id="city_tavern",
        name="오크 머리통 주점",
        description="나무 바닥과 석조 벽으로 둘러싸인 실내 선술집이다.",
        exits={},
        items=[],
        traits=["tavern", "indoor"]
    )
    botany_forest_world.locations["city_tavern"] = tavern_loc
    botany_forest_world.player.location = "city_tavern"

    valid2, reason2, _, _ = ActionValidator.pre_validate_action(
        "약초 채집을 시도한다.", botany_forest_world
    )
    assert valid2 is False
    assert "실내에서는 야생 약초나 식물을 채집할 수 없습니다" in reason2

    # 3. 인벤토리에 감별할 식물이 없는데 감별 시도 -> 차단
    botany_forest_world.player.inventory.clear()
    valid3, reason3, _, _ = ActionValidator.pre_validate_action(
        "약초를 정밀 감별한다.", botany_forest_world
    )
    assert valid3 is False
    assert "소지품에 정밀 감별할 수 있는 야생 식물이나 약초 표본이 없습니다" in reason3
