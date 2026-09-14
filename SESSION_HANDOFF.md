# Quilltale 프로젝트 세션 인수인계서 (Session Handoff)

> **[고정 규칙 1] 말투 규칙 (절대 수정/삭제 불가):**
> 1. 내부 연산같은거는 정상적으로 꼼꼼히 하지만, 유저에게 값을 출력해서 말해줄 때는, 토큰을 아끼기 위해 '우가' 같은 추임새를 뺀 원시인 말투로 고정한다.
>
> **[고정 규칙 2] 핸드오프 갱신 규칙 (절대 수정/삭제 불가):**
> 2. 매번 핸드오프 적으라고 할 때는 고정 규칙(하드웨어 스펙 포함) 및 [해야 할 일(Backlog)] 목록을 제외한, 다른 세부 수정 사항들만 삭제하고 새로 적는다.
>
> **[고정 규칙 3] 작업 환경 분리 규칙 (절대 수정/삭제 불가):**
> 3. 작업 환경에 따라 타겟을 분리한다. '집/노트북' 환경에서는 인게임 콘텐츠와 시스템 둘 다 다루고, '똥컴/학원' 환경에서는 시스템(내부 연산, 코드 구조, 로직 등)만 다룬다.
>
> **[고정 규칙 4] 백로그 삭제 금지 규칙 (절대 수정/삭제 불가):**
> 4. [해야 할 일(Backlog)] 삭제 금지 및 허락 규칙: 유저의 명시적 허락 없이 백로그를 임의로 지우지 못한다.
>
> **[고정 규칙 5] 중복 방지 및 기존 코드 우선 확인 규칙 (절대 수정/삭제 불가):**
> 5. 추가할 요소(클래스, 엔진, 템플릿, 기능 등)를 유저에게 제안하거나 백로그에 올릴 때, 이미 다른 파일에 관련 내용이나 유사 코드가 있는지 코드베이스를 철저히 사전 검색·확인한 후, 중복 신설 대신 기존 코드 확장/통합 여부를 먼저 유저에게 물어보고 보고한다.
>
> **[고정 규칙 6] 클래스 작성 시 요약 특성(traits) 의무 탑재 규칙 (절대 수정/삭제 불가):**
> 6. 월드/지리/정치/시설/개체 등 게임 내 주요 클래스 데이터 모델을 신설하거나 확장할 때, 플레이어 UI 요약, AI(GM) 서술 앵커링, 돌발 이벤트 판정에 사용될 `traits: List[str] = field(default_factory=list)`(요약 특성 태그 목록) 필드를 무조건 기본 탑재한다.
>
> **[고정 규칙 7] 제안/질의 시 구체적 설명 의무 탑재 규칙 (절대 수정/삭제 불가):**
> 7. 유저에게 무언가를 제안하거나 물어볼 때 대충 "~~할까?" 식으로 모호하게 묻지 말고, 그것이 시스템/게임플레이/코드상에서 구체적으로 무엇인지, 왜 필요한지 알아들을 수 있게 명확하고 짧은 설명을 반드시 덧붙여서 보고한다.
>
> **[고정 규칙 8] 외부 AI(GPT/Claude) 연동 및 프롬프트 제공 규칙 (절대 수정/삭제 불가):**
> 8. 유저 요청 작업 시 다음 3원칙을 준수한다:
>    - 1) 해야 할 작업은 외부 LLM(GPT/Claude 등)에 즉시 입력할 수 있는 구체적인 실행 프롬프트 형태로 제공한다.
>    - 2) 내부 연산이나 시스템 코드가 필요할 때는 완성형 코드가 아닌 명확한 인터페이스/뼈대(스켈레톤) 구조만 제공한다.
>    - 3) 세부 데이터 계산, 수치 연산, 방대한 데이터/콘텐츠 생성은 GPT나 Claude가 수행하도록 역할을 명확히 분담한다.
>
> **[고정 규칙 9] 리포지토리 청결 및 모듈 네이밍 중복 방지 규칙 (절대 수정/삭제 불가):**
> 9. 다음 3대 리포지토리 위생 및 코드 구조화 원칙을 철저히 준수한다:
>    - 1) scratch/ 폴더에 임시 패치/정규식 스크립트를 생성하거나 git에 커밋하지 않는다 (.gitignore 격리 및 즉시 삭제).
>    - 2) 단위 테스트 실행 시 `data/legacy/`나 `data/saves/` 등 실제 데이터 디렉터리에 더미 JSON 파일을 영구 누적하지 않도록 `tmp_path` 격리 또는 teardown 정리를 필수 적용한다.
>    - 3) 모듈 파일명 중복 금지: 서로 다른 디렉터리라도 동일한 파일명(`profiler.py` 등) 사용을 금지하며, 역할이 드러나는 고유 명칭(`combat_profiler.py` vs `engine/profiler.py`)을 부여한다.
>
> **[고정 규칙 10] 계단식 점진 통합 원칙 (Incremental Integration Gate / 절대 수정/삭제 불가):**
> 10. 신규 엔진 및 시스템 개발 시 일괄 결합(빅뱅 통합)으로 인한 의존성 폭발을 방지하기 위해 다음 3단계를 의무 준수한다:
>    - 1단계 (독립 완성 & 단위 테스트): 신규 엔진을 독립 모듈로 구현하고, 해당 엔진의 전용 단위 테스트(pytest >= 1개 이상)를 100% 통과시킨다.
>    - 2단계 (팩트시트 슬롯 연결): TwoPassEngine(Pass 1) 또는 GameMasterAgent에 해당 엔진의 결과를 수신할 슬롯(메서드/필드)을 1:1로 안전하게 연결한다.
>    - 3단계 (전체 회귀 검증): 기존 전체 테스트(BASELINE 이상)를 실행하여 단 1건의 결함/회귀도 발생하지 않음을 검증한 후 다음 백로그로 전진한다.

---

## 1. 프로젝트 기본 정보
- **엔진명**: Quilltale TRPG Engine
- **개발 언어 및 환경**: Python 3.13 / Windows 11
- **핵심 아키텍처**:
  - 100% 결정론적 연산 (Python Engine) + 로컬 RAG (Qdrant + Jina BGE-M3 1024-dim) + Two-Pass LLM 검증기 (Gemini API)
  - Anti-Yes-Man reality check & 100% 한국어 유저 페이싱 인터페이스

---

## 2. 하드웨어 스펙 & 모델 스펙 고정 기록

### [집/노트북 환경 스펙]
- **CPU**: AMD Ryzen 7 8845HS (8C/16T, up to 5.1GHz)
- **RAM**: 32GB DDR5 5600MHz
- **GPU**: NVIDIA GeForce RTX 4060 Laptop (8GB VRAM)
- **AI 로컬 구동 가능 범위**:
  - SD 1.5 이미지 생성 (LoRA 및 ADetailer 고속 가동)
  - 로컬 고성능 임베딩 모델 (BAAI/bge-m3 1024-dim)
  - TTS 한국어 음성 모델 (Edge-TTS / Kokoro)
  - 경량 LLM 로컬 서빙 (Qwen-2.5-7B-Instruct / EXL2 4-bit)

### [학원/똥컴 환경 스펙]
- **CPU**: 인텔 4코어 구형 사무용 CPU
- **RAM**: 8GB DDR3/DDR4
- **GPU**: 내장 그래픽 (VRAM 없음)
- **AI 구동 제약**: 로컬 무거운 모델 구동 불가, 순수 Gemini API 호출 및 파이썬 내부 연산/코드 작업만 집중.

---

## 3. [해야 할 일(Backlog)]

### [집/노트북 환경 — SD 1.5 이미지/LoRA & GUI 연동 고도화]
- [ ] **🔥 [신규 백로그 - UI/그래픽] LoRA SD 1.5 기반 실시간 동적 부분 갱신 이중 맵 이미지 시스템 (`DynamicDualMapRenderer`)**:
  - **구현 내용**:
    - 1. 세계관 생성 시 LoRA SD 1.5 모델로 2D 유클리드 도로 그래프 기반 전체 대륙/권역 지도를 고화질 렌더링.
    - 2. 이중 이미지 UI 구조: 기존 서사/인물 메인 뷰 + 버튼 클릭 시 독립 토글/팝업되는 맵 전용 이미지 뷰.
    - 3. 도로/지형 부분 실시간 갱신: 플레이어 이동(a마을 -> b마을) 또는 대규모 거시 지형 지각변동 발생 시, 전체 재생성 없이 해당 도로 구간/지형 파편만 정밀 연산 및 Masking Inpaint로 부분 갱신.
    - 4. 이동 틱 오버레이: 도로 길이, 이동 속도, 플레이어 현재 위치 핀을 지도 상에 실시간 추적 갱신.
- [ ] **🔥 [신규 백로그 - UI/플랫폼] 스팀 게임 스타일 독립 실행형 창 모드 런처 (`SteamStyleStandaloneLauncher`)**:
  - **구현 내용**:
    - 웹브라우저(Gradio Web GUI) 접속 방식 전면 탈피.
    - 스팀 패키지 게임처럼 클릭 시 브라우저 주소창/주변 프레임이 없는 전용 스탠드얼론 GUI 창(PyWebView/Electron 기반)으로 게임이 즉시 구동되는 앱 구조 전환.
- [ ] **💡 [아키텍처 원칙 - 그래픽] HD-2D(옥토패스 스타일) 2D-3D 렌더링 파이프라인 연동 설계**:
  - **핵심 원칙**: LLM 줄글 텍스트를 보고 그림을 그리는 것 절대 금지 (일관성 붕괴/환각 방지). `WorldState` 구조체 데이터를 단일 진실 원천으로 삼아 그래픽 엔진(Godot/Unity/Three.js)과 LLM이 각각 독립 소비.
  - **1) 좌표 및 노드-엣지**: 씬 그래프(Scene Graph) 및 레벨 배치도 담당 (월드맵 도로망, 마을/실내 그리드, 문 위치, 캐릭터 스폰 좌표).
  - **2) 장비/인물 외형**: `ItemVisualProfile`(칼날/코등이/오라), `NPCVisualDetails`(이목구비/체형), `ClothingLayer`(속옷/이너/외투) 기반 **모듈러 도트(Paperdoll)** 파츠 레이어 조립.
  - **3) 건물/실내 외형**: `Facility`/`Location`의 `architecture_style`(석조/목조), `materials` 타일셋 매핑 + `furniture` 프리팹 스폰 + `lighting_lux` 포인트 라이트 음영 처리(절차적 타일 조립).
  - **4) 몬스터 부위**: `MonsterPart` 모듈러 스프라이트 분리 렌더링 (꼬리 절단 시 해당 부위 스프라이트 OFF 및 필드에 피 묻은 절단 잔해 도트 투하).

### [똥컴/학원 환경 — 순수 시스템/로직/엔진 고도화]
- [x] **🔥 [긴급 0순위] 클린업 커밋 버그 수정 및 ATOMIC 커밋 룰 준수 강화**:
  - **발생 문제**: 
    1. `state.py`의 `Optional` import 누락으로 인해 앱 전체 크래시(`NameError: name 'Optional' is not defined`) 발생. (pytest 및 eval_runner가 이로 인해 실패했으나 잘못 보고됨)
    2. 이전 "클린업" 커밋에 신규 기능(`PowerScalePreset`, 다익스트라 경로 등)이 몰래 포함되어 `<Scope_Commit>`의 ATOMIC 원칙 훼손.
  - **해결 내역**:
    1. `state.py` L9에 `Optional` 추가.
    2. 커밋 전 `pyflakes`로 코드베이스 전체 undefined name 검사 수행 (`outfit_engine.py`의 `random` 누락 건도 추가 조치).
    3. `pytest`를 다시 실행해 진짜 545 passed 검증.
    4. 이후 작업 시 반드시 "1 session = 1 task only" 원칙을 엄수해 커밋 분리할 것.
- [x] **🔥 [완료] 6계층 거시-미시 현실 인프라 뼈대 시스템 (Level 0 ~ Level 5)**:
  - **구현 대상**: [아키텍처 전면 개편] `src/world/infrastructure.py`, `src/world/state.py`, `generator.py`, `geography.py`
  - **계층 구조 설계**:
    - **Level 0 (세계관/행성 - Cosmology/World)**: 천문 주기, 마나 기원, 신성 조약, 시대 배경 (`cosmology_templates.json` 57종 연동).
    - **Level 1 (대륙 - Continent)**: 거대 판/대륙 단위 (지형 플레이트, 고유 공통어, 대륙 단위 기상 전선).
    - **Level 2 (지리/기후 권역 - Region)**: 사막, 바다, 만년설 산맥, 맹독 늪 등 30대 환경 권역 (`region_templates.json` 연동, 자연 물가/자원 매트릭스).
    - **Level 3 (국가/영지 - Nation/Fiefdom)**: 정치 체제(왕정/공화정/군정), 영토 국경선, 국경 검문소(밀수 검사), 관세율, 고유 법률/화폐, 파벌 적대 관계.
    - **Level 4 (정주지/마을 - Settlement)**: 수도 성도, 요새 도시, 농경 마을, 광산 정착촌, 유목민 야영지 (지도 2D 좌표, 치안도, 인구 규모, 방어 시설, 도로망 노드).
    - **Level 5 (세부 인프라/시설 - Facility/Node)**: 시장/상점, 대장간/공방, 아카데미/학교/도장, 신전/사원, 주점/여관, 수문/관문, 지하 하수도/던전 (실제 NPC, 아이템, 서비스, 물리 상호작용).
  - **5단계 순차 실행 로드맵**:
    - [x] **1단계: 5대 계층 고밀도 데이터 클래스 정의 및 스키마 정제 (1-1 ~ 1-5 완료)**:
      - [x] **1-1. 세계관(Level 0) & 대륙(Level 1)**: 전 우주 고대어 체계 및 마나 기원(Level 0 `WorldState`) + 대륙 공통어, 지질 판, 기상 전선, 인구(`population`), 면적(`area_sq_km`)(`Continent`).
      - [x] **1-2. 지리/기후 권역(Level 2)**: 10대 지형, 4계절 기후대, 자연 자원 물가(0.3x~5.0x), 인구, 면적, 천연 특산품(`specialties`), 환경 위험, 시야/소음 차폐(`Region`).
      - [x] **1-3. 국가/영지(Level 3)**: 정치 체제, 영토 경계, 공식 화폐/환율, 관세율(0~50%), 국경 검문소(통행증/밀수), 법률/금기, 인구, 면적, 국가 특산품(`specialties`), 외교 관계(`Nation`).
      - [x] **1-4. 정주지/마을(Level 4)**: 정주지 등급/격(수도/요새/농촌/광산/항구), 2D 좌표, 인구, 행정 면적, 종족비, 치안도, 성벽 등급, 도로망, 식량/식수 자급율, 위생도, 향토 특산품(`specialties`), 중앙 광장 시설물, 성문·해자, 마구간, 물레방아/풍차, 방화수조, 검역소, 지하 하수망, 방목지(`Settlement`).
    - [x] **2단계: 상위 레이어(0~2층) 템플릿 연동**: 총 120종 대륙 템플릿 완비(`continent_templates.json`: 동양/선협/무협/괴담/신선 및 다크 판타지 등 전 120종 대륙 최강자/최강 몬스터 스케치 및 ID 포인터 전면 탑재) + `cosmology_templates.json`(57종) 및 `region_templates.json`(목표 300종 전격 돌파 총 304종 완비)을 `InfrastructureTemplateLoader`로 정밀 매핑/결합 완료.
    - [x] **3단계: 중간 레이어(3~4층) 국가/마을 영토 매핑 완비**: 국가별 정주지 귀속 바인딩 + 2D 유클리드 좌표 기반 결정론적 도로망(`assemble_settlement_roads`) 자동 연결(쌍방향 대칭, 도로 등급/특성/통행료) + 국경 관문 검문소(`border_checkpoints`) 및 대륙 간/국가 간 간선 가도(`international_highways`) 자동 등록 + 상하향식 인구/면적 총합 재계산(`recalculate_totals`) 완비.
    - [x] **4단계: 하위 레이어(5층) 마을 내 인프라 배치 완비**: 14종 시설 유형(`FacilityType`) 전 종목 아키타입 템플릿(`facility_templates.json`) 신설 + 정주지 유형별/규모별 3~10종 시설 결정론적 자동 슬롯화(`assemble_settlement_facilities`) + 정주지 상업/수련/길드 목록 자동 분류 및 O(1) 계층 역추적/관세 연동 완비.
    - [x] **5단계: [최종] 전 계층 수직 통합 검수 (End-to-End 완료)**: 시설에서 마을 ➔ 국가(관세) ➔ 권역(자연 물가) ➔ 대륙(언어) ➔ 세계관(마나)까지 상하향식 연동 100% 통합 단위 테스트 및 WorldState 직렬화/역직렬화 완비.
  - **작업 원칙**: 다른 백로그 전면 중단하고, 1단계부터 5단계까지 순차적으로 100% 완료한 후 다음 백로그 진행.
- [x] **🔥 [완료 0.5순위] 월드 엔티티(배우 & 소품) 인프라 연동 시스템 (NPC, Item, Skill, Monster, Quest)**:
  - **구현 대상**: [연동 파이프라인] `src/world/infrastructure.py`, `src/world/state.py`, `src/world/quest_engine.py`
  - **세부 연동 항목**:
    - [x] 1. **NPC & 종족 인프라 배치**: 4계층 마을 인구/종족비 및 5계층 시설(상점, 대장간, 주점)에 상주 NPC 자동 스폰 및 직책(영주/국왕/거상) ID 바인딩 (`bind_settlement_npcs`).
    - [x] 2. **Item & 장비 상점/루팅 연동**: 2계층 권역 특산물 및 5계층 시설 유형(`facility_type`)에 맞는 상점 재고 진열(`items`), 실시간 관세/물가 배율 적용 (`bind_facility_inventories`).
    - [x] 3. **Skill & 마법 훈련 연동**: 5계층 훈련장/마탑(`training_ground`, `mage_tower_academy`) 제공 스킬/고대어 연동 및 마나 밀도 기반 시전 환경 결합 (`bind_training_facilities`).
    - [x] 4. **Monster & 포식자 생태계 연동**: 2계층 권역 최상위 포식자(`apex_predator_id`) 및 4계층 외곽 마수 침식도(`monster_infestation_index`) 스폰 테이블 연동 (`bind_region_monsters`, `spawn_monster_from_template`).
    - [x] 5. **Quest & 사건 나비효과 연동**: 4계층 마을 공고판(`town_square_features`) 현상수배/의뢰 및 역사적 원한(`historical_grievances`) 퀘스트화 (`bind_settlement_quests`).
    - [x] 6. **Master Pipeline**: `InfrastructureTemplateLoader.bind_world_entities()` 및 `assemble_full_world(..., bind_entities=True)` 완비.
