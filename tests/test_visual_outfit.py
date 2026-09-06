"""
Unit tests for 5-Layer Clothing Visual System and TRPG Gear Mechanics.
Validates:
1. ClothingLayer Korean summary & AI image prompt generation.
2. EquipmentSlots extension (neck, belt, shoulders, storage, innerwear, bracelets).
3. EquipmentEngine integration across all 15 slots.
4. OutfitMechanicsEngine:
   - Backpack carry weight expansion and encumbrance penalties.
   - Thigh pouch / belt pouch quick-slots.
   - Quiver zero-delay arrow drawing vs without-quiver reload penalties.
   - Scabbard quick-draw surprise critical strikes (+30% crit damage, +10% crit rate).
   - Gambeson plate armor chafing prevention & 10% blunt shock absorption.
   - Stealth tights acoustic noise reduction (-6dB).
   - Monocle/glasses appraisal check bonus (+25%) & eyewear shatter hazard upon facial critical hits.
5. Two-way synchronization between EquipmentSlots and ClothingLayer.
6. Backwards compatibility with old JSON save states.
"""
import pytest
from src.world.state import (
    WorldState, Player, NPC, Item, Location, EquipmentSlots, ClothingLayer, NPCVisualDetails
)
from src.world.equipment import EquipmentEngine
from src.world.outfit_engine import (
    OutfitMechanicsEngine, EncumbranceStatus, ArmorChafingResult, QuickDrawResult, EyewearHazardResult
)


def create_test_state() -> WorldState:
    state = WorldState()
    state.locations["crossroads"] = Location(
        id="crossroads",
        name="갈림길",
        description="인적이 드문 황량한 흙길 갈림길.",
        exits={},
        items=[],
        npcs=[]
    )
    state.player.location = "crossroads"
    return state


def test_clothing_layer_korean_summary_and_prompt_keywords():
    """Validates 5-layer ClothingLayer Korean summary and AI image keywords."""
    outfit = ClothingLayer(
        head_face=["황동 단안경", "은빛 서클릿"],
        neck_acc=["청금석 호신 부적"],
        arms_wrists=["가죽 완갑", "회중시계"],
        ankle_legs=["강철 각반"],
        innerwear=["누비 갬비슨", "은신 타이즈"],
        base_upper="리넨 셔츠",
        base_lower="질긴 여행자 바지",
        waist_layer="가죽 전술 하네스 및 탄띠",
        outerwear="칠흑빛 마법사 로브",
        shoulders="회색 늑대 모피 숄",
        cape_back="낡은 여행자 숏망토",
        footwear="단단한 가죽 군화",
        socks_stockings="두꺼운 양모 양말",
        bags_storage=["모험가 대형 배낭", "허벅지 파우치"],
        weapon_mounts=["룬 은장도 칼집", "가죽 화살통"]
    )

    ko_summary = outfit.to_korean_summary()
    assert "겉옷: 칠흑빛 마법사 로브" in ko_summary
    assert "이너: 누비 갬비슨, 은신 타이즈" in ko_summary
    assert "어깨: 회색 늑대 모피 숄" in ko_summary
    assert "머리/안면: 황동 단안경, 은빛 서클릿" in ko_summary
    assert "수납: 모험가 대형 배낭, 허벅지 파우치" in ko_summary
    assert "거치: 룬 은장도 칼집, 가죽 화살통" in ko_summary

    prompt_en = outfit.to_prompt_keywords()
    assert "wearing 칠흑빛 마법사 로브" in prompt_en
    assert "회색 늑대 모피 숄 on shoulders" in prompt_en
    assert "carrying 모험가 대형 배낭, 허벅지 파우치" in prompt_en
    assert "equipped with 룬 은장도 칼집, 가죽 화살통" in prompt_en


