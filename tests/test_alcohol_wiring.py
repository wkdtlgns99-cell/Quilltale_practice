"""
Integration tests for AlcoholIntoxicationEngine wiring into TwoPassEngine, WorldState, and ActionValidator.
Verifies alcohol consumption (tavern vs inventory), BAC metabolism ticks, intoxication stages,
deterministic stat debuffs/buffs, blackout companion escort vs solo theft, and morning hangovers.
"""
import pytest
from src.world.state import WorldState, Player, NPC, Location, Item
from src.world.two_pass_engine import TwoPassEngine
from src.world.alcohol_engine import AlcoholIntoxicationEngine
from src.world.validator import ActionValidator


@pytest.fixture
def base_tavern_world():
    state = WorldState()
    loc = Location(
        id="boar_tavern",
        name="달리는 멧돼지 선술집",
        description="시끌벅적하고 왁자지껄한 주점이다. 맥주 거품과 고기 굽는 냄새가 진동한다.",
        exits={},
        items=[],
        traits=["tavern", "indoor"]
    )
    state.locations["boar_tavern"] = loc
    state.player = Player(
        name="모험가 카엘",
        location="boar_tavern",
        gold=20,
        health=50,
        max_health=100,
        mana=40,
        max_mana=60,
        fatigue=30,
        strength=12,
        agility=14,
        intelligence=12,
        perception=14,
        inventory=[],
        body_temperature=36.5,
        wetness=0.0
    )
    return state


def test_alcohol_metabolism_tick_and_pass1_status(base_tavern_world):
    """체내 알코올 자연 대사 틱 및 Pass 1 상태 틱 결합 검증."""
    player = base_tavern_world.player
    alc_state = AlcoholIntoxicationEngine.get_state(player)
    alc_state.blood_alcohol_content = 0.04
    alc_state.intoxication_stage = 1
    AlcoholIntoxicationEngine.sync_state(player, alc_state)

    # 1. Standalone metabolism tick: 20 minutes -> BAC -0.005 -> 0.035 (stage 1 kept)
    _ = AlcoholIntoxicationEngine.tick_metabolism(player, delta_minutes=20)
    cur_alc = AlcoholIntoxicationEngine.get_state(player)
    assert cur_alc.blood_alcohol_content == 0.035

    # 2. Further decay: 40 minutes -> BAC -0.010 -> 0.025 (stage drops to 0)
    logs2 = AlcoholIntoxicationEngine.tick_metabolism(player, delta_minutes=40)
    cur_alc2 = AlcoholIntoxicationEngine.get_state(player)
    assert cur_alc2.blood_alcohol_content == 0.025
    assert cur_alc2.intoxication_stage == 0
    assert any("체내 알코올이 대사되어" in l for l in logs2)

    # 3. TwoPassEngine compute_pass1 natural tick
    fact = TwoPassEngine.compute_pass1("주변을 둘러본다.", base_tavern_world)
    assert fact.is_valid is True
    # In turn loop, another 30 mins elapsed -> BAC decays further
    cur_alc3 = AlcoholIntoxicationEngine.get_state(player)
    assert cur_alc3.blood_alcohol_content < 0.025


def test_alcohol_deterministic_readers_and_deserialization(base_tavern_world):
    """결정론적 리더(스탯/방어력 보정) 및 직렬화/역직렬화/델타 동기화 검증."""
    player = base_tavern_world.player
    base_agi = player.effective_agility
    base_ac = player.armor_class
    base_int = player.effective_intelligence
    base_per = player.effective_perception

    # 2단계 만취 상태 설정: 민첩 -3, 고통 둔화 방어력 +2
    alc_state = AlcoholIntoxicationEngine.get_state(player)
    alc_state.intoxication_stage = 2
    alc_state.blood_alcohol_content = 0.12
    AlcoholIntoxicationEngine.sync_state(player, alc_state)

    assert player.effective_agility == base_agi - 3
    # 고통 둔화 방어력(+2)이 민첩 저하로 인한 agi_mod 감소(2 -> 0)를 보전하여 AC 12 유지 (미적용 시 10으로 추락)
    assert player.armor_class == player.base_armor_class + player.agi_mod + 2
    assert player.armor_class == base_ac  # Numbness bonus offsets agi penalty, preserving AC at 12

    # 익일 숙취 상태 설정: 지능 -2, 감각 -2
    alc_state.intoxication_stage = 0
    alc_state.has_hangover = True
    alc_state.hangover_hours_remaining = 4
    AlcoholIntoxicationEngine.sync_state(player, alc_state)

    assert player.effective_intelligence == base_int - 2
    assert player.effective_perception == base_per - 2

    # 직렬화 및 역직렬화 검증
    raw = base_tavern_world.to_dict()
    restored = WorldState.from_dict(raw)
    restored_alc = restored.player.alcohol_state
    assert restored_alc.get("has_hangover") is True
    assert restored.player.effective_intelligence == base_int - 2

    # apply_update 동기화 검증
    base_tavern_world.apply_update({
        "player": {
            "alcohol_state": {
                "blood_alcohol_content": 0.0,
                "intoxication_stage": 0,
                "has_hangover": False,
                "hangover_hours_remaining": 0
            }
        }
    })
    assert base_tavern_world.player.alcohol_state["has_hangover"] is False
    assert base_tavern_world.player.effective_intelligence == base_int