- [x] **🔥 [완료] 현실 물리 전투 거리·액션 타임트랙 & 스탯·인지·역법 통합 엔진 (Calendar, Turn & Combat Physics Engine)**:
  - **구현 대상**: `src/world/state.py`, `src/world/stat_engine.py`, `src/world/attack_physics_engine.py`, `src/world/combat_time_track_engine.py`, `src/world/time_calendar_engine.py`
  - **구현 완료 기능**:
    - [x] 1. `start_year` 랜덤 및 세계관 기년법 자율화 (`calendar_epoch_name`, 1~3000년 시드 연도).
    - [x] 2. 촘촘한 일상 15종 가변 시간 매트릭스 (`DAILY_ACTION_DURATIONS`, 잠입 15~30분, 연구 60~180분, 요리 30~60분 등).
    - [x] 3. 인간계 정점 스탯 15 기준 앵커링 (민첩 15=우사인 볼트 10.5m/s, 근력 15=장궁 150 lbs 완발, 지혜 15=영창 50% 단축).
    - [x] 4. 무한 확장 서브스탯 딕셔너리 (`sub_stats: Dict[str, float]`) 및 레벨업 경험치 곡선 (\(100 \times L^{1.5}\)) + 스탯 포인트 3점 지급.
    - [x] 5. 미터(m) 단위 상대 거리 매트릭스 (`distances`) & 초장거리(51~150m+) 5대 사거리 구간 (`CombatDistanceManager`).
    - [x] 6. 태그 기반 물리 공격 엔진 (`AttackPhysicsEngine`: `thrust` 가속도 운동에너지, `slash` 출혈, `blunt` 뼈 골절/저지력, `jab` 0.15초 캔슬, `straight` 넉백, `projectile` 장력 판정).
    - [x] 7. [A안 인지 엔진 기반] 리액션 인터럽트 트리거 (`PerceptionEngine`, `ActionTimeTrackEngine`: 위협 인지 시에만 턴 정지/반응 기회 부여, 미인지 시 기습 직격).
    - [x] 8. 시간 경과 나비효과 (조도 전환, 기온 보정, 22시 상점 문 닫음).
    - [x] 9. 세이브/로드 역직렬화 100% 하위 호환성 유지.
- [x] **1. 🔥 [완료] 물리적 은신/잠입/도청 엔진 (`StealthInfiltrationEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/stealth_engine.py`
  - **구현 완료 기능**:
    - [x] 1. 조도(Lighting lx) 역학: 룩스(lx) 거리 역제곱 감쇠 및 암흑(DC +8)부터 횃불 정면(DC -6) 육안 식별.
    - [x] 2. 바닥 재질 음향(dB): 양탄자(10dB), 진흙(20dB), 석판(28dB), 삐걱 목재(48dB), 깨진 유리(68dB).
    - [x] 3. [유저 피드백] 4대 보행 보법(`creeping_toe` -20dB, `running_sprint` +28dB) 및 민첩(AGI 15) 관절 완충 상쇄(-14dB).
    - [x] 4. [유저 피드백] 배경 소음 마스킹 시 [지면 미세 진동(Micro-Vibration)] 감지 (발소리가 묻혀도 발바닥 진동으로 기척 간파).
    - [x] 5. 풍향(풍상/풍하) 및 위생도 저하/피비린내 체취 분자 확산 판정.
    - [x] 6. 차폐 매질(문틈 8dB, 판자벽 15dB, 원목문 25dB, 석벽 45dB) 투과율 기반 도청(`evaluate_eavesdropping`) 및 비밀 청취.
- [x] **🔥 [완료] 세계관별 성장 스케일 프리셋 시스템 (`WorldPowerScalePresets`)**:
  - **구현 대상**: `src/world/stat_engine.py`, `src/world/state.py`, `src/world/infrastructure.py`, `src/world/generator.py`, `src/world/two_pass_engine.py`, `data/templates/cosmology_templates.json`, `tests/test_power_scale_presets.py`
  - **기능**: 세계관마다 다른 레벨 상한 및 스탯 성장률 프리셋 결합:
    - 1. 로우 판타지(발더게3형): 최대 16렙, 렙당 스탯 1개, 상한 30, 대미지 배율 1.0x.
    - 2. 스탠다드 판타지(D&D형): 최대 50렙, 렙당 스탯 3개, 상한 100, 대미지 배율 1.5x.
    - 3. 하이퍼 인플레(메이플형): 최대 300렙, 렙당 스탯 5개, 상한 99999, 대미지 배율 50.0x.
    - 4. 선협/무협(경지 돌파형): 평소 렙업 없음, 경지 돌파 시 스탯 10배 폭증 및 10대 대경지 명칭 자동 부여.
- [x] **2. 🔥 [완료] 몬스터 부위 파괴 & 특수 소재 채집 엔진 (`AnatomyHarvestEngine`) & 장비 세트 효과 시스템**:
  - **구현 대상**: [엔진: 신규] `src/world/harvest_engine.py`, [엔진: 확장] `src/world/equipment.py`, `src/world/state.py`
  - **구현 완료 기능**:
    - [x] 1. 몬스터 부위 모델(`MonsterPart`): 참격/타격/사격 육질 배율(Hitzone), 절단 가능(severable), 파괴 임계치.
    - [x] 2. 부위 조준 타격(`attack_targeted_part`): 부위 파괴 시 경직(Stagger) 유발 및 특수 기믹 무력화.
    - [x] 3. 꼬리 참격 절단(`severable + slash`): 절단 시 바닥에 신체 잔해 아이템 직접 드랍 및 필드 즉시 갈무리 지원.
    - [x] 4. [유저 피드백] 모바일 가챠 확률표/3회 제한 전면 제거 -> 현실적 해부학 도축/갈무리.
    - [x] 5. [유저 피드백] 부위 파괴 손상 페널티: 전투 중 박살 난 부위 갈무리 시 50% 확률로 짓이겨져 저급 파편으로 열화, 온전하게 약점 찔러 처치 시 100% 최상급 완제품 수확.
    - [x] 6. [유저 피드백] 일반 희귀 장비 세트 효과 확장:
      - 왕실 근위대 세트(2세트: 방어+6/체력+2/경직저항, 4세트: 방어+16/근력+3/체력+5/넉백완전면역).
      - 그림자 암살자 세트(2세트: 민첩+3/치명+5%/발소리-10dB, 4세트: 민첩+7/치명피해+25%/기습추가타).
      - 고대 비전 학자 세트(2세트: 지능+4/마나+30/마력회복, 4세트: 지능+10/지혜+5/영창-30%/마나-20%).
      - 강철벽 검투사 세트, 엘프 순찰대 세트.
    - [x] 7. 몬스터 소재 장비 세트 효과 (뇌격 흑액 메기 세트, 공포의 비룡 세트, 심해 갑각수 세트).
    - [x] 8. 도축 단검 내구도 소모 및 세이브/로드 100% 하위 호환성 검증 (338/338 테스트 패스).
- [x] **3. 🔥 [완료] 함정 해체 & 공학 퍼즐 물리 엔진 (`TrapEngine`) 및 던전 탐험 계층 엔진 (`DungeonEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/trap_engine.py`, `src/world/dungeon_engine.py`, `src/world/state.py`
  - **기능**:
    - 1. 지상(숲/산악/늪/가도/도시), 던전(천장압축/독가스/벽석궁/마력룬), 히든맵(공간왜곡/심연착란/생명갈취) 3대 맵 컨셉형 함정 분리 탑재.
    - 2. 지각(Perception) 함정 탐색, 민첩/지능 및 도적 도구(`thieves_tools`) 소모 해체, 실패 시 즉시 격발.
    - 3. 회피 세이빙 스로우, 피해/상태이상(출혈, 독, 기절 등), 소음(dB) 발생 어그로.
    - 4. 다층 지하 던전 인스턴스(B1F~B5F) 심도 스케일링(위험도 25~90, 몬스터 밀집도 40~95%, NPC 밀집도 0 수렴, 산소 농도 저하, 칠흑 어둠).
- [x] **4. 🔥 [완료] 파티원 멘탈 붕괴 & 트라우마 엔진 (`PartySanityEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/party_sanity_engine.py`, [엔진: 확장] `src/world/party_engine.py`, `src/world/two_pass_engine.py`
  - **기능**:
    - 1. 15종 멘탈 붕괴/각성 스펙(`MentalBreakdownSpec`): 공황(Panic), 편집증(Paranoia), 이기주의(Selfishness), 절망(Hopelessness), 각성(Awakening), 해리(Dissociation), 광폭화(Rage), 얼어붙음(Freeze), 강박(Obsession), 퇴행(Regression), 도주 본능(Flight Instinct), 생존자 죄책감(Survivor's Guilt), 파괴 충동(Destructive Impulse), 감정 폐쇄(Emotional Shutdown), 허세(False Confidence).
    - 2. 5대 스트레스 트리거: 칠흑 어둠 장기 체류(+2/턴), 동료/플레이어 빈사 목격(+15), 혐오체/미지의 존재 조우(+10), 함정 및 치명타 피격(+8/+12), 식량/식수 고갈.
    - 3. 8대 성향별 가중치 테이블(`PERSONALITY_BREAKDOWN_WEIGHTS`): 용감(brave), 비겁(cowardly), 충직(loyal), 이기적(selfish), 의심(suspicious), 이상주의(idealistic), 생존주의(survivalist), 냉철(stoic).
    - 4. 턴 틱 스트레스 검사(`process_turn_sanity`), 붕괴 시 전투 행동 거부/아군 공격/자해/방어 태세/패닉 도주 연동(`filter_companion_combat_intent`).
    - 5. 규칙 6 준수: `MentalBreakdownSpec` 및 `Companion`에 `traits` 필드 의무 탑재.
- [x] **5. 🔥 [완료] 날씨·체온 저체온증/열사병 생존 물리 엔진 (`ThermalSurvivalEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/thermal_engine.py`, [엔진: 확장] `src/world/weather_engine.py`, `src/world/state.py`
  - **기능**:
    - 1. 인체 열평형 심부 체온(36.5℃ 기본값) 및 젖음 수치(`wetness`, 0~100%) 물리 역학.
    - 2. 방한/방열 장비 보온 지수 4종(`fur_coat` +8.0/30%방수, `oilskin_cloak` +3.0/100%방수, `heavy_plate` -3.0/냉기전도/폭염열축적 1.5배, `linen_tunic` 통기/방열 10).
    - 3. 젖음 수치별 열손실 배율(50% 이상 3배, 75% 이상 5배) 및 강풍 체감온도 배율(산들바람 1.2배, 강풍 1.8배, 폭풍 3.0배).
    - 4. 저체온증 4단계: 경도(35.0~35.9℃, 민첩 -2, 조준 -3), 중등도(33.0~34.9℃, 지속피해 4, 영창실패 25%), 중증(30.0~32.9℃, 지속피해 8, 이동속도 50%), 치명(30.0℃ 미만, 지속피해 20, 심정지/행동불가).
    - 5. 열사병 4단계: 열탈진(37.5~38.4℃, 갈증, 기력소모 1.5배), 열경련(38.5~39.4℃, 근력/민첩 -3), 열사병(39.5~40.4℃, 지속피해 6, 피로도 +10, 발한정지), 다발성 장기부전(40.5℃ 이상, 뇌손상, 지속피해 15, 피로도 +15).
    - 6. 생존 모닥불(`light_campfire`): 점화 즉시 건조 15%, 턴당 건조 10%, 체온 정상화 회복(+0.5℃/턴).
    - 7. `WeatherEngine.process_turn_survival_ticks` 위임 연동으로 매 턴 자연스러운 생존 틱 가동.
    - 8. 규칙 6 준수: `ThermalClothingSpec`, `HypothermiaStageSpec`, `HyperthermiaStageSpec`에 `traits` 의무 탑재.
- [ ] **🔥 [템플릿 확충 6] 방한/방열/방수 생존 의복 및 장비 템플릿 확충 (현재 4종 ➔ 목표 20종)**:
  - **필요 사유**: 전 대륙 120종 및 304대 권역(극지방, 빙하, 사막, 열대우림, 화산, 고산지대 등)의 기후 생존 장비 다양성 확보 부족.
  - **확충 대상(16종)**: 극지방 물개 가죽 부츠, 순록 가죽 방한 파카, 양모 덧옷, 방풍 가죽 비니, 사막 베두인 로브, 흑요석 단열 갑주, 밀랍 방수 판초, 설산 아이젠 장화, 깃털 방한 조끼, 냉각 실크 내의, 용비늘 내화 흉갑, 서리늑대 털망토, 은박 단열 담요 등.
- [ ] **🔥 [템플릿 확충 7] 생존 열원 및 조리/건조 시설 템플릿 확충 (현재 2종 ➔ 목표 10종)**:
  - **필요 사유**: 동굴, 던전, 야영지, 극한지 생존 상황별 체온 회복 및 건조 수단 다양화 부족.
  - **확충 대상(8종)**: 휴대용 발열석/마나 화로, 화로대, 벽난로, 온천/지열 분출구, 기름 램프, 방열 룬 토템, 용암 지열 바위 등.
- [ ] **🔥 [템플릿 확충 8] 기상 물리 및 극한 환경 재해 템플릿 확충 (현재 2종 ➔ 목표 15종)**:
  - **필요 사유**: 강풍/강우 외에 습도/곰팡이, 낙뢰 전도, 기압/고도 등 현실 물리 생존 요소 심화.
  - **확충 대상(13종)**: 고산 저기압 고산병, 고습도 식량 곰팡이 부패, 폭풍우 금속 무구 낙뢰 감전, 황사/모래폭풍 호흡 곤란, 방사능 낙진 오염, 냉기 안개(동상 안개), 산성비 장비 부식 등.
- [x] **6. 🔥 [완료] 던전 구조적 붕괴 & 산소 고갈 질식 엔진 (`CaveCollapseEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/cave_in_engine.py`, [엔진: 확장] `src/world/dungeon_engine.py`, `src/world/state.py`, `src/world/two_pass_engine.py`
  - **기능**:
    - 1. 5대 암반 지질(`rock_strata`): 석회암, 화강암, 사암, 현무암, 흑요석(마력 취약 2.0x).
    - 2. 충격 진동원(`vibration_sources`): 화염구 폭발, 대형 둔기 강타, 굴착 곡괭이, 대형 함정 격발.
    - 3. 낙반 붕괴 4단계(`collapse_stages`): 안정(내구 70+), 천장 균열(40~69, 흙먼지/조도저하/1d4 피해), 부분 낙반(15~39, 낙석/민첩 DC 15 회피 세이빙), 전면 대붕괴(15 미만, 40 매몰 피해/통로 차단).
    - 4. 밀폐 공간 산소 농도 역학(`oxygen_dynamics`): 성인 호흡(-0.2/턴), 횃불 연소(-1.0/턴), 화염 마법(-5.0/시전), 환기구 개방(+2.0/턴), 4단계 저산소증(경도 70~80, 중등도 50~69, 중증 30~49, 질식 0~29).
    - 5. 5대 던전 환경 물리 시스템 결합: 독성 가스(`TOXIC_GAS_SYSTEM` 4종), 지하수 수질(`UNDERGROUND_WATER_SYSTEM` 5종 및 정화법), 가시거리 광원(`DUNGEON_VISIBILITY_SYSTEM`), 소음 메아리(`DUNGEON_SOUND_SYSTEM`), 지면 붕괴 위험(`FLOOR_HAZARD_SYSTEM` 5종).
    - 6. 규칙 6 준수: 모든 스펙 데이터클래스에 `traits` 필드 의무 탑재.
- [ ] **🔥 [템플릿 확충 1] 던전 지질 암반(Rock Strata) 템플릿 확충 (현재 5종 ➔ 목표 20종)**:
  - **필요 사유**: 전 대륙 120종 및 304대 지리 권역의 다양한 동굴 환경(광산, 화산동굴, 심연, 수정동굴 등) 표현 부족.
  - **확충 대상(15종)**: 편마암, 백운암, 천매암, 응회암, 점판암, 대리석, 감람암, 석탄/가스층, 마나 수정암, 빙하 암반, 혈석암, 성유물 석회석, 유문암, 안산암, 점토 이암 등.
- [ ] **🔥 [템플릿 확충 2] 진동 및 충격 발생원(Vibration Sources) 템플릿 확충 (현재 4종 ➔ 목표 15종)**:
  - **필요 사유**: 마법 및 전투 기믹 다양화(음파 마법, 지진 룬, 마수 돌진 등).
  - **확충 대상(11종)**: 음파 공명 주문, 지진 충격파, 대형 마수 돌진, 굴착 발파 폭약, 지하 수맥 범람 수압, 텔레포트 좌표 파열, 거신 강타 등.
- [ ] **🔥 [템플릿 확충 3] 독성 가스 및 대기 오염(Toxic Gas) 템플릿 확충 (현재 4종 ➔ 목표 12종)**:
  - **필요 사유**: 지하 밀폐 공간 생존 긴장감 극대화.
  - **확충 대상(8종)**: 일산화탄소, 메탄 폭발 가스, 청산 가스, 산성 증기, 마나 과포화 에테르 증기, 신경 마비 포자, 방사성 라돈 가스 등.
- [ ] **🔥 [템플릿 확충 4] 지하수 수질 및 오염원(Underground Water) 템플릿 확충 (현재 5종 ➔ 목표 12종)**:
  - **필요 사유**: 식수 자원 관리 및 생존 무게 강화.
  - **확충 대상(7종)**: 석회 탄산수, 마나 농축 영액, 방사성 폐수, 맹독 조류수, 부식성 산성 침출수, 성수 샘 등.
- [ ] **🔥 [템플릿 확충 5] 지면 붕괴 및 발판 위험(Floor Hazard) 템플릿 확충 (현재 5종 ➔ 목표 12종)**:
  - **필요 사유**: 전투 및 이동 시 지형 전술 요소 부여.
  - **확충 대상(7종)**: 진흙 뻘/수렁, 불안정한 너덜지대 자갈, 기름 유출 미끄럼 바닥, 삭은 철판 그레이팅, 마력 결정 가시밭, 뼈 무더기 바닥 등.
- [x] **7. 🔥 [완료] 전염병·역병·기생충 감염 생체 엔진 (`EpidemicEngine`) & 현실적 가방 용량/찢어짐 및 스킬 외형 연출**:
  - **구현 대상**: [엔진: 신규] `src/world/disease_engine.py`, [엔진: 확장] `src/world/outfit_engine.py`, `src/world/state.py`, `src/world/two_pass_engine.py`
  - **기능**:
    - 1. 6대 역병/기생충 스펙(`EPIDEMIC_SYSTEM`): 흑사병(`black_plague`), 오염수 이질(`dysentery`), 시체독 부패열(`corpse_decay_fever`), 지하 진균 포자증(`cave_spore_mycosis`), 흡혈 거머리 기생충(`blood_leech_parasite`), 광견병·마수 광란증(`rabies_madness`).
    - 2. 체질(CON) 세이빙 스로우(d20+CON vs DC), 대성공(완전 면역), 대실패(즉시 1단계 발병), 다중 노출(DC+2), 면역 저하(DC+2), 침구 공유(DC+4).
    - 3. 잠복기 카운트다운 및 3단계 발병 진행: 지속 피해, 기력 상한 감소, 진균 기침 발작 은신 해제(소음 45dB 방출), 광견병 신경 발작 아군 난투.
    - 4. 4대 치료 요법: 약초 달인물/연고(단계 완화), 알코올 소독(초기/외상 사멸), 신성 정화(완치), 환부 소작(잠복기 3턴 이내 화염/달군 칼 절제, 피해 8, 스트레스 +20).
    - 5. 격리 및 방역: 방역 마스크(비말 50% 차단), 격리실(80% 차단), 시체 소각(시체 매개 전파 영구 차단).
    - 6. 현실적 가방 3종 규격: 소형 전술 배낭(18L, 12kg 안전, 18kg 파손한계), 중형 여행자 배낭(40L, 25kg 안전, 35kg 파손한계), 육군 완전군장 대형 배낭(75L, 45kg 안전, 60kg 파손한계).
    - 7. 가방 용적(L) 초과 팽창 및 파손한계 초과 시 격렬한 행동(전력질주, 회피, 피격) 중 가방 찢어짐(바닥에 소지품 드랍).
    - 8. 스킬 외형 연출 엔진: 물리(회색·은색·백색 궤적 + 마나 주입 시 시전자 마나색), 마나/원소(속성색 + 시전자 고유 마나 혼합), 흑마법(무조건 칠흑빛/흑색), 혈마법(무조건 선홍빛/빨간색).
    - 9. 규칙 6 준수: `DiseaseSpec`, `DiseaseStageSpec`, `ActiveInfection`, `BackpackSpec`, `BackpackStorageStatus` 전원 `traits` 탑재.
- [ ] **🔥 [템플릿 확충 9] 역병·질병·기생충 템플릿 확충 (현재 6종 ➔ 목표 20종)**:
  - **필요 사유**: 전 대륙 120종 및 304대 권역(열대우림 풍토병, 혹한지 동사괴저, 사막 열사병 열병, 심연 에테르 변이증 등) 표현 부족.
  - **확충 대상(14종)**: 말라리아 풍토열, 백일해/결핵, 괴혈병, 파상풍, 흑색 탄저병, 마나 중독증, 에테르 종양 변이, 수면병(체체파리), 뇌수 기생 버섯, 괴사성 근막염, 썩은 폐렴, 황달 간독증, 흡혈 진드기 마비증, 심연 환각열 등.
- [ ] **🔥 [템플릿 확충 10] 생존 의약품·약초·치료 도구 템플릿 확충 (현재 4종 ➔ 목표 15종)**:
  - **필요 사유**: 야생 채집 및 응급 야전 치료 수단 다양화 부족.
  - **확충 대상(11종)**: 부목/압박붕대, 거머리 사혈 키트, 은침 봉합 도구, 수면 마취 아편, 훈증 마스크 필터, 활성탄 해독제, 지혈 이끼 가루, 해열 버들껍질 즙, 구충 마늘 정유, 항생 곰팡이 엑기스, 흑사병 새부리 방역 가면 등.
- [x] **8. 🔥 [완료] 마나 과부하 폭주 & 에테르 오염 변이 엔진 (`ManaBurnEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/mana_burn_engine.py`, [엔진: 확장] `src/world/state.py`
  - **구현 완료 기능**:
    - 1. 마나 회로 손상 상태 모델(`ManaCircuitState`): 회로 건전도(`vein_integrity_pct`), 누적 흉터(`scarred_veins`), 최대 MP 상한 영구 감소(`max_mp_penalty`), 과열 영창 불가 침묵(`burnout_turns`), 시전 시 신경통 기력 소모.
    - 2. 부족 마나 생명력(HP) 연소 과충전(`evaluate_overchannel`): 유저 규칙에 따라 일반 마법사는 엄격히 차단, 오직 대가 마법/흑마법/혈마법 지식 보유자만 생명력을 태워 마나로 치환 허용.
    - 3. 마나 폭주(`trigger_mana_backlash`): 시전자 회로 파열 및 직접 HP 피해, 주변 동료/적 에테르 역류 충격파 방출, 에테르 오염도 급증.
    - 4. 8대 에테르 변이 스펙(`ETHER_MUTATIONS_REGISTRY`): 이중성(혜택과 페널티 공존) 완비 (수정질 외피, 마력 누출 오라, 비전 갈증, 성간 열화, 유리 골격, 에테르 동공 개안, 혈맥 마나 도관, 반투명 영체 팔).
    - 5. 회로 복원 및 정화(`repair_circuit`): 마나 안정제, 은침 회로 소통술, 성수 정화.
    - 6. 규칙 6 준수: `ManaCircuitState`, `EtherMutationSpec`에 `traits` 의무 탑재.
- [x] **9. 🔥 [완료] 성벽 공성전 & 대규모 전열 전술 엔진 (`SiegeWarfareEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/siege_engine.py`, [엔진: 확장] `src/world/state.py`, `src/world/__init__.py`
  - **검증 증명**: 구현 파일 `src/world/siege_engine.py`, 통과 테스트 `tests/test_siege_engine.py` (12 passed), 전체 `pytest tests/` (497 passed).
  - **기능**:
    - 1) 다층 방어 구조물 물리 내구도 원칙: 성벽(`wall_durability`), 성문(`gate_durability`), 해자 방호도(`moat_durability`), 흉벽 엄폐 내구도(`battlement_durability`), 방어탑, 마도 결계 내구도 완전 구현.
    - 2) 5대 공성 병기 내구도 및 운용: 충차(Battering Ram), 평형추 트레뷰셋, 망고넬 투석기, 철갑 공성탑, 발리스타 노포, 공병 지하 갱도 내구도/조작원/화공 취약성/수리 로직 탑재.
    - 3) 해자 메우기(Moat filling) 역학: 해자 완파(평토화) 전 충차 및 공성탑 성벽/성문 접안 엄격 차단.
    - 4) 3군 전열 진형 상성 매트릭스: 방패벽 장창(기병 돌격 반사 2.0x, 화살 70% 차단), 쐐기 기병 돌격(비방진 보병 돌파 1.8x, 방패벽 충돌 시 자멸), 일제 사격(고도/흉벽 보정), 위장 후퇴, 산개 교란.
    - 5) 군대 사기(Morale) & 패주(Rout) 카스케이드: 지휘관 부상/외벽 완파/식량 고갈/사상자 50% 초과 시 사기 폭락 및 전면 패주 판정.
    - 6) 특공대 야간 침투 공작(`execute_commando_action`): 투석기 방화, 성문 빗장 개방, 군량고 방화, 지휘관 저격.
    - 7) 규칙 6 준수: 전 데이터클래스에 `traits` 기본 탑재.
    - 8) 규칙 8 준수: 외부 대형 LLM(GPT/Claude) 처절한 전장 문학 묘사 프롬프트 생성기(`generate_external_llm_prompt`) 탑재.
