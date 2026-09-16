# CHANGES_AUDIT: Static Reachability and Call Analysis

**Entrypoints**: `app.py`, `src/agents/game_master.py`  
**Total `src/world/` modules analyzed**: 65  

## Summary Table

| Module | File Reachable? | Total Public Methods | Called-in-Live-Path | Tests-Only | Never-Called |
|---|:---:|:---:|:---:|:---:|:---:|
| `alcohol_engine.py` | ✅ Yes | 8 | 8 | 0 | 0 |
| `attack_physics_engine.py` | ✅ Yes | 3 | 3 | 0 | 0 |
| `audio_engine.py` | ✅ Yes | 3 | 3 | 0 | 0 |
| `botany_engine.py` | ✅ Yes | 4 | 4 | 0 | 0 |
| `bounty_engine.py` | ✅ Yes | 4 | 3 | 0 | 1 |
| `campsite_engine.py` | ✅ Yes | 7 | 7 | 0 | 0 |
| `cave_in_engine.py` | ✅ Yes | 8 | 7 | 0 | 1 |
| `celestial_engine.py` | ✅ Yes | 4 | 2 | 1 | 1 |
| `chronicle.py` | ✅ Yes | 4 | 4 | 0 | 0 |
| `cognitive_engine.py` | ✅ Yes | 8 | 7 | 1 | 0 |
| `combat_time_track_engine.py` | ✅ Yes | 8 | 8 | 0 | 0 |
| `corpse_ecology_engine.py` | ✅ Yes | 6 | 4 | 2 | 0 |
| `crafting_engine.py` | ✅ Yes | 11 | 10 | 1 | 0 |
| `dice.py` | ✅ Yes | 7 | 5 | 1 | 1 |
| `disease_engine.py` | ✅ Yes | 5 | 3 | 2 | 0 |
| `dungeon_engine.py` | ✅ Yes | 4 | 2 | 1 | 1 |
| `economy_engine.py` | ✅ Yes | 15 | 14 | 1 | 0 |
| `enchant_engine.py` | ✅ Yes | 5 | 3 | 2 | 0 |
| `entities.py` | ✅ Yes | 54 | 44 | 4 | 6 |
| `equipment.py` | ✅ Yes | 5 | 4 | 0 | 1 |
| `event_perspective.py` | ✅ Yes | 2 | 2 | 0 | 0 |
| `generator.py` | ✅ Yes | 2 | 2 | 0 | 0 |
| `geography.py` | ✅ Yes | 5 | 5 | 0 | 0 |
| `graph_engine.py` | ✅ Yes | 5 | 4 | 1 | 0 |
| `harvest_engine.py` | ✅ Yes | 8 | 7 | 1 | 0 |
| `hidden_encounter_engine.py` | ✅ Yes | 3 | 3 | 0 | 0 |
| `incantation.py` | ✅ Yes | 6 | 3 | 2 | 1 |
| `infrastructure.py` | ✅ Yes | 39 | 31 | 8 | 0 |
| `injury_engine.py` | ✅ Yes | 5 | 5 | 0 | 0 |
| `legacy.py` | ✅ Yes | 4 | 4 | 0 | 0 |
| `mana_burn_engine.py` | ✅ Yes | 9 | 9 | 0 | 0 |
| `merchant_barter_engine.py` | ✅ Yes | 8 | 8 | 0 | 0 |
| `npc_skill_engine.py` | ✅ Yes | 4 | 3 | 1 | 0 |
| `object_physics_engine.py` | ✅ Yes | 7 | 5 | 2 | 0 |
| `outfit_engine.py` | ✅ Yes | 15 | 6 | 9 | 0 |
| `party_engine.py` | ✅ Yes | 11 | 10 | 1 | 0 |
| `party_sanity_engine.py` | ✅ Yes | 5 | 4 | 1 | 0 |
| `perception_engine.py` | ✅ Yes | 6 | 4 | 1 | 1 |
| `persistence.py` | ✅ Yes | 9 | 8 | 1 | 0 |
| `physics_matrix.py` | ✅ Yes | 3 | 2 | 1 | 0 |
| `poise_engine.py` | ✅ Yes | 12 | 6 | 5 | 1 |
| `psychology_engine.py` | ✅ Yes | 21 | 17 | 4 | 0 |
| `pupil_adaptation_engine.py` | ✅ Yes | 10 | 5 | 5 | 0 |
| `puzzle_engine.py` | ✅ Yes | 4 | 3 | 0 | 1 |
| `quest_engine.py` | ✅ Yes | 17 | 16 | 1 | 0 |
| `ration_engine.py` | ✅ Yes | 8 | 6 | 2 | 0 |
| `rumor_diffusion_engine.py` | ✅ Yes | 4 | 4 | 0 | 0 |
| `scenario_manager.py` | ✅ Yes | 3 | 3 | 0 | 0 |
| `siege_engine.py` | ✅ Yes | 23 | 20 | 0 | 3 |
| `skills.py` | ✅ Yes | 10 | 8 | 1 | 1 |
| `sleep_engine.py` | ✅ Yes | 7 | 5 | 1 | 1 |
| `stamina_engine.py` | ✅ Yes | 5 | 5 | 0 | 0 |
| `stat_engine.py` | ✅ Yes | 14 | 11 | 3 | 0 |
| `state.py` | ✅ Yes | 55 | 45 | 6 | 4 |
| `status_engine.py` | ✅ Yes | 11 | 11 | 0 | 0 |
| `stealth_engine.py` | ✅ Yes | 4 | 4 | 0 | 0 |
| `thermal_engine.py` | ✅ Yes | 5 | 5 | 0 | 0 |
| `time_calendar_engine.py` | ✅ Yes | 3 | 2 | 1 | 0 |
| `toxicology_engine.py` | ✅ Yes | 7 | 6 | 1 | 0 |
| `trap_engine.py` | ✅ Yes | 5 | 5 | 0 | 0 |
| `two_pass_engine.py` | ✅ Yes | 14 | 14 | 0 | 0 |
| `validator.py` | ✅ Yes | 4 | 4 | 0 | 0 |
| `vein_restoration_engine.py` | ✅ Yes | 5 | 4 | 1 | 0 |
| `weather_engine.py` | ✅ Yes | 3 | 1 | 1 | 1 |
| `weather_magic_engine.py` | ✅ Yes | 7 | 4 | 3 | 0 |
| **TOTAL** | - | **590** | **484** | **80** | **26** |

