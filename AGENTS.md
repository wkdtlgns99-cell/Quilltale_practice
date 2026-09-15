# SYSTEM_RULES:QUILLTALE
[CRITICAL] Strict adherence required. Violation = immediate rollback.

<DoD_Gate>
1. RUN `pytest tests/` before completion. Report stdout verbatim. NO faked results.
2. If modifying `state.py` or `src/world/*_engine.py`, RUN `eval_runner.py --no-judge` & report `invalid_transition_rate`.
3. Write >=1 pytest for any new feature.
4. NO test-gaming: never edit test assertions/skip tests to pass. Fix logic.
5. NO REGRESSION: record BASELINE pass/fail before starting. Fail count must not increase.
</DoD_Gate>

<Code_Hygiene>
1. NO regex/patch/temp scripts in `scratch/` for production modules.
2. USE file edit tools directly. Show full diff, no `...` or `/* same */`.
3. `scratch/` = local-only, never tracked in git. Tests use `tmp_path` only.
4. NO committing `__pycache__/`, `*.pyc`, or 0-byte files. Check `git status`.
5. Before commit: run ruff/pyflakes on `src/`. Zero syntax errors, unused vars, undefined names.
6. UI (`app.py`): I/O and rendering only. Zero business logic. Never block UI thread (async). All player-facing text: 100% natural Korean.
</Code_Hygiene>

<Dup_Prevention>
1. SEARCH existing modules before creating any new class/engine/template.
2. Verify `data/templates/*.json` and `data/legacy/*.json` for key overlaps before adding.
3. `WorldState` modifications must include defaults/optional fields for backward-compatible deserialization.
4. Korean text files: always explicit UTF-8 encoding.
5. Unique filenames across packages. No reuse (e.g. `profiler.py` in two dirs).
6. CALLER CHECK: grep all callers before changing any function/class signature.
</Dup_Prevention>

<Two_Pass>
1. PASS 1 (Python): 100% deterministic logic (dice, combat, status, quest). No math in LLM prompt.
2. PASS 2 (LLM): Narrative rendering only.
3. NPC episodic memory: must have truncation/summarization to prevent token overflow.
4. Network/image APIs: must have fallback paths. Log failures, never return fake success.
</Two_Pass>

<Scope_Commit>
1. AGENTS.md edits: forbidden without explicit user approval. If rule changes are needed, explain rationale and ASK first.
2. ATOMIC commit: 1 session = 1 task only. No mixed refactoring.
3. Backlog deletion: forbidden without explicit user approval.
</Scope_Commit>

<Handoff_Truth>
1. When marking backlog [x], record actual file path + passing test name in SESSION_HANDOFF.md.
2. At session start, verify handoff marks via ls/grep before scoping work.
3. If change touches Qdrant/Docker/external APIs untestable locally, mark "⚪ UNVERIFIED".
</Handoff_Truth>

<Wiring>
1. Feature not "done" until called from live turn path (`TwoPassEngine.compute_pass1`/`sanitize_pass2_result` or `GameMasterAgent.process_turn`).
2. Reachability check: confirm new code is statically reachable from `app.py` → `game_master.py`. `grep -rn "<fn>" --include=*.py . | grep -v tests/` — no hits = unwired.
3. No write-only fields on NPC/Player without >=1 deterministic reader. Mark `# TODO: unconsumed field` if deferred.
4. Search before creating new engine file. Extend existing module if same responsibility.
5. Every new engine needs >=1 integration test through `process_turn()` or `compute_pass1()`.
6. Unbounded-growth lists (`npc.memories`, `off_screen_logs`, `physical_traces`) need explicit cap/decay policy.
7. Docs follow code: grep-verify named class/function exists before writing "implemented" in docs.
8. Freeze new engine-file creation until reachability audit is clean.
</Wiring>

<Dev_Ops>
1. Communication: token-efficient Korean, caveman style without filler words ('우가' 제외 단답/원시인 말투).
2. Handoff updates: preserve fixed rules, HW specs, backlog. Update details only.
3. Environment: laptop=content+system, lab=system-only.
4. Before proposing new class/engine/template: search codebase for existing similar code. Report findings and ask user before creating.
5. New game data classes MUST include `traits: List[str] = field(default_factory=list)`.
6. Proposals/questions to user: always include concrete explanation of what/why.
7. External LLM delegation: (1) provide executable prompts, (2) internal code = interface/skeleton only, (3) bulk data/content generation → external LLM.
8. Incremental Integration: Step 1 = standalone module + unit test pass. Step 2 = wire slot to TwoPassEngine/GameMasterAgent. Step 3 = full regression (BASELINE) pass.
</Dev_Ops>

<Report_Format>
Session end report (exact format):
### 1. Modified Files
### 2. Pytest Results (verbatim, pass/fail counts)
### 3. Added/Modified Tests (function names & purpose)
### 4. Doc Alignment Check (status + propose updates if conflict)
</Report_Format>