def test_alcohol_action_validator(base_tavern_world):
    """ActionValidator 사전 검증: 선술집 유무, 골드 부족, 소지품 유무, 블랙아웃 차단."""
    # 1. 비선술집 야외에서 주류 소지 없이 술 마시기 시도 -> 거부
    wild_loc = Location(id="wild_plains", name="황량한 벌판", description="아무것도 없는 들판이다.", exits={}, items=[])
    base_tavern_world.locations["wild_plains"] = wild_loc
    base_tavern_world.player.location = "wild_plains"

    valid, reason, _, _ = ActionValidator.pre_validate_action(
        "가방에서 맥주를 꺼내 마신다.", base_tavern_world
    )
    assert valid is False
    assert "보유 중인 주류가 없습니다" in reason

    valid2, reason2, _, _ = ActionValidator.pre_validate_action(
        "시원한 술 한 잔 마신다.", base_tavern_world
    )
    assert valid2 is False
    assert "선술집이나 주점이 아닙니다" in reason2

    # 2. 선술집 복귀 후 골드 0원 시도 -> 거부
    base_tavern_world.player.location = "boar_tavern"
    base_tavern_world.player.gold = 0
    valid3, reason3, _, _ = ActionValidator.pre_validate_action(
        "주점에서 시원한 보리 에일 한 잔을 주문해 마신다.", base_tavern_world
    )
    assert valid3 is False
    assert "소지금 부족" in reason3

    # 3. 3단계 블랙아웃 상태에서 추가 주문 -> 거부
    base_tavern_world.player.gold = 50
    alc_state = AlcoholIntoxicationEngine.get_state(base_tavern_world.player)
    alc_state.intoxication_stage = 3
    AlcoholIntoxicationEngine.sync_state(base_tavern_world.player, alc_state)

    valid4, reason4, _, _ = ActionValidator.pre_validate_action(
        "술을 더 마신다.", base_tavern_world
    )
    assert valid4 is False
    assert "인사불성" in reason4


def test_alcohol_consumption_tavern_and_inventory(base_tavern_world):
    """선술집 구매 음용 vs 가방 소지품 음용 TwoPassEngine 결합 검증."""
    # 1. 선술집에서 골드로 에일(1골드) 구매 음용
    init_gold = base_tavern_world.player.gold
    init_fatigue = base_tavern_world.player.fatigue

    fact = TwoPassEngine.compute_pass1("시원한 보리 에일 한 잔을 들이킨다.", base_tavern_world)

    assert fact.is_valid is True
    assert fact.alcohol_summary is not None
    assert "구수한 보리 에일 한 잔" in fact.alcohol_summary
    assert "🍺 [주류 음용 및 취기/숙취/실신 판정" in fact.to_prompt_context()
    assert base_tavern_world.player.gold == init_gold - 1
    assert base_tavern_world.player.fatigue < init_fatigue
    alc = AlcoholIntoxicationEngine.get_state(base_tavern_world.player)
    assert alc.blood_alcohol_content >= 0.025

    # 2. 인벤토리에 와인 소지 후 무료 음용 (골드 소모 없음, 아이템 제거)
    wine_item = Item(id="spiced_wine", name="향신료 따뜻한 뱅쇼", description="따뜻한 포도주", location="inventory", traits=["alcohol", "wine"])
    base_tavern_world.items["spiced_wine"] = wine_item
    base_tavern_world.player.inventory.append("spiced_wine")
    gold_before = base_tavern_world.player.gold

    fact2 = TwoPassEngine.compute_pass1("가방에서 향신료 따뜻한 뱅쇼를 꺼내 마신다.", base_tavern_world)

    assert fact2.is_valid is True
    assert "spiced_wine" not in base_tavern_world.player.inventory
    assert base_tavern_world.player.gold == gold_before  # 인벤토리 주류는 골드 미차감
    alc2 = AlcoholIntoxicationEngine.get_state(base_tavern_world.player)
    assert alc2.blood_alcohol_content >= 0.08  # 0.03 + 0.06 - decay >= 0.08 (2단계 만취 진입)
    assert alc2.intoxication_stage == 2


