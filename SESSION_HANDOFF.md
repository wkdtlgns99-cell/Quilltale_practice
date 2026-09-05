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
- [ ] **🔥 [절대 최우선 착수 0순위] 6계층 거시-미시 현실 인프라 뼈대 시스템 (Level 0 ~ Level 5)**:
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
    - [x] **2단계: 상위 레이어(0~2층) 템플릿 연동**: 총 120종 대륙 템플릿 완비(`continent_templates.json`: 동양/선협/무협/괴담/신선 및 다크 판타지 등 전 120종 대륙 최강자/최강 몬스터 스케치 및 ID 포인터 전면 탑재) + `cosmology_templates.json`(57종) 및 `region_templates.json`(41종)을 `InfrastructureTemplateLoader`로 정밀 매핑/결합 완료.
    - [ ] **🔥 [다음 세션 즉시 착수 차례] 3단계: 중간 레이어(3~4층) 국가/마을 영토 매핑**: 4대 왕국 및 국경선, 관세율, 마을 단위(`Settlement`: 좌표, 인구, 치안도) 도로망 결합.
    - [ ] **4단계: 하위 레이어(5층) 마을 내 인프라 배치**: 마을별 상점, 대장간, 학교, 신전, 주점 등 세부 시설 슬롯화 및 기능 연동.
    - [ ] **5단계: [최종] 전 계층 수직 통합 검수 (End-to-End)**: 시설에서 마을 ➔ 국가(관세) ➔ 권역(자연 물가) ➔ 대륙(언어) ➔ 세계관(마나)까지 상하향식 연동 100% 통합 단위 테스트.
  - **작업 원칙**: 다른 백로그 전면 중단하고, 1단계부터 5단계까지 순차적으로 100% 완료한 후 다음 백로그 진행.
- [ ] **🔥 [인프라 5단계 완료 직후 착수 0.5순위] 월드 엔티티(배우 & 소품) 및 시간/역법 인프라 연동 시스템 (NPC, Item, Skill, Monster, Quest, Time)**:
  - **구현 대상**: [연동 파이프라인] `src/world/generator.py`, `src/world/state.py`, `src/world/time_engine.py` (또는 기존 state 확장), `data/templates/`
  - **기능 및 연동 순서**:
    1. **NPC & 종족 인프라 배치**: 4계층 마을 인구/종족비 및 5계층 시설(상점, 대장간, 주점)에 상주 NPC 자동 스폰 및 직책(영주/국왕/거상) ID 바인딩.
    2. **Item & 장비 상점/루팅 연동**: 2계층 권역 특산물 및 5계층 시설 유형(`facility_type`)에 맞는 상점 재고 진열(`items`), 10개 장비 슬롯 템플릿 연동.
    3. **Skill & 마법 훈련 연동**: 5계층 훈련장/마탑(`training_ground`, `mage_tower_academy`) 제공 스킬/고대어 연동 및 마나 밀도 기반 시전 환경 결합.
    4. **Monster & 포식자 생태계 연동**: 2계층 권역 최상위 포식자(`apex_predator_id`) 및 4계층 외곽 마수 침식도(`monster_infestation_index`) 스폰 테이블 연동.
    5. **Quest & 사건 나비효과 연동**: 4계층 마을 공고판(`town_square_features`) 현상수배/의뢰 및 역사적 원한(`historical_grievances`) 퀘스트화.
    6. **Turn & 시간/천문 역법 계절 시뮬레이션 연동 (`TimeCalendarEngine` & WorldState 역법 체계)**:
       - **기존 코드 확장**: `WorldState` 기존 `days_per_month(30)`, `months_per_year(12)`, `time_elapsed_minutes` 기반에 `start_year`, `current_year`, `current_month`, `current_day_of_month`, `current_season`(봄/여름/가을/겨울) 프로퍼티 및 캘린더 역법 체계 결합.
       - **행동별 표준 소요 시간 & 실시간 나비효과 연동**:
         - 탐색(10분), 대화(1~5분), 전투(턴당 6초/교전 후 정리 5분), 제작(30~120분), 이동(거리/이동속도 연산 분), 단기 휴식(60분), 장기 수면(480분) 가변 시간 전진 체계.
         - 시간 전진 ➔ 퀘스트 시한 마감(`quest_engine`), 소문 확산(`rumor_diffusion_engine`), 시설/상점 주야간 영업시간, 일출/일몰 조도(은신 판정), 계절별 기온 편차(저체온증/열사병)와 유기적 100% 결합.
