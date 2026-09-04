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
      - [x] **1-5. 세부 인프라/시설(Level 5)**: 시설 분류, 건물 생애주기(`BuildingStatus`: 정상/공사중/수리중/반파/폐허/방치), 완공도, 수리 자재, 창문 방범, 굴뚝 크기, 지붕 재질, 엄폐율, 비밀문, 지하실 유형, 파수 동물(`Facility`).
      - [x] **[추가 정제] 로어 하드코딩 제거 & 상향식 집계**: `Faction`, `WorldState`, `NPCVisualDetails`, `Settlement`, `EnvironmentalMetrics` 기본값 중립화 + `recalculate_totals()` 상향식 인구/면적 합산 + 3단 특산품 계층 조회.
    - [ ] **🔥 [다음 세션 즉시 착수 차례] 2단계: 상위 레이어(0~2층) 템플릿 연동**: 기존 `cosmology_templates.json`(57종)과 `region_templates.json`(30종)을 대륙/권역 그릇에 정밀 매핑.
    - [ ] **3단계: 중간 레이어(3~4층) 국가/마을 영토 매핑**: 4대 왕국 및 국경선, 관세율, 마을 단위(`Settlement`: 좌표, 인구, 치안도) 도로망 결합.
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

## 📅 [2026-09-04] 현재 세션 개발 현황

### 1. 이번 세션 구현 완료 핵심 시스템
1. **6대 계층 거시-미시 인프라 뼈대 1단계 완성 (infrastructure.py, state.py)**:
   - Continent(대륙), Region(권역), Nation(국가), Settlement(정주지), Facility(세부시설) 5대 고밀도 데이터 클래스 구축.
   - InfrastructureRegistry: O(1) 상하향식 계층 탐색, 권역 자연 자원 매트릭스(0.3x~5.0x) + 국가 관세율(0~50%) + 외교 관계 연동 유효 거래 가격 연산, 국경 관문 검문소(통행증, 밀수품 적발, 전시 차단) 검증 로직 구현.
2. **건물 생애주기(Lifecycle) 및 물리 파손/공사 상태 체계 탑재**:
   - BuildingStatus(str, Enum): OPERATIONAL(정상), UNDER_CONSTRUCTION(신축/증축), UNDER_REPAIR(수리보수), DAMAGED(반파/파손), RUINED(완파/폐허), ABANDONED(방치/소굴화).
   - FacilityType(str, Enum): 14대 표준 물리 시설 유형 완비.
   - Facility: building_status, construction_progress(완공 진척도 0~100%), repair_cost_materials(수리 자재/골드 장부), destruction_cause(파손 원인), scaffolding_accessible(비계 설치 여부).
   - Settlement: 물리적 시설 슬롯 분류 및 상태별 목록 관리 (commercial_shops, training_facilities, active_peddlers, guild_halls, under_construction_facilities, ruined_facilities).
