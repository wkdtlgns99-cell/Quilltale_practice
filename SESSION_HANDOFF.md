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

### [똥컴/학원 환경 — 순수 시스템/로직/엔진 고도화]
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
- [ ] **🔥 [신규 백로그] 세계관별 성장 스케일 프리셋 시스템 (`WorldPowerScalePresets`)**:
  - **구현 대상**: `src/world/stat_engine.py`, `src/world/state.py`, `cosmology_templates.json`
  - **기능**: 세계관마다 다른 레벨 상한 및 스탯 성장률 프리셋 결합:
    - 1. 로우 판타지(발더게3형): 최대 12~20렙, 렙당 스탯 0~1개, 상한 20~30, 대미지 10~50.
    - 2. 스탠다드 판타지(D&D형): 최대 50렙, 렙당 스탯 2~3개, 상한 50~100.
    - 3. 하이퍼 인플레(메이플형): 최대 300렙, 렙당 스탯 5개, 스탯 수천, 대미지 수만~수억.
    - 4. 선협/무협(경지 돌파형): 평소 렙업 없음, 경지 돌파 시 스탯 10배 폭증.
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
- [x] **40. 🔥 [1차 완공 / 향후 Claude/GPT 세분화 대조 예정] NPC 인지 추론 & 행동 예측 엔진 (`NPCCognitiveDeductionEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/cognitive_engine.py`, [엔진: 확장] `src/world/state.py`
  - **검증 증명**: 구현 파일 `src/world/cognitive_engine.py`, 통과 테스트 `tests/test_cognitive_engine.py` (11 passed).
  - **기능**:
    - 1) 10대 대인 태도 매트릭스 확장: 기존 3대(affinity, fear, debt) + trust(신뢰), respect(존경), envy(질투), pity(연민), dominance(지배욕), curiosity(호기심), disgust(혐오).
    - 2) 12대 심리 성향 축 확장: 기존 6대(altruism, greed, courage, suspicion, loyalty, aggression) + patience(인내), cunning(교활), pride(자존심), rationality(이성), neuroticism(신경증), deceit(기만).
    - 3) 20대 심층 페르소나 시스템: life_defining_moment(생애 분기점), value_hierarchy(가치관 위계), coping_mechanism(스트레스 대처), public_mask(사회적 가면), moral_justification(자기합리화), micro_leakage_traits(미세 신체 언어 복선), risk_tolerance(위험 감수성), bdi_state(세부 계획).
    - 4) 안티 예스맨 가설 검증 (`evaluate_player_hypothesis`): 플레이어의 주관적 의심/가설("저 놈이 독살하려 한다" 등)을 성향, 금기, 인벤토리, 태도와 전수 대조하여 6단계 판정(IMPOSSIBLE ~ CONFIRMED) 및 반박/수긍 증거 도출, GM 서사용 팩트 지침문 생성.
    - 5) 자율 행동 예측 (`predict_autonomous_next_intent`): 결핍/욕망/공포/원한 우선순위에 따라 12대 행동 범주 중 최적의 계획을 도출하고 `npc.intention` 및 `npc.goal` 자동 갱신.
    - 6) 미세 신체 언어 간파 (`check_micro_leakage`): 플레이어 감각 vs NPC 기만 대항 판정으로 속내 복선 노출.
    - 7) 외부 LLM 프롬프트 생성 (`generate_external_llm_prompt`): GPT-4o/Claude 3.5 연동용 고밀도 심리 프로필 생성 (규칙 8 준수).
    - 8) 향후 계획: 나중에 Claude나 GPT와 대조하여 행동 범주 및 심리 알고리즘을 한층 더 정밀하게 세분화 예정.

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

## 📅 [2026-09-07] 현재 세션 개발 현황

### 1. 이번 세션 구현 완료 핵심 시스템
1. **깃허브 최신 리포지토리 동기화 및 전체 아키텍처 점검 완료**:
   - `git pull`을 통해 물리/생존 엔진 및 대규모 템플릿(대륙 120종, 권역 304종 등) 무결점 수신.
   - 워킹 트리 클린 상태 및 474개 기존 테스트 100% 정상 작동 확인.
