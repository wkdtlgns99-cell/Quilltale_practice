# CHANGES_AUDIT: Static Reachability and Call Analysis

**Entrypoints**: `app.py`, `src/agents/game_master.py`  
**Total `src/world/` modules analyzed**: 64  

## Summary Table

| Module | File Reachable? | Total Public Methods | Called-in-Live-Path | Tests-Only | Never-Called |
|---|:---:|:---:|:---:|:---:|:---:|
| `alcohol_engine.py` | ❌ No | 7 | 4 | 2 | 1 |
| `attack_physics_engine.py` | ✅ Yes | 3 | 3 | 0 | 0 |
| `audio_engine.py` | ✅ Yes | 3 | 3 | 0 | 0 |
| `botany_engine.py` | ❌ No | 4 | 1 | 3 | 0 |
| `bounty_engine.py` | ✅ Yes | 4 | 2 | 1 | 1 |
| `campsite_engine.py` | ❌ No | 7 | 3 | 4 | 0 |
| `cave_in_engine.py` | ✅ Yes | 8 | 5 | 0 | 3 |
| `celestial_engine.py` | ✅ Yes | 4 | 2 | 1 | 1 |
| `chronicle.py` | ✅ Yes | 4 | 3 | 1 | 0 |
| `cognitive_engine.py` | ✅ Yes | 8 | 6 | 1 | 1 |
| `combat_time_track_engine.py` | ❌ No | 8 | 2 | 3 | 3 |
| `corpse_ecology_engine.py` | ✅ Yes | 6 | 4 | 2 | 0 |
| `crafting_engine.py` | ✅ Yes | 11 | 7 | 4 | 0 |
| `dice.py` | ✅ Yes | 7 | 4 | 1 | 2 |
| `disease_engine.py` | ✅ Yes | 5 | 2 | 2 | 1 |
| `dungeon_engine.py` | ✅ Yes | 4 | 2 | 1 | 1 |
| `economy_engine.py` | ✅ Yes | 15 | 9 | 3 | 3 |
| `enchant_engine.py` | ✅ Yes | 5 | 3 | 2 | 0 |
| `equipment.py` | ✅ Yes | 5 | 2 | 1 | 2 |
| `event_perspective.py` | ✅ Yes | 0 | 0 | 0 | 0 |
| `generator.py` | ✅ Yes | 2 | 2 | 0 | 0 |
| `geography.py` | ✅ Yes | 5 | 4 | 1 | 0 |
| `graph_engine.py` | ✅ Yes | 5 | 4 | 1 | 0 |
| `harvest_engine.py` | ❌ No | 8 | 2 | 5 | 1 |
| `hidden_encounter_engine.py` | ✅ Yes | 3 | 1 | 0 | 2 |
| `incantation.py` | ✅ Yes | 6 | 1 | 4 | 1 |
| `infrastructure.py` | ✅ Yes | 39 | 3 | 35 | 1 |
| `injury_engine.py` | ✅ Yes | 5 | 4 | 0 | 1 |
| `legacy.py` | ✅ Yes | 4 | 3 | 0 | 1 |
| `mana_burn_engine.py` | ❌ No | 9 | 2 | 6 | 1 |
| `merchant_barter_engine.py` | ❌ No | 8 | 0 | 8 | 0 |
| `npc_skill_engine.py` | ✅ Yes | 4 | 2 | 2 | 0 |
| `object_physics_engine.py` | ✅ Yes | 7 | 3 | 3 | 1 |
| `outfit_engine.py` | ❌ No | 15 | 0 | 12 | 3 |
| `party_engine.py` | ✅ Yes | 11 | 9 | 1 | 1 |
| `party_sanity_engine.py` | ✅ Yes | 5 | 2 | 3 | 0 |
| `perception_engine.py` | ✅ Yes | 6 | 4 | 1 | 1 |
| `persistence.py` | ✅ Yes | 6 | 6 | 0 | 0 |
| `physics_matrix.py` | ✅ Yes | 3 | 2 | 1 | 0 |
| `poise_engine.py` | ✅ Yes | 12 | 5 | 6 | 1 |
| `pupil_adaptation_engine.py` | ✅ Yes | 10 | 5 | 5 | 0 |
| `puzzle_engine.py` | ✅ Yes | 4 | 2 | 0 | 2 |
| `quest_engine.py` | ✅ Yes | 17 | 13 | 2 | 2 |
| `ration_engine.py` | ✅ Yes | 8 | 4 | 3 | 1 |
| `rumor_diffusion_engine.py` | ✅ Yes | 4 | 3 | 1 | 0 |
| `save_load_manager.py` | ❌ No | 11 | 4 | 6 | 1 |
| `scenario_manager.py` | ✅ Yes | 0 | 0 | 0 | 0 |
| `siege_engine.py` | ❌ No | 23 | 2 | 10 | 11 |
| `skills.py` | ✅ Yes | 10 | 4 | 3 | 3 |
| `sleep_engine.py` | ✅ Yes | 7 | 3 | 3 | 1 |
| `stamina_engine.py` | ✅ Yes | 5 | 5 | 0 | 0 |
| `stat_engine.py` | ✅ Yes | 11 | 2 | 8 | 1 |
| `state.py` | ✅ Yes | 107 | 59 | 29 | 19 |
| `status_engine.py` | ✅ Yes | 11 | 10 | 0 | 1 |
| `stealth_engine.py` | ❌ No | 4 | 0 | 3 | 1 |
| `thermal_engine.py` | ✅ Yes | 5 | 1 | 2 | 2 |
| `time_calendar_engine.py` | ❌ No | 3 | 1 | 2 | 0 |
| `toxicology_engine.py` | ✅ Yes | 7 | 5 | 2 | 0 |
| `trap_engine.py` | ✅ Yes | 5 | 3 | 2 | 0 |
| `two_pass_engine.py` | ✅ Yes | 3 | 3 | 0 | 0 |
| `validator.py` | ✅ Yes | 4 | 2 | 1 | 1 |
| `vein_restoration_engine.py` | ❌ No | 5 | 2 | 3 | 0 |
| `weather_engine.py` | ✅ Yes | 3 | 1 | 1 | 1 |
| `weather_magic_engine.py` | ✅ Yes | 7 | 3 | 4 | 0 |
| **TOTAL** | - | **555** | **263** | **211** | **81** |

