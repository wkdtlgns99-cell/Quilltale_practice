"""
Legacy Character Archiving and World Inhabitation System for Quilltale.
Manages character release/retirement, 3rd-person lore transformation,
and spawning legacy past characters as live NPCs in future sessions.
"""
import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.core.config import LEGACY_DIR
from src.world.state import WorldState, NPC, Item, MemoryEntry, Skill, Title
from src.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class LegacyManager:
    """
    Archives retired or released player characters and integrates them into
    the persistent world lore and NPC ecosystem.
    """

    @classmethod
    def archive_character(
        cls,
        state: WorldState,
        reason: str = "released",
        farewell_note: str = "",
    ) -> Dict[str, Any]:
        """
        Snapshots current player character state and saves it permanently to data/legacy/.
        reason: 'released' (방생/풀어주기) | 'retired' (여정 완결/은퇴)
        """
        LEGACY_DIR.mkdir(parents=True, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        char_name = state.player.name
        legacy_id = f"legacy_{timestamp_str}_{uuid.uuid4().hex[:6]}"

        # Gather player items
        player_items = state.player_inventory_items()
        item_dicts = [i.__dict__ for i in player_items]

        # Extract notable history events
        notable_events = []
        for h in state.history[-10:]:
            notable_events.append({
                "turn": h.get("turn", 0),
                "action": h.get("action", ""),
                "narration": h.get("narration", ""),
            })

        reason_ko = "더 넓은 세상을 향해 자유롭게 방생됨" if reason == "released" else "기나긴 여정을 마치고 명예롭게 은퇴함"

        legacy_data = {
            "legacy_id": legacy_id,
            "name": char_name,
            "reason": reason,
            "reason_ko": reason_ko,
            "farewell_note": farewell_note,
            "archived_at": timestamp_str,
            "turn_reached": state.turn,
            "location": state.player.location,
            "reputation": state.player.reputation,
            "stats": {
                "level": state.player.level,
                "health": state.player.health,
                "max_health": state.player.max_health,
                "str_stat": state.player.str_stat,
                "dex_stat": state.player.dex_stat,
                "con_stat": state.player.con_stat,
                "int_stat": state.player.int_stat,
                "wis_stat": state.player.wis_stat,
                "cha_stat": state.player.cha_stat,
                "gold": state.player.gold,
            },
            "equipped_weapon": state.player.equipped_weapon,
            "equipped_armor": state.player.equipped_armor,
            "inventory_item_ids": state.player.inventory,
            "inventory_items": item_dicts,
            "known_facts": state.player.known_facts,
            "notable_events": notable_events,
            "skills": state.player.skills,
            "titles": state.player.titles,
            "skill_objects": [state.skills_db[sid].__dict__ for sid in state.player.skills if sid in state.skills_db],
            "title_objects": [state.titles_db[tid].__dict__ for tid in state.player.titles if tid in state.titles_db],
        }

        save_path = LEGACY_DIR / f"{legacy_id}.json"
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(legacy_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Successfully archived legacy character: {legacy_id}")
        except Exception as e:
            logger.error(f"Failed to save legacy character {legacy_id}: {e}")

        return legacy_data

    @classmethod
    def convert_to_lore_and_index(
        cls,
        legacy_data: Dict[str, Any],
        memory_manager: MemoryManager,
    ) -> List[str]:
        """
        Converts 1st-person memories of the archived character into 3rd-person
        world lore and rumors, indexing them into Qdrant vector memory.
        """
        name = legacy_data.get("name", "과거의 방랑자")
        loc_id = legacy_data.get("location", "tavern")
        turn = legacy_data.get("turn_reached", 0)
        rep = legacy_data.get("reputation", 0)
        reason_ko = legacy_data.get("reason_ko", "자신만의 길을 걷기 위해 떠남")

        rep_desc = "악명을 떨치던 무자비한 인물" if rep <= -20 else ("많은 이들의 찬사를 받던 고결한 모험가" if rep >= 20 else "세상에 크고 작은 발자취를 남긴 방랑자")

        lore_entries = []

        # 1. Main Legend/Rumor of the character
        main_lore_title = f"전대 모험가 {name}의 전설"
        main_lore_content = (
            f"과거 {turn}번의 계절 동안 {rep_desc}이었던 '{name}'에 대한 소문이 전해진다. "
            f"그는 마지막으로 [{loc_id}] 인근에서 목격되었으며, {reason_ko}."
        )
        memory_manager.index_lore(
            lore_id=f"{legacy_data['legacy_id']}_main",
            title=main_lore_title,
            content=main_lore_content,
            location_id=loc_id,
            tags=["legacy", "legend", name, loc_id],
        )
        lore_entries.append(main_lore_content)

        # 2. Known facts and unsolved quest remnants transformed into lore
        known_facts = legacy_data.get("known_facts", [])
        if known_facts:
            facts_title = f"{name}이 남긴 단서와 미완의 비밀"
            facts_content = f"{name}은(는) 과거 다음 사실들을 밝혀내거나 추적하고 있었다: " + ", ".join(known_facts)
            memory_manager.index_lore(
                lore_id=f"{legacy_data['legacy_id']}_facts",
                title=facts_title,
                content=facts_content,
                location_id=loc_id,
                tags=["legacy", "clue", name],
            )
            lore_entries.append(facts_content)

        return lore_entries

    @classmethod
    def load_all_legacies(cls) -> List[Dict[str, Any]]:
        """Loads all archived legacy character records from disk."""
        results = []
        if not LEGACY_DIR.exists():
            return results

        files = sorted(LEGACY_DIR.glob("legacy_*.json"), key=lambda p: p.stat().st_mtime)
        for p in files:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    results.append(data)
            except Exception as e:
                logger.error(f"Error loading legacy file {p}: {e}")
        return results


    @classmethod
    def spawn_legacy_npcs_to_world(cls, world_state: WorldState) -> List[str]:
        """
        Instantiates archived legacy characters as live NPCs inside the current world state.
        Ensures at most 1 legacy NPC is present in the world to prevent cloning/duplicates.
        """
        # If the world already has a legacy NPC, do not spawn more
        existing_legacies = [n for n in world_state.npcs.values() if getattr(n, "is_legacy", False)]
        if existing_legacies:
            return []

        legacies = cls.load_all_legacies()
        if not legacies:
            return []

        # Pick the most recent legacy character
        leg = legacies[-1]

        legacy_id = leg.get("legacy_id")
        npc_id = f"npc_{legacy_id}"

        # If already in world, skip
        if npc_id in world_state.npcs:
            return []

        name = leg.get("name", "과거의 방랑자")
        title_prefix = "전설의 모험가" if leg.get("reason") == "retired" else "노련한 방랑자"
        npc_name = f"{title_prefix} {name}"

        loc_id = leg.get("location", "tavern")
        if loc_id not in world_state.locations:
            loc_id = "tavern"

        stats = leg.get("stats", {})
        rep = leg.get("reputation", 0)

        # Determine NPC initial disposition and attitude
        if rep >= 20:
            disposition = "friendly"
            attitude = "과거의 모험담을 떠올리며 호의적인 눈빛으로 바라봄"
        elif rep <= -20:
            disposition = "wary"
            attitude = "경계심 가득한 눈초리로 칼자루를 만지작거림"
        else:
            disposition = "neutral"
            attitude = "세월의 풍파를 겪은 듯 조용히 당신을 관찰함"

        npc_desc = (
            f"과거 이 세계를 누볐던 전대 모험가다. 세월의 흔적이 엿보이는 낡은 망토를 걸치고 있으며, "
            f"{leg.get('reason_ko', '자신만의 목적을 품고 서 있다.')}"
        )

        # Carry over items into world state
        inv_ids = []
        for itm_dict in leg.get("inventory_items", []):
            item_obj_id = f"{legacy_id}_{itm_dict['id']}"
            if item_obj_id not in world_state.items:
                itm_copy = dict(itm_dict)
                itm_copy["id"] = item_obj_id
                itm_copy["location"] = npc_id
                world_state.items[item_obj_id] = Item(**itm_copy)
            inv_ids.append(item_obj_id)

        # Create NPC memories of their past journey
        legacy_memories = [
            MemoryEntry(
                turn=0,
                description=f"과거 {leg.get('turn_reached', 0)}번의 턴 동안 세상을 누비며 수많은 모험을 겪었음을 기억하고 있다.",
                emotional_tone="neutral",
                significance=5,
                is_anchor=True,
            )
        ]

        # Restore skills
        legacy_skills = []
        for s_dict in leg.get("skill_objects", []):
            sid = s_dict["id"]
            is_unique = s_dict.get("is_unique", False)
            if is_unique:
                s_dict["owner_npc_id"] = npc_id
            if sid not in world_state.skills_db:
                world_state.skills_db[sid] = Skill(**s_dict)
            legacy_skills.append(sid)

        # Restore titles
        legacy_titles = []
        for t_dict in leg.get("title_objects", []):
            tid = t_dict["id"]
            if tid not in world_state.titles_db:
                world_state.titles_db[tid] = Title(**t_dict)
            legacy_titles.append(tid)

        dex = stats.get("dex_stat", 10)
        ac = 10 + (dex - 10) // 2

        npc = NPC(
            id=npc_id,
            name=npc_name,
            alias_ko=f"전대 {title_prefix}",
            description=npc_desc,
            location=loc_id,
            disposition=disposition,
            attitude_description=attitude,
            alive=True,
            health=stats.get("health", 60),
            max_health=stats.get("max_health", 60),
            armor_class=ac,
            inventory=inv_ids,
            memories=legacy_memories,
            stats_revealed=False,
            is_legacy=True,
            legacy_id=legacy_id,
            age_delta=1,
            skills=legacy_skills,
            titles=legacy_titles,
        )

        world_state.npcs[npc_id] = npc
        if loc_id in world_state.locations:
            if npc_id not in world_state.locations[loc_id].npcs:
                world_state.locations[loc_id].npcs.append(npc_id)

        return [npc_name]


