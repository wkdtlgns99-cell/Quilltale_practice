"""
Tests for balance caps, stat thresholds, scaling clamps, and Fog of War on NPC stats.
"""
from src.world.state import WorldState
from src.world.dice import DiceEngine
from src.core.config import MAX_STAT_VALUE, MIN_REPUTATION_DELTA, MAX_REPUTATION_DELTA


def load_test_state() -> WorldState:
    with open("data/worlds/default.json", encoding="utf-8") as f:
        return WorldState.from_json(f.read())


def test_reputation_delta_clamping():
    state = load_test_state()
    assert state.player.reputation == 0

    # Attempt huge positive jump (+100) -> should clamp to +15
    state.apply_update({"reputation_delta": 100})
    assert state.player.reputation == MAX_REPUTATION_DELTA

    # Attempt huge negative drop (-80) -> should clamp to -25
    state.apply_update({"reputation_delta": -80})
    assert state.player.reputation == MAX_REPUTATION_DELTA + MIN_REPUTATION_DELTA


def test_stat_level_up_cap():
    state = load_test_state()
    state.player.str_stat = 29

    # Add 100 exp to trigger level up
    state.apply_update({"add_exp": 100})
    assert state.player.level == 2
    assert state.player.str_stat == 30

    # Add another 100 exp -> STR should remain capped at MAX_STAT_VALUE (30)
    state.apply_update({"add_exp": 100})
    assert state.player.level == 3
    assert state.player.str_stat == MAX_STAT_VALUE


def test_skill_scaling_clamp():
    # Scaling of 5.0 should be clamped to 3.0
    dmg_high = DiceEngine.calculate_skill_damage(base_damage=10, stat_value=14, scaling=5.0)
    dmg_capped = DiceEngine.calculate_skill_damage(base_damage=10, stat_value=14, scaling=3.0)
    assert dmg_high == dmg_capped

    # Scaling of 0.1 should be clamped to 0.5
    dmg_low = DiceEngine.calculate_skill_damage(base_damage=10, stat_value=14, scaling=0.1)
    dmg_min = DiceEngine.calculate_skill_damage(base_damage=10, stat_value=14, scaling=0.5)
    assert dmg_low == dmg_min


def test_npc_stats_fog_of_war():
    state = load_test_state()
    barkeep = state.npcs["barkeep"]
    assert not barkeep.stats_revealed

    # Before reveal: Summary shows physical impression, hides exact HP/AC numbers
    summary_before = state.to_player_summary()
    assert barkeep.impression_ko in summary_before
    assert f"HP:{barkeep.health}" not in summary_before

    # Reveal stats
    state.apply_update({"reveal_npc_stats": ["barkeep"]})
    assert barkeep.stats_revealed

    summary_after = state.to_player_summary()
    assert f"HP:{barkeep.health}" in summary_after
    assert f"방어:{barkeep.armor_class}" in summary_after


def test_quote_syntax_parsing():
    from src.world.validator import ActionValidator
    raw = '"안녕 내 이름은 엘릭이야." \'뭐하는 사람이지?\' 단검을 집어든다'
    parsed = ActionValidator.parse_action_components(raw)
    assert parsed["dialogue"] == "안녕 내 이름은 엘릭이야."
    assert parsed["monologue"] == "뭐하는 사람이지?"
    assert parsed["action"] == "단검을 집어든다"


def test_no_incantation_damage_scaling():
    full_dmg, _ = DiceEngine.calculate_skill_damage_with_crit(
        base_damage=100,
        stat_value=20,
        scaling=2.0,
        target_defense=0,
        is_no_incantation=False
    )
    assert full_dmg > 100

    no_incant_dmg, _ = DiceEngine.calculate_skill_damage_with_crit(
        base_damage=100,
        stat_value=20,
        scaling=2.0,
        target_defense=0,
        is_no_incantation=True
    )
    assert no_incant_dmg == max(1, int(full_dmg * 0.1))