- [ ] **10. 가문 혈통 & 세대 계승 영구 레거시 엔진 (`LineageLegacyEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/lineage_engine.py`
  - **기능**: 영구 사망 시 유언장 집행, 직계 자손에게 가보/특성/영지/원수 가문 적대 관계 100% 인계.
- [x] **11. 🔥 [완료] 현상금 수배자 & 추적자 용병 AI 엔진 (`BountyHunterEngine` ➔ `NPCCognitiveDeductionEngine` 통합 완공)**:
  - **구현 대상**: [엔진: 통합] `src/world/cognitive_engine.py`, `src/world/two_pass_engine.py`, `src/world/bounty_engine.py`
  - **검증 증명**: 구현 파일 `src/world/cognitive_engine.py`, 통과 테스트 `tests/test_cognitive_engine.py` (11 passed), `tests/test_bounty_engine.py` (3 passed).
  - **기능**:
    - 1) 단일 뇌 아키텍처 통합: 현상금 사냥꾼만을 위한 별도 AI를 신설하지 않고, `NPCCognitiveDeductionEngine`의 마스터 인지 파이프라인(`process_npc_cognitive_turn`)으로 완벽 흡수 통합하여 코드 중복 및 뇌 파편화 방지.
    - 2) 성향 기반 추적 3대 분기: 탐욕+용기형 사냥꾼(기습 결행), 비겁+실리형 부랑배(관청 밀고), 충직+신뢰형 동료(은밀한 도주로 경고).
    - 3) 경비병 검문 체포 연동: 수배자 몽타주 식별 시 즉시 무력 체포 모드 전환.
    - 4) `two_pass_engine.py` 통합 연동: 매 턴 비전투 NPC 행동 틱을 단일 인지 파이프라인 호출로 완벽 일원화.