2. **NPC 10대 대인 태도 매트릭스 (`10-Factor Attitude Matrix`) 전격 구축**:
   - 기존 3대(affinity, fear, debt) 한계를 탈피하여 인간 관계의 복합 다면성을 완벽 수치화:
     - `trust`(신뢰도, 0~100): 상대의 약속/정보를 믿는 정도.
     - `respect`(존경 vs 경멸, 0~100): 실력과 도덕성에 대한 평가.
     - `envy`(질투/시기, 0~100): 상대의 부/재능에 대한 시기심.
     - `pity`(동정/연민, 0~100): 상대의 불행에 대한 마음의 흔들림.
     - `dominance`(지배욕 vs 복종심, 0~100): 상대를 통제하고 부리려는 욕구.
     - `curiosity`(호기심/탐구욕, 0~100): 상대의 내력/비밀을 캐내려는 집착.
     - `disgust`(도덕적/생리적 혐오, 0~100): 존재나 행태에 느끼는 거부감.
   - `src/world/state.py` 내 `NPC` 클래스 및 `from_dict` 역직렬화 100% 하위 호환 탑재.
3. **NPC 12대 심리 성향 축 (`12-Axis Personality`) 확장**:
   - `NPCPersonality`에 기존 6대(altruism, greed, courage, suspicion, loyalty, aggression) 외 6개 본성 축 추가:
     - `patience`(인내심 vs 충동성), `cunning`(교활함 vs 우직함), `pride`(자존심/오만 vs 굴신), `rationality`(이성/논리 vs 감정/격정), `neuroticism`(신경증/불안 vs 정서안정), `deceit`(기만/위선 vs 솔직함).
     - 규칙 6 준수: `traits: list[str] = field(default_factory=list)` 기본 탑재.
4. **NPC 20대 심층 페르소나 시스템 (`20-Factor Deep Persona`) 구축**:
   - `life_defining_moment`(생애 결정적 분기점): 성격을 결정지은 과거 사건.
   - `value_hierarchy`(가치관 우선순위): 한계 상황에서 포기하지 못하는 가치 순서(`[survival, wealth, honor, family, faith]`).
   - `coping_mechanism`(스트레스 대처 기제): 한계 도달 시 보이는 신체/행동 반응.
   - `public_mask`(사회적 가면): 겉으로 연기하는 가짜 인격.
   - `moral_justification`(자기합리화 논리): 악행 시 스스로를 정당화하는 논리.
   - `micro_leakage_traits`(무의식적 속내 복선): 거짓말이나 살의가 샐 때 나오는 신체 언어 버릇.
   - `risk_tolerance`(위험 감수성, 0~100): 도박적 성향 vs 안전제일.
   - `bdi_state`(고도화 BDI 세부 계획 및 신념 메타데이터).
5. **NPC 인지 추론 & 행동 예측 엔진 (`NPCCognitiveDeductionEngine`) 1차 완공 (`src/world/cognitive_engine.py`)**:
   - **안티 예스맨 가설 검증 (`evaluate_player_hypothesis`)**:
     - 플레이어가 "저 녀석이 날 독살하려 한다" 같은 주관적 의심을 표출했을 때, NPC의 12대 성향, 20대 페르소나, 도덕적 금기(`taboo`), 실제 소지품(인벤토리), 10대 태도를 전수 대조.
     - `contradicting_evidence` vs `supporting_evidence`를 가중치로 집계하여 6단계 판정(`IMPOSSIBLE` ~ `CONFIRMED`) 및 타당도 점수(0~100%) 산출.
     - GM용 서사 지침문(`gm_anti_yesman_verdict`)을 생성하여 LLM이 플레이어의 착각에 영합하지 않고 팩트로 반박하거나 정당한 복선을 제공하도록 제어.
   - **자율 다음 행동 예측 (`predict_autonomous_next_intent`)**:
     - 결핍/욕망/공포/원한 우선순위(생존 위협 ➔ 도주, 재정 압박/탐욕 ➔ 절도, 원한/공격성 ➔ 암살, 치부 은폐 ➔ 매수/밀고, 호감/신뢰 ➔ 조력)에 따라 구체적 다음 계획(`concrete_plan`), 인과 사슬(`motive_chain`), 필요 도구, 복선 단서를 결정론적으로 도출.
     - 도출된 계획을 `npc.intention` 및 `npc.goal`에 자동 동기화.
   - **미세 신체 언어 간파 (`check_micro_leakage`)**:
     - 플레이어 감각(Perception) vs NPC 기만/교활 주사위 대항 판정으로 거짓말 복선 노출.
   - **10대 태도 동적 갱신 (`update_attitude`)**:
     - 이벤트 및 플레이어 행동에 따른 태도 수치 증감 및 0~100(-100~+100) 안전 클램핑.
   - **외부 AI(GPT-4o/Claude 3.5) 연동 프롬프트 생성 (`generate_external_llm_prompt`)**:
     - 규칙 8 준수: 외부 대규모 LLM에 복사하여 심층 심리 연기 및 복선 세분화를 즉시 수행할 수 있는 실행 프롬프트 생성 함수 탑재.
   - **향후 계획 명시**:
     - 나중에 Claude나 GPT와 대조하여 행동 범주, 감정 모델, 심리 알고리즘을 한층 더 정밀하게 세분화 예정.
