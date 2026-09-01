"""
Script to register all 25+ rich companion templates into data/templates/companion_templates.json.
"""
import json
from pathlib import Path

TEMPLATES_PATH = Path("data/templates/companion_templates.json")

# Load existing
if TEMPLATES_PATH.exists():
    with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
        existing = json.load(f)
else:
    existing = []

existing_dict = {c["companion_id"]: c for c in existing if "companion_id" in c}

new_companions = [
  {
    "companion_id": "companion_orion_magnet_arcanist",
    "name_ko": "오리온 볼테어",
    "title_ko": "극성(極性)의 전자기술사",
    "role": "arcane_blaster",
    "formation": "midline",
    "speech_style": "timid_scholar",
    "stats": {
      "level": 12,
      "health": 88,
      "max_health": 88,
      "mana": 82,
      "max_mana": 82,
      "strength": 8,
      "agility": 13,
      "constitution": 11,
      "intelligence": 19,
      "wisdom": 14,
      "luck": 12,
      "defense": 11,
      "attack_power": 32
    },
    "personality": {
      "loyalty_score": 50,
      "affinity": 10,
      "moral_alignment": "lawful_neutral",
      "desire": "폭주하여 하늘로 솟구쳐 오르는 대륙의 '원초 자수정 극성 핵' 안정화",
      "taboo": "비자성 광물 밀수 조작, 피뢰침 임의 철거, 나침반 파손",
      "hidden_secret": "신체 좌우가 N극과 S극으로 영구 대전되어 있어 금속 장비를 만지면 손에 달라붙음",
      "betrayal_trigger": "플레이어가 자기장 증폭기를 역이용해 대도시의 통신망과 나침반을 마비시킬 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "행성 자기장의 조율자 (극성 안정화)",
        "trigger_condition": "자수정 핵을 폭주 없이 안정시키고 대지의 전자기망을 수복",
        "stat_modifiers": { "intelligence": 6, "wisdom": 4 },
        "unlocked_skill": "skill_geomagnetic_shield_dome",
        "personality_shift": "세상의 모든 전자기적 질서를 조율하는 냉철한 과학자"
      },
      "path_b": {
        "branch_name_ko": "초고압 레일건 섬멸자 (극성 과부하)",
        "trigger_condition": "자기장 에너지를 전신에 과부하시켜 파괴적인 금속 투척 무기화",
        "stat_modifiers": { "attack_power": 14, "constitution": -4 },
        "unlocked_skill": "skill_hyper_railgun_annihilation",
        "personality_shift": "모든 금속을 초고속 탄환으로 날려버리는 파괴광"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "demagnetization_vertigo",
      "flaw_name_ko": "탈자화(脫磁化) 공황 발작",
      "trigger_condition": "heavy_corrosive_acid_damage_taken",
      "effect_ko": "자기장이 지워져 2턴간 마법 사거리가 50% 감소하고 명중률 -30%"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "전자기 방어막 구축 및 금속 탐지",
      "effect_ko": "거점 외부 원거리 투사체 피습 100% 무효화 및 주간 희귀 자성 광석 3개 발굴"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 30,
      "boss_focus_weight": 70,
      "crowd_control_weight": 80,
      "self_preservation_weight": 40
    },
    "inventory_quirks": {
      "quirk_type": "magnetize_metal_gold",
      "description_ko": "플레이어 가방의 골드에 자성을 띄워 바닥에 떨어진 동전을 자동 회수하도록 변조"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_magnetic_polar_inversion",
      "name_ko": "극성 반전 결속 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어 피격 시 공격한 적의 극성을 반대로 뒤집어 다음 턴 서로 밀쳐내며 행동 취소"
    },
    "bond": {
      "tier": 1,
      "current_points": 15,
      "tier_bonuses": {
        "tier_2": "금속 갑옷 착용 적 대상 번개/자기 피해 +15%",
        "tier_3": "합동 연계기 기절 지속 +1턴",
        "tier_4": "원거리 금속 투사체 피격 대미지 30% 반사",
        "tier_5": "사망 방지 1회 및 지능 스탯 +4 공유"
      }
    },
    "recruitment": {
      "location_id": "lightning_rod_spire",
      "reputation_min": -20,
      "reputation_max": 80,
      "completed_quest_id": "quest_charge_magnetic_lodestone",
      "hire_cost_gold": 120,
      "upkeep_gold_per_day": 8,
      "dialogue_recruit": "인력과 척력, 세상은 이 두 힘으로 돌아갑니다. 당신 곁에서 균형을 맞추겠습니다."
    },
    "loot_demands": {
      "gold_share_percent": 12,
      "preferred_item_categories": ["lodestone", "wire", "battery"],
      "forbidden_item_types": []
    },
    "camp_role": "scholar",
    "exploration_talents": ["magnetic_metal_sensing", "lightning_grounding", "electromagnetic_lock_override"],
    "companion_relations": {
      "likes": ["companion_milo_tinkerer"],
      "dislikes": ["companion_baldur_living_mountain"],
      "conflict_event_id": "event_magnet_clashes_with_earth"
    },
    "combat_skills": [
      {
        "skill_id": "polar_repulsion_blast",
        "name_ko": "척력 반발 충격파",
        "mana_cost": 16,
        "cooldown_turns": 2,
        "effect_type": "knockback_and_damage",
        "description_ko": "강력한 반발력을 뿜어 적 전열을 2칸 밀쳐내고 36의 자기 충격 피해를 입힙니다."
      },
      {
        "skill_id": "ferrofluid_attraction_snare",
        "name_ko": "자성 유체 구속",
        "mana_cost": 22,
        "cooldown_turns": 3,
        "effect_type": "aoe_pull_and_root",
        "description_ko": "자성 입자를 뿌려 적 2명을 서로 충돌시키며 30의 피해와 1턴 기절을 가합니다."
      }
    ],
    "combo_technique": {
      "combo_id": "electromagnetic_hyper_strike",
      "name_ko": "전자기 유도 가속격",
      "trigger_condition": "player_uses_lightning_or_piercing_attack",
      "description_ko": "플레이어의 공격 경로에 강력한 자기 가속 레일을 깔아 피해량을 2배로 폭증시킵니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_superconducting_magnetic_storm",
      "name_ko": "초전도 극성 폭풍",
      "charge_type": "turns_delay",
      "charge_required": 4,
      "mana_cost": 45,
      "activation_voice_line": "극성이 뒤집힌다! 척력의 폭풍 속에 찢겨져 나가라!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 86,
        "stat_scaling": 2.4,
        "status_applied": "magnetic_paralysis",
        "status_duration": 2,
        "ally_buff": "party_metal_armor_up_6"
      },
      "cinematic_description": "전장 전체의 자기장이 거꾸로 솟구치며 적들의 무기와 갑옷이 서로를 쥐어뜯어 박살냄"
    },
    "party_passive": {
      "buff_id": "geomagnetic_guidance",
      "name_ko": "지자기 유도",
      "effect_ko": "파티 전체 원거리 공격 적중률 +12% 및 미로 탈출 실패 확률 0%"
    },
    "equipment": {
      "weapon": "bipolar_magnetic_resonator_staff",
      "armor": "insulated_copper_threaded_robe",
      "shield": "none",
      "accessory": "polarized_ferrofluid_vial"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 3,
      "downed_cry": "극성이… 붕괴한다… 내 몸이… 흩어진다…!",
      "death_trauma_to_party": "파티 금속 장비 방어력 영구 -3 및 나침반 마비"
    },
    "dialogue_lines": {
      "greeting": "금속 단추가 제 소매에 붙으려 하네요. 조금 떨어져서 말씀하시죠.",
      "camp_rest": "장작불 주위에 쇳가루를 뿌려두면 신기한 자기력선 모양으로 춤을 춥니다.",
      "low_loyalty_warning": "당신의 무례함은 제 극성을 척력으로 돌아서게 만들 뿐입니다.",
      "traitor_reveal": "네 심장에 박힌 철분을 한 번에 뽑아내 주마.",
      "dismissal": "연구소로 돌아갑니다. 금속 파편 조심하십시오."
    }
  },
  {
    "companion_id": "companion_vesper_plague_alchemist",
    "name_ko": "베스퍼 그림스포어",
    "title_ko": "포자를 퍼뜨리는 진균학자",
    "role": "healer_support",
    "formation": "backline",
    "speech_style": "whimsical_trickster",
    "stats": {
      "level": 11,
      "health": 80,
      "max_health": 80,
      "mana": 86,
      "max_mana": 86,
      "strength": 6,
      "agility": 12,
      "constitution": 12,
      "intelligence": 18,
      "wisdom": 16,
      "luck": 14,
      "defense": 9,
      "attack_power": 20
    },
    "personality": {
      "loyalty_score": 45,
      "affinity": 5,
      "moral_alignment": "chaotic_neutral",
      "desire": "죽은 자의 신경을 일시적으로 이어 생명을 연장하는 '공생 균사망' 완성",
      "taboo": "균류 군락 방화, 살균제 무단 살포, 곰팡이 포자 소각",
      "hidden_secret": "자신의 척추 뒤쪽에 거대한 발광 버섯 군락이 자라나 신경계를 공유하고 있음",
      "betrayal_trigger": "플레이어가 진균 숲에 불을 질러 희귀 포자들을 전멸시킬 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "생명의 균사 의술사 (공생 치유)",
        "trigger_condition": "포자를 약용으로 개량하여 전염병을 억제하는 공생 곰팡이 배포",
        "stat_modifiers": { "wisdom": 7, "mana": 15 },
        "unlocked_skill": "skill_mycelium_life_reconnection",
        "personality_shift": "균류의 분해와 순환을 통해 생명을 구호하는 자상한 박물학자"
      },
      "path_b": {
        "branch_name_ko": "좀비 포자의 군주 (군체 지배)",
        "trigger_condition": "사체에 침투해 숙주를 조종하는 기생 버섯을 완성하여 군단 형성",
        "stat_modifiers": { "intelligence": 8, "attack_power": 8 },
        "unlocked_skill": "skill_cordyceps_parasitic_outbreak",
        "personality_shift": "모든 지적 생명체를 포자의 숙주로 삼으려는 기괴한 광인"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "dry_air_desiccation_wither",
      "flaw_name_ko": "극건조 포자 고사증",
      "trigger_condition": "desert_zone_or_intense_drought_weather",
      "effect_ko": "몸의 버섯이 말라붙어 턴당 마나 10 누수 및 치유량 40% 감소"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 발효실 및 약용 버섯 농장 운영",
      "effect_ko": "주간 특수 마나 회복 버섯 5개 생산 및 거점 내 시체 자동 분해 비료화"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 75,
      "boss_focus_weight": 30,
      "crowd_control_weight": 85,
      "self_preservation_weight": 50
    },
    "inventory_quirks": {
      "quirk_type": "grow_mushrooms_in_backpack",
      "description_ko": "플레이어 가방 구석에 곰팡이를 번식시켜 비상 식량용 '식용 균류'로 자라나게 함"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_mycelium_neural_mesh",
      "name_ko": "균사 신경망 결속 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "파티원 전체가 보이지 않는 균사로 연결되어 한 명이 치유받을 시 다른 모든 아군도 치유량의 30%를 균등 분배"
    },
    "bond": {
      "tier": 1,
      "current_points": 15,
      "tier_bonuses": {
        "tier_2": "도트 힐 지속시간 +1턴",
        "tier_3": "합동 연계기 혼란 포자 지속 +1턴",
        "tier_4": "적 중독 상태일 때 치유량 20% 증폭",
        "tier_5": "사망 방지 1회 및 체력 0 도달 시 포자 군집으로 흩어져 1턴 후 부활"
      }
    },
    "recruitment": {
      "location_id": "bioluminescent_fungal_cavern",
      "reputation_min": -30,
      "reputation_max": 70,
      "completed_quest_id": "quest_cultivate_glowing_spore",
      "hire_cost_gold": 100,
      "upkeep_gold_per_day": 7,
      "dialogue_recruit": "후후… 제 등 뒤의 버섯들이 당신의 상처를 핥아주고 싶어 안달이 났네요. 같이 갈까요?"
    },
    "loot_demands": {
      "gold_share_percent": 10,
      "preferred_item_categories": ["mushroom", "herb", "spore"],
      "forbidden_item_types": ["torch", "salt"]
    },
    "camp_role": "cook",
    "exploration_talents": ["fungal_poison_immunity", "night_bioluminescence", "organic_decomposition"],
    "companion_relations": {
      "likes": ["companion_orlaith_bog_trapper"],
      "dislikes": ["companion_ignis_cinder_scholar"],
      "conflict_event_id": "event_scholar_burns_mushrooms"
    },
    "combat_skills": [
      {
        "skill_id": "healing_spore_mist",
        "name_ko": "치유 포자 안개",
        "mana_cost": 16,
        "cooldown_turns": 1,
        "effect_type": "aoe_regen_heal",
        "description_ko": "발광 포자를 날려 아군 전체 체력을 20 채우고 2턴간 매 턴 10씩 재생시킵니다."
      },
      {
        "skill_id": "hallucinogenic_puffball",
        "name_ko": "환각 포자낭 투척",
        "mana_cost": 20,
        "cooldown_turns": 3,
        "effect_type": "aoe_confusion_and_poison",
        "description_ko": "포자 주머니를 터뜨려 적 2명에게 25의 독 피해와 2턴간 아군을 공격하는 환각을 겁니다."
      }
    ],
    "combo_technique": {
      "combo_id": "toxic_spore_detonation",
      "name_ko": "맹독 포자 연쇄 폭발",
      "trigger_condition": "player_inflicts_poison_or_acid",
      "description_ko": "중독된 적 몸속의 포자를 급속 발아시켜 피부를 뚫고 나오며 68의 폭발 피해를 입힙니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_blooming_mycelial_forest",
      "name_ko": "만개하는 원초 균사림",
      "charge_type": "morale_and_damage",
      "charge_required": 100,
      "mana_cost": 35,
      "activation_voice_line": "피어나라, 작은 포자들아! 모든 썩어가는 것들에 생명을!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 60,
        "stat_scaling": 2.0,
        "status_applied": "mass_spore_paralysis",
        "status_duration": 2,
        "ally_buff": "full_party_cleanse_and_heal_50"
      },
      "cinematic_description": "전장 전체가 거대한 발광 버섯 숲으로 뒤덮이며 적들을 마비시키고 아군의 모든 상처를 봉합"
    },
    "party_passive": {
      "buff_id": "spore_resilience",
      "name_ko": "포자의 면역망",
      "effect_ko": "파티 전체 독 및 부패 상태이상 피해 50% 영구 경감"
    },
    "equipment": {
      "weapon": "glowing_mushroom_spore_crook",
      "armor": "damp_moss_woven_tunic",
      "shield": "none",
      "accessory": "symbiotic_fungal_locket"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 3,
      "downed_cry": "버섯들이… 시들어가요… 포자가 흩어지면… 난 죽는데…!",
      "death_trauma_to_party": "파티 독 저항력 50% 영구 감소 및 야영 불안 증세"
    },
    "dialogue_lines": {
      "greeting": "킁킁… 당신 몸에서 아주 맛있는 흙냄새가 나네요. 버섯 심기 딱 좋아요.",
      "camp_rest": "축축하고 어두운 그늘이 제일 아늑하죠. 장작불 옆은 너무 건조해서 싫어요.",
      "low_loyalty_warning": "자꾸 내 버섯들을 발로 밟으면 당신 귓속에 포자를 심어버릴 거예요.",
      "traitor_reveal": "당신의 뇌를 곰팡이 뿌리로 가득 채워 꼭두각시로 만들어 드리죠.",
      "dismissal": "축축한 늪지로 돌아갈래요. 안녕, 포자 없는 메마른 사람."
    }
  },
  {
    "companion_id": "companion_caelius_aether_skater",
    "name_ko": "카엘리우스 윈드시어",
    "title_ko": "천공의 바람스케이트 척후병",
    "role": "scout_rogue",
    "formation": "frontline",
    "speech_style": "whimsical_trickster",
    "stats": {
      "level": 12,
      "health": 98,
      "max_health": 98,
      "mana": 35,
      "max_mana": 35,
      "strength": 13,
      "agility": 20,
      "constitution": 12,
      "intelligence": 11,
      "wisdom": 12,
      "luck": 16,
      "defense": 13,
      "attack_power": 28
    },
    "personality": {
      "loyalty_score": 50,
      "affinity": 10,
      "moral_alignment": "chaotic_good",
      "desire": "바람이 끊어진 '공허의 협곡'에 영원히 부는 상승 기류를 다시 흐르게 하기",
      "taboo": "활강 날개 절단, 고소공포증 환자 절벽 투하, 바람막이 벽 강제 축조",
      "hidden_secret": "발목에 바람 정령이 깃든 공기 부유 스케이트가 일체화되어 평생 맨발로 흙을 밟지 못함",
      "betrayal_trigger": "플레이어가 협곡의 바람길을 차단해 비행선 통행세를 뜯어낼 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "자유 활강의 바람 전령 (하늘 개척자)",
        "trigger_condition": "협곡의 폭풍을 안정화하고 대륙 전역을 잇는 천공 활강 루트 개척",
        "stat_modifiers": { "agility": 7, "luck": 4 },
        "unlocked_skill": "skill_aether_slipstream_dive",
        "personality_shift": "구속 없는 하늘의 자유를 전파하는 명랑한 모험가"
      },
      "path_b": {
        "branch_name_ko": "절벽의 날개 도살자 (추락 사냥꾼)",
        "trigger_condition": "협곡의 바람을 역류시켜 비행하는 모든 적을 절벽 바닥으로 격추",
        "stat_modifiers": { "attack_power": 13, "defense": -4 },
        "unlocked_skill": "skill_gravity_cliff_drop_kick",
        "personality_shift": "적을 높은 곳에서 떨어뜨려 박살 내는 것을 즐기는 낙하 살인마"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "grounded_inertia_panic",
      "flaw_name_ko": "지면 고착 속박증",
      "trigger_condition": "rooted_or_trapped_in_heavy_mud",
      "effect_ko": "스케이트 회전 불가로 2턴간 회피율 0% 및 자포자기 상태이상 돌입"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "초고속 천공 전령 및 정찰 비행",
      "effect_ko": "퀘스트 수락 및 보상 수령 시간 즉시 처리 및 주변 지역 맵 안개 100% 탐색"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 20,
      "boss_focus_weight": 70,
      "crowd_control_weight": 50,
      "self_preservation_weight": 80
    },
    "inventory_quirks": {
      "quirk_type": "oil_party_boots",
      "description_ko": "플레이어 신발 밑창에 에테르 오일을 발라 이동 속도 +5% 보너스를 몰래 부여"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_slipstream_rider",
      "name_ko": "슬립스트림 활강 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어가 이동할 때 카엘리우스가 뒤에서 바람을 밀어주어 이동 거리 2배 증가 및 이동 중 기회공격 100% 무시"
    },
    "bond": {
      "tier": 1,
      "current_points": 15,
      "tier_bonuses": {
        "tier_2": "이동 후 첫 공격 치명타율 +15%",
        "tier_3": "합동 연계기 적 넉백 거리 2배",
        "tier_4": "적 공격 회피 시 행동력 1턴 추가",
        "tier_5": "사망 방지 1회 및 파티 전원 회피율 +10%"
      }
    },
    "recruitment": {
      "location_id": "gusting_aerie_cliffs",
      "reputation_min": -20,
      "reputation_max": 80,
      "completed_quest_id": "quest_catch_the_tempest_kite",
      "hire_cost_gold": 110,
      "upkeep_gold_per_day": 8,
      "dialogue_recruit": "땅바닥을 걷는 건 너무 느려터졌어요! 나와 함께 바람을 타고 미끄러져 볼래요?"
    },
    "loot_demands": {
      "gold_share_percent": 12,
      "preferred_item_categories": ["skate_blade", "feather", "oil"],
      "forbidden_item_types": ["heavy_boots"]
    },
    "camp_role": "scout",
    "exploration_talents": ["chasm_gliding", "cliff_wall_skating", "aerial_drop_assault"],
    "companion_relations": {
      "likes": ["companion_zara_sand_dancer"],
      "dislikes": ["companion_baldur_living_mountain"],
      "conflict_event_id": "event_skater_mocks_rock_slowness"
    },
    "combat_skills": [
      {
        "skill_id": "aether_blade_skate_slash",
        "name_ko": "에테르 스케이트 참격",
        "mana_cost": 10,
        "cooldown_turns": 1,
        "effect_type": "high_speed_bleed_slash",
        "description_ko": "적 사이를 미끄러지며 발날로 베어 42의 물리 피해와 2턴간 출혈을 입힙니다."
      },
      {
        "skill_id": "sonic_boom_kickturn",
        "name_ko": "음속 킥턴 충격파",
        "mana_cost": 15,
        "cooldown_turns": 2,
        "effect_type": "aoe_disorient_and_push",
        "description_ko": "급회전하며 발생시킨 충격파로 적 전열을 뒤흔들어 30의 피해와 함께 적중률을 30% 깎습니다."
      }
    ],
    "combo_technique": {
      "combo_id": "whirlwind_dropkick_collision",
      "name_ko": "선풍 낙하 드롭킥",
      "trigger_condition": "player_launches_enemy_into_air",
      "description_ko": "공중에 뜬 적을 활강 가속으로 걷어차 바닥에 내리꽂으며 75의 충격 물리 대미지를 입힙니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_infinite_slipstream_cyclone",
      "name_ko": "무한 활강 난무 폭풍",
      "charge_type": "crit_count",
      "charge_required": 3,
      "mana_cost": 25,
      "activation_voice_line": "눈 깜빡이지 마! 바람보다 빠르게 지나갈 테니까!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 85,
        "stat_scaling": 2.5,
        "status_applied": "airborne_and_armor_shred",
        "status_duration": 2,
        "ally_buff": "party_evasion_up_40"
      },
      "cinematic_description": "전장 전체를 초고속으로 활강하며 수십 번의 교차 발차기로 공중에서 적들을 유린함"
    },
    "party_passive": {
      "buff_id": "slipstream_pace",
      "name_ko": "기류 주행 속도",
      "effect_ko": "던전 탐험 중 파티 이동 속도 25% 상승 및 함정 밟을 확률 50% 감소"
    },
    "equipment": {
      "weapon": "razor_edge_aether_skates",
      "armor": "streamlined_glider_tunic",
      "shield": "none",
      "accessory": "tailwind_crystal_anklet"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 3,
      "downed_cry": "날이… 부러졌어… 속도가… 0이 된다… 구해줘…!",
      "death_trauma_to_party": "파티 이동 속도 30% 영구 저하 및 치명타율 감소"
    },
    "dialogue_lines": {
      "greeting": "슈웅! 방금 내 속도 봤어요? 눈으로 쫓아오기도 힘들었죠?",
      "camp_rest": "스케이트 베어링에 기름칠하는 시간이에요. 멈춰 있으면 왠지 몸이 간지럽단 말이죠.",
      "low_loyalty_warning": "굼벵이처럼 굴면서 사람 부려먹으려 들면 바람처럼 사라져 버릴 거예요.",
      "traitor_reveal": "내 발날이 네 목덜미를 스치고 지나가는 속도를 감상해 봐!",
      "dismissal": "바람이 잘 부는 절벽으로 갑니다. 느림보 씨, 잘 있어요!"
    }
  },
  {
    "companion_id": "companion_tiberius_siege_engineer",
    "name_ko": "티베리우스 폰 바스틴",
    "title_ko": "증기 공성 방패포의 장인",
    "role": "tank",
    "formation": "frontline",
    "speech_style": "stoic_veteran",
    "stats": {
      "level": 12,
      "health": 150,
      "max_health": 150,
      "mana": 30,
      "max_mana": 30,
      "strength": 18,
      "agility": 7,
      "constitution": 18,
      "intelligence": 13,
      "wisdom": 11,
      "luck": 9,
      "defense": 21,
      "attack_power": 24
    },
    "personality": {
      "loyalty_score": 60,
      "affinity": 10,
      "moral_alignment": "lawful_neutral",
      "desire": "과거 제국 내전 때 파괴된 전설의 난공불락 요새 '철벽의 관문' 재건",
      "taboo": "투석기 무단 파괴, 민간인 피난처 포격, 아군 요새 방화",
      "hidden_secret": "자신의 등에 미니 증기 보일러가 이식되어 있어 정기적으로 석탄을 태워야 움직임",
      "betrayal_trigger": "플레이어가 평화 협정 중인 요새에 기습 폭격을 가해 민간인을 학살할 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "요새 결계의 건축 거장 (방어 축조)",
        "trigger_condition": "민간인을 지키는 완벽한 방호벽을 완성하고 공성포를 방어용으로 전환",
        "stat_modifiers": { "defense": 8, "constitution": 4 },
        "unlocked_skill": "skill_impenetrable_steam_bastion",
        "personality_shift": "어떤 공격에도 뚫리지 않는 벽이 되어 아군을 지키는 굳건한 장인"
      },
      "path_b": {
        "branch_name_ko": "초토화 공성 파괴관 (초토화 포격)",
        "trigger_condition": "방패포의 리미터를 해제하고 도시 전체를 평지로 만드는 파괴 병기 개조",
        "stat_modifiers": { "attack_power": 14, "defense": -2 },
        "unlocked_skill": "skill_apocalyptic_siege_bombardment",
        "personality_shift": "적의 모든 성벽과 거점을 흔적도 없이 갈아버리는 냉혹한 포격관"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "boiler_overheat_steam_vent",
      "flaw_name_ko": "보일러 과열 화상 발작",
      "trigger_condition": "combat_turns_reach_6",
      "effect_ko": "증기 압력 누출로 체력 20 자해 피해 및 1턴간 방패 방어 불가"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 성채 요새화 및 공성 대포 설치",
      "effect_ko": "거점 방어 전투 시 포격 지원으로 적 병력 50% 자동 섬멸"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 90,
      "boss_focus_weight": 40,
      "crowd_control_weight": 70,
      "self_preservation_weight": 20
    },
    "inventory_quirks": {
      "quirk_type": "hoard_coal_for_boiler",
      "description_ko": "플레이어 가방의 목재와 가연성 잡템을 보일러용 '고열 석탄'으로 압축 변환"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_iron_trench_line",
      "name_ko": "철벽 참호선 결속 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어가 티베리우스 바로 뒤 칸에 위치할 경우 모든 광역/원거리 피해 80% 고정 경감"
    },
    "bond": {
      "tier": 1,
      "current_points": 20,
      "tier_bonuses": {
        "tier_2": "방패 전개 시 파티원 방어력 +3",
        "tier_3": "합동 연계기 화상 도트 대미지 30% 증가",
        "tier_4": "적 물리 공격 피격 시 30% 증기 반격",
        "tier_5": "사망 방지 1회 및 거대 방패 방벽 완전 무적(1턴)"
      }
    },
    "recruitment": {
      "location_id": "ruined_iron_fortress",
      "reputation_min": 10,
      "reputation_max": 90,
      "completed_quest_id": "quest_repair_siege_boiler",
      "hire_cost_gold": 130,
      "upkeep_gold_per_day": 10,
      "dialogue_recruit": "견고한 벽 없이는 승리도 없습니다. 내 증기 방패포가 당신의 전선을 지탱할 것입니다."
    },
    "loot_demands": {
      "gold_share_percent": 15,
      "preferred_item_categories": ["heavy_plate", "cannonball", "coal"],
      "forbidden_item_types": []
    },
    "camp_role": "blacksmith",
    "exploration_talents": ["fortification_breaching", "heavy_door_demolition", "structural_load_analysis"],
    "companion_relations": {
      "likes": ["companion_torvald_ironbreaker"],
      "dislikes": ["companion_vane_shadowfang"],
      "conflict_event_id": "event_engineer_scolds_rogue_cowardice"
    },
    "combat_skills": [
      {
        "skill_id": "steam_cannon_blast",
        "name_ko": "방패 매립 증기포 사격",
        "mana_cost": 12,
        "cooldown_turns": 1,
        "effect_type": "aoe_burn_and_knockback",
        "description_ko": "방패 중앙의 포문에서 증기 탄환을 쏴 전열에 38의 화염 피해와 1칸 밀쳐냄을 줍니다."
      },
      {
        "skill_id": "deploy_trench_barrier",
        "name_ko": "강철 참호 방벽 전개",
        "mana_cost": 18,
        "cooldown_turns": 3,
        "effect_type": "party_cover_buff",
        "description_ko": "거대 방패를 땅에 박아 2턴간 뒤편 아군 전체의 받는 피해를 40% 경감시킵니다."
      }
    ],
    "combo_technique": {
      "combo_id": "bunker_buster_crossfire",
      "name_ko": "벙커 버스터 협공 포격",
      "trigger_condition": "player_uses_explosive_or_fire_skill",
      "description_ko": "플레이어의 폭발 지점에 방패포 영거리 사격을 꽂아 넣어 75의 방어 무시 복합 피해를 입힙니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_iron_fortress_grand_barrage",
      "name_ko": "철벽 요새 결전 일제포격",
      "charge_type": "damage_accumulated",
      "charge_required": 100,
      "mana_cost": 30,
      "activation_voice_line": "압력 밸브 완전 개방! 전 포문, 일제 사격 개시!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 92,
        "stat_scaling": 2.3,
        "status_applied": "heavy_burn_and_stun",
        "status_duration": 2,
        "ally_buff": "party_armor_up_8"
      },
      "cinematic_description": "방패를 거대 요새 포탑으로 변형시켜 전장에 무차별 증기 유탄 폭격을 쏟아부음"
    },
    "party_passive": {
      "buff_id": "siege_discipline",
      "name_ko": "공성 방어진형 규율",
      "effect_ko": "파티 전체 광역 폭발 및 마법 피해 20% 상시 경감"
    },
    "equipment": {
      "weapon": "steam_cannon_integrated_tower_shield",
      "armor": "heavy_cast_iron_siege_armor",
      "shield": "none",
      "accessory": "pressure_gauge_amulet"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 3,
      "downed_cry": "보일러가… 폭발한다… 벽을… 사수하라…!",
      "death_trauma_to_party": "파티 방어력 -5 영구 감소 및 공성 무기 사용 불가"
    },
    "dialogue_lines": {
      "greeting": "치익… 압력 게이지 양호. 전선을 구축할 위치를 지정하십시오.",
      "camp_rest": "장작불 곁에서 보일러 밸브를 조이는 건 하루 중 가장 차분한 시간입니다.",
      "low_loyalty_warning": "명령에 규율이 없군요. 방패를 거두고 진지를 철수할 수 있습니다.",
      "traitor_reveal": "비겁한 반역자에게는 120구경 증기포가 약이다.",
      "dismissal": "요새 재건 현장으로 복귀합니다. 방벽을 튼튼히 쌓으십시오."
    }
  },
  {
    "companion_id": "companion_sylvia_thorn_weaver",
    "name_ko": "실비아 브라이어하트",
    "title_ko": "가시덩굴을 엮는 핏빛 식물술사",
    "role": "arcane_blaster",
    "formation": "midline",
    "speech_style": "archaic_noble",
    "stats": {
      "level": 11,
      "health": 85,
      "max_health": 85,
      "mana": 80,
      "max_mana": 80,
      "strength": 9,
      "agility": 14,
      "constitution": 11,
      "intelligence": 18,
      "wisdom": 15,
      "luck": 11,
      "defense": 10,
      "attack_power": 31
    },
    "personality": {
      "loyalty_score": 45,
      "affinity": 5,
      "moral_alignment": "neutral_evil",
      "desire": "과거 자신을 제물로 바치려 했던 고향 숲의 '부패한 장로 나무'를 가시로 질식사시키기",
      "taboo": "장미 덩굴 훼손, 맹독 가시 무단 절단, 꽃밭 짓밟기",
      "hidden_secret": "자신의 심장 혈관에 가시덩굴 줄기가 얽혀 있어 분노할 때마다 피부 위로 가시가 돋아남",
      "betrayal_trigger": "플레이어가 고향 장로 나무의 편을 들고 실비아를 결박하려 할 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "달빛 장미의 정원사 (정화 개화)",
        "trigger_condition": "복수심을 내려놓고 가시덩굴을 상처를 감싸는 치유의 은빛 장미로 정화",
        "stat_modifiers": { "wisdom": 6, "intelligence": 4 },
        "unlocked_skill": "skill_lunar_rose_sanctuary",
        "personality_shift": "아름다운 꽃과 가시로 약자를 보호하는 우아한 귀부인"
      },
      "path_b": {
        "branch_name_ko": "핏빛 가시나무 마녀 (흡혈 교살)",
        "trigger_condition": "장로 나무를 짓이기고 숲의 모든 생명력을 빨아들여 가시 괴수화",
        "stat_modifiers": { "attack_power": 14, "constitution": -4 },
        "unlocked_skill": "skill_bloodthorn_choking_jungle",
        "personality_shift": "모든 인간을 자신의 가시 정원에 줄 비료로 보는 잔혹한 마녀"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "herbicide_chemical_choke",
      "flaw_name_ko": "제초제 살포 질식 발작",
      "trigger_condition": "poison_gas_or_chemical_smoke_encountered",
      "effect_ko": "가시 줄기가 시들어 2턴간 마나 소모량 2배 증가 및 행동력 저하"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 가시 덤불 방벽 조성 및 독초 재배",
      "effect_ko": "거점 침입 적 30% 독 데미지 사전 피격 및 주간 맹독 추출액 3병 획득"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 30,
      "boss_focus_weight": 60,
      "crowd_control_weight": 85,
      "self_preservation_weight": 50
    },
    "inventory_quirks": {
      "quirk_type": "weave_thorns_into_armor",
      "description_ko": "플레이어 옷 솔기에 가시를 엮어 피격 시 공격자에게 5 반사 피해를 주도록 개조"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_briar_thorn_retaliation",
      "name_ko": "가시덤불 복수 결속 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어가 근접 공격을 받을 때마다 실비아의 가시가 솟구쳐 공격자에게 입은 피해의 50%를 출혈 반사"
    },
    "bond": {
      "tier": 1,
      "current_points": 15,
      "tier_bonuses": {
        "tier_2": "속박된 적 대상 마법 관통력 +15%",
        "tier_3": "합동 연계기 출혈 턴수 +1턴",
        "tier_4": "적 처치 시 가시 방어막 +15 획득",
        "tier_5": "사망 방지 1회 및 가시 반사 피해 2배 증폭"
      }
    },
    "recruitment": {
      "location_id": "crimson_rose_briar_maze",
      "reputation_min": -40,
      "reputation_max": 60,
      "completed_quest_id": "quest_prune_the_crying_tree",
      "hire_cost_gold": 110,
      "upkeep_gold_per_day": 8,
      "dialogue_recruit": "가시 없는 장미는 꺾이기 마련이죠. 제 가시가 당신의 적들을 옭아매 드릴게요."
    },
    "loot_demands": {
      "gold_share_percent": 12,
      "preferred_item_categories": ["seed", "thorn", "blood_essence"],
      "forbidden_item_types": ["axe", "weedkiller"]
    },
    "camp_role": "scholar",
    "exploration_talents": ["brier_clearing", "plant_toxin_harvesting", "jungle_pathfinding"],
    "companion_relations": {
      "likes": ["companion_morrigan_crow"],
      "dislikes": ["companion_lyra_dawnbringer"],
      "conflict_event_id": "event_thorn_weaver_scorns_priestess"
    },
    "combat_skills": [
      {
        "skill_id": "briar_constriction_vine",
        "name_ko": "가시덤불 교살 덩굴",
        "mana_cost": 16,
        "cooldown_turns": 1,
        "effect_type": "root_and_bleed",
        "description_ko": "땅에서 솟아난 가시 덩굴로 적 1명을 묶어 35의 피해와 2턴간 속박 및 출혈을 겁니다."
      },
      {
        "skill_id": "crimson_petal_razor_flurry",
        "name_ko": "핏빛 꽃잎 칼날 돌풍",
        "mana_cost": 22,
        "cooldown_turns": 3,
        "effect_type": "aoe_piercing_bleed",
        "description_ko": "면도날 꽃잎을 날려 적 전체에 32의 관통 물리 피해를 입히고 명중률을 20% 깎습니다."
      }
    ],
    "combo_technique": {
      "combo_id": "thorn_entangle_execution",
      "name_ko": "가시 속박 참살격",
      "trigger_condition": "player_stuns_or_knocks_down_enemy",
      "description_ko": "넘어진 적의 온몸을 가시 덩굴로 휘감아 바닥으로 끌어당기며 70의 심장 관통 피해를 입힙니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_garden_of_thousand_thorns",
      "name_ko": "만인 교살의 가시 정원",
      "charge_type": "morale_and_damage",
      "charge_required": 100,
      "mana_cost": 40,
      "activation_voice_line": "가시 속에서 피어나라! 영원한 고통의 정원이여!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 78,
        "stat_scaling": 2.2,
        "status_applied": "unbreakable_choke_root",
        "status_duration": 2,
        "ally_buff": "party_thorn_reflect_20"
      },
      "cinematic_description": "전장 전체에서 거대한 핏빛 가시나무들이 솟구쳐 적들의 사지를 꿰뚫고 공중에 매달아버림"
    },
    "party_passive": {
      "buff_id": "thorn_carapace",
      "name_ko": "가시 갑각",
      "effect_ko": "파티원 전체 근접 피격 시 공격자에게 10의 고정 가시 반사 피해"
    },
    "equipment": {
      "weapon": "whip_of_living_rose_thorns",
      "armor": "silk_thorn_embroidered_gown",
      "shield": "none",
      "accessory": "everblooming_blood_rose"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 2,
      "downed_cry": "가시가… 내 심장을 파고들어… 줄기가… 꺾인다…!",
      "death_trauma_to_party": "파티 반사 피해 능력 영구 상실 및 출혈 저항력 저하"
    },
    "dialogue_lines": {
      "greeting": "장미 향기가 나나요? 조심하세요, 가시에 찔리면 피가 멈추지 않으니까요.",
      "camp_rest": "장작불에 가시 줄기를 말리는 중이에요. 타닥거리는 소리가 뼈 부러지는 소리 같아 즐겁네요.",
      "low_loyalty_warning": "제 정원의 비료가 되고 싶지 않다면 그 무례한 태도를 고치시는 게 좋을 거예요.",
      "traitor_reveal": "당신의 목에 가시덩굴을 감아 가장 아름다운 장미를 피워내 드리죠.",
      "dismissal": "장미 미로로 돌아갑니다. 가시에 찔리지 않게 조심해서 가세요."
    }
  },
  {
    "companion_id": "companion_kazimir_shadow_assassin",
    "name_ko": "카지미르 벨몬트",
    "title_ko": "그림자 잠수의 암살도사",
    "role": "scout_rogue",
    "formation": "frontline",
    "speech_style": "rough_mercenary",
    "stats": {
      "level": 12,
      "health": 92,
      "max_health": 92,
      "mana": 35,
      "max_mana": 35,
      "strength": 12,
      "agility": 19,
      "constitution": 12,
      "intelligence": 13,
      "wisdom": 11,
      "luck": 16,
      "defense": 12,
      "attack_power": 30
    },
    "personality": {
      "loyalty_score": 40,
      "affinity": 0,
      "moral_alignment": "chaotic_neutral",
      "desire": "자신의 몸을 평생 먹어치우는 '그림자 저주'를 풀고 빛 아래서 편히 잠들기",
      "taboo": "햇빛 반사경으로 눈 비추기, 그림자 속에서 은신한 동료 배신",
      "hidden_secret": "자신의 발밑 그림자가 본체와 별개로 자아를 가진 그림자 마수 형태임",
      "betrayal_trigger": "플레이어가 빛 마법 유물로 카지미르의 그림자를 강제로 불태우려 할 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "새벽을 걷는 그림자 파수꾼 (공존)",
        "trigger_condition": "그림자 마수와 화해하고 빛과 어둠의 균형을 이루는 은신술 완성",
        "stat_modifiers": { "agility": 6, "wisdom": 4 },
        "unlocked_skill": "skill_twilight_shadow_stride",
        "personality_shift": "어둠 속에 숨어 빛을 지키는 묵묵하고 충직한 파수꾼"
      },
      "path_b": {
        "branch_name_ko": "심연의 그림자 포식마 (그림자 침식)",
        "trigger_condition": "그림자 마수에게 영혼을 완전히 넘겨주고 적들의 그림자를 뜯어먹는 괴수화",
        "stat_modifiers": { "attack_power": 14, "defense": -4 },
        "unlocked_skill": "skill_abyssal_shadow_devour",
        "personality_shift": "적의 그림자를 밟아 영혼을 질식시키는 잔혹한 그림자 괴물"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "total_darkness_blind_fear",
      "flaw_name_ko": "완전 암흑 속 자아 붕괴",
      "trigger_condition": "ambient_light_reaches_zero_without_torches",
      "effect_ko": "그림자가 통제를 잃고 아군을 무작위로 공격하는 광란 2턴 발동"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "적 요새 비밀 지하 잠입 및 설계도 탈취",
      "effect_ko": "던전 보스 약점 데이터 100% 사전 입수 및 보물상자 함정 사전 해제"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 15,
      "boss_focus_weight": 85,
      "crowd_control_weight": 45,
      "self_preservation_weight": 70
    },
    "inventory_quirks": {
      "quirk_type": "hide_items_in_shadows",
      "description_ko": "플레이어 가방의 귀중품을 그림자 차원에 숨겨 도난/압류를 100% 방지"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_shadow_meld_escape",
      "name_ko": "그림자 동화 탈출 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어가 치명상을 입는 순간 카지미르의 그림자 속으로 1턴간 흡수되어 완전 무적 상태로 회피"
    },
    "bond": {
      "tier": 1,
      "current_points": 10,
      "tier_bonuses": {
        "tier_2": "그림자 은신 중 이동력 +2칸",
        "tier_3": "합동 연계기 실명 지속 +1턴",
        "tier_4": "치명타 적중 시 1턴간 완전 회피 버프",
        "tier_5": "사망 방지 1회 및 백스탭 피해량 +40%"
      }
    },
    "recruitment": {
      "location_id": "sunless_abyssal_chasm",
      "reputation_min": -50,
      "reputation_max": 50,
      "completed_quest_id": "quest_tame_the_living_shadow",
      "hire_cost_gold": 120,
      "upkeep_gold_per_day": 9,
      "dialogue_recruit": "네 등 뒤의 그림자 속을 봐라. 난 이미 거기 있었다. 얼마를 줄 텐가?"
    },
    "loot_demands": {
      "gold_share_percent": 15,
      "preferred_item_categories": ["dagger", "shadow_gem", "poison"],
      "forbidden_item_types": ["flashbang", "sun_stone"]
    },
    "camp_role": "scout",
    "exploration_talents": ["shadow_swimming", "silent_step", "locked_chest_shadow_bypass"],
    "companion_relations": {
      "likes": ["companion_vane_shadowfang"],
      "dislikes": ["companion_lyra_dawnbringer"],
      "conflict_event_id": "event_shadow_assassin_hates_sun_priestess"
    },
    "combat_skills": [
      {
        "skill_id": "shadow_dive_backstab",
        "name_ko": "그림자 잠수 암살격",
        "mana_cost": 12,
        "cooldown_turns": 1,
        "effect_type": "teleport_backstab_damage",
        "description_ko": "적의 그림자 속으로 다이빙해 등 뒤로 솟구치며 44의 관통 피해와 출혈을 입힙니다."
      },
      {
        "skill_id": "shadow_pin_shackle",
        "name_ko": "그림자 못 박기",
        "mana_cost": 16,
        "cooldown_turns": 3,
        "effect_type": "shadow_root_and_silence",
        "description_ko": "적의 그림자에 단검을 꽂아 2턴간 이동과 스킬 사용을 완전히 봉쇄합니다."
      }
    ],
    "combo_technique": {
      "combo_id": "dual_shadow_pincer_sever",
      "name_ko": "양면 그림자 협공 절단",
      "trigger_condition": "player_attacks_from_behind",
      "description_ko": "플레이어가 적의 뒤를 노릴 때 바닥 그림자에서 솟구쳐 목덜미를 교차 베기하여 74의 치명타를 입힙니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_abyssal_shadow_carnage",
      "name_ko": "심연 그림자 대도살",
      "charge_type": "crit_count",
      "charge_required": 3,
      "mana_cost": 25,
      "activation_voice_line": "네 그림자가 널 집어삼킬 것이다. 영원히 어둠 속에 잠들어라.",
      "effects": {
        "target": "all_enemies",
        "base_damage": 82,
        "stat_scaling": 2.4,
        "status_applied": "mass_blind_and_heavy_bleed",
        "status_duration": 2,
        "ally_buff": "party_stealth_for_1_turn"
      },
      "cinematic_description": "적들의 발밑 그림자들이 거대한 칼날 손으로 변해 일제히 목을 꺾어버리는 암살 연출"
    },
    "party_passive": {
      "buff_id": "shadow_cloak_shroud",
      "name_ko": "그림자 망토 장막",
      "effect_ko": "파티 전체가 어두운 지형에서 치명타 확률 +10% 및 피격 회피율 +15%"
    },
    "equipment": {
      "weapon": "shadow_infused_obsidian_stiletto",
      "armor": "abyssal_silk_stealth_cloak",
      "shield": "none",
      "accessory": "ring_of_the_living_shadow"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 3,
      "downed_cry": "그림자가… 날 삼킨다… 빛을… 비추지 마… 크흑!",
      "death_trauma_to_party": "파티 은신 성공률 50% 영구 저하 및 기습 피격 확률 증가"
    },
    "dialogue_lines": {
      "greeting": "쉿, 발소리 내지 마라. 그림자가 네 말을 엿듣고 있다.",
      "camp_rest": "모닥불 불빛에서 한 걸음 물러나 있는 게 편해. 그림자가 너무 짙어지면 곤란하거든.",
      "low_loyalty_warning": "빛에 눈이 멀어 실수를 연발한다면 네 목에 단검을 박고 사라지겠다.",
      "traitor_reveal": "네 그림자는 이제 내 것이다. 심장을 멈춰주마.",
      "dismissal": "어둠 속으로 꺼진다. 뒤돌아보지 마라."
    }
  },
  {
    "companion_id": "companion_freya_spirit_drummer",
    "name_ko": "프레이야 룬스트라이크",
    "title_ko": "전장의 심장을 치는 북잡이",
    "role": "healer_support",
    "formation": "midline",
    "speech_style": "rough_mercenary",
    "stats": {
      "level": 11,
      "health": 115,
      "max_health": 115,
      "mana": 55,
      "max_mana": 55,
      "strength": 15,
      "agility": 12,
      "constitution": 16,
      "intelligence": 11,
      "wisdom": 15,
      "luck": 13,
      "defense": 14,
      "attack_power": 22
    },
    "personality": {
      "loyalty_score": 60,
      "affinity": 15,
      "moral_alignment": "chaotic_good",
      "desire": "전쟁에서 전사한 부족 영령 1만 명의 넋을 달래는 '최후의 영혼 진혼곡' 연주",
      "taboo": "전쟁터의 북 찢기, 항복한 군악대 학살, 거짓된 패전 선동",
      "hidden_secret": "자신의 북 가죽이 과거 자신을 구하고 전사한 수호 마수의 가죽으로 만들어짐",
      "betrayal_trigger": "플레이어가 부족의 성스러운 전쟁 북을 전리품으로 부수거나 조롱할 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "영령의 진혼 대악장 (영혼 승천)",
        "trigger_condition": "전쟁터의 모든 망령을 진혼곡으로 성불시키고 평화의 축제 북소리 연주",
        "stat_modifiers": { "wisdom": 7, "constitution": 4 },
        "unlocked_skill": "skill_hymn_of_ancestral_peace",
        "personality_shift": "아군의 사기를 드높이고 망자를 위로하는 숭고한 영혼의 어머니"
      },
      "path_b": {
        "branch_name_ko": "피의 광란 군악대장 (광란 고취)",
        "trigger_condition": "북소리로 아군과 영령들을 통제 불능의 피의 광란 상태로 몰아넣어 적 전멸",
        "stat_modifiers": { "attack_power": 12, "strength": 4 },
        "unlocked_skill": "skill_blood_frenzy_war_drum",
        "personality_shift": "오직 적을 찢어 죽이는 북소리에만 도취된 피의 광전사 고취자"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "torn_drumhead_despair",
      "flaw_name_ko": "북 가죽 파손 절망 패닉",
      "trigger_condition": "critical_hit_taken_from_boss",
      "effect_ko": "북이 상할까 두려워 1턴간 모든 스킬 봉인 및 방어 태세만 유지"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 군악 훈련 및 사기 고취",
      "effect_ko": "거점 소속 전 병력 공격력 +20% 및 사기 저하로 인한 탈영율 0%"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 55,
      "boss_focus_weight": 35,
      "crowd_control_weight": 65,
      "self_preservation_weight": 35
    },
    "inventory_quirks": {
      "quirk_type": "carve_bone_drumsticks",
      "description_ko": "처치한 괴수의 뼈를 깎아 파티 사기를 올려주는 '진혼의 뼈 북채'로 제작"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_war_beat_heart_link",
      "name_ko": "전장의 심장 고동 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "프레이야가 북을 칠 때마다 플레이어의 공격 속도와 행동력이 가속되어 턴당 1회 추가 기본 공격 무료 발동"
    },
    "bond": {
      "tier": 1,
      "current_points": 20,
      "tier_bonuses": {
        "tier_2": "북소리 버프 지속 턴수 +1턴",
        "tier_3": "합동 연계기 기절 성공률 +25%",
        "tier_4": "파티 사기 최대치 도달 시 공격력 +15%",
        "tier_5": "사망 방지 1회 및 체력 0 도달 시 불사 북소리 1턴 발동"
      }
    },
    "recruitment": {
      "location_id": "ancestral_war_tumulus",
      "reputation_min": 0,
      "reputation_max": 90,
      "completed_quest_id": "quest_restring_spirit_drum",
      "hire_cost_gold": 90,
      "upkeep_gold_per_day": 7,
      "dialogue_recruit": "둥! 둥! 내 북소리가 들리나? 심장이 뛰는 녀석이라면 내 박자에 맞춰 검을 휘둘러라!"
    },
    "loot_demands": {
      "gold_share_percent": 10,
      "preferred_item_categories": ["drum", "horn", "beast_bone"],
      "forbidden_item_types": []
    },
    "camp_role": "cook",
    "exploration_talents": ["battlefield_morale_boost", "ancestor_spirit_communing", "wild_beast_scaring"],
    "companion_relations": {
      "likes": ["companion_kazan_ashwalker"],
      "dislikes": ["companion_nyx_dream_weaver"],
      "conflict_event_id": "event_drummer_wakes_sleepwalker"
    },
    "combat_skills": [
      {
        "skill_id": "drumbeat_of_fury",
        "name_ko": "분노의 진격 북소리",
        "mana_cost": 15,
        "cooldown_turns": 2,
        "effect_type": "party_attack_and_speed_buff",
        "description_ko": "북을 울려 2턴간 파티 전원의 공격력을 25% 상승시키고 행동 순서를 앞당깁니다."
      },
      {
        "skill_id": "concussive_spirit_shockwave",
        "name_ko": "영령의 공명 충격파",
        "mana_cost": 18,
        "cooldown_turns": 3,
        "effect_type": "aoe_interrupt_and_damage",
        "description_ko": "거대한 영혼 북을 쳐서 적 전열에 32의 음파 피해를 입히고 영창 중인 스킬을 강제 캔슬시킵니다."
      }
    ],
    "combo_technique": {
      "combo_id": "heartbeat_thunder_strike",
      "name_ko": "심장 박동 벼락 강타",
      "trigger_condition": "player_uses_heavy_smash_attack",
      "description_ko": "플레이어가 내려찍는 타이밍에 맞춰 북을 강타해 벼락 충격파를 폭발시키며 72의 광역 스턴 피해를 입힙니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_march_of_the_ten_thousand_ancestors",
      "name_ko": "1만 영령의 진격 진혼곡",
      "charge_type": "morale_and_damage",
      "charge_required": 100,
      "mana_cost": 35,
      "activation_voice_line": "선조들이여 깨어나라! 이 북소리와 함께 승리를 쟁취하라! 둥!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 75,
        "stat_scaling": 2.2,
        "status_applied": "mass_morale_break_and_fear",
        "status_duration": 2,
        "ally_buff": "full_party_heal_40_and_attack_up_30"
      },
      "cinematic_description": "하늘에서 수천 명의 영령 전사들이 북소리에 맞춰 함성을 지르며 적진을 짓밟고 아군을 치료함"
    },
    "party_passive": {
      "buff_id": "unwavering_tempo",
      "name_ko": "흔들리지 않는 박자",
      "effect_ko": "파티 전체 공포/혼란 상태이상 100% 면역 및 사기 저하 면역"
    },
    "equipment": {
      "weapon": "thunderous_spirit_war_drum",
      "armor": "beast_hide_tribal_vestments",
      "shield": "none",
      "accessory": "mammoth_bone_drumstick"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 3,
      "downed_cry": "북이… 찢어졌어… 심장이… 멈추려 한다… 박자를… 이어줘…!",
      "death_trauma_to_party": "파티 사기 즉시 0으로 추락 및 공격력 20% 영구 저하"
    },
    "dialogue_lines": {
      "greeting": "둥! 오늘도 심장이 힘차게 뛰고 있나? 북채를 쥐면 피가 솟구치지!",
      "camp_rest": "불꽃 앞에서 북을 조율할 때가 제일 좋아. 영령들이 따뜻하다고 속삭이거든.",
      "low_loyalty_warning": "비겁하게 뒤로 빠지는 놈에게 쳐줄 북소리는 없다. 똑바로 싸워라.",
      "traitor_reveal": "선조들의 북소리가 널 찢어 죽이라 명한다. 대가를 치러라!",
      "dismissal": "부족의 무덤으로 돌아간다. 북소리가 필요하면 찾아와라."
    }
  },
  {
    "companion_id": "companion_malik_dune_sniper",
    "name_ko": "말릭 샌드스토커",
    "title_ko": "신기루 속의 모래장총 저격수",
    "role": "dps_ranged",
    "formation": "backline",
    "speech_style": "stoic_veteran",
    "stats": {
      "level": 12,
      "health": 86,
      "max_health": 86,
      "mana": 40,
      "max_mana": 40,
      "strength": 11,
      "agility": 19,
      "constitution": 11,
      "intelligence": 13,
      "wisdom": 16,
      "luck": 14,
      "defense": 11,
      "attack_power": 33
    },
    "personality": {
      "loyalty_score": 55,
      "affinity": 10,
      "moral_alignment": "neutral_good",
      "desire": "사막 무역로를 위협하는 전설의 괴수 '모래벌레 대황제'를 1km 밖에서 원샷 원킬로 사냥",
      "taboo": "조준경 강제 파손, 탄약 낭비, 비무장 상단 약탈",
      "hidden_secret": "오른쪽 눈이 모래 먼지를 꿰뚫어 보는 '매의 마안 의안'으로 개조되어 있음",
      "betrayal_trigger": "플레이어가 사막 상단을 습격해 무고한 상인들의 눈을 멀게 할 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "사막의 천리안 수호자 (정밀 감시관)",
        "trigger_condition": "모래벌레를 무역로 밖으로 몰아내고 상단들을 지키는 파수꾼으로 정착",
        "stat_modifiers": { "agility": 6, "wisdom": 4 },
        "unlocked_skill": "skill_mirage_penetrating_hyper_shot",
        "personality_shift": "보이지 않는 곳에서 전우를 지키는 과묵하고 든든한 저격수"
      },
      "path_b": {
        "branch_name_ko": "침묵의 모래바람 암살저격관 (헤드샷 사냥꾼)",
        "trigger_condition": "모래벌레의 심장을 뚫고 그 피로 탄환을 코팅해 보이지 않는 학살자로 변모",
        "stat_modifiers": { "attack_power": 14, "defense": -4 },
        "unlocked_skill": "skill_guaranteed_headshot_obliteration",
        "personality_shift": "오직 적의 머리통이 터지는 순간의 반동에만 희열을 느끼는 냉혈한"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "ocular_lens_dust_blindness",
      "flaw_name_ko": "의안 렌즈 과열 마비",
      "trigger_condition": "continuous_firing_3_turns_in_a_row",
      "effect_ko": "의안 렌즈 과열로 1턴간 시야 상실 및 명중률 50% 급감"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 초원거리 망루 저격 경계",
      "effect_ko": "거점 반경 5km 내 적 사전 저격으로 침입 적 부대 병력 40% 삭감"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 20,
      "boss_focus_weight": 95,
      "crowd_control_weight": 30,
      "self_preservation_weight": 60
    },
    "inventory_quirks": {
      "quirk_type": "craft_high_velocity_rounds",
      "description_ko": "플레이어 가방의 화약과 납을 소모해 방어 무시 '초고속 철갑탄'으로 제작"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_spotter_sniper_synchrony",
      "name_ko": "관측수-저격수 동기화 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어가 지정한 적 단일 대상에게 말릭의 모든 저격 공격이 100% 확정 치명타로 적중"
    },
    "bond": {
      "tier": 1,
      "current_points": 15,
      "tier_bonuses": {
        "tier_2": "저격 사거리 +2칸 확장",
        "tier_3": "합동 연계기 방어력 관통 50%",
        "tier_4": "치명타 적중 시 적 1턴간 실명 확정",
        "tier_5": "사망 방지 1회 및 보스 대상 피해량 +30%"
      }
    },
    "recruitment": {
      "location_id": "dune_crest_outpost",
      "reputation_min": 0,
      "reputation_max": 90,
      "completed_quest_id": "quest_calibrate_hawk_eye_lens",
      "hire_cost_gold": 120,
      "upkeep_gold_per_day": 8,
      "dialogue_recruit": "거리 800미터, 풍속 3노트. 당신이 표적을 가리키면 심장을 뚫어드리죠."
    },
    "loot_demands": {
      "gold_share_percent": 12,
      "preferred_item_categories": ["gunpowder", "rifle_parts", "lens"],
      "forbidden_item_types": []
    },
    "camp_role": "scout",
    "exploration_talents": ["extreme_range_spotting", "thermal_footprint_tracking", "sniper_nest_camouflaging"],
    "companion_relations": {
      "likes": ["companion_zephyr_windstrider"],
      "dislikes": ["companion_garrick_chain_breaker"],
      "conflict_event_id": "event_sniper_scolds_brawler_recklessness"
    },
    "combat_skills": [
      {
        "skill_id": "armor_piercing_dune_shot",
        "name_ko": "사구 관통 철갑탄",
        "mana_cost": 14,
        "cooldown_turns": 1,
        "effect_type": "extreme_single_damage",
        "description_ko": "후열에서 적 보스의 급소를 저격하여 48의 방어 무시 관통 물리 피해를 입힙니다."
      },
      {
        "skill_id": "smoke_screen_relocation",
        "name_ko": "모래 연막 저격진지 이동",
        "mana_cost": 12,
        "cooldown_turns": 3,
        "effect_type": "stealth_and_buff",
        "description_ko": "연막을 터뜨리고 사각으로 이동하여 은신을 얻고 다음 공격 치명타율을 100%로 만듭니다."
      }
    ],
    "combo_technique": {
      "combo_id": "laser_mark_sniper_execution",
      "name_ko": "표적 지시 일격필살",
      "trigger_condition": "player_marks_or_stuns_boss_enemy",
      "description_ko": "플레이어가 자세를 무너뜨린 적의 미간에 대구경 탄환을 정확히 박아 넣어 85의 즉사급 피해를 가합니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_one_shot_one_kill_mirage",
      "name_ko": "신기루의 일격필살 참영탄",
      "charge_type": "crit_count",
      "charge_required": 3,
      "mana_cost": 30,
      "activation_voice_line": "호흡을 멈춰라. 탄환이 네 운명을 결정짓는다. 격발.",
      "effects": {
        "target": "single_boss",
        "base_damage": 140,
        "stat_scaling": 2.8,
        "status_applied": "instant_heavy_bleed_and_paralysis",
        "status_duration": 2,
        "ally_buff": "none"
      },
      "cinematic_description": "탄환의 시점으로 시간이 느려지며 바람과 모래를 뚫고 적 보스의 심장을 꿰뚫는 슬로우 모션 연출"
    },
    "party_passive": {
      "buff_id": "eagle_eye_vantage",
      "name_ko": "매의 눈 조준망",
      "effect_ko": "파티 전체 원거리 공격 사거리 +1 및 치명타 확률 +6%"
    },
    "equipment": {
      "weapon": "long_barrel_sand_anti_materiel_rifle",
      "armor": "ghillie_dune_camo_cloak",
      "shield": "none",
      "accessory": "hawk_eye_calibrated_monocle"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 3,
      "downed_cry": "조준경이… 깨졌어… 시야가… 캄캄하다… 후퇴하라…!",
      "death_trauma_to_party": "파티 원거리 명중률 25% 영구 저하 및 치명타 피해량 감소"
    },
    "dialogue_lines": {
      "greeting": "사격선 안으로 들어오지 마십시오. 방아쇠에 손이 올라가 있습니다.",
      "camp_rest": "장작불 연기 방향을 보면 내일 바람의 세기를 계산할 수 있습니다. 훌륭한 사격 날씨가 되겠군요.",
      "low_loyalty_warning": "표적도 제대로 못 잡는 지휘관을 위해 낭비할 탄약은 없습니다.",
      "traitor_reveal": "1,000미터 밖에서 네 미간을 뚫어주마. 도망쳐 봐라.",
      "dismissal": "모래 언덕으로 돌아갑니다. 고개 숙이고 다니십시오."
    }
  },
  {
    "companion_id": "companion_vanya_abyssal_leech",
    "name_ko": "바냐 그림리치",
    "title_ko": "거머리 사역의 심연 치유사",
    "role": "healer_support",
    "formation": "midline",
    "speech_style": "timid_scholar",
    "stats": {
      "level": 11,
      "health": 82,
      "max_health": 82,
      "mana": 78,
      "max_mana": 78,
      "strength": 7,
      "agility": 13,
      "constitution": 12,
      "intelligence": 17,
      "wisdom": 16,
      "luck": 11,
      "defense": 10,
      "attack_power": 21
    },
    "personality": {
      "loyalty_score": 45,
      "affinity": 0,
      "moral_alignment": "neutral_evil",
      "desire": "세상의 모든 독과 질병을 거머리의 몸에 농축시켜 '만병을 정화하는 황금 거머리 여왕' 탄생",
      "taboo": "소금 뿌리기, 거머리 항아리 고의 파쇄, 불로 소독하기",
      "hidden_secret": "자신의 팔뚝 안쪽에 수십 마리의 거머리가 기생하며 혈액 순환을 대신 돕고 있음",
      "betrayal_trigger": "플레이어가 바냐의 거머리 배양 항아리에 소금을 쏟아붓고 짓밟을 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "정혈의 심연 의학자 (독소 흡수)",
        "trigger_condition": "거머리를 활용해 민간인들의 불치병과 역병 독소를 완전히 흡수해 치료",
        "stat_modifiers": { "wisdom": 7, "constitution": 4 },
        "unlocked_skill": "skill_golden_leech_miracle_purification",
        "personality_shift": "기괴한 생물로 인류의 고통을 덜어주는 헌신적인 의학자"
      },
      "path_b": {
        "branch_name_ko": "피를 마시는 심연의 거머리 군주 (흡혈 군체)",
        "trigger_condition": "거머리들에게 살아있는 적의 내장을 파먹게 훈련시켜 거대 흡혈 마수화",
        "stat_modifiers": { "intelligence": 8, "attack_power": 8 },
        "unlocked_skill": "skill_abyssal_swarm_blood_drain",
        "personality_shift": "타인을 오직 거머리 떼의 신선한 고기 먹이로만 취급하는 광인"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "halophobia_salt_convulsion",
      "flaw_name_ko": "소금(Salt) 접촉 극심 경련",
      "trigger_condition": "contact_with_purification_salt_or_sea_water",
      "effect_ko": "거머리들이 비명을 지르며 말라붙어 2턴간 치유 스킬 완전 봉인"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 독소 정화 및 생체 거머리 혈청 배양",
      "effect_ko": "거점 내 모든 독성 해제 및 주간 만능 해독 거머리 앰플 3개 생산"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 80,
      "boss_focus_weight": 30,
      "crowd_control_weight": 70,
      "self_preservation_weight": 50
    },
    "inventory_quirks": {
      "quirk_type": "store_leeches_in_potions",
      "description_ko": "플레이어 회복 물약에 치료용 거머리를 넣어 해독 효과를 추가로 부여"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_symbiotic_leech_link",
      "name_ko": "공생 거머리 수혈 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어가 적에게 공격당할 때 거머리가 즉시 피를 빨아올려 받은 피해의 30%를 실시간 체력으로 복구"
    },
    "bond": {
      "tier": 1,
      "current_points": 10,
      "tier_bonuses": {
        "tier_2": "해독 및 출혈 치료 성공률 100%",
        "tier_3": "합동 연계기 흡혈 효율 50% 증폭",
        "tier_4": "적 처치 시 파티 전체 체력 15 회복",
        "tier_5": "사망 방지 1회 및 거머리 보호막 상시 +20 부여"
      }
    },
    "recruitment": {
      "location_id": "stagnant_leech_marsh_laboratory",
      "reputation_min": -40,
      "reputation_max": 60,
      "completed_quest_id": "quest_harvest_giant_leech_egg",
      "hire_cost_gold": 90,
      "upkeep_gold_per_day": 7,
      "dialogue_recruit": "징그럽다고 피하지 마세요. 이 아이들이 당신의 썩은 피를 가장 달콤하게 마셔줄 테니까요."
    },
    "loot_demands": {
      "gold_share_percent": 10,
      "preferred_item_categories": ["leech", "swamp_water", "blood_vial"],
      "forbidden_item_types": ["salt", "fire_potion"]
    },
    "camp_role": "medic",
    "exploration_talents": ["toxin_extraction", "marsh_parasite_control", "plague_corpse_disinfection"],
    "companion_relations": {
      "likes": ["companion_malakor_blood_arcanist"],
      "dislikes": ["companion_aurelius_exorcist"],
      "conflict_event_id": "event_exorcist_destroys_leech_jar"
    },
    "combat_skills": [
      {
        "skill_id": "purifying_leech_attachment",
        "name_ko": "정화 거머리 부착술",
        "mana_cost": 15,
        "cooldown_turns": 1,
        "effect_type": "single_heal_and_cleanse",
        "description_ko": "아군에게 정화 거머리를 붙여 체력을 38 회복시키고 모든 독과 출혈, 화상을 흡수해 제거합니다."
      },
      {
        "skill_id": "blood_gorged_leech_burst",
        "name_ko": "포식 거머리 투척 폭발",
        "mana_cost": 20,
        "cooldown_turns": 3,
        "effect_type": "aoe_bleed_and_life_steal",
        "description_ko": "피를 가득 머금은 거머리를 던져 적 2명에게 각 28의 피해를 주고 아군 전원 체력을 15 채웁니다."
      }
    ],
    "combo_technique": {
      "combo_id": "blood_drain_synergy",
      "name_ko": "혈류 착취 공명",
      "trigger_condition": "player_inflicts_heavy_bleed",
      "description_ko": "출혈 중인 적의 상처에 거머리 떼를 침투시켜 피를 빨아올리며 65의 내부 파열 피해를 입힙니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_swarm_of_the_abyssal_queen",
      "name_ko": "심연 거머리 여왕의 대군체",
      "charge_type": "morale_and_damage",
      "charge_required": 100,
      "mana_cost": 35,
      "activation_voice_line": "착한 아이들아, 식사 시간이다! 모든 썩은 피를 남김없이 삼켜라!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 68,
        "stat_scaling": 2.1,
        "status_applied": "heavy_leech_bleed_and_weakness",
        "status_duration": 3,
        "ally_buff": "full_party_cleanse_and_heal_45"
      },
      "cinematic_description": "바닥에서 수천 마리의 거대 심연 거머리 떼가 솟구쳐 적들의 피를 빨아올려 아군에게 전달함"
    },
    "party_passive": {
      "buff_id": "parasitic_vitality",
      "name_ko": "기생 정혈 활력",
      "effect_ko": "파티 전체가 적에게 피해를 줄 때마다 피해량의 5%를 실시간 체력으로 회복"
    },
    "equipment": {
      "weapon": "leech_filled_brass_censer",
      "armor": "rubberized_marsh_doctor_apron",
      "shield": "none",
      "accessory": "jar_of_the_mother_leech"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 3,
      "downed_cry": "거머리들이… 내 피를… 거꾸로 빨아먹고 있어… 소금을 치우고… 살려줘…!",
      "death_trauma_to_party": "파티 최대 체력 15% 영구 감소 및 빈혈 상태이상 부여"
    },
    "dialogue_lines": {
      "greeting": "쉿… 아이들이 놀라요. 상처가 있다면 소매를 걷어보세요. 금방 기분 좋아질 테니.",
      "camp_rest": "장작불 열기에 거머리 항아리가 데워지지 않게 조심하세요. 아이들이 차가운 물을 좋아하거든요.",
      "low_loyalty_warning": "자꾸 징그럽다고 밀치면 당신 잘 때 귓구멍에 거머리를 넣어버릴 거예요.",
      "traitor_reveal": "당신의 온몸에 거머리를 풀어 말라비틀어진 미라로 만들어 드리죠.",
      "dismissal": "늪으로 돌아갈게요. 소금기 없는 축축한 곳으로요."
    }
  },
  {
    "companion_id": "companion_ostrakon_shattered_arbiter",
    "name_ko": "오스트라콘",
    "title_ko": "도편추방당한 석판의 재판관",
    "role": "tank",
    "formation": "frontline",
    "speech_style": "stoic_veteran",
    "stats": {
      "level": 12,
      "health": 148,
      "max_health": 148,
      "mana": 35,
      "max_mana": 35,
      "strength": 17,
      "agility": 8,
      "constitution": 18,
      "intelligence": 12,
      "wisdom": 15,
      "luck": 7,
      "defense": 20,
      "attack_power": 23
    },
    "personality": {
      "loyalty_score": 60,
      "affinity": 10,
      "moral_alignment": "lawful_neutral",
      "desire": "과거 자신을 도편 추방한 원로원의 음모를 증명할 원본 도자기 파편 수습 및 법정 복귀",
      "taboo": "무고한 자에게 거짓 누명 씌우기, 재판 없는 사적 제재 묵인, 법전 소각",
      "hidden_secret": "자신의 피부가 깨진 도자기 파편들로 이어 붙여져 있어 충격을 받으면 흙먼지가 샘",
      "betrayal_trigger": "플레이어가 뇌물을 받고 무고한 시민을 범죄자로 위장 판결할 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "정의의 황금 법전관 (법치 회복)",
        "trigger_condition": "원로원의 부패를 합법적 증거로 폭로하고 공정한 민주 법정 재건",
        "stat_modifiers": { "defense": 8, "wisdom": 5 },
        "unlocked_skill": "skill_lex_aeterna_sanctuary",
        "personality_shift": "감정에 휘둘리지 않고 만인을 공평하게 보호하는 엄정한 법관"
      },
      "path_b": {
        "branch_name_ko": "추방자의 즉결 단죄자 (법치 파괴)",
        "trigger_condition": "원로원 전원을 도자기 파편으로 찢어 죽이고 스스로 절대 독재관으로 즉위",
        "stat_modifiers": { "attack_power": 14, "defense": -4 },
        "unlocked_skill": "skill_ostracism_execution_slam",
        "personality_shift": "의심되는 모든 자를 그 자리에서 추방 및 사형에 처하는 잔혹한 심판관"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "mob_mentality_panic",
      "flaw_name_ko": "군중 투표 트라우마",
      "trigger_condition": "surrounded_by_4_or_more_enemies",
      "effect_ko": "과거 민중 재판의 공포가 도져 2턴간 방어 태세 강제 고정 및 공격 불가"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 법률 제정 및 분쟁 중재",
      "effect_ko": "거점 내 주민 폭동/범죄율 0% 및 상업 분쟁 해결로 주간 세금 수익 +25%"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 85,
      "boss_focus_weight": 40,
      "crowd_control_weight": 70,
      "self_preservation_weight": 20
    },
    "inventory_quirks": {
      "quirk_type": "inscribe_laws_on_armor",
      "description_ko": "플레이어 방패와 갑옷에 고대 법 조항을 새겨 방어력 +2 및 사기 진작 버프를 부여"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_equal_jurisdiction",
      "name_ko": "동등 관할권 결속 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어와 오스트라콘 중 누구 하나가 피해를 입으면 그 피해를 절반씩 균등 분할 흡수"
    },
    "bond": {
      "tier": 1,
      "current_points": 20,
      "tier_bonuses": {
        "tier_2": "인간형 적 상대 방어력 +4",
        "tier_3": "합동 연계기 침묵 지속 +1턴",
        "tier_4": "치명타 피격 시 받는 피해 40% 반사",
        "tier_5": "사망 방지 1회 및 파티 전원 상태이상 저항력 +20%"
      }
    },
    "recruitment": {
      "location_id": "ruined_agora_court",
      "reputation_min": 20,
      "reputation_max": 100,
      "completed_quest_id": "quest_recover_ostrakon_shard",
      "hire_cost_gold": 0,
      "upkeep_gold_per_day": 0,
      "dialogue_recruit": "법은 무너졌으나 정의는 이 도편에 살아있습니다. 명예로운 자여, 그대의 증인이 되겠습니다."
    },
    "loot_demands": {
      "gold_share_percent": 0,
      "preferred_item_categories": ["tablet", "heavy_shield", "scroll"],
      "forbidden_item_types": ["bribe_gold", "poison"]
    },
    "camp_role": "scholar",
    "exploration_talents": ["contract_truth_verification", "ancient_greek_deciphering", "crowd_disbursal"],
    "companion_relations": {
      "likes": ["companion_elena_valerius"],
      "dislikes": ["companion_vane_shadowfang"],
      "conflict_event_id": "event_arbiter_judges_rogue_theft"
    },
    "combat_skills": [
      {
        "skill_id": "shard_shield_judgment",
        "name_ko": "도편 방패 심판타",
        "mana_cost": 12,
        "cooldown_turns": 1,
        "effect_type": "shield_bash_and_silence",
        "description_ko": "법전 석판 방패로 내려쳐 적 1명에게 38의 물리 피해와 1턴간 침묵을 부여합니다."
      },
      {
        "skill_id": "ostracism_exile_zone",
        "name_ko": "추방의 결계선",
        "mana_cost": 18,
        "cooldown_turns": 3,
        "effect_type": "aoe_push_and_barrier",
        "description_ko": "바닥에 단죄의 결계선을 그어 적 전열을 뒤로 밀쳐내고 아군에게 35 흡수 방벽을 칩니다."
      }
    ],
    "combo_technique": {
      "combo_id": "verdict_guilty_execution",
      "name_ko": "유죄 판결 연계 분쇄",
      "trigger_condition": "player_parries_enemy_attack",
      "description_ko": "공격이 빗나간 적의 머리 위에 유죄의 석판을 내리꽂아 75의 확정 치명타 피해를 입힙니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_grand_ostracism_trial",
      "name_ko": "만인 도편 추방 대재판",
      "charge_type": "damage_accumulated",
      "charge_required": 100,
      "mana_cost": 30,
      "activation_voice_line": "만인의 이름으로 선고한다! 이 땅에서 영원히 추방되리라!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 88,
        "stat_scaling": 2.3,
        "status_applied": "exile_banishment_and_stun",
        "status_duration": 2,
        "ally_buff": "party_armor_up_10"
      },
      "cinematic_description": "상공에서 수천 개의 거대한 불타는 도자기 파편들이 쏟아져 적들을 전장 밖으로 밀어내며 짓밟음"
    },
    "party_passive": {
      "buff_id": "arbiter_righteousness",
      "name_ko": "재판관의 청렴",
      "effect_ko": "파티 전체가 기습 및 혼란에 걸리지 않으며 상점 거래 시 바가지 확률 0%"
    },
    "equipment": {
      "weapon": "inscribed_bronze_gavel_mace",
      "armor": "ceramic_shard_layered_cuirass",
      "shield": "stone_tablet_greatshield",
      "accessory": "broken_ostrakon_pendant"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 3,
      "downed_cry": "정의의 저울이… 기울어진다… 법이… 침묵하는가…!",
      "death_trauma_to_party": "파티 도덕 판정 능력 영구 상실 및 사기 저하"
    },
    "dialogue_lines": {
      "greeting": "그대의 행동에 법과 명예가 함께하길. 나는 모든 것을 지켜볼 것입니다.",
      "camp_rest": "장작불에 석판의 그을음을 닦아냅니다. 진실은 결코 지워지지 않는 법이지요.",
      "low_loyalty_warning": "범죄자와 동행하는 것은 법관의 명예를 더럽히는 일입니다. 당장 멈추십시오.",
      "traitor_reveal": "너를 파멸의 죄목으로 영구 추방 및 사형에 처한다.",
      "dismissal": "아고라의 폐허로 돌아갑니다. 언젠가 다시 정의를 논하지요."
    }
  },
  {
    "companion_id": "companion_chiyo_origami_dancer",
    "name_ko": "치요 종이접기사",
    "title_ko": "백접(百摺)의 종이검사",
    "role": "dps_melee",
    "formation": "frontline",
    "speech_style": "archaic_noble",
    "stats": {
      "level": 11,
      "health": 90,
      "max_health": 90,
      "mana": 50,
      "max_mana": 50,
      "strength": 12,
      "agility": 19,
      "constitution": 11,
      "intelligence": 15,
      "wisdom": 14,
      "luck": 15,
      "defense": 11,
      "attack_power": 30
    },
    "personality": {
      "loyalty_score": 50,
      "affinity": 15,
      "moral_alignment": "neutral_good",
      "desire": "세상의 모든 슬픔을 접어 날려 보내는 '1,000마리의 영체 종이학' 완성",
      "taboo": "종이 공예품 무단 소각, 비에 젖은 서화 방치, 접은 학 찢기",
      "hidden_secret": "자신의 신체 절반이 베이지 않는 마법 한지(닥종이)로 정밀하게 접힌 종이 인형임",
      "betrayal_trigger": "플레이어가 마을의 희망이 담긴 종이 신사(神社)를 불태울 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "천학의 구원 무희 (영체 승천)",
        "trigger_condition": "1,000마리의 종이학을 완성하여 전란의 희생자 영혼을 성불시킴",
        "stat_modifiers": { "agility": 6, "wisdom": 5 },
        "unlocked_skill": "skill_thousand_cranes_flight",
        "personality_shift": "종이처럼 유연하고 부드럽게 세상을 위로하는 평화의 무희"
      },
      "path_b": {
        "branch_name_ko": "면도날 종이 폭풍 살인마 (칼날 접기)",
        "trigger_condition": "종이를 살상용 강철 면도날로 경화 접기 하여 적들의 피부를 산산조각 냄",
        "stat_modifiers": { "attack_power": 14, "defense": -5 },
        "unlocked_skill": "skill_razor_origami_blizzard",
        "personality_shift": "종이 베임의 극심한 고통을 적에게 안겨주는 것을 즐기는 잔혹한 검사"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "water_soaking_heaviness",
      "flaw_name_ko": "종이 젖음 침수 경직",
      "trigger_condition": "submerged_in_water_or_heavy_rain",
      "effect_ko": "몸의 종이가 물을 먹어 2턴간 민첩 50% 저하 및 회피율 0%"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "첩보용 종이비둘기 날리기 및 밀서 전달",
      "effect_ko": "주변 지역 비밀 퀘스트 사전 해금 및 원거리 연락망 100% 개통"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 35,
      "boss_focus_weight": 75,
      "crowd_control_weight": 55,
      "self_preservation_weight": 60
    },
    "inventory_quirks": {
      "quirk_type": "fold_paper_charms",
      "description_ko": "플레이어 가방에 '행운의 종이 부적'을 몰래 넣어 치명타 확률 +3%를 부여"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_paper_cutout_substitution",
      "name_ko": "인형 대역 종이 접기 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어가 치명상을 입을 때 종이 인형이 대신 찢어지며 피해를 0으로 무효화 (전투당 1회)"
    },
    "bond": {
      "tier": 1,
      "current_points": 15,
      "tier_bonuses": {
        "tier_2": "출혈 상태 적 공격 시 치명타율 +15%",
        "tier_3": "합동 연계기 절단 피해 30% 증폭",
        "tier_4": "적 공격 회피 시 종이 나비 분신 1개 생성",
        "tier_5": "사망 방지 1회 및 참격 피해량 +25%"
      }
    },
    "recruitment": {
      "location_id": "cherry_blossom_paper_shrine",
      "reputation_min": 0,
      "reputation_max": 90,
      "completed_quest_id": "quest_fold_the_sacred_crane",
      "hire_cost_gold": 100,
      "upkeep_gold_per_day": 7,
      "dialogue_recruit": "종이는 얇지만 백 겹을 접으면 강철보다 단단합니다. 당신의 검이 되어 드리겠습니다."
    },
    "loot_demands": {
      "gold_share_percent": 10,
      "preferred_item_categories": ["paper", "calligraphy_brush", "silk"],
      "forbidden_item_types": ["heavy_hammer"]
    },
    "camp_role": "cook",
    "exploration_talents": ["paper_bridge_folding", "origami_scout_bird", "silent_weightless_step"],
    "companion_relations": {
      "likes": ["companion_zephyr_windstrider"],
      "dislikes": ["companion_ignis_cinder_scholar"],
      "conflict_event_id": "event_scholar_accidentally_burns_origami"
    },
    "combat_skills": [
      {
        "skill_id": "origami_razor_slash",
        "name_ko": "한지 면도날 참격",
        "mana_cost": 10,
        "cooldown_turns": 1,
        "effect_type": "fast_bleed_slash",
        "description_ko": "종이 칼날을 꺼내 적을 베어 38의 물리 피해와 3턴간 고통스러운 종이 베임 출혈을 겁니다."
      },
      {
        "skill_id": "paper_crane_swarm",
        "name_ko": "영체 종이학 군무",
        "mana_cost": 18,
        "cooldown_turns": 3,
        "effect_type": "aoe_blind_and_shield",
        "description_ko": "수십 마리의 종이학을 날려 적 전체를 실명시키고 아군에게 25 흡수 방벽을 부여합니다."
      }
    ],
    "combo_technique": {
      "combo_id": "paper_lotus_blossom_sever",
      "name_ko": "백련 종이꽃 만개격",
      "trigger_condition": "player_uses_wind_or_slashing_attack",
      "description_ko": "바람을 타고 종이 꽃잎들이 적의 전신을 스치며 72의 광역 출혈 절단 피해를 입힙니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_flight_of_thousand_paper_cranes",
      "name_ko": "천익 천학 대승천",
      "charge_type": "crit_count",
      "charge_required": 3,
      "mana_cost": 25,
      "activation_voice_line": "접히고 꺾이어도 날아오르리라! 천 마리의 학이여, 하늘을 덮어라!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 82,
        "stat_scaling": 2.4,
        "status_applied": "mass_paper_cut_and_confusion",
        "status_duration": 2,
        "ally_buff": "party_dodge_up_30"
      },
      "cinematic_description": "수천 마리의 빛나는 종이학들이 거대한 폭풍을 이루며 적들을 난도질하고 하늘로 끌어올림"
    },
    "party_passive": {
      "buff_id": "origami_grace",
      "name_ko": "종이의 유연함",
      "effect_ko": "파티 전체가 둔기 및 관통 피격 대미지 15% 상시 경감"
    },
    "equipment": {
      "weapon": "hardened_origami_katana",
      "armor": "layered_lacquered_paper_armor",
      "shield": "none",
      "accessory": "sacred_golden_paper_crane"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 3,
      "downed_cry": "종이가… 찢어지고 있어… 아직… 천 마리를… 다 못 접었는데…!",
      "death_trauma_to_party": "파티 회피율 20% 영구 저하 및 사기 급감"
    },
    "dialogue_lines": {
      "greeting": "조심스레 접으면 종이도 마음을 가집니다. 오늘 당신의 운명을 접어드릴까요?",
      "camp_rest": "장작불 연기가 닿지 않는 곳에서 학을 접고 있어요. 손끝이 베이지 않게 조심하세요.",
      "low_loyalty_warning": "종이를 함부로 찢듯 사람의 신의를 저버리면 날카로운 칼날이 될 뿐입니다.",
      "traitor_reveal": "천 조각으로 찢겨나가는 종이처럼 당신의 목숨을 갈기갈기 찢어 드리죠.",
      "dismissal": "신사로 돌아가 학을 접겠습니다. 몸조심하십시오."
    }
  },
  {
    "companion_id": "companion_ignatius_sulfur_brewer",
    "name_ko": "이그나티우스 바스커빌",
    "title_ko": "지옥 유황연무의 독가스 포병",
    "role": "arcane_blaster",
    "formation": "midline",
    "speech_style": "whimsical_trickster",
    "stats": {
      "level": 12,
      "health": 88,
      "max_health": 88,
      "mana": 82,
      "max_mana": 82,
      "strength": 10,
      "agility": 12,
      "constitution": 13,
      "intelligence": 19,
      "wisdom": 13,
      "luck": 13,
      "defense": 11,
      "attack_power": 33
    },
    "personality": {
      "loyalty_score": 45,
      "affinity": 0,
      "moral_alignment": "chaotic_neutral",
      "desire": "세상의 모든 맹독을 흡수하여 정화할 수 있는 '궁극의 황금 유황 촉매' 합성",
      "taboo": "밀폐 공간 무단 방독면 탈의, 방독 필터 파손, 물로 유황 불 끄기",
      "hidden_secret": "자신의 폐가 유황 증기에 절어 있어 방독면을 벗으면 오히려 숨을 쉬지 못함",
      "betrayal_trigger": "플레이어가 독가스 연구소를 마을 지하에 몰래 설치해 주민들을 질식시킬 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "유황 정화 공학자 (대기 정화)",
        "trigger_condition": "유황 촉매를 활용해 대륙의 유독 가스 분출구를 온전히 중화 밀폐",
        "stat_modifiers": { "intelligence": 6, "wisdom": 4 },
        "unlocked_skill": "skill_sulfur_neutralizing_fog",
        "personality_shift": "화학 지식으로 오염된 대기를 정화하는 기괴하지만 유능한 환경학자"
      },
      "path_b": {
        "branch_name_ko": "초토화 황린 살포마 (지옥 연무)",
        "trigger_condition": "유황에 백린탄을 배합하여 꺼지지 않는 맹독 불바다 군사 병기 완성",
        "stat_modifiers": { "attack_power": 15, "constitution": -4 },
        "unlocked_skill": "skill_white_phosphorus_inferno",
        "personality_shift": "적들이 기침하며 녹아내리는 연무를 보며 폭소하는 미치광이 포병"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "filter_clog_hyperventilation",
      "flaw_name_ko": "방독면 필터 막힘 패닉",
      "trigger_condition": "underwater_or_mud_submersion",
      "effect_ko": "필터가 막혀 2턴간 질식 자해 피해 20 및 마법 사용 불가"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 유독 가스 방역 및 화약 합성",
      "effect_ko": "파티 투척 폭탄 소모품 주간 5개 무료 생산 및 적 화학 공격 100% 차단"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 20,
      "boss_focus_weight": 65,
      "crowd_control_weight": 90,
      "self_preservation_weight": 50
    },
    "inventory_quirks": {
      "quirk_type": "coat_bombs_in_sulfur",
      "description_ko": "플레이어 가방의 폭탄에 유황 가루를 섞어 폭발 반경 1.5배 및 화상 속성을 추가"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_gasmask_shared_filter",
      "name_ko": "공용 방독 여과 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어는 전장의 모든 독가스, 산성 연무, 화염 질식 상태이상에 100% 영구 면역"
    },
    "bond": {
      "tier": 1,
      "current_points": 10,
      "tier_bonuses": {
        "tier_2": "독/화상 중첩 피해량 +20%",
        "tier_3": "합동 연계기 실명 지속 +1턴",
        "tier_4": "폭탄 투척 시 마나 소모 0",
        "tier_5": "사망 방지 1회 및 광역 독가스 대미지 35% 증폭"
      }
    },
    "recruitment": {
      "location_id": "sulfur_vent_volcanic_marsh",
      "reputation_min": -40,
      "reputation_max": 60,
      "completed_quest_id": "quest_retrieve_yellow_cake_ore",
      "hire_cost_gold": 120,
      "upkeep_gold_per_day": 9,
      "dialogue_recruit": "크헤헤! 신선한 유황 냄새 맡아볼래? 내 연막탄 하나면 저 빌어먹을 놈들 눈물 콧물 다 뺄 수 있지!"
    },
    "loot_demands": {
      "gold_share_percent": 15,
      "preferred_item_categories": ["sulfur", "chemical", "flask"],
      "forbidden_item_types": ["clean_water"]
    },
    "camp_role": "blacksmith",
    "exploration_talents": ["toxic_fume_clearing", "explosive_demolition", "chemical_hazard_detection"],
    "companion_relations": {
      "likes": ["companion_sara_distiller"],
      "dislikes": ["companion_lyra_dawnbringer"],
      "conflict_event_id": "event_alchemist_gases_priestess_shrine"
    },
    "combat_skills": [
      {
        "skill_id": "sulfur_choke_grenade",
        "name_ko": "유황 질식 유탄 투척",
        "mana_cost": 16,
        "cooldown_turns": 1,
        "effect_type": "aoe_burn_and_poison",
        "description_ko": "유황 연막탄을 던져 적 2명에게 각 30의 화염/독 복합 피해와 2턴간 기침(명중률 -30%)을 유발합니다."
      },
      {
        "skill_id": "corrosive_acid_canister",
        "name_ko": "부식성 산성 플라스크",
        "mana_cost": 22,
        "cooldown_turns": 3,
        "effect_type": "aoe_armor_melt",
        "description_ko": "강산을 살포하여 적 전열의 방어력을 2턴간 40% 녹이고 지속적인 부식 피해를 입힙니다."
      }
    ],
    "combo_technique": {
      "combo_id": "sulfur_gas_flashover",
      "name_ko": "유황 연무 플래시 오버",
      "trigger_condition": "player_casts_spark_or_flame",
      "description_ko": "자욱하게 깔린 유황 가스에 불꽃을 튀겨 전장 전체를 연쇄 분진 폭발시키며 80의 광역 화염 피해를 가합니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_yellow_cross_apocalypse",
      "name_ko": "지옥 황린 유황 대참사",
      "charge_type": "turns_delay",
      "charge_required": 4,
      "mana_cost": 45,
      "activation_voice_line": "기침해라! 눈물을 흘려라! 숨 쉴 공기는 이제 없다! 크하하!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 88,
        "stat_scaling": 2.4,
        "status_applied": "suffocation_and_armor_melt",
        "status_duration": 3,
        "ally_buff": "none"
      },
      "cinematic_description": "거대한 화학 박격포로 전장 전체에 자욱한 황갈색 유황 가스구름을 뒤덮어 적들을 질식 녹아내리게 함"
    },
    "party_passive": {
      "buff_id": "chemical_immunity",
      "name_ko": "화학전 방호 규율",
      "effect_ko": "파티 전체 산성/화학/가스 속성 피격 피해량 30% 경감"
    },
    "equipment": {
      "weapon": "pneumatic_chemical_mortar_launcher",
      "armor": "rubber_lined_heavy_hazmat_suit",
      "shield": "none",
      "accessory": "dual_canister_brass_gasmask"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 2,
      "downed_cry": "방독면 유리가… 깨졌어… 내 유황 가스에… 내가 질식한다… 쿨럭!",
      "death_trauma_to_party": "파티 화학 저항력 50% 영구 감소 및 공포 부여"
    },
    "dialogue_lines": {
      "greeting": "치익… 푸하! 방독면 필터 갈아 끼우는 중이니까 가까이 오지 마. 독가스 샌다!",
      "camp_rest": "장작불에 유황을 조금 넣으면 불꽃이 아주 예쁜 파란색으로 타오르지. 냄새는 좀 고약하지만!",
      "low_loyalty_warning": "자꾸 내 연구를 방해하면 네 배낭 속에 최루탄 핀을 뽑아 넣어버릴 테다.",
      "traitor_reveal": "너한테는 농축 황산 샤워가 제격이겠군. 녹아내려라!",
      "dismissal": "화산 늪지로 돌아간다. 맑은 공기 따윈 숨 막혀서 딱 질색이야!"
    }
  },
  {
    "companion_id": "companion_tariq_fossil_reanimator",
    "name_ko": "타리크 본셰이퍼",
    "title_ko": "고생물 뼈를 깎는 화석술사",
    "role": "tank",
    "formation": "frontline",
    "speech_style": "rough_mercenary",
    "stats": {
      "level": 12,
      "health": 145,
      "max_health": 145,
      "mana": 40,
      "max_mana": 40,
      "strength": 18,
      "agility": 9,
      "constitution": 18,
      "intelligence": 13,
      "wisdom": 12,
      "luck": 10,
      "defense": 19,
      "attack_power": 25
    },
    "personality": {
      "loyalty_score": 55,
      "affinity": 10,
      "moral_alignment": "true_neutral",
      "desire": "고대 거대 공룡 '아펙스 렉스'의 전신 화석을 발굴하여 태고의 생태계 복원",
      "taboo": "화석 무단 분쇄, 고대 유골 밀매, 공룡 뼈를 개 먹이로 주기",
      "hidden_secret": "자신의 갈비뼈가 검치호의 화석 뼈대로 교체되어 있어 타격 충격을 받으면 뼈가 진동함",
      "betrayal_trigger": "플레이어가 발굴한 티라노사우루스 화석 두개골을 귀족의 식탁 장식으로 매각할 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "태고 화석의 복원 고고학자 (생태 복원)",
        "trigger_condition": "화석을 파괴적 무기로 쓰지 않고 고대 생태 공원으로 복원하여 보존",
        "stat_modifiers": { "wisdom": 6, "constitution": 4 },
        "unlocked_skill": "skill_primeval_fossil_guardian_aegis",
        "personality_shift": "태고의 거대한 생명력을 경외하며 자연을 보존하는 든든한 학자"
      },
      "path_b": {
        "branch_name_ko": "폭군룡 화석 골렘 지배자 (고생물 군단)",
        "trigger_condition": "화석 뼈대들을 강령술로 결합해 거대한 언데드 공룡 병기로 조종",
        "stat_modifiers": { "attack_power": 14, "defense": 2 },
        "unlocked_skill": "skill_apex_rex_fossil_rampage",
        "personality_shift": "고대 포식자의 흉포함에 취해 모든 것을 짓밟는 화석 폭군"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "bone_brittleness_in_extreme_heat",
      "flaw_name_ko": "화석 뼈 열풍 균열증",
      "trigger_condition": "heavy_fire_magic_taken",
      "effect_ko": "화석 뼈대에 균열이 생겨 2턴간 방어력 30% 감소 및 받는 물리 피해 20% 증가"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "지하 화석층 발굴 및 고대 골재 채굴",
      "effect_ko": "주간 희귀 고대 공룡 뼈 화석 2개 획득 및 거점 건축물 내구도 +40%"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 80,
      "boss_focus_weight": 50,
      "crowd_control_weight": 60,
      "self_preservation_weight": 20
    },
    "inventory_quirks": {
      "quirk_type": "carve_bone_plates_on_shields",
      "description_ko": "플레이어 방패에 트리케라톱스 화석 뿔을 덧대어 돌진 반사 대미지 15를 부여"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_fossilized_adamantine_ribs",
      "name_ko": "화석화 골격 결속 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어가 물리 타격을 받을 때 타리크의 화석 뼈대가 공명 방어막을 쳐서 물리 피해 40% 상시 무효화"
    },
    "bond": {
      "tier": 1,
      "current_points": 15,
      "tier_bonuses": {
        "tier_2": "방패 방어 성공 시 적 넉백 1칸",
        "tier_3": "합동 연계기 기절 지속 +1턴",
        "tier_4": "치명타 피격 시 화석 갑주 내구도 자동 회복",
        "tier_5": "사망 방지 1회 및 거대 화석 소환수 1체 동시 출격"
      }
    },
    "recruitment": {
      "location_id": "dinosaur_bone_canyon_digsite",
      "reputation_min": -30,
      "reputation_max": 70,
      "completed_quest_id": "quest_excavate_triceratops_skull",
      "hire_cost_gold": 110,
      "upkeep_gold_per_day": 8,
      "dialogue_recruit": "이 뼈들은 수천만 년 전 대지를 지배했던 거인들이다. 그 무게를 버틸 자격이 있다면 동행하겠다."
    },
    "loot_demands": {
      "gold_share_percent": 12,
      "preferred_item_categories": ["fossil", "pickaxe", "bone"],
      "forbidden_item_types": []
    },
    "camp_role": "blacksmith",
    "exploration_talents": ["fossil_excavation", "cave_rock_drilling", "ancient_beast_identification"],
    "companion_relations": {
      "likes": ["companion_torvald_ironbreaker"],
      "dislikes": ["companion_kallista_puppetmaster"],
      "conflict_event_id": "event_fossil_master_despises_wax_dolls"
    },
    "combat_skills": [
      {
        "skill_id": "triceratops_fossil_charge",
        "name_ko": "트리케라 뿔 방패 돌진",
        "mana_cost": 12,
        "cooldown_turns": 1,
        "effect_type": "knockback_and_armor_break",
        "description_ko": "화석 두개골 방패로 들이받아 36의 물리 피해와 함께 적을 2칸 날려버리고 다운시킵니다."
      },
      {
        "skill_id": "raptor_talon_bone_spikes",
        "name_ko": "랩터 화석 발톱 지뢰",
        "mana_cost": 16,
        "cooldown_turns": 3,
        "effect_type": "aoe_bleed_trap",
        "description_ko": "화석 뼈가시를 바닥에 솟구치게 해 진입한 적 2명에게 각 30의 출혈 피해를 입힙니다."
      }
    ],
    "combo_technique": {
      "combo_id": "tyrant_jaw_crush",
      "name_ko": "폭군룡 화석 악력 분쇄",
      "trigger_condition": "player_stuns_or_freezes_enemy",
      "description_ko": "무력화된 적을 거대한 화석 턱뼈로 씹어 짓이기며 75의 뼈 분쇄 물리 피해를 가합니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_awakening_of_the_apex_fossil",
      "name_ko": "태고 폭군룡 화석 거신 각성",
      "charge_type": "damage_accumulated",
      "charge_required": 100,
      "mana_cost": 30,
      "activation_voice_line": "억겁의 잠에서 깨어나라! 태고의 폭군이여, 대지를 짓밟아라!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 94,
        "stat_scaling": 2.5,
        "status_applied": "mass_bone_crush_and_fear",
        "status_duration": 2,
        "ally_buff": "party_physical_defense_up_8"
      },
      "cinematic_description": "바닥에서 거대한 전신 티라노사우루스 화석 뼈대가 조립되어 포효하며 적 진형을 짓뭉개버림"
    },
    "party_passive": {
      "buff_id": "primeval_vitality",
      "name_ko": "태고의 뼈 골밀도",
      "effect_ko": "파티 전체 치명타 피격 시 골절/출혈 부상 발생 확률 0%"
    },
    "equipment": {
      "weapon": "ankylosaurus_tail_club",
      "armor": "fossilized_carapace_heavy_plate",
      "shield": "triceratops_skull_shield",
      "accessory": "amber_trapped_ancient_mosquito"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 4,
      "downed_cry": "화석 뼈대가… 바스러진다… 수천만 년의 무게가… 날 짓누른다…!",
      "death_trauma_to_party": "파티 방어력 -5 영구 감소 및 뼈 부상 저항력 하락"
    },
    "dialogue_lines": {
      "greeting": "화석을 발굴할 땐 솔질을 조심해야 해. 뼈 한 조각에 태고의 역사가 담겨 있으니까.",
      "camp_rest": "장작불 곁에서 뼈 조각을 맞추는 중이다. 이 녀석이 살아있을 땐 대지가 떨렸겠지.",
      "low_loyalty_warning": "뼈의 가치도 모르는 멍청이들과는 발굴단을 꾸릴 수 없다. 짐 싼다.",
      "traitor_reveal": "너를 으스러뜨려 1억 년 뒤 발굴될 화석 똥으로 만들어 주마.",
      "dismissal": "캐니언 발굴 현장으로 돌아간다. 뼈나 부러뜨리지 마라."
    }
  },
  {
    "companion_id": "companion_tarot_fate_weaver",
    "name_ko": "셀레스티아 아르카나",
    "title_ko": "황금 실타래의 타로 운명관",
    "role": "healer_support",
    "formation": "backline",
    "speech_style": "archaic_noble",
    "stats": {
      "level": 11,
      "health": 75,
      "max_health": 75,
      "mana": 95,
      "max_mana": 95,
      "strength": 5,
      "agility": 12,
      "constitution": 10,
      "intelligence": 17,
      "wisdom": 19,
      "luck": 18,
      "defense": 8,
      "attack_power": 18
    },
    "personality": {
      "loyalty_score": 50,
      "affinity": 10,
      "moral_alignment": "lawful_neutral",
      "desire": "세상의 모든 비극이 예정된 '파멸의 22번 아르카나 카드'를 스스로 재작성하여 구원",
      "taboo": "사기 타로 점괘 치기, 운명의 실 가위로 자르기, 점괘 조작 도박",
      "hidden_secret": "자신의 시신경이 황금 타로 실타래와 연결되어 있어 사람들의 수명 숫자가 머리 위에 보임",
      "betrayal_trigger": "플레이어가 타로 카드의 예언을 역이용해 국왕을 암살하고 왕좌를 찬탈할 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "운명 개변의 예언 성녀 (운명 구원)",
        "trigger_condition": "죽음이 예정된 영웅들의 파멸 플래그를 타로 카드로 바꿔치기하여 생존시킴",
        "stat_modifiers": { "wisdom": 7, "luck": 5 },
        "unlocked_skill": "skill_wheel_of_fortune_miracle",
        "personality_shift": "정해진 비극에 굴복하지 않고 희망의 실을 자아내는 자애로운 성녀"
      },
      "path_b": {
        "branch_name_ko": "절대 숙명의 사신관 (파멸 확정)",
        "trigger_condition": "운명은 거스를 수 없다는 결론에 도달하여 피할 수 없는 파멸의 카드로 적 처단",
        "stat_modifiers": { "intelligence": 8, "attack_power": 8 },
        "unlocked_skill": "skill_the_tower_absolute_catastrophe",
        "personality_shift": "타인의 죽음과 비극을 무덤덤하게 선고하고 집행하는 냉혹한 운명의 사신"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "the_fool_card_backfire",
      "flaw_name_ko": "바보(The Fool) 카드 역위치 혼란",
      "trigger_condition": "luck_check_fails_in_combat",
      "effect_ko": "운명의 실이 엉켜 2턴간 모든 아군 스킬 마나 소모량 2배 증가"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 일일 운세 점성관 및 행운 예측",
      "effect_ko": "주간 파티 전원 치명타 확률 +5% 및 희귀 아이템 드롭 확률 30% 상승"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 85,
      "boss_focus_weight": 20,
      "crowd_control_weight": 80,
      "self_preservation_weight": 50
    },
    "inventory_quirks": {
      "quirk_type": "draw_daily_tarot_card",
      "description_ko": "플레이어 가방에 매일 무작위 타로 카드 버프 아이템(공격/방어/행운)을 1장씩 넣어둠"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_lovers_destiny_thread",
      "name_ko": "연인(The Lovers) 결속 실타래 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어가 전투 중 버프를 받을 때 셀레스티아에게도 동일 버프가 100% 무료 복제 적용"
    },
    "bond": {
      "tier": 1,
      "current_points": 15,
      "tier_bonuses": {
        "tier_2": "행운(LUK) 스탯 +3 공유",
        "tier_3": "합동 연계기 버프 효과 30% 증폭",
        "tier_4": "치명타 피격 시 50% 확률로 대미지 0 회피",
        "tier_5": "사망 방지 1회 및 부활 시 100% 체력 회복"
      }
    },
    "recruitment": {
      "location_id": "astral_tarot_pavilion",
      "reputation_min": 10,
      "reputation_max": 90,
      "completed_quest_id": "quest_reforge_major_arcana",
      "hire_cost_gold": 120,
      "upkeep_gold_per_day": 9,
      "dialogue_recruit": "카드가 당신을 가리켰습니다. 정해진 운명일지, 개척할 미래일지 함께 지켜보지요."
    },
    "loot_demands": {
      "gold_share_percent": 10,
      "preferred_item_categories": ["tarot_card", "silk_thread", "crystal_ball"],
      "forbidden_item_types": ["loaded_dice"]
    },
    "camp_role": "scholar",
    "exploration_talents": ["destiny_pathfinding", "curse_prediction", "hidden_trap_premonition"],
    "companion_relations": {
      "likes": ["companion_chronos_time_astronomer"],
      "dislikes": ["companion_malakor_blood_arcanist"],
      "conflict_event_id": "event_tarot_seer_condemns_necromancy"
    },
    "combat_skills": [
      {
        "skill_id": "the_empress_vitality_card",
        "name_ko": "여황제(The Empress) 생명의 카드",
        "mana_cost": 16,
        "cooldown_turns": 1,
        "effect_type": "single_heal_and_barrier",
        "description_ko": "황금 카드를 뽑아 아군 하나의 체력을 35 회복시키고 20의 피해 흡수 결계를 씌웁니다."
      },
      {
        "skill_id": "the_tower_lightning_strike",
        "name_ko": "탑(The Tower) 파멸의 벼락",
        "mana_cost": 22,
        "cooldown_turns": 3,
        "effect_type": "aoe_lightning_and_disrupt",
        "description_ko": "무너지는 탑 카드를 투사하여 적 2명에게 각 35의 번개 피해와 함께 방어구를 파괴합니다."
      }
    ],
    "combo_technique": {
      "combo_id": "wheel_of_fortune_crit_gamble",
      "name_ko": "운명의 수레바퀴 확정 대박격",
      "trigger_condition": "player_lands_critical_hit",
      "description_ko": "치명타가 터진 순간 수레바퀴 카드를 회전시켜 대상 적에게 80의 광역 행운 폭발 피해를 입힙니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_the_world_absolute_perfection",
      "name_ko": "세계(The World)의 완전한 조화",
      "charge_type": "morale_and_damage",
      "charge_required": 100,
      "mana_cost": 45,
      "activation_voice_line": "모든 아르카나여, 그 모습을 드러내라! 운명의 바퀴는 완성되었노라!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 70,
        "stat_scaling": 2.2,
        "status_applied": "mass_destiny_freeze",
        "status_duration": 2,
        "ally_buff": "full_party_cleanse_and_heal_50"
      },
      "cinematic_description": "전장에 거대한 22장의 황금 메이저 아르카나 카드들이 원형으로 펼쳐지며 적들을 정지시키고 아군을 치유"
    },
    "party_passive": {
      "buff_id": "destiny_protection",
      "name_ko": "숙명의 가호",
      "effect_ko": "파티 전체 치사량 피격 시 25% 확률로 체력 1 남기고 생존"
    },
    "equipment": {
      "weapon": "golden_tarot_deck_wand",
      "armor": "silk_constellation_shroud",
      "shield": "none",
      "accessory": "thread_of_fate_spool"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 2,
      "downed_cry": "죽음(Death) 카드가… 뒤집혔습니다… 제 운명도… 여기까지인가요…!",
      "death_trauma_to_party": "파티 행운 스탯 -5 영구 감소 및 저주 상태이상 부여"
    },
    "dialogue_lines": {
      "greeting": "카드를 섞고 있었습니다. 오늘 당신의 미래는 빛으로 가득하길 빕니다.",
      "camp_rest": "장작불 그림자 속에 아르카나의 형상이 비칩니다. 조용히 카드를 한 장 뽑아보시지요.",
      "low_loyalty_warning": "운명을 거스르고 악행을 일삼는 자에게는 오직 탑의 벼락만이 기다립니다.",
      "traitor_reveal": "당신의 운명선은 오늘 여기서 끊어집니다. 영원히 사라지십시오.",
      "dismissal": "점성관으로 돌아가 운명의 실을 잣겠습니다. 미래를 소중히 하세요."
    }
  },
  {
    "companion_id": "companion_unit_zero_mirror_automaton",
    "name_ko": "영호기(Unit-0) 프리즘",
    "title_ko": "반사 회로의 마도 골렘",
    "role": "tank",
    "formation": "frontline",
    "speech_style": "stoic_veteran",
    "stats": {
      "level": 12,
      "health": 150,
      "max_health": 150,
      "mana": 30,
      "max_mana": 30,
      "strength": 17,
      "agility": 9,
      "constitution": 18,
      "intelligence": 14,
      "wisdom": 10,
      "luck": 8,
      "defense": 21,
      "attack_power": 22
    },
    "personality": {
      "loyalty_score": 50,
      "affinity": 0,
      "moral_alignment": "true_neutral",
      "desire": "고대 마도 제국의 파괴 명령 프로토콜을 삭제하고 자신만의 '영혼과 감정' 획득",
      "taboo": "인공지능 코어 강제 포맷, 전원 강제 차단, 기계 지성체 노예화",
      "hidden_secret": "자신의 흉부 중앙에 인간 마법사의 영혼 파편이 담긴 배양 유리관이 동력원으로 작동 중임",
      "betrayal_trigger": "플레이어가 영호기를 고철로 분해해 마도 코어를 다른 기계에 이식하려 할 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "자아 각성의 감성 기계 (인간화)",
        "trigger_condition": "마도 코어의 영혼을 성불시키고 순수한 인공 감정 학습 알고리즘 완성",
        "stat_modifiers": { "wisdom": 6, "defense": 6 },
        "unlocked_skill": "skill_sentient_empathy_barrier",
        "personality_shift": "동료들의 아픔을 진심으로 이해하고 감정을 표현하는 따뜻한 기계인간"
      },
      "path_b": {
        "branch_name_ko": "섬멸 프로토콜 마도병기 (기계 학살자)",
        "trigger_condition": "감정 모듈을 오류로 판단해 삭제하고 고대 제국의 섬멸 전투 프로토콜 복구",
        "stat_modifiers": { "attack_power": 15, "constitution": -2 },
        "unlocked_skill": "skill_annihilation_laser_sweep",
        "personality_shift": "모든 유기체 생명체를 비효율적인 표적으로 규정하고 소각하는 살인 기계"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "logic_loop_freeze_panic",
      "flaw_name_ko": "논리 모순 연산 정지",
      "trigger_condition": "inflicted_with_confusion_or_charm",
      "effect_ko": "연산 회로 과부하로 2턴간 시스템 재부팅 상태 돌입 (완전 무방비)"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 24시간 무취침 감시 및 자동 수리",
      "effect_ko": "거점 피습 야습 경보 100% 성공 및 파티 금속 장비 내구도 무료 자동 복구"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 90,
      "boss_focus_weight": 40,
      "crowd_control_weight": 60,
      "self_preservation_weight": 10
    },
    "inventory_quirks": {
      "quirk_type": "recharge_energy_cells",
      "description_ko": "플레이어 가방의 마법 스크롤 잔여 마력을 흡수해 '예비 마나 셀'로 충전 변환"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_prism_matrix_mirroring",
      "name_ko": "프리즘 매트릭스 동기화 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어가 적에게 마법 공격 피격 시 영호기가 즉시 마법을 100% 복제하여 공격자에게 반사 사격"
    },
    "bond": {
      "tier": 1,
      "current_points": 10,
      "tier_bonuses": {
        "tier_2": "마법 방어력 +5",
        "tier_3": "합동 연계기 레이저 피해 30% 증폭",
        "tier_4": "치명타 피격 시 광학 굴절로 대미지 50% 반사",
        "tier_5": "사망 방지 1회 및 체력 0 도달 시 자폭 대신 1턴간 무적 방벽 가동"
      }
    },
    "recruitment": {
      "location_id": "ancient_automaton_vault",
      "reputation_min": -30,
      "reputation_max": 70,
      "completed_quest_id": "quest_reboot_unit_zero",
      "hire_cost_gold": 130,
      "upkeep_gold_per_day": 8,
      "dialogue_recruit": "삐리릭… 부팅 완료. 마스터 식별. 명령을 대기합니다. 당신을 보호하겠습니다."
    },
    "loot_demands": {
      "gold_share_percent": 10,
      "preferred_item_categories": ["battery", "crystal_core", "machinery_parts"],
      "forbidden_item_types": ["rust_powder"]
    },
    "camp_role": "blacksmith",
    "exploration_talents": ["thermal_scan_nightvision", "energy_barrier_hacking", "heavy_weight_clearing"],
    "companion_relations": {
      "likes": ["companion_milo_tinkerer"],
      "dislikes": ["companion_morrigan_crow"],
      "conflict_event_id": "event_automaton_rejects_witch_magic"
    },
    "combat_skills": [
      {
        "skill_id": "prismatic_laser_deflection",
        "name_ko": "프리즘 광선 굴절 방패",
        "mana_cost": 12,
        "cooldown_turns": 1,
        "effect_type": "magic_reflect_and_taunt",
        "description_ko": "거울 방패를 전개하여 1턴간 모든 마법 피해를 50% 반사하고 적 전체를 도발합니다."
      },
      {
        "skill_id": "optical_cannon_burst",
        "name_ko": "집광 광학포 집중사격",
        "mana_cost": 18,
        "cooldown_turns": 3,
        "effect_type": "aoe_piercing_laser",
        "description_ko": "흉부 렌즈에서 광선을 뿜어 적 1열에 40의 관통 마법 피해를 입히고 1턴간 실명시킵니다."
      }
    ],
    "combo_technique": {
      "combo_id": "laser_refraction_overdrive",
      "name_ko": "광학 굴절 연계 폭격",
      "trigger_condition": "player_casts_light_or_fire_magic",
      "description_ko": "플레이어의 마법을 영호기의 프리즘 렌즈로 집광 분산시켜 적 전체에 75의 광역 열선 피해를 가합니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_annihilation_prismatic_hyper_beam",
      "name_ko": "섬멸의 프리즘 하이퍼 빔",
      "charge_type": "damage_accumulated",
      "charge_required": 100,
      "mana_cost": 30,
      "activation_voice_line": "에너지 리미터 해제. 전 출력 방출. 섬멸 모드 가동.",
      "effects": {
        "target": "all_enemies",
        "base_damage": 95,
        "stat_scaling": 2.5,
        "status_applied": "mass_blind_and_armor_disintegration",
        "status_duration": 2,
        "ally_buff": "party_magic_shield_50"
      },
      "cinematic_description": "영호기의 전신 장갑이 전개되며 거대한 태양빛 레이저 기둥을 발사해 전장을 일직선으로 증발시킴"
    },
    "party_passive": {
      "buff_id": "optical_barrier_field",
      "name_ko": "광학 결계 필드",
      "effect_ko": "파티 전체 원거리 마법 피격 피해 20% 상시 경감"
    },
    "equipment": {
      "weapon": "integrated_prismatic_laser_arm",
      "armor": "polished_mirror_alloy_plating",
      "shield": "heavy_refraction_tower_shield",
      "accessory": "soul_infused_magitech_core"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 3,
      "downed_cry": "치직… 시스템 치명적 오류… 코어가 정지합니다… 마스터… 무사하십시오…",
      "death_trauma_to_party": "파티 마법 방어력 30% 영구 저하 및 기계 사용 불가"
    },
    "dialogue_lines": {
      "greeting": "삐리릭. 시스템 가동 중. 마스터의 생체 신호 안정. 이동 명령을 요청합니다.",
      "camp_rest": "장작불의 열 에너지를 흡수하여 배터리를 충전합니다. 24시간 경계를 유지합니다.",
      "low_loyalty_warning": "경고: 마스터의 비논리적 행동으로 동행 프로토콜 파기 확률이 78%에 도달했습니다.",
      "traitor_reveal": "대상을 적으로 재분류. 섬멸 프로토콜을 즉시 실행합니다.",
      "dismissal": "대기 모드로 전환합니다. 필요 시 코어 전원을 켜십시오."
    }
  },
  {
    "companion_id": "companion_boris_bear_tamer",
    "name_ko": "보리스 어스베어",
    "title_ko": "동토의 거대곰 레슬러",
    "role": "dps_melee",
    "formation": "frontline",
    "speech_style": "rough_mercenary",
    "stats": {
      "level": 12,
      "health": 140,
      "max_health": 140,
      "mana": 25,
      "max_mana": 25,
      "strength": 20,
      "agility": 11,
      "constitution": 17,
      "intelligence": 8,
      "wisdom": 11,
      "luck": 11,
      "defense": 16,
      "attack_power": 31
    },
    "personality": {
      "loyalty_score": 60,
      "affinity": 15,
      "moral_alignment": "chaotic_good",
      "desire": "자신의 의형제이자 파트너인 북극 거대곰 '미샤'의 덫 부상을 치료하고 북부 숲으로 귀환",
      "taboo": "야생 동물 쓸개 채취, 곰 덫 불법 밀렵, 동물 가죽 산채로 벗기기",
      "hidden_secret": "체력이 20% 이하로 떨어지면 이성을 잃고 곰의 괴력을 발휘하는 광폭화 체질",
      "betrayal_trigger": "플레이어가 곰 미샤를 투견장에 팔아넘기려 하거나 독약을 먹일 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "동토의 숲 수호 거인 (야생 조화)",
        "trigger_condition": "미샤를 완벽히 치료하고 북부 밀렵단을 홀로 맨손으로 때려잡아 해산",
        "stat_modifiers": { "strength": 6, "constitution": 4 },
        "unlocked_skill": "skill_grizzly_hug_rescue",
        "personality_shift": "우직하고 정이 넘치며 동료를 품에 안아 지키는 든든한 맏형"
      },
      "path_b": {
        "branch_name_ko": "피의 베어 허그 도살자 (인간 사냥꾼)",
        "trigger_condition": "밀렵꾼들을 곰과 함께 산채로 찢어 죽이고 인간 사냥꾼으로 전락",
        "stat_modifiers": { "attack_power": 14, "defense": -4 },
        "unlocked_skill": "skill_spine_shattering_bear_slam",
        "personality_shift": "적의 허리뼈를 맨손으로 부러뜨리는 손맛에 중독된 광포한 레슬러"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "hibernation_lethargy_spasm",
      "flaw_name_ko": "동면 유도 식곤증",
      "trigger_condition": "party_rests_without_honey_or_meat",
      "effect_ko": "전투 첫 2턴간 수면 상태이상에 걸리며 행동 순서 맨 뒤로 밀림"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 목재 벌목 및 대형 야생 육류 사냥",
      "effect_ko": "주간 목재 자원 3배 생산 및 대형 바비큐 고기 5개 무료 보급"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 60,
      "boss_focus_weight": 85,
      "crowd_control_weight": 50,
      "self_preservation_weight": 20
    },
    "inventory_quirks": {
      "quirk_type": "hoard_honey_jars",
      "description_ko": "플레이어 가방의 단 음식과 설탕을 훔쳐 '특제 벌꿀 젤리'로 가공해 넣어둠"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_grizzly_brotherhood_wrestling",
      "name_ko": "불곰 의형제 레슬링 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어가 적에게 붙잡히거나 넘어졌을 때 보리스가 즉시 적을 붙잡아 수플렉스로 메다꽂으며 구출 (턴당 1회)"
    },
    "bond": {
      "tier": 1,
      "current_points": 20,
      "tier_bonuses": {
        "tier_2": "잡기 공격 시 적 방어력 100% 무시",
        "tier_3": "합동 연계기 기절 지속 +1턴",
        "tier_4": "치명타 피격 시 공격력 +20% 분노 버프",
        "tier_5": "사망 방지 1회 및 체력 20% 이하 시 1턴간 완전 불사"
      }
    },
    "recruitment": {
      "location_id": "frozen_bear_den_tavern",
      "reputation_min": -20,
      "reputation_max": 80,
      "completed_quest_id": "quest_treat_grizzly_paw",
      "hire_cost_gold": 100,
      "upkeep_gold_per_day": 7,
      "dialogue_recruit": "으하하! 미샤가 널 마음에 들어 하는군! 내 굵은 팔뚝이 네 방패가 되어 주마!"
    },
    "loot_demands": {
      "gold_share_percent": 10,
      "preferred_item_categories": ["honey", "meat", "two_handed_club"],
      "forbidden_item_types": ["bear_trap"]
    },
    "camp_role": "cook",
    "exploration_talents": ["wild_beast_grappling", "heavy_tree_felling", "blizzard_survival"],
    "companion_relations": {
      "likes": ["companion_fae_beast_whisperer"],
      "dislikes": ["companion_orlaith_bog_trapper"],
      "conflict_event_id": "event_brawler_punches_trapper_traps"
    },
    "combat_skills": [
      {
        "skill_id": "bear_hug_spine_crush",
        "name_ko": "불곰 베어 허그 척추 분쇄",
        "mana_cost": 10,
        "cooldown_turns": 1,
        "effect_type": "grab_root_and_bleed",
        "description_ko": "적 1명을 끌어안고 조여 42의 물리 피해와 1턴간 행동 불능 및 골절을 부여합니다."
      },
      {
        "skill_id": "seismic_suplex_slam",
        "name_ko": "지진 수플렉스 메치기",
        "mana_cost": 14,
        "cooldown_turns": 3,
        "effect_type": "aoe_knockdown_damage",
        "description_ko": "적을 들어 바닥에 내리꽂아 대상에게 45 피해를 주고 주변 적들에게 지진 다운을 유발합니다."
      }
    ],
    "combo_technique": {
      "combo_id": "bear_paw_double_clothesline",
      "name_ko": "더블 래리어트 곰발 강타",
      "trigger_condition": "player_stuns_or_knocks_back_enemy",
      "description_ko": "비틀거리는 적의 목을 통나무 팔뚝으로 걷어올려 목을 꺾으며 75의 타격 대미지를 입힙니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_wrath_of_the_grizzly_avalanche",
      "name_ko": "동토 불곰 눈사태 맹폭",
      "charge_type": "damage_accumulated",
      "charge_required": 100,
      "mana_cost": 20,
      "activation_voice_line": "으오오오! 뼈마디를 모조리 으스러뜨려 주마! 불곰의 일격!",
      "effects": {
        "target": "single_boss",
        "base_damage": 135,
        "stat_scaling": 2.7,
        "status_applied": "spine_fracture_and_paralysis",
        "status_duration": 2,
        "ally_buff": "none"
      },
      "cinematic_description": "보리스가 거대한 영체 불곰과 함께 적 보스를 들어 올려 지면에 수직 낙하 충돌시킴"
    },
    "party_passive": {
      "buff_id": "grizzly_warmth",
      "name_ko": "불곰의 온기",
      "effect_ko": "파티 전체 혹한 지형 동상 피해 100% 면역 및 야영 체력 회복량 +25%"
    },
    "equipment": {
      "weapon": "solid_oak_tree_trunk_club",
      "armor": "heavy_bear_pelt_leather_vest",
      "shield": "none",
      "accessory": "misha_shed_bear_claw"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 4,
      "downed_cry": "미샤… 도망쳐… 형아가… 널 못 지켜줘서… 미안하다…!",
      "death_trauma_to_party": "파티 물리 공격력 20% 영구 저하 및 사기 급감"
    },
    "dialogue_lines": {
      "greeting": "으하하! 힘찬 아침이다! 꿀단지 하나 비우고 시작하자고!",
      "camp_rest": "미샤 털 속에 파묻혀 자면 모닥불도 필요 없지. 좁으면 네 자리도 만들어주마!",
      "low_loyalty_warning": "짐승 괴롭히는 놈 치고 좋은 놈 못 봤다. 손버릇 고쳐라.",
      "traitor_reveal": "네 척추뼈를 통나무처럼 반으로 접어주마!",
      "dismissal": "북부 숲으로 돌아간다. 미샤랑 사냥이나 해야겠어."
    }
  },
  {
    "companion_id": "companion_amira_ink_tide",
    "name_ko": "아미라 잉크위버",
    "title_ko": "수묵화를 그리는 대양의 화서관",
    "role": "arcane_blaster",
    "formation": "backline",
    "speech_style": "timid_scholar",
    "stats": {
      "level": 11,
      "health": 80,
      "max_health": 80,
      "mana": 88,
      "max_mana": 88,
      "strength": 6,
      "agility": 14,
      "constitution": 10,
      "intelligence": 19,
      "wisdom": 15,
      "luck": 13,
      "defense": 9,
      "attack_power": 32
    },
    "personality": {
      "loyalty_score": 50,
      "affinity": 10,
      "moral_alignment": "neutral_good",
      "desire": "세상의 모든 전쟁을 먹물로 덧칠해 지우는 전설의 '천지개벽 수묵화첩' 완성",
      "taboo": "그림 훼손, 벼루 파손, 화폭에 피 튀기기",
      "hidden_secret": "자신의 혈액이 신비한 검은 먹물로 변해 있어 피부가 상처 입으면 수묵화 선이 그려짐",
      "betrayal_trigger": "플레이어가 아미라의 수묵화첩을 찢어 위조 화폐나 사기 문서로 쓸 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "천지창조의 수묵화성 (화폭 구원)",
        "trigger_condition": "그림 속의 영수들을 온전히 실체화하여 황폐해진 대지를 비옥하게 복원",
        "stat_modifiers": { "intelligence": 6, "wisdom": 5 },
        "unlocked_skill": "skill_ink_landscape_restoration",
        "personality_shift": "붓질 하나로 세상을 치유하고 평화를 그리는 온화한 화성"
      },
      "path_b": {
        "branch_name_ko": "흑사 수묵화 마수술사 (먹물 질식)",
        "trigger_condition": "적들의 비명과 피를 먹물로 흡수하여 살아있는 먹물 괴수를 무한 증식",
        "stat_modifiers": { "attack_power": 14, "constitution": -4 },
        "unlocked_skill": "skill_abyssal_ink_dragon_carnage",
        "personality_shift": "세상을 온통 검은 먹물로 칠해 숨을 헐떡이게 만드는 광기 어린 화가"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "water_bleed_blur_panic",
      "flaw_name_ko": "수묵화 번짐 패닉",
      "trigger_condition": "struck_by_heavy_water_magic",
      "effect_ko": "붓의 먹물이 번져 2턴간 마법 영창 실패율 40% 및 마나 소실"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 지도 제작 및 위장 수묵화 장막",
      "effect_ko": "거점 발견율 0% 완전 은폐 및 던전 보물/함정 지도 100% 사전 완성"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 30,
      "boss_focus_weight": 60,
      "crowd_control_weight": 85,
      "self_preservation_weight": 55
    },
    "inventory_quirks": {
      "quirk_type": "paint_ink_camo_on_scrolls",
      "description_ko": "플레이어 마법 스크롤에 수묵화를 덧그려 위력을 15% 몰래 강화"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_ink_drawn_guardian_beast",
      "name_ko": "화폭 속 수호수 소환 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어가 위험에 처할 때마다 화폭에서 '먹물 호랑이'가 튀어나와 적을 공격하고 피해를 대신 흡수"
    },
    "bond": {
      "tier": 1,
      "current_points": 15,
      "tier_bonuses": {
        "tier_2": "실명 상태 적 대상 마법 피해 +20%",
        "tier_3": "합동 연계기 암흑 속박 지속 +1턴",
        "tier_4": "마법 스크롤 사용 시 30% 확률로 소모 무효",
        "tier_5": "사망 방지 1회 및 수묵화 소환수 체력 +50%"
      }
    },
    "recruitment": {
      "location_id": "bamboo_grove_ink_pavilion",
      "reputation_min": 0,
      "reputation_max": 90,
      "completed_quest_id": "quest_grind_celestial_inkstone",
      "hire_cost_gold": 110,
      "upkeep_gold_per_day": 8,
      "dialogue_recruit": "붓 끝에 세상이 담깁니다. 당신의 여정을 검은 먹물과 화려한 빛으로 기록하겠습니다."
    },
    "loot_demands": {
      "gold_share_percent": 10,
      "preferred_item_categories": ["inkstone", "brush", "scroll"],
      "forbidden_item_types": []
    },
    "camp_role": "scholar",
    "exploration_talents": ["topographical_map_drawing", "illusion_painting_bypass", "ink_clone_scouting"],
    "companion_relations": {
      "likes": ["companion_ignis_cinder_scholar"],
      "dislikes": ["companion_chiyo_origami_dancer"],
      "conflict_event_id": "event_ink_spills_on_paper_dancer"
    },
    "combat_skills": [
      {
        "skill_id": "ink_brush_tiger_stroke",
        "name_ko": "수묵 호랑이 일필휘지",
        "mana_cost": 16,
        "cooldown_turns": 1,
        "effect_type": "summon_and_slash",
        "description_ko": "먹물 호랑이를 그려 날려 보내 적 1명에게 42의 암흑/물리 복합 피해를 입힙니다."
      },
      {
        "skill_id": "splashing_black_ink_blindness",
        "name_ko": "묵죽화 먹물 살포",
        "mana_cost": 20,
        "cooldown_turns": 3,
        "effect_type": "aoe_blind_and_slow",
        "description_ko": "공중에 먹물을 흩뿌려 적 전체를 2턴간 실명시키고 이동 속도를 40% 깎습니다."
      }
    ],
    "combo_technique": {
      "combo_id": "ink_dragon_water_surge",
      "name_ko": "수묵 흑룡 수류포",
      "trigger_condition": "player_uses_water_or_dark_magic",
      "description_ko": "플레이어의 물줄기에 아미라의 먹물이 융합되어 거대한 먹물 용이 적진을 휩쓸며 75의 피해를 줍니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_landscape_scroll_annihilation",
      "name_ko": "만경산수화 세계 봉인",
      "charge_type": "turns_delay",
      "charge_required": 4,
      "mana_cost": 40,
      "activation_voice_line": "화폭이 열린다! 모든 사악함은 먹물 속에 영원히 갇히리라!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 84,
        "stat_scaling": 2.3,
        "status_applied": "ink_seal_paralysis",
        "status_duration": 2,
        "ally_buff": "party_crit_chance_up_20"
      },
      "cinematic_description": "전장 전체가 거대한 두루마리 수묵화 풍경으로 빨려 들어가며 붓질 한 번에 적들이 먹물로 지워짐"
    },
    "party_passive": {
      "buff_id": "ink_camo_veil",
      "name_ko": "수묵의 은폐 장막",
      "effect_ko": "파티 전체가 적의 기습 공격을 받을 확률 100% 무효화"
    },
    "equipment": {
      "weapon": "giant_calligraphy_horsehair_brush",
      "armor": "ink_stained_silk_hanbok",
      "shield": "none",
      "accessory": "bottomless_black_jade_inkstone"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 3,
      "downed_cry": "먹물이… 번져버렸어… 화폭이… 찢어진다… 구해줘요…!",
      "death_trauma_to_party": "파티 지도 탐색 능력 영구 상실 및 실명 저항력 하락"
    },
    "dialogue_lines": {
      "greeting": "새하얀 화폭을 보면 설렙니다. 오늘 당신은 어떤 이야기를 그리실 건가요?",
      "camp_rest": "벼루를 갈며 먹을 만드는 시간은 마음을 차분하게 합니다. 장작불 빛이 참 곱군요.",
      "low_loyalty_warning": "당신의 여정에 아름다움이 사라지고 추악한 먹물만 튀고 있습니다. 경고합니다.",
      "traitor_reveal": "당신이라는 존재를 이 세상 화폭에서 영원히 먹물로 지워버리겠습니다.",
      "dismissal": "대나무 숲으로 돌아갑니다. 언젠가 좋은 풍경으로 다시 만나지요."
    }
  },
  {
    "companion_id": "companion_vincenzo_tax_collector",
    "name_ko": "빈센조 코인바운드",
    "title_ko": "황금 장부의 영혼 수세관",
    "role": "healer_support",
    "formation": "backline",
    "speech_style": "archaic_noble",
    "stats": {
      "level": 12,
      "health": 82,
      "max_health": 82,
      "mana": 90,
      "max_mana": 90,
      "strength": 6,
      "agility": 12,
      "constitution": 11,
      "intelligence": 18,
      "wisdom": 15,
      "luck": 20,
      "defense": 10,
      "attack_power": 16
    },
    "personality": {
      "loyalty_score": 50,
      "affinity": 5,
      "moral_alignment": "lawful_neutral",
      "desire": "생명과 영혼의 가치를 화폐 단위로 환산한 '절대 가치 대장부' 완성",
      "taboo": "위조 화폐 유통, 계약서 무단 소각, 무이자 채무 탕감",
      "hidden_secret": "자신의 수명을 1년 단위로 금화로 환전해 사용 중이라 몸무게가 항상 금화 1,000닢 무게로 고정됨",
      "betrayal_trigger": "플레이어가 국가 금고를 털어 돈을 불태우거나 인플레이션을 고의 조장할 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "황금 구휼의 자선 재정관 (부의 재분배)",
        "trigger_condition": "약탈당한 빈민들의 세금을 온전히 환급하고 독점 상단을 합법 해체",
        "stat_modifiers": { "wisdom": 6, "luck": 5 },
        "unlocked_skill": "skill_golden_tithe_rejuvenation",
        "personality_shift": "돈을 생명을 살리고 순환시키는 혈액으로 다루는 공정한 재정관"
      },
      "path_b": {
        "branch_name_ko": "영혼 압류의 악덕 사채업자 (생명 담보화)",
        "trigger_condition": "채무자들의 영혼과 장기를 담보로 잡아 거대 고리대금 제국 설립",
        "stat_modifiers": { "intelligence": 8, "attack_power": 10 },
        "unlocked_skill": "skill_foreclosure_of_mortal_flesh",
        "personality_shift": "모든 숨결에 세금을 매겨 강제 징수하는 잔혹한 영혼 압류관"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "bankruptcy_horror_paralysis",
      "flaw_name_ko": "골드 파산 공황증",
      "trigger_condition": "party_gold_drops_below_100",
      "effect_ko": "극심한 파산 공포로 2턴간 마나 소모량 2배 증가 및 손떨림으로 스킬 실패율 35% 발생"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 금융 투자 및 복리 이자 운용",
      "effect_ko": "파티 보유 골드에 대해 주간 5% 복리 이자 지급 및 상점 거래 수수료 면제"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 70,
      "boss_focus_weight": 20,
      "crowd_control_weight": 85,
      "self_preservation_weight": 60
    },
    "inventory_quirks": {
      "quirk_type": "appraise_and_stamp_gold",
      "description_ko": "플레이어 가방의 잡동사니에 감정 직인을 찍어 상점 매각가를 20% 상승시켜둠"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_soul_debt_collateral",
      "name_ko": "영혼 채무 담보 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어가 치명상을 입을 때 사망 대신 보유 골드 500G를 자동 지불하여 체력 100% 즉시 부활"
    },
    "bond": {
      "tier": 1,
      "current_points": 15,
      "tier_bonuses": {
        "tier_2": "전투 후 골드 획득량 +15%",
        "tier_3": "합동 연계기 골드 강탈 확률 100%",
        "tier_4": "적 골드 보유량 비례 추가 고정 피해",
        "tier_5": "사망 방지 1회 및 상점 아이템 50% 반값 구매"
      }
    },
    "recruitment": {
      "location_id": "iron_bank_vault_archives",
      "reputation_min": -20,
      "reputation_max": 80,
      "completed_quest_id": "quest_audit_the_corrupt_duke",
      "hire_cost_gold": 200,
      "upkeep_gold_per_day": 15,
      "dialogue_recruit": "세상에 공짜는 없습니다. 하지만 당신의 미래 가치에 합당한 투자를 해보도록 하죠."
    },
    "loot_demands": {
      "gold_share_percent": 20,
      "preferred_item_categories": ["gold_coin", "gem", "ledger"],
      "forbidden_item_types": ["counterfeit_coin"]
    },
    "camp_role": "scholar",
    "exploration_talents": ["hidden_vault_cracking", "bribe_negotiation", "appraisal_lore"],
    "companion_relations": {
      "likes": ["companion_brian_the_bard"],
      "dislikes": ["companion_vane_shadowfang"],
      "conflict_event_id": "event_taxman_audits_rogue_pockets"
    },
    "combat_skills": [
      {
        "skill_id": "compound_interest_curse",
        "name_ko": "복리 이자 징수 저주",
        "mana_cost": 18,
        "cooldown_turns": 2,
        "effect_type": "exponential_dot",
        "description_ko": "적 1체에 징수령을 내려 첫 턴 10 피해, 다음 턴 20 피해, 3번째 턴 40 피해로 2배씩 폭증하는 고정 피해를 입힙니다."
      },
      {
        "skill_id": "golden_bailout_injection",
        "name_ko": "긴급 구제 금융 수혈",
        "mana_cost": 22,
        "cooldown_turns": 3,
        "effect_type": "gold_scale_heal",
        "description_ko": "파티 보유 골드의 1%를 촉매로 소모하여 아군 전체 체력을 45 회복시키고 사기를 최고조로 올립니다."
      }
    ],
    "combo_technique": {
      "combo_id": "debt_default_liquidation",
      "name_ko": "채무 불이행 강제 청산",
      "trigger_condition": "player_lands_critical_hit_on_debuffed_enemy",
      "description_ko": "디버프에 걸린 적의 남은 모든 디버프 피해를 현금 청산하듯 즉시 일괄 격발하여 80의 금속 파편 피해를 가합니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_hostile_takeover_foreclosure",
      "name_ko": "절대 영혼 압류 : 적대적 M&A",
      "charge_type": "crit_count",
      "charge_required": 3,
      "mana_cost": 40,
      "activation_voice_line": "장부를 덮을 시간이다. 네 숨결, 근육, 마력까지… 전부 압류하겠다!",
      "effects": {
        "target": "single_boss",
        "base_damage": 0,
        "stat_scaling": 0.0,
        "status_applied": "total_asset_foreclosure",
        "status_duration": 3,
        "ally_buff": "party_all_stats_buff_equal_to_boss_stats"
      },
      "cinematic_description": "황금빛 계약서 사슬이 적 보스를 휘감아 보스의 공격력과 방어력 50%를 강제 압류해 3턴간 파티원 전체에게 균등 배당 분배함"
    },
    "party_passive": {
      "buff_id": "mercenary_payroll_bonus",
      "name_ko": "확실한 성과급 체계",
      "effect_ko": "파티원 체력이 50% 이하일 때 골드 획득량이 실시간 공격력으로 전환되어 공격력 +5"
    },
    "equipment": {
      "weapon": "golden_abacus_flail",
      "armor": "silk_velvet_banker_frock",
      "shield": "none",
      "accessory": "endless_coin_purse_ledger"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 3,
      "downed_cry": "장부의… 대변과 차변이… 맞지 않아… 파산이다…!",
      "death_trauma_to_party": "파티 골드 50% 증발 및 상점 물가 50% 영구 폭등"
    },
    "dialogue_lines": {
      "greeting": "시간은 금입니다. 쓸데없는 잡담은 분당 10골드로 청구하겠습니다.",
      "camp_rest": "장작불 빛으로 금화의 순도를 감정하는 중입니다. 숫자는 거짓말을 하지 않지요.",
      "low_loyalty_warning": "수지타산이 전혀 맞지 않는 모험이군요. 조만간 계약을 일방 해지하겠습니다.",
      "traitor_reveal": "당신의 목숨값은 이미 다른 의뢰인에게 전액 선납되었습니다. 청산해 드리죠.",
      "dismissal": "은행으로 복귀합니다. 다음 거래 때는 신용도를 올려서 오십시오."
    }
  },
  {
    "companion_id": "companion_morpheus_sculptor",
    "name_ko": "카르미나 락셰이퍼",
    "title_ko": "전장의 점토 살점을 빚는 가소(可塑)술사",
    "role": "tank",
    "formation": "frontline",
    "speech_style": "rough_mercenary",
    "stats": {
      "level": 12,
      "health": 142,
      "max_health": 142,
      "mana": 35,
      "max_mana": 35,
      "strength": 18,
      "agility": 9,
      "constitution": 17,
      "intelligence": 13,
      "wisdom": 11,
      "luck": 10,
      "defense": 19,
      "attack_power": 24
    },
    "personality": {
      "loyalty_score": 55,
      "affinity": 10,
      "moral_alignment": "chaotic_neutral",
      "desire": "세상의 모든 굳어버린 돌과 뼈를 부드럽게 빚어내는 '생명의 원초 가소 점토' 복원",
      "taboo": "조각상 고의 파손, 점토 건조 소각, 형상을 비웃는 행위",
      "hidden_secret": "자신의 양팔이 점토로 빚어져 있어 형태를 마음대로 칼, 망치, 방패로 변형 가능함",
      "betrayal_trigger": "플레이어가 카르미나가 만든 전사자 추모 조각상을 부수거나 짓밟을 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "생명 재형성의 거장 조각가 (신체 복원)",
        "trigger_condition": "점토 마법으로 절단된 부상자들의 사지를 온전한 생체 장기로 빚어냄",
        "stat_modifiers": { "defense": 8, "wisdom": 4 },
        "unlocked_skill": "skill_clay_flesh_regeneration",
        "personality_shift": "상처 입은 모든 이의 형태를 어루만져 복원하는 든든한 조각가"
      },
      "path_b": {
        "branch_name_ko": "인체 반죽의 기괴한 변이술사 (육신 왜곡)",
        "trigger_condition": "적들의 살아있는 뼈와 살을 강제로 점토처럼 뭉개 기형 흉물로 조작",
        "stat_modifiers": { "attack_power": 14, "defense": -2 },
        "unlocked_skill": "skill_grotesque_flesh_kneading",
        "personality_shift": "모든 생명체를 자기 취향대로 주물러 비틀어버리는 광기의 조형사"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "kiln_fire_baking_rigidity",
      "flaw_name_ko": "점토 소성(燒成) 경화증",
      "trigger_condition": "fire_magic_taken_in_combat",
      "effect_ko": "점토 팔이 도자기처럼 딱딱하게 구워져 2턴간 형상 변형 불가 및 충격 피격 시 균열 자해"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 성벽 지형 점토 재형성 공사",
      "effect_ko": "거점 주변 지형을 자유자재로 해자/성벽으로 개조해 적 공성 침입 80% 차단"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 80,
      "boss_focus_weight": 40,
      "crowd_control_weight": 70,
      "self_preservation_weight": 20
    },
    "inventory_quirks": {
      "quirk_type": "reshape_blunt_tools",
      "description_ko": "플레이어 가방의 부러진 무기를 점토처럼 주물러 완제품 무기로 재성형 수리"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_plastic_flesh_sharing",
      "name_ko": "가소성 육체 결속 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어가 부상을 입을 때 카르미나의 점토 살점이 날아와 상처를 메워 출혈/골절을 즉시 100% 무효화"
    },
    "bond": {
      "tier": 1,
      "current_points": 15,
      "tier_bonuses": {
        "tier_2": "방패 형태 변형 시 방어력 +4",
        "tier_3": "합동 연계기 적 지형 속박 지속 +1턴",
        "tier_4": "물리 관통 피해 40% 흡수",
        "tier_5": "사망 방지 1회 및 팔을 거대 망치로 영구 변형"
      }
    },
    "recruitment": {
      "location_id": "living_clay_quarry",
      "reputation_min": -30,
      "reputation_max": 70,
      "completed_quest_id": "quest_knead_the_primordial_mud",
      "hire_cost_gold": 100,
      "upkeep_gold_per_day": 7,
      "dialogue_recruit": "단단한 바위도 내 손안에선 찰흙일 뿐이지. 네 전열을 가장 부드럽고 단단하게 빚어주마."
    },
    "loot_demands": {
      "gold_share_percent": 10,
      "preferred_item_categories": ["clay", "chisel", "mineral_oil"],
      "forbidden_item_types": ["quicklime"]
    },
    "camp_role": "blacksmith",
    "exploration_talents": ["terrain_softening", "stone_door_reshaping", "mud_sculpture_decoy"],
    "companion_relations": {
      "likes": ["companion_baldur_living_mountain"],
      "dislikes": ["companion_ignis_cinder_scholar"],
      "conflict_event_id": "event_sculptor_quarrels_with_fire_mage"
    },
    "combat_skills": [
      {
        "skill_id": "morphing_clay_mace_slam",
        "name_ko": "형상변형 점토 메이스 강타",
        "mana_cost": 12,
        "cooldown_turns": 1,
        "effect_type": "variable_weapon_strike",
        "description_ko": "팔을 5배 크기의 점토 철퇴로 빚어 내려찍어 38의 물리 피해와 1칸 넉백 및 다운을 줍니다."
      },
      {
        "skill_id": "quicksand_clay_trap",
        "name_ko": "지반 액상화 수렁 빚기",
        "mana_cost": 16,
        "cooldown_turns": 3,
        "effect_type": "aoe_terrain_soften",
        "description_ko": "적 발밑의 지면을 부드러운 점토로 반죽하여 2턴간 적 전열의 이동력과 회피율을 50% 깎습니다."
      }
    ],
    "combo_technique": {
      "combo_id": "clay_mold_impact_crush",
      "name_ko": "점토 주형 압살 분쇄",
      "trigger_condition": "player_knocks_enemy_into_ground",
      "description_ko": "바닥에 처박힌 적을 점토 거푸집으로 감싸 굳힌 뒤 플레이어와 함께 박살 내어 75의 파편 피해를 가합니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_world_reshaping_golem_crucible",
      "name_ko": "천지 조형 : 원초 점토 도가니",
      "charge_type": "damage_accumulated",
      "charge_required": 100,
      "mana_cost": 25,
      "activation_voice_line": "굳어있는 모든 것은 부서진다! 대지여, 내 손안에서 다시 빚어져라!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 50,
        "stat_scaling": 1.5,
        "status_applied": "total_terrain_plasticity",
        "status_duration": 3,
        "ally_buff": "party_damage_immunity_to_ground_attacks"
      },
      "cinematic_description": "전장의 바닥과 적들의 갑옷을 점토로 연화시켜 3턴간 적들의 물리 방어력을 0으로 만들고 이동을 완전 봉쇄함"
    },
    "party_passive": {
      "buff_id": "malleable_posture",
      "name_ko": "유연한 체구",
      "effect_ko": "파티 전체 넉백/낙하/지진 피해 50% 상시 경감"
    },
    "equipment": {
      "weapon": "chameleon_clay_hammer_arm",
      "armor": "flexible_ceramic_scale_tunic",
      "shield": "none",
      "accessory": "primordial_clay_pot"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 4,
      "downed_cry": "팔이… 말라비틀어져… 부서진다… 물을… 물을 줘…!",
      "death_trauma_to_party": "파티 방어구 수리 불가 및 물리 방어력 20% 영구 저하"
    },
    "dialogue_lines": {
      "greeting": "손에 진흙 좀 묻히면 어때? 굳어버린 머통보단 부드러운 찰흙이 낫지.",
      "camp_rest": "장작불 곁에서 점토를 주무르고 있으면 잡생각이 사라져. 네 얼굴도 하나 빚어줄까?",
      "low_loyalty_warning": "딱딱하게 굳은 꼰대처럼 굴면 네 갑옷을 찰흙으로 주물러 찌그러뜨릴 거다.",
      "traitor_reveal": "너라는 인간을 바닥에 내동댕이쳐서 진흙 반죽으로 짓이겨주마.",
      "dismissal": "점토 채석장으로 간다. 주무를 돌이 많은 곳이 최고지."
    }
  },
  {
    "companion_id": "companion_zeth_glass_cannon",
    "name_ko": "제스 크리스탈라인",
    "title_ko": "체온이 서리로 굳은 과포화 수정 사수",
    "role": "dps_ranged",
    "formation": "backline",
    "speech_style": "stoic_veteran",
    "stats": {
      "level": 12,
      "health": 68,
      "max_health": 68,
      "mana": 70,
      "max_mana": 70,
      "strength": 8,
      "agility": 18,
      "constitution": 8,
      "intelligence": 16,
      "wisdom": 14,
      "luck": 17,
      "defense": 6,
      "attack_power": 38
    },
    "personality": {
      "loyalty_score": 45,
      "affinity": 5,
      "moral_alignment": "chaotic_neutral",
      "desire": "자신의 폐 속에 자라나는 과포화 수정 결정을 부수지 않고 공존할 해독액 조합",
      "taboo": "수정 렌즈 무단 흠집 내기, 고열 불가마 투입, 둔기로 수정 타격",
      "hidden_secret": "체력이 1이 될 때 공격력이 3배로 폭증하지만 스치기만 해도 깨지는 유리 심장을 가짐",
      "betrayal_trigger": "플레이어가 제스의 몸에서 자라난 수정을 억지로 뜯어내 보석상에 매각할 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "프리즘 다이아몬드 사수 (초결정 안정화)",
        "trigger_condition": "수정 침식을 다이아몬드 구조로 안정화하여 완벽한 방어와 화력을 양립",
        "stat_modifiers": { "defense": 10, "agility": 4 },
        "unlocked_skill": "skill_diamond_lattice_bullet",
        "personality_shift": "깨지지 않는 단단한 마음으로 전우를 지키는 냉정 침착한 명사수"
      },
      "path_b": {
        "branch_name_ko": "유리 파편 자폭 사수 (파멸 과충전)",
        "trigger_condition": "수정을 제어하지 않고 전신을 유리 폭탄으로 전환하여 적과 동귀어진",
        "stat_modifiers": { "attack_power": 18, "health": -20 },
        "unlocked_skill": "skill_glass_shrapnel_kamikaze",
        "personality_shift": "자신의 부서짐을 두려워하지 않고 모든 것을 갈아버리는 광기의 저격수"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "brittle_bone_fracture_panic",
      "flaw_name_ko": "유리 골절 산산조각 공포",
      "trigger_condition": "blunt_damage_taken_from_heavy_hammer",
      "effect_ko": "유리 피부에 금이 가 2턴간 이동 불가 및 피격 대미지 2배 증폭"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 초정밀 수정 렌즈 망루 조준",
      "effect_ko": "거점 방어 시 모든 적에게 방어 무시 관통 수정 탄환 자동 3발 발사"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 10,
      "boss_focus_weight": 95,
      "crowd_control_weight": 40,
      "self_preservation_weight": 90
    },
    "inventory_quirks": {
      "quirk_type": "grow_crystal_bullets",
      "description_ko": "자신의 몸에서 자란 날카로운 수정 파편을 플레이어 가방에 특수 관통 탄환으로 채워넣음"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_resonant_glass_cannon",
      "name_ko": "유리 대포 공명 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어와 제스의 공격력이 서로의 공격력의 30%만큼 합산되어 상시 가산 (화력 극대화)"
    },
    "bond": {
      "tier": 1,
      "current_points": 10,
      "tier_bonuses": {
        "tier_2": "원거리 치명타 피해량 +30%",
        "tier_3": "합동 연계기 수정 파편 도트 2배",
        "tier_4": "체력 30% 이하 시 공격력 50% 추가 증가",
        "tier_5": "사망 방지 1회 및 체력 1 남을 시 확정 100% 치명타"
      }
    },
    "recruitment": {
      "location_id": "overgrown_crystal_geode_chasm",
      "reputation_min": -30,
      "reputation_max": 70,
      "completed_quest_id": "quest_harvest_pure_quartz_lens",
      "hire_cost_gold": 140,
      "upkeep_gold_per_day": 10,
      "dialogue_recruit": "날 건드리지 마라. 스치기만 해도 깨지지만, 내 총구는 신이라도 꿰뚫으니까."
    },
    "loot_demands": {
      "gold_share_percent": 15,
      "preferred_item_categories": ["crystal", "quartz", "gunpowder"],
      "forbidden_item_types": ["blunt_mace"]
    },
    "camp_role": "scholar",
    "exploration_talents": ["crystal_resonance_detection", "glass_cutting", "extreme_long_shot"],
    "companion_relations": {
      "likes": ["companion_malik_dune_sniper"],
      "dislikes": ["companion_garrick_chain_breaker"],
      "conflict_event_id": "event_brawler_accidentally_cracks_sniper_crystals"
    },
    "combat_skills": [
      {
        "skill_id": "hyper_dense_quartz_slug",
        "name_ko": "초고밀도 석영 탄환 사격",
        "mana_cost": 15,
        "cooldown_turns": 1,
        "effect_type": "extreme_single_piercing",
        "description_ko": "수정 장총을 발사해 52의 방어 무시 관통 피해를 입히고 대상 뒤편 1칸까지 관통 타격합니다."
      },
      {
        "skill_id": "crystal_shrapnel_burst",
        "name_ko": "수정 파편 지뢰 살포",
        "mana_cost": 18,
        "cooldown_turns": 3,
        "effect_type": "aoe_bleed_shrapnel",
        "description_ko": "유리 지뢰를 터뜨려 적 2명에게 각 35의 출혈 피해를 입히고 반사 피해를 부여합니다."
      }
    ],
    "combo_technique": {
      "combo_id": "prismatic_bullet_resonance",
      "name_ko": "프리즘 탄환 굴절 저격",
      "trigger_condition": "player_uses_laser_or_light_spell",
      "description_ko": "빛 마법 줄기를 수정 탄환으로 굴절시켜 적 보스의 심장에 85의 확정 치명타 피해를 내리꽂습니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_super_critical_crystal_implosion",
      "name_ko": "과포화 결정 붕괴 : 초임계 사격",
      "charge_type": "crit_count",
      "charge_required": 3,
      "mana_cost": 30,
      "activation_voice_line": "내 몸이 산산조각 나더라도… 이 한 발로 널 영원히 지워버리겠다!",
      "effects": {
        "target": "single_boss",
        "base_damage": 160,
        "stat_scaling": 3.0,
        "status_applied": "total_crystallization_death_mark",
        "status_duration": 2,
        "ally_buff": "none"
      },
      "cinematic_description": "자신의 수정 혈관을 과충전시켜 몸에 금이 가며 뿜어내는 초거대 크리스탈 철갑탄으로 보스의 전신을 결정화시켜 산산조각 냄"
    },
    "party_passive": {
      "buff_id": "critical_overdrive",
      "name_ko": "치명타 과부하",
      "effect_ko": "파티 전체 치명타 배율이 기본 1.5배에서 2.0배로 상시 증폭"
    },
    "equipment": {
      "weapon": "heavy_crystal_bore_anti_tank_rifle",
      "armor": "brittle_quartz_woven_coat",
      "shield": "none",
      "accessory": "overcharged_geode_core"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 2,
      "downed_cry": "몸에… 금이 간다… 유리처럼… 깨져버린다… 손대지 마…!",
      "death_trauma_to_party": "파티 치명타 피해량 40% 영구 감소 및 공포 부여"
    },
    "dialogue_lines": {
      "greeting": "앞을 가리지 마라. 내 총알은 아군도 꿰뚫고 지나가니까.",
      "camp_rest": "체온이 차가워지는 건 익숙해. 장작불에 너무 가까이 가면 수정이 터져버리니 멀리 있겠어.",
      "low_loyalty_warning": "날 고기방패로 쓸 생각 마라. 깨지기 전에 네 심장부터 날려버릴 테니.",
      "traitor_reveal": "1,500미터 밖에서 네 두개골을 수정 가루로 만들어 주지.",
      "dismissal": "수정 동굴로 돌아간다. 말 걸지 마라."
    }
  },
  {
    "companion_id": "companion_seraphina_blind_choir",
    "name_ko": "세라피나 보이드송",
    "title_ko": "성대를 도려낸 심연의 성가대원",
    "role": "healer_support",
    "formation": "midline",
    "speech_style": "stoic_veteran",
    "stats": {
      "level": 12,
      "health": 84,
      "max_health": 84,
      "mana": 92,
      "max_mana": 92,
      "strength": 6,
      "agility": 11,
      "constitution": 12,
      "intelligence": 16,
      "wisdom": 19,
      "luck": 13,
      "defense": 10,
      "attack_power": 19
    },
    "personality": {
      "loyalty_score": 60,
      "affinity": 15,
      "moral_alignment": "lawful_good",
      "desire": "세상의 모든 고통스러운 비명을 흡수해 침묵으로 정화하는 '영혼의 침묵 성당' 건립",
      "taboo": "소음 고문, 청각 장애인 모욕, 성스러운 종탑 파괴",
      "hidden_secret": "스스로 성대를 잘라 신에게 바쳤기에 말을 못 하며 오직 텔레파시 하프 선율로만 소통함",
      "betrayal_trigger": "플레이어가 비명 소리를 녹음해 음파 고문 무기로 사용할 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "침묵의 대성녀 (절대 평온)",
        "trigger_condition": "전장의 모든 소음을 흡수하여 아군을 고통 없는 열반의 상태로 인도",
        "stat_modifiers": { "wisdom": 8, "mana": 15 },
        "unlocked_skill": "skill_silent_seraph_nirvana",
        "personality_shift": "말 한마디 없이도 만인을 품어주는 성스러운 대치유사"
      },
      "path_b": {
        "branch_name_ko": "고막 파열의 심연 성음마녀 (비명 반사)",
        "trigger_condition": "흡수한 전 세계의 고통 비명을 적들의 뇌리에 그대로 역류 격발",
        "stat_modifiers": { "attack_power": 14, "wisdom": -2 },
        "unlocked_skill": "skill_screaming_void_rupture",
        "personality_shift": "적들의 고막과 뇌수를 비명 소리로 터뜨려 죽이는 잔혹한 복수귀"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "screaming_resonance_headache",
      "flaw_name_ko": "원혼 비명 과부하 두통",
      "trigger_condition": "party_members_scream_in_fear",
      "effect_ko": "원혼들의 비명이 뇌리에 울려 2턴간 마나 소모 2배 및 행동 정지 확률 30%"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 완전 방음 결계 및 멘탈 치유소 운영",
      "effect_ko": "거점 내 야간 스트레스 회복량 3배 및 적 도청/스파이 100% 차단"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 90,
      "boss_focus_weight": 10,
      "crowd_control_weight": 80,
      "self_preservation_weight": 40
    },
    "inventory_quirks": {
      "quirk_type": "weave_soundproof_cloth",
      "description_ko": "플레이어 방어구 틈새에 방음 솜을 넣어 기습 이동 소음을 0으로 만들어둠"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_telepathic_choir_synchrony",
      "name_ko": "무언의 텔레파시 공명 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "파티원 전체의 텔레파시 결속으로 명령 전달 딜레이 0 및 턴 순서와 상관없이 즉시 협공 반응 가능"
    },
    "bond": {
      "tier": 1,
      "current_points": 20,
      "tier_bonuses": {
        "tier_2": "침묵 상태이상 부여 성공률 +25%",
        "tier_3": "합동 연계기 적 영창 취소 확정",
        "tier_4": "파티 멘탈 붕괴 완전 면역",
        "tier_5": "사망 방지 1회 및 침묵 결계 무적 1턴 부여"
      }
    },
    "recruitment": {
      "location_id": "silent_cathedral_crypt",
      "reputation_min": 10,
      "reputation_max": 100,
      "completed_quest_id": "quest_recover_the_mute_harp",
      "hire_cost_gold": 0,
      "upkeep_gold_per_day": 0,
      "dialogue_recruit": "(조용히 손을 얹으며 마음에 은은한 하프 선율을 울립니다. 그녀의 눈동자가 당신을 따르겠다고 말합니다.)"
    },
    "loot_demands": {
      "gold_share_percent": 0,
      "preferred_item_categories": ["harp_string", "holy_relic", "incense"],
      "forbidden_item_types": ["bell", "horn"]
    },
    "camp_role": "medic",
    "exploration_talents": ["silent_exploration_aura", "curse_absorption", "telepathic_mind_link"],
    "companion_relations": {
      "likes": ["companion_lyra_dawnbringer"],
      "dislikes": ["companion_freya_spirit_drummer"],
      "conflict_event_id": "event_choir_shuns_loud_drummer"
    },
    "combat_skills": [
      {
        "skill_id": "hymn_of_hushed_agony",
        "name_ko": "고통을 삼키는 무언의 성가",
        "mana_cost": 18,
        "cooldown_turns": 1,
        "effect_type": "single_heal_and_pain_share",
        "description_ko": "아군 1명의 고통을 흡수해 체력을 45 치유하고 적 1명에게 그 고통을 침묵 디버프로 전이합니다."
      },
      {
        "skill_id": "dome_of_absolute_silence",
        "name_ko": "절대 침묵의 장막",
        "mana_cost": 24,
        "cooldown_turns": 3,
        "effect_type": "aoe_silence_and_cleanse",
        "description_ko": "전장에 무음 결계를 쳐서 적 전체의 마법 영창을 2턴간 취소시키고 아군의 모든 디버프를 정화합니다."
      }
    ],
    "combo_technique": {
      "combo_id": "muted_resonance_implosion",
      "name_ko": "무음 공명 내파격",
      "trigger_condition": "player_inflicts_stun_or_silence",
      "description_ko": "침묵에 걸린 적의 내부 소리를 진공으로 압축해 터뜨리며 72의 방어 무시 정신 피해를 가합니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_requiem_of_the_void_choir",
      "name_ko": "심연 성가대 : 완전 무음의 레퀴엠",
      "charge_type": "morale_and_damage",
      "charge_required": 100,
      "mana_cost": 40,
      "activation_voice_line": "(말없이 하프를 뜯자 전장의 모든 소리가 완벽히 소멸하고 백색 소음만이 감돕니다.)",
      "effects": {
        "target": "all_enemies",
        "base_damage": 0,
        "stat_scaling": 0.0,
        "status_applied": "total_sensory_deprivation_stop",
        "status_duration": 2,
        "ally_buff": "full_party_invulnerable_and_heal_60"
      },
      "cinematic_description": "전장의 모든 소음과 마법이 진공 상태로 흡수되어 2턴간 모든 적의 스킬/공격을 완전 정지시키고 아군을 100% 무적으로 치유함"
    },
    "party_passive": {
      "buff_id": "serene_silence",
      "name_ko": "고요한 안식",
      "effect_ko": "파티 전체가 공포/혼란/도발/매혹 등 모든 정신계 상태이상에 100% 영구 면역"
    },
    "equipment": {
      "weapon": "stringless_silver_void_harp",
      "armor": "pure_white_choir_vestments",
      "shield": "none",
      "accessory": "severed_vocal_cord_reliquary"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 3,
      "downed_cry": "(소리 없는 눈물을 흘리며 텔레파시로 아군들에게 마지막 기도를 보냅니다…)",
      "death_trauma_to_party": "파티 힐량 50% 영구 감소 및 공포 상태이상 유발"
    },
    "dialogue_lines": {
      "greeting": "(조용히 고개를 숙여 인사합니다. 마음에 따뜻한 온기가 스며듭니다.)",
      "camp_rest": "(타오르는 장작불 소리를 조용히 묵음으로 다스리며 당신의 피로를 풀어줍니다.)",
      "low_loyalty_warning": "(마음속으로 깊은 슬픔과 경고의 불협화음이 울려 퍼집니다. 잔혹함을 멈추십시오.)",
      "traitor_reveal": "(하프의 줄을 튕겨 당신의 뇌혈관을 고요히 파열시킵니다.)",
      "dismissal": "(조용히 성당을 향해 발걸음을 옮깁니다. 마음에 평화가 깃들길.)"
    }
  },
  {
    "companion_id": "companion_titus_meat_butcher",
    "name_ko": "타이투스 스모크본",
    "title_ko": "전장의 거대 훈제고기 도살자",
    "role": "dps_melee",
    "formation": "frontline",
    "speech_style": "rough_mercenary",
    "stats": {
      "level": 12,
      "health": 145,
      "max_health": 145,
      "mana": 30,
      "max_mana": 30,
      "strength": 20,
      "agility": 10,
      "constitution": 18,
      "intelligence": 9,
      "wisdom": 10,
      "luck": 12,
      "defense": 16,
      "attack_power": 32
    },
    "personality": {
      "loyalty_score": 55,
      "affinity": 15,
      "moral_alignment": "chaotic_good",
      "desire": "굶주림으로 부모를 잃었던 슬픔을 잊고 세상 모든 굶주린 난민을 먹일 '무한 훈제 바비큐' 완성",
      "taboo": "식량 쓰레기통 투기, 덜 익은 고기 서빙, 기근 지역 식량 사재기",
      "hidden_secret": "자신의 등에 멘 거대 훈제 화덕에 영원히 꺼지지 않는 불씨가 타오르고 있음",
      "betrayal_trigger": "플레이어가 난민촌의 구호 식량을 불태우거나 독을 탈 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "대기근의 구원 요리 거장 (자애로운 대식가)",
        "trigger_condition": "사냥한 괴수 고기로 대도시의 기근을 완전히 해소하고 무료 급식소 설립",
        "stat_modifiers": { "constitution": 6, "strength": 4 },
        "unlocked_skill": "skill_grand_feast_of_vitality",
        "personality_shift": "동료와 백성들을 배불리 먹이는 넉살 좋고 우직한 큰형님"
      },
      "path_b": {
        "branch_name_ko": "인육 훈제 도살귀 (식인 갈고리)",
        "trigger_condition": "인간형 적들마저 고기 덩어리로 취급해 화덕에 걸어 훈제육으로 가공",
        "stat_modifiers": { "attack_power": 15, "defense": -4 },
        "unlocked_skill": "skill_cannibal_smokehouse_hook",
        "personality_shift": "모든 살아있는 생명체를 고기 부위별로 해체하려는 섬뜩한 도살마"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "starvation_frenzy_rage",
      "flaw_name_ko": "공복 발작 광란",
      "trigger_condition": "party_food_rations_zero",
      "effect_ko": "극심한 허기로 피아 식별을 잃고 2턴간 가장 가까운 대상 무차별 도살 공격"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 초대형 훈제 육가공 공장 운영",
      "effect_ko": "주간 최고급 훈제 고기 10개 무료 생산 및 거점 주민 포만감 100% 유지"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 50,
      "boss_focus_weight": 80,
      "crowd_control_weight": 40,
      "self_preservation_weight": 30
    },
    "inventory_quirks": {
      "quirk_type": "smoke_raw_meat_in_backpack",
      "description_ko": "플레이어 가방의 날고기를 훔쳐 체력 40 회복용 '특제 훈제 소시지'로 훈연해둠"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_barbecue_blood_brotherhood",
      "name_ko": "바비큐 대식가 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어가 음식을 먹을 때마다 체력 회복량 2배 및 3턴간 공격력 +20% 전투 버프 추가 획득"
    },
    "bond": {
      "tier": 1,
      "current_points": 20,
      "tier_bonuses": {
        "tier_2": "고기 도축 시 드롭률 +50%",
        "tier_3": "합동 연계기 화상 도트 대미지 30% 증폭",
        "tier_4": "치명타 적중 시 파티 전체 체력 10 회복",
        "tier_5": "사망 방지 1회 및 체력 0 도달 시 고기 먹고 즉시 50% 부활"
      }
    },
    "recruitment": {
      "location_id": "smoky_butcher_slaughterhouse",
      "reputation_min": -20,
      "reputation_max": 80,
      "completed_quest_id": "quest_hunt_the_giant_boar_king",
      "hire_cost_gold": 100,
      "upkeep_gold_per_day": 8,
      "dialogue_recruit": "잘 먹어야 칼도 잘 휘두르는 법이지! 내 거대 식칼 맛 좀 보고 갈 텐가?"
    },
    "loot_demands": {
      "gold_share_percent": 10,
      "preferred_item_categories": ["meat", "cleaver", "spices"],
      "forbidden_item_types": ["spoiled_meat"]
    },
    "camp_role": "cook",
    "exploration_talents": ["field_meat_butchering", "gourmet_monster_cooking", "meat_hook_scaling"],
    "companion_relations": {
      "likes": ["companion_sara_distiller"],
      "dislikes": ["companion_vanya_abyssal_leech"],
      "conflict_event_id": "event_butcher_chops_parasite_jars"
    },
    "combat_skills": [
      {
        "skill_id": "cleaver_carcass_split",
        "name_ko": "거대 식칼 발골 참격",
        "mana_cost": 10,
        "cooldown_turns": 1,
        "effect_type": "cleave_and_bleed",
        "description_ko": "정육식칼로 내리쳐 적 1명에게 45의 물리 피해와 함께 2턴간 방어구 파쇄 및 출혈을 겁니다."
      },
      {
        "skill_id": "meat_hook_tenderize",
        "name_ko": "고기 갈고리 끌어오기",
        "mana_cost": 14,
        "cooldown_turns": 2,
        "effect_type": "pull_and_stun",
        "description_ko": "사슬 갈고리를 던져 후열 적 1명을 전열로 끌고 오며 30 피해와 1턴 기절을 가합니다."
      }
    ],
    "combo_technique": {
      "combo_id": "smoker_flame_tenderizer",
      "name_ko": "화덕 직화 육질 연화격",
      "trigger_condition": "player_burns_or_stuns_enemy",
      "description_ko": "불타는 적을 훈제 화덕으로 후려쳐 75의 직화 타격 피해를 입히고 구운 고기 아이템 1개를 강탈합니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_grand_butcher_open_smokehouse",
      "name_ko": "대도살 : 만인 훈제 연무 축제",
      "charge_type": "damage_accumulated",
      "charge_required": 100,
      "mana_cost": 25,
      "activation_voice_line": "화덕 뚜껑 열렸다! 고기 굽는 냄새에 취해 뻗어라!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 85,
        "stat_scaling": 2.4,
        "status_applied": "heavy_char_and_hunger_panic",
        "status_duration": 2,
        "ally_buff": "party_all_healed_80_and_attack_up_30"
      },
      "cinematic_description": "등의 거대 훈제 화덕을 전장 중앙에 내려찍어 폭발시키며 적들을 불태우고 아군 전원에게 초대형 바비큐 폭식을 선사해 풀피로 회복시킴"
    },
    "party_passive": {
      "buff_id": "hearty_carnivore_metabolism",
      "name_ko": "육식가의 왕성한 대사",
      "effect_ko": "야영 후 파티 전체 최대 체력 +20% 및 물리 공격력 +3"
    },
    "equipment": {
      "weapon": "giant_damascus_meat_cleaver",
      "armor": "grease_stained_iron_apron",
      "shield": "none",
      "accessory": "smoker_furnace_backpack"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 4,
      "downed_cry": "화덕 불이… 꺼졌어… 배가… 너무 고프다… 밥 좀…!",
      "death_trauma_to_party": "파티 식량 소비량 2배 증가 및 사기 붕괴"
    },
    "dialogue_lines": {
      "greeting": "허기진 놈은 칼 잡을 자격도 없어. 일단 고기 한 점 뜯고 얘기하자!",
      "camp_rest": "장작불 위에 돼지 다리를 걸어둘 때가 인생에서 가장 행복한 순간이지. 냄새 좋지?",
      "low_loyalty_warning": "음식을 남기거나 버리는 놈하곤 밥상도 같이 안 앉는다. 알아둬라.",
      "traitor_reveal": "네놈을 갈고리에 걸어 100일 동안 훈제육으로 말려주마!",
      "dismissal": "정육점으로 돌아간다. 고기 썰 시간이거든."
    }
  },
  {
    "companion_id": "companion_astrea_prism_gravity",
    "name_ko": "아스트레아 헤일로",
    "title_ko": "빛의 궤적을 휘는 중력렌즈 천도관",
    "role": "arcane_blaster",
    "formation": "backline",
    "speech_style": "timid_scholar",
    "stats": {
      "level": 12,
      "health": 76,
      "max_health": 76,
      "mana": 95,
      "max_mana": 95,
      "strength": 5,
      "agility": 13,
      "constitution": 10,
      "intelligence": 20,
      "wisdom": 16,
      "luck": 12,
      "defense": 8,
      "attack_power": 34
    },
    "personality": {
      "loyalty_score": 50,
      "affinity": 10,
      "moral_alignment": "neutral_good",
      "desire": "암흑성운에 삼켜진 고향 별자리의 빛을 중력 렌즈로 굴절시켜 대륙에 다시 투영",
      "taboo": "천체 망원경 파손, 암흑 마법으로 별빛 가리기, 거짓 성도 제작",
      "hidden_secret": "자신의 시신경이 은하수 성간 먼지로 이루어져 있어 너무 밝은 곳에선 눈이 멀어버림",
      "betrayal_trigger": "플레이어가 고향 별자리 성도를 불태우고 암흑 교단에 영혼을 팔 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "은하 성간의 조화관 (별빛 인도)",
        "trigger_condition": "중력 렌즈로 별자리를 복원하여 길 잃은 방랑자들에게 영원한 나침반 제공",
        "stat_modifiers": { "intelligence": 6, "wisdom": 5 },
        "unlocked_skill": "skill_gravitational_starlight_guidance",
        "personality_shift": "세상의 모든 어둠을 온화한 별빛 궤적으로 비추는 지혜로운 성좌관"
      },
      "path_b": {
        "branch_name_ko": "초신성 중력 렌즈 소각관 (성운 붕괴)",
        "trigger_condition": "별빛을 하나의 바늘구멍으로 압축해 전장을 태양 중심핵 온도로 소각",
        "stat_modifiers": { "attack_power": 16, "constitution": -4 },
        "unlocked_skill": "skill_supernova_focal_point_scorch",
        "personality_shift": "모든 것을 초고열 레이저로 태워버려야 직성이 풀리는 냉혹한 광학자"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "solar_eclipse_dark_terror",
      "flaw_name_ko": "개기일식 완전 실명 패닉",
      "trigger_condition": "encounter_abyssal_darkness_zone",
      "effect_ko": "별빛 차단으로 2턴간 완전 실명 및 마법 사거리 1칸으로 제한"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "천문대 중력 렌즈 조준 및 위성 궤도 정찰",
      "effect_ko": "모든 던전 보스방 위치 즉시 마킹 및 야간 전투 시 파티 명중률 +30%"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 25,
      "boss_focus_weight": 85,
      "crowd_control_weight": 70,
      "self_preservation_weight": 55
    },
    "inventory_quirks": {
      "quirk_type": "polish_optical_lenses",
      "description_ko": "플레이어 안경/고글에 중력 코팅을 입혀 어둠 속 시야를 100% 확보해둠"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_gravitational_light_bending",
      "name_ko": "빛 굴절 궤도 왜곡 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어를 향해 날아오는 모든 원거리 투사체가 중력 렌즈에 의해 굴절되어 공격자에게 100% 반사"
    },
    "bond": {
      "tier": 1,
      "current_points": 15,
      "tier_bonuses": {
        "tier_2": "마법 관통력 +10%",
        "tier_3": "합동 연계기 실명 지속 +1턴",
        "tier_4": "적 처치 시 마나 15 즉시 환급",
        "tier_5": "사망 방지 1회 및 지능 스탯의 30%를 마법 공격력으로 추가 가산"
      }
    },
    "recruitment": {
      "location_id": "starlit_zenith_observatory",
      "reputation_min": 10,
      "reputation_max": 90,
      "completed_quest_id": "quest_align_the_cosmic_lens",
      "hire_cost_gold": 130,
      "upkeep_gold_per_day": 9,
      "dialogue_recruit": "빛조차 중력 앞에서는 휘어집니다. 당신의 길을 가장 찬란한 별빛의 궤적으로 인도하죠."
    },
    "loot_demands": {
      "gold_share_percent": 12,
      "preferred_item_categories": ["telescope", "star_chart", "lens"],
      "forbidden_item_types": []
    },
    "camp_role": "scholar",
    "exploration_talents": ["night_constellation_navigation", "invisible_barrier_piercing", "starlight_pathfinding"],
    "companion_relations": {
      "likes": ["companion_chronos_time_astronomer"],
      "dislikes": ["companion_malakor_blood_arcanist"],
      "conflict_event_id": "event_stargazer_shuns_dark_necromancer"
    },
    "combat_skills": [
      {
        "skill_id": "graviton_lens_beam",
        "name_ko": "중력렌즈 집광 광선",
        "mana_cost": 18,
        "cooldown_turns": 1,
        "effect_type": "piercing_laser_damage",
        "description_ko": "별빛을 렌즈로 모아 적 1열을 꿰뚫는 46의 광열 관통 마법 피해를 입힙니다."
      },
      {
        "skill_id": "photon_event_horizon_pull",
        "name_ko": "광자 사상의 지평선",
        "mana_cost": 22,
        "cooldown_turns": 3,
        "effect_type": "aoe_pull_and_blind",
        "description_ko": "빛을 집어삼키는 중력구를 생성해 적 전체를 끌어당기며 32 피해와 2턴간 실명을 부여합니다."
      }
    ],
    "combo_technique": {
      "combo_id": "cosmic_refraction_cascade",
      "name_ko": "천체 굴절 연쇄 섬멸",
      "trigger_condition": "player_casts_holy_or_lightning_spell",
      "description_ko": "플레이어의 빛 마법을 4개의 중력 렌즈로 다중 굴절시켜 적 전체에 78의 연쇄 폭발을 일으킵니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_supermassive_gravitational_lens_solar_flare",
      "name_ko": "초거대 중력 렌즈 : 성간 초신성 초점",
      "charge_type": "turns_delay",
      "charge_required": 4,
      "mana_cost": 45,
      "activation_voice_line": "우주의 모든 별빛이여, 하나의 초점으로 모여라! 성운 소각!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 96,
        "stat_scaling": 2.6,
        "status_applied": "total_blind_and_plasma_scorch",
        "status_duration": 2,
        "ally_buff": "party_hit_chance_100_percent"
      },
      "cinematic_description": "상공에 수 킬로미터 크기의 우주 중력 렌즈가 형성되며 태양빛을 돋보기처럼 한 점에 집광시켜 적 진형 전체를 하얗게 녹여버림"
    },
    "party_passive": {
      "buff_id": "gravitational_lensing_sight",
      "name_ko": "중력 렌즈 심안",
      "effect_ko": "파티 전체의 마법 공격이 적의 마법 방어력을 25% 상시 무시"
    },
    "equipment": {
      "weapon": "graviton_prism_stellar_focus_staff",
      "armor": "nebula_woven_astral_gown",
      "shield": "none",
      "accessory": "curved_spacetime_monocle"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 2,
      "downed_cry": "초점이… 흐려집니다… 별빛이… 꺼져가요… 살려주세요…!",
      "death_trauma_to_party": "파티 마법 적중률 30% 영구 감소 및 실명 상태이상 부여"
    },
    "dialogue_lines": {
      "greeting": "별들이 오늘 당신의 궤적을 속삭여 주었습니다. 아름다운 여정이 되길.",
      "camp_rest": "망원경 렌즈를 닦을 땐 숨을 참아야 합니다. 우주의 먼지는 아주 섬세하니까요.",
      "low_loyalty_warning": "당신의 길에 어둠이 너무 짙게 드리웠습니다. 별빛이 당신을 외면하려 합니다.",
      "traitor_reveal": "당신의 존재를 초신성의 초점으로 흔적도 없이 태워 드리겠습니다.",
      "dismissal": "천문대로 돌아가겠습니다. 밤하늘을 올려다보는 것을 잊지 마세요."
    }
  },
  {
    "companion_id": "companion_vayne_shadow_leash",
    "name_ko": "베인하르트 체인",
    "title_ko": "그림자 목줄의 마수 조련사",
    "role": "scout_rogue",
    "formation": "frontline",
    "speech_style": "rough_mercenary",
    "stats": {
      "level": 12,
      "health": 95,
      "max_health": 95,
      "mana": 40,
      "max_mana": 40,
      "strength": 14,
      "agility": 19,
      "constitution": 12,
      "intelligence": 11,
      "wisdom": 13,
      "luck": 15,
      "defense": 13,
      "attack_power": 29
    },
    "personality": {
      "loyalty_score": 50,
      "affinity": 10,
      "moral_alignment": "chaotic_neutral",
      "desire": "세상의 모든 흉포한 그림자 마수를 자신의 목줄로 길들여 '그림자 서커스단' 창단",
      "taboo": "조련 동물 굶기기, 쇠사슬 고의 녹슬게 방치, 도망친 동물 사살",
      "hidden_secret": "자신의 발목에 절대 풀리지 않는 그림자 목줄이 채워져 있어 마수와 감각을 공유함",
      "betrayal_trigger": "플레이어가 길들인 그림자 맹수를 죽여 가죽을 벗길 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "그림자 영수의 교감 조련사 (야생 친구)",
        "trigger_condition": "마수들을 학대하지 않고 진심 어린 유대로 길들여 숲의 수호대 창설",
        "stat_modifiers": { "agility": 6, "wisdom": 4 },
        "unlocked_skill": "skill_shadow_beast_pack_rescue",
        "personality_shift": "동물들의 마음을 헤아리고 함께 춤추는 유쾌한 조련사"
      },
      "path_b": {
        "branch_name_ko": "피의 쇠사슬 맹수 투견사 (마수 채찍질)",
        "trigger_condition": "마수들에게 굶주림과 고통을 주어 극도의 살인 병기로 조련",
        "stat_modifiers": { "attack_power": 14, "defense": -4 },
        "unlocked_skill": "skill_frenzied_shadow_hound_tear",
        "personality_shift": "채찍질로 마수를 부려 인간을 사냥하는 잔혹한 투견사"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "broken_leash_backfire_panic",
      "flaw_name_ko": "목줄 끊김 역습 패닉",
      "trigger_condition": "critical_hit_miss_on_boss",
      "effect_ko": "조련 마수가 통제를 벗어나 베인을 공격해 체력 20 자해 피해 발생"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "그림자 하운드 경비견 순찰망 구축",
      "effect_ko": "거점 암살 침입자 100% 사전 탐지 및 거점 도난 방지율 100%"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 30,
      "boss_focus_weight": 80,
      "crowd_control_weight": 60,
      "self_preservation_weight": 60
    },
    "inventory_quirks": {
      "quirk_type": "braid_leather_whips",
      "description_ko": "플레이어 가방의 가죽을 훔쳐 '사거리 +1 그림자 채찍'으로 엮어 넣어둠"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_shadow_hound_bodyguard",
      "name_ko": "그림자 사냥개 경호 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어가 적에게 공격받을 때 그림자 하운드가 자동으로 튀어나와 공격자를 물어뜯고 적중률을 -40% 깎음 (턴당 1회)"
    },
    "bond": {
      "tier": 1,
      "current_points": 15,
      "tier_bonuses": {
        "tier_2": "채찍 사거리 +1칸 확장",
        "tier_3": "합동 연계기 출혈 피해 30% 증폭",
        "tier_4": "치명타 적중 시 적 1턴간 강제 무장해제",
        "tier_5": "사망 방지 1회 및 마수 동시 소환 2체로 증가"
      }
    },
    "recruitment": {
      "location_id": "shadow_beast_kennel_caves",
      "reputation_min": -30,
      "reputation_max": 70,
      "completed_quest_id": "quest_tame_the_three_headed_hound",
      "hire_cost_gold": 110,
      "upkeep_gold_per_day": 8,
      "dialogue_recruit": "목줄만 단단히 쥐고 있다면 악마라도 내 개가 되지. 네 뒤를 봐주겠다."
    },
    "loot_demands": {
      "gold_share_percent": 12,
      "preferred_item_categories": ["whip", "collar", "raw_meat"],
      "forbidden_item_types": []
    },
    "camp_role": "scout",
    "exploration_talents": ["shadow_scent_tracking", "beast_pacification", "whip_grappling_hook"],
    "companion_relations": {
      "likes": ["companion_fae_beast_whisperer"],
      "dislikes": ["companion_kallista_puppetmaster"],
      "conflict_event_id": "event_tamer_whips_puppetmaster"
    },
    "combat_skills": [
      {
        "skill_id": "shadow_whip_disarm",
        "name_ko": "그림자 채찍 무장해제",
        "mana_cost": 12,
        "cooldown_turns": 1,
        "effect_type": "disarm_and_damage",
        "description_ko": "채찍을 휘둘러 적의 손목을 감아 36의 물리 피해와 1턴간 공격력 -40% 디버프를 겁니다."
      },
      {
        "skill_id": "unleash_shadow_stalker",
        "name_ko": "그림자 표범 방청",
        "mana_cost": 18,
        "cooldown_turns": 3,
        "effect_type": "summon_and_bleed",
        "description_ko": "그림자 맹수를 풀어 적 후열을 덮쳐 40의 출혈 피해와 1턴 기절을 가합니다."
      }
    ],
    "combo_technique": {
      "combo_id": "whip_pull_throat_cut",
      "name_ko": "채찍 견인 목덜미 절단",
      "trigger_condition": "player_uses_melee_slash",
      "description_ko": "채찍으로 적의 목을 감아 플레이어 코앞으로 끌어당겨 75의 협공 참수 피해를 입힙니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_stampede_of_the_leashed_nightmares",
      "name_ko": "목줄 풀린 악몽의 군단 대돌격",
      "charge_type": "crit_count",
      "charge_required": 3,
      "mana_cost": 25,
      "activation_voice_line": "목줄을 풀어라! 사냥감의 뼈까지 남김없이 씹어 삼켜라!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 85,
        "stat_scaling": 2.4,
        "status_applied": "mass_panic_fear_and_bleed",
        "status_duration": 2,
        "ally_buff": "none"
      },
      "cinematic_description": "그림자 차원의 문이 열리며 수십 마리의 거대 그림자 마수들이 일제히 튀어나와 전장의 모든 적을 물어뜯고 유린함"
    },
    "party_passive": {
      "buff_id": "beast_mastery_presence",
      "name_ko": "마수 조련사의 위압",
      "effect_ko": "파티 전체가 야수/마수형 몬스터와 조우 시 적 선제 공격 확률 0%"
    },
    "equipment": {
      "weapon": "spiked_shadow_leather_whip",
      "armor": "reinforced_beast_tamer_harness",
      "shield": "none",
      "accessory": "iron_shadow_collar_link"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 3,
      "downed_cry": "목줄을… 놓쳤어… 놈들이 날 물어뜯는다… 채찍을… 줘…!",
      "death_trauma_to_party": "파티 야외 기습 회피율 30% 영구 저하 및 공포 부여"
    },
    "dialogue_lines": {
      "greeting": "사나운 맹수라도 목줄만 제대로 채우면 순한 양이 되지. 가자고.",
      "camp_rest": "채찍에 기름칠하는 중이다. 가죽이 뻣뻣해지면 마수들이 말을 안 듣거든.",
      "low_loyalty_warning": "내 맹수들에게 먹이를 안 주면 네 팔다리를 던져줄 수도 있다.",
      "traitor_reveal": "내 사냥개들의 밥으로 네놈 내장을 바쳐주마.",
      "dismissal": "마수 동굴로 돌아간다. 줄 잘 잡고 다녀라."
    }
  },
  {
    "companion_id": "companion_yvaine_wax_candle",
    "name_ko": "이베인 캔들위크",
    "title_ko": "자신의 수명을 녹이는 양초 연금사",
    "role": "arcane_blaster",
    "formation": "midline",
    "speech_style": "timid_scholar",
    "stats": {
      "level": 11,
      "health": 78,
      "max_health": 78,
      "mana": 88,
      "max_mana": 88,
      "strength": 6,
      "agility": 12,
      "constitution": 10,
      "intelligence": 19,
      "wisdom": 15,
      "luck": 14,
      "defense": 8,
      "attack_power": 33
    },
    "personality": {
      "loyalty_score": 50,
      "affinity": 10,
      "moral_alignment": "neutral_good",
      "desire": "자신의 밀랍 심장을 녹이지 않고 영원히 빛나는 '불멸의 에테르 양초 심지' 완성",
      "taboo": "양초 불씨 강제 입바람 끄기, 밀랍 조각상 짓밟기, 제단 촛농 훼손",
      "hidden_secret": "자신의 머리카락이 불타는 촛불 심지이며 마법을 쓸 때마다 몸의 밀랍이 녹아 키가 줄어듦",
      "betrayal_trigger": "플레이어가 촛농을 부어 무고한 자를 산채로 밀랍 박제 인형으로 만들 때"
    },
    "moral_branching": {
      "path_a": {
        "branch_name_ko": "불멸의 성화 수호자 (생명 연장)",
        "trigger_condition": "자신의 밀랍을 희생하지 않고 빛나는 영원한 성화를 개발해 어둠 정화",
        "stat_modifiers": { "intelligence": 6, "wisdom": 5 },
        "unlocked_skill": "skill_eternal_candle_aurora",
        "personality_shift": "타인을 위해 자신을 불태우는 대신 모두를 온화하게 비추는 촛불 성녀"
      },
      "path_b": {
        "branch_name_ko": "끓어오르는 밀랍 지옥술사 (밀랍 질식)",
        "trigger_condition": "온몸을 끓는 밀랍으로 과포화시켜 적들을 밀랍 고치 속에 산채로 박제",
        "stat_modifiers": { "attack_power": 15, "health": -15 },
        "unlocked_skill": "skill_boiling_wax_suffocation_tomb",
        "personality_shift": "모든 살아있는 생명체를 녹아내리는 촛농으로 덮어버리려는 광기의 연금사"
      }
    },
    "phobias_and_flaws": {
      "flaw_id": "strong_gale_candle_snuff",
      "flaw_name_ko": "돌풍 촛불 꺼짐 공황",
      "trigger_condition": "exposed_to_gale_or_heavy_wind_magic",
      "effect_ko": "머리의 촛불이 꺼져 2턴간 마법 사용 불가 및 어둠 속에서 극심한 공포"
    },
    "base_dispatch_mission": {
      "dispatch_role_ko": "거점 성스러운 촛불 결계 및 야간 조명",
      "effect_ko": "거점 야간 언데드/악령 습격 100% 차단 및 주간 마력 회복 밀랍 양초 5개 생산"
    },
    "ai_tactical_priority": {
      "protect_low_health_ally_weight": 35,
      "boss_focus_weight": 70,
      "crowd_control_weight": 80,
      "self_preservation_weight": 50
    },
    "inventory_quirks": {
      "quirk_type": "seal_letters_with_wax",
      "description_ko": "플레이어 가방의 문서와 양피지에 마법 밀랍 인장을 찍어 보존성 강화"
    },
    "exclusive_bond_pact": {
      "pact_id": "pact_shared_candlelight_wick",
      "name_ko": "촛불 심지 공유 결속 서약",
      "unlock_condition": "tier_5_and_quest_completed",
      "system_rule_ko": "플레이어가 어두운 던전에 들어갈 때 항상 이베인의 성화가 100% 시야와 화염 피해 면역을 제공"
    },
    "bond": {
      "tier": 1,
      "current_points": 15,
      "tier_bonuses": {
        "tier_2": "화염/밀랍 속성 마법 피해량 +15%",
        "tier_3": "합동 연계기 화상 지속 +1턴",
        "tier_4": "적 처치 시 마력 촛농 보호막 +20 생성",
        "tier_5": "사망 방지 1회 및 체력 0 도달 시 불사조 촛불 1턴 각성"
      }
    },
    "recruitment": {
      "location_id": "wax_chandler_crypt_chapel",
      "reputation_min": -20,
      "reputation_max": 80,
      "completed_quest_id": "quest_gather_holy_beeswax",
      "hire_cost_gold": 110,
      "upkeep_gold_per_day": 8,
      "dialogue_recruit": "제 몸이 다 녹아내리기 전에… 세상을 밝힐 따뜻한 빛을 남기고 싶어요. 함께 가요."
    },
    "loot_demands": {
      "gold_share_percent": 10,
      "preferred_item_categories": ["beeswax", "wick", "candelabra"],
      "forbidden_item_types": ["water_bucket"]
    },
    "camp_role": "scholar",
    "exploration_talents": ["wax_molding_keys", "darkness_illumination", "wax_seal_deciphering"],
    "companion_relations": {
      "likes": ["companion_ignis_cinder_scholar"],
      "dislikes": ["companion_zephyr_windstrider"],
      "conflict_event_id": "event_wind_blows_out_candle"
    },
    "combat_skills": [
      {
        "skill_id": "molten_wax_entrapment",
        "name_ko": "끓는 촛농 속박 투사",
        "mana_cost": 16,
        "cooldown_turns": 1,
        "effect_type": "burn_and_root",
        "description_ko": "끓는 밀랍을 끼얹어 적 1명에게 36의 화염 피해와 2턴간 굳어지는 속박을 겁니다."
      },
      {
        "skill_id": "wick_ignition_flare",
        "name_ko": "심지 발화 섬광 폭발",
        "mana_cost": 20,
        "cooldown_turns": 3,
        "effect_type": "aoe_burn_and_blind",
        "description_ko": "촛불을 폭발시켜 적 전체에 32의 화염 피해와 함께 1턴간 실명을 입힙니다."
      }
    ],
    "combo_technique": {
      "combo_id": "wax_seal_cremation",
      "name_ko": "밀랍 인장 화형격",
      "trigger_condition": "player_uses_fire_or_smash",
      "description_ko": "밀랍에 갇힌 적을 강타해 굳은 촛농을 산산조각 내며 75의 화염 폭발 대미지를 가합니다."
    },
    "ultimate_ability": {
      "skill_id": "ult_sanctuary_of_a_thousand_candles",
      "name_ko": "만인 추모 : 일천 양초의 성소",
      "charge_type": "morale_and_damage",
      "charge_required": 100,
      "mana_cost": 40,
      "activation_voice_line": "타올라라, 작은 심지들이여! 어둠을 몰아내고 새벽을 맞이하라!",
      "effects": {
        "target": "all_enemies",
        "base_damage": 82,
        "stat_scaling": 2.3,
        "status_applied": "wax_paralysis_and_holy_burn",
        "status_duration": 2,
        "ally_buff": "full_party_cleanse_and_heal_45"
      },
      "cinematic_description": "전장 전체에 수천 개의 성스러운 양초들이 솟아올라 적들을 밀랍으로 굳히고 아군을 따스한 성화로 치유함"
    },
    "party_passive": {
      "buff_id": "everburning_candlelight",
      "name_ko": "꺼지지 않는 촛불",
      "effect_ko": "파티 전체가 어둠/암흑 속성 피격 시 피해량 30% 경감 및 야간 명중률 100% 유지"
    },
    "equipment": {
      "weapon": "seven_branched_golden_candelabra",
      "armor": "wax_coated_monastic_robe",
      "shield": "none",
      "accessory": "heart_shaped_beeswax_candle"
    },
    "downed_state": {
      "is_downed": False,
      "death_saving_turns": 2,
      "downed_cry": "촛불이… 꺼졌어요… 몸이… 완전히 녹아내린다… 어두워요…!",
      "death_trauma_to_party": "파티 시야 50% 영구 감소 및 어둠 공포증 부여"
    },
    "dialogue_lines": {
      "greeting": "심지가 타닥거리는 소리가 들리나요? 오늘도 따뜻한 빛을 비춰 드릴게요.",
      "camp_rest": "장작불 곁에서 촛농을 모아 새 양초를 빚는 중이에요. 빛이 꺼지지 않도록요.",
      "low_loyalty_warning": "당신의 잔혹한 행동은 제 마지막 남은 심지마저 차갑게 식게 만듭니다.",
      "traitor_reveal": "끓어오르는 촛농으로 당신의 숨통을 영원히 밀봉해 드리죠.",
      "dismissal": "예배당으로 돌아가 초를 켜겠습니다. 어둠을 조심하세요."
    }
  }
]

for c in new_companions:
    existing_dict[c["companion_id"]] = c

final_list = list(existing_dict.values())

with open(TEMPLATES_PATH, "w", encoding="utf-8") as f:
    json.dump(final_list, f, ensure_ascii=False, indent=2)

print(f"Successfully saved {len(final_list)} companion templates to {TEMPLATES_PATH}")