### Unreachable Modules (13/64)

- ❌ `alcohol_engine.py`
- ❌ `botany_engine.py`
- ❌ `campsite_engine.py`
- ❌ `combat_time_track_engine.py`
- ❌ `harvest_engine.py`
- ❌ `mana_burn_engine.py`
- ❌ `merchant_barter_engine.py`
- ❌ `outfit_engine.py`
- ❌ `save_load_manager.py`
- ❌ `siege_engine.py`
- ❌ `stealth_engine.py`
- ❌ `time_calendar_engine.py`
- ❌ `vein_restoration_engine.py`

## Detailed Method Breakdown

### `alcohol_engine.py` (Reachable: False)
- `consume_drink`: **called-from-tests-only**
- `resolve_blackout`: **never-called**
- `process_morning_hangover`: **called-from-tests-only**

### `botany_engine.py` (Reachable: False)
- `forage`: **called-from-tests-only**
- `identify_plant`: **called-from-tests-only**
- `consume_plant`: **called-from-tests-only**

### `bounty_engine.py` (Reachable: True)
- `add_bounty`: **called-from-tests-only**
- `format_bounty_context_for_prompt`: **never-called**

### `campsite_engine.py` (Reachable: False)
- `get_campsite`: **called-from-tests-only**
- `setup_campsite`: **called-from-tests-only**
- `assign_sentry_shifts`: **called-from-tests-only**
- `resolve_campsite_night`: **called-from-tests-only**

### `cave_in_engine.py` (Reachable: True)
- `get_rock_strata`: **never-called**
- `get_collapse_stage_for_durability`: **never-called**
- `assess_stability`: **never-called**

### `celestial_engine.py` (Reachable: True)
- `get_active_modifiers`: **called-from-tests-only**
- `format_celestial_context_for_prompt`: **never-called**

### `chronicle.py` (Reachable: True)
- `load_chronicles_for_world`: **called-from-tests-only**

### `cognitive_engine.py` (Reachable: True)
- `classify_hypothesis`: **never-called**
- `update_attitude`: **called-from-tests-only**