- [ ] **1. 물리적 은신/잠입/도청 엔진 (`StealthInfiltrationEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/stealth_engine.py`
  - **기능**: 조도(암흑/달빛/횃불), 바닥 재질(진흙/마른 짚/삐걱이는 목재), 소음(dB), 바람 방향(체취 감지) 기반 결정론적 은신/도청 연산.
- [ ] **2. 몬스터 부위 파괴 & 특수 소재 채집 엔진 (`AnatomyHarvestEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/harvest_engine.py`
  - **기능**: 와이번 날개막 찢기, 베히모스 뿔 절단, 해체 단검 내구도 소모 및 스킬 기반 고유 연금술/제작 소재 획득.
- [ ] **3. 함정 해체 & 공학 퍼즐 물리 엔진 (`TrapEngineeringEngine`)**:
  - **구현 대상**: [엔진: 신규] `src/world/trap_engine.py`
  - **기능**: 낙하 분쇄석, 독가스 분출구, 와이어 격발기, 도적 도구 세트 소모 및 덱스/지능 기반 단계별 기믹 해체.
- [ ] **4. 파티원 멘탈 붕괴 & 트라우마 엔진 (`PartySanityEngine`)**:
  - **구현 대상**: [엔진: 확장] `src/world/party_engine.py`
  - **기능**: 동료 사망, 칠흑 어둠 장기 체류, 식인/언데드 조우 시 스트레스 폭증, 공황 발작/망상/배신/탈주.
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

## 📅 [2026-09-05] 현재 세션 개발 현황

### 1. 이번 세션 구현 완료 핵심 시스템
1. **총 120종 대륙 템플릿 신규 구축 및 대륙 최강자/최강 몬스터 스케치 전면 완비 (`data/templates/continent_templates.json`)**:
   - 1차 20종 + 2차 30종 + 3차 40종 + 4차 30종 = 총 120종의 고밀도 대륙 템플릿 JSON 완성.
   - 대륙 최강자 스케치(`continental_apex_champion_sketch`) 및 최강 몬스터 스케치(`continental_apex_monster_sketch`) 전 120개 대륙 100% 완비.
2. **총 215종 4계층 정주지/마을 템플릿 전격 구축 및 무결성 검증 (`data/templates/settlement_templates.json`)**:
   - 215종 전 템플릿 완비 및 `traits >= 1`, 좌표, 치안도, 성벽, 특산품, 중앙 광장, 금기, 원한, 스캔들 100% 무결점 탑재.
3. **총 134종 Level 3 국가/영지 템플릿 완비 및 데이터 클래스 확장 (`data/templates/nation_templates.json`)**:
   - `Nation` 클래스에 `dominant_species: List[str] = field(default_factory=list)`(국가 주요 구성 종족 목록) 신설하여 대륙(`mortal_species`) - 국가(`dominant_species`) - 마을(`racial_demographics`)로 이어지는 3단 종족 계층 체계 완성.
   - 1차 29종 + 2차 26종 + 3차 7종 + 4차 15종 + 5차 16종 + 6차 10종 + 7차 31종 = 총 134종 국가 템플릿 100% 무결점 완비.
4. **총 136종 Level 2 권역(Region) 템플릿 대폭 보강 및 적응 로더 완비 (`data/templates/region_templates.json`)**:
   - 기존 41종 + 1차 20종 + 2차 21종 + 3차 15종 + 4차 15종 + 5차 12종 + 6차 12종 = 총 136종 고밀도 권역 전격 병합 (속삭이는 서리 계곡, 흑요석 화산 분지, 탁류의 진흙 습원, 고대 고사리 원시림, 날카로운 화강암 첨봉, 에테르 수정 고원, 환초 산호 제도, 고철 파편 황무지, 속삭이는 지하 납골당, 해바라기 산들바람 들판, 울부짖는 폭풍 고원, 신기루 수정 모래언덕 제2구역 등 6차 12종 추가 탑재).
   - `InfrastructureTemplateLoader.adapt_region_template_to_region` 고도화: 중첩 생태계(`ecology`), 유적(`landmarks_and_ruins`), 자원(`resources`), 식문화/복식/신앙(`lifestyle_and_culture`)을 `Region` 데이터클래스에 100% 바인딩.
5. **`InfrastructureTemplateLoader` 전 계층 로더 라인업 완성**:
   - `load_settlement_templates()`, `load_nation_templates()`, `load_region_templates()`, `load_continent_templates()` 전 계층 로더 완비.

### 2. 테스트 및 평가 검증 상태
- **인프라 계층 단위 테스트 50개 및 프로젝트 전체 299개 테스트 100% 무결점 통과**:
  - `tests/test_infrastructure_hierarchy.py`: 총 50개 테스트 전체 통과.
    - `test_region_templates_json_integrity`: 136개 권역 템플릿 고유 ID, `traits >= 1`, 지형, 바닥 표면, 희귀 광맥, 몬스터 및 복식/식문화/신앙 프로필 전수 무결성 검증.
    - `test_infrastructure_template_loader_regions`: 136개 권역 데이터 클래스 로딩 및 terrain/price multiplier 매핑 검증.
    - `test_nation_templates_json_integrity` (134개) & `test_infrastructure_template_loader_nations` (134개) 검증.
  - 전체 회귀 결함 0건, 299 passed in 3.64s.
- **DoD Gate 평가 검증 (`eval_runner.py --no-judge`)**:
  - `Invalid transition rate: 0.0%` (무결점 통과).

### 3. 다음 세션 작업 착수 안내 (Next Step)
- **현재 완료 상태**:
  - Level 0 우주론/세계관 57종 (`cosmology_templates.json`)
  - Level 1 대륙 120종 + 최강자/최강 몬스터 (`continent_templates.json`)
  - Level 2 권역 136종 (`region_templates.json`) [목표 300개 중 136개 달성 (45.3%)]
  - Level 3 국가 134종 (`nation_templates.json`)
  - Level 4 정주지/마을 215종 (`settlement_templates.json`)
- **다음 세션 즉시 착수 작업**:
  - 권역 템플릿 추가 투입 시 이어서 병합 (총 300개 목표치 향해 진행),
  - 또는 [4단계 하위 레이어] Level 5 마을 내 세부 시설(`Facility`) 슬롯화 및 기능 연동 진행.