### Unreachable Modules (0/65)


## Detailed Method Breakdown

### `bounty_engine.py` (Reachable: True)
- `format_bounty_context_for_prompt`: **never-called**

### `cave_in_engine.py` (Reachable: True)
- `assess_stability`: **never-called**

### `celestial_engine.py` (Reachable: True)
- `get_active_modifiers`: **called-from-tests-only**
- `format_celestial_context_for_prompt`: **never-called**

### `cognitive_engine.py` (Reachable: True)
- `update_attitude`: **called-from-tests-only**

### `corpse_ecology_engine.py` (Reachable: True)
- `loot_corpse`: **called-from-tests-only**
- `dispose_corpse`: **called-from-tests-only**

### `crafting_engine.py` (Reachable: True)
- `experiment_blind_craft`: **called-from-tests-only**

### `dice.py` (Reachable: True)
- `calculate_skill_damage_with_crit`: **called-from-tests-only**
- `incantation_interrupted_check`: **never-called**

### `disease_engine.py` (Reachable: True)
- `apply_remedy`: **called-from-tests-only**
- `burn_corpses`: **called-from-tests-only**

### `dungeon_engine.py` (Reachable: True)
- `create_dungeon_instance`: **called-from-tests-only**
- `get_current_dungeon`: **never-called**

### `economy_engine.py` (Reachable: True)
- `perform_haggle`: **called-from-tests-only**

### `enchant_engine.py` (Reachable: True)
- `socket_rune`: **called-from-tests-only**
- `repair_item`: **called-from-tests-only**

### `entities.py` (Reachable: True)
- `display_weight`: **never-called**
- `appraisal_text`: **never-called**
- `to_korean_visual_summary`: **called-from-tests-only**
- `to_image_prompt_keywords`: **called-from-tests-only**
- `stamina_regen_effective`: **never-called**
- `get_recent_off_screen_logs`: **called-from-tests-only**
- `stamina_status_ko`: **never-called**
- `movement_speed_mps`: **called-from-tests-only**
- `max_draw_weight_lbs`: **never-called**
- `incantation_speed_multiplier`: **never-called**

### `equipment.py` (Reachable: True)
- `get_active_set_bonuses`: **never-called**

### `graph_engine.py` (Reachable: True)
- `evaluate_vacuum_collapse`: **called-from-tests-only**

### `harvest_engine.py` (Reachable: True)
- `create_standard_monster_anatomy`: **called-from-tests-only**

### `incantation.py` (Reachable: True)
- `parse_incantation`: **called-from-tests-only**
- `validate_incantation`: **called-from-tests-only**
- `can_be_cancelled_by_npc`: **never-called**

### `infrastructure.py` (Reachable: True)
- `calculate_total_military_power`: **called-from-tests-only**
- `check_border_entry`: **called-from-tests-only**
- `resolve_specialties`: **called-from-tests-only**
- `resolve_natural_resources`: **called-from-tests-only**
- `resolve_settlement_lifestyle`: **called-from-tests-only**
- `register_inter_tier_route`: **called-from-tests-only**
- `find_inter_tier_routes`: **called-from-tests-only**
- `audit_settlement_resilience`: **called-from-tests-only**

