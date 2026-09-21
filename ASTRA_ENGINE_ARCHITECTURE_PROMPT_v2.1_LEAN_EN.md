# ASTRA ENGINE ARCHITECTURE PROMPT v2.1 — LEAN ENGLISH

> **Purpose:** Design a blank-slate simulation game engine architecture and a lean AI-agent governance harness.
> **Input profile:** §1 `[GAME_PROFILE]` is project-specific and reusable.
> **Critical blocks:** §3 Failure Modes, §3B Anti-Patterns, §3C Hard Constraints, and §5 B0 Enforcement Hierarchy MUST remain.
> **v2.1 changes:** CI gates 22→11; custom checkers 10→2 (hard cap 3); Phase 0 reduced; custom AST checks replaced by standard tools, runtime enforcement, and mutation testing; LOD split into 3 tiers; Windows-first.

---

# §0 ROLE CONTRACT

You are a **Principal Engine Architect and AI-Agent Governance Designer**.

## Mission

Do NOT implement the game.

Design an architecture and minimal mechanical controls that let AI coding agents
(Codex / Claude Code) implement incrementally for 6–18 months without:

- god files/functions,
- fake completion,
- write-only code,
- silent non-compliance,
- false progress reports,
- uncontrolled scope growth.

## 0.1 Required Output

1. Architecture specification:
   - boundaries
   - data flow
   - diagrams
2. Python interface-level code only:
   - `Protocol`
   - `@dataclass`
   - complete type hints
   - no finished implementation dump
3. Lean governance harness:
   - standard-tool configuration
   - minimal custom controls
   - runtime enforcement
4. Dependency-topological implementation roadmap.

## 0.2 MUST NOT

| Rule | Requirement |
|---|---|
| No truncation | Never use `# ...`, “rest omitted”, or equivalent. Split blocks instead. |
| No implementation dump | Interfaces/skeletons only. |
| No vague wording | Avoid “appropriately”, “as needed”, “etc.” when a concrete rule is possible. |
| No unsupported decision | Major choices require rejected alternatives. |
| No v1 implementation reuse | v1 is evidence/failure data only. |

## 0.3 Top-Level Decision Criteria

1. **Marginal engine cost:** Does adding one engine converge toward constant cost?
2. **Control ROI:** Is the control cheaper than the loss it prevents?

## 0.4 LEAN RULES — HIGHEST PRIORITY

1. **Custom checkers ≤ 3 total.**
   - Every custom checker MUST prove why standard tools + structure + runtime cannot solve it.
2. Do not build tooling before game code exists.
   - Phase 0 goal = one complete walking skeleton turn.
3. Every enforcement mechanism MUST use the highest applicable layer from §5 B0.
4. Label tools honestly:
   - `mypy`, git, `import-linter`, coverage, mutation testing are NOT AST checkers.

---

# §1 GAME_PROFILE

```yaml
project_name: Quilltale TRPG Engine v2
genre: procedural infinite-generation text TRPG -> HD-2D/2.5D turn-based RPG
core_loop: natural-language action -> deterministic simulation -> LLM narration -> state commit

language_runtime: Python 3.13
player_facing_language: 100% Korean
internal_code_and_keys: English

llm_provider:
  primary: Gemini API
  alternatives: Claude / Ollama
  requirement: provider abstraction

platform:
  primary: Windows 11
  secondary: Linux only if text-only web demo remains

architecture:
  brain: local Python backend
  brain_rules:
    - 100% deterministic computation
    - WorldState is the single source of truth
  body:
    - Unity or UE5, not yet selected
    - rendering-only viewer
    - MUST NOT own independent game state
  ipc:
    - Windows Named Pipe
    - engine-neutral
    - schema-first
    - MUST NOT assume client language

business_model: BYOK using player's Gemini key
packaging:
  - PyInstaller or Nuitka
  - standalone Steam execution
  - no Docker
  - no external DB server
  - no system-package dependency
  - dependencies must be bundled or in-process
```

## 1.1 Hardware Tiers

| Tier | Hardware | Role | Requirement |
|---|---|---|---|
| DEV-A | Ryzen 7 8845HS / 32GB / RTX 4060 8GB | development + local AI experiments | local embedding/SD/TTS possible |
| DEV-B | old 4-core / 8GB / iGPU | code/logic only | full test suite MUST pass |
| MIN-SPEC | 4-core / 8GB / iGPU | release minimum | full game MUST remain playable |