def test_npc_and_player_visual_outfit_integration():
    """Validates NPC and Player visual outfit properties and methods."""
    state = create_test_state()
    npc = NPC(
        id="elena",
        name="엘레나",
        description="민첩한 정찰병",
        location="crossroads",
        job="정찰병",
        visual=NPCVisualDetails(
            species="엘프",
            life_stage="청년",
            age_apparent="20대 초반",
            hair_color="백금발",
            hair_style="포니테일",
            eye_color="비취색",
            eye_shape="날렵한 눈매",
            outfit=ClothingLayer(
                outerwear="숲의 정찰 가죽 조끼",
                cape_back="위장용 녹색 판초",
                head_face=["가죽 안대"],
                weapon_mounts=["사냥활 및 화살통"]
            )
        )
    )

    npc_prompt = npc.to_image_prompt_keywords()
    assert "엘프" in npc_prompt
    assert "정찰병" in npc_prompt
    assert "wearing 숲의 정찰 가죽 조끼" in npc_prompt

    npc_summary = npc.to_korean_visual_summary()
    assert "엘레나" not in npc_summary  # Format is [엘프 청년 / 정찰병] ...
    assert "위장용 녹색 판초" in npc_summary

    # Player visual integration
    state.player.name = "로웰"
    state.player.visual.outfit.outerwear = "검은 코트"
    state.player.visual.outfit.weapon_mounts = ["강철검 칼집"]
    p_summary = state.player.to_korean_visual_summary()
    assert "로웰" in p_summary
    assert "검은 코트" in p_summary


def test_equipment_slots_extension_and_bonuses():
    """Validates new equipment slots (neck, belt, shoulders, storage, innerwear, bracelets) and stat calculations."""
    state = create_test_state()

    # Create items for new slots
    items = [
        Item(id="amulet_1", name="마나 펜던트", description="지능을 높여주는 목걸이", location="inventory", defense=1, properties={"stat_bonuses": {"intelligence": 3}}),
        Item(id="belt_1", name="용병의 가죽 벨트", description="허리를 단단히 받치는 벨트", location="inventory", defense=2, properties={"stat_bonuses": {"strength": 2}}),
        Item(id="shoulders_1", name="강철 견갑", description="어깨를 감싸는 강철 방어구", location="inventory", defense=4, properties={"stat_bonuses": {"constitution": 2}}),
        Item(id="storage_1", name="대형 여행자 백팩", description="소지 무게를 크게 늘려주는 배낭", location="inventory", defense=0, properties={"carry_capacity_bonus": 30.0}),
        Item(id="innerwear_1", name="두꺼운 갬비슨", description="판금 갑옷의 충격을 완화하는 누비옷", location="inventory", defense=3, properties={"stat_bonuses": {"constitution": 1}}),
        Item(id="bracelet_1", name="질풍의 은팔찌", description="민첩성을 높여주는 팔찌", location="inventory", defense=1, properties={"stat_bonuses": {"agility": 2}}),
    ]
    for it in items:
        state.items[it.id] = it
        state.player.inventory.append(it.id)

    # Equip items via apply_update
    state.apply_update({
        "equip_slot": {"item_id": "amulet_1", "slot": "neck"}
    })
    state.apply_update({
        "equip_slot": {"item_id": "belt_1", "slot": "belt"}
    })
    state.apply_update({
        "equip_slot": {"item_id": "shoulders_1", "slot": "shoulders"}
    })
    state.apply_update({
        "equip_slot": {"item_id": "storage_1", "slot": "storage"}
    })
    state.apply_update({
        "equip_slot": {"item_id": "innerwear_1", "slot": "innerwear"}
    })
    state.apply_update({
        "equip_slot": {"item_id": "bracelet_1", "slot": "bracelet"}
    })

    assert state.player.equipment.neck == "amulet_1"
    assert state.player.equipment.belt == "belt_1"
    assert state.player.equipment.shoulders == "shoulders_1"
    assert state.player.equipment.storage == "storage_1"
    assert state.player.equipment.innerwear == "innerwear_1"
    assert "bracelet_1" in state.player.equipment.bracelets

    # Calculate equipment bonuses
    bonuses = EquipmentEngine.calculate_equipment_bonuses(state, state.player)
    # Total defense: 1 + 2 + 4 + 0 + 3 + 1 = 11
    assert bonuses["total_defense"] == 11
    # Stat bonuses: INT +3, STR +2, CON +3 (2+1), AGI +2
    assert bonuses["stat_bonuses"]["intelligence"] == 3
    assert bonuses["stat_bonuses"]["strength"] == 2
    assert bonuses["stat_bonuses"]["constitution"] == 3
    assert bonuses["stat_bonuses"]["agility"] == 2

    # Unequip bracelet
    state.apply_update({
        "unequip_slot": {"item_id": "bracelet_1", "slot": "bracelet"}
    })
    assert "bracelet_1" not in state.player.equipment.bracelets