3. **전 계층(Level 0 ~ Level 5) 현실 물리 & 거시 재앙 인프라 완비**:
   - **Level 0 (WorldState - 거시 인류 난제, 대재앙 & 물리/기억/성간 상수)**:
     - global_apocalyptic_threat: 전 세계적 멸망/재앙 위협 명칭 ("마왕군 침공", "영구 빙하기", "심연 차원문").
     - world_crisis_active_stage: 위기 진행 단계 (0: 평화 ~ 5: 완전 파멸).
     - global_nemesis_npc_id: 전 세계 공통 주적/마왕/파멸의 사도 NPC ID 포인터 (NPC 클래스 포인팅).
     - global_sanctuary_region_id: 유일하게 침식되지 않은 인류 최후의 성역 권역 ID 포인터 (Region 클래스 포인팅).
     - grand_crusade_coalition: 대재앙 대항 초국가 성전군/연합 세력 목록.
     - universal_gravity_scale: 세계 물리 중력 계수 (1.0 = 표준, 중량 과적 및 낙하 충격량 배율 기준치).
     - memory_decay_turn_interval: 사소한(1~2급) 에피소딕 기억의 자연 망각/흐려짐 턴 주기 (50턴).
     - cosmic_alignment_element: 현재 행성이 통과 중인 우주 성간 속성/천체 정렬 ("neutral", "fire", "void", "holy", "life").
     - world_soul_awakening_ratio: 행성 자체의 영혼/가이아 자아 각성도 (0~100, 마나 폭풍/지각 변동).
   - **Level 1 (Continent)**:
     - dominant_tycoon_npc_id: 대륙 최고 거상/상단 총수 NPC ID 포인터.
     - continental_chokepoints: 대륙 관문 해협/지협/대협곡 등 전략적 병목 통로 목록.
     - tectonic_instability_rating: 지질 판 불안정도 (0~100, 지진/화산 빈도).
     - continental_forbidden_zones: 신벌/낙진 격리 금기 구역 목록.
     - standard_physique_archetype: 대륙 주류 표준 체형 골격 ("humanoid_medium", "dwarven_broad", "beastfolk_large", 노획 장비 리사이징 기준).
     - endemic_continental_resources: 대륙 고유 희귀 근원 자원 (타 대륙엔 아예 없는 자원: 미스릴 원석, 세계수 수액, 용골 화석).
     - ancient_titan_remains: 대륙을 형성하는 잠든 고대 거신/시조룡의 유해 지형 목록 (["거신 이미르의 늑골 산맥", "세계뱀의 등뼈"]).
     - leyline_network_scale: 대륙 전역을 관통하는 거대 마나 지맥 규모 ("sparse", "medium", "dense", "wild_surge").
   - **Level 2 (Region)**:
     - wildfire_hazard_rating: 산불/대화재 확산 취약도 (0~100).
     - foliage_density: 야생 수목/식생 밀도 (0~100, 시야 차폐, 화살 방해, 매복 보너스).
     - river_crossing_dc: 주요 하천/급류 도강 난이도 DC (도보/마차 침수 및 유실 판정).
     - campfire_detection_risk: 야영 모닥불 피울 시 야생 맹수/도적 유인 위험도 (0~100, 야간 기습 확률).
     - watch_shift_visibility_bonus: 권역 지형/시야에 따른 야간 불침번 경계 감시 보정치 (-50: 밀림 ~ +50: 사막).
     - rare_mineral_deposits: 지질/지하 희소 광맥 (오리하르콘 광맥, 천연 유황 동굴, 심층 마나 수정맥 등).
     - endemic_biological_resources: 기후 고유 희귀 생체/약초 자원 (만년설 설련화, 심연 발광 포자, 화염 도마뱀 쓸개 등).
     - draconic_presence_level: 권역 내 용족/고룡 서식 위협도 (0: 없음, 1: 와이번/유룡, 2: 성룡 영역, 3: 고룡 동면/지배).
     - dominant_elemental_affinity: 권역 지배 속성 마나 편향 ("neutral", "fire", "ice", "lightning", "darkness", "holy", "wind", "earth").
     - monster_stampede_risk: 마수 번식기/마나 폭주 시 일어나는 마수 대침공/스탬피드 위험도 (0~100).
   - **Level 3 (Nation)**:
     - national_merchant_leader_id: 국가 공인 상단 총수/왕실 조달청장 NPC ID 포인터.
     - border_barrier_type: 국경 물리 장벽 체계 ("none", "wooden_palisade_line", "great_stone_wall", "chasm_fortress").
     - beacon_network_speed_hours: 국영 봉화대/파발망 신호 전파 시간.
     - coin_minting_purity: 조폐국 주화 금/은 순도 (0~100%, 동전 깎기 및 위조 판정).
     - ammunition_strategic_control: 국가 전시 철제 화살촉/탄약 민간 유통 통제 여부.
     - refitting_guild_tax_rate: 노획 장비 체형 개조/수선 시 국영 대장장이 길드 공임 관세율 (0.0~0.3).
     - monopoly_strategic_resources: 국가 독점 전매 및 수출 금지 전략 자원 (왕실 비전 초석, 고농축 마력석 등).
     - national_mining_concessions: 영토 내 주요 광산 채굴권/조계지 장부 (mine_name -> 소유 길드/가문 ID).
     - court_mage_circle_strength: 궁정 마법사단/국영 마도 결사단 규모 및 방어 전력 (0~100).
     - national_patron_deity_boon: 국가 수호신전의 국가 단위 신성 가호 축복 (예: "솔라리스의 태양 방벽", "불멸의 강철 축복").
     - airship_dock_count: 국영 공중 마도 비공정 계류장 및 정규 비공정 수.
     - **국가 군사 5대 표준 병과 & 특수부대 체계 (Option C 하이브리드)**:
       - `knights_count`: 정예 기사단 / 중장기병 / 성기사 병력 수 (기본 100).
       - `infantry_count`: 정규 보병 (장창병, 방패병, 검사) 병력 수 (기본 600).
       - `ranged_corps_count`: 원거리 부대 (궁병, 석궁병, 총사대) 병력 수 (기본 200).
       - `cavalry_count`: 경기병 / 수색 기동대 병력 수 (기본 100).
       - `siege_engine_count`: 공성 투석기 / 공성포 / 발리스타 수 (기본 10).
       - `beast_riders_count`: 마수 / 환수 기병 (그리폰, 와이번, 늑대 기병) 수 (기본 0).
       - `special_military_units`: 국가 고유 특수부대/정예 연대 딕셔너리 (예: `{"왕실 머스킷 총사대": 100, "그리폰 공습대": 30}`).
       - `calculate_total_military_power()`: 지상군 총 전력 자동 산출 메서드.
   - **Level 4 (Settlement)**:
     - town_square_features(단두대/공고판/시계탑/분수대), gate_type(성문 방호), moat_type(해자), stable_and_cart_capacity(마구간/마차 주차장), watermills_count/windmills_count(물레방아/풍차), firefighting_cistern_rating(방화수조), quarantine_camp_active(검역소 텐트촌), sewer_network_scale(지하 하수망), pasture_area_hectares(가축 방목지).
     - street_lighting_type: 가로등/야간 조명망 ("none", "pitch_torches", "whale_oil_lamps", "magic_crystals").
     - battlement_type: 성벽 총안 및 사격 흉벽 ("none", "wooden_hurdles", "stone_crenels", "machicolations").
     - militia_armory_capacity: 마을 공용 무기고 비축 정원 (징집 민병대 무기 비축량).
     - fletching_and_ammo_supply_tier: 화살/볼트 탄약 공방 보급 등급 (0: 품귀, 1: 일반, 2: 관통살, 3: 마도화살).
     - armor_refitting_forge_tier: 이종족 노획 장비 체형 수선 대장간 등급 (0: 불가, 1: 가죽/경갑, 2: 판금중갑, 3: 마도구).
     - pack_animal_rental_available: 중량 과적 해소를 위한 노새/짐마차 대여 가능 여부.
     - disguise_inspection_strictness: 성문/거리 경비병의 복면/가면 착용자 불심검문 엄격도 (0~100).
     - local_resource_nodes: 마을 관할 현지 물리적 채굴/채집 노드 (예: ["제1 철광 갱도", "고대 은광맥", "유황 온천", "벌채장"]).
     - resource_depletion_risk: 자원 고갈 및 폐광 위험도 (0~100, 100 도달 시 폐광 및 유령마을화).
     - magical_barrier_active: 고위 마법 폭격/드래곤 브레스 차단용 도시 광역 마도 결계 돔 가동 여부.
     - aerial_mount_dock_tier: 비행 마수 승강장 등급 (0: 없음, 1: 전령소, 2: 그리폰 마구간, 3: 비공정 계류탑).
     - teleportation_waystone_active: 정주지 중앙 공간 전송 마법석/웨이포인트 결절점 활성 여부.
     - undead_haunting_index: 야간 영체/원혼/언데드 출몰 및 사령 농도 (0~100, 50 이상 시 야간 횃불 푸르게 변함).
   - **Level 5 (Facility)**:
     - window_security_type(창문 철창), chimney_hearth_size(벽난로 침투), roof_material_type(지붕 재질), cover_density(실내 엄폐율), secret_door_mechanism(비밀문), cellar_type(지하실/감옥), guard_beast_type(파수 동물).
     - vent_duct_size: 환기 배관/덕트 크기 ("none", "grate_narrow", "crawlable_human").
     - floor_water_depth_cm: 바닥 침수/오수 깊이 (cm: 0 건조, 5 찰랑거림, 30 무릎/감전).
     - key_holder_npc_id: 자물쇠 열쇠 소지자 NPC ID 포인터 (소매치기/협박 탈취 대상).
     - ceiling_height_meters: 실내 천장 높이 (m, 2.2m 미만 시 장창/대검 휘두름 벽 충돌 튕김 제약).
     - hallway_width_meters: 실내 복도/통로 유효 폭 (m, 1.5m 미만 시 찌르기 무기 한정 및 회피 불가).
     - cover_poise_durability: 실내 엄폐물/문짝의 체간 충격량 버팀도 (0~100, 대형 둔기/폭발 가드 파괴).
     - dungeon_max_depth_floors: 던전/지하 유적 시설의 최대 지하 심도 층수 (0: 일반 지상 건물, 1~50: 지하 미궁 층수).
     - dungeon_core_element: 살아있는 던전 핵의 속성 ("none", "abyss", "fire", "arcane", "nature", "undead").
     - sanctification_rating: 시설 신성 축성/정화도 (0~100: 0 사령/저주 소굴, 50 세속 중립, 100 언데드 즉시 정화 성소).