def test_fatigue_and_time_updates():
    state = load_test_state()
    assert state.player.fatigue == 0
    assert state.player.time_elapsed_minutes == 0

    state.apply_update({
        "fatigue_delta": 25,
        "time_minutes": 30
    })

    assert state.player.fatigue == 25
    assert state.player.time_elapsed_minutes == 30
    assert state.player.fatigue_status_ko == "경미한 피로"

    state.apply_update({"fatigue_delta": 60})
    assert state.player.fatigue == 85
    assert "탈진" in state.player.fatigue_status_ko


def test_npc_schedule_progression_and_traces():
    state = load_test_state()
    npc = state.npcs["barkeep"]
    npc.schedule = [
        {"turn": 1, "location": "tavern", "activity": "손님 응대"},
        {"turn": 2, "location": "street", "activity": "식자재 구매를 위해 거리로 나섬", "trace_left": "카운터에 남겨진 쪽지와 닫힌 자물쇠"}
    ]

    # Turn 1
    state.turn = 1
    state.advance_npc_schedules()
    assert npc.location == "tavern"
    assert npc.current_activity == "손님 응대"

    # Turn 2: NPC moves to street, leaving trace in tavern
    state.turn = 2
    state.advance_npc_schedules()
    assert npc.location == "street"
    assert "식자재 구매" in npc.current_activity
    assert len(state.locations["tavern"].physical_traces) > 0
    assert "쪽지" in state.locations["tavern"].physical_traces[-1]["trace"]

    # Off-screen context generation
    ctx = state.get_off_screen_context_for_location("tavern")
    assert "[현장에 남겨진 물리적 흔적 및 단서]" in ctx
    assert "쪽지" in ctx


def test_npc_player_symmetry():
    state = load_test_state()
    npc = state.npcs["barkeep"]
    assert npc.job is not None
    assert npc.gold >= 0
    assert hasattr(npc, "equipment")
    assert hasattr(npc, "needs")
    assert npc.strength >= 1
    assert npc.str_mod == (npc.strength - 10) // 2
    assert npc.effective_crit_rate >= 5.0
    
    # Test JSON roundtrip
    raw_json = state.to_json()
    loaded_state = WorldState.from_json(raw_json)
    loaded_npc = loaded_state.npcs["barkeep"]
    assert loaded_npc.job == npc.job
    assert loaded_npc.gold == npc.gold
    assert loaded_npc.needs.hunger == npc.needs.hunger


def test_npc_needs_and_economy_simulation():
    state = load_test_state()
    npc = state.npcs["barkeep"]
    initial_hunger = npc.needs.hunger
    
    # Give damaged health and healing item
    npc.health = 20
    npc.inventory.append("minor_heal_potion")
    state.items["minor_heal_potion"] = type("ItemObj", (), {"name": "하급 치유 포션", "id": "minor_heal_potion"})()
    
    logs = state.simulate_npc_needs_and_economy()
    assert npc.needs.hunger == initial_hunger + 1
    assert npc.health > 20
    assert "minor_heal_potion" not in npc.inventory


def test_gossip_chain_rumor_exchange():
    state = load_test_state()
    # Place two NPCs in the tavern
    state.locations["tavern"].npcs = ["barkeep", "merchant"]
    state.npcs["merchant"].location = "tavern"
    
    # Give barkeep an impactful memory
    state.npcs["barkeep"].memories.append(
        type("MemObj", (), {
            "turn": 1,
            "description": "어젯밤 폐허에서 수상한 푸른 불빛을 목격함",
            "emotional_tone": "suspicious",
            "significance": 4,
            "is_anchor": False
        })()
    )
    
    gossip_logs = state.exchange_rumors_in_locations()
    assert len(gossip_logs) > 0
    merchant_mems = [m.description for m in state.npcs["merchant"].memories]
    assert any("어젯밤 폐허에서" in m for m in merchant_mems)


