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

## 📅 [2026-09-03] 현재 세션 개발 현황

### 1. 이번 세션 구현 완료 핵심 시스템
1. **날씨에 따른 도로 상태 시스템 (`WeatherRoadDynamics` in [geography.py](file:///c:/Quilltale/src/world/geography.py))**:
   - 진흙탕, 침수 수렁, 빙판 결빙, 설산 눈보라, 모래폭풍, 아지랑이 열파 등 6대 도로 상태 추가.
   - 다익스트라 최단 경로 연산 시 환경 상태에 따른 속도 배율 및 피로도, 서사 경고 자동 결합.
2. **히든 보스 / 엘리트 몹 조우 엔진 (`HiddenEncounterEngine` in [hidden_encounter_engine.py](file:///c:/Quilltale/src/world/hidden_encounter_engine.py))**:
   - 심야+낮은 위생도(심연의 도살자), 영하+산길 결빙(서리 망령), 폭우+수렁(벼락 메기), 밀수품 소지(도살장 저울상인) 등 4대 조건부 히든 보스 스폰 및 비기 스킬/약점 기믹 연동.
3. **12대 시작 오리진 매트릭스 다양화 ([generator.py](file:///c:/Quilltale/src/world/generator.py))**:
   - 시작 장소 선술집 몰빵 바이어스 제거. 죄수 호송마차 전복 비탈, 외해 난파선 해식 동굴, 불타는 카라반 잔해, 국경 방역 검문소 등 12종 무대 및 조우 NPC 무작위 생성 매트릭스 확장.
4. **오프닝 서사 800자 보장 2차 패스 길이 검증기 ([game_master.py](file:///c:/Quilltale/src/agents/game_master.py))**:
   - 800자 미만 시 4대 필수 구조(거시 역사/당대 비극/플레이어 몰골 및 소지품/현장 오감)로 자동 확장 재작성하는 길이 검증기 장착.
5. **감각(Perception) 초감각·육감 공식 체계 구축 ([perception_engine.py](file:///c:/Quilltale/src/world/perception_engine.py))**:
   - 단순 오감을 넘어선 8대 초감각(사각 살기 감지, 시선의 무게, 본능적 눈치/거짓말 포착, 약점의 결 직관, 모션 프리뷰, 소리 반향, 숨소리/심박 청취, 마나 공명) 공식 판정 및 서사 단서 연동.
6. **물리 시간 기반 턴·시간 동적 매트릭스 ([two_pass_engine.py](file:///c:/Quilltale/src/world/two_pass_engine.py))**:
   - 턴 수 대신 인게임 경과 시간(분)을 단일 진실원천으로 확립.
   - 장거리 이동(도로 노면 비례 15~40분), 대화/조사(10분), 전투(1~3분) 실시간 누적 및 소문 확산(`RumorDiffusionEngine`)과 일체화.
7. **Anti-Melodrama & 과장 금지 규칙 주입 ([prompts.py](file:///c:/Quilltale/src/agents/prompts.py))**:
   - 1~3골드 소액 팁에 "오크통을 통째로 비우는 거액"이라며 호들갑 떨던 삼류 양판소 과장 영구 차단. 차분하고 메마른 하드보일드 리얼리즘 톤 고정.
8. **자연어 이동 동사 확장 & 서사-맵 노드 동적 동기화 ([two_pass_engine.py](file:///c:/Quilltale/src/world/two_pass_engine.py))**:
   - "간다", "가자", "향한다", "내려간다" 등 자연어 이동 동사 인식 누락 수정.
   - 서사 속 단서("운하 수문")와 맵 노드(`loc_2`) 명칭 및 맥락 실시간 동기화.
9. **결정론적 골드 지불 자동 차감 엔진 ([two_pass_engine.py](file:///c:/Quilltale/src/world/two_pass_engine.py))**:
   - 대사/지문 속 골드 지불 의도 자동 감지하여 `player.gold` 즉시 차감 (`30G -> 27G`).
10. **미학습 고대어 DC 폭증 페널티 & 마나 역류 자해 피해 ([validator.py](file:///c:/Quilltale/src/world/validator.py), [two_pass_engine.py](file:///c:/Quilltale/src/world/two_pass_engine.py))**:
    - `known_magic_words` 미습득 단어 1개당 DC +4 폭증, 실패 시 `단어수 * 4` 확정 자해 역류 피해 및 [감전 마비] 상태이상 연동.
11. **직관적 마나 조형 시스템 (`Intuitive Mana Shaping` in [validator.py](file:///c:/Quilltale/src/world/validator.py))**:
    - 고대어 주문 없이도 자연어 심상 묘사(`[원소] + [형태] + [기동]`) 시 **INT + WIS + PER 삼위일체 정신/감각 스탯 합산 보너스**를 받아 마법을 성공시키는 비정형 심상 마법 시스템 신설.
12. **최신 Gemini 모델 풀 및 503 재시도 로직 ([gemini.py](file:///c:/Quilltale/src/llm/gemini.py))**:
    - deprecated된 `gemini-2.5-flash` 제거 및 `gemini-3.6-flash`, `gemini-3.7-flash`, `gemini-3.1-pro-preview` 등록. 503 발생 시 자동 재시도.
13. **ActionValidator 대화/질문 오판정 차단 버그 수정 ([validator.py](file:///c:/Quilltale/src/world/validator.py))**:
    - 따옴표 속 대사에 "마법" 단어가 포함되었다고 공격 판정으로 넘어가던 버그 수정 (`is_inquiry_intent` 감지).

### 2. 테스트 검증 상태
- **249개 전체 단위 테스트 100% 통과** (`249 passed in 2.21s`).
