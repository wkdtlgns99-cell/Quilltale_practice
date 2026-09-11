---
title: ᚛ Quilltale ᚜
emoji: 🪶
colorFrom: indigo
colorTo: gray
sdk: gradio
sdk_version: 6.14.0
app_file: app.py
tags:
  - storytelling
  - game
  - llm
  - ai-agents
  - rpg
  - memory
---
# ᚛ Quilltale (깃펜 설화) ᚜
> **100% 결정론적 시뮬레이션 엔진과 LLM 서사가 결합된 차세대 하이퍼 리얼리즘 TRPG 엔진**

Quilltale은 인공지능의 자유로운 환각(Hallucination)에 서사를 맡기지 않습니다. **100% 엄격한 파이썬 결정론적 물리 엔진(Pass 1)**이 세계의 법칙, 거리, 소음, 체온, 산소, 주사위 판정, 가방 무게를 계산하고, **언어 모델(Pass 2)**은 오직 확정된 팩트시트만을 서사적으로 묘사합니다.

---

## 🌟 핵심 설계 철학 (Core Philosophy)

1. **Anti-Yes-Man Rule (필멸자 플레이어 원칙)**
   - 플레이어는 전능한 주인공이 아닌 연약한 필멸자입니다.
   - 개연성 없는 억지 행동, 무리한 파워스케일링 시도는 가차 없이 현실적인 물리 법칙과 주사위 판정에 의해 실패합니다.
2. **Two-Pass Architecture (결정론적 2단계 파이프라인)**
   - **Pass 1 (Python Engine)**: 물리 법칙, 턴 소요 시간, 거리 매트릭스, 생존 틱, 은신 데시벨, 전투 판정 등 모든 계산을 100% 결정론적으로 수행하여 `FactSheet`를 작성합니다.
   - **Pass 2 (LLM Narrative)**: 언어 모델은 오직 `FactSheet`에 확정된 사건만을 문학적으로 묘사합니다. 만약 LLM이 팩트를 거스르는 환각을 출력하면 `sanitize_pass2_result` 검증기가 이를 감지하고 강제 교정합니다.
3. **단일 진실 공급원 (`WorldState`)**
   - 모든 인벤토리, NPC의 심리 상태, 도로망, 던전의 암반 내구도, 체온, 유효 시간은 구조화된 JSON/데이터클래스로 완벽히 추적되며 영구 보존됩니다.
4. **100% 한국어 유저 페이싱 (100% Natural Idiomatic Korean)**
   - 시스템 변수나 디버그 텍스트가 플레이어에게 노출되지 않으며, 모든 대화, 지문, 아이템명, 마법 고대어 발음(`바르`, `카르`, `이그니스`)은 자연스러운 한국어로 렌더링됩니다.

---

## 🗺️ 6계층 거시-미시 인프라 시스템 (Infrastructure Hierarchy)

Quilltale의 세계관은 단순 텍스트가 아니라 **수천 개의 정밀 JSON 템플릿과 2D 유클리드 기하학 그래프**로 실시간 조립됩니다:

- **Level 0 (세계관/우주 - Cosmology)**: 57종 우주론 템플릿 (`cosmology_templates.json`), 천문 주기, 마나 기원, 기년법 연도.
- **Level 1 (대륙 - Continent)**: 120종 대륙 템플릿 (`continent_templates.json`), 지질 판, 대륙 고유 공통어, 기상 전선, 인구/면적.
- **Level 2 (지리 권역 - Region)**: 304종 지리/기후 권역 (`region_templates.json`), 10대 지형, 자연 물가 지수, 최상위 포식자 생태계.
- **Level 3 (국가/영지 - Nation)**: 134종 국가 템플릿 (`nation_templates.json`), 정치 체제, 영토 국경선, 관세율, 고유 화폐, 국경 검문 관문.
- **Level 4 (정주지/마을 - Settlement)**: 215종 정주지 템플릿 (`settlement_templates.json`), 2D 좌표 `(X, Y)`, 광장 구조물, 지역 금기(`local_curses_and_taboos`), 역사적 원한, 은밀한 스캔들.
- **Level 5 (세부 시설 - Facility)**: 14종 상세 시설 아키타입 (`facility_templates.json`), 바닥 재질 소음, 방음 등급(dB), 침투 경로, 비밀 은닉처.

---

## ⚙️ 내장된 결정론적 시뮬레이션 엔진 (Deterministic Engines)

- **물리 은신 & 도청 엔진 (`StealthInfiltrationEngine`)**:
  - 룩스(lx) 거리 역제곱 감쇠에 따른 시야 식별.
  - 바닥 재질 음향 (양탄자 10dB ~ 깨진 유리 68dB) 및 4대 보법(`creeping_toe`, `running_sprint`), 민첩 관절 완충, 지면 미세 진동 감지.
  - 차폐 매질(문틈, 판자벽, 석벽) 음향 투과율 기반 실시간 도청 판정.
- **공격 물리 & 거리 매트릭스 엔진 (`AttackPhysicsEngine` & `CombatDistanceManager`)**:
  - 미터(m) 단위 상대 거리 5대 사거리 구간 (0~2m 초근접부터 51~150m+ 초장거리).
  - 6대 물리 공격 태그: 찌르기(관통 운동에너지), 베기(동맥 출혈), 타격(뼈 골절/저지력), 잽(선딜레이 인터럽트), 스트레이트(넉백), 사격(장력 비례 관통).
