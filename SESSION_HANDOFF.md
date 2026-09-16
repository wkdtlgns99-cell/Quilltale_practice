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
- [ ] **🔥 [P0-0-1] `src/llm/claude.py` 퇴역 모델 교체 및 다중 모델 폴백 체인 구축**:
  - **위험**: `claude-3-5-sonnet-latest`는 2026년 2월 19일 완전 퇴역(retired)되어 provider 전환 시 100% 호출 실패. 현재 단일 모델 재시도만 존재하여 Gemini 수준 다중 모델 폴백 부재.
  - **처방**: 최신 활성 모델(`claude-3-7-sonnet-latest` 등)로 하드코딩 교체, `gemini.py`처럼 후보 모델 리스트(`candidate_models`) 순차 폴백 구조 구축.
- [ ] **🔥 [P0-0-2] `src/world/two_pass_engine.py` 무효 행동 선행 변이 차단 (QT-F01)**:
  - **위험**: `compute_pass1()`에서 `ActionValidator.pre_validate_action()` 전에 상태이상 피해, 저체온증, 감염, 식량 부패, 수면 피로, 퀘스트 시간 차감, 쿨다운, 세계 시뮬레이션이 인플레이스로 먼저 반영된 후 기각 시 롤백 없이 DB에 영구 저장됨.
  - **처방**: 딥카피 오버헤드 없이 `ActionValidator.pre_validate_action()`을 `compute_pass1()` 최상단(모든 환경/상태 틱 이전)으로 순서 재배치하여 무효 행동 시 0-변이 보장.
- [ ] **🚨 [P0-0-3] `src/world/state.py` 토큰 폭발 방지 world_facts 프롬프트 슬라이싱 & 원본 리스트 상한 (QT-F03)**:
  - **위험**: `state.world_facts`가 슬라이싱 없이 매 턴 전체가 LLM 프롬프트에 통째로 주입됨. `npc.off_screen_logs`, `location.physical_traces`, `state.history`의 상한 부재로 세이브 파일 비대화.
  - **처방**: `to_narrative_context()`에서 `world_facts[-10:]` 슬라이싱 적용. `off_screen_logs` 10개 캡, `physical_traces` 10개 캡/15턴 감쇄, `history` 활성 50턴 캡 및 별도 SQLite 아카이브 분리.
- [x] **🚨 [P0-0-4] 보조 LLM JSON 출력 파싱 시 raw `json.loads`의 `JSONRepairEngine` 통일 (QT-F04)**:
  - **수정**: `src/llm/resilience.py`에 `JSONRepairEngine.repair_json(raw_text)` 범용 정적 메서드 추가(마크다운 코드펜스, outer JSON 추출, trailing comma, unescaped 줄바꿈 복구). `game_master.py:643`(세계 뉴스), `chronicle.py:105`(연대기), `generator.py:850`(동적 지역)의 raw `json.loads`를 `repair_json`으로 전면 교체.
  - **검증 파일/테스트**: `src/llm/resilience.py`, `src/agents/game_master.py`, `src/world/chronicle.py`, `src/world/generator.py` | `tests/test_p0_p2_fixes.py::test_json_repair_engine_auxiliary_repair` (통과), `pytest tests/` 605 passed | commit `7cc4b8d`
- [x] **🔧 [P0-0-5] 8개 파일 UTF-8 BOM (`\ufeff`) 제거 및 정적 분석 정상화 (QT-F05)**:
  - **수정**: 8개 파일 BOM 제거. `reachability_audit.py`를 `utf-8-sig` 인코딩 + AST `ast.Call` 노드 기반 내부 호출 탐지 방식으로 전면 수정 (기존 `if f != w_resolved` 오판 버그 근본 수정).
  - **결과**: `two_pass_engine.py` never-called 6→0 (campsite/stealth/harvest/eavesdrop 4종 `called-from-live-path` 정상 분류). 전체 never-called 84→31. `event_perspective.py`/`scenario_manager.py` 0메서드→정상 집계.
  - **검증 파일/테스트**: `scripts/reachability_audit.py`, 8개 파일 | BOM 0건 확인, AST 전체 파싱 통과, `pytest tests/` 604 passed | commit `ae32096`
- [ ] **🔧 [P0-0-6] 문서-코드 팩트 정정 및 동기화 (QT-F07)**:
  - **처방**: P0-0-5 audit 결과로 campsite/stealth/harvest/eavesdrop 4종 배선이 이미 정상으로 자동 정정됨. `TRIAGE.md` 배선 상태 반영 및 `README.md` 테스트 수치(604개) 갱신은 8순위(최종 문서 동기화)에서 일괄 처리.