6. **백로그 11번 (현상금 사냥꾼 & 추적자 AI) 단일 뇌 아키텍처 완전 흡수 통합**:
   - `BountyEngine`의 수배 장부 및 검문 로직을 `NPCCognitiveDeductionEngine.process_npc_cognitive_turn`과 직결.
   - 탐욕 사냥꾼의 기습(`bounty_hunter_ambush`), 비겁한 부랑자의 밀고(`bounty_snitch`), 충직한 동료의 도주로 경고(`friendly_warning`), 경비병의 체포(`guard_arrest`)를 성격·태도 가중치에 따라 결정론적 연산.
   - `src/world/two_pass_engine.py`의 매 턴 비전투 NPC 행동 루프를 `NPCCognitiveDeductionEngine`으로 일원화 연동 완료.

7. **백로그 9번 성벽 공성전 & 대규모 전열 전술 엔진 (`SiegeWarfareEngine`) 완공 (`src/world/siege_engine.py`)**:
   - **다층 방어 구조물 물리 내구도 원칙 탑재**:
     - 성벽(`wall_durability`), 성문(`gate_durability`), 해자 방호도(`moat_durability`), 흉벽 엄폐도(`battlement_durability`), 방어탑, 마도 결계 내구도 완전 구현.
     - 정주지(`Settlement`) 인프라 스탯(`wall_defense_tier`, `gate_type`, `moat_type`, `battlement_type`, `elevation_meters`, `siege_supplies_days`)을 읽어 자동 조립.
   - **5대 공성 병기 내구도 및 운용**:
     - 충차(Battering Ram), 평형추 트레뷰셋, 망고넬 투석기, 철갑 공성탑, 발리스타 노포, 공병 지하 갱도 인스턴스화.
     - 물리/화공 피해 감쇠(hardness), 파괴 판정, 화공 취약성, 수리 메커니즘 탑재.
   - **해자 메우기(Moat filling) 역학**:
     - 해자 내구도가 0(평토화)이 되기 전까지 충차 및 공성탑의 성벽/성문 접안을 엄격히 차단.
   - **3군 전열 진형 상성 매트릭스**:
     - 장창 방패벽(기병 돌격 반사 2.0x, 화살비 70% 차단), 쐐기 기병 돌격(비방진 보병 1.8x 돌파 학살, 방패벽 충돌 시 자멸), 일제 사격선(고도/흉벽 보정), 위장 후퇴, 산개 교란.
   - **군대 사기(Morale) & 패주(Rout) 카스케이드**:
     - 지휘관 부상/외벽 완파/식량 고갈/사상자 50% 초과 시 사기 폭락 및 전면 패주 판정.
   - **특공대 야간 침투 공작 (`execute_commando_action`)**:
     - 투석기 방화, 성문 빗장 개방, 군량고 방화, 지휘관 저격.
   - **규칙 8 준수 외부 대형 LLM(GPT/Claude) 프롬프트 생성기 (`generate_external_llm_prompt`)**:
     - 결정론적 수치(내구도 잔여량, 사상자, 사기, 진형) 기반 처절한 전장 문학 생성 프롬프트 탑재.