def test_storage_gear_and_carrying_capacity():
    """Validates carry capacity expansion from backpacks and encumbrance tiers."""
    state = create_test_state()
    state.player.strength = 10  # Base capacity = 20 + (10-10)*3 = 20kg

    # Without backpack
    total_cap, base_cap, bag_bonus = OutfitMechanicsEngine.calculate_carry_capacity(state.player, state)
    assert base_cap == 20.0
    assert bag_bonus == 0.0
    assert total_cap == 20.0

    # Equip backpack with +25kg bonus
    backpack = Item(
        id="backpack_adventurer",
        name="모험가 배낭",
        description="수납력 우수한 가죽 배낭",
        location="inventory",
        weight=2.0,
        properties={"carry_capacity_bonus": 25.0}
    )
    state.items[backpack.id] = backpack
    state.player.inventory.append(backpack.id)
    state.player.equipment.storage = backpack.id

    total_cap, base_cap, bag_bonus = OutfitMechanicsEngine.calculate_carry_capacity(state.player, state)
    assert base_cap == 20.0
    assert bag_bonus == 25.0
    assert total_cap == 45.0

    # Add heavy iron bars to test encumbrance
    iron_ingot = Item(id="iron_bar", name="강철 주괴", description="묵직한 주괴", location="inventory", weight=10.0)
    state.items[iron_ingot.id] = iron_ingot
    state.player.inventory.extend(["iron_bar", "iron_bar"])  # Total weight: 2.0 (backpack) + 20.0 = 22.0kg

    status = OutfitMechanicsEngine.evaluate_encumbrance(state.player, state)
    assert status.status_level == "light" or status.status_level == "normal"
    assert status.can_sprint is True

    # Overburden the player (> 130% of 45kg = 58.5kg)
    for i in range(4):
        state.player.inventory.append("iron_bar")
    # Total weight: 2 + 60 = 62kg (62 / 45 = 1.37 > 1.3)
    status_heavy = OutfitMechanicsEngine.evaluate_encumbrance(state.player, state)
    assert status_heavy.status_level == "overburdened"
    assert status_heavy.speed_penalty_mps == 3.0
    assert status_heavy.can_sprint is False
    assert status_heavy.fatigue_multiplier == 2.5


def test_quick_slots_mechanic():
    """Validates belt and thigh pouch quick-slot capabilities."""
    state = create_test_state()
    qs_before = OutfitMechanicsEngine.get_quick_slots(state.player, state)
    assert qs_before["has_quick_slots"] is False

    # Equip belt with quick slots
    belt = Item(
        id="tactical_belt",
        name="전술 탄띠 및 파우치",
        description="소모품을 신속히 꺼낼 수 있는 전술 벨트",
        location="inventory",
        properties={"quick_slots": 3}
    )
    state.items[belt.id] = belt
    state.player.equipment.belt = belt.id

    qs_after = OutfitMechanicsEngine.get_quick_slots(state.player, state)
    assert qs_after["has_quick_slots"] is True
    assert qs_after["quick_slot_capacity"] == 3
    assert "전술 탄띠 및 파우치" in qs_after["sources"]


