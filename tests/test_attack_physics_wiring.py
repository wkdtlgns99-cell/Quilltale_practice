"""
Integration tests for attack_physics_engine.py wiring into TwoPassEngine.
Verifies thrust charge momentum, slash agility bleed, blunt strength bone fracture,
fast jab action interrupt, bow tension mechanics, and prompt context serialization.
"""
import pytest
from src.world.state import WorldState, Location, NPC, Item
from src.world.two_pass_engine import TwoPassEngine
from src.world.attack_physics_engine import AttackPhysicsEngine, AttackPhysicsResult


@pytest.fixture(autouse=True)
def fixed_dice_roll(monkeypatch):
    """Guarantees deterministic combat success during physics wiring tests."""
    monkeypatch.setattr("random.randint", lambda a, b: 18)


def setup_physics_combat_world():
    state = WorldState()
    loc = Location(
        id="combat_arena",
        name="투기장 훈련장",
        description="모래가 깔린 원형 투기장.",
        exits={},
        npcs=[],
        items=[]
    )
    state.locations["combat_arena"] = loc
    state.player.location = "combat_arena"
    state.player.strength = 10
    state.player.agility = 10

    # Target NPC
    target = NPC(
        id="training_dummy",
        name="오크 전사",
        description="단단한 근육과 가죽 갑옷을 입은 오크.",
        location="combat_arena",
        health=120,
        max_health=120,
        disposition="hostile"
    )
    target.poise = 10.0
    state.npcs["training_dummy"] = target
    loc.npcs.append("training_dummy")

    return state


def test_thrust_charge_momentum_and_armor_penetration():
    """5m 돌진 찌르기 시 가속도 운동에너지 피해 보너스 및 방어구 관통 검증."""
    state = setup_physics_combat_world()
    state.player.agility = 14  # High speed

    spear = Item(
        id="iron_spear_01",
        name="강철 장창",
        description="길고 예리한 강철 장창.",
        location="inventory",
        item_type="weapon",
        damage=15,
        physics_tags=["thrust"]
    )
    state.items["iron_spear_01"] = spear
    state.player.inventory.append("iron_spear_01")
    state.player.equipment.weapon = "iron_spear_01"

    action = "5m 거리를 전력으로 돌진하며 강철 장창으로 오크 전사의 가슴을 깊숙이 찌른다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid
    assert fact_sheet.attack_physics_summary is not None
    assert "돌진 가속 찌르기" in fact_sheet.attack_physics_summary
    assert "운동에너지" in fact_sheet.attack_physics_summary

    prompt_ctx = fact_sheet.to_prompt_context()
    assert "물리 공격 역학" in prompt_ctx


def test_slash_agility_bleed_infliction():
    """민첩 12 이상 참격 공격 시 적에게 출혈 상태이상 부여 검증."""
    state = setup_physics_combat_world()
    state.player.agility = 15  # >= 12 for bleed trigger

    sword = Item(
        id="steel_saber_01",
        name="강철 세이버",
        description="가볍고 날카로운 곡도.",
        location="inventory",
        item_type="weapon",
        damage=14,
        physics_tags=["slash", "blade"]
    )
    state.items["steel_saber_01"] = sword
    state.player.inventory.append("steel_saber_01")
    state.player.equipment.weapon = "steel_saber_01"

    action = "강철 세이버를 빠르게 휘둘러 오크 전사의 목덜미를 베어버린다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid
    assert fact_sheet.attack_physics_summary is not None
    assert "출혈" in fact_sheet.attack_physics_summary

    target = state.npcs["training_dummy"]
    assert "bleeding" in target.status_effects
    assert any("출혈" in log for log in fact_sheet.status_tick_logs)