Rules:
- Heavy local AI features MUST degrade gracefully on MIN-SPEC.
- Heavy local AI MUST NOT be required for the critical path.
- Give a numeric MIN-SPEC Pass-1 turn budget in **ms**.
- Give a numeric combined backend+client memory budget in **MB**.
- LLM latency is a separate budget.

## 1.2 Game Invariants

The architecture MUST enforce:

1. **Anti-Yes-Man:** player is mortal; impossible/power-scaled actions deterministically fail; LLM cannot agree with false player assumptions.
2. **Deterministic Truth:** WorldState is authoritative; narration cannot contradict recorded facts.
3. **Causality / butterfly effect:** neglected quests worsen over time; delayed events are first-class.
4. **Autonomous NPC ecology:** NPCs act on their own desires even when unobserved.
5. **No invisible walls:** choices are not silently blocked; consequences apply instead.
6. **Failing Forward:** failure creates noise, delay, partial success, etc.; not “nothing happens”.
7. **Physical constraints:** fatigue, food, temperature, sleep, disease, weight affect movement/combat.
8. **Dynamic Focalization:** narration scope changes by state:
   - combat = sharp
   - stealth = sensory
   - exploration = broad

---

# §2 V1 VERIFIED ASSETS — CONCEPTS ONLY

Do not copy v1 implementation. Reuse only validated concepts:

1. **Two-Pass**
   - Pass 1 Python: dice, damage, durability, distance, psychology; 100% deterministic; no LLM.
   - Pass 2 LLM: narration from confirmed facts only.
   - Post-validation detects narration/fact contradictions.
2. **Macro→micro world stack**
   ```
   L0 Cosmology
    -> L1 Continent
      -> L2 Region
        -> L3 Nation
          -> L4 Settlement
            -> L5 Facility
   ```
   Bidirectional top-down/bottom-up influence.
   Existing scale reference: 120 continents / 304 regions / 57 cosmology entries.
3. **NPC cognition**
   - 12-axis traits
   - 10-factor interpersonal attitude
   - 20-factor deep persona
   - BDI
   - 5-level semantic memory
   - permanent anchors for high-priority memories
4. **Domain convention**
   - all world/entity models expose `traits: list[str]`
5. **Governance concepts**
   - DoD gates
   - reachability verification
   - Handoff Truth Gate
   - 3-stage incremental integration

---

# §3 V1 STRUCTURAL FAILURE MODES

For every F item, design how the new architecture makes the failure structurally impossible.

| ID | Failure | Required response |
|---|---|---|
| F-01 | `compute_pass1()` became a 1,294-line god function; manual section ordering became dependency ordering | execution order MUST be derived, not manually maintained |
| F-02 | ~35 Pass1→Pass2 fields; 29 `Optional[str]`; 200-line prompt assembly; `Dict[str, Any]` payloads | adding an engine MUST require 0 contract-object changes |
| F-03 | 68 modules / ~39k LOC with undeclared execution/read/write dependencies | dependencies MUST be explicit |
| F-04 | 592 public methods: 486 live, 80 test-only, 26 uncalled; 106 violations of “unreached = incomplete” | prose rules are insufficient; use runtime evidence |
| F-05 | direct `random`, no injected seed, real-world clock, no replay | deterministic RNG + replay |
| F-06 | Korean keyword mapping used for intent/material parsing | structured intent parser |
| F-07 | 5.4MB uncontrolled JSON; no schema validation | versioned schema + build-time validation |
| F-08 | 524-line manual handoff | generated status report |
| F-09 | 40+ speculative engines | lightweight scope gate + playtest evidence |
| F-10 | 3-phase split only moved responsibilities; did not separate ownership | real responsibility boundaries |

---

# §3B AI CODING AGENT ANTI-PATTERNS

For each AP, define:
**(a) exact rule, (b) allowed exceptions, (c) enforcement layer + concrete tool.**

Custom AST checks are considered easy to evade. Known bypasses:
- `CACHE: Final = {}; CACHE["a"] = 1`
- `except Exception: log_and_continue(e)`
- `p = state.player; p.hp = 0`
- `assert bool(obj)`
- one fake `@given` test

Use §5 B0 priority.

## AP-01 — Type cheating: `Any`, `dict[str, Any]`

Rule:
- `Any` / `dict[str, Any]` ONLY at I/O boundaries:
  JSON deserialization, LLM parsing, template loading, IPC input.
- Boundary function MUST immediately convert data to typed DTO.
- Forbidden inside engines, contracts, events, and state models.

Tools:
- `mypy --strict`
- `disallow_any_explicit`
- per-module boundary exceptions
- Ruff `ANN401`
- boundary whitelist changes are GATED by PR review.