def test_quiver_draw_delay_mechanic():
    """Validates projectile draw delay: 0.0s with quiver, +0.5s without quiver."""
    state = create_test_state()

    # Without quiver
    delay, msg = OutfitMechanicsEngine.calculate_projectile_draw_delay(state.player, state)
    assert delay == 0.5
    assert "미장착" in msg

    # With quiver in storage
    quiver = Item(
        id="leather_quiver",
        name="가죽 화살통",
        description="등이나 허리에 매는 화살통",
        location="inventory"
    )
    state.items[quiver.id] = quiver
    state.player.equipment.storage = quiver.id

    delay_with, msg_with = OutfitMechanicsEngine.calculate_projectile_draw_delay(state.player, state)
    assert delay_with == 0.0
    assert "화살 즉시 발사" in msg_with


def test_scabbard_quick_draw_critical_strike():
    """Validates opening turn quick-draw critical strike bonus (+30% crit dmg, +10% crit rate)."""
    state = create_test_state()

    # No scabbard
    res_no = OutfitMechanicsEngine.calculate_quick_draw_attack(state.player, state, is_opening_turn=True)
    assert res_no.eligible is False

    # Equip scabbard in belt
    scabbard = Item(
        id="fine_scabbard",
        name="명장의 흑철 칼집",
        description="발도를 매끄럽게 보조하는 명품 칼집",
        location="inventory"
    )
    state.items[scabbard.id] = scabbard
    state.player.equipment.belt = scabbard.id

    res_yes = OutfitMechanicsEngine.calculate_quick_draw_attack(state.player, state, is_opening_turn=True)
    assert res_yes.eligible is True
    assert res_yes.crit_damage_bonus_pct == 30.0
    assert res_yes.crit_rate_bonus_pct == 10.0
    assert "발도술" in res_yes.summary_ko


def test_gambeson_armor_chafing_prevention():
    """Validates plate armor chafing debuff without gambeson, and 10% blunt mitigation with gambeson."""
    state = create_test_state()

    # Plate armor without innerwear
    plate = Item(
        id="full_plate",
        name="강철 판금 흉갑",
        description="단단한 전신 판금 갑옷",
        location="inventory",
        defense=12
    )
    state.items[plate.id] = plate
    state.player.equipment.chest = plate.id

    res_chafing = OutfitMechanicsEngine.check_armor_chafing(state.player, state)
    assert res_chafing.has_chafing is True
    assert res_chafing.penalty_active is True
    assert "피부 직착용" in res_chafing.summary_ko

    # Equip gambeson innerwear
    gambeson = Item(
        id="thick_gambeson",
        name="누비 갬비슨",
        description="두꺼운 양모로 누빈 방호 이너웨어",
        location="inventory",
        defense=3
    )
    state.items[gambeson.id] = gambeson
    state.player.equipment.innerwear = gambeson.id

    res_cushioned = OutfitMechanicsEngine.check_armor_chafing(state.player, state)
    assert res_cushioned.has_chafing is False
    assert res_cushioned.penalty_active is False
    assert res_cushioned.blunt_mitigation_pct == 10.0
    assert "완충 효과" in res_cushioned.summary_ko


def test_stealth_tights_noise_reduction():
    """Validates acoustic footstep noise reduction from stealth tights (-6dB)."""
    state = create_test_state()
    noise_no = OutfitMechanicsEngine.calculate_clothing_noise_reduction(state.player, state)
    assert noise_no == 0.0

    tights = Item(
        id="stealth_tights",
        name="그림자 은신 타이즈",
        description="마찰음을 극도로 억제한 특수 직조 타이즈",
        location="inventory"
    )
    state.items[tights.id] = tights
    state.player.equipment.innerwear = tights.id

    noise_red = OutfitMechanicsEngine.calculate_clothing_noise_reduction(state.player, state)
    assert noise_red == 6.0


