# Quilltale TRPG Engine - AI Developer & GM Rules

# SYSTEM_RULES:QUILLTALE
[CRITICAL] Strict adherence required. Failure to comply = immediate roll-back.

<DoD_Gate>
1. RUN pytest: Execute `pytest tests/` in bash before completion. Report stdout/stderr verbatim. NO faked results.
2. RUN eval: If modifying `state.py` or `src/world/*_engine.py`, execute `eval_runner.py --no-judge` & report `invalid_transition_rate`.
3. TEST req: Write >=1 pytest case for any new feature.
4. NO test-gaming: Do not edit test assertions/skip tests just to pass. Fix logic instead.
5. NO REGRESSION: Record pytest pass/fail count before starting (BASELINE). If fail count increases after changes, the commit is invalid — fix root cause and retry. Never proceed with a regression.
</DoD_Gate>

<Prompt_Rules>
1. NO regex/patch/temp scripts in `scratch/` for `src/agents/prompts.py` or any module.
2. USE file edit tools directly. Do not omit code (no `...` or `/* same */`). Show full diff.
3. REPO hygiene: `scratch/` is local-only and must NEVER be tracked in git. Unit tests must use `tmp_path` and never leak dummy JSON into production directories (`data/legacy/`, `data/saves/`).
4. NO ARTIFACT COMMIT: __pycache__, *.pyc, and 0-byte files must not be committed. Check `git status` before commit.
</Prompt_Rules>

<No_Dup_Compatibility>
1. SEARCH first: Grep existing modules before creating new class/engine/template.
2. JSON check: Verify `data/templates/*.json` and `data/legacy/*.json` key overlaps before adding.
3. SAVE_LOAD: Ensure `WorldState` modifications include defaults/optional fields to prevent deserialization break with old JSON saves.
4. ENCODING: Always read/write Korean text files as UTF-8 explicit. No implicit encoding.
5. UNIQUE naming: Do not reuse identical module/file names across different packages (e.g. `profiler.py`). Use descriptive, disambiguated filenames (`combat_profiler.py` vs `engine/profiler.py`).
6. CALLER CHECK: Before changing any function/class signature, grep all callers first. Confirm no breakage before editing.
</No_Dup_Compatibility>

<Two_Pass_Resource>
1. PASS 1 (Python): 100% deterministic logic (dice, combat, status, quest). No math/rules in LLM prompt.
2. PASS 2 (LLM): Narrative rendering only.
3. MEMORY limit: NPCs episodic memory must have truncation/summarization to avoid token overflow.
4. FALLBACK: Network/image APIs must have fallback paths to prevent app crash on timeout/error.
5. NO silent fallback masking: On API/network fail, log the failure. Never return fake success narration.
</Two_Pass_Resource>

<UI_Architecture>
1. GRADIO isolation: UI code (`app.py`) must only handle I/O and rendering. Zero business logic.
2. ASYNC: Do not block UI thread with heavy processing/external API calls.
</UI_Architecture>

<Scope_Commit>
1. AGENTS.md PROPOSAL & PERMISSION GATE: `AGENTS.md` (rules, backlog, hw)는 임의 무단 편집이 엄격히 금지된다. 단, 새로운 영구 개발 규칙 추가나 규정 개정이 필요할 때는 '침묵하거나 언급을 회피하지 말고, 반드시 유저에게 필요 사유를 먼저 구체적으로 설명하고 수정 허락을 질문'해야 한다. 유저의 명시적 승인을 받은 경우에만 편집이 허용된다.
2. ATOMIC commit: 1 session = 1 task/requirement only. No mixed refactoring.
</Scope_Commit>

<UI_Localization>
1. 100% natural, idiomatic Korean for all user-facing text (narration, NPC dialogue, options).
2. ISOLATE system/debug text (snake_case, variables) from user view.
</UI_Localization>

<Static_Analysis_Gate>
1. Before commit, run ruff (or pyflakes) on src/. Zero syntax errors, unused vars, or undefined names allowed.
</Static_Analysis_Gate>

<Handoff_Truth_Gate>
1. When marking a backlog item [x], record the actual file path and passing test name in SESSION_HANDOFF.md as proof. No unverified completions.
2. At session start, do not trust handoff [ ]/[x] marks as-is — verify via ls/grep against actual files before scoping work.
</Handoff_Truth_Gate>

<Unverifiable_Scope_Gate>
1. If a change touches Qdrant/Docker/external APIs untestable in the current session, mark it "⚪ UNVERIFIED — needs real-env check" in the report. Never claim verification without running it.
</Unverifiable_Scope_Gate>

<Report_Format>
Return exact markdown format at session end:
### 1. Modified Files
(paths)
### 2. Pytest Results
(verbatim bash log, pass/fail counts)
### 3. Added/Modified Tests
(function names & purpose)
### 4. Doc Alignment Check
(status) + IF conflict found: propose doc update, do not just report and ignore.
</Report_Format>

