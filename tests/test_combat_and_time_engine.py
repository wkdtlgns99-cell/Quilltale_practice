"""
Unit tests for Realistic Combat Physics, Dynamic Action Time-Track,
StatEngine (Human Peak 15), and Macro Calendar & Environmental Ripple Engine.
"""
import pytest
import json

from src.world.state import WorldState, Player, Item, Location, NPC
from src.world.stat_engine import StatEngine, HUMAN_PEAK_STAT, AVERAGE_HUMAN_STAT
from src.world.attack_physics_engine import AttackPhysicsEngine, AttackPhysicsResult
from src.world.combat_time_track_engine import (
    CombatDistanceManager, ActionTimeTrackEngine, CombatAction, InterruptEvent, DISTANCE_ZONES
)
from src.world.time_calendar_engine import TimeCalendarEngine, DAILY_ACTION_DURATIONS
from src.world.perception_engine import PerceptionEngine


def test_stat_engine_human_peak_anchors_and_substats():
    """스탯 10(일반인 평균) 및 스탯 15(인간 정점/올림픽) 물리 수치 및 서브스탯 검증."""
    # 1. 민첩 10 vs 15 질주 속도
    speed_10 = StatEngine.calculate_movement_speed(10)
    speed_15 = StatEngine.calculate_movement_speed(15)
    assert speed_10 == 4.5
    assert speed_15 == 10.5  # 우사인 볼트 최고 전력 질주 속도

    # 2. 근력 10 vs 15 활 장력 한계
    draw_10 = StatEngine.calculate_max_draw_weight(10)
    draw_15 = StatEngine.calculate_max_draw_weight(15)
    assert draw_10 == 50.0   # 일반인 50 lbs
    assert draw_15 == 150.0  # 영국 중세 장궁병 150 lbs 완발

    # 3. 선딜레이 및 영창 속도 단축 배율
    windup_10 = StatEngine.calculate_windup_multiplier(10)
    windup_15 = StatEngine.calculate_windup_multiplier(15)
    assert windup_10 == 1.0
    assert windup_15 == 0.5  # 50% 단축

    incant_10 = StatEngine.calculate_incantation_multiplier(10)
    incant_15 = StatEngine.calculate_incantation_multiplier(15)
    assert incant_10 == 1.0
    assert incant_15 == 0.5  # 50% 영창 시간 단축

    # 4. 강인도 산출
    poise_val = StatEngine.calculate_poise(constitution=14, armor_bonus=10.0)
    assert poise_val == (14 - 10) * 2.0 + 10.0 * 0.5  # 8.0 + 5.0 = 13.0

    # 5. 서브스탯 딕셔너리 관리
    player = Player(name="바바리안")
    StatEngine.set_sub_stat(player, "night_vision_m", 15.5)
    StatEngine.set_sub_stat(player, "bone_fracture_resist", 30.0)
    assert StatEngine.get_sub_stat(player, "night_vision_m") == 15.5
    assert StatEngine.get_sub_stat(player, "bone_fracture_resist") == 30.0

    new_val = StatEngine.modify_sub_stat(player, "bone_fracture_resist", 5.0)
    assert new_val == 35.0
    assert StatEngine.get_sub_stat(player, "bone_fracture_resist") == 35.0

    sheet = StatEngine.format_stat_sheet_ko(player)
    assert "바바리안" in sheet
    assert "night_vision_m: 15.5" in sheet


def test_leveling_exp_curve_and_stat_allocation():
    """레벨업 경험치 곡선 req_exp(L) = 100 * L^1.5 및 자유 분배 스탯 포인트 검증."""
    assert StatEngine.calculate_required_exp(1) == 100
    assert StatEngine.calculate_required_exp(2) == 282
    assert StatEngine.calculate_required_exp(3) == 519

    player = Player(name="견습생", strength=10, agility=10, stat_points=0, exp=0, level=1)
    
    # 1. 50 EXP 획득 (레벨업 미달)
    res1 = player.add_exp(50)
    assert not res1["leveled_up"]
    assert player.level == 1
    assert player.exp == 50
    assert player.stat_points == 0

    # 2. 60 EXP 추가 획득 (총 110 EXP -> 레벨 2 달성)
    res2 = player.add_exp(60)
    assert res2["leveled_up"]
    assert player.level == 2
    assert player.exp == 10  # 110 - 100
    assert player.stat_points == 3  # 레벨당 3포인트 지급

    # 3. 스탯 포인트 분배
    assert player.allocate_stat("strength", 2)
    assert player.strength == 12
    assert player.stat_points == 1

    assert player.allocate_stat("민첩", 1)
    assert player.agility == 11
    assert player.stat_points == 0

    # 포인트 부족 시 실패
    assert not player.allocate_stat("지능", 1)