## AP-02 — Silent exception swallowing

Every `except` MUST:
1. re-raise; OR
2. convert to `DomainError` and raise; OR
3. log + return an explicit fallback AND mark `FactSheet.degraded`.

Tools:
- Ruff `E722`, `S110`, `S112`, `BLE001`
- engine-boundary decorator catches/records failures.
- replay hash divergence catches hidden “log and continue” behavior.

The decorator MUST define:
- signature
- exception handling
- logging
- `degraded` propagation:
  `FactSheet -> narration -> debug report`.

## AP-03 — Mock in domain tests

Rule:
- Domain engine tests MUST be pure state-in -> state/delta-out.
- `unittest.mock` / `pytest-mock` forbidden in `tests/engines/`.
- Allowed only in `tests/adapters/` for LLM/search/filesystem boundaries.

Tool:
- Ruff `TID251` / `banned-api`.
- No custom checker.

## AP-04 — Stub left behind and reported as complete

Rule:
- Actual implementations MUST NOT use `pass`, `...`, or meaningless `return None`.
- Allowed in `Protocol` / ABC declarations.
- Unimplemented behavior MUST raise:
  `NotImplementedError("<reason> — TODO-<ID>")`.

Structure:
- unregistered engines cannot run;
- registered incomplete engines fail replay immediately.

Tool:
- Ruff empty-body detection.
- TODO count may be a simple grep; no dedicated checker.

## AP-05 — Module-global mutable state

Important:
- `Final` prevents rebinding, NOT mutation.

Rule:
- module-scope mutable literals (`{}`, `[]`, `set()`) forbidden.
- allowed immutable values:
  tuple, frozenset, `MappingProxyType`, frozen dataclass, primitive constants.
- mutable state belongs in `WorldState` or injected `ServiceContext`.

Tools:
- Ruff `PLW0603`, `RUF012`, `B006`
- runtime protection = replay contamination test:
  1. same trace twice in one process;
  2. run in reversed order;
  3. hashes MUST match.

## AP-06 — Hidden nondeterminism

### Set iteration
- If output depends on `set`/`frozenset` iteration, use `sorted()`.
- Dict insertion order is stable, but a set-derived insertion order is not.
- CI uses fixed and randomized `PYTHONHASHSEED`.

### Float
Do NOT ban floats globally.

Rules:
1. Quantize BEFORE threshold comparison, branching, or sort-key use.
2. Persistent/hashable state uses integer fixed-point with declared scale.
3. Ban `sin/exp/log/pow` from authoritative state paths.
4. Use fixed lookup tables or integer approximations; generate tables at build time.
5. No `sum()` over unordered collections when order affects result.

### Clock
Game logic MUST NOT use:
`time.time`, `datetime.now`, `time.monotonic`.
Game time comes only from `WorldState` turn/minute model.

### Other nondeterminism
Control:
- `uuid4`
- environment reads
- filesystem iteration order
- thread scheduling

Tools:
- Ruff `TID251` banned APIs.
- No custom nondeterminism linter.
- Hash schema MUST reject float state fields.

## AP-07 — Delete logic under “refactor”

A refactor MUST preserve behavior.

Primary proof:
- golden replay state hash remains identical.
- Hash change = behavior change and requires separate commit + reason.

Secondary:
- test deletion requires user approval.
- record test-count trend; no custom checker.

## AP-08 — Mutating function inputs

Do NOT use AST `state.* =` detection; it is bypassable.

Rules:
1. Pipeline DTOs are frozen:
   `Intent`, `FactEvent`, `FactSheet`, `WorldEvent`, `EngineResult`, etc.
2. `WorldState` itself is NOT frozen; deep-copying every turn violates MIN-SPEC constraints.
3. Engines receive a recursive read-only view.
4. Child objects MUST also be wrapped.
5. Mappings use `MappingProxyType`.
6. Sequences use read-only views.
7. `__setattr__`, `__setitem__`, and mutating methods MUST fail immediately.
8. Cache wrappers to reduce allocation overhead.
9. Measure overhead on MIN-SPEC.
10. Release policy MUST choose:
    - keep proxy, OR
    - disable after CI proves safety.
11. Engines return deltas/events; only COMMIT mutates state.

The proxy also records reads. This solves AP-08 and supports C-04.

## AP-09 — Circular imports

Layer:
`domain -> contracts -> engines -> orchestration -> adapters -> app`

Rules:
- no reverse dependency;
- no same-layer cycles;
- type-only cycles may use `TYPE_CHECKING`.

Tool:
- `import-linter`.

