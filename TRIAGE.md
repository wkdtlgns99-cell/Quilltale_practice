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
- **Verdict**: **`KEEP_WIRE_NOW` (Narrow Ranged/Bow Integration Only)**
  - Do NOT attempt a full wholesale replacement of live combat math (risks breaking balance and tests).
  - Instead, narrowly wire `can_draw_bow`, `calculate_flight_time`, and `evaluate_attack_physics` into ranged bow attacks inside `npc_skill_engine.py` / `two_pass_engine.py` as physics-based damage modifiers and draw strength checks.

---

## 2. Classification of All 16 Unreachable Modules + Tests-Only Priority Modules

### Category A: `KEEP_WIRE_NOW` (Priority for this cycle: Phase C & D)
These modules are directly relevant to current priorities (NPC cognition/psychology engine, physics engine):
1. **`cognitive_engine.py`** (Reachable, but 4/8 public methods tests-only):
   - Methods: `evaluate_player_hypothesis`, `predict_autonomous_next_intent`, `check_micro_leakage`, `generate_external_llm_prompt`.
   - Action: Wire in Phase C1, C2, C3.
2. **`attack_physics_engine.py`** (Unreachable):
   - Action: Wire bow draw weight / flight time into ranged combat in Phase D1.
3. **`stat_engine.py`** (Unreachable):
   - Action: Wire `calculate_max_draw_weight` for bow tension check in Phase D1.
4. **`object_physics_engine.py`** (Unreachable):
   - Action: Wire `UniversalObjectPhysicsEngine` (`damage_object`, `ignite_object`) into object destroy/burn turn actions in Phase D2.

---

### Category B: `DUPLICATE_DELETE` (Deletion Candidates)
1. **`save_load_manager.py`**:
   - Covered completely by `persistence.py`. Redundant JSON file-based persistence engine.
2. **`merchant_barter_engine.py`**:
   - Orphan file (unregistered in `__init__.py`). Slated for complete absorption into `EconomyEngine` under Backlog #21 (`UnifiedCommerceEngine`). Deletion / absorption candidate.

---

### Category C: `KEEP_WIRE_LATER` (Needed eventually, defer to subsequent cycles)
These modules have 100% passing unit tests and clean architectures, but are deferred to preserve the atomic scope of this remediation cycle:
1. **`alcohol_engine.py`**: Defer until Tavern / Campsite recreation loop expansion.
2. **`botany_engine.py`**: Defer until wilderness foraging turn actions are wired.
3. **`campsite_engine.py`**: Defer until long rest / campsite security loop is wired.
4. **`combat_time_track_engine.py`**: Defer until micro-second reaction interrupt turn track is fully phased in.
5. **`harvest_engine.py`**: Defer until post-combat monster butchery / part severing loop is wired.
6. **`mana_burn_engine.py`**: Defer until spell overcharge / ether backlash is wired into magic casting.
7. **`outfit_engine.py`**: Defer until backpack tearing / modular armor layer refit loop is wired.
8. **`siege_engine.py`**: Defer until settlement warfare / siege event trigger is wired.
9. **`stealth_engine.py`**: Defer until dedicated infiltration / eavesdropping turn action is wired.
10. **`time_calendar_engine.py`**: Defer until calendar epoch / daily action duration loop is integrated with `WorldState.turn`.
11. **`vein_restoration_engine.py`**: Defer until medical surgery / clinic interaction loop is wired.

---

### Category D: `UNCLEAR` (Needs Human Judgment)
- None. All 16 modules and priority methods have unambiguous roles and clean triage categorizations.