def test_physical_object_weight_and_bag_storage():
    from src.world.validator import ActionValidator
    from src.world.state import Item
    state = load_test_state()
    
    # Add a heavy boulder (required STR 50) and a medium chair (can't store in bag) to tavern
    state.items["heavy_boulder"] = Item(
        id="heavy_boulder",
        name="거대한 화강암 바위",
        description="혼자서는 도저히 들 수 없는 거대한 바위다.",
        location="tavern",
        weight=250.0,
        size="heavy",
        required_strength=50,
        can_store_in_bag=False
    )
    state.items["tavern_chair"] = Item(
        id="tavern_chair",
        name="오크나무 의자",
        description="투박하지만 튼튼한 목재 의자다.",
        location="tavern",
        weight=8.0,
        size="medium",
        required_strength=10,
        can_store_in_bag=False
    )
    state.locations["tavern"].items.extend(["heavy_boulder", "tavern_chair"])
    
    # 1. Attempt to pick up heavy boulder with STR 12 -> Rejected
    state.player.strength = 12
    valid, msg, _, _ = ActionValidator.pre_validate_action("거대한 화강암 바위를 번쩍 집어든다", state)
    assert not valid
    assert "너무 무겁습니다" in msg

    # 2. Attempt to put medium chair into bag -> Rejected
    valid, msg, _, _ = ActionValidator.pre_validate_action("오크나무 의자를 가방에 넣는다", state)
    assert not valid
    assert "부피가 너무 커서 가방에 들어가지 않습니다" in msg

    # 3. Superhuman strength (STR 100) picking up boulder -> Allowed
    state.player.strength = 100
    valid, msg, _, _ = ActionValidator.pre_validate_action("거대한 화강암 바위를 번쩍 들어올린다", state)
    assert valid


def test_news_poster_materialization_and_reading():
    state = load_test_state()
    poster = state.generate_news_poster("북부 가도에서 상단을 습격한 도적단 수색 중", turn=10)
    assert poster.id in state.items
    assert "news_poster_turn_10" == poster.id
    assert "【갓 붙은 벽보 (제10보)】" == poster.name
    assert "📜 [제10보]" in poster.document_text
    assert "북부 가도에서 상단을 습격한 도적단 수색 중" in poster.document_text


def test_in_game_time_progression_and_periodicals():
    state = load_test_state()
    # Initial: Day 1 Monday 08:00
    assert state.current_day == 1
    assert state.day_of_week_ko == "월"
    assert state.current_hour == 8
    assert state.current_minute == 0
    assert "1일차 월요일 08:00" in state.time_display_ko

    # 1. First check at 08:00 AM on Day 1 Monday: publishes daily paper & weekly gazette
    published = state.check_and_publish_periodicals()
    assert len(published) >= 2
    pub_ids = [p.id for p in published]
    assert "daily_paper_day_1" in pub_ids
    assert "weekly_gazette_week_1" in pub_ids
    
    # 2. Advance time by 3 hours (180 mins) -> 11:00 AM (Same day, no new publication)
    state.player.time_elapsed_minutes += 180
    assert state.current_hour == 11
    assert len(state.check_and_publish_periodicals()) == 0

    # 3. Add critical event to breaking news queue
    state.pending_breaking_news.append("동쪽 유적 제3회랑 대붕괴 발생")

    # 4. Advance time to next day 08:30 AM (+21.5 hours = 1290 mins)
    state.player.time_elapsed_minutes += 1290
    assert state.current_day == 2
    assert state.day_of_week_ko == "화"
    assert state.current_hour == 8
    assert state.current_minute == 30

    # Check publication on Day 2 Tuesday morning: Daily paper + Extra Edition Breaking News!
    published_day2 = state.check_and_publish_periodicals()
    pub_ids_day2 = [p.id for p in published_day2]
    assert "daily_paper_day_2" in pub_ids_day2
    assert "extra_edition_day_2" in pub_ids_day2
    
    # Verify Breaking News Content
    extra_item = state.items["extra_edition_day_2"]
    assert "🚨🚨 【긴급 호외 (EXTRA EDITION): 특보】" in extra_item.document_text
    assert "동쪽 유적 제3회랑 대붕괴 발생" in extra_item.document_text


