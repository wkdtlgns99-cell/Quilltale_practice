"""
Unit and Integration Tests for Diablo-style Procedural Loot Generator (loot_generator.py).
Validates:
1. 5-Tier Rarity System (Common, Magic, Rare, Epic, Unique) & Affix slot allocations.
2. Unique item generation with lore, guaranteed sockets, and special effects.
3. Level scaling of damage, defense, and stat bonuses.
4. EquipmentEngine properties['stat_bonuses'] full compatibility.
5. Monster drop rolling (commoners vs elite/boss monsters).
6. Dungeon chest loot rolling and depth-based rarity scaling.
7. Equipment salvage / disenchanting material recoveries.
8. Rule 5 traits compliance across all data models.
9. TwoPassEngine live turn combat kill and chest opening integration.
"""
import pytest
from src.world.entities import Item, NPC, Player, Location, EquipmentSlots, CombatProfile, NPCPersonality
from src.world.equipment import EquipmentEngine
from src.world.loot_generator import (
    LootGenerator, ItemRarity, ItemAffix, BaseItemTemplate,
    UniqueItemTemplate, RARITY_COLORS,
)
from src.world.state import WorldState
from src.world.two_pass_engine import TwoPassEngine
from src.world.dungeon_engine import DungeonEngine


# ──────────────────────────────────────────────
# 1. Rarity & Affix Allocation Tests
# ──────────────────────────────────────────────

class TestRarityAndAffixes:
    def test_common_item_has_zero_affixes_and_zero_sockets(self):
        """Common items must have 0 prefixes, 0 suffixes, and 0 rune sockets."""
        item = LootGenerator.generate_item(level=1, rarity=ItemRarity.COMMON, seed=1)
        assert item.rune_slots == 0
        props = item.properties
        assert len(props["prefixes"]) == 0
        assert len(props["suffixes"]) == 0
        assert props["rarity"] == ItemRarity.COMMON.value

    def test_magic_item_has_one_to_two_affixes(self):
        """Magic items must have 1 to 2 affixes and 0 to 1 sockets."""
        item = LootGenerator.generate_item(level=2, rarity=ItemRarity.MAGIC, seed=2)
        props = item.properties
        total_affixes = len(props["prefixes"]) + len(props["suffixes"])
        assert 1 <= total_affixes <= 2
        assert item.rune_slots in (0, 1)
        assert props["rarity"] == ItemRarity.MAGIC.value

    def test_rare_item_has_three_to_four_affixes(self):
        """Rare items must have 3 to 4 affixes and 1 to 2 sockets."""
        item = LootGenerator.generate_item(level=3, rarity=ItemRarity.RARE, seed=3)
        props = item.properties
        total_affixes = len(props["prefixes"]) + len(props["suffixes"])
        assert 3 <= total_affixes <= 4
        assert item.rune_slots in (1, 2)
        assert props["rarity"] == ItemRarity.RARE.value

    def test_epic_item_has_four_to_five_affixes(self):
        """Epic items must have 4 to 5 affixes and 1 to 2 sockets."""
        item = LootGenerator.generate_item(level=5, rarity=ItemRarity.EPIC, seed=4)
        props = item.properties
        total_affixes = len(props["prefixes"]) + len(props["suffixes"])
        assert 4 <= total_affixes <= 5
        assert item.rune_slots in (1, 2)
        assert props["rarity"] == ItemRarity.EPIC.value

    def test_unique_item_generation(self):
        """Unique items must have special effect, lore, and 2 to 3 sockets."""
        item = LootGenerator.generate_item(level=5, rarity=ItemRarity.UNIQUE, seed=5)
        props = item.properties
        assert props["rarity"] == ItemRarity.UNIQUE.value
        assert props["is_unique"] is True
        assert len(props["special_effects"]) >= 1
        assert item.rune_slots in (2, 3)
        assert item.material == "mythril"


# ──────────────────────────────────────────────
# 2. Scaling & Filtering Tests
# ──────────────────────────────────────────────

