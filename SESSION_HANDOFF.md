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

#### [P0 — CONFIRMED CRASH BUGS (최우선 긴급 수정)]
- [ ] **🔥 [P0-1] `src/agents/player_bot.py:137` `Item` import 누락으로 인한 NameError 크래시 해결**:
  - **증상**: 봇 체력 < 35% 시 포션 검색 라인에서 `Item` 미임포트로 `NameError` 발생, 100% 크래시.
  - **처방**: `from src.world.state import Item` 추가 또는 `i in state.items` 사전 검사 구조 개선.
- [ ] **🔥 [P0-2] `src/llm/claude.py` 퇴역 모델 교체, KeyError 방어 및 Gemini 수준 재시도/폴백 구축**:
  - **증상**: `claude-sonnet-4-20250514` 모델 퇴역으로 호출 불가. 키 누락 시 KeyError 발생 및 재시도 부재.
  - **처방**: 최신 현행 모델(`claude-3-5-sonnet-latest` 등) 갱신, 안전한 키 참조 및 지수 백오프/재시도 이식.
- [ ] **🔥 [P0-3] `app.py` `take_action()` 내 `world_state` 파싱 실패 시 `None` 유입 크래시 방어**:
  - **증상**: `state is None` 상태로 `gm.process_turn()` 호출 시 `AttributeError` 크래시 발생.
  - **처방**: `state is None` 가드 단락 추가 및 로드 대기 안내 반환.

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
- [ ] **🔧 [P2-4] 문서-코드 드리프트 최신화 및 자동화 프로세스**: README.md 수치 최신화(585 통과), 배선 변경 시 `reachability_audit.py` 및 `CHANGES_AUDIT.md` 동시 커밋 프로세스 준수.
- [ ] **🐛 [P2-5] LLM JSON 출력 파싱 파이프라인 일원화 (`JSONRepairEngine`)**: `game_master.py:638` raw `json.loads`를 `JSONRepairEngine.repair_json()`으로 통일.
- [ ] **🐛 [P2-6] `src/world/economy_engine.py:423` 독 치료(`remove_poison`) 반환값 무시 버그 수정**: `cured` 결과에 따라 성공 시에만 골드 차감 및 메시지 분기.
- [ ] **🐛 [P2-7] `src/world/attack_physics_engine.py:59` 활 오버드로우 배율(`ratio`) 미사용 버그 수정**: 반환 튜플의 인장 배율 자리에 계산된 `ratio` 정상 연결.
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

---

### 2. 테스트 및 평가 검증 상태
- **전체 단위 테스트**: 597 passed (0 failed) — 신규 12개 추가.
- **회귀 기준선 대비**: 585 → 597 (+12, 기존 회귀 0건).

---

### 3. 다음 세션 작업 착수 안내 (Next Step)
1. **[P0 긴급 버그]**:
   - `src/agents/player_bot.py:137` `Item` 임포트 누락 수정.
   - `src/llm/claude.py` 퇴역 모델 교체 및 API 에러 가드 보강.
   - `app.py` `take_action()` 내 `state is None` 가드 추가.
2. **[P2 로직 결함]**:
   - `src/world/economy_engine.py:423` 독 치료 반환값 분기.
   - `src/world/attack_physics_engine.py:59` 활 오버드로우 `ratio` 연결.
3. **[P1-1 6계층 인프라 결합]**:
   - `generate_new_world()`에서 `InfrastructureRegistry` 및 `assemble_full_world` 호출.
4. **[P2 CI 구축]**:
   - `.github/workflows/ci.yml` 작성.