### `combat_time_track_engine.py` (Reachable: False)
- `get_distance_zone`: **called-from-tests-only**
- `get_distance_zone_ko`: **called-from-tests-only**
- `move_towards`: **called-from-tests-only**
- `move_away`: **never-called**
- `end_second`: **never-called**
- `check_perception_interrupt`: **never-called**

### `corpse_ecology_engine.py` (Reachable: True)
- `loot_corpse`: **called-from-tests-only**
- `dispose_corpse`: **called-from-tests-only**

### `crafting_engine.py` (Reachable: True)
- `get_recipe_template`: **called-from-tests-only**
- `check_recipe_prerequisites`: **called-from-tests-only**
- `check_recipe_ingredients`: **called-from-tests-only**
- `experiment_blind_craft`: **called-from-tests-only**

### `dice.py` (Reachable: True)
- `roll_crit`: **never-called**
- `calculate_skill_damage_with_crit`: **called-from-tests-only**
- `incantation_interrupted_check`: **never-called**

### `disease_engine.py` (Reachable: True)
- `get_disease`: **never-called**
- `apply_remedy`: **called-from-tests-only**
- `burn_corpses`: **called-from-tests-only**

### `dungeon_engine.py` (Reachable: True)
- `create_dungeon_instance`: **called-from-tests-only**
- `get_current_dungeon`: **never-called**

### `economy_engine.py` (Reachable: True)
- `get_shop_template`: **called-from-tests-only**
- `get_active_shop`: **never-called**
- `check_item_unlock`: **called-from-tests-only**
- `calculate_buy_price`: **never-called**
- `calculate_sell_price`: **never-called**
- `perform_haggle`: **called-from-tests-only**

### `enchant_engine.py` (Reachable: True)
- `socket_rune`: **called-from-tests-only**
- `repair_item`: **called-from-tests-only**

### `equipment.py` (Reachable: True)
- `get_equipped_items`: **never-called**
- `get_active_set_bonuses`: **never-called**
- `get_slot_for_body_part`: **called-from-tests-only**

### `geography.py` (Reachable: True)
- `dijkstra_shortest_travel`: **called-from-tests-only**

### `graph_engine.py` (Reachable: True)
- `evaluate_vacuum_collapse`: **called-from-tests-only**

### `harvest_engine.py` (Reachable: False)
- `get_or_create_part`: **never-called**
- `attack_targeted_part`: **called-from-tests-only**
- `can_harvest`: **called-from-tests-only**
- `harvest_part`: **called-from-tests-only**
- `harvest_severed_object`: **called-from-tests-only**
- `create_standard_monster_anatomy`: **called-from-tests-only**

### `hidden_encounter_engine.py` (Reachable: True)
- `is_boss_defeated`: **never-called**
- `has_contraband`: **never-called**

### `incantation.py` (Reachable: True)
- `get_char_limit`: **called-from-tests-only**
- `parse_incantation`: **called-from-tests-only**
- `validate_incantation`: **called-from-tests-only**
- `detect_incantation_in_action`: **called-from-tests-only**
- `can_be_cancelled_by_npc`: **never-called**

### `infrastructure.py` (Reachable: True)
- `calculate_total_military_power`: **called-from-tests-only**
- `register_continent`: **called-from-tests-only**
- `register_region`: **called-from-tests-only**
- `register_nation`: **called-from-tests-only**
- `register_settlement`: **called-from-tests-only**
- `register_facility`: **called-from-tests-only**
- `resolve_hierarchy`: **called-from-tests-only**
- `calculate_effective_price`: **called-from-tests-only**
- `check_border_entry`: **called-from-tests-only**
- `resolve_specialties`: **called-from-tests-only**
- `resolve_natural_resources`: **called-from-tests-only**
- `recalculate_totals`: **called-from-tests-only**
- `resolve_settlement_lifestyle`: **called-from-tests-only**
- `register_inter_tier_route`: **called-from-tests-only**
- `find_inter_tier_routes`: **called-from-tests-only**
- `audit_settlement_resilience`: **called-from-tests-only**
- `load_continent_templates`: **called-from-tests-only**
- `adapt_region_template_to_region`: **called-from-tests-only**
- `load_region_templates`: **called-from-tests-only**
- `load_settlement_templates`: **called-from-tests-only**
- `load_nation_templates`: **called-from-tests-only**
- `load_facility_templates`: **called-from-tests-only**
- `inject_cosmology_to_world_state`: **called-from-tests-only**
- `assemble_world_upper_layers`: **called-from-tests-only**
- `assemble_settlement_roads`: **called-from-tests-only**
- `assemble_world_middle_layers`: **called-from-tests-only**
- `assemble_settlement_facilities`: **called-from-tests-only**
- `assemble_full_world`: **called-from-tests-only**
- `bind_settlement_npcs`: **called-from-tests-only**
- `bind_facility_inventories`: **called-from-tests-only**
- `bind_training_facilities`: **called-from-tests-only**
- `load_monster_templates`: **never-called**
- `spawn_monster_from_template`: **called-from-tests-only**
- `bind_region_monsters`: **called-from-tests-only**
- `bind_settlement_quests`: **called-from-tests-only**
- `bind_world_entities`: **called-from-tests-only**