def test_npc_hierarchy_and_tiers():
    state = load_test_state()
    merchant = state.npcs["merchant"]
    assert merchant.tier == "commoner"
    assert merchant.influence_scope == "local"

    barkeep = state.npcs["barkeep"]
    assert barkeep.tier == "intermediate"

    # Create a legend named NPC

    state.apply_update({
        "create_npc": {
            "id": "veteran_mercenary_vane",
            "name": "외눈의 베인",
            "tier": "intermediate",
            "job": "용병단장",
            "influence_scope": "regional",
            "titles": ["blood_mercenary_leader"],
            "skills": ["iron_cleave"],
            "location": "tavern"
        }
    })

    vane = state.npcs["veteran_mercenary_vane"]
    assert vane.name == "외눈의 베인"
    assert vane.tier == "intermediate"
    assert vane.influence_scope == "regional"
    assert "veteran_mercenary_vane" in state.locations["tavern"].npcs


def test_live_data_persistence_and_environment():
    state = load_test_state()
    # 1. Update persistent environment changes (broken tavern table, burned fireplace)
    state.apply_update({
        "update_environment": {
            "tavern": {"main_table": "전투로 인해 반파됨", "wooden_door": "도끼로 찍힌 자국"}
        },
        "record_clue": {
            "secret_note_clue": "선술집 지하실 비밀 통로는 세 번째 오크통 뒤편에 존재함"
        }
    })

    assert state.environment_states["tavern"]["main_table"] == "전투로 인해 반파됨"
    assert "secret_note_clue" in state.discovered_clues

    # Test serialization roundtrip (Zero Evaporation)
    raw_json = state.to_json()
    loaded = WorldState.from_json(raw_json)
    assert loaded.environment_states["tavern"]["main_table"] == "전투로 인해 반파됨"
    assert loaded.discovered_clues["secret_note_clue"] == "선술집 지하실 비밀 통로는 세 번째 오크통 뒤편에 존재함"


def test_dynamic_on_demand_expansion_registration():
    state = load_test_state()
    
    # Dynamically explore a newly mentioned secret backroom and a black market merchant
    state.apply_update({
        "create_location": {
            "id": "tavern_secret_basement",
            "name": "선술집 지하 비밀 창고",
            "description": "먼지 쌓인 에일통과 수상한 밀수품들이 가득한 어두운 지하실이다.",
            "exits": {"upstairs": "tavern"}
        },
        "create_npc": {
            "id": "black_market_smuggler",
            "name": "밀수꾼 핀치",
            "tier": "intermediate",
            "job": "암시장 중개인",
            "location": "tavern_secret_basement"
        },
        "create_item": {
            "id": "ancient_runic_scroll",
            "name": "고대 룬어 마법 스크롤",
            "location": "tavern_secret_basement",
            "item_type": "document",
            "document_text": "【헬리오스 이그니스】: 열역학적 팽창에 기반한 화염 발현"
        }
    })

    assert "tavern_secret_basement" in state.locations
    assert "black_market_smuggler" in state.npcs
    assert "ancient_runic_scroll" in state.items
    assert state.items["ancient_runic_scroll"].location == "tavern_secret_basement"


def test_factions_and_macro_lore_persistence():
    state = load_test_state()
    assert "border_guard" in state.factions
    assert state.factions["border_guard"].name == "국경 치안 수비대"
    assert state.factions["border_guard"].relations.get("shadow_guild") == "적대"
    assert "magic_origin" in state.world_lore


def test_npc_desire_weakness_and_appearance_story():
    state = load_test_state()
    barkeep = state.npcs["barkeep"]
    assert barkeep.desire != ""
    assert barkeep.weakness != ""
    assert barkeep.appearance_story != ""

    # Test serialization
    raw = state.to_json()
    loaded = WorldState.from_json(raw)
    assert loaded.npcs["barkeep"].desire == barkeep.desire
    assert loaded.npcs["barkeep"].weakness == barkeep.weakness


