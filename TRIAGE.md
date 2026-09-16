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

---

### Category B: `DUPLICATE_DELETE` (Deletion Candidates)
1. **`save_load_manager.py`**:
   - Fully superseded by `persistence.py`. Redundant JSON file-based persistence engine.
2. **`merchant_barter_engine.py`**:
   - Orphan file (unregistered in `__init__.py`). Slated for complete absorption into `EconomyEngine` under Backlog #21 (`UnifiedCommerceEngine`). Deletion / absorption candidate.

---

### Category C: `SHELVED / P1-2 BACKLOG` (Unreachable: 3/64 modules)
Current unreachable modules identified by `reachability_audit.py` (3 of 64):
1. **`combat_time_track_engine.py`**: **[공식 보류 SHELVED]** — 미터 단위 거리/초 단위 인터럽트 엔진. 현재 고정 턴제 전투 전면 개편 세션으로 보류 (CombatDistanceManager, ActionTimeTrackEngine).
2. **`merchant_barter_engine.py`**: **[공식 보류 SHELVED - 통합 대기]** — `EconomyEngine` 흡수 대기.
3. **`siege_engine.py`**: **[공식 보류 SHELVED]** — 1,065줄 요새 공성전/군단 전술 엔진. 독립 공성 시나리오 설계 세션까지 분리 보류.

### Category D: `UNCLEAR` (Needs Human Judgment)
- None. All 16 modules and priority methods have unambiguous roles and clean triage categorizations.