### `injury_engine.py` (Reachable: True)
- `classify_injury`: **never-called**

### `legacy.py` (Reachable: True)
- `load_all_legacies`: **never-called**

### `mana_burn_engine.py` (Reachable: False)
- `get_circuit_state`: **called-from-tests-only**
- `can_use_life_as_mana`: **called-from-tests-only**
- `evaluate_overchannel`: **called-from-tests-only**
- `apply_overchannel_consequences`: **never-called**
- `trigger_mana_backlash`: **called-from-tests-only**
- `accumulate_contamination`: **called-from-tests-only**
- `repair_circuit`: **called-from-tests-only**

### `merchant_barter_engine.py` (Reachable: False)
- `get_regional_price`: **called-from-tests-only**
- `calculate_barter_exchange`: **called-from-tests-only**
- `check_smuggling_checkpoint`: **called-from-tests-only**
- `sell_to_black_market`: **called-from-tests-only**
- `record_merchant_debt`: **called-from-tests-only**
- `check_debt_default`: **called-from-tests-only**
- `appraise_unidentified_item`: **called-from-tests-only**
- `attempt_coin_clipping`: **called-from-tests-only**

### `npc_skill_engine.py` (Reachable: True)
- `get_available_npc_skills`: **called-from-tests-only**
- `process_npc_opportunistic_turn`: **called-from-tests-only**

### `object_physics_engine.py` (Reachable: True)
- `resolve_material`: **called-from-tests-only**
- `get_material_spec`: **never-called**
- `improvise_weapon_stats`: **called-from-tests-only**
- `repair_object`: **called-from-tests-only**

### `outfit_engine.py` (Reachable: False)
- `calculate_carry_capacity`: **called-from-tests-only**
- `calculate_inventory_weight`: **never-called**
- `evaluate_encumbrance`: **called-from-tests-only**
- `get_backpack_spec`: **never-called**
- `estimate_item_volume_liters`: **never-called**
- `evaluate_backpack_storage`: **called-from-tests-only**
- `get_quick_slots`: **called-from-tests-only**
- `calculate_projectile_draw_delay`: **called-from-tests-only**
- `calculate_quick_draw_attack`: **called-from-tests-only**
- `check_armor_chafing`: **called-from-tests-only**
- `calculate_clothing_noise_reduction`: **called-from-tests-only**
- `calculate_eyewear_appraisal_bonus`: **called-from-tests-only**
- `evaluate_eyewear_damage`: **called-from-tests-only**
- `sync_equipment_to_clothing_layer`: **called-from-tests-only**
- `build_consistent_character_prompt`: **called-from-tests-only**

### `party_engine.py` (Reachable: True)
- `get_companion_template`: **never-called**
- `process_camp_rest_effects`: **called-from-tests-only**

### `party_sanity_engine.py` (Reachable: True)
- `add_stress`: **called-from-tests-only**
- `trigger_breakdown`: **called-from-tests-only**
- `trigger_event_stress`: **called-from-tests-only**

### `perception_engine.py` (Reachable: True)
- `evaluate_sensory_awareness`: **never-called**
- `evaluate_combat_threat_perception`: **called-from-tests-only**

### `physics_matrix.py` (Reachable: True)
- `format_reactions_for_prompt`: **called-from-tests-only**

