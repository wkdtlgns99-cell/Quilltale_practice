# Quilltale 프로젝트 세션 인수인계서 (Session Handoff)

> **규칙 및 거버넌스 (Single Source of Truth)**: 모든 개발·시스템·말투 규칙은 [AGENTS.md](file:///c:/Quilltale/AGENTS.md)를 유일한 단일 출처로 참조한다.
> **과거 세션 & 완료 백로그 아카이브**: 상세 완료 내역 및 과거 세션 기록은 [docs/archive/SESSION_LOG_2026-09.md](file:///c:/Quilltale/docs/archive/SESSION_LOG_2026-09.md) 참조.

---

## 1. 프로젝트 기본 정보 & 환경 스펙
- **엔진명**: Quilltale TRPG Engine
- **개발 언어 및 환경**: Python 3.13 / Windows 11
- **핵심 아키텍처**: 100% 결정론적 연산 (Python Engine) + 로컬 RAG (Qdrant + Jina BGE-M3 1024-dim) + Two-Pass LLM 검증기 (Gemini API)
- **하드웨어 스펙**:
  - **집/노트북**: AMD Ryzen 7 8845HS / 32GB RAM / RTX 4060 Laptop (8GB VRAM) — SD 1.5 LoRA, bge-m3, TTS, 경량 LLM 로컬 가능
  - **학원/똥컴**: 인텔 4코어 구형 사무용 CPU / 8GB RAM / 내장 그래픽 — Gemini API 및 순수 파이썬 내부 연산/코드 작업 집중

---

## 2. [해야 할 일(Backlog)]
상세 엔진 분류 및 도달성 상태는 [TRIAGE.md](file:///c:/Quilltale/TRIAGE.md) 및 [CHANGES_AUDIT.md](file:///c:/Quilltale/CHANGES_AUDIT.md) 단일 출처 참조.

### [🏛️ 시스템 결함 수정 & 6계층 인프라 실전 결합 — 2026-09-15 분석 기반]

#### [P0-0 — 2026-09-15 교차 검증 기반 0순위 긴급 과제 (Backlog 0순위)]
- [x] **🔥 [P0-0-1] `src/llm/claude.py` 퇴역 모델 교체 및 다중 모델 폴백 체인 구축**:
  - **수정**: 퇴역된 `claude-3-5-sonnet-latest` 제거하고 최신 활성 모델 `claude-sonnet-4-6`을 기본값으로 지정. `ANTHROPIC_MODEL` 환경변수 우선 적용 및 `candidate_models` 순차 폴백 체인(`claude-sonnet-4-6` -> `claude-3-7-sonnet-20250219` -> `claude-3-5-sonnet-20241022` -> `claude-3-5-haiku-20241022`) 구축. 404/not_found/retired/overloaded/429 발생 시 즉시 다음 후보 모델로 자동 전환.
  - **검증 파일/테스트**: `src/llm/claude.py` | `tests/test_p0_p2_fixes.py::test_claude_llm_without_api_key_no_crash`, `test_claude_llm_model_env_override`, `test_claude_llm_fallback_chain_on_error` (통과), `pytest tests/` 608 passed | commit `3af42b3`
- [x] **🔥 [P0-0-2] `src/world/two_pass_engine.py` 무효 행동 선행 변이 차단 (QT-F01)**:
  - **수정**: `ActionValidator.pre_validate_action()`을 `compute_pass1()` 최상단(스텝 0)으로 이동. `is_valid=False` 시 상태이상 틱, 환경 피해, 쿨다운 감소, 월드 시뮬레이션 일체 실행 없이 즉시 반환하여 0-변이 보장. 기존 버그 동작(무효 행동 시 선행 틱으로 쿨다운 감소)을 전제로 하던 `tests/test_mana_burn_wiring.py:54`의 어설션을 0-변이(2턴 유지)로 사용자 승인 하에 정정.
  - **검증 파일/테스트**: `src/world/two_pass_engine.py`, `tests/test_mana_burn_wiring.py` | `tests/test_p0_p2_fixes.py::test_invalid_action_zero_mutation_guaranteed` (통과), `eval_runner.py --no-judge` (invalid_transition_rate: 0.0%), `pytest tests/` 609 passed | commit `7029b60`
- [x] **🚨 [P0-0-3] `src/world/state.py` 토큰 폭발 방지 world_facts 프롬프트 슬라이싱 & 원본 리스트 상한 (QT-F03)**:
  - **수정**: `to_context_summary()`에서 `world_facts[-10:]` 슬라이싱 적용하여 프롬프트 토큰 폭발 원천 방지. `advance_world_simulation()` 및 `apply_action_effects()`에서 `npc.off_screen_logs` 10개 캡, `location.physical_traces` 10개 캡 및 15턴 감쇄 자동 소멸 적용. `two_pass_engine.py:2355` off_screen_logs 캡 30->10 하향. `src/world/persistence.py`에 `turn_history_archive` 테이블 및 `archive_turns()`, `get_full_history()` 구현. `WorldState.append_history()`를 통해 50턴 초과 시 SQLite로 자동 이관하고 메모리 50턴 유지. `SaveMigrationEngine.migrate()`를 세이브 로드 시점(`WorldState.from_dict()`)과 결합하여 구버전 세이브의 비대 리스트 트리밍 및 초과 턴 아카이빙 진입점으로 실전 재활용.
  - **검증 파일/테스트**: `src/world/state.py`, `src/world/two_pass_engine.py`, `src/world/persistence.py`, `src/persistence/migration.py`, `src/agents/game_master.py` | `tests/test_p0_p2_fixes.py::test_world_facts_summary_sliced`, `test_physical_traces_decay_and_cap`, `test_history_50_turn_cap_and_sqlite_archive`, `test_save_migration_list_trimming_and_archive` (통과), `eval_runner.py --no-judge` (invalid_transition_rate: 0.0%), `pytest tests/` 613 passed | commit `3338ed4`
- [x] **🚨 [P0-0-4] 보조 LLM JSON 출력 파싱 시 raw `json.loads`의 `JSONRepairEngine` 통일 (QT-F04)**:
  - **수정**: `src/llm/resilience.py`에 `JSONRepairEngine.repair_json(raw_text)` 범용 정적 메서드 추가(마크다운 코드펜스, outer JSON 추출, trailing comma, unescaped 줄바꿈 복구). `game_master.py:643`(세계 뉴스), `chronicle.py:105`(연대기), `generator.py:850`(동적 지역)의 raw `json.loads`를 `repair_json`으로 전면 교체.
  - **검증 파일/테스트**: `src/llm/resilience.py`, `src/agents/game_master.py`, `src/world/chronicle.py`, `src/world/generator.py` | `tests/test_p0_p2_fixes.py::test_json_repair_engine_auxiliary_repair` (통과), `pytest tests/` 605 passed | commit `7cc4b8d`
- [x] **🔧 [P0-0-5] 8개 파일 UTF-8 BOM (`\ufeff`) 제거 및 정적 분석 정상화 (QT-F05)**:
  - **수정**: 8개 파일 BOM 제거. `reachability_audit.py`를 `utf-8-sig` 인코딩 + AST `ast.Call` 노드 기반 내부 호출 탐지 방식으로 전면 수정 (기존 `if f != w_resolved` 오판 버그 근본 수정).
  - **결과**: `two_pass_engine.py` never-called 6→0 (campsite/stealth/harvest/eavesdrop 4종 `called-from-live-path` 정상 분류). 전체 never-called 84→31. `event_perspective.py`/`scenario_manager.py` 0메서드→정상 집계.
  - **검증 파일/테스트**: `scripts/reachability_audit.py`, 8개 파일 | BOM 0건 확인, AST 전체 파싱 통과, `pytest tests/` 604 passed | commit `ae32096`
- [x] **🔧 [P0-0-6] 문서-코드 팩트 정정 및 동기화 (QT-F07)**:
  - **수정**: `scripts/reachability_audit.py` 실행으로 `CHANGES_AUDIT.md` 최신화 (미도달 3/64개 모듈: `combat_time_track_engine.py`, `merchant_barter_engine.py`, `siege_engine.py` 정확 반영). `TRIAGE.md`의 오래된 Phase C/D 보류 목록을 2026-09-16 기준 실제 배선 상태(Wired Active 12종)로 전면 정정. `README.md` 테스트 합격 수치(544 → 615 passed, 무효 전이율 0.0%) 최신화.
  - **검증 파일/테스트**: `CHANGES_AUDIT.md`, `TRIAGE.md`, `README.md`, `SESSION_HANDOFF.md` | `reachability_audit.py` 실행 완료, `pytest tests/` 615 passed | commit 대기
- [x] **🔧 [P0-0-7] LLM 쿼터 고갈 시 영문 예외 문자열 서사 유출 방어 (QT-F08)**:
  - **수정**: `game_master.py`의 `process_turn()` 예외 블록에서 `repair_and_parse(str(e))` 호출 완전 제거 및 한국어 서사 폴백 딕셔너리 직접 반환. `resilience.py`의 `JSONRepairEngine`에 `is_technical_error()` 정적 메서드를 구축하여 JSON 파싱 실패/폴백 시 영문 기술적 예외(429, exhausted, traceback 등)가 서사로 유출되는 것을 2중 원천 차단.
  - **검증 파일/테스트**: `src/agents/game_master.py`, `src/llm/resilience.py` | `tests/test_p0_p2_fixes.py::test_llm_quota_exhausted_fallback_korean`, `tests/test_p0_p2_fixes.py::test_game_master_process_turn_llm_exception_safe_korean_narration` (통과), `pytest tests/` 607 passed | commit `33cfd11`
- [x] **🔧 [P0-0-8] 잔여 결함 디테일 보강 (P0-1, P2-7)**:
  - **수정**: `src/agents/player_bot.py`의 미사용 죽은 `Item` import 정리 및 typing 정리. `src/world/attack_physics_engine.py`의 `evaluate_attack_physics()` 및 `src/world/npc_skill_engine.py:168`에 `allow_overdraw=True` 전달 진입점 연결(강궁/저격/과인장 스킬 또는 명시적 플래그 시 최대 1.2x 오버드로우 및 서사 반영). 미사용 import 정리.
  - **검증 파일/테스트**: `src/agents/player_bot.py`, `src/world/attack_physics_engine.py`, `src/world/npc_skill_engine.py` | `tests/test_p0_p2_fixes.py::test_player_bot_no_dead_item_import`, `tests/test_p0_p2_fixes.py::test_npc_skill_engine_overdraw_wiring` (통과), `eval_runner.py --no-judge` (invalid_transition_rate: 0.0%), `pytest tests/` 615 passed | commit `aa51314`

#### [P0 — CONFIRMED CRASH BUGS (최우선 긴급 수정 — 1차 완료)]
- [x] **🔥 [P0-1] `src/agents/player_bot.py:137` `Item` import 누락으로 인한 NameError 크래시 해결**:
  - **수정**: `i in state.items` 검사 리팩터링으로 더미 Item 생성 제거 및 NameError 해결 (미사용 Item import는 P0-0-8에서 청소 예정).
  - **검증 파일/테스트**: `src/agents/player_bot.py` | `tests/test_p0_p2_fixes.py::test_player_bot_low_hp_with_potion_no_name_error` (통과)
- [x] **🔥 [P0-2] `src/llm/claude.py` 퇴역 모델 교체, KeyError 방어 및 3회 재시도 구축**:
  - **수정**: `ANTHROPIC_MODEL` 환경변수 우선 적용, 키 부재 시 KeyError 방어 및 3회 지수 백오프 구축. (단, 하드코딩된 `claude-3-5-sonnet-latest`의 2026-02-19 퇴역으로 P0-0-1에서 최신 활성 모델 교체 및 다중 모델 폴백 재작업 등록).
  - **검증 파일/테스트**: `src/llm/claude.py` | `tests/test_p0_p2_fixes.py::test_claude_llm_without_api_key_no_crash` (통과)
- [x] **🔥 [P0-3] `app.py` `take_action()` 내 `world_state` 파싱 실패 시 `None` 유입 크래시 방어**:
  - **수정**: `state is None` 가드 단락 추가 및 안내 메시지와 기존 뷰 안전 반환(AttributeError 방어).
  - **검증 파일/테스트**: `app.py` | `tests/test_p0_p2_fixes.py::test_app_take_action_none_state_guarded` (통과)

#### [P1 — ENGINE WIRING GAPS (엔진 미연결 & 6계층 인프라 실전 결합)]
- [x] **🔥 [P1-1] 6계층 인프라 시스템(5.3MB 템플릿/infrastructure.py)과 `WorldGenerator.generate_new_world` 실전 결합**:
  - **수정**: `generate_new_world()`에서 `InfrastructureTemplateLoader.assemble_full_world(..., bind_entities=True)`를 직접 호출하여 6계층(대륙/권역/국가/정주지/시설) 및 거주민 NPC, 상점 아이템, 퀘스트, 2D 도로망을 실전 턴 루프에 완전 바인딩. 시설(Facility)들을 탐험 가능한 `Location`으로 자동 등록하고 시작 위치(`loc_1`)와 상호 연결. `two_pass_engine.py`의 이동 액션 방향 키워드('이동' 단어 포함 시 'east' 오인식) 버그 수정.
  - **검증 파일/테스트**: `src/world/generator.py`, `src/world/two_pass_engine.py` | `tests/test_infrastructure_generator_wiring.py::test_world_generator_assembles_6_tier_infrastructure`, `test_world_generator_infrastructure_live_turn_navigation`, `test_world_generator_full_serialization_roundtrip` (통과), `eval_runner.py --no-judge` (invalid_transition_rate: 0.0%), `pytest tests/` 618 passed
- [x] **🔧 [P1-2] 미연결 3대 엔진 게임 루프(`TwoPassEngine`/`process_turn`) 실전 결합**:
  - **수정**:
    1. `merchant_barter_engine.py`: 물물교환(barter), 유물 감정(appraisal), 금화 깎기(coin clipping), 밀수 검문(smuggling checkpoint), 지역 물가 시세(regional arbitrage), 암시장 금융(black market debt)을 `TwoPassEngine.resolve_action_barter()`로 라이브 턴 결합.
    2. `combat_time_track_engine.py`: 미터 기반 상대 교전 거리 계산, 5대 사거리 존(초근접/근거리/중거리/원거리/초장거리), 접근(move_towards)/후퇴(move_away) 기동, 감각(PER) 기반 A안 위기 인지 인터럽트(perception interrupt)를 `TwoPassEngine.resolve_action_combat_distance_and_timing()`으로 결합.
    3. `siege_engine.py`: 요새 다층 방호(성벽/성문/해자/흉벽/마도결계), 포격/접근/성벽돌파 백병전/사기결산 턴 시뮬레이션 및 별동대 침투 특공(commando action), 외부 LLM 서사 프롬프트 연동을 `TwoPassEngine.resolve_action_siege()`로 결합.
    4. `two_pass_engine.py`: `DeterministicFactSheet`에 `barter_summary`, `combat_distance_summary`, `interrupt_event`, `siege_summary` 필드 및 `to_prompt_context()` 서사 지침 직렬화 추가. `compute_pass1()` 루프에서 2.496, 2.497, 2.498 순차 연산 및 `state_delta` 완전 반영.
  - **정적 도달성 결과**: `scripts/reachability_audit.py` 실행 시 미도달 모듈 **`3/64` -> `0/64` (100% Reachable)** 달성.
  - **검증 파일/테스트**: `src/world/two_pass_engine.py`, `src/world/merchant_barter_engine.py`, `src/world/combat_time_track_engine.py`, `src/world/siege_engine.py` | `tests/test_p1_2_engines_wiring.py::test_merchant_barter_engine_live_pass1`, `test_combat_distance_and_perception_interrupt_live_pass1`, `test_siege_warfare_engine_live_pass1`, `test_game_master_agent_process_turn_p1_2_integration` (4 passed), `eval_runner.py --no-judge` (invalid_transition_rate: 0.0%), `pytest tests/` 622 passed in 232.54s (0 failed)

#### [P2 — CODE QUALITY, CI & REFACTORING (품질 / CI / 유지보수)]
- [x] **🔧 [P2-1] God 메서드 분할 (`apply_update` 797줄, `pre_validate_action` 870줄)**:
  - **수정**:
    1. `src/world/state.py`의 `WorldState.apply_update()`(802줄)를 5대 도메인 서브 메서드로 분할: `_apply_player_updates`, `_apply_inventory_and_equipment_updates`, `_apply_npc_updates`, `_apply_world_environment_updates`, `_apply_subsystem_engine_deltas`. 메인 `apply_update()`는 15줄의 가독성 높은 오케스트레이터로 경량화.
    2. `src/world/validator.py`의 `ActionValidator.pre_validate_action()`(873줄)을 5대 서브 검증기로 분할: `_validate_physical_blocks`, `_validate_inventory_and_equipment`, `_validate_target_and_interaction`, `_validate_spatial_and_physical_limits`, `_dispatch_action_challenges`. 메인 `pre_validate_action()`은 간결한 오케스트레이터로 경량화.
    3. 외부 API 시그니처 및 반환 튜플 규격 100% 보존.
  - **검증 파일/테스트**: `src/world/state.py`, `src/world/validator.py` | `tests/test_p2_1_god_methods_refactor.py` (12 passed), `eval_runner.py --no-judge` (invalid_transition_rate: 0.0%), `pytest tests/` 634 passed in 229.33s (0 failed)
- [x] **🔧 [P2-2] God 파일 분할 로드맵 수립 및 3단계(entities.py, infrastructure.py, action_resolvers.py) 전면 완수**:
  - **수정**:
    1. `docs/ROADMAP_GOD_FILE_DECOMPOSITION.md` 수립: 3대 God 파일(`state.py`, `infrastructure.py`, `two_pass_engine.py`)의 책임 분리 원칙 확립.
    2. Phase 1 완수: `src/world/state.py` 상단 데이터 모델 19종을 `src/world/entities.py`로 분리 (1,900줄 경량화).
    3. Phase 2 완수: `src/world/infrastructure.py` (3,092줄)를 순수 데이터 모델 21종(`src/world/infra_models.py`), 거대 템플릿 로더(`src/world/infra_loader.py`, 1,630줄), 런타임 레지스트리(`src/world/infrastructure.py`, 654줄)로 3단 분할.
    4. Phase 3 완수: `src/world/two_pass_engine.py` (2,942줄)에서 10대 서브시스템 액션 리졸버(`resolve_action_*`, 1,228줄)를 4대 도메인 믹스인(`Movement`, `Stealth`, `Survival`, `TacticalCombat`) 및 합성 믹스인(`ActionResolversMixin`)으로 모듈화하여 `src/world/action_resolvers.py` (1,293줄)로 분리. `TwoPassEngine(ActionResolversMixin)` 다중 상속으로 기존 호출자 및 전체 테스트 100% 무회귀 하위 호환성 보장 (`two_pass_engine.py` 줄 수: 2,942줄 → 1,718줄).
  - **검증 파일/테스트**: `src/world/action_resolvers.py`, `src/world/two_pass_engine.py` | `tests/test_p2_2_god_files_decomposition.py` (11 passed), `eval_runner.py --no-judge` (invalid_transition_rate: 0.0%), `pytest tests/` 660 passed in 16.94s (0 failed)
- [x] **🔧 [P2-3] GitHub Actions CI 워크플로우(`.github/workflows/ci.yml`) 구축**:
  - **수정**:
    1. `.github/workflows/ci.yml` 파이프라인 구축: push 및 pull_request 트리거, Ubuntu 환경, Python 3.12, 의존성 pip 캐싱.
    2. 4대 품질 게이트 자동화: `pyflakes src/ tests/` (코드 위생), `ruff check src/ --select F,E9` (구문/임포트 치명적 린트), `python scripts/reachability_audit.py` (정적 도달성 100% 검증), `pytest tests/` (640개 자동화 테스트 스위트 전수 실행).
    3. `scripts/reachability_audit.py`에 미도달 모듈 발생 시 `sys.exit(1)` 반환 차단 가드 구축.
  - **검증 파일/테스트**: `.github/workflows/ci.yml`, `scripts/reachability_audit.py` | `tests/test_p2_3_ci_workflow.py` (3 passed), `pytest tests/` 640 passed in 232.20s (0 failed)
- [x] **🔧 [P2-4] 문서-코드 드리프트 최신화 및 자동화 프로세스**:
  - **수정**:
    1. `scripts/sync_doc_metrics.py` 신설: `pytest --collect-only` 기반 실제 테스트 수 및 `CHANGES_AUDIT.md` 기반 정적 도달성 통계를 자동 추출하여 `README.md`의 단위 테스트 합격 수치, 명령어 주석, 디렉터리 트리 주석, 도달률 수치 자동 동기화 (`--sync`) 및 검증 (`--check`).
    2. `.github/workflows/ci.yml`에 `Document-Code Drift Check` 게이트 단계 추가하여 문서-코드 불일치 시 CI 자동 차단.
    3. `TRIAGE.md`의 오래된 Category C(P1-2 3대 엔진 보류 상태)를 최신 100% 도달 상태(`0 of 65 modules`)로 갱신.
  - **검증 파일/테스트**: `scripts/sync_doc_metrics.py`, `TRIAGE.md`, `README.md`, `.github/workflows/ci.yml` | `tests/test_p2_4_doc_drift.py` (3 passed), `pytest tests/` 643 passed in 234.37s (0 failed)
- [x] **🐛 [P2-5] LLM JSON 출력 파싱 파이프라인 일원화 (`JSONRepairEngine`)**:
  - **수정**:
    1. `src/llm/resilience.py`: `JSONRepairEngine.repair_json()` 및 `repair_and_parse()`에 `ast.literal_eval` 폴백을 추가하여 LLM이 작은따옴표(`'`)를 포함한 Python 딕셔너리 형태로 반환하거나 줄바꿈 에러 발생 시에도 안전하게 파싱 지원.
    2. `src/agents/game_master.py`: `generate_world_news_tick(state)`을 `process_turn()`의 10턴 주기(`state.turn > 0 and state.turn % 10 == 0`) 경로에 정식 배선하여 매 10턴마다 오프스크린 NPC 활동 기반 소문 생성 및 `narration`, `world_news_feed`, `world_facts`에 반영. `world_news_feed` 및 `world_facts` 최대 30개 캡/감쇄 정책 적용.
    3. `src/world/state.py`: `WorldState.from_dict()`에서 `world_news_feed` 역직렬화 복구 반영.
    4. `eval_runner.py`: LLM 판정관(`judge_memory_utilisation`, `judge_factual_consistency`)의 raw `json.loads`를 `JSONRepairEngine.repair_json()`으로 통일하여 마크다운 코드블록 등으로 인한 판정 누락 방지.
  - **검증 파일/테스트**: `src/llm/resilience.py`, `src/agents/game_master.py`, `src/world/state.py`, `eval_runner.py` | `tests/test_p2_5_json_repair_pipeline.py` (9 passed), `pytest tests/` 652 passed in 269.80s (0 failed)
- [x] **🐛 [P2-6] `src/world/economy_engine.py:423` 독 치료(`remove_poison`) 반환값 무시 버그 수정**:
  - **수정**: `cured` 결과에 따라 치료 대상 존재 시에만 골드 차감 및 성공 반환, 미치료 시 골드 미차감 및 안내 메시지 반환.
  - **검증 파일/테스트**: `src/world/economy_engine.py` | `tests/test_p0_p2_fixes.py::test_economy_engine_remove_poison_cured_check` (통과)
- [x] **🐛 [P2-7] `src/world/attack_physics_engine.py:59` 활 오버드로우 배율(`ratio`) 미사용 버그 수정**:
  - **수정**: `allow_overdraw` 플래그 지원을 통해 기존 완전 만작 계약(1.0)을 유지하면서 과인장 시 계산된 `ratio`(최대 1.2) 정상 반영.
  - **검증 파일/테스트**: `src/world/attack_physics_engine.py` | `tests/test_p0_p2_fixes.py::test_attack_physics_can_draw_bow_overdraw_ratio` (통과)
- [ ] **⚠️ [P2-8 / 원칙] `scripts/reachability_audit.py` 단일 파일 내부 호출 판정(False Positive) 주의 원칙**: 동일 파일 내 호출 메서드 오인 방지 및 삭제 전 grep 필수.

### [로드맵 & 플랫폼 백로그 (공통/플랫폼)]
- [ ] **UI/플랫폼 로드맵 [찐찐 마지막 최종 업데이트로 동결]**:
  - `SteamStyleStandaloneLauncher` (독립 실행형 창 모드 런처)
  - `DynamicDualMapRenderer` (LoRA SD 1.5 기반 실시간 동적 부분 갱신 이중 맵)
  - `InteractiveWebUI` (웹 대시보드), `DynamicAudioPlayer` (BGM 믹서), `ChronicleBookExporter` (소설책 조판)
  - *상세 아키텍처 및 동결 원칙은 [MASTER_GAME_ARCHITECTURE.md Section 8 & 9](file:///c:/Quilltale/MASTER_GAME_ARCHITECTURE.md) 참조.*
- [ ] **기타 미완성 기능 및 템플릿 백로그 (가문 혈통, 종교 신앙, 영지 개척, 네크로맨시, 템플릿 확충 등)**:
  - *전체 상세 명세 및 40여 종 완료 이력은 [docs/archive/SESSION_LOG_2026-09.md](file:///c:/Quilltale/docs/archive/SESSION_LOG_2026-09.md)에 보존됨.*

---

## 3. 📅 [2026-09-17] 현재 세션 통합 개발 현황

### 1. 이번 세션 구현 완료 핵심 내용 종합 (총 4대 핵심 과제 100% 완수)

#### 1) [P2-4] 문서-코드 드리프트 자동 동기화 도구 및 CI 게이트 구축
- `scripts/sync_doc_metrics.py` 구축: 단위 테스트 수치, 명령어 주석, 디렉터리 트리 주석, 정적 도달률 자동 동기화(`--sync`) 및 CI 검증(`--check`).
- `.github/workflows/ci.yml` 파이프라인 연동 및 `tests/test_p2_4_doc_drift.py` 3종 테스트 구축 및 통과.

#### 2) [P2-5] LLM JSON 파싱 파이프라인 일원화 및 세계 뉴스 턴 배선
- `JSONRepairEngine`에 AST `literal_eval` 폴백 추가(작은따옴표 포함 Python 딕셔너리 안전 복원).
- `GameMasterAgent.generate_world_news_tick()` 10턴 주기 라이브 배선 및 30개 상한 슬라이싱/감쇄 정책 적용.
- `eval_runner.py` 판정관 JSON 복원 로직 일원화 및 `tests/test_p2_5_json_repair_pipeline.py` 9종 테스트 구축 및 통과.

#### 3) [P2-2 Phase 2] `src/world/infrastructure.py` 계층 분리
- 3,092줄 God 파일을 3단 분리:
  - `src/world/infra_models.py` (21종 데이터 모델, 858줄)
  - `src/world/infra_loader.py` (템플릿 로더 및 계층 바인딩, 1,680줄)
  - `src/world/infrastructure.py` (런타임 레지스트리 및 심볼 100% re-export, 654줄)
- `tests/test_p2_2_god_files_decomposition.py` Phase 2 테스트 4종 추가 (총 7 passed).

#### 4) [P2-2 Phase 3] `src/world/two_pass_engine.py` 액션 리졸버 분리
- 2,942줄 God 파일 분할:
  - `src/world/action_resolvers.py` (10대 리졸버 4대 도메인 믹스인, 1,293줄)
  - `src/world/two_pass_engine.py` (1,228줄 제거 및 `ActionResolversMixin` 상속, 2,942줄 → 1,718줄)
- `TwoPassEngine(ActionResolversMixin)` 다중 상속으로 100% 무회귀 하위 호환성 보장.
- `tests/test_p2_2_god_files_decomposition.py` Phase 3 테스트 4종 추가 (총 11 passed).

#### 5) [P1-3] 결정론적 대사 슬롯 조립, 하이브리드 의도 라우터 및 심층 대화 페르소나 앵커링 (`DialogueSlotEngine`) 3단계 전면 완수
- `data/templates/dialogue_slots.json`: 8대 아키타입, 431개 대사 템플릿, 70종 스트레스/감정 행동 지문, 32종 성격 트레이트 어미 데이터베이스 완성 (~965,000가지 조합).
- `src/world/dialogue_slot_engine.py`: 100% 결정론적 SHA-256 슬롯 조립 엔진 및 `classify_intent()` 하이브리드 라우터 구현 (`IntentRoutingResult`, Rule 5 `traits` 준수).
- `src/world/action_resolvers.py` & `src/world/two_pass_engine.py`:
  - `compute_pass1()` 라이브 턴 경로 및 `DeterministicFactSheet` 완전 배선 (`requires_llm`, `dialogue_routing`, `dialogue_persona_anchor` 슬롯 주입).
  - Pass 1 프롬프트 컨텍스트에 `[🎭 NPC 페르소나 및 화법 앵커링 (PERSONA ANCHORING)]` 자동 직렬화.
  - `TwoPassEngine.sanitize_pass2_result()`에 화자 누락 시 대상 NPC 및 행동 지문 강제 주입 화자 검증기(Speaker Grounding) 탑재.
- `src/agents/game_master.py`:
  - **[1~2단계] 0-토큰 하이브리드 바이패스 (0원 / 0ms)**: 일상 대화(`requires_llm is False`) 시 LLM 호출을 건너뛰고 조립 대사 즉시 반환.
  - **[3단계] 심층 대화 페르소나 화법 주입**: 심층 질문(`requires_llm is True`) 시 대상 NPC의 말투 규칙, 신체 행동 지문, 스트레스/감정을 `dynamic_system_prompt`에 강제 주입하여 캐붕(캐릭터 붕괴) 및 AI 비서체 원천 차단.
- `tests/test_dialogue_slot_engine.py`: 12종 단위 테스트 전원 통과 (0-토큰 바이패스, 심층 질문 페르소나 앵커링, 검증기 화자 보정 전수 검증).

---

### 2. 테스트 및 평가 검증 상태 (세션 누적 지표)
- **전체 단위 테스트**: `672 passed` (0 failed, 무회귀).
- **무효 상태 전이율 (eval_runner.py --no-judge)**: `0.0%` (20턴 시나리오 무결점 통과).
- **정적 도달성 (scripts/reachability_audit.py)**: `0/69 Unreachable` (69/69 모듈 100% 도달).
- **코드 정적 검사 (pyflakes & ruff)**: `src/` 및 `tests/` 전수 검증 통과 (`pyflakes src/ tests/`: 0건 Clean, `ruff check`: Clean).

---

### 3. 다음 세션 작업 착수 안내 (Next Step)
1. **[정리 과제] `save_load_manager.py` 삭제**:
   - `persistence.py`로 완전 대체된 레거시 중복 파일 정리 (Category B).
2. **[게임플레이 도메인 확장 백로그]**:
   - 가문 혈통(Lineage), 종교 신앙(Deity), 영지 개척(Domain), 사령술(Necromancy) 시스템.
3. **[플랫폼/UI 로드맵]**:
   - 독립 실행형 창 모드 런처(`SteamStyleStandaloneLauncher`), 동적 부분 갱신 이중 맵(`DynamicDualMapRenderer`).