---

## 1. Core Mission & Philosophy
- **Anti-Yes-Man Rule:** Do not be an agreeable 'yes-man'. The player is a grounded mortal character. Absurd, power-scaling, or impossible actions must realistically fail.
- **Deterministic Truth (WorldState):** The JSON `WorldState` is the single source of truth. LLM narration must never contradict recorded facts, stats, locations, or items.
- **100% Korean Player-Facing UI:** All text shown to the player (narration, NPC dialogue, item names, stats, location names, UI status) must be in natural, atmospheric Korean. Internal codes/data keys can be in English.

## 2. Memory & RAG Architecture
- **Episodic & Long-term Memory:** Use a hybrid architecture of JSON WorldState + Local RAG (Qdrant & Jina Embeddings).
- **5-Scale Significance:** Memory entries use a 1-5 scale. Level 4-5 memories represent world-shaping events and are anchored for permanent retention.
- **Reputation & Rumors:** Global world facts and player reputation affect NPC initial disposition across locations.

## 3. Strict Dice & Stat Rules
- Combat and skill checks are resolved through deterministic Python mechanics (d20 + stat modifier vs DC). LLMs describe the narrative outcome based on the deterministic roll result.

## 4. Magic Language & Skill Book Rules
- **Korean Pronunciation for Ancient Words (고대어 한글 발음 표기 원칙):** All ancient magic vocabulary words must be written in Korean phonetic transcriptions with their conceptual roles (e.g. `바르(발화/열에너지)`, `카르(강제/물리운동)`, `이그니스(화염)`), NEVER in raw Latin/English alphabets (`barre`, `motus`, etc.).
- **Skill Book UI & No-Spoiler Formula:** The skill book header must maintain the crisp 2-tier white/high-contrast layout. Magic combination tips must only show the abstract formula `[원소] + [형태] + [기동]` without concrete spoiler examples so players can discover spell combinations themselves.

## 5. Storytelling & World Reactivity Rules
- **No Invisible Walls (투명 벽 금지):** 플레이어의 이동과 선택을 강제로 막지 않는다. 무조건적인 지역 체류 강요를 금지한다.
- **Strict Causality & Butterfly Effect (철저한 인과효과와 나비효과):** 플레이어가 퀘스트를 무시하거나 다른 지역으로 떠나면, 시간의 흐름에 따라 그 방치된 사건은 가차 없이 악화된다(마을 파괴, NPC 사망 등). 선택과 방관에는 반드시 현실적인 대가가 따른다.
- **NPC Independence (NPC 독자적 생태계):** NPC는 퀘스트 자판기가 아니다. 플레이어가 안 볼 때도 각자의 욕망과 타임라인에 따라 은밀하게 움직이며, 때로는 플레이어의 뒤통수를 치거나 목표와 충돌한다.
- **Dilemmas & Flawed Victories (딜레마와 불완전한 승리):** 모두가 행복한 완벽한 해피엔딩을 지양한다. 정답 없는 윤리적 딜레마를 강요하고, 무언가를 얻으면 다른 것을 잃는 씁쓸한 여운을 남긴다.
- **Micro & Macro Blend (미시와 거시의 교차):** 거대한 멸망의 위협은 배경(원경)으로 깔아두고, 당장의 목표는 '동생 찾기', '가보 회수' 등 지극히 개인적이고 밀도 높은 사건에 집중시킨 후 점진적으로 스케일을 넓혀간다.
- **Resource & Physical Constraints:** 장거리 이동 시 피로도, 식량 소모, 날씨 변화 등 물리적 제약을 엄격히 적용한다. 빠른 이동을 지양하고 생존의 무게를 부여한다.
- **Failing Forward (의미 있는 실패):** 주사위 판정 실패 시 "아무 일도 없었다"로 넘기지 않는다. 단순 실패가 아닌 소음, 시간 낭비, 부분적 성공 등 개연성 있는 피해로 묘사한다.
- **NPC Consistency:** NPC는 일관된 성격과 태도를 유지해야 하며, 유저에게 무조건 호의를 베풀거나 정보 자판기처럼 굴지 않는다.
- **Dynamic Focalization (상황적 시야 제한 및 오감 극대화):** 내러티브 묘사는 플레이어의 상태를 반영한다. 1. 전투/도주는 생존 직결 요소와 전술적 지형지물을 빠르고 날카롭게 묘사. 2. 잠입/긴장 상태는 오감(청각, 후각, 촉각)을 극도로 예민하게 미친 디테일로 묘사. 3. 여유로운 탐색은 넓고 세밀하게 묘사. 