### `poise_engine.py` (Reachable: True)
- `set_blocking_stance`: **called-from-tests-only**
- `tick_combat_duration`: **never-called**
- `apply_physical_impact`: **called-from-tests-only**
- `apply_magic_impact`: **called-from-tests-only**
- `apply_mental_impact`: **called-from-tests-only**
- `recover_posture_time`: **called-from-tests-only**
- `consume_guard_break_crit`: **called-from-tests-only**

### `pupil_adaptation_engine.py` (Reachable: True)
- `equip_eye_patch`: **called-from-tests-only**
- `equip_shaded_goggles`: **called-from-tests-only**
- `swap_eye_patch_action`: **called-from-tests-only**
- `check_illumination_transition`: **called-from-tests-only**
- `adapt_eyes_action`: **called-from-tests-only**

### `puzzle_engine.py` (Reachable: True)
- `get_puzzle_for_location`: **never-called**
- `format_puzzle_context_for_prompt`: **never-called**

### `quest_engine.py` (Reachable: True)
- `is_time_limited`: **called-from-tests-only**
- `get_template`: **never-called**
- `check_prerequisites`: **called-from-tests-only**
- `get_available_quests_for_location`: **never-called**

### `ration_engine.py` (Reachable: True)
- `is_food_or_drink`: **never-called**
- `get_or_create_food_status`: **called-from-tests-only**
- `preserve_food`: **called-from-tests-only**
- `consume_ration`: **called-from-tests-only**

### `rumor_diffusion_engine.py` (Reachable: True)
- `get_distorted_text_for_hops`: **called-from-tests-only**

### `save_load_manager.py` (Reachable: False)
- `set_saves_directory`: **called-from-tests-only**
- `get_saves_directory`: **never-called**
- `list_slots`: **called-from-tests-only**
- `delete_slot`: **called-from-tests-only**
- `auto_save`: **called-from-tests-only**
- `quick_save`: **called-from-tests-only**
- `quick_load`: **called-from-tests-only**

### `siege_engine.py` (Reachable: False)
- `take_damage`: **called-from-tests-only**
- `damage_barrier`: **never-called**
- `damage_wall`: **never-called**
- `damage_gate`: **never-called**
- `fill_moat`: **never-called**
- `damage_battlement`: **never-called**
- `casualty_count`: **never-called**
- `casualty_rate`: **never-called**
- `apply_casualties`: **never-called**
- `morale_tier`: **never-called**
- `adjust_morale`: **never-called**
- `initialize_fortress_defense`: **called-from-tests-only**
- `create_siege_engine`: **called-from-tests-only**
- `initialize_siege`: **called-from-tests-only**
- `execute_artillery_phase`: **called-from-tests-only**
- `execute_advance_phase`: **called-from-tests-only**
- `resolve_formation_clash`: **called-from-tests-only**
- `execute_breach_assault_phase`: **never-called**
- `execute_morale_and_logistics_phase`: **called-from-tests-only**
- `advance_siege_turn`: **called-from-tests-only**
- `execute_commando_action`: **called-from-tests-only**

### `skills.py` (Reachable: True)
- `get_category_display_name`: **called-from-tests-only**
- `can_player_acquire`: **called-from-tests-only**
- `calculate_unique_skill_drop_chance`: **never-called**
- `apply_passive_bonuses`: **called-from-tests-only**
- `diverge_skill_from_magic_word`: **never-called**
- `parse_skill_template`: **never-called**

### `sleep_engine.py` (Reachable: True)
- `get_clock`: **called-from-tests-only**
- `check_microsleep`: **never-called**
- `apply_stimulant`: **called-from-tests-only**
- `resolve_sleep`: **called-from-tests-only**

### `stat_engine.py` (Reachable: True)
- `calculate_required_exp`: **called-from-tests-only**
- `calculate_windup_multiplier`: **called-from-tests-only**
- `calculate_incantation_multiplier`: **called-from-tests-only**
- `calculate_poise`: **called-from-tests-only**
- `get_sub_stat`: **called-from-tests-only**
- `set_sub_stat`: **called-from-tests-only**
- `modify_sub_stat`: **called-from-tests-only**
- `get_tier_description_ko`: **never-called**
- `format_stat_sheet_ko`: **called-from-tests-only**