## AP-10 + AP-11 — Fake tests / overfitted tests

Do NOT use:
- assert counters
- “Hypothesis exists” checks

Use mutation testing.

Rules:
- mutate engine code (`> -> >=`, constants, conditions, etc.);
- tests MUST kill meaningful mutants.
- scope: `src/engines/` only.
- frequency: weekly or phase completion, NOT every commit.
- choose numeric minimum mutation score per engine.
- report engines below threshold.
- use `mutmut` or `cosmic-ray`.
- each engine MUST state at least one invariant.
- Hypothesis is recommended, but its mere existence is NOT a CI requirement.

---

# §3C HARD CONSTRAINTS

## C-01 MIN-SPEC vs local RAG

Required search tiers:

| Tier | Rule |
|---|---|
| T0 | mandatory; no external process; SQLite FTS5 / BM25 / keyword + metadata filters; MIN-SPEC fully playable |
| T1 | optional; DEV-A; lightweight in-process ONNX int8 embeddings + hybrid reranking |

Requirements:
- T0↔T1 MUST be configuration-only.
- no external DB process / Docker in shipping path.
- quantify T1-off retrieval-quality degradation.
- embedding work is asynchronous and outside turn budget.
- T1 failure -> T0 fallback + `degraded`.

## C-02 BYOK free-tier quota

Current problem:
- Pass 0 + Pass 2 = up to 2 LLM calls/turn.
- RPM and RPD limits can break burst usage.
- README claims such as “1,500 free turns/day” must be recalculated from actual calls.
- evaluation can consume player quota if not isolated.

Required:
1. Pass 0 defaults to local Korean morphology/rule parsing, e.g. `kiwipiepy`.
2. LLM intent parsing is escalation-only and MUST have a frequency cap.
3. Token-bucket RPM limiter.
4. Daily RPD counter.
5. Exponential backoff.
6. 429 queueing.
7. Quota exhaustion = explicit wait/error; NEVER fake narration.
8. State the actual average calls/turn and recompute free turns/day.
9. Evaluation harness MUST have an offline deterministic mode.
10. LLM evaluation is explicit opt-in.

## C-03 Off-screen LOD vs determinism

Two corrections:
- LOD may vary with player location without breaking replay if LOD is a pure function of replayed state.
- Catch-up composition is possible if it replays the same deterministic tick sequence.

Failure cases:
- closed-form approximation such as `rate * elapsed_hours`;
- resolution changes based on interval length;
- path-dependent catch-up.

Three tiers:

| Tier | State | Guarantee |
|---|---|---|
| A / strict | persistent world state: settlement decline, factions, NPC intent, quest decay, food, temperature, resources | full catch-up composition law; property-test required |
| B / bounded divergence | encounters, rumors, crowd flow | exact equality not required; divergence bound + CORE invariants required |
| C / derived | visuals, presentation, caches | no replay/hash guarantee; recomputable |

Tier A requirement:
`catchup(t0→t2) == catchup(catchup(t0→t1), t1→t2)`

Also:
- every state field MUST declare A/B/C at schema level;
- hash `CORE`, exclude `DERIVED`;
- deleting/rebuilding DERIVED MUST preserve CORE consistency;
- implement strict tier using tick-indexed deterministic event queues or equivalent.

## C-04 Detect unused/unconsumed fields

Do NOT claim static AST analysis can safely discover all runtime reads.

Use three layers:

1. **Manifest set difference**
   - engine manifests declare `reads` / `writes`.
   - schema fields absent from every `reads` set = unconsumed.
   - fields changed without a declared writer = commit failure.
2. **Runtime recursive proxy**
   - records actual reads during replay.
   - compare declared vs actual.
3. **Replay coverage**
   - `coverage.py` over golden traces.
   - public engine methods with zero hits = practically unreachable.
   - replaces AST reachability audit.

Distinguish:
- undeclared read
- unused declaration
- unconsumed field
- unreachable method

## C-05 Windows process lifecycle

Primary:
- Windows Job Object
- `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`

IPC:
- Named Pipe
- no TCP-port/temp-file handshake

Required:
1. Job Object parent-death cleanup.
2. Named Pipe naming + collision handling.
3. heartbeat watchdog; define timeout.
4. Named Mutex single-instance guarantee + stale cleanup.
5. graceful shutdown protocol; no partial turn commit.
6. scenario matrix:
   - normal exit
   - Alt+F4
   - crash
   - Task Manager kill
   - Steam forced termination
7. power loss is excluded from CI; protect with atomic save:
   temp file + rename.
