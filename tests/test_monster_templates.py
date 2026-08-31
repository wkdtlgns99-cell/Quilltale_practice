import json
import pytest
from pathlib import Path
from src.memory.memory_manager import MemoryManager


def test_monster_templates_json_validity():
    path = Path("data/templates/monster_templates.json")
    assert path.exists(), "monster_templates.json should exist"
    with open(path, "r", encoding="utf-8") as f:
        monsters = json.load(f)
    assert len(monsters) == 82, f"Expected 82 monsters, got {len(monsters)}"

    ids = [m["id"] for m in monsters]
    # Check original bosses & elites
    assert "copper_scaled_thunder_catfish" in ids
    assert "slaughterhouse_hook_scale_merchant" in ids
    assert "boiler_alveoli_iron_golem" in ids
    assert "drowned_captain_anchor_bearer" in ids
    assert "notary_of_the_wax_seal" in ids
    assert "music_box_heart_ballerina" in ids
    assert "mercury_mirror_portrait_matron" in ids

    # Check 1st batch new bosses
    assert "crestfallen_knight_elastic_limit" in ids
    assert "taxidermist_optometrist_dr_eyeless" in ids
    assert "executioner_negative_pressure_cleaver" in ids
    assert "latent_heat_triple_chanter_baran" in ids
    assert "mass_defect_alchemage_alcahest" in ids
    assert "silence_librarian_destructive_interference" in ids
    assert "refraction_prism_sorceress_velche" in ids
    assert "thermoelectric_archmage_seebeck" in ids
    assert "non_newtonian_fluid_mage_balak" in ids

    # Check 2nd batch new bosses
    assert "angular_momentum_mage_gyros" in ids
    assert "surface_tension_shield_membra" in ids
    assert "supercritical_artillery_mage_walter" in ids
    assert "capillary_osmosis_spore_fungus" in ids
    assert "sonic_boom_rapier_duelist_allegro" in ids

    # Check 3rd batch new sword saint bosses
    assert "friction_heat_sunspot_swordsman_volkov" in ids
    assert "shear_stress_wire_iaidoka_kaede" in ids
    assert "total_internal_reflection_duelist_sylphia" in ids
    assert "lorentz_rail_katana_raiden" in ids
    assert "cavitation_water_hammer_greatsword_bartholomew" in ids
    assert "dielectric_barrier_ceramic_saint_galvani" in ids
    assert "pneumatic_piston_sword_saint_ferrum" in ids
    assert "moebius_phase_sword_saint_infinita" in ids

    # Check 4th batch new archer bosses
    assert "predetermined_dusk_archer_orphea" in ids
    assert "negative_imprint_shadow_archer_belial" in ids
    assert "marrow_resonance_bone_sniper_osseus" in ids
    assert "leyline_inversion_zenith_archer_thalia" in ids
    assert "astral_constellation_archer_astrid" in ids
    assert "retinal_siphon_blind_archer_antiope" in ids

    # Check 5th batch new bosses
    assert "solar_core_sunspot_artillery_helios" in ids
    assert "lightning_afterimage_assassin_zephyros" in ids
    assert "infinite_mana_abyssal_sage_agatha" in ids
    assert "trinity_tri-synchronous_puppet_monarch" in ids
    assert "memory_pickpocket_assassin_nemos" in ids
    assert "pocket_dimension_thief_bartholome" in ids
    assert "concept_erasure_faceless_noir" in ids
    assert "sound_thief_silence_cadenza" in ids
    assert "debt_deferral_assassin_moratori" in ids
    assert "shadow_smuggler_puppeteer_shady" in ids

    # Check 6th batch new bosses
    assert "blood_meridian_berserk_assassin_karma" in ids
    assert "trickster_pixie_resource_thief" in ids
    assert "grave_robber_necromantic_assassin_mortus" in ids
    assert "shadow_assassin_king_dokgo_jan" in ids
    assert "mount_hua_plum_blossom_master_baekun" in ids
    assert "firmament_heavens_heavy_blade_cheon_ak" in ids
    assert "sword_saint_mujin_perfection" in ids

    # Check 7th batch new bosses
    assert "wudang_taichi_dual_harmony_jincheon" in ids
    assert "flowing_water_sword_saint_suryong" in ids
    assert "gale_storm_sword_master_pungun" in ids
    assert "heavenly_demon_cult_leader_cheon_mamyung" in ids
    assert "parrying_bell_shield_templar_aegis" in ids
    assert "gravity_shield_magnet_sentinel_ferro" in ids
    assert "shadow_mirror_shield_swordsman_umbra" in ids

    # Check 8th batch new beast bosses
    assert "levitation_abyssal_sky_whale_leviathan" in ids
    assert "oriental_storm_dragon_cheongryong" in ids
    assert "spectral_antler_forest_guardian_elan" in ids
    assert "chlorophyll_solar_sea_bear_ursus" in ids
    assert "leaf_sheep_solar_gastropod_kuro" in ids
    assert "blue_dragon_sea_slug_glaucus" in ids
    assert "leafy_seadragon_camouflaged_spirit_phyco" in ids

    # Check 9th batch new bosses & domain expansions
    assert "continental_tectonic_world_tortoise_tartaros" in ids
    assert "chromatic_prismatic_drake_tiamatos" in ids
    assert "parry_master_strawhat_ronin_hyemuk" in ids
    assert "domain_infernal_dice_gambler_roulette" in ids
    assert "domain_endless_blade_graveyard_muramasa" in ids
    assert "domain_absolute_vacuum_singularity_void" in ids

    # Check 10th batch new bosses
    assert "iron_fist_domain_king_cheon_ak_myung" in ids
    assert "concept_collective_agony_the_weeping_monolith" in ids

    for m in monsters:
        assert "id" in m
        assert "name" in m
        assert "tier" in m
        assert "concept_theme" in m
        assert "observation_clue" in m
        assert "stat_profile" in m
        assert "weakness_exploit" in m
        assert "drops_and_materials" in m
        assert "extractable_skill" in m
        assert "voice_lines" in m


def test_memory_manager_monster_templates_rag():
    mm = MemoryManager()
    count = mm.index_monster_templates()
    assert count == 82, f"Expected 82 indexed monsters, got {count}"

    results = mm.search_monster_templates("접지와 전격 번개", limit=3)
    assert len(results) >= 1
    assert "name" in results[0]
    assert "observation_clue" in results[0]
    assert "stat_profile" in results[0]