- [x] **🔧 [P0-0-7] LLM 쿼터 고갈 시 영문 예외 문자열 서사 유출 방어 (QT-F08)**:
  - **수정**: `game_master.py`의 `process_turn()` 예외 블록에서 `repair_and_parse(str(e))` 호출 완전 제거 및 한국어 서사 폴백 딕셔너리 직접 반환. `resilience.py`의 `JSONRepairEngine`에 `is_technical_error()` 정적 메서드를 구축하여 JSON 파싱 실패/폴백 시 영문 기술적 예외(429, exhausted, traceback 등)가 서사로 유출되는 것을 2중 원천 차단.
  - **검증 파일/테스트**: `src/agents/game_master.py`, `src/llm/resilience.py` | `tests/test_p0_p2_fixes.py::test_llm_quota_exhausted_fallback_korean`, `tests/test_p0_p2_fixes.py::test_game_master_process_turn_llm_exception_safe_korean_narration` (통과), `pytest tests/` 607 passed | commit `33cfd11`
- [ ] **🔧 [P0-0-8] 잔여 결함 디테일 보강 (P0-1, P2-7)**:
  - `player_bot.py:137`: 미사용 죽은 `Item` import 청소.
  - `attack_physics_engine.py`: `can_draw_bow` 호출부(`npc_skill_engine.py` 등)에 `allow_overdraw=True` 전달 진입점 마련.

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
- [ ] **🔥 [P1-1] 6계층 인프라 시스템(5.3MB 템플릿/infrastructure.py)과 `WorldGenerator.generate_new_world` 실전 결합**:
  - **증상**: 6계층 인프라의 대륙/국가/정주지/시설 데이터와 도로망 그래프가 실전 게임플레이에서 미호출 상태.
  - **선택 및 처방**: `generate_new_world()`에서 `InfrastructureRegistry` 및 `assemble_full_world` 호출로 계층 조립 결합.