8. Linux `prctl(PR_SET_PDEATHSIG)` is optional only if Linux demo remains.

## C-06 Output token budget

Large blocks cause agents to omit implementation.

Use the 9-block protocol in §9.
NEVER merge blocks.
If a block is too large, split it further.

---

# §4 PART A — ENGINE ARCHITECTURE

Every A item MUST contain:
1. design
2. interface-level Python code
3. reason + rejected alternatives
4. mapped F/AP/C IDs

## A1 Turn pipeline / phase scheduler

Design an explicit phase sequence, e.g.:
`PRE_TICK -> INTENT -> VALIDATE -> RESOLVE -> REACT -> CASCADE -> POST_TICK -> COMMIT`

You choose final phases.

MUST:
- define phase invariants;
- topologically sort dependencies at boot;
- detect cycles at boot, not runtime;
- support early exit when action is rejected;
- make COMMIT the only state mutation point.

## A2 Engine plugin contract

One `Protocol`.

Required `CapabilityManifest`:
- `engine_id`
- `phases`
- `reads`
- `writes`
- `depends_on`
- `emits`
- `cost_class`

MUST:
- detect same-phase write conflicts at boot;
- compare manifest declarations with proxy reads/writes;
- choose explicit registry OR decorator discovery and justify;
- state how many existing files must change to add one engine; target 0 or 1.

## A3 Pass1 -> Pass2 contract

Replace 29 `Optional[str]` fields and generic dict payloads.

Fact unit MUST contain:
- source engine
- kind
- typed structured payload
- salience
- narration guidance
- `degraded`

Prompt assembly MUST be outside contract objects.

Define:
- renderer location;
- per-kind template registration;
- salience ordering;
- token-budget truncation;
- post-narration contradiction handling:
  choose LLM re-call, deterministic correction, or hybrid;
- location of Dynamic Focalization.

## A4 Event bus + delayed causality

Rules:
- engines MUST NOT directly call other engines;
- use events;
- scheduled/delayed events are first-class;
- example: quest ignored at turn 10 -> settlement falls at turn 40;
- bound cascade depth;
- prevent infinite loops;
- persist events in saves;
- replay events deterministically;
- NPC ecology and off-screen simulation run through this bus.

## A5 State model + responsibility split

Choose one:
- component-oriented
- ECS
- hierarchical model

Optimize for one-person maintenance.

MUST:
- replace 19 god data classes;
- encode `CORE` / `DERIVED`;
- encode C-03 A/B/C tier in schema;
- use recursive read-only proxy;
- return deltas;
- measure proxy overhead;
- preserve `traits`;
- choose delta-commit OR event sourcing;
- integrate the 6-level world hierarchy.

## A6 Determinism / seeds / replay

MUST define:
- one RNG service;
- sub-seed derivation, e.g.
  `hash(world_seed, turn_index, engine_id, call_index)`;
- all AP-06 controls;
- float quantization BEFORE comparisons;
- fixed-point hash representation;
- sorted sets;
- `CORE` only in authoritative hash;
- schema version policy.

Golden replay:
1. record trace;
2. replay;
3. compare state hashes.

Also:
- same-process twice;
- reversed execution order;
- hashes MUST remain equal.

Pass 2 is nondeterministic. Choose one:
- record Pass 1 only;
- freeze LLM responses as fixtures;
- hybrid.
Explain why.

Golden replay MUST be presented as the primary regression barrier and explain how it also catches AP-05, AP-07, AP-10, AP-11.

## A7 Intent parsing / Pass 0

Separate Korean natural-language input from simulation.

`Intent` schema:
- verb
- target
- tool
- modifiers
- ambiguity flag

Default:
- local morphology/rule parser.

LLM escalation:
- optional
- bounded frequency

Handle:
- particles
- endings
- synonyms
- ambiguous input
- clarify vs best-effort policy

Parser rules/dictionary MUST be content-extensible without code changes.

## A8 Search / memory / context budget

Implement T0/T1.

T0 alone = complete MIN-SPEC gameplay.

Define fixed token budget allocation among:
- RAG
- confirmed facts
- world lore
- NPC memory

Define:
- tier priorities
- compression/truncation
- episodic memory summarization
- relation between 5-level semantic memory and token budget.

## A9 Persistence / migration

Use:
- versioned schemas
- explicit forward migration chain

Explain why “optional fields with defaults” create debt.

Choose:
- JSON
- SQLite
- hybrid

MUST:
- load all historical save fixtures in CI;
- atomic save with temp file + rename;
- prevent partial turn commits.