def test_eyewear_appraisal_bonus_and_breakage_hazard():
    """Validates monocle appraisal bonus (+25%) and facial impact glass shatter hazard."""
    state = create_test_state()

    # Appraisal check without glasses
    bonus, msg = OutfitMechanicsEngine.calculate_eyewear_appraisal_bonus(state.player, state)
    assert bonus == 0

    # Equip monocle
    monocle = Item(
        id="scholar_monocle",
        name="학자의 황동 단안경",
        description="세밀한 각인과 보석의 진위를 감정하는 단안경",
        location="inventory",
        durability=100
    )
    state.items[monocle.id] = monocle
    state.player.equipment.face = monocle.id

    bonus_with, msg_with = OutfitMechanicsEngine.calculate_eyewear_appraisal_bonus(state.player, state)
    assert bonus_with == 25
    assert "가치 감정 성공률 +25%" in msg_with

    # Non-face hit: no hazard
    res_chest = OutfitMechanicsEngine.evaluate_eyewear_damage(state.player, state, target_part="chest")
    assert res_chest.is_shattered is False

    # Facial critical hit: shatter hazard triggers
    res_face_crit = OutfitMechanicsEngine.evaluate_eyewear_damage(
        state.player, state, target_part="얼굴", is_critical=True
    )
    assert res_face_crit.is_shattered is True
    assert "유리 파편 실명 위험" in res_face_crit.debuff_applied
    assert state.items["scholar_monocle"].durability == 0


def test_sync_equipment_to_clothing_layer():
    """Validates automatic synchronization from EquipmentSlots into 5-layer ClothingLayer."""
    state = create_test_state()

    items = [
        Item(id="helm", name="기사단 투구", description="", location="inventory"),
        Item(id="armor", name="흑철 판금갑", description="", location="inventory"),
        Item(id="pants", name="사슬 보강 바지", description="", location="inventory"),
        Item(id="boots", name="강철 군화", description="", location="inventory"),
        Item(id="cloak", name="진홍빛 망토", description="", location="inventory"),
        Item(id="sword", name="은빛 장검", description="", location="inventory"),
    ]
    for it in items:
        state.items[it.id] = it
    state.player.equipment.head = "helm"
    state.player.equipment.chest = "armor"
    state.player.equipment.legs = "pants"
    state.player.equipment.boots = "boots"
    state.player.equipment.cape = "cloak"
    state.player.equipment.weapon = "sword"

    outfit = OutfitMechanicsEngine.sync_equipment_to_clothing_layer(state.player, state)
    assert "기사단 투구" in outfit.head_face
    assert outfit.outerwear == "흑철 판금갑"
    assert outfit.base_lower == "사슬 보강 바지"
    assert outfit.footwear == "강철 군화"
    assert outfit.cape_back == "진홍빛 망토"
    assert any("은빛 장검 칼집" in wm for wm in outfit.weapon_mounts)


def test_backwards_compatibility_save_load():
    """Validates that older JSON save states without outfit/visual load 100% seamlessly."""
    legacy_json = {
        "world_name": "고대 왕국",
        "player": {
            "name": "방랑자 카일",
            "health": 80,
            "max_health": 100,
            "equipment": {
                "weapon": "old_sword",
                "chest": "old_cloth"
            }
        },
        "locations": {
            "start": {"id": "start", "name": "여관"}
        },
        "npcs": {
            "barkeep": {
                "id": "barkeep",
                "name": "주모",
                "job": "여관주인"
            }
        }
    }

    state = WorldState.from_dict(legacy_json)
    assert state.player.name == "방랑자 카일"
    assert state.player.equipment.weapon == "old_sword"
    assert state.player.equipment.neck is None
    assert state.player.equipment.storage is None
    assert state.player.equipment.bracelets == []
    assert hasattr(state.player, "visual")
    assert hasattr(state.player.visual, "outfit")
    assert state.player.visual.outfit.traits is not None
    assert "barkeep" in state.npcs
    assert hasattr(state.npcs["barkeep"].visual, "outfit")