- [ ] **12. 종교 신앙도 & 신성 기적 축복/파문 엔진 (`DeityFaithEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/faith_engine.py`
  - **기능**: 신전 기도/규율 준수 시 신앙도 상승 및 기적 발동, 금기 위반 시 파문 및 성벌(신성 마법 봉인).
- [ ] **13. 사기 도박 & 주점 미니게임 주사위 엔진 (`GamblingDenEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/gambling_engine.py`
  - **기능**: 주점 주사위 도박(라이어스 다이스), 밑장빼기 은신 판정 및 적발 시 조폭 난투극.
- [ ] **14. 항해·해상전 & 난파 표류 조난 엔진 (`NavalVoyageEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/naval_engine.py`
  - **기능**: 선체 내구도, 돛 풍향, 괴수 크라켄 습격, 암초 충돌 및 무인도 조난 생존기.
- [ ] **15. 수사·추리·증거 결합 알리바이 검증 엔진 (`DeductionEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/deduction_engine.py`
  - **기능**: 살인 현장 족적/흉기/독극물 반응 수집, 알리바이 모순 교차 검증 및 진범 지목.
- [x] **16. 🔥 [완료] 식량 부패·수질 오염 & 보존식 염장 가공 엔진 (`RationSpoilageEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/ration_engine.py`, [엔진: 확장] `src/world/two_pass_engine.py`
  - **구현 완료 기능**:
    - 1. 개별 아이템 신선도 상태 모델(`FoodItemStatus`): 유저 규칙에 따라 묶음 아이템도 부패 시 개별 분리 관리, 신선도(100~0), 보존 방식, 턴당 부패율.
    - 2. 환경 연동 부패 가속(`process_turn_spoilage`): 체온/환경 기온(37.5℃ 이상 1.5배, 39℃ 이상 2.5배) 및 젖음/습도(40% 이상 1.4배, 75% 이상 2.2배 곰팡이 번식) 복합 가속.
    - 3. 부패 4단계 전이: 신선(100~80) ➔ 굳음/신선도 저하(79~40) ➔ 상함/쉰내(39~1, 식중독 위험) ➔ 썩은 폐기물(0, 구더기/악취, 이질 유발).
    - 4. 4대 보존 및 소독 가공(`preserve_food`, `purify_water`): 소금 염장(부패 10배 지연), 훈제(5배 지연), 태양 건조(6.6배 지연), 가열 비등 소독(오염수 100% 멸균 정화).
    - 5. 섭취 생체 반응(`consume_ration`): 허기 및 기력 회복, 상한 음식 섭취 시 급성 식중독(구토/피해/기력 소실), 썩은 음식/오염수 섭취 시 `EpidemicEngine.attempt_infection("dysentery")` 이질 감염 즉시 연동.
    - 6. 규칙 6 준수: `FoodItemStatus`, `PreservationMethodSpec`에 `traits` 의무 탑재.
- [ ] **17. 영지 개척 & 자원 채굴 방어 건설 엔진 (`FiefdomBuilderEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/fief_engine.py`
  - **기능**: 목재/석재 수급, 망루/성벽 건설, 주민 세금 징수, 주기적 도적 떼 약탈 웨이브 방어.
- [ ] **18. 암시장 경매 & 입찰 경쟁 비딩 엔진 (`BlackMarketAuctionEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/auction_engine.py`
  - **기능**: 희귀 금서/성유물 경매 출품, NPC 부호들과의 실시간 눈치싸움 호가 비딩, 낙찰품 강탈 도적.
- [ ] **19. NPC 파벌 내분 & 정치적 쿠데타 음모 엔진 (`FactionConspiracyEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/conspiracy_engine.py`
  - **기능**: 영주 vs 길드 암투, 뇌물 매수, 암살 사주, 권력 지분 변동에 따른 도시 지배 세력 전복.
- [ ] **20. 시체 부활 & 네크로맨시 언데드 사역 엔진 (`NecromancyCorpseEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/necromancy_engine.py`
  - **기능**: 처치한 적 시체 보존 상태에 따른 스켈레톤/좀비 되살리기, 마나 지속 소모 및 성기사 적대.
- [ ] **21. 마을 상점 & 10대 지형 무역 단일 통합 시스템 (`UnifiedCommerceEngine`)**:
  - **구현 대상**: [엔진: 통합] `EconomyEngine` + `MerchantBarterEngine` 단일화
  - **기능**: 기존 상점 거래(`EconomyEngine`)와 10대 지형 물가 매트릭스를 완전히 하나로 합쳐, 일반 상점에서도 지역 지형에 따른 소금/철/식수 시세 차익과 바터가 단일 인터페이스로 자연스럽게 연동.
- [ ] **22. 자세/체간 충격량 & 가드 브레이크 물리 엔진 (`PosturePoiseEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/poise_engine.py`
  - **기능**: 대형 둔기 타격 및 방패 방어 시 단순 HP 피해 외 체간(Posture) 게이지 차감, 0 도달 시 균형 붕괴(Stagger/Knockdown), 1턴간 무방비 치명타 피격.
- [ ] **23. 원거리 탄약 소모 및 화살 잔탄/수거 물리 엔진 (`AmmunitionRecoveryEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/ammo_engine.py`
  - **기능**: 활/석궁/투척단검 실시간 탄약 차감, 화살통 잔탄 관리, 전투 종료 후 빗나간 화살 50% 온전 회수 및 50% 파손 유실 판정.
- [ ] **24. 공간 협소도에 따른 무기 휘두름 제약 엔진 (`SpatialClearanceEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/clearance_engine.py`
  - **기능**: 천장 2.2m 미만 또는 복도 1.5m 미만 협소 공간에서 대검/장창 휘두름 시 벽면 튕김(Deflection) 역경직 및 찌르기 무기 한정 판정.
- [ ] **25. NPC 에피소딕 기억 망각 곡선 및 감정 왜곡 편향 엔진 (`MemoryDecayBiasEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/memory_decay_engine.py`
  - **기능**: 1~2급 사소한 기억의 시간 경과 망각(Decay), 공포/친밀도에 따른 주관적 기억 왜곡(과장/합리화) 인지 편향 시뮬레이션.
- [ ] **26. 변장/신분 간파 및 의심 누적 수사 엔진 (`DisguisePenetrationEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/disguise_engine.py`
  - **기능**: 투구/복면 착용 시 과거 기억(체형, 흉터, 걸음걸이, 고유 무기)과 대조해 경비병/NPC 의심 수치 누적 및 복면 강제 탈의 심문.
- [ ] **27. 근력 기반 소지 중량 과적 물리 제약 엔진 (`EncumbranceEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/encumbrance_engine.py`
  - **기능**: 근력(STR) 대비 휴대 한계 초과 시 3단계 과적(경미/중과적/한계), 이동속도 감속, 회피 불가, 주사위 디메리트, 스태미나 고갈.
- [ ] **28. 노획 장비 체형/골격 불일치 및 대장간 리사이징 엔진 (`ArmorRefittingEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/refitting_engine.py`
  - **기능**: 이종족(오크/드워프) 노획 갑옷 즉시 착용 시 극심한 민첩/이동 패널티, 대장간 체형 수선(Refitting) 공임 지불 후 완전 착용.
- [ ] **29. 야외 야영 모닥불 어그로 & 불침번 교대 기습 엔진 (`CampfireSecurityEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/campfire_engine.py`
  - **기능**: 모닥불 점화 시 체온 유지 vs 맹수/도적 유인 어그로, 동료 불침번 교대 실패 시 야간 기습 확정 및 수면 방해 피로도 미회복.
- [x] **30. 🔥 [완료] 수면 결핍 & 생체 각성 시계 엔진 (`SleepDeprivationEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/sleep_engine.py`, [엔진: 확장] `src/world/two_pass_engine.py`
  - **구현 완료 기능**:
    - 1. 생체 각성 시계 모델(`CircadianClock`): 연속 각성 턴/시간(`awake_hours`), 수면 결핍 3단계, 각성제 복용 버프 및 크래시 대기, 각성제 내성치.
    - 2. 수면 결핍 3단계 역학: 1단계(24h+, 주의 산만, 명중/지각 -2) ➔ 2단계(48h+, 회피 DC +4, 미세수면 확률 15%) ➔ 3단계(72h+, 급성 착란/환각, 미세수면 확률 35%, 심장마비/기절 위험).
    - 3. 미세수면(Microsleep) 격발 판정(`check_microsleep`): 2~3단계 결핍 시 이동 및 전투 중 순간 졸도, 1턴 강제 행동 취소 및 무방비 상태 전락.
    - 4. 3대 각성제 및 금단 크래시(`apply_stimulant`): 진한 커피, 야생 각성초, 비전 각성제 일시 복용 시 피로 억제 및 미세수면 면역. 약효 소진 시 억눌린 피로 폭풍(Crash, 피로도 +25~70) 즉시 폭발.
    - 5. 4대 침구 환경 수면 물리(`resolve_sleep`): 맨땅 노숙(효율 0.35, 오한/저체온증 위험) vs 가죽 침낭(0.70) vs 여관 침대(1.00) vs 귀족 깃털 침대(1.35, 스트레스 완화).
    - 6. 규칙 6 준수: `CircadianClock`, `StimulantSpec`, `BeddingQualitySpec`에 `traits` 의무 탑재.
- [x] **31. 🔥 [완료] 전장 시체 부패 & 청소 야수/사령 유인 생태계 (`CorpseEcologyEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/corpse_ecology_engine.py`, [엔진: 확장] `src/world/two_pass_engine.py`, `src/world/state.py`
  - **검증 증명**: 구현 파일 `src/world/corpse_ecology_engine.py`, 통과 테스트 `tests/test_corpse_ecology_engine.py` (5 passed).
  - **기능**: 전투 승리 후 방치된 시체 부패 4단계(fresh 0~60m ➔ bloated 61~180m ➔ rotting 181~360m ➔ skeleton 361m+). 유저 결정 Q1에 따라 3단계 부패 시 유기물/식량 썩음(A안) + 45% 확률 스캐벤저(늑대/까마귀/구울) 유인 스폰으로 잔여 전리품 및 골드 훼손/손실(B안) 하이브리드 결합, 시체열병 전염 오염원 경고, 시신 소각(역병 차단) 및 가매장(위생/신앙) 완비.
- [x] **32. 🔥 [완료] 포션 약물 남용 간 독성 & 내성 축적 엔진 (`ToxicologyToleranceEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/toxicology_engine.py`, [엔진: 확장] `src/world/two_pass_engine.py`, `src/world/campsite_engine.py`
  - **검증 증명**: 구현 파일 `src/world/toxicology_engine.py`, 통과 테스트 `tests/test_toxicology_engine.py` (5 passed).
  - **기능**: 회복 물약 연속 음용 시 약물 내성(최대 50% 힐량 감쇄) 및 체내 간 독성 누적(100 도달 시 급성 구토/스태미나 고갈). 유저 결정 Q1에 따라 현실 월드 타임 시간제(30분당 -5) 독성 대사 및 숙영지(Campsite) 8시간 수면 시 간 대사 완료 100% 완전 리셋.
- [x] **33. 🔥 [완료] 급격한 명암 변화 안구 암적응/명적응 물리 엔진 (`PupilAdaptationEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/pupil_adaptation_engine.py`, [엔진: 확장] `src/world/two_pass_engine.py`, `src/world/state.py`
  - **검증 증명**: 구현 파일 `src/world/pupil_adaptation_engine.py`, 통과 테스트 `tests/test_pupil_adaptation_engine.py` (5 passed).
  - **기능**: 조도(lx) 매트릭스 기반 망막 로돕신 적응 역학. 유저 결정 Q2에 따라 완전 시간제(초 단위) 구현: 대낮/밝음 ➔ 칠흑 암흑 진입 시 20.0초 암적응 지연(명중 DC+6, 이동속도 50% 감쇄). 해적 애꾸눈 안대(Eye Patch) 전술로 안대 반대편 전환 시 0.0초 즉각 암적응 패스. 암흑 ➔ 순간 섬광(Flash) 노출 시 2.0초 섬광 실명(행동 불가), 차광 고글(Shaded Goggles) 착용 시 섬광 100% 차단. 비전투 시 20초간 대기/적응 전용 행동(`adapt_eyes_action`) 지원.
- [x] **34. 🔥 [완료] 알코올 취기 & 숙취 중독 물리 엔진 (`AlcoholIntoxicationEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/alcohol_engine.py`, [엔진: 확장] `src/world/campsite_engine.py`
  - **검증 증명**: 구현 파일 `src/world/alcohol_engine.py`, 통과 테스트 `tests/test_alcohol_engine.py` (5 passed).
  - **기능**: 주점 맥주/와인/독주 섭취 시 혈중 알코올 농도(BAC), 1단계(알딸딸: 기분 고양, 스트레스 완화, 명중 -1), 2단계(만취: 비틀거림, 민첩 -3, 고통 둔화), 3단계(블랙아웃). 유저 결정 Q3에 따라 동료 동행 시 안전 호송 귀가 vs 동료 부재 시 60% 확률 노상 소매치기(30% 골드 도난) 및 뒷골목 저체온증/젖음 발생, 익일 기상 시 숙취 두통/탈수.
- [x] **35. 🔥 [완료] 야영 모닥불 & 침낭/숙영지 방어 엔진 (`CampsiteRestEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/campsite_engine.py`
  - **검증 증명**: 구현 파일 `src/world/campsite_engine.py`, 통과 테스트 `tests/test_campsite_engine.py` (6 passed).
  - **기능**: 모닥불 점화 시 건조/보온 유지 vs 야수/도적 유인 어그로 배율, 방어 목책/경보 덫 설치(침입자 지각 vs 덫 DC 주사위 대항 판정), 파티원 불침번 3교대 경계 근무 및 수면/피로도 회복.
- [x] **36. 🔥 [완료] 독초 감별 & 약초 채집 야생 식물학 엔진 (`HerbalismBotanyEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/botany_engine.py`
  - **검증 증명**: 구현 파일 `src/world/botany_engine.py`, 통과 테스트 `tests/test_botany_engine.py` (5 passed).
  - **기능**: 숲/산악/늪지 식물 채집 시 지능/지혜 식물학 판정, 맹독 유사종 오인 채집(식용 버섯 vs 맹독 광대버섯), 채집 도구 내구도 및 신선도 유지 채집통.
- [x] **37. 🔥 [완료] 마나 회로 손상 수술 & 에테르 정화 치료 엔진 (`ManaVeinRestorationEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/vein_restoration_engine.py`
  - **검증 증명**: 구현 파일 `src/world/vein_restoration_engine.py`, 통과 테스트 `tests/test_vein_restoration_engine.py` (6 passed).
  - **기능**: 마나 폭주로 파열된 회로(Vein Scarring)를 은침 소통술, 채집 약초 탕약 복용, 전문 비전 의사 에테르 투석 수술로 복구(영구 흉터 제거 및 최대 MP 복원). 유저 결정 Q2에 따라 수술 실패 시 마나 역류 충격파(-15 HP 및 마나 발작).
- [x] **38. 🔥 [완료] 기상 제어 마법 & 시공간 환경 재해 시뮬레이션 엔진 (`WeatherMagicSimulationEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/weather_magic_engine.py`
  - **검증 증명**: 구현 파일 `src/world/weather_magic_engine.py`, 통과 테스트 `tests/test_weather_magic_engine.py` (5 passed).
  - **기능**: 고드름 비/폭풍우/태양빛 소환 등 환경 제어 마법(최소 4서클+ 요구, 기본 30분 + 서클당 15분 추가), 전투 중 라운드 종료 틱 피해 vs 탐험 이동 중 10분 환경 틱 누적 피해 및 저체온/피로 정산, 마법 기상 지속시간 감쇄.
- [x] **39. 🔥 [완료] 자세/체간 충격량 & 가드 브레이크 물리 엔진 (`PosturePoiseEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/poise_engine.py`, [엔진: 확장] `src/world/two_pass_engine.py`, `src/world/state.py`
  - **검증 증명**: 구현 파일 `src/world/poise_engine.py`, 통과 테스트 `tests/test_poise_engine.py` (5 passed).
  - **기능**: 세키로형 체간(Posture) 및 강인도 역학. 유저 결정 Q3 및 지침 반영:
    - 1) 다중 충격량 누적: 가드 방어 성공 시 HP 대신 체간 충격 대량 흡수(1.6배), 피격 직격 시 둔기/강타 고유 체간 피해, 마법 원소 폭압(땅/바람/중력) 중심 붕괴, 정신적 공포/스트레스 충격 체간 누적(신경 불안정 자세 붕괴).
    - 2) 세키로형 기력 연동 자연 회복: 스태미나 잔여율 비례 회복, 가드 태세 시 2.0배 가속 회복, 스태미나 0 고갈(탈진) 시 체간 회복 완전 정지.
    - 3) 시간제 가드 브레이크 스턴: 체간 100 도달 시 가드 붕괴, 기본 1.0초 무방비 경직에서 장기전 지속시간(+0.5s/분) 및 기력 소진율(+1.5s)에 비례하여 스턴 시간 증가, 가드 브레이크 중 다음 피격 시 확정 치명타(+50% 추가 피해).
- [ ] **🔥 [템플릿 확충 11] 에테르 변이(Ether Mutation) 템플릿 확충 (현재 8종 ➔ 목표 20종)**:
  - **필요 사유**: 마나 폭주 및 에테르 피폭 시 다크 판타지형 이중성(혜택+페널티) 변이 다양성 부족.
  - **확충 대상(12종)**: 중력 왜곡 발걸음, 시간 지연 신경계, 비전 화염 혈류, 키틴질 마나 외골격, 영체 공명 성대, 마나 결핍 발작, 심연 침식 심장, 번개 전도 피부, 에테르 날개 피막, 비전 부유 분진, 왜곡된 마나 포식낭, 차원 균열 흉터 등.
- [ ] **🔥 [템플릿 확충 12] 보존식 및 야생 식자재 템플릿 확충 (현재 6종 ➔ 목표 25종)**:
  - **필요 사유**: 전 대륙 120종 및 304대 권역별 현실적 생존 음식 및 보존 가공 식품 부족.
  - **확충 대상(19종)**: 페미컨(지방 보존육), 하드택(건빵), 건포도/건무화과, 훈제 청어, 염장 대구, 식초 피클/절임 채소, 꿀에 절인 호두, 치즈 휠, 건조 콩, 휴대용 건조 수프 큐브, 동결건조 베리, 소금에 절인 돼지비계, 마나 건초 비스킷, 건조 버섯, 보리 미숫가루, 훈제 소시지, 밀랍 코팅 달걀, 밀폐 버터 단지, 정제수 알약 등.
- [ ] **🔥 [템플릿 확충 13] 수면 방해 요인 및 악몽 템플릿 확충 (현재 4종 ➔ 목표 15종)**:
  - **필요 사유**: 야생/동굴/던전 야영 시 생존 압박 및 심리적 공포 다양화.
  - **확충 대상(11종)**: 야수 울음소리, 습기 찬 침구 불쾌감, 모기/진드기 가려움, 살인마 추적 공포 악몽, 동사 공포 한기, 눅눅한 곰팡이 냄새, 전우 사망 죄책감 악몽, 지하 낙반 공포, 코골이 소음 불침번 분쟁, 모닥불 연기 질식 기침, 고열 헛소리 등.
- [x] **40. 🔥 [완료] NPC 심리·성격·인지 추론 & 12단계 행동 예측 엔진 (`NPCCognitiveDeductionEngine` & `PsychologyDecisionPipeline`)**:
  - **구현 대상**: [엔진: 신규] `src/world/psychology_engine.py`, [엔진: 확장] `src/world/cognitive_engine.py`, `src/world/state.py`, `src/world/two_pass_engine.py`
  - **검증 증명**: 구현 파일 `src/world/psychology_engine.py`, `src/world/cognitive_engine.py`, 통과 테스트 `tests/test_npc_psychology_state.py` (4 passed), `tests/test_npc_psychology_engine.py` (5 passed), `tests/test_npc_psychology_pipeline.py` (6 passed), 기존 `tests/test_cognitive_engine.py` (14 passed), 전체 `pytest tests/` (530 passed).
  - **기능**:
    - 1) 8대 성격 템플릿 아키타입 (`PERSONALITY_TEMPLATES`): 신중한 학자, 무모한 모험가, 헌신적인 기사, 냉소적인 용병, 야심찬 귀족, 다정한 치유사, 편집증 생존자, 광신적 이단심문관 (SHA256 결정론적 인스턴스 분산 탑재).
    - 2) 14종 복합 감정 시뮬레이션 (`EmotionEngine`): fear, anger, joy, grief, disgust, curiosity, pride, shame, guilt, hope, contempt, affection, anxiety, excitement 동시 활성화, 성향별 감수성 보정, 턴당 감쇠, 지배적 감정 산출 및 행동 점수 모디파이어.
    - 3) 독립 심리 스트레스 5단계 & 페르소나 붕괴 (`StressEngine`): 피로/사기와 분리된 0~100 스트레스, 90+ 붕괴 시 단순 패닉이 아닌 성격/가치관/대처기제에 따른 붕괴 행동(광기 난투, 비정한 배신 도주, 맹목적 공황, 종교적 마비 등) 직결.
    - 4) 인과 트라우마 활성화 체인 (`TraumaEngine`): 사건 키워드 매칭 ➔ 스트레스 증폭 ➔ 공포/불안 감정 유발 ➔ 회피/공격 편향 반환 및 안전 환경 노출 시 완화.
    - 5) 다자간 9축 관계 매트릭스 (`RelationshipEngine`): trust, affection, respect, fear, resentment, dependence, loyalty, suspicion, familiarity 다자간 맵 관리, 델타 5 이상 시 캐시 무효화 버전 증가, 플레이어 대상 시 레거시 필드(trust, affinity, respect, fear) 양방향 동기화.
    - 6) 메모리 심리 브릿지 (`MemoryPsychologyBridge`): 4+ 영구 앵커 우선 순위 인출, 5턴 윈도우 중복 기억 차단 및 기존 기억 강화.
    - 7) 3-Tier 평가 라우터 (`PsychologyDecisionPipeline`): Tier 1(일상/원거리 O(1) 감정 감쇠/스트레스 회복), Tier 2(동일 위치 국소 소란 < 5ms 경량 감지), Tier 3(직접 상호작용/대화/전투/트라우마 12단계 전체 파이프라인 및 trace 방출).
    - 8) 결정 캐시 (`DecisionCacheManager`): 상황 해시 + 상태 버전 + 스트레스 구간 기반 결정 캐싱 및 무효화.
    - 9) Two-Pass 및 인지 엔진 결합: `NPCCognitiveDeductionEngine.process_npc_cognitive_turn`과 직결되어 일반 턴에서도 12단계 심리 판단에 따라 `npc.intention` 및 `npc.goal` 자동 동기화.
    - 10) 외부 LLM 프롬프트 고도화 (`generate_external_llm_prompt`): 실시간 감정, 스트레스, 트라우마 상태 및 서술 경계 지침문(Strict Narrative Expression Boundary) 완전 탑재 (규칙 8 준수).

### [🔧 기존 엔진 배선(Wiring) & 통합 정비 — 클로드 코드리뷰 검증 기반]
> ⚠️ **[발견 경위]**: 2026-09-09 외부 Claude 정적 분석 피드백 → Antigravity(Gemini) 3개 서브에이전트 코드베이스 전수 교차 검증 완료. 설계/스키마 완성도는 높으나, 전체 모듈의 약 25%(16/64개)가 계단식 통합 2단계(팩트시트 슬롯 연결) 미진행 상태로 확인됨.

- [ ] **🔧 [배선 A] 16대 고립 엔진 → `TwoPassEngine` 팩트시트 슬롯 연결 (계단식 통합 2단계)**:
  - **진행 현황**:
    * **[x] `stealth_engine.py` (물리 은신/잠입/도청) 배선 완공**:
      - 구현 파일: `src/world/two_pass_engine.py` (`DeterministicFactSheet` 슬롯 탑재, `resolve_action_stealth`, `resolve_action_eavesdrop`), `src/world/state.py` (`Player.is_stealthed` 탑재 및 직렬화).
      - 통과 테스트: `tests/test_stealth_wiring.py` (4 passed), 전체 회귀 검증 `pytest tests/` (549 passed, 0 failed).
    * **[ ] 미연결 13대 엔진 잔여**: `mana_burn_engine`(차기 1순위), `harvest_engine`, `attack_physics_engine`, `campsite_engine`, `alcohol_engine`, `botany_engine`, `vein_restoration_engine`, `object_physics_engine`, `combat_time_track_engine`, `time_calendar_engine`, `siege_engine`, `stat_engine`, `outfit_engine`.
  - **작업 방식**: 엔진별로 `DeterministicFactSheet`에 슬롯 추가 → `compute_pass1` 적절 순서에 호출 삽입 → 3단계 전체 회귀 검증. 한 번에 1~2개씩 점진 통합 (빅뱅 통합 금지).
- [ ] **🔧 [배선 B] NPC 인지 엔진 4대 핵심 메서드 → 게임 루프 연결**:
  - **필요 사유**: `cognitive_engine.py`의 핵심 4대 메서드(`evaluate_player_hypothesis`, `predict_autonomous_next_intent`, `check_micro_leakage`, `generate_external_llm_prompt`)가 테스트에서만 호출되고, 유일하게 런타임 연결된 `process_npc_cognitive_turn` 내부에서도 호출하지 않음. "12단계 NPC 심리 인지 예측"이라는 마스터 문서 서술이 실제 돌아가는 게임 기준으로는 미달성 상태.
  - **작업 방식**: `process_npc_cognitive_turn` 내부에서 적절한 트리거 조건(플레이어 대화 중 가설 표출 → `evaluate_player_hypothesis`, 비전투 턴 종료 → `predict_autonomous_next_intent`, 대면 대화 시 → `check_micro_leakage`)에 따라 호출 분기 삽입.
- [ ] **🔧 [배선 C] NPC 심리 확장 필드 Write-Only 해소 → 결정론적 로직 소비**:
  - **필요 사유**: `NPCPersonality` 확장 6축(`patience`, `cunning`, `pride`, `rationality`, `neuroticism`, `deceit`) 및 심층 페르소나 필드(`life_defining_moment`, `value_hierarchy`, `coping_mechanism`, `public_mask`, `moral_justification`, `micro_leakage_traits`, `risk_tolerance`, `bdi_state`) 대부분이 생성/저장만 되고 어떤 결정론적 코드에서도 읽히지 않는 write-only 상태. 특히 `bdi_state`, `risk_tolerance`는 전 코드베이스에서 100% 미사용.
  - **작업 방식**: `process_npc_cognitive_turn`의 행동 분기 가중치에 확장 축 반영(예: `patience` 높으면 즉각 공격 억제, `pride` 높으면 굴복/항복 거부, `rationality` 높으면 감정적 폭주 억제). `predict_autonomous_next_intent`에서 `value_hierarchy`, `risk_tolerance`, `bdi_state` 소비.
- [ ] **🔧 [배선 D] NPC 에피소딕 기억 망각/가지치기 로직 구현 (`MemoryDecayPruner`)**:
  - **필요 사유**: `npc.memories`가 세션 내내 append만 되고 삭제/요약/트림 로직이 전무. AGENTS.md `<Two_Pass_Resource>` 규칙 3 "MEMORY limit: NPCs episodic memory must have truncation/summarization to avoid token overflow" 위반 상태. 장기 세션 시 세이브 파일 무한 증가 및 LLM 프롬프트 토큰 폭발 위험.
  - **작업 방식**: `state.py`의 `memory_decay_turn_interval`(현재 50턴) 활용하여 significance 1~2급 기억의 주기적 망각/요약. 백로그 25번(`MemoryDecayBiasEngine`)과 통합 설계. 기존 `relevant_memories(max_memories=5)` 슬라이싱은 프롬프트용 뷰만 제공하므로 실제 데이터 가지치기 별도 필요.
- [ ] **🔧 [정비 E] 죽은 모듈 정리 및 문서-코드 네이밍 불일치 수정**:
  - **필요 사유**: (1) `save_load_manager.py`는 `persistence.py`와 기능 완전 중복, `__init__.py`에도 미등록된 고아 파일. (2) `merchant_barter_engine.py`도 `__init__.py` 미등록 고아. (3) SESSION_HANDOFF.md L160의 `PERSONALITY_BREAKDOWN_WEIGHTS` 명칭이 실제 코드(`party_sanity_engine.py`)에서는 `PERSONALITY_BREAKDOWN_TABLES`로 구현됨 — 문서-코드 네이밍 불일치.
  - **작업 방식**: `save_load_manager.py` 삭제 여부 유저 확인 후 처리. `merchant_barter_engine.py`는 백로그 21번 통합 시 흡수. SESSION_HANDOFF.md 네이밍 수정.

### [🐛 구조적 버그 & 리포 위생 수정 — 클로드 2차 코드리뷰 검증 기반]
> ⚠️ **[발견 경위]**: 2026-09-10 외부 Claude 2차 정밀 코드리뷰 → Antigravity(Gemini) 3개 서브에이전트 전수 교차 검증 완료. 구조적 디싱크(시간/서사/인벤토리/소문) 및 리포 위생 문제 확인됨. 아래 항목은 작업량 기준 한 세션에 1~2개씩 수정 가능한 단위로 분리.

- [ ] **🐛 [수정 F] `README.md` 죽은 문서 전면 교체 [5분 단독 작업]**:
  - **증상**: README.md가 초기 5개 룸 Gradio 데모(WorldState 4~5클래스)를 설명. 실제 코드는 state.py 4396행/20개 클래스, 64개 엔진, 530+ 테스트의 완전히 다른 프로젝트. 누가 봐도 혼란 유발.
  - **처방**: README.md를 현행 MASTER_GAME_ARCHITECTURE.md + AGENTS.md 기반으로 전면 재작성. 기존 README는 `docs/legacy_readme_prototype.md`로 보관.
- [ ] **🐛 [수정 G] `__pycache__/*.pyc` Git 추적 제거 [5분 단독 작업]**:
  - **증상**: `.gitignore`에 `__pycache__/`가 있지만, 이미 커밋된 3개 pyc 파일이 git 추적 상태로 남아있음: `src/__pycache__/__init__.cpython-314.pyc`, `src/image/__pycache__/__init__.cpython-314.pyc`, `src/image/__pycache__/flux.cpython-314.pyc`. AGENTS.md `<Prompt_Rules>` 4번 "NO ARTIFACT COMMIT" 규칙 위반.
  - **처방**: `git rm --cached src/__pycache__/__init__.cpython-314.pyc src/image/__pycache__/__init__.cpython-314.pyc src/image/__pycache__/flux.cpython-314.pyc` 실행 후 커밋. `.gitignore`는 이미 정상.
- [x] **🐛 [완료: 수정 H] `sanitize_pass2_result` 서사-판정 모순 검증 로직 구현**:
  - **구현 대상**: [엔진: 확장] `src/world/two_pass_engine.py`, [테스트] `tests/test_two_pass_engine.py` (11 passed, 신규 4개 통과).
  - **증명**: 구현 메서드 `TwoPassEngine.reconcile_narration_with_fact_sheet`, 테스트 `tests/test_two_pass_engine.py::test_sanitize_pass2_result_*`.
  - **완료 기능**:
    1) Anti-Yes-Man 물리/논리 거부(`is_valid=False`) 시 강제 거부 서사로 전면 대체.
    2) 주사위 판정 실패(`is_success=False`)인데 LLM이 성공("성공", "돌파", "격파" 등) 날조 시 `[⚠️ 서사-판정 모순 감지]` 경고 로깅 및 `*(⚠️ 판정 결과: 실패...)*` 강제 팩트 보정 부착.
    3) 적 생존(`killed=False`)인데 사망 날조 시 `*(⚠️ 전투 지속: ...)*` 강제 팩트 부착.
    4) 적 사망(`killed=True`)인데 생존/도주 날조 시 `*(⚠️ 처치 확인: ...)*` 강제 팩트 부착.
- [x] **🐛 [완료: 수정 I] 장거리 이동 시 생존 틱 시간 비례 미적용 — "30분 하드코딩" 문제 완공 [중간 작업]**:
  - **구현 대상**: [엔진: 연동] `src/world/two_pass_engine.py` (`resolve_action_movement`, Step 1/Step 2.5), `src/world/weather_engine.py`, `src/world/thermal_engine.py`, `src/world/ration_engine.py`, `src/world/sleep_engine.py`, `src/world/party_sanity_engine.py`, `src/world/disease_engine.py`, [테스트] `tests/test_two_pass_engine.py` (2 passed, 13/13 passed).
  - **증명**: 구현 메서드 `TwoPassEngine.resolve_action_movement`, `TwoPassEngine.compute_pass1`, 테스트 `tests/test_two_pass_engine.py::test_long_distance_travel_scales_survival_ticks`, `tests/test_two_pass_engine.py::test_non_movement_action_keeps_default_30min_ticks`.
  - **완료 기능**:
    1) 이동 액션 발생 시 `GeographyEngine.calculate_segment_travel_hours` 기반 실제 소요시간(`mins`)을 사전 연산(`resolve_action_movement`).
    2) 계산된 `elapsed_minutes`를 Step 1의 모든 생존 및 환경 틱 함수에 전달:
       - `WeatherEngine.process_turn_survival_ticks` & `ThermalSurvivalEngine.process_turn_thermal_survival` (`delta_minutes` 비례 체온/젖음/동상/열사 틱 반복).
       - `RationSpoilageEngine.process_turn_spoilage` (`delta_minutes / 30.0` 비례 부패율 스케일링).
       - `SleepDeprivationEngine.process_turn_circadian` (`delta_minutes / 20.0` 비례 각성 턴/시간 누적, 각성제 소모, 피로 가산).
       - `PartySanityEngine.process_turn_sanity` (`delta_minutes / 30.0` 비례 지하 어둠 스트레스 및 붕괴 턴 차감).
       - `EpidemicEngine.process_turn_infections` (`delta_minutes / 30.0` 비례 잠복기 감소 및 질병 지속 피해).
       - `WeatherMagicSimulationEngine.tick_anomalies`, `ToxicologyToleranceEngine.process_time_metabolism`, `QuestEngine.check_turn_time_limits`, `CorpseEcologyEngine.process_turn_corpse_decay`, `PupilAdaptationEngine.tick_adaptation_seconds`, `EconomyEngine.restock_turn_ticks` 실시간 시간 비례 적용.
    3) 비이동 액션은 기존 30분 틱 / 10분 소요시간 정상 유지.
    4) 전체 539개 테스트 100% 무결점 통과 (BASELINE 537 대비 +2 신규 통과, 0 failed), `eval_runner.py --no-judge` 20턴 `Invalid transition rate: 0.0%` 달성.
- [ ] **🐛 [수정 J] `dijkstra_shortest_travel` 다중 구간 경로탐색 미연결 [중간 작업]**:
  - **증상**: `geography.py:269-336`에 다익스트라 최단 경로 탐색 구현 완료. 그러나 실제 플레이어 이동(`two_pass_engine.py:366-406`)은 현재 위치의 직접 연결된 `curr_loc.exits`만 검색. 여러 구간을 거치는 장거리 이동("늪지대까지 가라")은 매칭 불가. `dijkstra_shortest_travel`은 테스트에서만 호출됨(소문 확산 엔진도 별도 함수 `get_all_reachable_locations_with_distances` 사용).
  - **처방**: 이동 액션에서 직접 exit에 없는 목적지 요청 시, `dijkstra_shortest_travel`로 다중 구간 경로 계산 → 첫 구간만 즉시 이동 + 나머지 경유지를 `state`에 `pending_travel_waypoints`로 저장 → 다음 턴마다 자동 1구간 진행.
- [x] **🐛 [완료: 수정 K] 인벤토리 무제한 append 방지 & 기존 `outfit_engine.py` 가방 용량/찢어짐 엔진 배선 [중간 작업]**:
  - **구현 대상**: [엔진: 연동] `src/world/state.py` (L3401-3445 `pickup_item` 분기), [테스트] `tests/test_world_state.py` (3 passed).
  - **증명**: 구현 메서드 `WorldState.apply_update:pickup_item`, 테스트 `tests/test_world_state.py::test_pickup_item_*`, `tests/test_world_state.py::test_validator_rejects_picking_up_massive_furniture`.
  - **완료 기능**:
    1) `apply_update`의 `pickup_item` 분기에서 `OutfitMechanicsEngine.get_backpack_spec` 및 `evaluate_backpack_storage` 배선.
    2) 가방 파손 한계(`tear_weight_limit_kg`) 및 용적(1.5x) 초과 시 인벤토리 수납 거부(`REJECTED pickup ... — 가방 적재 한계 초과`) 및 필드 유지.
    3) 가구/구조물(`item_type in ["furniture", "structure"]` 또는 `can_store_in_bag=False`) 수납 시도 시 즉각 거부(`⛔ [...]은(는) 너무 거대하거나 구조물 형태이므로 가방에 넣을 수 없습니다.`).
    4) `state.py:3753`의 `update_environment` 등 LLM이 dict 대신 문자열/비-dict 입력 시의 타입 에러 예외 방어 보강 완료.
    5) 전체 537개 테스트 100% 무결점 통과 (BASELINE 534 대비 +3 신규 통과, 0 failed), `eval_runner.py --no-judge` 20턴 `Invalid transition rate: 0.0%` 달성.
- [ ] **🐛 [수정 L] NPC 처치 소문 무조건 발동 — 목격자 게이트(Witness Gate) 부재 [쉬운 작업]**:
  - **증상**: `two_pass_engine.py:689-699` — NPC 사망 시 같은 위치에 살아있는 목격자(다른 NPC/동료) 존재 여부를 검사하지 않고 무조건 `RumorDiffusionEngine.dispatch_event_rumor` 발동. 아무도 없는 던전 밀실에서 암살해도 `carrier="merchant"`로 소문 자동 발사.
  - **처방**: dispatch 호출 전에 `witnesses = [n for n in state.npcs.values() if n.location == state.player.location and n.id != target_npc.id and n.health > 0]` 체크 추가. `len(witnesses) == 0`이면 소문 미발동 (완전 범죄 성공). 동료 NPC만 있으면 동료 신뢰도에 따라 누설 확률 분기.

### [인프라, UI 및 플랫폼 시스템 (공통/플랫폼)]
> ⚠️ **[유저 절대 규칙] 찐찐 마지막 최종 업데이트 지정**: UI 연동, TTS 음성, 이미지 AI(SD LoRA) 연동 등은 전반적인 게임플레이, 전투, 생존 물리 시스템 및 밸런싱 작업이 100% 완료된 이후에 진행할 '찐찐 마지막 최종 업데이트'로 동결한다.

- [ ] **1. 인터랙티브 웹 UI 대시보드 (`InteractiveWebUI`) [찐찐 마지막 업데이트]**:
  - **구현 대상**: [UI: 신규] FastHTML/React 프론트엔드 대시보드
  - **기능**: 실시간 HP/MP/피로도/스트레스 게이지, 지리 도로망 2D 미니맵, 인벤토리 툴팁, SD 초상화 & TTS 오디오 플레이어.
- [ ] **2. 동적 BGM 믹서 & 크로스페이드 사운드 엔진 (`DynamicAudioPlayer`) [찐찐 마지막 업데이트]**:
  - **구현 대상**: [오디오: 신규] 파이썬 오디오 플레이어 & 믹서
  - **기능**: 전투 돌입 시 1.5초 크로스페이드(자연스러운 음악 전환), 환경 앰비언스 루프(비/바람/주점).
- [ ] **3. 모험 전기록(크로니클) 판타지 소설책 HTML/PDF 내보내기 (`ChronicleBookExporter`)**:
  - **구현 대상**: [툴: 신규] HTML/PDF 양장본 북 렌더러
  - **기능**: 30일간 모험 기록을 챕터별 삽화와 함께 진짜 판타지 양장본 소설책 형태로 자동 조판/내보내기.
- [ ] **4. 모딩(Mod) & 커스텀 시나리오/세계관 검증기 (`ModdingValidator`)**:
  - **구현 대상**: [툴: 신규] CLI 모드 검증 및 핫로더
  - **기능**: 신규 퀘스트, 몬스터, 세계관 JSON 무결성 자동 검증 및 원클릭 로딩.

### [집/노트북 환경 — 인게임 콘텐츠 및 데이터 구축]
- [ ] **🔥 [집 도착 즉시 최우선 착수] 실전 인터랙티브 스토리 플레이테스트 & 결핍 시스템 발굴**:
  - **진행 방식**: 유저와 AI가 실제 캐릭터로 1턴씩 실전 스토리를 플레이(행동 입력 -> 주사위/전투/대화/이동/수면/상호작용).
  - **목적**: "이런 상황에서 지금 시스템에 뭐가 없지? 어떻게 처리되지?"를 현장에서 1:1로 확인하며 말을 맞춤.
  - **효과**: 책상머리 뇌피셜 거품 엔진(도박엔진, 숟가락엔진 등)을 1초 만에 걸러내고, 실전에서 진짜 결핍된 핵심 시스템/상태이상만 핀포인트로 발굴하여 즉시 구현.
- [ ] **장비 템플릿 DB 50종 구축 (`data/templates/equipment_templates.json`)**:
  - 10개 슬롯(투구, 흉갑, 각반, 장갑, 부츠, 망토, 반지 20개, 귀걸이 8개, 무기)용 고유 아이템 스탯/방어력/내구도/소켓 데이터 완성 및 상점/루팅 생성기 연동.
- [ ] **SD 1.5 LoRA & NPC 7대 표정 팩 백그라운드 파이프라인 [찐찐 마지막 업데이트]**:
  - 인물 A 생성 시 기본 그림 1~2초 즉시 출력 후, 백그라운드(ADetailer 얼굴 인페인팅)로 7대 표정(기본, 놀람, 분노, 웃음, 패닉, 공포, 각성) 무지연 순차 생성(총 15초 내외).
- [ ] **TTS 한국어 음성 엔진 탑재 (Edge-TTS / Kokoro) [찐찐 마지막 업데이트]**:
  - NPC 성별/나이/톤별 보이스 매핑 및 자연스러운 한국어 음성 출력.
- [x] **🔥 [완료] 만물 사물 내구도 & 물리 파괴 엔진 (`UniversalObjectPhysicsEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/object_physics_engine.py`, [엔진: 확장] `src/world/state.py`, `src/world/__init__.py`
  - **검증 증명**: 구현 파일 `src/world/object_physics_engine.py`, 통과 테스트 `tests/test_object_physics_engine.py` (11 passed), 전체 `pytest tests/` (508 passed).
  - **기능**:
    - 1) 12대 만물 물리 재질 매트릭스(종이/유리/천/가죽/목재/흙/석재/철재/귀금속/유기물/목조건물/석조건물) 완전 구축.
    - 2) 의자, 책상, 침대, 책, 종이, 돌, 나무, 집, 유리병 등 세상의 모든 사물에 내구도, 경도(Hardness), 인화성, 취성 부여.
    - 3) 사물 파괴 시 재질 태그에 따른 결정론적 잔해 분해 스폰 (의자 ➔ 각목 즉석 무기 & 장작, 유리병 ➔ 날카로운 유리 파편 & 65dB 소음, 종이/책 ➔ 잿더미 & 텍스트 소멸, 바위 ➔ 돌멩이 & 자갈, 냄비/철창 ➔ 고철).
    - 4) 보관함(상자, 서랍장, 옷장) 파괴 시 수납 아이템 바닥 유출(Spill) 루팅 연동.
