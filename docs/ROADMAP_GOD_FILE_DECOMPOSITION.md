# God 파일 3종 분할 및 모듈화 로드맵 (God File Decomposition Roadmap)

> **원칙**: 
> 1. 단일 책임 원칙(SRP) 준수 및 순수 데이터 모델과 런타임 전이/시뮬레이션 로직의 분리.
> 2. 외부 호출자 대상 100% 하위 호환성 보장 (Re-export 패턴).
> 3. 단계별 원자적(Atomic) 마이그레이션 및 무회귀(Zero-Regression) 검증.

---

## 1. 3대 God 파일 현황 및 진단

| 파일명 | 줄 수 | 주 책임 (Responsibility) | 문제점 (Issue) |
| :--- | :---: | :--- | :--- |
| **src/world/state.py** | 4,641줄 | 게임 엔티티 모델 19종 + WorldState 런타임 상태 컨테이너 & 턴 시뮬레이션 | 데이터 엔티티 정의(1,900줄)와 턴 상태 연산(2,700줄)이 뒤섞여 유지보수성 저하 |
| **src/world/infrastructure.py** | 3,092줄 | 6계층 인프라 데이터 모델 + InfrastructureRegistry + 템플릿 로더/바인더 | 엔티티 모델(840줄), 레지스트리(580줄), 거대 템플릿 파서(1,630줄) 공존 |
| **src/world/two_pass_engine.py** | 2,941줄 | DeterministicFactSheet + TwoPassEngine (10대 서브시스템 액션 리졸버 + compute_pass1) | 개별 행동 판정 로직(1,300줄)과 1,291줄의 오케스트레이터가 단일 클래스/파일에 비대화 |

---

## 2. 단계별 분할 로드맵 (Phased Execution)

### 🚀 Phase 1 (완료): src/world/state.py 엔티티 모델 분리
- **목표**: 순수 데이터 엔티티 19종을 `src/world/entities.py`로 분리하고, `state.py`에서 전면 re-export.
- **결과**: `state.py` 4,641줄 → 2,740줄로 약 1,900줄 경량화 완료, 기존 전역 import 코드 100% 호환.

### 🚀 Phase 2 (완료): src/world/infrastructure.py 계층 분리
- **목표**: 거시 데이터 모델, 런타임 레지스트리, 템플릿 조립기 3단 분리.
- **분리 구조**:
  - `src/world/infra_models.py`: Continent, Region, Nation, Settlement, Facility 등 순수 데이터클래스 21종 (858줄).
  - `src/world/infra_loader.py`: InfrastructureTemplateLoader JSON 로드 및 계층 바인딩 (1,680줄).
  - `src/world/infrastructure.py`: InfrastructureRegistry 및 기존 심볼 전원 re-export (654줄).
- **결과**: 3,092줄 → 3개 모듈(각 600~1,700줄)로 분할 완료, 하위 호환 100% 유지.

### 🚀 Phase 3 (완료): src/world/two_pass_engine.py 액션 리졸버 모듈화
- **목표**: 10대 서브시스템 `resolve_action_*` 메서드를 도메인별 믹스인으로 분리.
- **분리 구조**:
  - `src/world/action_resolvers.py` (1,293줄):
    - `MovementResolverMixin`: `resolve_action_movement`
    - `StealthResolverMixin`: `resolve_action_eavesdrop`, `resolve_action_stealth`
    - `SurvivalResolverMixin`: `resolve_action_harvest`, `resolve_action_campsite`, `resolve_action_drink`, `resolve_action_botany`
    - `TacticalCombatResolverMixin`: `resolve_action_barter`, `resolve_action_combat_distance_and_timing`, `resolve_action_siege`
    - `ActionResolversMixin`: 4대 믹스인 일괄 합성
  - `src/world/two_pass_engine.py`: 2,942줄 → 1,718줄 (1,224줄 경량화).
    - `TwoPassEngine(ActionResolversMixin)` 다중 상속으로 100% 무회귀 하위 호환성 보장.
    - DeterministicFactSheet 및 순수 `compute_pass1` 오케스트레이션에 집중.
- **결과**: 660개 단위 테스트 전원 통과, reachability 68/68 100% 유지, invalid_transition_rate 0.0%.

---

## 3. 하위 호환성 보장 원칙 (Zero-Breaking Policy)

모든 분할 파일은 기존 import 경로를 100% 보존해야 합니다:
`python
# 기존 호출자 (변경 불필요)
from src.world.state import WorldState, Player, NPC, Location, Item
from src.world.infrastructure import InfrastructureRegistry, Settlement, Facility
from src.world.two_pass_engine import TwoPassEngine, DeterministicFactSheet
`
모든 리팩터링은 pytest tests/ 무회귀 및 eval_runner.py 0.0% 검증을 통과해야 완료 처리됩니다.