def test_blackout_solo_vs_companion(base_tavern_world):
    """User Decision Q3: 3단계 만취 블랙아웃 시 동료 호송 vs 단독 소매치기/저체온증 검증."""
    # 1. 단독 상태에서 독주 폭음 -> 블랙아웃 및 소매치기/저체온증
    base_tavern_world.player.gold = 100
    base_tavern_world.player.body_temperature = 36.5
    base_tavern_world.player.wetness = 0.0

    # BAC를 0.18로 미리 올려둔 상태에서 드워프 불꽃 증류주(+0.15 BAC) 음용 -> BAC 0.30+ 블랙아웃 확정
    alc = AlcoholIntoxicationEngine.get_state(base_tavern_world.player)
    alc.blood_alcohol_content = 0.18
    AlcoholIntoxicationEngine.sync_state(base_tavern_world.player, alc)

    # fixed_theft_roll=30 (<= 60% 소매치기 격발)
    drink_res = TwoPassEngine.resolve_action_drink("드워프 불꽃 증류주를 단숨에 들이킨다.", base_tavern_world, fixed_theft_roll=30)
    assert drink_res is not None
    assert drink_res["blackout"] is True
    assert drink_res["stage"] == 3
    assert base_tavern_world.player.gold < 100 - 8  # 8골드 술값 + 소매치기 30% 털림
    assert base_tavern_world.player.body_temperature < 36.5
    assert base_tavern_world.player.wetness > 0.0

    # 2. 동료 동행 상태에서 블랙아웃 -> 안전 호송 (소매치기/저체온증 면제)
    companion = NPC(
        id="friendly_paladin",
        name="성기사 가레스",
        description="믿음직한 전우",
        location="boar_tavern",
        affinity=90,
        alive=True,
        disposition="friendly"
    )
    base_tavern_world.npcs["friendly_paladin"] = companion
    base_tavern_world.player.gold = 100
    base_tavern_world.player.body_temperature = 36.5
    base_tavern_world.player.wetness = 0.0

    alc.blood_alcohol_content = 0.18
    alc.intoxication_stage = 2
    AlcoholIntoxicationEngine.sync_state(base_tavern_world.player, alc)

    drink_res2 = TwoPassEngine.resolve_action_drink("드워프 불꽃 증류주를 또 들이킨다.", base_tavern_world, fixed_theft_roll=30)
    assert drink_res2["blackout"] is True
    assert "동료의 든든한 호송" in drink_res2["summary"]
    assert "성기사 가레스" in drink_res2["summary"]
    assert base_tavern_world.player.gold == 100 - 8  # 술값 8골드만 차감, 소매치기 0
    assert base_tavern_world.player.wetness == 0.0


def test_campsite_peaceful_sleep_hangover_and_recovery(base_tavern_world):
    """만취 후 야영 숙면 시 숙취 발생 및 지능/감각 디버프, 시간 경과 해소 검증."""
    player = base_tavern_world.player
    alc = AlcoholIntoxicationEngine.get_state(player)
    alc.blood_alcohol_content = 0.15
    alc.intoxication_stage = 2
    AlcoholIntoxicationEngine.sync_state(player, alc)

    # 8시간 야영 숙면 시뮬레이션
    hangover_logs = AlcoholIntoxicationEngine.process_morning_hangover(player, hours_slept=8)
    cur_alc = AlcoholIntoxicationEngine.get_state(player)

    assert cur_alc.blood_alcohol_content == 0.0
    assert cur_alc.intoxication_stage == 0
    assert cur_alc.has_hangover is True
    assert cur_alc.hangover_hours_remaining == 4
    assert any("극심한 숙취 발생" in l for l in hangover_logs)

    # 디버프 적용 확인 (지능 -2, 감각 -2)
    assert player.effective_intelligence == 10  # 12 - 2
    assert player.effective_perception == 12    # 14 - 2

    # 시간 대사로 숙취 카운트다운 (4시간 경과 후 해소)
    AlcoholIntoxicationEngine.tick_metabolism(player, delta_minutes=240)
    cleared_alc = AlcoholIntoxicationEngine.get_state(player)

    assert cleared_alc.has_hangover is False
    assert cleared_alc.hangover_hours_remaining == 0
    assert player.effective_intelligence == 12  # 정상 복구
    assert player.effective_perception == 14