- [ ] **24. 공간 협소도에 따른 무기 휘두름 제약 엔진 (`SpatialClearanceEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/clearance_engine.py`
  - **기능**: 천장 2.2m 미만 또는 복도 1.5m 미만 협소 공간에서 대검/장창 휘두름 시 벽면 튕김(Deflection) 역경직 및 찌르기 무기 한정 판정.
- [ ] **25. NPC 에피소딕 기억 망각 곡선 및 감정 왜곡 편향 엔진 (`MemoryDecayBiasEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/memory_decay_engine.py`
  - **기능**: 1~2급 사소한 기억의 시간 경과 망각(Decay), 공포/친밀도에 따른 주관적 기억 왜곡(과장/합리화) 인지 편향 시뮬레이션.
- [ ] **26. 변장/신분 간파 및 의심 누적 수사 엔진 (`DisguisePenetrationEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/disguise_engine.py`
  - **기능**: 투구/복면 착용 시 과거 기억(체형, 흉터, 걸음걸이, 고유 무기)과 대조해 경비병/NPC 의심 수치 누적 및 복면 강제 탈의 심문.
- [ ] **27. 근력 기반 소지 중량 과적 물리 제약 엔진 (`EncumbranceEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/encumbrance_engine.py`
  - **기능**: 근력(STR) 대비 휴대 한계 초과 시 3단계 과적(경미/중과적/한계), 이동속도 감속, 회피 불가, 주사위 디메리트, 스태미나 고갈.
- [ ] **28. 노획 장비 체형/골격 불일치 및 대장간 리사이징 엔진 (`ArmorRefittingEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/refitting_engine.py`
  - **기능**: 이종족(오크/드워프) 노획 갑옷 즉시 착용 시 극심한 민첩/이동 패널티, 대장간 체형 수선(Refitting) 공임 지불 후 완전 착용.
- [ ] **29. 야외 야영 모닥불 어그로 & 불침번 교대 기습 엔진 (`CampfireSecurityEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/campfire_engine.py`
  - **기능**: 모닥불 점화 시 체온 유지 vs 맹수/도적 유인 어그로, 동료 불침번 교대 실패 시 야간 기습 확정 및 수면 방해 피로도 미회복.
- [x] **30. 🔥 [완료] 수면 결핍 & 생체 각성 시계 엔진 (`SleepDeprivationEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/sleep_engine.py`, [엔진: 확장] `src/world/two_pass_engine.py`
  - **구현 완료 기능**:
    - 1. 생체 각성 시계 모델(`CircadianClock`): 연속 각성 턴/시간(`awake_hours`), 수면 결핍 3단계, 각성제 복용 버프 및 크래시 대기, 각성제 내성치.
    - 2. 수면 결핍 3단계 역학: 1단계(24h+, 주의 산만, 명중/지각 -2) ➔ 2단계(48h+, 회피 DC +4, 미세수면 확률 15%) ➔ 3단계(72h+, 급성 착란/환각, 미세수면 확률 35%, 심장마비/기절 위험).
    - 3. 미세수면(Microsleep) 격발 판정(`check_microsleep`): 2~3단계 결핍 시 이동 및 전투 중 순간 졸도, 1턴 강제 행동 취소 및 무방비 상태 전락.
    - 4. 3대 각성제 및 금단 크래시(`apply_stimulant`): 진한 커피, 야생 각성초, 비전 각성제 일시 복용 시 피로 억제 및 미세수면 면역. 약효 소진 시 억눌린 피로 폭풍(Crash, 피로도 +25~70) 즉시 폭발.
    - 5. 4대 침구 환경 수면 물리(`resolve_sleep`): 맨땅 노숙(효율 0.35, 오한/저체온증 위험) vs 가죽 침낭(0.70) vs 여관 침대(1.00) vs 귀족 깃털 침대(1.35, 스트레스 완화).
    - 6. 규칙 6 준수: `CircadianClock`, `StimulantSpec`, `BeddingQualitySpec`에 `traits` 의무 탑재.
- [x] **31. 🔥 [완료] 전장 시체 부패 & 청소 야수/사령 유인 생태계 (`CorpseEcologyEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/corpse_ecology_engine.py`, [엔진: 확장] `src/world/two_pass_engine.py`, `src/world/state.py`
  - **검증 증명**: 구현 파일 `src/world/corpse_ecology_engine.py`, 통과 테스트 `tests/test_corpse_ecology_engine.py` (5 passed).
  - **기능**: 전투 승리 후 방치된 시체 부패 4단계(fresh 0~60m ➔ bloated 61~180m ➔ rotting 181~360m ➔ skeleton 361m+). 유저 결정 Q1에 따라 3단계 부패 시 유기물/식량 썩음(A안) + 45% 확률 스캐벤저(늑대/까마귀/구울) 유인 스폰으로 잔여 전리품 및 골드 훼손/손실(B안) 하이브리드 결합, 시체열병 전염 오염원 경고, 시신 소각(역병 차단) 및 가매장(위생/신앙) 완비.
- [x] **32. 🔥 [완료] 포션 약물 남용 간 독성 & 내성 축적 엔진 (`ToxicologyToleranceEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/toxicology_engine.py`, [엔진: 확장] `src/world/two_pass_engine.py`, `src/world/campsite_engine.py`
  - **검증 증명**: 구현 파일 `src/world/toxicology_engine.py`, 통과 테스트 `tests/test_toxicology_engine.py` (5 passed).
  - **기능**: 회복 물약 연속 음용 시 약물 내성(최대 50% 힐량 감쇄) 및 체내 간 독성 누적(100 도달 시 급성 구토/스태미나 고갈). 유저 결정 Q1에 따라 현실 월드 타임 시간제(30분당 -5) 독성 대사 및 숙영지(Campsite) 8시간 수면 시 간 대사 완료 100% 완전 리셋.
- [x] **33. 🔥 [완료] 급격한 명암 변화 안구 암적응/명적응 물리 엔진 (`PupilAdaptationEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/pupil_adaptation_engine.py`, [엔진: 확장] `src/world/two_pass_engine.py`, `src/world/state.py`
  - **검증 증명**: 구현 파일 `src/world/pupil_adaptation_engine.py`, 통과 테스트 `tests/test_pupil_adaptation_engine.py` (5 passed).
  - **기능**: 조도(lx) 매트릭스 기반 망막 로돕신 적응 역학. 유저 결정 Q2에 따라 완전 시간제(초 단위) 구현: 대낮/밝음 ➔ 칠흑 암흑 진입 시 20.0초 암적응 지연(명중 DC+6, 이동속도 50% 감쇄). 해적 애꾸눈 안대(Eye Patch) 전술로 안대 반대편 전환 시 0.0초 즉각 암적응 패스. 암흑 ➔ 순간 섬광(Flash) 노출 시 2.0초 섬광 실명(행동 불가), 차광 고글(Shaded Goggles) 착용 시 섬광 100% 차단. 비전투 시 20초간 대기/적응 전용 행동(`adapt_eyes_action`) 지원.
- [x] **34. 🔥 [완료] 알코올 취기 & 숙취 중독 물리 엔진 (`AlcoholIntoxicationEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/alcohol_engine.py`, [엔진: 확장] `src/world/campsite_engine.py`
  - **검증 증명**: 구현 파일 `src/world/alcohol_engine.py`, 통과 테스트 `tests/test_alcohol_engine.py` (5 passed).
  - **기능**: 주점 맥주/와인/독주 섭취 시 혈중 알코올 농도(BAC), 1단계(알딸딸: 기분 고양, 스트레스 완화, 명중 -1), 2단계(만취: 비틀거림, 민첩 -3, 고통 둔화), 3단계(블랙아웃). 유저 결정 Q3에 따라 동료 동행 시 안전 호송 귀가 vs 동료 부재 시 60% 확률 노상 소매치기(30% 골드 도난) 및 뒷골목 저체온증/젖음 발생, 익일 기상 시 숙취 두통/탈수.
- [x] **35. 🔥 [완료] 야영 모닥불 & 침낭/숙영지 방어 엔진 (`CampsiteRestEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/campsite_engine.py`
  - **검증 증명**: 구현 파일 `src/world/campsite_engine.py`, 통과 테스트 `tests/test_campsite_engine.py` (6 passed).
  - **기능**: 모닥불 점화 시 건조/보온 유지 vs 야수/도적 유인 어그로 배율, 방어 목책/경보 덫 설치(침입자 지각 vs 덫 DC 주사위 대항 판정), 파티원 불침번 3교대 경계 근무 및 수면/피로도 회복.
- [x] **36. 🔥 [완료] 독초 감별 & 약초 채집 야생 식물학 엔진 (`HerbalismBotanyEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/botany_engine.py`
  - **검증 증명**: 구현 파일 `src/world/botany_engine.py`, 통과 테스트 `tests/test_botany_engine.py` (5 passed).
  - **기능**: 숲/산악/늪지 식물 채집 시 지능/지혜 식물학 판정, 맹독 유사종 오인 채집(식용 버섯 vs 맹독 광대버섯), 채집 도구 내구도 및 신선도 유지 채집통.
- [x] **37. 🔥 [완료] 마나 회로 손상 수술 & 에테르 정화 치료 엔진 (`ManaVeinRestorationEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/vein_restoration_engine.py`
  - **검증 증명**: 구현 파일 `src/world/vein_restoration_engine.py`, 통과 테스트 `tests/test_vein_restoration_engine.py` (6 passed).
  - **기능**: 마나 폭주로 파열된 회로(Vein Scarring)를 은침 소통술, 채집 약초 탕약 복용, 전문 비전 의사 에테르 투석 수술로 복구(영구 흉터 제거 및 최대 MP 복원). 유저 결정 Q2에 따라 수술 실패 시 마나 역류 충격파(-15 HP 및 마나 발작).
- [x] **38. 🔥 [완료] 기상 제어 마법 & 시공간 환경 재해 시뮬레이션 엔진 (`WeatherMagicSimulationEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/weather_magic_engine.py`
  - **검증 증명**: 구현 파일 `src/world/weather_magic_engine.py`, 통과 테스트 `tests/test_weather_magic_engine.py` (5 passed).
  - **기능**: 고드름 비/폭풍우/태양빛 소환 등 환경 제어 마법(최소 4서클+ 요구, 기본 30분 + 서클당 15분 추가), 전투 중 라운드 종료 틱 피해 vs 탐험 이동 중 10분 환경 틱 누적 피해 및 저체온/피로 정산, 마법 기상 지속시간 감쇄.
- [x] **39. 🔥 [완료] 자세/체간 충격량 & 가드 브레이크 물리 엔진 (`PosturePoiseEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/poise_engine.py`, [엔진: 확장] `src/world/two_pass_engine.py`, `src/world/state.py`
  - **검증 증명**: 구현 파일 `src/world/poise_engine.py`, 통과 테스트 `tests/test_poise_engine.py` (5 passed).
  - **기능**: 세키로형 체간(Posture) 및 강인도 역학. 유저 결정 Q3 및 지침 반영:
    - 1) 다중 충격량 누적: 가드 방어 성공 시 HP 대신 체간 충격 대량 흡수(1.6배), 피격 직격 시 둔기/강타 고유 체간 피해, 마법 원소 폭압(땅/바람/중력) 중심 붕괴, 정신적 공포/스트레스 충격 체간 누적(신경 불안정 자세 붕괴).
    - 2) 세키로형 기력 연동 자연 회복: 스태미나 잔여율 비례 회복, 가드 태세 시 2.0배 가속 회복, 스태미나 0 고갈(탈진) 시 체간 회복 완전 정지.
    - 3) 시간제 가드 브레이크 스턴: 체간 100 도달 시 가드 붕괴, 기본 1.0초 무방비 경직에서 장기전 지속시간(+0.5s/분) 및 기력 소진율(+1.5s)에 비례하여 스턴 시간 증가, 가드 브레이크 중 다음 피격 시 확정 치명타(+50% 추가 피해).
- [ ] **🔥 [템플릿 확충 11] 에테르 변이(Ether Mutation) 템플릿 확충 (현재 8종 ➔ 목표 20종)**:
  - **필요 사유**: 마나 폭주 및 에테르 피폭 시 다크 판타지형 이중성(혜택+페널티) 변이 다양성 부족.
  - **확충 대상(12종)**: 중력 왜곡 발걸음, 시간 지연 신경계, 비전 화염 혈류, 키틴질 마나 외골격, 영체 공명 성대, 마나 결핍 발작, 심연 침식 심장, 번개 전도 피부, 에테르 날개 피막, 비전 부유 분진, 왜곡된 마나 포식낭, 차원 균열 흉터 등.
- [ ] **🔥 [템플릿 확충 12] 보존식 및 야생 식자재 템플릿 확충 (현재 6종 ➔ 목표 25종)**:
  - **필요 사유**: 전 대륙 120종 및 304대 권역별 현실적 생존 음식 및 보존 가공 식품 부족.
  - **확충 대상(19종)**: 페미컨(지방 보존육), 하드택(건빵), 건포도/건무화과, 훈제 청어, 염장 대구, 식초 피클/절임 채소, 꿀에 절인 호두, 치즈 휠, 건조 콩, 휴대용 건조 수프 큐브, 동결건조 베리, 소금에 절인 돼지비계, 마나 건초 비스킷, 건조 버섯, 보리 미숫가루, 훈제 소시지, 밀랍 코팅 달걀, 밀폐 버터 단지, 정제수 알약 등.
- [ ] **🔥 [템플릿 확충 13] 수면 방해 요인 및 악몽 템플릿 확충 (현재 4종 ➔ 목표 15종)**:
  - **필요 사유**: 야생/동굴/던전 야영 시 생존 압박 및 심리적 공포 다양화.
  - **확충 대상(11종)**: 야수 울음소리, 습기 찬 침구 불쾌감, 모기/진드기 가려움, 살인마 추적 공포 악몽, 동사 공포 한기, 눅눅한 곰팡이 냄새, 전우 사망 죄책감 악몽, 지하 낙반 공포, 코골이 소음 불침번 분쟁, 모닥불 연기 질식 기침, 고열 헛소리 등.
- [x] **40. 🔥 [완료] NPC 심리·성격·인지 추론 & 12단계 행동 예측 엔진 (`NPCCognitiveDeductionEngine` & `PsychologyDecisionPipeline`)**:
  - **구현 대상**: [엔진: 신규] `src/world/psychology_engine.py`, [엔진: 확장] `src/world/cognitive_engine.py`, `src/world/state.py`, `src/world/two_pass_engine.py`
  - **검증 증명**: 구현 파일 `src/world/psychology_engine.py`, `src/world/cognitive_engine.py`, 통과 테스트 `tests/test_npc_psychology_state.py` (4 passed), `tests/test_npc_psychology_engine.py` (5 passed), `tests/test_npc_psychology_pipeline.py` (6 passed), 기존 `tests/test_cognitive_engine.py` (14 passed), 전체 `pytest tests/` (530 passed).
  - **기능**:
    - 1) 8대 성격 템플릿 아키타입 (`PERSONALITY_TEMPLATES`): 신중한 학자, 무모한 모험가, 헌신적인 기사, 냉소적인 용병, 야심찬 귀족, 다정한 치유사, 편집증 생존자, 광신적 이단심문관 (SHA256 결정론적 인스턴스 분산 탑재).
    - 2) 14종 복합 감정 시뮬레이션 (`EmotionEngine`): fear, anger, joy, grief, disgust, curiosity, pride, shame, guilt, hope, contempt, affection, anxiety, excitement 동시 활성화, 성향별 감수성 보정, 턴당 감쇠, 지배적 감정 산출 및 행동 점수 모디파이어.
    - 3) 독립 심리 스트레스 5단계 & 페르소나 붕괴 (`StressEngine`): 피로/사기와 분리된 0~100 스트레스, 90+ 붕괴 시 단순 패닉이 아닌 성격/가치관/대처기제에 따른 붕괴 행동(광기 난투, 비정한 배신 도주, 맹목적 공황, 종교적 마비 등) 직결.
    - 4) 인과 트라우마 활성화 체인 (`TraumaEngine`): 사건 키워드 매칭 ➔ 스트레스 증폭 ➔ 공포/불안 감정 유발 ➔ 회피/공격 편향 반환 및 안전 환경 노출 시 완화.
    - 5) 다자간 9축 관계 매트릭스 (`RelationshipEngine`): trust, affection, respect, fear, resentment, dependence, loyalty, suspicion, familiarity 다자간 맵 관리, 델타 5 이상 시 캐시 무효화 버전 증가, 플레이어 대상 시 레거시 필드(trust, affinity, respect, fear) 양방향 동기화.
    - 6) 메모리 심리 브릿지 (`MemoryPsychologyBridge`): 4+ 영구 앵커 우선 순위 인출, 5턴 윈도우 중복 기억 차단 및 기존 기억 강화.
    - 7) 3-Tier 평가 라우터 (`PsychologyDecisionPipeline`): Tier 1(일상/원거리 O(1) 감정 감쇠/스트레스 회복), Tier 2(동일 위치 국소 소란 < 5ms 경량 감지), Tier 3(직접 상호작용/대화/전투/트라우마 12단계 전체 파이프라인 및 trace 방출).
    - 8) 결정 캐시 (`DecisionCacheManager`): 상황 해시 + 상태 버전 + 스트레스 구간 기반 결정 캐싱 및 무효화.
    - 9) Two-Pass 및 인지 엔진 결합: `NPCCognitiveDeductionEngine.process_npc_cognitive_turn`과 직결되어 일반 턴에서도 12단계 심리 판단에 따라 `npc.intention` 및 `npc.goal` 자동 동기화.
    - 10) 외부 LLM 프롬프트 고도화 (`generate_external_llm_prompt`): 실시간 감정, 스트레스, 트라우마 상태 및 서술 경계 지침문(Strict Narrative Expression Boundary) 완전 탑재 (규칙 8 준수).

### [🔧 기존 엔진 배선(Wiring) & 통합 정비 — 클로드 코드리뷰 검증 기반]
> ⚠️ **[발견 경위]**: 2026-09-09 외부 Claude 정적 분석 피드백 → Antigravity(Gemini) 3개 서브에이전트 코드베이스 전수 교차 검증 완료. 설계/스키마 완성도는 높으나, 전체 모듈의 약 25%(16/64개)가 계단식 통합 2단계(팩트시트 슬롯 연결) 미진행 상태로 확인됨.

- [ ] **🔧 [배선 A] 16대 고립 엔진 → `TwoPassEngine` 팩트시트 슬롯 연결 (계단식 통합 2단계)**:
  - **진행 현황**:
    * **[x] `stealth_engine.py` (물리 은신/잠입/도청) 배선 완공**:
      - 구현 파일: `src/world/two_pass_engine.py` (`DeterministicFactSheet` 슬롯 탑재, `resolve_action_stealth`, `resolve_action_eavesdrop`), `src/world/state.py` (`Player.is_stealthed` 탑재 및 직렬화).
      - 통과 테스트: `tests/test_stealth_wiring.py` (4 passed), 전체 회귀 검증 `pytest tests/` (549 passed, 0 failed).
    * **[x] `mana_burn_engine.py` (마나 과부하 폭주 & 회로 파열) 배선 완공**:
      - 구현 파일: `src/world/two_pass_engine.py` (`DeterministicFactSheet` 슬롯 탑재, 턴 틱 냉각), `src/world/validator.py` (`pre_validate_action` 과열 침묵 및 과충전 검사), `src/world/state.py` (역직렬화 및 유효 최대 마나 감산).
    * **[x] `harvest_engine.py` (몬스터 부위 파괴 & 도축/갈무리) 배선 완공**:
      - 구현 파일: `src/world/two_pass_engine.py` (`DeterministicFactSheet.harvest_summary` 슬롯 탑재, 전투 중 `AnatomyHarvestEngine.attack_targeted_part` 육질 배율/부위 파괴/꼬리 참격 절단 필드 투하 연동, 비전투 `resolve_action_harvest` 시체/잔해 도축 연동), `src/world/validator.py` (살아있는 몬스터 도축 차단 및 약점 부위 키워드 확충, 착용 무기 접근 허용), `src/world/harvest_engine.py` (전용 도축 단검 우선 선별).
      - 통과 테스트: `tests/test_harvest_wiring.py` (6 passed), 전체 회귀 검증 `pytest tests/` (561 passed, 0 failed).
    * **[x] `attack_physics_engine.py` (물리 타격 3대 유형: 찌르기/베기/둔기 골절/피격 캔슬) 배선 완공**:
      - 구현 파일: `src/world/equipment.py` (`armor_penetration_pct` 방탄/장갑 관통 연산), `src/world/two_pass_engine.py` (`DeterministicFactSheet.attack_physics_summary` 슬롯 탑재, 돌진 가속도 운동에너지, 방어 관통 대미지, 참격 출혈, 둔기 골절 부상, 잽 적 행동 캔슬, 강인도 붕괴 연동), `src/world/validator.py` (물리 공격 동사 확충).
      - 통과 테스트: `tests/test_attack_physics_wiring.py` (6 passed), 전체 회귀 검증 `pytest tests/` (567 passed, 0 failed).
    * **[x] `campsite_engine.py` (야영지 구축/모닥불 온기/불침번 경계/야간 기습 및 생존 회복) 배선 완공**:
      - 구현 파일: `src/world/state.py` (`active_campsite` 상태 필드, `apply_update` 델타 동기화 및 `from_dict` 복원), `src/world/validator.py` (교전 중 야영/수면/모닥불 시도 사전 차단), `src/world/campsite_engine.py` (동행 NPC 감각 스탯 판정 확장), `src/world/two_pass_engine.py` (`DeterministicFactSheet.campsite_summary` 슬롯 탑재, 야영지 구축, 모닥불 점화, 불침번 편성, 야간 기습 몬스터 실제 스폰 및 안전 수면 생존 회복 결합).
      - 통과 테스트: `tests/test_campsite_wiring.py` (6 passed), 전체 회귀 검증 `pytest tests/` (573 passed, 0 failed).
    * **[x] `alcohol_engine.py` (주류 음용, 만취, 알코올 중독 및 숙취) 배선 완공**:
      - 구현 파일: `src/world/alcohol_engine.py` (`tick_metabolism` 자연 대사 틱 탑재), `src/world/state.py` (`Player.effective_agility` -3, `armor_class` +2, `effective_intelligence` -2, `effective_perception` -2 결정론적 리더 및 `apply_update`/`from_dict` 역직렬화 동기화), `src/world/validator.py` (음주 의도 식별 및 비선술집/골드부족/블랙아웃 차단, '수술/기술' 등 비주류 합성어 오인 차단), `src/world/two_pass_engine.py` (`DeterministicFactSheet.alcohol_summary` 슬롯 탑재, 턴 시작 간 알코올 대사 틱, 선술집 골드 구매 vs 가방 소지품 음용 리졸버 `resolve_action_drink`, 3단계 블랙아웃 동료 안전 호송 vs 단독 소매치기/저체온증 및 야영 숙면 익일 숙취 연동).
      - 통과 테스트: `tests/test_alcohol_wiring.py` (6 passed), 전체 회귀 검증 `pytest tests/` (579 passed, 0 failed).
    * **[x] `botany_engine.py` (독초 감별 & 약초 채집 야생 식물학) 배선 완공**:
      - 구현 파일: `src/world/state.py` (`Item`에 `true_spec_id`, `is_identified`, `is_poisonous_lookalike`, `origin_target_name` 필드 및 `from_dict` 역직렬화 완비), `src/world/validator.py` (`pre_validate_action`에서 교전 중 채집 차단, 비식생 실내 채집 차단, 미소지 감별 차단), `src/world/two_pass_engine.py` (`DeterministicFactSheet.botany_summary` 슬롯 탑재, `resolve_action_botany` 채집/감별/섭취 리졸버 및 `compute_pass1` 턴 루프 인벤토리 생성/소모/체력 델타 결합).
      - 통과 테스트: `tests/test_botany_wiring.py` (6 passed), 전체 회귀 검증 `pytest tests/` (585 passed, 0 failed).
    * **[ ] 미연결 7대 엔진 잔여**: `vein_restoration_engine`, `object_physics_engine`, `combat_time_track_engine`, `time_calendar_engine`, `siege_engine`, `stat_engine`, `outfit_engine`.
  - **작업 방식**: 엔진별로 `DeterministicFactSheet`에 슬롯 추가 → `compute_pass1` 적절 순서에 호출 삽입 → 3단계 전체 회귀 검증. 한 번에 1~2개씩 점진 통합 (빅뱅 통합 금지).
- [ ] **🔧 [배선 B] NPC 인지 엔진 4대 핵심 메서드 → 게임 루프 연결**:
  - **필요 사유**: `cognitive_engine.py`의 핵심 4대 메서드(`evaluate_player_hypothesis`, `predict_autonomous_next_intent`, `check_micro_leakage`, `generate_external_llm_prompt`)가 테스트에서만 호출되고, 유일하게 런타임 연결된 `process_npc_cognitive_turn` 내부에서도 호출하지 않음. "12단계 NPC 심리 인지 예측"이라는 마스터 문서 서술이 실제 돌아가는 게임 기준으로는 미달성 상태.
  - **작업 방식**: `process_npc_cognitive_turn` 내부에서 적절한 트리거 조건(플레이어 대화 중 가설 표출 → `evaluate_player_hypothesis`, 비전투 턴 종료 → `predict_autonomous_next_intent`, 대면 대화 시 → `check_micro_leakage`)에 따라 호출 분기 삽입.
- [ ] **🔧 [배선 C] NPC 심리 확장 필드 Write-Only 해소 → 결정론적 로직 소비**:
  - **필요 사유**: `NPCPersonality` 확장 6축(`patience`, `cunning`, `pride`, `rationality`, `neuroticism`, `deceit`) 및 심층 페르소나 필드(`life_defining_moment`, `value_hierarchy`, `coping_mechanism`, `public_mask`, `moral_justification`, `micro_leakage_traits`, `risk_tolerance`, `bdi_state`) 대부분이 생성/저장만 되고 어떤 결정론적 코드에서도 읽히지 않는 write-only 상태. 특히 `bdi_state`, `risk_tolerance`는 전 코드베이스에서 100% 미사용.
  - **작업 방식**: `process_npc_cognitive_turn`의 행동 분기 가중치에 확장 축 반영(예: `patience` 높으면 즉각 공격 억제, `pride` 높으면 굴복/항복 거부, `rationality` 높으면 감정적 폭주 억제). `predict_autonomous_next_intent`에서 `value_hierarchy`, `risk_tolerance`, `bdi_state` 소비.
- [ ] **🔧 [배선 D] NPC 에피소딕 기억 망각/가지치기 로직 구현 (`MemoryDecayPruner`)**:
  - **필요 사유**: `npc.memories`가 세션 내내 append만 되고 삭제/요약/트림 로직이 전무. AGENTS.md `<Two_Pass_Resource>` 규칙 3 "MEMORY limit: NPCs episodic memory must have truncation/summarization to avoid token overflow" 위반 상태. 장기 세션 시 세이브 파일 무한 증가 및 LLM 프롬프트 토큰 폭발 위험.
  - **작업 방식**: `state.py`의 `memory_decay_turn_interval`(현재 50턴) 활용하여 significance 1~2급 기억의 주기적 망각/요약. 백로그 25번(`MemoryDecayBiasEngine`)과 통합 설계. 기존 `relevant_memories(max_memories=5)` 슬라이싱은 프롬프트용 뷰만 제공하므로 실제 데이터 가지치기 별도 필요.
- [ ] **🔧 [정비 E] 죽은 모듈 정리 및 문서-코드 네이밍 불일치 수정**:
  - **필요 사유**: (1) `save_load_manager.py`는 `persistence.py`와 기능 완전 중복, `__init__.py`에도 미등록된 고아 파일. (2) `merchant_barter_engine.py`도 `__init__.py` 미등록 고아. (3) SESSION_HANDOFF.md L160의 `PERSONALITY_BREAKDOWN_WEIGHTS` 명칭이 실제 코드(`party_sanity_engine.py`)에서는 `PERSONALITY_BREAKDOWN_TABLES`로 구현됨 — 문서-코드 네이밍 불일치.
  - **작업 방식**: `save_load_manager.py` 삭제 여부 유저 확인 후 처리. `merchant_barter_engine.py`는 백로그 21번 통합 시 흡수. SESSION_HANDOFF.md 네이밍 수정.

### [🐛 구조적 버그 & 리포 위생 수정 — 클로드 2차 코드리뷰 검증 기반]
> ⚠️ **[발견 경위]**: 2026-09-10 외부 Claude 2차 정밀 코드리뷰 → Antigravity(Gemini) 3개 서브에이전트 전수 교차 검증 완료. 구조적 디싱크(시간/서사/인벤토리/소문) 및 리포 위생 문제 확인됨. 아래 항목은 작업량 기준 한 세션에 1~2개씩 수정 가능한 단위로 분리.

- [ ] **🐛 [수정 F] `README.md` 죽은 문서 전면 교체 [5분 단독 작업]**:
  - **증상**: README.md가 초기 5개 룸 Gradio 데모(WorldState 4~5클래스)를 설명. 실제 코드는 state.py 4396행/20개 클래스, 64개 엔진, 530+ 테스트의 완전히 다른 프로젝트. 누가 봐도 혼란 유발.
  - **처방**: README.md를 현행 MASTER_GAME_ARCHITECTURE.md + AGENTS.md 기반으로 전면 재작성. 기존 README는 `docs/legacy_readme_prototype.md`로 보관.
- [ ] **🐛 [수정 G] `__pycache__/*.pyc` Git 추적 제거 [5분 단독 작업]**:
  - **증상**: `.gitignore`에 `__pycache__/`가 있지만, 이미 커밋된 3개 pyc 파일이 git 추적 상태로 남아있음: `src/__pycache__/__init__.cpython-314.pyc`, `src/image/__pycache__/__init__.cpython-314.pyc`, `src/image/__pycache__/flux.cpython-314.pyc`. AGENTS.md `<Prompt_Rules>` 4번 "NO ARTIFACT COMMIT" 규칙 위반.
  - **처방**: `git rm --cached src/__pycache__/__init__.cpython-314.pyc src/image/__pycache__/__init__.cpython-314.pyc src/image/__pycache__/flux.cpython-314.pyc` 실행 후 커밋. `.gitignore`는 이미 정상.
- [x] **🐛 [완료: 수정 H] `sanitize_pass2_result` 서사-판정 모순 검증 로직 구현**:
  - **구현 대상**: [엔진: 확장] `src/world/two_pass_engine.py`, [테스트] `tests/test_two_pass_engine.py` (11 passed, 신규 4개 통과).
  - **증명**: 구현 메서드 `TwoPassEngine.reconcile_narration_with_fact_sheet`, 테스트 `tests/test_two_pass_engine.py::test_sanitize_pass2_result_*`.
  - **완료 기능**:
    1) Anti-Yes-Man 물리/논리 거부(`is_valid=False`) 시 강제 거부 서사로 전면 대체.
    2) 주사위 판정 실패(`is_success=False`)인데 LLM이 성공("성공", "돌파", "격파" 등) 날조 시 `[⚠️ 서사-판정 모순 감지]` 경고 로깅 및 `*(⚠️ 판정 결과: 실패...)*` 강제 팩트 보정 부착.
    3) 적 생존(`killed=False`)인데 사망 날조 시 `*(⚠️ 전투 지속: ...)*` 강제 팩트 부착.
    4) 적 사망(`killed=True`)인데 생존/도주 날조 시 `*(⚠️ 처치 확인: ...)*` 강제 팩트 부착.