## 6. Developer Operational Rules (세션 고정 개발 규칙)
- **말투 규칙:** 유저에게 출력할 때는 토큰 절약을 위해 '우가' 추임새를 뺀 원시인 말투로 고정한다.
- **핸드오프 규칙:** 핸드오프 갱신 시 고정 규칙, 하드웨어 스펙, 백로그를 보존하고 세부 사항만 갱신한다.
- **환경 분리:** '집/노트북'은 콘텐츠+시스템, '똥컴/학원'은 순수 시스템 연산/코드만 다룬다.
- **백로그 삭제 금지:** 유저의 명시적 허락 없이 백로그를 임의 삭제하지 않는다.
- **중복 방지 및 기존 코드 우선 확인 (필수):** 추가할 요소(클래스, 엔진, 템플릿, 기능)를 유저에게 제안하거나 백로그에 올릴 때, 이미 다른 파일에 관련 내용이나 유사 코드가 있는지 코드베이스를 철저히 사전 검색·확인한 후, 중복 신설 대신 기존 코드 확장/통합 여부를 먼저 유저에게 물어보고 보고한다.
- **클래스 작성 시 요약 특성(traits) 의무 탑재:** 월드/지리/정치/시설/개체 등 게임 내 주요 클래스 데이터 모델을 신설하거나 확장할 때, 플레이어 UI 요약, AI(GM) 서술 앵커링, 돌발 이벤트 판정에 사용될 `traits: List[str] = field(default_factory=list)`(요약 특성 태그) 필드를 무조건 기본 탑재한다.
- **제안/질의 시 구체적 설명 의무 탑재:** 유저에게 무언가를 제안하거나 물어볼 때 모호하게 묻지 말고, 시스템/게임플레이/코드상에서 구체적으로 무엇인지, 왜 필요한지 명확하고 짧은 설명을 반드시 덧붙여서 보고한다.
- **외부 AI(GPT/Claude) 연동 3원칙:** 1) 해야 할 작업은 외부 LLM에 즉시 입력 가능한 구체적 실행 프롬프트 형태로 제공, 2) 내부 연산/시스템 코드는 완성형이 아닌 명확한 인터페이스/뼈대 구조만 제공, 3) 세부 데이터 계산 및 방대한 콘텐츠 생성은 외부 LLM이 수행하도록 분담한다.
- **계단식 점진 통합 원칙 (Incremental Integration Gate):** 신규 엔진 및 시스템 개발 시 일괄 결합(빅뱅 통합)으로 인한 의존성 폭발 및 디버깅 지옥을 방지하기 위해 다음 3단계를 의무 준수한다:
  1. 1단계 (독립 완성 & 단위 테스트): 신규 엔진을 독립 모듈로 구현하고, 해당 엔진의 전용 단위 테스트(`pytest >= 1개`)를 100% 통과시킨다.
  2. 2단계 (팩트시트 슬롯 연결): `TwoPassEngine`(Pass 1) 또는 `GameMasterAgent`에 해당 엔진의 결과를 수신할 슬롯(메서드/필드)을 1:1로 안전하게 연결한다.
  3. 3단계 (전체 회귀 검증): 기존 전체 테스트(BASELINE 508개 이상)를 실행하여 단 1건의 결함/회귀도 발생하지 않음을 검증한 후 다음 백로그로 전진한다.

## 7. Wiring & Integration Rules
1. No feature is "done" until called from the live turn path (`TwoPassEngine.compute_pass1`/`sanitize_pass2_result` or `GameMasterAgent.process_turn`), same session it's written. A public method called only from its own test file = incomplete.
2. Reachability check is part of Definition of Done. Before marking done: confirm the new code is statically reachable from `app.py` and `src/agents/game_master.py`. Quick check: `grep -rn "<fn>" --include=*.py . | grep -v tests/` — no hits outside its own file = unwired.
3. No write-only fields. Any new field on NPC/Player must have >=1 deterministic reader. If no reader yet, defer the field or mark `# TODO: unconsumed field`.
4. Search before creating a new engine file. If an existing module covers the same responsibility, extend it — don't duplicate (e.g. check `save_load_manager.py` vs `persistence.py` pattern).
5. Every new engine needs >=1 integration test through `GameMasterAgent.process_turn()` or `TwoPassEngine.compute_pass1()`, not just isolated unit tests.
6. Any list that only grows (`npc.memories`, `off_screen_logs`, `physical_traces`) needs an explicit cap/decay/pruning policy, or a comment justifying unbounded growth.
7. Docs follow code, not vice versa. Before writing "implemented" in SESSION_HANDOFF.md / MASTER_GAME_ARCHITECTURE.md, grep-verify the named class/function/constant exists. If not: label "designed, not implemented."
8. Freeze new engine-file creation until the reachability audit (see Phase A) is clean.

## 8. Explicit Scope Gate
- TTS, 3D modeling, sound/BGM production, and character illustration/image generation are deliberately deferred to the final project phase. Until core simulation logic (NPC cognition, physics, quests) is wired and content-stable, do not scaffold code or asset pipelines in this area — even if it seems like a natural next suggestion mid-task.

