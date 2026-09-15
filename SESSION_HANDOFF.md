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
1. **문서 및 에이전트 거버넌스 토큰 부하 대규모 최적화 (Token Diet)**:
   - **`SESSION_HANDOFF.md` 압축**:
     - 중복 "고정 규칙 1-10" 삭제 ➔ `AGENTS.md` 단일 원천 포인터로 일원화.
     - 완료된 40여 개 과거 백로그 및 상세 세션 로그를 `docs/archive/SESSION_LOG_2026-09.md`로 아카이빙 분리.
     - 미도달 엔진 세부 목록을 `TRIAGE.md` / `CHANGES_AUDIT.md` 참조 구조로 정리.
   - **`AGENTS.md` 단일 출처화 & 정비**:
     - `<UI>` 섹션을 `<Code_Hygiene>`에 통합.
     - `<Game_Design_Anchors>` 8대 원칙을 `src/agents/prompts.py`의 `GM_SYSTEM_PROMPT` 상단 주석으로 재배치.
     - `<Scope_Gate>` 동결 정책 및 HD-2D 시각화 Q&A를 `MASTER_GAME_ARCHITECTURE.md` Section 8, 9로 재배치.
     - `<Dev_Ops>` 3번 환경 분리 조항 압축.
2. **DoD Gate 및 전체 테스트 회귀 검증**:
   - `pytest tests/`: **585 passed** (0 failed).

---

### 2. 테스트 및 평가 검증 상태
- **전체 단위 테스트**: 585 passed in full suite (0 failed, 231.25s).
- **Static Analysis & Repository Hygiene**:
  - `src/` 내 문법 오류, 미정의 변수(`pyflakes`), 미사용 임포트 없음.

---

### 3. 다음 세션 작업 착수 안내 (Next Step)
1. **[P0 긴급 버그 착수]**:
   - `src/agents/player_bot.py:137` `Item` 임포트 누락 수정 및 회귀 테스트.
   - `src/llm/claude.py` 퇴역 모델 교체 및 API 에러 가드 보강.
   - `app.py` `take_action()` 내 `state is None` 가드 추가.
2. **[P2 로직 결함 즉시 수정]**:
   - `src/world/economy_engine.py:423` 독 치료 반환값 분기.
   - `src/world/attack_physics_engine.py:59` 활 오버드로우 `ratio` 연결.
3. **[P2 CI 구축]**:
   - `.github/workflows/ci.yml` 작성.