- [x] **🐛 [완료: 수정 I] 장거리 이동 시 생존 틱 시간 비례 미적용 — "30분 하드코딩" 문제 완공 [중간 작업]**:
  - **구현 대상**: [엔진: 연동] `src/world/two_pass_engine.py` (`resolve_action_movement`, Step 1/Step 2.5), `src/world/weather_engine.py`, `src/world/thermal_engine.py`, `src/world/ration_engine.py`, `src/world/sleep_engine.py`, `src/world/party_sanity_engine.py`, `src/world/disease_engine.py`, [테스트] `tests/test_two_pass_engine.py` (2 passed, 13/13 passed).
  - **증명**: 구현 메서드 `TwoPassEngine.resolve_action_movement`, `TwoPassEngine.compute_pass1`, 테스트 `tests/test_two_pass_engine.py::test_long_distance_travel_scales_survival_ticks`, `tests/test_two_pass_engine.py::test_non_movement_action_keeps_default_30min_ticks`.
  - **완료 기능**:
    1) 이동 액션 발생 시 `GeographyEngine.calculate_segment_travel_hours` 기반 실제 소요시간(`mins`)을 사전 연산(`resolve_action_movement`).
    2) 계산된 `elapsed_minutes`를 Step 1의 모든 생존 및 환경 틱 함수에 전달:
       - `WeatherEngine.process_turn_survival_ticks` & `ThermalSurvivalEngine.process_turn_thermal_survival` (`delta_minutes` 비례 체온/젖음/동상/열사 틱 반복).
       - `RationSpoilageEngine.process_turn_spoilage` (`delta_minutes / 30.0` 비례 부패율 스케일링).
       - `SleepDeprivationEngine.process_turn_circadian` (`delta_minutes / 20.0` 비례 각성 턴/시간 누적, 각성제 소모, 피로 가산).
       - `PartySanityEngine.process_turn_sanity` (`delta_minutes / 30.0` 비례 지하 어둠 스트레스 및 붕괴 턴 차감).
       - `EpidemicEngine.process_turn_infections` (`delta_minutes / 30.0` 비례 잠복기 감소 및 질병 지속 피해).
       - `WeatherMagicSimulationEngine.tick_anomalies`, `ToxicologyToleranceEngine.process_time_metabolism`, `QuestEngine.check_turn_time_limits`, `CorpseEcologyEngine.process_turn_corpse_decay`, `PupilAdaptationEngine.tick_adaptation_seconds`, `EconomyEngine.restock_turn_ticks` 실시간 시간 비례 적용.
    3) 비이동 액션은 기존 30분 틱 / 10분 소요시간 정상 유지.
    4) 전체 539개 테스트 100% 무결점 통과 (BASELINE 537 대비 +2 신규 통과, 0 failed), `eval_runner.py --no-judge` 20턴 `Invalid transition rate: 0.0%` 달성.