4. **4단계 희소 지하 자원 & 천연 광물 계층 상하향 조회 엔진 (resolve_natural_resources)**:
   - 마을 물리 채굴장 ➔ 국가 독점 전매 자원 ➔ 권역 희소 광맥/생체 자원 ➔ 대륙 고유 근원 자원 4단 자동 결합 포트폴리오 산출.
5. **하드코딩 로어 완전 제거 및 스키마 중립화**:
   - Faction, WorldState, NPCVisualDetails, Settlement 기본값 중립화 및 의사소통 가능한 휴머노이드 필멸자 지성체 다종족 규격 확립.
6. **전 계층 공통 인구/면적 체계 및 상향식 자동 합산 (Roll-up)**:
   - recalculate_totals() 상향식 집계 탑재 및 3단 특산품 계층 조회.
7. **마을 5대 생존/공동체 인프라 & 회복탄력성 감사 시스템**:
   - 상하수도, 식량창고, 방위치안, 상공업공방, 주민후생 5대 분류 및 audit_settlement_resilience() 진단 엔진 탑재.
8. **문명 6 & 중세 시뮬레이션 심화 요소 확장**:
   - 문명 3단 위계, 6대 산출량(SettlementYields), 국왕/영주/빌리프/촌장 통치 체계, 계층 갈등, 종교 관용도, 암흑가, 전시 명분, 기온 편차, 최상위 포식자/지역 챔피언 포인터 완비.
