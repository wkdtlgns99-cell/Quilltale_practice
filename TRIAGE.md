# TRIAGE: Unreachable and Tests-Only Modules Classification

> **Generated during Remediation Phase B**  
> **Status**: Triage and classification only. No deletions or code edits performed without explicit human review.

---

## 1. Required Architecture Comparisons

### 1.1 `save_load_manager.py` vs `persistence.py`
- **Evidence & Call-site Analysis**:
  - `persistence.py`: Fully reachable from live entrypoints (`app.py`, `src/agents/game_master.py`, `src/world/__init__.py`). Implements SQLite3 document store (`save_session`, `load_session`, `manual_save`, `load_manual_save`, `list_saved_worlds`). Actively used throughout the entire runtime.
  - `save_load_manager.py`: Unreachable from all live entrypoints. Not registered in `src/world/__init__.py`. Saves raw JSON files to `saves/` with `.tmp` and `.bak` backups. Called only by `tests/test_save_load_manager.py`.
- **Verdict**: **`DUPLICATE_DELETE`**
  - `persistence.py` is the single source of truth for persistence. `save_load_manager.py` is a duplicate implementation. If slot metadata caching is desired in the future, it should be added as a column to `save_slots` table in `persistence.py`.

### 1.2 `attack_physics_engine.py` + `stat_engine.py` vs Live Combat Math (`dice.py` / `skills.py` / `npc_skill_engine.py`)
- **Evidence & Call-site Analysis**:
  - Live Combat Math:
    - `dice.py` handles d20 rolls, advantages, critical hits, DC checks.
    - `skills.py` handles skill registration, difficulty checks, MP/stamina costs.
    - `npc_skill_engine.py` executes combat skill attacks, calculating deterministic damage with base formula: `base_dmg + stat_mod * 1.5 + weapon_power - target_armor`.
  - Unwired Real-unit Physics:
    - `stat_engine.py`: Calculates human-peak anchored attributes, maximum draw weight (lbs), sprint speed (m/s), reaction time (s).
    - `attack_physics_engine.py`: Calculates bow draw weight tension ratio (`can_draw_bow`), arrow flight time (`calculate_flight_time`), kinetic penetration, and tag-based physics damage.

### 2. Current Classification & True Reachability Status (2026-09-16 Verified)

### Category A: `WIRED_ACTIVE` (Live Path Verified)
These modules are confirmed fully reachable and active in the live turn execution path:
1. **`cognitive_engine.py`**: Reachable (`TwoPassEngine` autonomous off-screen NPC next intent prediction).
2. **`attack_physics_engine.py`**: Reachable (`npc_skill_engine.py` & `two_pass_engine.py` ranged bow draw weight, flight time, overdraw ratio).
3. **`stat_engine.py`**: Reachable (anchored human-peak attributes, movement speed, draw weight).
4. **`object_physics_engine.py`**: Reachable (`UniversalObjectPhysicsEngine` object damage and burning).
5. **`campsite_engine.py`**: Reachable (`TwoPassEngine` campsite safety, rest, sleep recovery).
6. **`stealth_engine.py`**: Reachable (`TwoPassEngine` stealth infiltration and acoustic eavesdropping).
7. **`harvest_engine.py`**: Reachable (`TwoPassEngine` anatomy harvest and butchery loop).
8. **`mana_burn_engine.py`**: Reachable (`TwoPassEngine` ether backlash and mana burn).
9. **`alcohol_engine.py`**: Reachable (`TwoPassEngine` tavern drinking and drunkenness).
10. **`botany_engine.py`**: Reachable (`TwoPassEngine` flora foraging).
11. **`vein_restoration_engine.py`**: Reachable (`TwoPassEngine:2.75 Sub-path B` surgery loop).
12. **`time_calendar_engine.py`**: Reachable (`TwoPassEngine:compute_pass1` variable turn duration).
13. **`combat_time_track_engine.py`**: Reachable (`TwoPassEngine:resolve_action_combat_distance_and_timing` 5대 사거리 존 & PER 인터럽트).
14. **`merchant_barter_engine.py`**: Reachable (`TwoPassEngine:resolve_action_barter` 물물교환, 감정, 금화 깎기, 밀수 검문).
15. **`siege_engine.py`**: Reachable (`TwoPassEngine:resolve_action_siege` 요새 다층 방호, 포격, 특공 침투).
16. **`entities.py`**: Reachable (순수 도메인 엔티티 19종 모델).

---

### Category B: `DUPLICATE_DELETE` (Deletion Candidates)
1. **`save_load_manager.py`**:
   - Fully superseded by `persistence.py`. Redundant JSON file-based persistence engine.

---

### Category C: `SHELVED / UNREACHABLE` (0 of 65 modules)
- **None**. All 65 `src/world/` modules are 100% reachable from live game entrypoints (`app.py`, `src/agents/game_master.py`). Verified by `reachability_audit.py`.

---

### Category D: `UNCLEAR` (Needs Human Judgment)
- None. All modules have unambiguous roles and clean triage categorizations.