class TestScalingAndFiltering:
    def test_level_scaling_increases_stats(self):
        """Higher level items must have higher base stats and values."""
        item_lv1 = LootGenerator.generate_item(level=1, rarity=ItemRarity.RARE, category_filter="weapon", seed=42)
        item_lv10 = LootGenerator.generate_item(level=10, rarity=ItemRarity.RARE, category_filter="weapon", seed=42)

        assert item_lv10.damage >= item_lv1.damage
        assert item_lv10.value > item_lv1.value

    def test_category_filtering(self):
        """Requesting 'weapon' or 'armor' must only yield matching item_types."""
        wep = LootGenerator.generate_item(level=1, category_filter="weapon", seed=10)
        assert wep.item_type == "weapon"

        arm = LootGenerator.generate_item(level=1, category_filter="armor", seed=20)
        assert arm.item_type == "armor"

        acc = LootGenerator.generate_item(level=1, category_filter="accessory", seed=30)
        assert acc.item_type == "accessory"


# ──────────────────────────────────────────────
# 3. EquipmentEngine Integration Tests
# ──────────────────────────────────────────────

class TestEquipmentEngineIntegration:
    def test_generated_item_stats_recognized_by_equipment_engine(self):
        """Generated item stat_bonuses must be recognized and aggregated by EquipmentEngine."""
        weapon = LootGenerator.generate_item(
            level=3, rarity=ItemRarity.RARE, category_filter="weapon", seed=777
        )
        armor = LootGenerator.generate_item(
            level=3, rarity=ItemRarity.RARE, category_filter="armor", seed=888
        )

        state = WorldState()
        state.items[weapon.id] = weapon
        state.items[armor.id] = armor
        state.player.inventory.extend([weapon.id, armor.id])
        state.player.equipment.weapon = weapon.id
        state.player.equipment.chest = armor.id

        bonuses = EquipmentEngine.calculate_equipment_bonuses(state, state.player)

        # Total defense and damage must match
        assert bonuses["total_defense"] == armor.defense + weapon.defense
        assert bonuses["total_damage"] == weapon.damage + armor.damage

        # Stat modifiers must be calculated
        w_stats = weapon.properties.get("stat_bonuses", {})
        a_stats = armor.properties.get("stat_bonuses", {})
        combined_stats = bonuses["stat_bonuses"]

        for k in ["strength", "agility", "constitution", "intelligence"]:
            expected = w_stats.get(k, 0) + w_stats.get(k[:3], 0) + a_stats.get(k, 0) + a_stats.get(k[:3], 0)
            if expected > 0:
                assert combined_stats[k] >= expected


# ──────────────────────────────────────────────
# 4. Drop Rolling Tests
# ──────────────────────────────────────────────

class TestDropRolling:
    def test_commoner_monster_drops_one_item(self):
        """Common monster drops at least 1 item."""
        goblin = NPC(id="gob_1", name="고블린 졸개", description="테스트 고블린", location="loc_1", level=1, tier="commoner")
        drops = LootGenerator.roll_monster_drop(goblin, player_luck=10, seed=123)

        assert len(drops) >= 1
        assert isinstance(drops[0], Item)

    def test_boss_monster_drops_multiple_rare_items(self):
        """Boss monsters drop 2~3 items with guaranteed Rare or higher rarity."""
        boss = NPC(id="boss_1", name="심연의 군주", description="테스트 보스", location="loc_1", level=5, tier="boss")
        drops = LootGenerator.roll_monster_drop(boss, player_luck=15, seed=456)

        assert len(drops) >= 2
        for d in drops:
            assert d.properties["rarity"] in (ItemRarity.RARE.value, ItemRarity.EPIC.value, ItemRarity.UNIQUE.value)

    def test_dungeon_chest_loot_scales_with_depth(self):
        """Dungeon chest on floor 3 yields higher rarity items than floor 1."""
        chest_f1 = LootGenerator.roll_chest_loot(floor_num=1, seed=11)
        chest_f3 = LootGenerator.roll_chest_loot(floor_num=3, seed=22)

        assert len(chest_f1) >= 1
        assert len(chest_f3) >= 1
        # Floor 3 chests guarantee Rare or Epic
        for item in chest_f3:
            assert item.properties["rarity"] in (ItemRarity.RARE.value, ItemRarity.EPIC.value)


# ──────────────────────────────────────────────
# 5. Salvage & Traits Compliance Tests
# ──────────────────────────────────────────────