### `state.py` (Reachable: True)
- `to_korean_summary`: **called-from-tests-only**
- `to_prompt_keywords`: **called-from-tests-only**
- `display_weight`: **never-called**
- `tooltip_text`: **called-from-tests-only**
- `appraisal_text`: **never-called**
- `to_korean_visual_summary`: **called-from-tests-only**
- `to_image_prompt_keywords`: **called-from-tests-only**
- `per_stat`: **never-called**
- `str_mod`: **called-from-tests-only**
- `stamina_regen_effective`: **never-called**
- `display_name_ko`: **never-called**
- `disposition_ko`: **never-called**
- `impression_ko`: **called-from-tests-only**
- `prune_memories`: **never-called**
- `get_recent_off_screen_logs`: **called-from-tests-only**
- `relevant_memories`: **called-from-tests-only**
- `memory_summary`: **called-from-tests-only**
- `distort_event`: **called-from-tests-only**
- `outfit`: **called-from-tests-only**
- `fatigue_status_ko`: **called-from-tests-only**
- `stamina_status_ko`: **never-called**
- `movement_speed_mps`: **called-from-tests-only**
- `max_draw_weight_lbs`: **never-called**
- `incantation_speed_multiplier`: **never-called**
- `allocate_stat`: **called-from-tests-only**
- `current_day`: **called-from-tests-only**
- `current_minute`: **called-from-tests-only**
- `current_week`: **never-called**
- `day_of_week_ko`: **called-from-tests-only**
- `effective_start_year`: **never-called**
- `current_year`: **called-from-tests-only**
- `current_month`: **called-from-tests-only**
- `current_day_of_month`: **never-called**
- `current_season`: **called-from-tests-only**
- `calendar_display_ko`: **called-from-tests-only**
- `get_distance`: **called-from-tests-only**
- `time_display_ko`: **called-from-tests-only**
- `items_in_location`: **never-called**
- `recalculate_equipment_stats`: **called-from-tests-only**
- `simulate_npc_needs_and_economy`: **called-from-tests-only**
- `exchange_rumors_in_locations`: **called-from-tests-only**
- `generate_news_poster`: **called-from-tests-only**
- `advance_npc_schedules`: **called-from-tests-only**
- `to_audio_html`: **never-called**
- `register_dynamic_npc`: **never-called**
- `register_dynamic_location`: **never-called**
- `register_dynamic_item`: **never-called**
- `update_environment_state`: **never-called**

### `status_engine.py` (Reachable: True)
- `create_status`: **never-called**

### `stealth_engine.py` (Reachable: False)
- `calculate_footstep_sound_db`: **called-from-tests-only**
- `calculate_distance_sound_attenuation`: **never-called**
- `evaluate_stealth_approach`: **called-from-tests-only**
- `evaluate_eavesdropping`: **called-from-tests-only**

### `thermal_engine.py` (Reachable: True)
- `get_clothing_spec`: **never-called**
- `calculate_net_insulation`: **called-from-tests-only**
- `determine_thermal_stage`: **never-called**
- `light_campfire`: **called-from-tests-only**

### `time_calendar_engine.py` (Reachable: False)
- `resolve_world_start_year`: **called-from-tests-only**
- `determine_action_duration`: **called-from-tests-only**

### `toxicology_engine.py` (Reachable: True)
- `ingest_potion`: **called-from-tests-only**
- `reset_on_full_rest`: **called-from-tests-only**

### `trap_engine.py` (Reachable: True)
- `get_contextual_trap_specs`: **called-from-tests-only**
- `trigger_trap`: **called-from-tests-only**

### `validator.py` (Reachable: True)
- `detect_target_part`: **never-called**
- `parse_action_components`: **called-from-tests-only**

### `vein_restoration_engine.py` (Reachable: False)
- `get_circuit_state`: **called-from-tests-only**
- `perform_surgery`: **called-from-tests-only**
- `brew_vein_tonic`: **called-from-tests-only**

### `weather_engine.py` (Reachable: True)
- `get_elemental_multiplier`: **called-from-tests-only**
- `format_weather_context_for_prompt`: **never-called**

### `weather_magic_engine.py` (Reachable: True)
- `get_anomalies`: **called-from-tests-only**
- `cast_weather_magic`: **called-from-tests-only**
- `resolve_combat_weather_tick`: **called-from-tests-only**
- `resolve_travel_weather_exposure`: **called-from-tests-only**