- [ ] **🔧 [P1-2] 미연결 5대 엔진 게임 루프(`TwoPassEngine`/`process_turn`) 연결**:
  - **대상 엔진**: `siege_engine.py`, `merchant_barter_engine.py`, `combat_time_track_engine.py`, `time_calendar_engine.py`, `vein_restoration_engine.py` (상세는 [TRIAGE.md](file:///c:/Quilltale/TRIAGE.md) 참조).
  - **처방**: `TwoPassEngine.compute_pass1` / `DeterministicFactSheet` 슬롯에 순차 연결 또는 기존 엔진 통합.

#### [P2 — CODE QUALITY, CI & REFACTORING (품질 / CI / 유지보수)]
- [ ] **🔧 [P2-1] God 메서드 분할 (`apply_update` 797줄, `pre_validate_action` 870줄)**: 업데이트/액션 타입별 디스패치 핸들러로 모듈화 분할.
- [ ] **🔧 [P2-2] God 파일 분할 로드맵 수립 (`state.py` 4,588줄, `infrastructure.py` 3,092줄, `two_pass_engine.py` 2,433줄)**: 데이터클래스/엔티티 스키마와 턴 상태 갱신/전이 로직 분리.
- [ ] **🔧 [P2-3] GitHub Actions CI 워크플로우(`.github/workflows/ci.yml`) 구축**: `pytest tests/`, `ruff check --select F,E9`, `python scripts/reachability_audit.py` 자동 검증.
- [ ] **🔧 [P2-4] 문서-코드 드리프트 최신화 및 자동화 프로세스**: README.md 수치 최신화(604 통과), 배선 변경 시 `reachability_audit.py` 및 `CHANGES_AUDIT.md` 동시 커밋 프로세스 준수.
- [ ] **🐛 [P2-5] LLM JSON 출력 파싱 파이프라인 일원화 (`JSONRepairEngine`)**: `game_master.py:638` raw `json.loads`를 `JSONRepairEngine.repair_json()`으로 통일.
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

## 3. 📅 [2026-09-15] 현재 세션 개발 현황

### 1. 이번 세션 구현 완료 핵심 내용

#### P1-6 시간 경제 단일 원천 정리 (3중 구현 → 1개)
- `src/core/config.py`의 미사용 고정 상수(`TIME_TALK_MINUTES` 등 4종) 삭제.
- `TimeCalendarEngine.determine_action_duration()` 단일 원천으로 채택.
- `TwoPassEngine.compute_pass1()` 1119행: 비이동 행동 기본 시간을 고정 30분에서 키워드 기반 가변 소요 시간으로 교체. 피로도 변화도 자동 반영.
- 파일: `src/core/config.py`, `src/world/two_pass_engine.py`

#### P1-7 오디오 파이프라인 낭비 차단
- `src/core/config.py`에 `ENABLE_AUDIO: bool = False` 플래그 추가.
- `src/agents/game_master.py` 314행: `ENABLE_AUDIO=False` 시 `AudioEngine` 연산 완전 스킵.
- 파일: `src/core/config.py`, `src/agents/game_master.py`

#### vein_restoration_engine.py 실전 배선 완료 (마나 파괴↔치유 루프 완성)
- `ManaVeinRestorationEngine.perform_surgery()` → `two_pass_engine.py:2.75 Sub-path B` 연결.
- 수술 키워드(에테르 투석/탕약/기적 봉합/회로 재건 등) 감지 시 회로 손상 가드 후 실행.
- `DeterministicFactSheet.vein_restoration_summary` 필드 및 `to_prompt_context()` 섹션 추가.
- `vein_restoration_engine.get_circuit_state()`: `ManaCircuitState` 객체 ↔ dict 자동 변환.
- 파일: `src/world/two_pass_engine.py`, `src/world/vein_restoration_engine.py`

#### 공식 보류 엔진 3종 (의도적 Shelve 처리 문서화)
- `siege_engine.py`: 요새 공성 시나리오 세션까지 보류.
- `combat_time_track_engine.py`: 초/미터 단위 전투 개편 세션까지 보류.
- `merchant_barter_engine.py`: EconomyEngine 흡수 통합(Backlog #21) 대기 유지.
- `TRIAGE.md` 갱신 완료.

#### 신규 통합 테스트 (12개 → 총 597개)
- `tests/test_vein_restoration_wiring.py`: `compute_pass1()` 통과 수술/골드차감/회로 복구/프롬프트 컨텍스트 (5개)
- `tests/test_time_economy_wiring.py`: 행동별 가변 소요 시간 검증 (7개)
- `tests/test_two_pass_engine.py::test_non_movement_action_uses_calendar_engine_duration`: P1-6 반영 갱신

#### Reachability Audit
- 미도달 모듈: **13/64 → 3/64** (이번 세션 및 이전 세션 누적 해소)
- `CHANGES_AUDIT.md` 자동 갱신 완료.

#### P0 크래시 3종 & P2 로직 결함 2종 해결 (완료)
- `src/agents/player_bot.py:137`: `Item` 임포트 누락 해결 및 안전한 딕셔너리 검사 적용.
- `src/llm/claude.py`: 퇴역 모델 교체(`claude-3-5-sonnet-latest`), `ANTHROPIC_MODEL` 환경변수 우선 적용, 키 부재 시 KeyError 방어 및 재시도/지수 백오프 구축.
- `app.py`: `take_action()` 내 `state is None` 가드 단락 추가 (AttributeError 차단).
- `src/world/economy_engine.py:423`: `cured` 결과에 따라 치료 성공 시에만 골드 차감 분기.
- `src/world/attack_physics_engine.py:59`: `allow_overdraw` 플래그로 과인장 배율(`ratio`, 최대 1.2) 연결 및 기존 완전 만작 계약(1.0) 보존.

#### 신규 테스트 (7개 → 총 604개)
- `tests/test_p0_p2_fixes.py`: P0 버그 3종 및 P2 버그 2종 회귀 방지 단위 테스트 (7개)

---

### 2. 테스트 및 평가 검증 상태
- **전체 단위 테스트**: 604 passed (0 failed) — 신규 7개 추가.
- **회귀 기준선 대비**: 597 → 604 (+7, 기존 회귀 0건).
- **무효 상태 전이율 (eval_runner.py --no-judge)**: `0.0%` (20턴 시나리오 무결점 통과)

---

### 3. 다음 세션 작업 착수 안내 (Next Step)
1. **[P0-0-1 & P0-0-2 최우선 버그 해결]**:
   - `claude.py` 퇴역 모델명 교체 및 후보 모델 순차 폴백 체인 구축.
   - `two_pass_engine.py`의 `ActionValidator.pre_validate_action`을 최상단으로 재배치하여 무효 행동 시 선행 상태 변이 및 오염 저장 원천 차단.
2. **[P0-0-3 ~ P0-0-5 토큰/안정성/BOM 정리]**:
   - `world_facts` 프롬프트 슬라이싱 `[-10:]`, 원본 리스트 상한/감쇄 적용.
   - raw `json.loads`의 `JSONRepairEngine` 공통 통일.
   - 8개 파일 UTF-8 BOM 제거 및 `reachability_audit.py` `utf-8-sig` 적용.
3. **[P1-1 6계층 인프라 결합]**:
   - `WorldGenerator.generate_new_world()`에서 `InfrastructureRegistry` 및 `assemble_full_world` 호출로 대륙/국가/정주지/시설 데이터와 도로망 그래프 실전 턴 루프 결합.
4. **[P0-0-6 문서 최신화 및 보류 정리]**:
   - `TRIAGE.md`, `SESSION_HANDOFF.md`, `README.md` 실제 코드 상태와 동기화 (`campsite`/`stealth` 보류 유지, `save_load_manager.py` 잔여 언급 제거, 604 통과 수치 최신화).
   - `merchant_barter_engine.py` (EconomyEngine 흡수).