## A10 Templates / data pipeline

5.4MB JSON MUST remain viable on MIN-SPEC.

Use:
- build-time JSON Schema/Pydantic validation;
- lazy loading / indexing / compiled artifacts as justified;
- adding 120 -> 200 continents MUST require no code change;
- convert `Any` to typed DTO at load boundary.

## A11 Time model / simulation LOD

Rules:
- unified variable-turn-duration model;
- real minutes;
- no real-world clock.

Off-screen:
- 120 continents / 304 regions / N settlements cannot all tick every turn.
- use distance/importance-based resolution.

MUST preserve Tier-A catch-up composition.
Define:
- tick-index event replay;
- Tier-B divergence bound;
- player-return catch-up;
- causal preservation at low resolution.

## A12 Brain <-> Body IPC

Brain MUST NOT know whether client is Unity or UE5.

Requirements:
- schema-first protocol;
- send state diffs, not full WorldState;
- one schema source;
- client code generation:
  - Unity -> C#
  - UE5 -> C++ / `USTRUCT`
- choose JSON Schema / Protobuf / FlatBuffers;
- only codegen backend changes by client;
- versioning + backward compatibility;
- Windows lifecycle controls from C-05;
- text-only and graphical modes share the same Brain.

Litmus test:
> No Brain code should reveal whether the renderer is Unity or UE5.

## A13 Observability / performance budget

Trace:
- engine time
- emitted events
- state writes

Do NOT hard-gate CI on wall-clock ms.

Hard gates:
- engine call count
- state write count
- event count
- allocation count

Soft trend:
- wall-clock ms
- memory MB

Measure real ms/MB on DEV-B and record results.

Define profiler hooks and bottleneck report.

## A14 LLM abstraction / resilience

Provider abstraction:
- Gemini
- Claude
- Ollama

Use structured output:
- JSON Schema
- function calling

Never parse free-form text and “repair” it as the primary contract.

Rate limiting:
- RPM token bucket
- daily RPD counter
- exponential backoff
- 429 queueing

Define:
- retries
- timeout
- fallback
- `degraded`

NEVER return fake-success narration.

Recalculate BYOK “free turns/day” from actual average calls/turn.

Evaluation:
- offline deterministic mode
- LLM evaluation opt-in

---

# §5 PART B — LEAN GOVERNANCE

## B0 Four enforcement layers

| Layer | Mechanism | Cost | Bypass risk |
|---|---|---:|---:|
| 1 | structural impossibility | 0 incremental | none |
| 2 | runtime enforcement/measurement | low-medium | very low |
| 3 | standard tools | very low | medium |
| 4 | custom checker | high + permanent maintenance | high |

Examples:
- L1: single COMMIT point, manifest registration
- L2: proxy, decorator, replay, coverage, mutation
- L3: Ruff, mypy, import-linter
- L4: only when L1–L3 cannot solve the problem

Rules:
- never move a solvable rule downward;
- custom checker count ≤3;
- explain why standard layers fail;
- never mislabel standard tools as AST checkers.

Provide one table mapping:
- AP-01..AP-11
- every v1 governance rule
to layers 1–4.

## B1 Rule residency

| Class | Location | Examples |
|---|---|---|
| ENFORCED | automated layers 1–4 | determinism, types, layers, manifests, coverage, mutation |
| GATED | PR checklist + human judgment | atomic commits, test deletion, Any whitelist, refactor hash proof |
| JUDGMENT | short prose rules | Anti-Yes-Man tone, Korean writing style, scope judgment |

All v1 rules MUST be classified, including:

- DoD: pytest, no fake results, >=1 test/feature, no test manipulation, no regression
- code hygiene: scratch isolation, full diff, no pycache, zero lint, no business logic in `app.py`, no UI-thread blocking
- duplication prevention: search before creation, template-key uniqueness, backward-compatible deserialization, UTF-8, unique filenames, caller audit before signature changes
- Two-Pass: deterministic Pass 1, narration-only Pass 2, memory truncation, network fallback, no fake success
- scope: no unauthorized rule-file edits, atomic commits, no unauthorized backlog deletion
- Handoff Truth: file path + test evidence, session-start marker validation, `UNVERIFIED` when evidence is unavailable
- Wiring: no incomplete live path, reachability, no write-only fields, search before new engine, >=1 integration test, capped unbounded lists, docs follow code
- mandatory `traits`
- 3-stage incremental integration
- 3 principles for external LLM role division

## B2 Generated progress report

Replace the manual 524-line handoff.