### `npc_skill_engine.py` (Reachable: True)
- `process_npc_opportunistic_turn`: **called-from-tests-only**

### `object_physics_engine.py` (Reachable: True)
- `improvise_weapon_stats`: **called-from-tests-only**
- `repair_object`: **called-from-tests-only**

### `outfit_engine.py` (Reachable: True)
- `evaluate_encumbrance`: **called-from-tests-only**
- `get_quick_slots`: **called-from-tests-only**
- `calculate_projectile_draw_delay`: **called-from-tests-only**
- `calculate_quick_draw_attack`: **called-from-tests-only**
- `check_armor_chafing`: **called-from-tests-only**
- `calculate_clothing_noise_reduction`: **called-from-tests-only**
- `calculate_eyewear_appraisal_bonus`: **called-from-tests-only**
- `evaluate_eyewear_damage`: **called-from-tests-only**
- `build_consistent_character_prompt`: **called-from-tests-only**

### `party_engine.py` (Reachable: True)
- `process_camp_rest_effects`: **called-from-tests-only**

### `party_sanity_engine.py` (Reachable: True)
- `trigger_event_stress`: **called-from-tests-only**

### `perception_engine.py` (Reachable: True)
- `evaluate_sensory_awareness`: **never-called**
- `evaluate_combat_threat_perception`: **called-from-tests-only**

### `persistence.py` (Reachable: True)
- `get_full_history`: **called-from-tests-only**

### `physics_matrix.py` (Reachable: True)
- `format_reactions_for_prompt`: **called-from-tests-only**

### `poise_engine.py` (Reachable: True)
- `set_blocking_stance`: **called-from-tests-only**
- `tick_combat_duration`: **never-called**
- `apply_physical_impact`: **called-from-tests-only**
- `apply_magic_impact`: **called-from-tests-only**
- `apply_mental_impact`: **called-from-tests-only**
- `consume_guard_break_crit`: **called-from-tests-only**

### `psychology_engine.py` (Reachable: True)
- `apply_personality_template`: **called-from-tests-only**
- `recover_trauma`: **called-from-tests-only**
- `apply_relationship_delta`: **called-from-tests-only**
- `record_memory_deduplicated`: **called-from-tests-only**

### `pupil_adaptation_engine.py` (Reachable: True)
- `equip_eye_patch`: **called-from-tests-only**
- `equip_shaded_goggles`: **called-from-tests-only**
- `swap_eye_patch_action`: **called-from-tests-only**
- `check_illumination_transition`: **called-from-tests-only**
- `adapt_eyes_action`: **called-from-tests-only**

### `puzzle_engine.py` (Reachable: True)
- `format_puzzle_context_for_prompt`: **never-called**

### `quest_engine.py` (Reachable: True)
- `is_time_limited`: **called-from-tests-only**

### `ration_engine.py` (Reachable: True)
- `preserve_food`: **called-from-tests-only**
- `consume_ration`: **called-from-tests-only**

### `siege_engine.py` (Reachable: True)
- `casualty_count`: **never-called**
- `casualty_rate`: **never-called**
- `morale_tier`: **never-called**

### `skills.py` (Reachable: True)
- `apply_passive_bonuses`: **called-from-tests-only**
- `diverge_skill_from_magic_word`: **never-called**

### `sleep_engine.py` (Reachable: True)
- `check_microsleep`: **never-called**
- `apply_stimulant`: **called-from-tests-only**

### `stat_engine.py` (Reachable: True)
- `calculate_scaled_damage`: **called-from-tests-only**
- `modify_sub_stat`: **called-from-tests-only**
- `format_stat_sheet_ko`: **called-from-tests-only**

### `state.py` (Reachable: True)
- `current_minute`: **called-from-tests-only**
- `current_week`: **never-called**
- `day_of_week_ko`: **called-from-tests-only**
- `effective_start_year`: **never-called**
- `current_year`: **called-from-tests-only**
- `current_month`: **called-from-tests-only**
- `current_day_of_month`: **never-called**
- `time_display_ko`: **called-from-tests-only**
- `generate_news_poster`: **called-from-tests-only**
- `to_audio_html`: **never-called**

### `time_calendar_engine.py` (Reachable: True)
- `resolve_world_start_year`: **called-from-tests-only**

### `toxicology_engine.py` (Reachable: True)
- `ingest_potion`: **called-from-tests-only**

### `vein_restoration_engine.py` (Reachable: True)
- `brew_vein_tonic`: **called-from-tests-only**

### `weather_engine.py` (Reachable: True)
- `get_elemental_multiplier`: **called-from-tests-only**
- `format_weather_context_for_prompt`: **never-called**

### `weather_magic_engine.py` (Reachable: True)
- `cast_weather_magic`: **called-from-tests-only**
- `resolve_combat_weather_tick`: **called-from-tests-only**
- `resolve_travel_weather_exposure`: **called-from-tests-only**