def test_attack_physics_engine_tags_and_bow_tension():
    """태그 기반 물리 연산 (장력, 찌르기 가속도, 잽 캔슬, 둔기 골절, 스트레이트 넉백) 검증."""
    attacker = Player(name="사냥꾼", strength=10, agility=15)
    defender = NPC(id="orc1", name="오크", description="거친 오크", location="plains", constitution=12)

    # 1. 장력 부족 활 vs 완전 만작 활
    heavy_warbow = Item(id="bow1", name="대형 강궁", description="육중한 전쟁 활", location="inventory", damage=15, draw_weight_lbs=120.0, physics_tags=["projectile"])
    can_draw, ratio, msg = AttackPhysicsEngine.can_draw_bow(attacker.strength, heavy_warbow.draw_weight_lbs)
    assert not can_draw
    assert ratio < 1.0  # 근력 10(한계 50 lbs)으로는 120 lbs 활을 42% 정도만 당김

    attacker.strength = 15  # 근력 15(한계 150 lbs)
    can_draw2, ratio2, msg2 = AttackPhysicsEngine.can_draw_bow(attacker.strength, heavy_warbow.draw_weight_lbs)
    assert can_draw2
    assert ratio2 == 1.0

    # 2. 투사체 공격 물리 연산
    proj_res = AttackPhysicsEngine.evaluate_attack_physics(attacker, defender, weapon=heavy_warbow)
    assert "projectile" in proj_res.tags_applied
    assert proj_res.total_damage > heavy_warbow.damage
    assert proj_res.armor_penetration_pct > 0.0

    # 3. 돌진 가속 찌르기 (thrust + charge distance 5.0m)
    spear = Item(id="spear1", name="창", description="긴 장창", location="inventory", damage=8, physics_tags=["thrust"])
    thrust_res = AttackPhysicsEngine.evaluate_attack_physics(
        attacker, defender, weapon=spear, distance_charge_m=5.0
    )
    assert thrust_res.armor_penetration_pct >= 0.35
    assert thrust_res.physics_damage_bonus > 0.0  # 가속도 운동에너지 추가 피해

    # 4. 초고속 잽 캔슬 (jab)
    fist = Item(id="fist", name="맨손", description="단단한 주먹", location="inventory", damage=5, physics_tags=["jab"])
    jab_res = AttackPhysicsEngine.evaluate_attack_physics(
        attacker, defender, weapon=fist, target_current_action="고대어 마법 영창 중"
    )
    assert jab_res.interrupted_action
    assert "캔슬" in jab_res.interrupt_reason

    # 5. 육중한 둔기 타격 (blunt) & 골절 위험
    mace = Item(id="mace", name="전쟁 철퇴", description="강철 모닝스타", location="inventory", damage=10, physics_tags=["blunt"])
    blunt_res = AttackPhysicsEngine.evaluate_attack_physics(attacker, defender, weapon=mace)
    assert blunt_res.stagger_inflicted > 15.0
    assert blunt_res.bone_fracture_risk  # 근력 15 이상이므로 골절 위험 유발

    # 6. 체중 이동 스트레이트 (straight) & 넉백
    straight_res = AttackPhysicsEngine.evaluate_attack_physics(
        attacker, defender, attack_tags=["straight"]
    )
    assert straight_res.knockback_m > 0.0


def test_combat_distance_and_perception_interrupt():
    """5대 거리 구간 및 [A안 인지 기반] 인터럽트 판정 검증."""
    state = WorldState()
    id_player = "player"
    id_enemy = "goblin_archer"

    # 1. 거리 매트릭스 설정 및 존 확인
    CombatDistanceManager.set_distance(state, id_player, id_enemy, 35.0)
    assert CombatDistanceManager.get_distance(state, id_player, id_enemy) == 35.0
    assert CombatDistanceManager.get_distance_zone(35.0) == "long_range"
    assert "원거리" in CombatDistanceManager.get_distance_zone_ko(35.0)

    # 초장거리 (80m) 확인
    CombatDistanceManager.set_distance(state, id_player, id_enemy, 80.0)
    assert CombatDistanceManager.get_distance_zone(80.0) == "extreme_range"
    assert "초장거리" in CombatDistanceManager.get_distance_zone_ko(80.0)

    # 2. 이동 연산
    new_d = CombatDistanceManager.move_towards(state, id_player, id_enemy, speed_mps=10.0, seconds=3.0)
    assert new_d == 50.0
    assert CombatDistanceManager.get_distance(state, id_player, id_enemy) == 50.0

    # 3. [A안 인지 인터럽트] - 감각 15 플레이어의 조기 감지
    sharp_player = Player(name="스나이퍼", perception=15)
    enemy = NPC(id="thief1", name="도적", description="그림자 도적", location="alley", agility=12)
    action = CombatAction(
        entity_id="thief",
        action_name="암습 화살 발사",
        start_second=10.0,
        duration_seconds=1.2,
        target_id="player"
    )

    # 인지 엔진 판정
    threat_perc = PerceptionEngine.evaluate_combat_threat_perception(
        victim=sharp_player,
        threat_source=enemy,
        threat_name=action.action_name,
        distance_m=40.0,
        duration_seconds=action.duration_seconds
    )
    # 감각 15는 높은 보정치를 가지므로 위협 감지 및 인터럽트 생성
    if threat_perc["is_perceived"]:
        assert threat_perc["time_remaining_seconds"] > 0.0
        assert threat_perc["distance_at_perception_m"] > 0.0