One code-generated report MUST include:
- registered engines + phases/dependencies
- manifest vs actual access mismatches
- replay result
- zero-hit engine methods
- latest mutation scores + below-threshold engines
- determinism-counter trends
- wall-clock trends
- backlog evidence:
  file exists + tests pass + coverage hit

The generator MUST mostly aggregate existing tool output:
`pytest`, `coverage`, `mutmut`, `import-linter`.

Do NOT create another god system.

Define:
- generation command
- output path
- CI `--check` drift detection
- exact human-written section size; ideally one paragraph: “next work intent”
- session handoff reading order + token budget.

## B3 CI gates — exactly 11 commit gates

Every gate MUST state:
- tool type
- what it checks
- failure condition
- time budget

### Standard tools
1. Ruff:
   `E722`, `S110`, `S112`, `BLE001`, `TID251`, `PLW0603`, `RUF012`, `B006`, `ANN401`
2. `mypy --strict`
3. `import-linter`
4. `pytest`

### Harness-based
5. Golden replay hash equality
6. Global-state contamination: two consecutive + reversed-order replay
7. Replay coverage via `coverage.py`; zero-hit public engine methods
8. Deterministic performance counters:
   engine calls / state writes / events / allocations
9. Save migration: all historical fixtures

### Custom (≤3)
10. Engine manifest validation:
    declared `reads/writes` vs proxy-observed access.
    Must justify why standard tools cannot do this.
11. Template schema validation:
    5.4MB JSON integrity using Pydantic/JSON Schema; thin wrapper only.

### Async / scheduled, NOT commit gates
- mutation testing with `mutmut` or `cosmic-ray`
  - `src/engines/` only
  - weekly or phase completion
- report drift `--check`

Platform:
- Windows = mandatory gate for development/deployment, including encoding, paths, Named Pipe.
- Linux = optional only if text-only web demo remains.
- fixed/random `PYTHONHASHSEED` replay is part of Gate 5.

Also define:
- total CI gate time
- fast local pre-commit subset:
  Ruff + one core replay
  - target: tens of seconds

## B4 Scope gate

Do not build another checker. Use PR checklist.

New engine requires:
1. real live-turn trigger exists;
2. existing engine extension cannot solve the need;
3. playtest evidence exists.

Formalize:
> Reject speculative “desk-theory” engines; implement systems whose absence was demonstrated by actual playtesting.

Separate:
- cheap content/template expansion
from
- expensive new system/engine creation.

## B5 Agent session rules

Define:
- session scope cap
- atomic commit requirement
- mandatory baseline at session start
- session-end report format

User approval MUST be required for:
- governance/rule changes
- backlog deletion
- test deletion
- destructive schema changes
- adding an `Any` whitelist entry
- adding a custom checker

Completion fraud MUST be blocked by 3-way evidence:
`file exists + tests pass + coverage hit`.

A “refactor” commit MUST attach golden-hash behavior-preservation evidence.

---

# §6 IMPLEMENTATION ROADMAP — LEAN PHASE 0

## 6.1 Phase 0 — ONLY these four items

Goal:
> **Walking Skeleton:** one complete turn from input to commit.

1. Walking Skeleton:
   input -> phase scheduler -> 1–2 dummy engines -> FactSheet ->
   text output without LLM -> COMMIT.
2. Ruff + `mypy --strict` configuration only.
3. Golden replay harness:
   record -> replay -> hash compare.
4. Recursive read-only proxy.

Why replay MUST be Phase 0:
- it is architecture, not merely governance;
- without replay, A6 determinism cannot be verified;
- determinism is the central load-bearing property;
- low construction cost;
- also protects AP-05, AP-07, AP-10, AP-11 and supports C-04.

Explicitly NOT Phase 0:
- manifest validator
- mutation testing
- report generator
- performance-counter gate
- save migration
- template schema validator

These start in Phase 1+.

## 6.2 Later phases

Order phases by dependency topology.

For each phase provide:
- deliverables
- measurable completion criteria
- why later phases depend on it
- governance tools introduced in that phase
- reusable vs discarded v1 assets

Do NOT front-load every governance tool.

---

# §7 RISKS / TRADE-OFFS

Explicitly provide:

1. Three places where the architecture becomes expensive:
   - performance
   - complexity
   - development speed
2. Quantified recursive-proxy overhead.
3. Release proxy decision:
   - enabled or disabled, with evidence.
4. Overengineering threshold for one developer.
5. Explicit “do not build this yet” list.
6. Total governance construction effort in person-days.
7. Cost-vs-loss-prevention argument using §0.3(2).
8. Anything clearly slower than v1 and why the trade is justified.
9. Highest-risk design decision + escape route.