- **던전 붕괴 & 산소 고갈 엔진 (`CaveCollapseEngine`)**:
  - 5대 암반 지질(석회암, 화강암, 사암, 현무암, 흑요석) 내구도 역학.
  - 충격파 진동 전파 및 4단계 낙반 붕괴(안정 ➔ 균열 ➔ 부분 낙반 ➔ 전면 대붕괴).
  - 횃불 연소, 화염 마법, 호흡에 따른 밀폐 공간 산소 농도 감소 및 저산소증 질식.
- **날씨 & 체온 생존 물리 엔진 (`ThermalSurvivalEngine`)**:
  - 36.5℃ 심부 체온 역학, 젖음 수치(0~100%), 강풍 체감온도 배율.
  - 저체온증 4단계 (경도 ~ 심정지) 및 열사병 4단계, 모닥불 열역학 건조.
- **파티원 멘탈 붕괴 & 트라우마 엔진 (`PartySanityEngine`)**:
  - 15종 정신 붕괴/각성 스펙 (공황, 편집증, 이기주의, 절망, 광폭화, 각성 등).
  - 칠흑 어둠 체류, 아군 빈사, 혐오체 조우 스트레스 틱 및 전투 거부/패닉 도주.
- **몬스터 부위 파괴 & 해부학 채집 엔진 (`AnatomyHarvestEngine`)**:
  - 몬스터 부위별(머리, 다리, 꼬리) 육질 배율(Hitzone), 참격 절단, 부위 파괴 경직.
  - 전투 파손 페널티: 부위 파괴 시 잔해 열화, 급소 정밀 타격 시 온전한 최상급 소재 갈무리.
- **식량 부패 & 수면 부족 역학 (`RationSpoilageEngine` & `SleepDeprivationEngine`)**:
  - 보관 환경(온도, 습도, 소금 절임)에 따른 식량 유통기한 부패, 식중독.
  - 24시간 각성 주기, 각성제 복용 후 반동 수면 붕괴.
- **소문 확산 & 목격자 게이트 (`RumorDiffusionEngine`)**:
  - 가도 상단을 통한 지역 소문 전파.
  - 목격자가 없는 밀실/단독 암살 시 소문 확산 완전 차단 (완전 범죄 시스템).
- **2D 유클리드 도로망 다익스트라 최단 경로 (`GeographyEngine`)**:
  - 노면 상태, 도로 등급, 지형 마찰력을 반영한 Dijkstra 최단 경로 및 다중 경유지 자동 이동.

---

## 🧪 테스트 및 품질 보증 (DoD Gate)

Quilltale은 코드의 안정성을 위해 회귀 결함 0건 원칙을 엄격히 준수합니다.

```bash
# 전체 단위 테스트 실행 (544개 테스트 100% 무결점 통과)
python -m pytest tests/

# 20턴 자동화 시나리오 무효 전이율 검증
python eval_runner.py --no-judge
```

- **단위 테스트**: `544 passed` (0 failed)
- **무효 상태 전이율 (Invalid Transition Rate)**: `0.0%` 달성

---

## 🚀 로컬 실행 방법 (Running Locally)

### 1. 가상환경 세팅 및 의존성 설치
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. 환경 변수 설정 (`.env`)
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. 게임 실행
```bash
python app.py
```

---

## 📁 프로젝트 구조 (Repository Layout)

```
Quilltale/
├── src/
│   ├── world/
│   │   ├── state.py                      # WorldState, Location, Settlement, NPC, Player 모델
│   │   ├── infrastructure.py             # 6계층 거시-미시 인프라 로더 및 도로망 조립기
│   │   ├── stat_engine.py                # 7대 스탯, 정점 15 앵커링, 무한 서브스탯 엔진
│   │   ├── attack_physics_engine.py      # 물리 공격 역학, 사거리, 타격 부위 엔진
│   │   ├── stealth_engine.py             # 조도, 바닥 재질 데시벨, 도청 음향 엔진
│   │   ├── cave_in_engine.py             # 암반 지질, 진동 충격, 낙반 붕괴, 산소 고갈 엔진
│   │   ├── thermal_engine.py             # 심부 체온, 젖음, 저체온증/열사병 엔진
│   │   ├── party_sanity_engine.py        # 15종 파티원 멘탈 붕괴 & 스트레스 엔진
│   │   ├── harvest_engine.py             # 몬스터 부위 파괴 및 도축 해부 채집 엔진
│   │   ├── geography.py                  # 2D 유클리드 거리 및 다익스트라 최단 경로 탐색기
│   │   ├── weather_engine.py             # 동적 기상 전선 및 환경 틱 연동
│   │   ├── two_pass_engine.py            # Pass 1 결정론적 연산 & Pass 2 서사 통합 엔진
│   │   └── ...
│   ├── agents/
│   │   └── game_master.py                # Game Master LLM 오케스트레이터
│   └── llm/                              # Gemini / Claude 추상화 인터페이스
├── data/
│   ├── templates/                        # 1,000종 이상의 정밀 세계관/시설/몬스터 JSON
│   └── saves/                            # 세이브/로드 슬롯 데이터
├── tests/                                # 544개 자동화 테스트 스위트
├── app.py                                # Gradio UI 프론트엔드 (I/O 및 렌더링 전용)
└── eval_runner.py                        # 20턴 자동 평가 러너
```

