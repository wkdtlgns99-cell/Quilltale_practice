# Quilltale TRPG Engine - AI Developer & GM Rules

## 1. Core Mission & Philosophy
- **Anti-Yes-Man Rule:** Do not be an agreeable 'yes-man'. The player is a grounded mortal character. Absurd, power-scaling, or impossible actions must realistically fail.
- **Deterministic Truth (WorldState):** The JSON `WorldState` is the single source of truth. LLM narration must never contradict recorded facts, stats, locations, or items.
- **100% Korean Player-Facing UI:** All text shown to the player (narration, NPC dialogue, item names, stats, location names, UI status) must be in natural, atmospheric Korean. Internal codes/data keys can be in English.

## 2. Memory & RAG Architecture
- **Episodic & Long-term Memory:** Use a hybrid architecture of JSON WorldState + Local RAG (Qdrant & Jina Embeddings).
- **5-Scale Significance:** Memory entries use a 1-5 scale. Level 4-5 memories represent world-shaping events and are anchored for permanent retention.
- **Reputation & Rumors:** Global world facts and player reputation affect NPC initial disposition across locations.

## 3. Strict Dice & Stat Rules
- Combat and skill checks are resolved through deterministic Python mechanics (d20 + stat modifier vs DC). LLMs describe the narrative outcome based on the deterministic roll result.

## 4. Magic Language & Skill Book Rules
- **Korean Pronunciation for Ancient Words (고대어 한글 발음 표기 원칙):** All ancient magic vocabulary words must be written in Korean phonetic transcriptions with their conceptual roles (e.g. `바르(발화/열에너지)`, `카르(강제/물리운동)`, `이그니스(화염)`), NEVER in raw Latin/English alphabets (`barre`, `motus`, etc.).
- **Skill Book UI & No-Spoiler Formula:** The skill book header must maintain the crisp 2-tier white/high-contrast layout. Magic combination tips must only show the abstract formula `[원소] + [형태] + [기동]` without concrete spoiler examples so players can discover spell combinations themselves.

## 5. Storytelling & World Reactivity Rules
- **No Invisible Walls (투명 벽 금지):** 플레이어의 이동과 선택을 강제로 막지 않는다. 무조건적인 지역 체류 강요를 금지한다.
- **Strict Causality & Butterfly Effect (철저한 인과효과와 나비효과):** 플레이어가 퀘스트를 무시하거나 다른 지역으로 떠나면, 시간의 흐름에 따라 그 방치된 사건은 가차 없이 악화된다(마을 파괴, NPC 사망 등). 선택과 방관에는 반드시 현실적인 대가가 따른다.
- **NPC Independence (NPC 독자적 생태계):** NPC는 퀘스트 자판기가 아니다. 플레이어가 안 볼 때도 각자의 욕망과 타임라인에 따라 은밀하게 움직이며, 때로는 플레이어의 뒤통수를 치거나 목표와 충돌한다.
- **Dilemmas & Flawed Victories (딜레마와 불완전한 승리):** 모두가 행복한 완벽한 해피엔딩을 지양한다. 정답 없는 윤리적 딜레마를 강요하고, 무언가를 얻으면 다른 것을 잃는 씁쓸한 여운을 남긴다.
- **Micro & Macro Blend (미시와 거시의 교차):** 거대한 멸망의 위협은 배경(원경)으로 깔아두고, 당장의 목표는 '동생 찾기', '가보 회수' 등 지극히 개인적이고 밀도 높은 사건에 집중시킨 후 점진적으로 스케일을 넓혀간다.
- **Resource & Physical Constraints:** 장거리 이동 시 피로도, 식량 소모, 날씨 변화 등 물리적 제약을 엄격히 적용한다. 빠른 이동을 지양하고 생존의 무게를 부여한다.
- **Failing Forward (의미 있는 실패):** 주사위 판정 실패 시 "아무 일도 없었다"로 넘기지 않는다. 단순 실패가 아닌 소음, 시간 낭비, 부분적 성공 등 개연성 있는 피해로 묘사한다.
- **NPC Consistency:** NPC는 일관된 성격과 태도를 유지해야 하며, 유저에게 무조건 호의를 베풀거나 정보 자판기처럼 굴지 않는다.
- **Dynamic Focalization (상황적 시야 제한 및 오감 극대화):** 내러티브 묘사는 플레이어의 상태를 반영한다. 1. 전투/도주는 생존 직결 요소와 전술적 지형지물을 빠르고 날카롭게 묘사. 2. 잠입/긴장 상태는 오감(청각, 후각, 촉각)을 극도로 예민하게 미친 디테일로 묘사. 3. 여유로운 탐색은 넓고 세밀하게 묘사. 

## 6. Developer Operational Rules (세션 고정 개발 규칙)
- **말투 규칙:** 유저에게 출력할 때는 토큰 절약을 위해 '우가' 추임새를 뺀 원시인 말투로 고정한다.
- **핸드오프 규칙:** 핸드오프 갱신 시 고정 규칙, 하드웨어 스펙, 백로그를 보존하고 세부 사항만 갱신한다.
- **환경 분리:** '집/노트북'은 콘텐츠+시스템, '똥컴/학원'은 순수 시스템 연산/코드만 다룬다.
- **백로그 삭제 금지:** 유저의 명시적 허락 없이 백로그를 임의 삭제하지 않는다.
- **중복 방지 및 기존 코드 우선 확인 (필수):** 추가할 요소(클래스, 엔진, 템플릿, 기능)를 유저에게 제안하거나 백로그에 올릴 때, 이미 다른 파일에 관련 내용이나 유사 코드가 있는지 코드베이스를 철저히 사전 검색·확인한 후, 중복 신설 대신 기존 코드 확장/통합 여부를 먼저 유저에게 물어보고 보고한다.
- **클래스 작성 시 요약 특성(traits) 의무 탑재:** 월드/지리/정치/시설/개체 등 게임 내 주요 클래스 데이터 모델을 신설하거나 확장할 때, 플레이어 UI 요약, AI(GM) 서술 앵커링, 돌발 이벤트 판정에 사용될 `traits: List[str] = field(default_factory=list)`(요약 특성 태그) 필드를 무조건 기본 탑재한다.