8. **만물 사물 내구도 & 물리 파괴 엔진 (`UniversalObjectPhysicsEngine`) 완공 (`src/world/object_physics_engine.py`)**:
   - **12대 전천후 물리 재질 분류 체계 구축**:
     - `paper`(종이), `glass`(유리), `cloth`(천), `leather`(가죽), `wood`(목재), `stone`(석재), `metal`(철재), `precious_metal`(귀금속), `clay`(점토), `flesh`(유기물), `structure_wood`(목조건물), `structure_stone`(석조건물).
   - **사물 재질 태그 및 지능형 키워드 휴리스틱 매핑 (`resolve_material`)**:
     - 명시적 `material` 및 `mat:` 태그 외에도 '낡은 참나무 의자' ➔ `wood`, '비밀 지령 양피지 서한' ➔ `paper` 등 한국어 조사/어미 오인식 완벽 차단.
   - **타격·방화·부식 물리 역학 (`damage_object`, `ignite_object`)**:
     - 재질 경도(Hardness) 피해 감쇠, 인화율 배율, 취성 분쇄, 산성 부식 가속.
   - **사물 파괴 시 결정론적 잔해 분해 스폰**:
     - 의자 ➔ 각목(즉석 둔기 무기) & 장작 / 유리병 ➔ 날카로운 유리 파편 & 65dB 소음 / 책 ➔ 잿더미 & 텍스트 소멸 / 바위 ➔ 돌멩이 & 자갈 / 냄비 ➔ 고철.
   - **보관함(상자, 서랍, 궤짝) 파괴 시 수납 아이템 바닥 유출 루팅 연동**.
   - **즉석 무기화 스탯 산출(`improvise_weapon_stats`) 및 사물 수리(`repair_object`) 로직 완비**.
   - **규칙 8 준수 외부 대형 LLM 파괴 연출 프롬프트 생성기(`generate_external_llm_prompt`) 탑재**.

### 2. 테스트 및 평가 검증 상태
- **프로젝트 전체 508개 단위 테스트 100% 무결점 통과 (회귀 결함 0건, BASELINE 대비 +23 신규 통과)**:
  - `tests/test_object_physics_engine.py`: 11개 테스트 전원 통과 (12대 재질 판별, 목재 의자 각목/장작 파편 분해, 종이 문서 전소/텍스트 소멸, 유리병 파쇄/65dB 소음, 산성 부식, 상자 파괴 시 수납 아이템 유출, 즉석 무기화, 사물 수리, 벌목/채석, 세이브/로드 호환성, LLM 프롬프트).
  - `tests/test_siege_engine.py`: 12개 테스트 전원 통과.
  - `pytest tests/`: **508 passed in 211.89s**.
- **DoD Gate Eval Runner 검증**:
  - `python eval_runner.py --no-judge` (20턴): **`Invalid transition rate: 0.0%`** 달성.
- **Static Analysis**: `py_compile` 문법 오류 0건 검증 완료.

### 3. 다음 세션 작업 착수 안내 (Next Step)
- **현재 완료 상태**:
  - 만물 사물 내구도 & 물리 파괴 엔진 (`UniversalObjectPhysicsEngine`) 완공.
  - 성벽 공성전 & 대규모 전열 전술 엔진 (`SiegeWarfareEngine` / 백로그 9번) 완공.
  - NPC 인지 추론 & 행동 예측 엔진 (`NPCCognitiveDeductionEngine` / 백로그 40번) 완공.
  - 현상금 수배자 & 추적자 AI 엔진 (`BountyHunterEngine` / 백로그 11번) 단일 뇌 아키텍처 흡수 통합 완공.
- **다음 작업 (유저 결정에 따른 후속 진행)**:
  - **가문 혈통 & 세대 계승 영구 레거시 엔진 (`LineageLegacyEngine` / 백로그 10번 - legacy.py 확장)**
    * 영구 사망 시 유언장 집행, 직계 자손에게 가보/특성/영지/원수 가문 적대 관계 100% 인계.