def test_utility_item_and_environmental_hazards():
    state = load_test_state()
    
    # 1. Check utility function and hazards in tavern
    state.locations["tavern"].environmental_hazards = ["쇠사슬 샹들리에", "기름통"]
    assert "쇠사슬 샹들리에" in state.locations["tavern"].environmental_hazards

    # 2. Trigger hazard via apply_update
    state.apply_update({
        "trigger_hazard": {
            "location_id": "tavern",
            "hazard_name": "쇠사슬 샹들리에",
            "effect": "밧줄이 잘려나가며 적 2명을 깔아뭉갬"
        }
    })
    assert state.environment_states["tavern"]["hazard_쇠사슬 샹들리에"] == "밧줄이 잘려나가며 적 2명을 깔아뭉갬"


def test_faction_ripple_propagation():
    state = load_test_state()
    ripple_logs = state.apply_faction_ripple("border_guard", 20, reason="도적단 소탕")
    assert any("국경 치안 수비대" in log for log in ripple_logs)
    assert any("그림자 밀수 연합" in log for log in ripple_logs)
    assert any("-14" in log for log in ripple_logs)


def test_world_secrets_and_dilemma_recording():
    state = load_test_state()
    
    # 1. Reveal clue fragment for mystery
    state.apply_update({
        "reveal_clue_fragment": {
            "secret_id": "shadow_conspiracy",
            "truth": "치안대장과 밀수단 수장이 동일인물임",
            "fragment": "비밀 장부에 적힌 치안대장의 서명 필적"
        },
        "record_dilemma": {
            "dilemma_id": "save_caravan_vs_ruin_entry",
            "choice_summary": "상단을 구호하느라 유적 진입 타이밍을 놓침",
            "cost": "유적 선점 기회 상실"
        }
    })

    assert "shadow_conspiracy" in state.world_secrets
    assert any("비밀 장부에 적힌" in c for c in state.world_secrets["shadow_conspiracy"]["clues"])
    assert len(state.dilemmas_faced) > 0
    assert state.dilemmas_faced[0]["cost"] == "유적 선점 기회 상실"


def test_npc_13_human_factors_full_preservation():
    state = load_test_state()
    barkeep = state.npcs["barkeep"]
    
    # Verify all 13 human persona factors are populated
    assert "merchant" in barkeep.bonds
    assert "용병 시절" in barkeep.trauma
    assert "앞치마 매듭" in barkeep.quirk
    assert "아이" in barkeep.taboo
    assert len(barkeep.tastes["likes"]) > 0
    assert "절뚝거림" in barkeep.physical_condition
    assert "북부 국경 방언" in barkeep.speech_style
    assert "새벽 5시" in barkeep.daily_routine
    assert "소금" in barkeep.superstitions
    assert "냉혹한 장사치" in barkeep.self_image_vs_reputation
    assert "고아원" in barkeep.hidden_side
    assert "문맹" in barkeep.education_level
    assert "임대료" in barkeep.financial_state

    # Roundtrip serialization
    raw = state.to_json()
    loaded = WorldState.from_json(raw)
    loaded_bk = loaded.npcs["barkeep"]
    assert loaded_bk.bonds == barkeep.bonds
    assert loaded_bk.trauma == barkeep.trauma
    assert loaded_bk.superstitions == barkeep.superstitions
    assert loaded_bk.hidden_side == barkeep.hidden_side


def test_dynamic_npc_creation_with_13_factors():
    state = load_test_state()
    state.apply_update({
        "create_npc": {
            "id": "shadow_assassin_kain",
            "name": "그림자 암살자 카인",
            "job": "암살자",
            "tier": "intermediate",
            "bonds": {"barkeep": "과거 생명의 은인"},
            "trauma": "단 한 번의 암살 실패로 파문당한 기억",
            "quirk": "동전을 손가락 사이로 굴리는 버릇",
            "taboo": "아이 의뢰는 절대 수락하지 않음",
            "speech_style": "나지막하고 건조한 속삭임",
            "hidden_side": "몰래 길고양이들에게 먹이를 줌",
            "financial_state": "암시장 장비 구매로 100골드 빚더미"
        }
    })

    kain = state.npcs["shadow_assassin_kain"]
    assert kain.name == "그림자 암살자 카인"
    assert kain.bonds.get("barkeep") == "과거 생명의 은인"
    assert kain.hidden_side == "몰래 길고양이들에게 먹이를 줌"