def test_blunt_strength_bone_fracture():
    """근력 14 이상 둔기 타격 시 뼈 골절 위험 및 높은 피격 저지력 검증."""
    state = setup_physics_combat_world()
    state.player.strength = 16  # >= 14 for bone fracture

    hammer = Item(
        id="heavy_mace_01",
        name="육중한 흑철 메이스",
        description="두개골을 부수는 무거운 철퇴.",
        location="inventory",
        item_type="weapon",
        damage=16,
        stagger_power=15.0,
        physics_tags=["blunt", "strike"]
    )
    state.items["heavy_mace_01"] = hammer
    state.player.inventory.append("heavy_mace_01")
    state.player.equipment.weapon = "heavy_mace_01"

    action = "육중한 흑철 메이스로 오크 전사의 다리를 힘껏 내려친다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid
    assert fact_sheet.attack_physics_summary is not None
    assert "골절" in fact_sheet.attack_physics_summary

    target = state.npcs["training_dummy"]
    assert any("골절" in inj for inj in target.injuries)


def test_fast_jab_interrupts_enemy_action():
    """초고속 잽 견제타로 적의 영창/행동 즉각 불발 캔슬 검증."""
    state = setup_physics_combat_world()
    target = state.npcs["training_dummy"]
    target.current_intent = "주문 영창을 외우며 마력을 모은다"

    fist = Item(
        id="leather_cuff_01",
        name="가죽 권투 글러브",
        description="민첩한 잽 연타에 적합한 장갑.",
        location="inventory",
        item_type="weapon",
        damage=6,
        physics_tags=["jab"]
    )
    state.items["leather_cuff_01"] = fist
    state.player.inventory.append("leather_cuff_01")
    state.player.equipment.weapon = "leather_cuff_01"

    action = "가죽 권투 글러브로 번개 같은 잽을 찔러 오크 전사의 안면을 가격한다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid
    assert fact_sheet.attack_physics_summary is not None
    assert "캔슬" in fact_sheet.attack_physics_summary
    assert target.current_intent == ""  # Action cancelled


def test_bow_draw_strength_check_in_pass1():
    """근력 부족 시 활의 불완전 인장 판정 및 투사체 발사 검증."""
    state = setup_physics_combat_world()
    state.player.strength = 8  # Weak strength (max draw weight ~64 lbs)

    warbow = Item(
        id="heavy_warbow_01",
        name="120파운드 대궁",
        description="인간의 힘으로는 쉽게 당길 수 없는 거궁.",
        location="inventory",
        item_type="weapon",
        damage=20,
        draw_weight_lbs=120.0,
        physics_tags=["projectile"]
    )
    state.items["heavy_warbow_01"] = warbow
    state.player.inventory.append("heavy_warbow_01")
    state.player.equipment.weapon = "heavy_warbow_01"

    action = "120파운드 대궁에 화살을 걸어 오크 전사를 향해 활을 쏜다"
    fact_sheet = TwoPassEngine.compute_pass1(action, state)

    assert fact_sheet.is_valid
    assert fact_sheet.attack_physics_summary is not None
    assert "불완전 인장" in fact_sheet.attack_physics_summary


def test_attack_physics_prompt_context_serialization():
    """FactSheet 직렬화 및 프롬프트 서사 지침문 출력 검증."""
    state = setup_physics_combat_world()
    action = "강철 직검을 크게 휘둘러 오크 전사를 베어버린다"

    sword = Item(
        id="sword_basic_01",
        name="강철 직검",
        description="예리한 검.",
        location="inventory",
        item_type="weapon",
        damage=12,
        physics_tags=["slash"]
    )
    state.items["sword_basic_01"] = sword
    state.player.inventory.append("sword_basic_01")
    state.player.equipment.weapon = "sword_basic_01"

    fact_sheet = TwoPassEngine.compute_pass1(action, state)
    prompt_ctx = fact_sheet.to_prompt_context()

    assert "⚔️ [물리 공격 역학 및 피격 반응 (Attack Physics & Stagger)]" in prompt_ctx
    assert "GM 서사 지침" in prompt_ctx