- [ ] **🐛 [수정 J] `dijkstra_shortest_travel` 다중 구간 경로탐색 미연결 [중간 작업]**:
  - **증상**: `geography.py:269-336`에 다익스트라 최단 경로 탐색 구현 완료. 그러나 실제 플레이어 이동(`two_pass_engine.py:366-406`)은 현재 위치의 직접 연결된 `curr_loc.exits`만 검색. 여러 구간을 거치는 장거리 이동("늪지대까지 가라")은 매칭 불가. `dijkstra_shortest_travel`은 테스트에서만 호출됨(소문 확산 엔진도 별도 함수 `get_all_reachable_locations_with_distances` 사용).
  - **처방**: 이동 액션에서 직접 exit에 없는 목적지 요청 시, `dijkstra_shortest_travel`로 다중 구간 경로 계산 → 첫 구간만 즉시 이동 + 나머지 경유지를 `state`에 `pending_travel_waypoints`로 저장 → 다음 턴마다 자동 1구간 진행.
- [x] **🐛 [완료: 수정 K] 인벤토리 무제한 append 방지 & 기존 `outfit_engine.py` 가방 용량/찢어짐 엔진 배선 [중간 작업]**:
  - **구현 대상**: [엔진: 연동] `src/world/state.py` (L3401-3445 `pickup_item` 분기), [테스트] `tests/test_world_state.py` (3 passed).
  - **증명**: 구현 메서드 `WorldState.apply_update:pickup_item`, 테스트 `tests/test_world_state.py::test_pickup_item_*`, `tests/test_world_state.py::test_validator_rejects_picking_up_massive_furniture`.
  - **완료 기능**:
    1) `apply_update`의 `pickup_item` 분기에서 `OutfitMechanicsEngine.get_backpack_spec` 및 `evaluate_backpack_storage` 배선.
    2) 가방 파손 한계(`tear_weight_limit_kg`) 및 용적(1.5x) 초과 시 인벤토리 수납 거부(`REJECTED pickup ... — 가방 적재 한계 초과`) 및 필드 유지.
    3) 가구/구조물(`item_type in ["furniture", "structure"]` 또는 `can_store_in_bag=False`) 수납 시도 시 즉각 거부(`⛔ [...]은(는) 너무 거대하거나 구조물 형태이므로 가방에 넣을 수 없습니다.`).
    4) `state.py:3753`의 `update_environment` 등 LLM이 dict 대신 문자열/비-dict 입력 시의 타입 에러 예외 방어 보강 완료.
    5) 전체 537개 테스트 100% 무결점 통과 (BASELINE 534 대비 +3 신규 통과, 0 failed), `eval_runner.py --no-judge` 20턴 `Invalid transition rate: 0.0%` 달성.
- [ ] **🐛 [수정 L] NPC 처치 소문 무조건 발동 — 목격자 게이트(Witness Gate) 부재 [쉬운 작업]**:
  - **증상**: `two_pass_engine.py:689-699` — NPC 사망 시 같은 위치에 살아있는 목격자(다른 NPC/동료) 존재 여부를 검사하지 않고 무조건 `RumorDiffusionEngine.dispatch_event_rumor` 발동. 아무도 없는 던전 밀실에서 암살해도 `carrier="merchant"`로 소문 자동 발사.
  - **처방**: dispatch 호출 전에 `witnesses = [n for n in state.npcs.values() if n.location == state.player.location and n.id != target_npc.id and n.health > 0]` 체크 추가. `len(witnesses) == 0`이면 소문 미발동 (완전 범죄 성공). 동료 NPC만 있으면 동료 신뢰도에 따라 누설 확률 분기.

### [인프라, UI 및 플랫폼 시스템 (공통/플랫폼)]
> ⚠️ **[유저 절대 규칙] 찐찐 마지막 최종 업데이트 지정**: UI 연동, TTS 음성, 이미지 AI(SD LoRA) 연동 등은 전반적인 게임플레이, 전투, 생존 물리 시스템 및 밸런싱 작업이 100% 완료된 이후에 진행할 '찐찐 마지막 최종 업데이트'로 동결한다.

- [ ] **1. 인터랙티브 웹 UI 대시보드 (`InteractiveWebUI`) [찐찐 마지막 업데이트]**:
  - **구현 대상**: [UI: 신규] FastHTML/React 프론트엔드 대시보드
  - **기능**: 실시간 HP/MP/피로도/스트레스 게이지, 지리 도로망 2D 미니맵, 인벤토리 툴팁, SD 초상화 & TTS 오디오 플레이어.
- [ ] **2. 동적 BGM 믹서 & 크로스페이드 사운드 엔진 (`DynamicAudioPlayer`) [찐찐 마지막 업데이트]**:
  - **구현 대상**: [오디오: 신규] 파이썬 오디오 플레이어 & 믹서
  - **기능**: 전투 돌입 시 1.5초 크로스페이드(자연스러운 음악 전환), 환경 앰비언스 루프(비/바람/주점).
- [ ] **3. 모험 전기록(크로니클) 판타지 소설책 HTML/PDF 내보내기 (`ChronicleBookExporter`)**:
  - **구현 대상**: [툴: 신규] HTML/PDF 양장본 북 렌더러
  - **기능**: 30일간 모험 기록을 챕터별 삽화와 함께 진짜 판타지 양장본 소설책 형태로 자동 조판/내보내기.
- [ ] **4. 모딩(Mod) & 커스텀 시나리오/세계관 검증기 (`ModdingValidator`)**:
  - **구현 대상**: [툴: 신규] CLI 모드 검증 및 핫로더
  - **기능**: 신규 퀘스트, 몬스터, 세계관 JSON 무결성 자동 검증 및 원클릭 로딩.

### [집/노트북 환경 — 인게임 콘텐츠 및 데이터 구축]
- [ ] **🔥 [집 도착 즉시 최우선 착수] 실전 인터랙티브 스토리 플레이테스트 & 결핍 시스템 발굴**:
  - **진행 방식**: 유저와 AI가 실제 캐릭터로 1턴씩 실전 스토리를 플레이(행동 입력 -> 주사위/전투/대화/이동/수면/상호작용).
  - **목적**: "이런 상황에서 지금 시스템에 뭐가 없지? 어떻게 처리되지?"를 현장에서 1:1로 확인하며 말을 맞춤.
  - **효과**: 책상머리 뇌피셜 거품 엔진(도박엔진, 숟가락엔진 등)을 1초 만에 걸러내고, 실전에서 진짜 결핍된 핵심 시스템/상태이상만 핀포인트로 발굴하여 즉시 구현.
- [ ] **장비 템플릿 DB 50종 구축 (`data/templates/equipment_templates.json`)**:
  - 10개 슬롯(투구, 흉갑, 각반, 장갑, 부츠, 망토, 반지 20개, 귀걸이 8개, 무기)용 고유 아이템 스탯/방어력/내구도/소켓 데이터 완성 및 상점/루팅 생성기 연동.
- [ ] **SD 1.5 LoRA & NPC 7대 표정 팩 백그라운드 파이프라인 [찐찐 마지막 업데이트]**:
  - 인물 A 생성 시 기본 그림 1~2초 즉시 출력 후, 백그라운드(ADetailer 얼굴 인페인팅)로 7대 표정(기본, 놀람, 분노, 웃음, 패닉, 공포, 각성) 무지연 순차 생성(총 15초 내외).