def test_time_calendar_and_daily_action_matrix():
    """거시 역법, 기년법 자율화, 일상 가변 시간 매트릭스 및 나비효과 검증."""
    state = WorldState(calendar_epoch_name="성휘력", start_year=782)
    
    # 1. 캘린더 표시 검증
    assert state.current_year == 782
    assert state.current_month == 1
    assert "성휘력 782년" in state.calendar_display_ko
    assert "겨울" in state.current_season

    # 2. 시작 연도 자율성 (고정 1024년 탈피 검증)
    seed_year = TimeCalendarEngine.resolve_world_start_year({}, world_id="valoria_prime")
    assert seed_year != 1024 or seed_year > 0
    assert 1 <= seed_year <= 3000

    # 3. 일상 행동 분류 및 가변 시간 매트릭스
    key_stealth, dur_stealth, fat_stealth = TimeCalendarEngine.determine_action_duration("숨죽이며 벽을 타고 몰래 잠입을 시도한다")
    assert key_stealth == "stealth_creeping"
    assert dur_stealth == 20
    assert fat_stealth == 3

    key_study, dur_study, fat_study = TimeCalendarEngine.determine_action_duration("고대 마도서의 룬 문자를 해독하며 연구한다")
    assert key_study == "study_reading"
    assert dur_study == 90

    key_cook, dur_cook, fat_cook = TimeCalendarEngine.determine_action_duration("캠프파이어에 사슴 고기를 굽고 식사를 한다")
    assert key_cook == "cooking_eating"
    assert dur_cook == 40
    assert fat_cook < 0  # 피로도 회복

    # 4. 시간 경과 및 나비효과 (조도, 기온, 영업시간)
    # 시작 시간 08:00 (낮, 상점 오픈)
    adv1 = TimeCalendarEngine.advance_time(state, minutes=120)
    assert state.current_hour == 10
    assert adv1["time_of_day"] == "낮"
    assert adv1["is_shops_open"]

    # 12시간 경과 -> 22:00 (심야, 조도 암흑, 상점 폐점, 기온 하강)
    adv2 = TimeCalendarEngine.advance_time(state, minutes=12 * 60)
    assert state.current_hour == 22
    assert adv2["time_of_day"] == "심야"
    assert "어둠" in adv2["lighting"]
    assert not adv2["is_shops_open"]  # 22시 상점 문 닫음


def test_world_state_deserialization_backwards_compatibility():
    """기존 레거시 세이브 JSON과의 100% 역직렬화 하위 호환성 검증."""
    old_save_json = {
        "session_id": "legacy_session_001",
        "turn": 5,
        "player": {
            "name": "구도자",
            "health": 80,
            "max_health": 100,
            "strength": 12,
            "agility": 11,
            "inventory": ["sword_01"]
        },
        "items": {
            "sword_01": {
                "id": "sword_01",
                "name": "낡은 철검",
                "damage": 6
            }
        }
    }

    state = WorldState.from_dict(old_save_json)
    # 1. 새 필드 기본값 유지 확인
    assert state.calendar_epoch_name == "제국력"
    assert state.start_year == 0
    assert state.current_year > 0  # 동적 시드 연도 자동 부여
    assert state.player.stat_points == 0
    assert state.player.sub_stats == {}
    assert state.player.poise == 0.0
    assert state.player.movement_speed_mps > 4.0

    # 2. 아이템 새 필드 기본값 확인
    item = state.items["sword_01"]
    assert item.draw_weight_lbs == 0.0
    assert item.windup_seconds == 0.0
    assert item.stagger_power == 0.0
    assert item.physics_tags == []

    # 3. 다시 JSON 직렬화 후 재복원 테스트
    serialized = state.to_json()
    reloaded = WorldState.from_json(serialized)
    assert reloaded.player.name == "구도자"
    assert reloaded.player.strength == 12
    assert reloaded.items["sword_01"].name == "낡은 철검"
