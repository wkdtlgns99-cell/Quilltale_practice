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
- [ ] **5. 날씨·체온 저체온증/열사병 생존 물리 엔진 (`ThermalSurvivalEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/thermal_engine.py`
  - **기능**: 영하 기온 + 젖은 옷 = 저체온증(턴당 체력 감소, 손 떨림 디버프), 화기 피우기/방한 모피 의무화.
- [ ] **6. 던전 구조적 붕괴 & 산소 고갈 질식 엔진 (`CaveCollapseEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/cave_in_engine.py`
  - **기능**: 폭발 마법 시전 시 동굴 천장 붕괴 판정, 밀폐 지하 석실 산소 고갈(횃불 꺼짐, 질식사).
- [ ] **7. 전염병·역병·기생충 감염 생체 엔진 (`EpidemicEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/disease_engine.py`
  - **기능**: 쥐떼 교전 시 흑사병 감염, 오염된 식수 음용 시 이질, 잠복기 후 발열/환각 및 약초 치료.
- [ ] **8. 마나 과부하 폭주 & 에테르 오염 변이 엔진 (`ManaBurnEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/mana_burn_engine.py`
  - **기능**: 최대 마나 초과 영창 시 신체 혈관 파열(자해 피해), 고위 마법 난사 구역 에테르 변이체 스폰.
- [ ] **9. 성벽 공성전 & 대규모 전열 전술 엔진 (`SiegeWarfareEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/siege_engine.py`
  - **기능**: 투석기/공성추 내구도, 성문 돌파율, 병력 사기(Morale) 붕괴 시 패주, 3군 전열 진형 상성.
- [ ] **10. 가문 혈통 & 세대 계승 영구 레거시 엔진 (`LineageLegacyEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/lineage_engine.py`
  - **기능**: 영구 사망 시 유언장 집행, 직계 자손에게 가보/특성/영지/원수 가문 적대 관계 100% 인계.
- [ ] **11. 현상금 수배자 & 추적자 용병 AI 엔진 (`BountyHunterEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/bounty_engine.py`
  - **기능**: 범죄/밀수 누적 시 현상금 수배령, 마을 휴식/이동 중 실시간 현상금 사냥꾼 파티 기습.
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
- [ ] **16. 식량 부패·수질 오염 & 보존식 염장 가공 엔진 (`RationSpoilageEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/ration_engine.py`
  - **기능**: 시간 경과/습도에 따른 식량 부패, 소금 염장/건조 가공, 상한 음식 식중독 구토 디버프.
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

### [인프라, UI 및 플랫폼 시스템 (공통/플랫폼)]
- [ ] **1. 인터랙티브 웹 UI 대시보드 (`InteractiveWebUI`)**:
  - **구현 대상**: [UI: 신규] FastHTML/React 프론트엔드 대시보드
  - **기능**: 실시간 HP/MP/피로도/스트레스 게이지, 지리 도로망 2D 미니맵, 인벤토리 툴팁, SD 초상화 & TTS 오디오 플레이어.
- [ ] **2. 동적 BGM 믹서 & 크로스페이드 사운드 엔진 (`DynamicAudioPlayer`)**:
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
- [ ] **SD 1.5 LoRA & NPC 7대 표정 팩 백그라운드 파이프라인**:
  - 인물 A 생성 시 기본 그림 1~2초 즉시 출력 후, 백그라운드(ADetailer 얼굴 인페인팅)로 7대 표정(기본, 놀람, 분노, 웃음, 패닉, 공포, 각성) 무지연 순차 생성(총 15초 내외).
- [ ] **TTS 한국어 음성 엔진 탑재 (Edge-TTS / Kokoro)**:
  - NPC 성별/나이/톤별 보이스 매핑 및 자연스러운 한국어 음성 출력.
- [ ] **Sound AI 효과음 & 환경 앰비언스 BGM 파이프라인**:
  - 전투 타격음, 마법 영창음, 비/바람 날씨 소리, 던전/주점 앰비언스 사운드 생성 및 재생.

---

## 📅 [2026-09-06] 현재 세션 개발 현황

### 1. 이번 세션 구현 완료 핵심 시스템
1. **리포지토리 위생 및 구조적 결함 정비 (Claude 지적 3대 결함 완벽 해결)**:
   - `scratch/` 내 임시 스크립트 전면 제거 및 `.gitignore` 등록 격리.
   - `data/legacy/` 내 164개 더미 JSON 깃 추적 해제 및 디스크 파일 정리, `tests/test_legacy.py` `monkeypatch` + `tmp_path` 격리 (영구 파일 누적 방지).
   - `src/agents/profiler.py` ➔ `src/agents/combat_profiler.py` 리네이밍 (명칭 중복 해소).
   - `AGENTS.md` 및 `SESSION_HANDOFF.md`에 [고정 규칙 9] 리포지토리 청결 및 모듈 네이밍 중복 방지 규칙 탑재.
2. **Claude 백로그 4건 사전 분석 및 중복 방지 검토 (규칙 5 준수)**:
   - 1) `bounty_engine.py`: 이미 완전 구현 및 단위 테스트 완료 상태 확인.
   - 2) `legacy.py`: 캐릭터 아카이빙/스폰 기구현 완료. 가문 혈통(`lineage`)은 신설 대신 `legacy.py` 확장 대상.
   - 3) `weather_engine.py`: 심부 체온(`body_temperature`), 저체온증(34도 이하 데미지), 열사병(39도 이상) 기구현 완료. `thermal_engine` 신설 불필요, `weather_engine` 확장 대상.
   - 4) `puzzle_engine.py`: 유적/던전 기믹 해체 기구현 완료. `trap_engine` 신설 대신 `puzzle_engine`에 함정 기믹 통합 대상.
3. **스태미너(기력) 시스템 및 물리 전투 자원 엔진 전격 완공 (`StaminaEngine`)**:
   - **`src/world/stamina_engine.py`**:
     - CON/AGI 비례 상한(`calculate_max_stamina`) 및 턴당 자연 회복량(`calculate_regen_rate`) 계산.
     - 사전 검증(`can_afford`): 기력 부족 시 거부 + 탈진 상태 시 고비용(>20) 신체 행동 봉인.
     - 기력 소모(`consume`): 기력 차감 및 0 도달 시 `status_engine.py`의 기존 `exhaustion`(탈진) 상태이상 자동 격발.
     - 턴 자연 회복(`recover_turn`): 상한까지 자연 회복, 탈진 상태 시 50% 페널티 적용.
     - 수치 제약: 밸런싱 세션 분리를 위해 확정 수치 대신 `TODO` 주석 및 플레이스홀더 유지.
   - **`src/world/state.py`**:
     - `Player` 및 `NPC`에 `stamina: int = 100`, `max_stamina: int = 100` 필드 탑재.
     - `max_stamina_effective`, `stamina_regen_effective`, `stamina_status_ko` 프로퍼티 탑재.
     - `WorldState.from_dict`에서 구버전 세이브(기력 필드 없는 구형 JSON) 로드 시 기본값 100 자동 주입 (100% 하위 호환 보장).
   - **`src/world/validator.py`**:
     - `ActionValidator`에서 `resource_type == "stamina"` 스킬 시전 시 `StaminaEngine.can_afford` 사전 검증 연동.
   - **`src/world/two_pass_engine.py`**:
     - 패스 1 스킬 실행 시 실시간 기력 차감 및 `triggered_exhaustion` 시 탈진 상태이상 및 안내 로그 출력.
     - 턴 경과 시 플레이어 및 인근 NPC 턴당 자연 회복 연동.
   - **`src/world/npc_skill_engine.py`**:
     - `get_available_npc_skills`: 기력 부족한 스킬 필터링 제외.
     - NPC AI: 저기력(stamina < 25) 시 스킬 아끼고 기본 공격으로 기력 보존하는 판단 로직 탑재.
     - 전투 실행 시 NPC 기력 정상 차감.
4. **던전 탐험 시스템 (`DungeonEngine`) & 3대 권역(지상/던전/히든) 컨셉 함정 엔진 (`TrapEngine`) 전격 완공**:
   - **`src/world/trap_engine.py`**:
     - 3대 맵 카테고리(`surface`, `dungeon`, `hidden_realm`) 및 지형 컨셉형 함정 12종 완비.
     - 지상: 사냥꾼 강철 덫(숲/출혈), 낙하 통나무(산림/둔기), 방울 경보 와이어(가도/고소음 65dB), 빙판 크레바스(설산/저체온), 늪지 유사(수렁/독).
     - 던전: 천장 압축 슬래브(파쇄 35/기절/체간붕괴), 독가스 분출구(신경독/산소급감), 벽면 연발 석궁(관통 24), 마력 지뢰 룬(화염 28/마나 20 차감).
     - 히든 맵: 공간 왜곡 강제 전이(입구 강제 송환), 심연 착란 안개(공황/혼란/탈진), 생명 갈취 인장(최대 체력 25 흡수).
     - 지각(Perception) 패시브/액티브 수색 탐지, 민첩/지능 및 도적 도구(`thieves_tools`) 소모 해체, 실패 시 즉시 격발, 회피 세이빙 스로우(반감).
     - 규칙 6 준수: `TrapSpec` 및 `TrapInstance`에 `traits` 기본 탑재.
   - **`src/world/dungeon_engine.py`**:
     - 지하 다층 던전 인스턴스(B1F~B5F) 심도 스케일링(위험도 25~90, 몬스터 밀집도 40~95%, NPC 밀집도 0 수렴, 산소 농도 저하, 칠흑 어둠).
     - 방 유형별(입구 홀, 복도, 납골당 석실, 무기고, 보스 성소) 선형/분기 연결 및 던전 함정 자동 배치.
     - 층간 이동 (`descend_floor`, `ascend_floor`) 및 지상 탈출/귀환 연동.
   - **`src/world/state.py`**:
     - `Location`에 `location_category`, `dungeon_id`, `floor_depth`, `monster_density`, `npc_density`, `danger_level`, `traps` 필드 추가 및 `from_dict` 역직렬화 100% 하위 호환 보장.
   - **`src/world/validator.py` & `src/world/two_pass_engine.py`**:
     - 함정 탐색, 함정 해체, 던전 층간 이동 인텐트 검증 및 패스 1 결정론적 실행 연동.

5. **파티원 멘탈 붕괴 & 스트레스 엔진 (`PartySanityEngine`) 전격 완공**:
   - **`src/world/party_sanity_engine.py`**:
     - 15종 멘탈 붕괴/각성 스펙(`MentalBreakdownSpec`): 공황(Panic), 편집증(Paranoia), 이기주의(Selfishness), 절망(Hopelessness), 각성(Awakening), 해리(Dissociation), 광폭화(Rage), 얼어붙음(Freeze), 강박(Obsession), 퇴행(Regression), 도주 본능(Flight Instinct), 생존자 죄책감(Survivor's Guilt), 파괴 충동(Destructive Impulse), 감정 폐쇄(Emotional Shutdown), 허세(False Confidence).
     - 5대 스트레스 트리거: 칠흑 어둠 장기 체류(+2/턴), 동료/플레이어 빈사 목격(+15), 혐오체/미지의 존재 조우(+10), 함정 및 치명타 피격(+8/+12), 식량/식수 고갈.
     - 8대 성향별 가중치 테이블(`PERSONALITY_BREAKDOWN_WEIGHTS`): brave, cowardly, loyal, selfish, suspicious, idealistic, survivalist, stoic.
     - 턴 틱 스트레스 검사(`process_turn_sanity`), 붕괴 시 전투 행동 거부/아군 공격/자해/방어 태세/패닉 도주 연동(`filter_companion_combat_intent`).
     - 규칙 6 준수: `MentalBreakdownSpec`에 `traits` 기본 탑재.
   - **`src/world/party_engine.py`**:
     - `Companion`에 `stress`, `max_stress`, `mental_status`, `breakdown_turns_remaining`, `personality_type`, `traits` 탑재.
     - `from_dict` 역직렬화 시 `stress=0`, `mental_status='normal'` 기본값 주입으로 100% 하위 호환 보장.
     - `process_companion_combat_turns`에 `PartySanityEngine.filter_companion_combat_intent` 연동하여 붕괴 상태에 따른 행동 거부/도주 적용.
   - **`src/world/two_pass_engine.py`**:
     - 턴 틱(`process_turn`) 시 파티원 멘탈 스트레스 자연 증가/체류 판정(`PartySanityEngine.process_turn_sanity`) 연동.

### 2. 테스트 및 평가 검증 상태
- **프로젝트 전체 391개 단위 테스트 100% 무결점 통과 (회귀 결함 0건)**:
  - `tests/test_party_sanity.py`: 8개 신규 단위 테스트 통과 (스트레스 누적 및 붕괴 격발, 각성 발동, 성향별 가중치, 턴 경과 어둠 스트레스, 전투 행동 필터링, 동료 빈사 이벤트 스트레스, 동료 직렬화/역직렬화 하위 호환).
  - `pytest tests/`: **391 passed in 4.58s**.
- **DoD Gate Eval Runner 검증**:
  - `python eval_runner.py --no-judge` (20턴): **`Invalid transition rate: 0.0%`** 달성.

### 3. 다음 세션 작업 착수 안내 (Next Step)
- **현재 완료 상태**:
  - 스태미너 시스템 + 던전 탐험 계층 시스템 + 3대 맵 컨셉 함정 엔진 + 파티원 멘탈 붕괴 & 스트레스 엔진 100% 완공.
- **다음 작업 후보**:
  - 후보 1: 던전 구조적 붕괴 & 산소 고갈 질식 엔진 (`CaveCollapseEngine` / 백로그 6번)
  - 후보 2: 날씨·체온 저체온증/열사병 생존 물리 엔진 (`ThermalSurvivalEngine` / 백로그 5번)
  - 후보 3: 전염병·역병·기생충 감염 생체 엔진 (`EpidemicEngine` / 백로그 7번)
  - 후보 4: 세계관별 4대 성장 스케일 프리셋 (`WorldPowerScalePresets`)