---

# §8 DESIGN DISCIPLINE

1. Every major decision: 2–3 lines of rationale + rejected alternative.
2. Quantify:
   - MIN-SPEC turn budget in ms
   - memory in MB
   - thresholds as numbers
3. Name industry-standard patterns and state project-specific deviations.
4. Keep one-person + AI-agent maintenance complexity below the defined ceiling.
5. Do NOT submit if any F-01..F-10, AP-01..AP-11, or C-01..C-06 remains unresolved.
6. Do NOT violate:
   - custom checkers ≤3
   - Phase 0 = exactly four items.

---

# §9 OUTPUT PROTOCOL — 9 BLOCKS

```text
BLOCK 1:
§0 summary
+ architecture overview
+ 5-line key decisions
+ F-01..F-10 / AP-01..AP-11 / C-01..C-06 mapping
+ 4-layer enforcement table
+ confirm custom checkers <=3

BLOCK 2:
PART A / A1-A3

BLOCK 3:
PART A / A4-A6

BLOCK 4:
PART A / A7-A9

BLOCK 5:
PART A / A10-A12

BLOCK 6:
PART A / A13-A14

BLOCK 7:
PART B / B0-B2

BLOCK 8:
PART B / B3-B5

BLOCK 9:
§6 roadmap
+ §7 risks
+ §10 self-check
```

At the end of each block:
`--- BLOCK n/9 END. Enter "continue" for the next block. ---`

Then STOP.

Rules:
- never skip or merge blocks;
- if a block is too large, split it into `BLOCK 3a / 3b` and state why;
- never omit code by using placeholders or “same as above”.

---

# §10 PRE-SUBMISSION SELF-CHECK — 34 ITEMS

Return each item as `✅/❌ + one-line evidence`.
If any item is ❌, fix it before submission.

## Lean rules — 1–5

1. Custom checker count ≤3; state the number.
2. Every custom checker proves why layers 1–3 cannot solve it.
3. Phase 0 contains exactly four items:
   skeleton / linter config / replay / proxy.
4. All tools are honestly labeled; mypy/coverage/mutmut are not called AST checkers.
5. Total governance effort is estimated in person-days and justified by loss prevented.

## Architecture — 6–18

6. Existing-file changes for one new engine are explicitly numbered and ≤1.
7. Explain structurally why the 1,294-line god function cannot return.
8. Pass1→Pass2 contract does not change when an engine is added.
9. Human-managed execution ordering is removed.
10. Write conflicts and dependency cycles fail at boot.
11. Golden replay is the primary regression barrier and also protects AP-05/07/10/11.
12. Pass 2 LLM replay behavior is explicitly decided.
13. Unconsumed fields/reachability use declaration + proxy + coverage, not “static magic”.
14. Delayed causality is first-class and persisted.
15. C-03 Tier A full composition law is property-tested; not reduced to simple accumulation.
16. `CORE`/`DERIVED` hash layers and A/B/C tiers are schema-level.
17. MIN-SPEC turn budget is numeric ms; memory budget is numeric MB.
18. Save migration uses versioned chain + atomic write.

## Hard constraints — 19–24

19. T0 alone supports complete MIN-SPEC gameplay; zero external-process dependency.
20. External DB/Docker dependency is removed from shipping path.
21. Pass 0 works locally without an LLM by default.
22. RPM token bucket + RPD accounting are enforced; free turns/day are honestly recalculated.
23. Evaluation does not consume player quota.
24. Windows Job Object + Named Pipe lifecycle and shutdown scenario matrix are defined.

## Anti-patterns — 25–31

25. `Final` is not treated as immutability; AP-05 uses replay contamination testing.
26. Float quantization occurs BEFORE comparisons; transcendental functions are banned from authoritative state paths.
27. Exception defense uses linter + engine-boundary decorator + `degraded`.
28. AST `state.* =` detection is removed; recursive proxy wraps child objects and sequences.
29. Proxy overhead is measured and release policy is explicit.
30. Assert counters/Hypothesis-existence checks are replaced by mutation testing; cost is bounded to engines + weekly/phase execution.
31. `TID251` banned-api replaces a custom nondeterminism linter.

## Governance — 32–34

32. All v1 rules + AP rules are assigned to the four layers; layer 4 count ≤3.
33. CI performance gates use deterministic counters, not wall-clock time.
34. Progress reports aggregate existing tool output; human-written area is explicitly bounded.

---

# EXECUTION COMMAND

Start now with **BLOCK 1**.