- [ ] **TTS 한국어 음성 엔진 탑재 (Edge-TTS / Kokoro) [찐찐 마지막 업데이트]**:
  - NPC 성별/나이/톤별 보이스 매핑 및 자연스러운 한국어 음성 출력.
- [x] **🔥 [완료] 만물 사물 내구도 & 물리 파괴 엔진 (`UniversalObjectPhysicsEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/object_physics_engine.py`, [엔진: 확장] `src/world/state.py`, `src/world/__init__.py`
  - **검증 증명**: 구현 파일 `src/world/object_physics_engine.py`, 통과 테스트 `tests/test_object_physics_engine.py` (11 passed), 전체 `pytest tests/` (508 passed).
  - **기능**:
    - 1) 12대 만물 물리 재질 매트릭스(종이/유리/천/가죽/목재/흙/석재/철재/귀금속/유기물/목조건물/석조건물) 완전 구축.
    - 2) 의자, 책상, 침대, 책, 종이, 돌, 나무, 집, 유리병 등 세상의 모든 사물에 내구도, 경도(Hardness), 인화성, 취성 부여.
    - 3) 사물 파괴 시 재질 태그에 따른 결정론적 잔해 분해 스폰 (의자 ➔ 각목 즉석 무기 & 장작, 유리병 ➔ 날카로운 유리 파편 & 65dB 소음, 종이/책 ➔ 잿더미 & 텍스트 소멸, 바위 ➔ 돌멩이 & 자갈, 냄비/철창 ➔ 고철).
    - 4) 보관함(상자, 서랍장, 옷장) 파괴 시 수납 아이템 바닥 유출(Spill) 루팅 연동.
    - 5) 즉석 무기화(`improvise_weapon_stats`) 및 사물 수리(`repair_object`) 로직 완비.
    - 6) 규칙 6 준수 `traits` 탑재 및 규칙 8 준수 외부 대형 LLM(GPT/Claude) 파괴 서사 묘사 프롬프트 생성기 탑재.

---

##### 📅 [2026-09-14] 현재 세션 개발 현황

### 1. 이번 세션 구현 완료 핵심 시스템
1. **[배선 A-2] 마나 과부하 폭주 & 마나 회로 손상 엔진 (`mana_burn_engine.py`) 턴 루프 완전 배선**:
   - `src/world/validator.py`:
     * `ActionValidator.pre_validate_action` 스킬 시전 분기:
       - **회로 과열 침묵 검사**: `ManaBurnEngine.get_circuit_state(player).burnout_turns > 0`일 때 마법 시전 즉시 기각 (`is_valid = False`, `⚠️ [마나 회로 과열]...`).
       - **마나 부족 시 과충전 평가**: 마나 부족 시 `ManaBurnEngine.evaluate_overchannel` 호출. 대가/혈마법/변이 지식 미보유 일반 마법사는 엄격 차단, 자격 보유자는 `extra_flags["overchannel"]` 플래그 및 과충전 판정 정보 기록.
     * 일반 마법 공격 분기: 동일하게 `burnout_turns > 0` 회로 과열 침묵 차단.
   - `src/world/two_pass_engine.py`:
     * `DeterministicFactSheet`: `mana_burn_summary: Optional[str] = None` 슬롯 탑재 및 `to_prompt_context()` 프롬프트 렌더링/GM 서사 지침문 결합.
     * `compute_pass1` 턴 루프 결합:
       - **턴 틱 자연 냉각**: 턴 경과 시 플레이어 및 현재 위치 NPC의 `circuit.burnout_turns`를 1씩 자연 냉각 (0 도달 시 냉각 해제 로그 출력).
       - **스킬 과충전 실행**: `extra_flags["overchannel"]` 존재 시 `ManaBurnEngine.apply_overchannel_consequences`를 통해 HP 연소 차감, 회로 긴장 건전도 감소, 백래시 판정 및 에테르 오염/변이 발현을 확정 처리하고 `fact_sheet.mana_burn_summary`에 기록.
       - **회로 손상 신경통**: 일반 마나 소모 시에도 `circuit.stamina_drain_on_cast > 0`인 경우 기력 추가 소모 적용.
       - **마법 역류/백파이어 연계**: 고대어/언령 마법 실패로 인한 백파이어 시 `ManaBurnEngine.trigger_mana_backlash`를 직접 호출하여 회로 파열 흉터, 최대 MP 페널티, 과열 침묵, 비전 파편 충격파 발생.
       - **회로 치료 연계**: 마나 안정제, 은침 소통술, 성수 정화 복용/치료 시 `ManaBurnEngine.repair_circuit` 호출 및 델타 동기화.
   - `src/world/state.py`:
     * `WorldState.apply_update`: `mana_burn_state` 델타 수신 및 플레이어 상태 동기화 지원.
     * `WorldState.from_dict`: 플레이어 역직렬화 시 `mana_burn_state` 완벽 복원.
     * `Player.max_mana_effective` 및 `NPC.max_mana_effective`: 회로 파열 흉터로 인한 `max_mp_penalty`를 유효 최대 마나에서 결정론적으로 감산 반영 (Deterministic Reader 보장).
   - `tests/test_mana_burn_wiring.py`:
     * 신규 통합 배선 테스트 6종 구축 및 100% 통과:
       - `test_mana_burnout_silence_blocks_magic`: 회로 과열 침묵 시 마법 영창 물리적 차단 검증.
       - `test_unqualified_caster_cannot_overchannel`: 일반 마법사의 생명력 연소 과충전 불가 검증.
       - `test_blood_mage_overchannel_executes_in_pass1`: 혈마법사의 생명력 연소 과충전 영창 성공 및 회로 손상/프롬프트 반영 검증.
       - `test_circuit_burnout_tick_cooling`: 턴 경과 시 마나 과열 침묵 자연 냉각 틱 검증.
       - `test_max_mp_penalty_deterministic_reader`: 회로 흉터 `max_mp_penalty`의 유효 최대 마나 감산 결정론적 리더 검증.
       - `test_mana_circuit_remedy_repair`: 마나 안정제 복용을 통한 회로 건전도 회복 검증.

2. **[배선 A-4] 물리 타격 3대 유형 & 피격 캔슬 엔진 (`attack_physics_engine.py`) 턴 루프 완전 배선**:
   - `src/world/equipment.py`:
     * `apply_armor_durability_and_mitigation`에 `armor_penetration_pct: float = 0.0` 인자 추가. 방어구의 기본 경감률을 관통률만큼 곱연산 감산(`effective_mitigation = mitigation * (1.0 - armor_penetration_pct)`)하여 돌진 찌르기 및 철갑탄 방어 관통 대미지 결정론적 계산.
   - `src/world/validator.py`:
     * 물리 공격 동사("내려친", "후려친", "내려쳐", "후려쳐", "잽", "정권", "스트레이트", "사격", "쏜다", "발사") 키워드 확충하여 관형/현재형 물리 타격 액션이 정상 검증 통과되도록 보강.
   - `src/world/two_pass_engine.py`:
     * `DeterministicFactSheet`: `attack_physics_summary: Optional[str] = None` 슬롯 탑재 및 `to_prompt_context()` GM 서사 지침문 결합.
     * `compute_pass1` 전투 섹션 결합:
       - **물리 태그 및 돌진 거리 추출**: 행동 텍스트 및 무기 속성 기반 `atk_tags` 자동 식별, 돌진 거리(`distance_charge_m`) 추출.
       - **AttackPhysicsEngine 평가**: `evaluate_attack_physics` 호출하여 운동에너지 대미지 배율, 방어구 관통률, 출혈/골절 확률, 행동 캔슬 여부 판정.
       - **참격 출혈 및 둔기 골절 연동**: `StatusEffectEngine.apply_status(target, "bleeding", ...)` 및 `target.injuries.append("blunt_fracture_...")` 상태이상 결정론적 부여.
       - **잽 적 행동 캔슬 및 강인도 붕괴**: `cancelled_opponent_action` 시 적의 예정된 공격/영창 차단(`interrupted_action = True`), 대상 강인도(`poise`) 감산 및 그로기 유도.
   - `tests/test_attack_physics_wiring.py`:
     * 신규 통합 배선 테스트 6종 구축 및 100% 통과:
       - `test_charge_thrust_kinetic_damage_and_armor_penetration`: 돌진 찌르기 가속도 운동에너지 배율 및 방어 관통 대미지 검증.
       - `test_slash_inflicts_bleeding_status`: 참격 공격 시 고민첩 비례 출혈 부여 검증.
       - `test_blunt_heavy_strike_causes_bone_fracture`: 둔기 강타 시 고근력 비례 뼈 골절 부상 부여 검증.
       - `test_quick_jab_cancels_enemy_action`: 기습 잽 공격으로 적의 공격 의도 캔슬 검증.
       - `test_physics_summary_in_fact_sheet_prompt_context`: 물리 결과가 `fact_sheet` 프롬프트에 정상 주입되는지 검증.
       - `test_two_pass_engine_full_turn_attack_physics_integration`: `TwoPassEngine.process_turn` 전체 파이프라인 무결점 통과 검증.

2. **[배선 A-5] 야영/모닥불 온기 및 야외 생존 회복 엔진 (`campsite_engine.py`) 턴 루프 완전 배선**:
   - `src/world/state.py`: `active_campsite` 상태 필드, `apply_update` 델타 동기화 및 `from_dict` 복원 완비.
   - `src/world/validator.py`: 교전 중 야영/수면/모닥불 시도 사전 차단.
   - `src/world/two_pass_engine.py`: `DeterministicFactSheet.campsite_summary` 슬롯 탑재, 야영지 구축, 모닥불 점화, 불침번 편성, 야간 기습 몬스터 실제 스폰 및 안전 수면 생존 회복 결합.
   - `tests/test_campsite_wiring.py`: 6 passed.

3. **[배선 A-6] 주류 음용/만취/알코올 중독 및 숙취 엔진 (`alcohol_engine.py`) 턴 루프 완전 배선**:
   - `src/world/alcohol_engine.py`: `tick_metabolism` 자연 대사 틱 탑재.
   - `src/world/state.py`: `Player.effective_agility` -3, `armor_class` +2, `effective_intelligence` -2, `effective_perception` -2 결정론적 프로퍼티 리더 탑재.
   - `src/world/validator.py`: 음주 의도 식별 및 비선술집/골드부족/블랙아웃 차단, '수술/기술' 등 비주류 합성어 오인 차단.
   - `src/world/two_pass_engine.py`: `DeterministicFactSheet.alcohol_summary` 슬롯 탑재, 턴 시작 알코올 대사 틱, 선술집 골드 구매 vs 가방 소지품 음용 `resolve_action_drink` 리졸버, 3단계 블랙아웃 호송/소매치기/저체온증 및 야영 숙면 익일 숙취 연동.
   - `tests/test_alcohol_wiring.py`: 6 passed.

4. **[배선 A-7] 독초 감별 & 야생 약초 채집 식물학 엔진 (`botany_engine.py`) 턴 루프 완전 배선**:
   - `src/world/state.py`:
     * `Item` 데이터클래스에 식물학 전용 4대 필드 탑재: `true_spec_id: str = ""`, `is_identified: bool = True`, `is_poisonous_lookalike: bool = False`, `origin_target_name: str = ""`.
     * `Item.from_dict` 역직렬화 safe_init 완비로 기존 세이브 데이터 100% 하위 호환 복원 지원.
   - `src/world/validator.py`:
     * 교전 중 채집 차단: 위치 내 생존 적대적(`disposition == "hostile"`) NPC 감지 시 채집 차단 (`ActionValidator.pre_validate_action`).
     * 비식생 실내 채집 차단: 선술집, 주점, 감옥, 밀실 등 석벽/인공 바닥 실내 환경에서 야생 채집 차단.
     * 미소지 정밀 감별 차단: 가방에 감별 대상 표본이 없을 시 액션 사전 기각.
   - `src/world/two_pass_engine.py`:
     * `DeterministicFactSheet`: `botany_summary: Optional[str] = None` 슬롯 탑재 및 `to_prompt_context()` GM 서사 지침문 결합.
     * `resolve_action_botany`: 야생 채집(`forage`), 정밀 감별(`identify`), 섭취/달임(`consume`) 3대 액션 완전 분기 파싱.
     * `compute_pass1` 턴 루프 결합:
       - **채집 성공**: `Item` 실체 생성 및 플레이어 인벤토리 등록 (`state.items`, `state.player.inventory`).
       - **대실패(Roll 1/DC-4 미만)**: 치명적 위장종(예: 송이버섯 외형의 '독우산광대버섯') 획득 및 미감별(`unidentified`) 태그 부여.
       - **정밀 감별**: `HerbalismBotanyEngine.identify_plant` 판정 성공 시 위장 해제 및 진짜 독초 스펙/이름 폭로.
       - **섭취/달임**: 진짜 약초 섭취 시 체력 회복/지혈/피로 개선; 맹독초 섭취 시 즉시 독성 피해 및 패혈증/심정지 치명 상태이상 격발, 인벤토리 아이템 소모.
   - `tests/test_botany_wiring.py`:
     * 신규 통합 배선 테스트 6종 구축 및 100% 통과:
       - `test_botany_forage_success_inventory_and_pass1`: 야생 약초 채집 성공 시 인벤토리 등록, 아이템 생성 및 Pass 1 FactSheet 연동 검증.
       - `test_botany_forage_lookalike_critical_failure`: 채집 대실패 시 외형 위장 맹독 유사종(독우산광대버섯) 채집 검증.
       - `test_botany_identify_reveals_lookalike`: 정밀 감별 성공 시 위장된 맹독 유사종의 정체 폭로 및 아이템 갱신 검증.
       - `test_botany_consume_genuine_herb_heals`: 진짜 약초(지혈 이끼) 섭취 시 체력 회복, 피로 개선 및 인벤토리 소모 검증.
       - `test_botany_consume_toxic_lookalike_inflicts_poison`: 미감별 맹독 버섯 섭취 시 독 대미지 피격 및 중독 상태이상 격발 검증.
       - `test_botany_validator_combat_and_indoor_prevention`: ActionValidator 사전 검증(교전 중 채집 차단, 비식생 실내 채집 차단, 미소지 감별 차단) 검증.

---

### [디자인/아키텍처 Q&A 기록]
- **Q. 옥토패스 트래블러 스타일 2D-3D HD-2D 도트 그래픽 구현 시, 2D 좌표와 노드-엣지 그래프만으로 장비/건물/몬스터/외형 모델링 및 그래픽 표현이 가능한가?**:
  - **A. 공간 위상(Topology)과 시각 표현(Visual Presentation)의 분리 원칙**:
    1) 2D 유클리드 좌표 + 노드-엣지 그래프는 **"세계의 뼈대와 연결 구조(어디에 무엇이 있고 어떻게 이동/충돌하는가)"**를 정의하는 순수 데이터 레이어임.
    2) 외형(시각적 렌더링)은 좌표 자체가 아니라 엔티티 데이터에 부여된 **결정론적 태그(`traits`), 메타데이터 템플릿(`visual_profile`, 재질, 양식, 손상도), 프로시저럴 타일셋/페이퍼돌 스프라이트 조립 규칙**을 통해 생성됨.
    3) **건물/맵**: 좌표(x, y, w, h) + 연결 노드(문/벽/창문) + 건축 테마(예: '고딕 양식 석조', '퇴색된 참나무') -> 타일셋 자동 배치 및 2.5D 깊이감(Z-축 빌보드/스프라이트) 부여.
    4) **장비/캐릭터**: 장비 부위 + 소재(강철, 미스릴) + 제작 양식 + 상태(녹슨, 피묻은) -> 도트 레이어 합성(Paper-Doll 스프라이트 시스템: 몸체 베이스 + 의복 레이어 + 무기 오버레이).
    5) **LLM의 역할**: LLM은 픽셀을 직접 그리는 것이 아니라 100% 결정론적 팩트시트를 받아 시각적/감각적 서사(Pass 2)를 묘사하며, 실제 그래픽 렌더러는 파이썬 월드 스테이트의 결정론적 시각 데이터 구조를 읽어 스프라이트/도트 그래픽을 화면에 렌더링함.

---

### 2. 테스트 및 평가 검증 상태
- **프로젝트 전체 585개 단위 테스트 100% 무결점 통과 (회귀 결함 0건, BASELINE 579 + 신규 배선 6 = 585 passed)**:
  - `tests/test_botany_wiring.py`: **6 passed in 1.13s**.
  - `tests/test_botany_engine.py`: 5 passed.
  - `tests/test_alcohol_wiring.py`: 6 passed.
  - `tests/test_campsite_wiring.py`: 6 passed.
  - `tests/test_attack_physics_wiring.py`: 6 passed.
  - `tests/test_harvest_wiring.py`: 6 passed.
  - `tests/test_mana_burn_wiring.py`: 6 passed.
  - `tests/test_stealth_wiring.py`: 4 passed.
  - `pytest tests/`: **585 passed in 211.71s**.
- **DoD Gate Eval Runner 검증**:
  - `python eval_runner.py --no-judge` (20턴 실전 시뮬레이션): **`Invalid transition rate: 0.0%`** 완벽 달성.
- **Static Analysis Gate**:
  - `pyflakes` 및 `python -m compileall src/ -q`: **구문 오류 및 미사용 import 0건 통과**.

### 3. 다음 세션 작업 착수 안내 (Next Step)
- **현재 완료 상태**:
  - **[배선 A-1] `stealth_engine.py` (물리 은신/잠입/도청) 배선 완공**
  - **[배선 A-2] `mana_burn_engine.py` (마나 과부하 폭주 & 회로 파열) 배선 완공**
  - **[배선 A-3] `harvest_engine.py` (몬스터 부위 파괴 & 도축/갈무리) 배선 완공**
  - **[배선 A-4] `attack_physics_engine.py` (물리 타격 3대 유형: 찌르기/베기/둔기 골절/피격 캔슬) 배선 완공**
  - **[배선 A-5] `campsite_engine.py` (야영지 구축/모닥불 온기/불침번 경계/야간 기습 및 생존 회복) 배선 완공**
  - **[배선 A-6] `alcohol_engine.py` (주류 음용, 만취, 알코올 중독 및 숙취) 배선 완공**
  - **[배선 A-7] `botany_engine.py` (독초 감별 & 약초 채집 야생 식물학) 배선 완공**
- **다음 잔여 배선 후속 진행 (잔여 7개 엔진)**:
  - **차기 타겟: [배선 A-8] `vein_restoration_engine.py` (마나 맥로 손상 및 혈맥 재생) 배선**
  - 후속 대기: [배선 A-9] `object_physics_engine.py` (사물 투척/파괴/엄폐/가구 물리) 배선