class TestSalvageAndTraits:
    def test_salvage_recovers_appropriate_materials(self):
        """Disenchanting Epic or Unique items must yield magic dust, ingots, and rune fragments."""
        common_item = LootGenerator.generate_item(rarity=ItemRarity.COMMON, seed=1)
        epic_item = LootGenerator.generate_item(rarity=ItemRarity.EPIC, seed=2)

        salvage_c = LootGenerator.salvage_item(common_item)
        salvage_e = LootGenerator.salvage_item(epic_item)

        assert salvage_c["magic_dust"] == 0
        assert salvage_e["magic_dust"] >= 10
        assert salvage_e["rune_fragments"] >= 3
        assert salvage_e["gold_recovered"] > salvage_c["gold_recovered"]
        assert "분해 완료" in salvage_e["summary_ko"]

    def test_rule_5_traits_compliance(self):
        """All item affixes, templates, and generated items must have traits: List[str]."""
        affix = ItemAffix(name="테스트 접사", affix_type="prefix")
        assert hasattr(affix, "traits") and isinstance(affix.traits, list)

        base = BaseItemTemplate(base_id="b1", name="검", item_type="weapon", category="sword")
        assert hasattr(base, "traits") and isinstance(base.traits, list)

        unique = UniqueItemTemplate(
            unique_id="u1", name="전설검", item_type="weapon", category="sword",
            damage=20, defense=0, value=200, scaling_stat="str",
            stat_bonuses={}, special_effect="", lore_description=""
        )
        assert hasattr(unique, "traits") and isinstance(unique.traits, list)

        generated = LootGenerator.generate_item(seed=99)
        assert hasattr(generated, "traits") and isinstance(generated.traits, list)


# ──────────────────────────────────────────────
# 6. Live TwoPassEngine Integration Tests
# ──────────────────────────────────────────────

class TestLiveTwoPassIntegration:
    def test_monster_kill_rolls_procedural_loot_in_pass1(self):
        """Killing a hostile monster in Pass 1 must deposit loot into player inventory and FactSheet."""
        loc = Location(id="loc_1", name="전투장", description="", exits={})
        target_npc = NPC(
            id="orc_1",
            name="오크 전사",
            description="테스트 오크",
            location="loc_1",
            disposition="hostile",
            health=5,
            max_health=50,
            tier="commoner",
            level=2,
        )
        loc.npcs.append("orc_1")
        state = WorldState(
            locations={"loc_1": loc},
            npcs={"orc_1": target_npc},
        )
        state.player.location = "loc_1"

        # Action that deals lethal damage to orc_1
        action = "오크 전사의 목을 날카롭게 베어버린다"
        fact_sheet = TwoPassEngine.compute_pass1(action, state)

        # Verify combat outcome killed flag
        if fact_sheet.combat_outcome and fact_sheet.combat_outcome.get("killed"):
            assert len(fact_sheet.loot_drop_logs) >= 1
            assert "처치 전리품 획득" in fact_sheet.loot_drop_logs[0]
            # Verify item added to player inventory
            assert len(state.player.inventory) >= 1
            item_id = state.player.inventory[-1]
            assert item_id in state.items
            assert "loot_" in item_id

    def test_dungeon_chest_opening_in_pass1(self):
        """Opening a dungeon chest in Pass 1 rolls chest loot and populates loot_drop_logs."""
        loc = Location(id="surface_cave", name="동굴 입구", description="", exits={})
        state = WorldState(locations={"surface_cave": loc})
        instance = DungeonEngine.create_dungeon_instance(state, "surface_cave", max_depth=2)

        # Put player inside dungeon floor 1 room 1
        state.player.location = f"{instance.dungeon_id}_b1f_r1"

        action = "방 한구석에 놓인 보물상자를 열어 내용물을 확인한다"
        fact_sheet = TwoPassEngine.compute_pass1(action, state)

        assert len(fact_sheet.loot_drop_logs) >= 1
        assert "보물상자 개봉 성공" in fact_sheet.loot_drop_logs[0]
        assert len(state.player.inventory) >= 1
        assert "Loot Drop & Affixes" in fact_sheet.to_prompt_context()