9. **6대 전 계층(Level 0~5) 및 가도/차량/세력 전면 요약 특성 태그 체계 (`traits: List[str]`) 탑재**:
   - **Level 0~5 수직 계층**: `WorldState`(Level 0, `world_traits` 및 `traits` 프로퍼티), `Continent`(Level 1), `Region`(Level 2), `Nation`(Level 3), `Settlement`(Level 4), `Facility`(Level 5) 전면 탑재.
   - **가도/운송/세력 확장**: `InterTierRoute`(광역 간선가도/원양항로), `RoadConnection`(마을 연결도로), `TransitVehicle`(비공정/마차 등 운송수단), `Faction`(국가/세력), `Location`(실시간 탐색 노드)까지 유효한 전 클래스에 `traits` 필드 100% 개설.
   - 플레이어 UI 한눈 요약, AI(GM) 서술 앵커링, 도로 매복/돌발 퀘스트 발생기 기초 데이터 규격 완성.

### 2. 테스트 검증 상태
- **인프라 계층 단위 테스트 45개 및 핵심 스위트 49개 100% 무결점 통과 (1.27s / 13.31s)**:
  - tests/test_infrastructure_hierarchy.py 39개 테스트 통과.
  - tests/test_world_state.py 6개 테스트 통과.
  - tests/test_two_pass_engine.py 4개 테스트 통과.
  - 신규 군사 병과(Option C), 6계층 + 가도/운송/세력 traits 태그, 직렬화/역직렬화 회귀 결함 0건. 전 모듈 호환성 100% 검증.

### 3. 다음 세션 작업 착수 안내 (Next Step)
- **현재 완료 상태**: **1단계 (Level 0~5 고밀도 데이터 클래스 정의, 물리/생존 인프라, 군사 전력 Option C, 10개 클래스 traits 요약 특성 태그 체계)** 100% 완료.
- **다음 세션 즉시 착수 작업**: **🔥 [인프라 2단계 착수] 상위 레이어(0~2층) 템플릿 연동**:
  - `data/templates/cosmology_templates.json`(57종)과 `data/templates/region_templates.json`(30종)의 방대한 로어/기후/지형 데이터를 대륙(`Continent`), 권역(`Region`), 세계관(`WorldState`) 데이터 클래스 인스턴스로 자동 매핑·주입하는 로더 파이프라인 구축 및 검증.

