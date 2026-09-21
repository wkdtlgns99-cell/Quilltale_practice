# [MASTER ARCHITECTURE] 절차적 생성 HD-2D 턴제 RPG 기획 및 아키텍처 명세서
> **문서 목적:** 본 문서는 프로젝트의 핵심 비전, 기술 스택, 렌더링 파이프라인, 백엔드 연산 구조, 성능 최적화 테크닉을 집대성한 마스터 가이드입니다. 향후 GPT, Claude Code, Cursor 등 어떤 AI 에이전트에게 본 문서를 단독 입력하더라도 프로젝트의 정체성과 기술 표준을 100% 이해하고 일관되게 코드를 작성할 수 있도록 설계되었습니다.

---

## 1. 게임 기본 개요 & 핵심 비전 (Executive Summary)

* **게임 장르:** 절차적 무한 생성 HD-2D / 2.5D 도트 턴제 RPG (Procedural HD-2D Turn-based RPG)
* **아트 레퍼런스 스타일:**
  * **옥토패스 트래블러 (Octopath Traveler):** 화려한 3D 조명/심도 효과와 클래식 도트의 융합
  * **쓰레드 오브 타임 (Threads of Time):** 360도 자유 카메라 회전이 가능한 입체 도트 그래픽
  * **데드 셀 (Dead Cells):** 3D 로우폴리 모델링 + 픽셀화 셰이더 기반의 유려한 도트 모션
  * **발더스 게이트 1·2 & 디스코 엘리시움:** 인게임 모듈러 뷰 + 대화창 초고화질 일러스트 초상화
* **핵심 철학:**
  1. **절차적 무한 생성 (Infinite Procedural World):** 스토리, 맵 지형, NPC 심리, 사물 물리, 역사적 사건 나비효과가 매 플레이마다 완전히 새롭게 생성됨.
  2. **과부하 0, 토큰 0의 현실적 아키텍처:** 플레이 중 실시간 3D/이미지 생성(과부하/GPU 폭발)을 배제하고, **[사전 3D 에셋 풀 + 규칙 엔진 자동 조립 + 3D-to-픽셀 실시간 셰이더]** 파이프라인을 채택.
  3. **Zero-Server-Cost & Zero-Developer-Risk (영구 무료 인디 BYOK 모델):** 개발사의 API 키를 전혀 쓰지 않고, **게임을 플레이하는 유저 본인의 개인 Google Gemini API 키(무료/유료)**를 클라이언트에 직접 등록하여 구동. 개발사 서버비 및 API 과금 0원, 사용자 일일 무료 할당량(하루 1,500턴)으로 평생 무료 플레이 가능.

---

## 2. 이원화 시스템 아키텍처 (Brain & Body 분리)

시스템은 **[파이썬 로직 엔진 (Brain)]**과 **[프론트엔드 클라이언트 (Body)]**로 완벽히 물리 분리된다.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BRAIN: Quilltale Python Logic Engine                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Single Source of Truth & Validation                                      │
│    - src/world/state.py (WorldState, Player, NPC, Location, Faction 등)      │
│    - src/world/validator.py (ActionValidator, 물리/장비/규칙 불변식 검증)   │
│    - src/world/persistence.py, legacy.py, chronicle.py (세계 저장/계승/연대기)│
│                                                                             │
│ 2. Two-Pass GM Engine (결정론 연산과 서사의 완전 분리)                      │
│    - src/world/two_pass_engine.py (TwoPassEngine, DeterministicFactSheet)   │
│    - src/world/action_resolvers.py (이동, 은신, 생존/채집, 전술전투 리졸버) │
│    - src/agents/game_master.py (GameMasterAgent - Pass 2 문학적 서사 렌더링)│
│                                                                             │
│ 3. 50+ Deterministic Domain Engines (4대 핵심 영역 매트릭스)                │
│    ① 물리 & 환경 생태 (13개 엔진):                                          │
│       object_physics_engine (12대 재질 파괴역학), physics_matrix,           │
│       attack_physics_engine, cave_in_engine, thermal_engine,                │
│       weather_engine, weather_magic_engine, celestial_engine,               │
│       pupil_adaptation_engine, botany_engine, harvest_engine,               │
│       vein_restoration_engine, corpse_ecology_engine                        │
│    ② 전투, 전술 & 생존 (10개 엔진):                                         │
│       poise_engine, stamina_engine, status_engine, injury_engine,           │
│       toxicology_engine, alcohol_engine, mana_burn_engine,                  │
│       stealth_engine, siege_engine, combat_time_track_engine                │
│    ③ NPC 심리 & 사회 역학 (12개 엔진):                                      │
│       psychology_engine (8 아키타입, 14 감정, 트라우마/스트레스 파이프라인),│
│       cognitive_engine, npc_skill_engine, dialogue_slot_engine,             │
│       rumor_diffusion_engine, merchant_barter_engine, bounty_engine,        │
│       party_engine, party_sanity_engine, economy_engine, perception_engine,  │
│       outfit_engine                                                         │
│    ④ 공간 위상 & 인프라 계층 (13개 모듈):                                   │
│       infrastructure.py / infra_models.py (Level 0~5 6계층 현실 인프라),    │
│       map_blueprint_engine.py, map_interactive_renderer.py,                 │
│       dungeon_engine, trap_engine, puzzle_engine, hidden_encounter_engine,  │
│       campsite_engine, ration_engine, sleep_engine, time_calendar_engine,   │
│       quest_engine, graph_engine                                            │
│                                                                             │
│ 4. Local RAG & Vector Memory Layer                                          │
│    - src/memory/qdrant_store.py (로컬 Qdrant 벡터 검색)                     │
│    - src/memory/memory_manager.py (NPC 에피소드 기억 및 단기/장기 컨텍스트) │
│                                                                             │
│ 5. LLM Engine Gateway                                                       │
│    - src/llm/gemini.py, resilience.py (유저 본인 API 키 기반 직접 통신)     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ 로컬 웹소켓 / IPC (JSON 패킷 통신)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 BODY: Client Front-End Presentation (Gradio / Unity)        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. 현재 프로토타입 프론트엔드:                                              │
│    - app.py (Gradio 인터랙티브 탭 UI + 터미널 세션 인터페이스)              │
│    - map_interactive_renderer.py (5계층 인터랙티브 3D 등고선 HTML/SVG 뷰어) │
│                                                                             │
│ 2. 정식 상용화 클라이언트 (Unity Front-End):                                │
│    - 실시간 3D-to-HD-2D 픽셀 렌더링 & 자유 회전(360도) 카메라 조작          │
│    - 3D 모듈러 에셋 스폰 & 드로우콜 단일화(Bake) 메시 병합                  │
│    - Toon Cel-Shading (2~3단 명암) + 1px Depth Outline 외곽선               │
│    - 대화창 고화질 2D 일러스트 초상화 팝업 (SD 1.5 + LoRA + ADetailer 연동) │
│    - 의성어(Gibberish) 사운드 재생 & 플레이어 키보드/패드 입력 처리         │
└─────────────────────────────────────────────────────────────────────────────┘

---

## 3. HD-2D 비주얼 & 렌더링 파이프라인 (쓰레드 오브 타임 방식)

### 3.1 3D-to-Pixel 실시간 렌더링 (카메라 회전 뷰의 비밀)
* **전통 도트 방식의 한계 극복:** 2D 스프라이트로는 360도 카메라 회전 시 16방향 도트 수만 장을 그려야 하므로 1인 개발이 불가능함.
* **해결책:** **[Meshy/AI 사전 제작 3D 로우폴리 모듈러 모델 + 유니티 픽셀화 포스트 프로세싱]**
  * 카메라가 어떤 각도로 회전하든, 3D 모델이 실시간 회전하며 **완벽한 도트 그래픽**으로 자동 래스터화됨.
  * 3D 실시간 광원(포인트 라이트, 횃불, 달빛)을 도트 캐릭터가 그대로 흡수하여 옥토패스 특유의 입체 광원 완성.

### 3.2 필수 최적화 & 렌더링 품질 보정 (결정적 4대 테크닉)
1. **드로우콜(Draw Call) 단일화 Bake (`Mesh.CombineMeshes`):**
   * NPC 1명당 부품(눈, 코, 헤어, 겉옷, 바지, 무기 등)이 15개씩 붙으면 NPC 30명에 드로우콜 450개 발생 ➔ 극심한 렉 유발.
   * **해결:** 캐릭터 생성/조립 완료 즉시 `SkinnedMeshCombiner` / `Mesh.CombineMeshes`로 단일 메시로 베이크(Bake)하여 **캐릭터당 드로우콜 1개로 압축**.
2. **외곽선 뭉개짐 방지 (`Point Filter`):**
   * 카메라 해상도를 낮춘 Render Texture를 메인 캔버스에 올릴 때 필터 모드를 절대 `Bilinear`(흐릿한 블러)로 두지 않고, 반드시 **`Point (no filter / clamp)`**로 강제 ➔ 칼같이 선명한 레트로 픽셀 도트 출력.
3. **도트 자글거림/떨림 제거 (`Pixel Snapping`):**
   * 3D 좌표 이동 시 발생하는 미세한 픽셀 크롤링(부르르 떨림) 방지를 위해 **`Pixel Perfect Camera`** 적용 및 버텍스 셰이더 레벨에서 픽셀 그리드 스냅(Snapping) 처리.
4. **레트로 감성 완성 2대 셰이더:**
   * **Toon Ramp (2~3단 명암 셀 셰이더):** 3D의 부드러운 그러데이션 그림자를 배제하고, [밝음/중간/그림자] 3단계로 딱딱 끊어서 도트의 음영 표현.
   * **1픽셀 뎁스 외곽선 (Pixel Outline):** Depth/Normal 버퍼 기반으로 캐릭터 테두리에 1픽셀 검은 외곽선을 둘러 3D 배경과 도트 캐릭터를 완벽히 분리.

---

## 4. NPC 외모 상세 요소 생성 (하이브리드 모듈러 시스템)

Quilltale의 방대한 텍스트 외형 데이터(`FacialDetails`, `BodyMeasurements`, `ClothingLayer`, `OutfitEngine`)를 어정쩡한 클론 없이 100% 시각화하는 방법:

```
[인게임 필드 3D 도트] (전신 실루엣)
- 체형 메시 (키, 덩치, 종족 베이스)
- 헤어스타일 3D 파츠 (색상 셰이더 적용)
- 모듈러 의상 소켓 결착 (EquipmentSlots: 흉갑, 망토, 견갑 등)
- 텍스처 스왑: 눈/눈썹/입 2D 도트 텍스처를 머리 메시에 스왑 (표정 변화 0.001초 반영)

                     +

[대화창 UI 2D 일러스트] (극실사 디테일)
- 화면 절반에 "초고화질 일러스트 초상화 (Portrait)" 팝업
- NPC.to_image_prompt_keywords() 기반으로 사전/실시간 생성된 AI 초상화
- 눈동자 오드아이, 칼자국 흉터, 입술 주름, 가문 문장 인발 등 미친 디테일을 대화창에서 100% 표현
```
👉 **플레이어 심리:** 대화창의 미친 퀄리티 일러스트를 보는 순간, 인게임의 단순화된 도트 캐릭터를 뇌 내에서 자동으로 고화질로 보정하여 인식함 (발더스 게이트의 원리).

---

## 5. 사운드 & BGM & 의성어 TTS 구조

* **BGM 연동:** 6계층 인프라 권역(`Region`: 사막, 툰드라, 고대 유적) 및 전투 위기 상황(사기 붕괴, 공성전) 태그에 맞춰 사전 라이브러리 음원을 크로스페이드 재생.
* **의성어/가상 음소 TTS 체계 (Full-Speech TTS 전면 배제):**
  * **철학:** 긴 텍스트 문장을 통째로 읽어주는 일반 TTS는 텍스트 RPG 특유의 빠른 읽기 템포를 저해하고 대화 지연 및 과도한 리소스를 유발하므로 **전면 금지**.
  * **방식:** 동물의 숲 / 옥토패스 트래블러 / 젤다의 전설 스타일의 **의성어·가상 음소 웅얼거림(Gibberish / Chatter Sound)**만 채택.
  * **무료 옵션 (기본 탑재, 비용 0원):**
    - 20~30개 기본 감탄사/음소 풀을 유니티 런타임에서 피치 변조(`AudioSource.pitch = 0.70f ~ 1.30f`) 및 룸 리버브를 적용하여 수백 명의 고유 음색 자동 생성.
    - 파이썬 오프라인 배치 스크립트(`pydub`)를 통한 무제한 음소 바리에이션 풀 무료 사전 생성.
  * **유료 옵션 (선택적 DLC / 고품질 사운드팩):**
    - 전문 성우 기반의 직업/성격별 프리미엄 의성어 보이스 팩 DLC.
    - 선택적 고음질 프로시저럴 음소/효과음 합성 엔진(FMOD/Wwise 고급 음소 신디사이저) 연동 지원.

---

## 6. 비즈니스 모델 & 유저 본인 API 키 연동 (BYOK 아키텍처)

* **핵심 명제:** **API 키는 개발사의 것이 아니라, 게임을 플레이하는 유저 본인의 개인 소유 키이다.**
  * 개발사는 중앙 중계 서버를 운영하지 않으며, API 과금 비용과 트래픽 리스크를 일체 부담하지 않음 (**개발사 유지비 0원 / Zero-Liability**).
* **원리 (BYOK: Bring Your Own Key):**
  * 유저는 Google AI Studio에서 본인 명의로 개인 무료 API 키(하루 1,500회 무료) 또는 유료 종량제 키를 발급받아 인게임에 등록.
  * 클라이언트는 유저 본인의 로컬 PC에 키를 안전하게 암호화 보관하며, 백엔드와 Gemini 간 직접 통신 수행.
* **인게임 UX 플로우:**
  1. 게임 최초 실행 또는 설정(Settings) 메뉴 진입.
  2. **[내 Google Gemini API 키 등록 (무료 발급 안내)]** 버튼 클릭.
  3. Google AI Studio 키 발급 브라우저 창 팝업 ➔ 키 복사 후 인게임 입력창에 붙여넣기.
  4. 로컬 PC에 암호화 저장 후, 유저 본인의 일일 무료 할당량으로 무제한 싱글 플레이 진행.
* **효과:**
  * 개발사: **서버비 및 LLM API 유지비 0원, 무한 확장 가능한 영구 무료 인디 모델**.
  * 플레이어: **구글 계정 하나로 평생 무료로 안전하고 무제한한 게임 플레이 가능**.

---

## 7. AI 개발자를 위한 코드 작성 규칙 (Agent Implementation Rules)

향후 본 프로젝트의 시스템 코드를 작성하는 모든 AI(Claude, GPT 등)는 다음을 준수해야 한다:

1. **Two-Pass Resource 분리 엄수:**
   * Pass 1 (Python): 주사위, 대미지, 성벽 내구도, NPC 심리 수치 연산에 절대 LLM을 개입시키지 않는다. (100% 결정론적 수학).
   * Pass 2 (LLM): 결정론적 수치 결과를 기반으로 자연어 묘사/대사 렌더링에만 사용한다.
2. **비동기 격리 (Async Isolation):**
   * 통신, 이미지 로딩, 사운드 처리는 게임 루프를 블로킹하지 않는 비동기 구조로 작성한다.
3. **Single Source of Truth:**
   * 유니티는 독자적인 게임 상태를 갖지 않는다. 모든 진실은 파이썬 `WorldState` JSON에 존재하며, 유니티는 수신된 JSON의 상태를 화면에 그리는 뷰어 역할만 수행한다.
4. **도메인 클래스 `traits` 기본 탑재:**
   * 월드/엔티티 모델 신설 시 `traits: list[str] = field(default_factory=list)`를 필수로 탑재하여 UI 요약 및 돌발 이벤트 판정에 활용한다.

---


## [추가 스펙] 비주얼·배경·음성·패키징 확정 파이프라인

### 1. 대화창 2D 일러스트: SD 1.5 + LoRA + ADetailer (확정)
- **선정 이유:** 
  - SD 1.5는 수년간 축적된 전 세계 판타지 화풍 LoRA 풀이 가장 방대하여 화풍 고정/일관성에 최적.
  - 512~768 해상도 기반으로 로컬 RTX 4060에서 2~3초 만에 초고속 생성 가능.
  - **ADetailer (얼굴 자동 보정 필수 탑재):** 얼굴과 눈동자를 자동 감지해 2차 고해상도 인페인팅 덧칠을 수행하므로, SD 1.5의 단점인 얼굴 뭉개짐을 95% 이상 해결하여 상용급 일러스트 완성.

### 2. 배경 3D 에셋 확보 전략: 하이브리드 (무료 풀 + Meshy)
- **일반 배경/던전/자연물:**
  - 상업적 무료(CC0) 에셋 라이브러리(Kenney.nl, OpenGameArt, itch.io 게임잼 번들) 적극 활용.
  - 벽, 바닥 타일, 나무, 바위, 기본 가구는 무료 에셋에 픽셀화 셰이더를 입혀 0원으로 해결.
- **핵심 랜드마크/특수 사물:**
  - 고유한 마왕성 제단, 고대 유적 룬 석상, 특수 퀘스트 사물 등 상징적 오브젝트만 시간/크레딧 여유 시 Meshy로 선별 생성.

### 3. 스팀 단독 실행 일체형 패키징 (Standalone Executable)
- **UX 목표:** 유저가 스팀에서 [게임 시작]을 누르면, 백엔드 콘솔이나 파이썬의 존재를 전혀 모른 채 단독 게임 창 하나만 즉시 팝업되어 플레이 시작.
- **빌드 구조:**
  - 파이썬(Quilltale) 백엔드: `PyInstaller` 또는 `Nuitka`를 통해 단독 실행 바이너리로 패키징.
  - 유니티(Unity) 클라이언트: 실행 시 백그라운드에서 로컬 파이썬 바이너리를 자동 호출/종료하도록 생명주기(Lifecycle) 바인딩.

### 4. TTS/의성어 배리에이션 무한 확장 (Full-Speech 배제 & 의성어 전용 단일화)
- **핵심 철학:** 긴 대사 문장을 통째로 읽어주는 일반 TTS는 게임 템포 저하 및 리소스 낭비로 인해 **완벽히 배제**. 오직 옥토패스 트래블러 / 동물의 숲 스타일의 **의성어·가상 음소 웅얼거림(Gibberish Chatter)**만 채택.
- **무료 옵션 (기본 엔진 탑재, 비용 0원):**
  - 기본 감탄사 20~30세트 기반 유니티 런타임 피치 변조(`AudioSource.pitch = 0.70f ~ 1.30f`) 및 룸 리버브로 수백 명의 음색을 실시간 자동 파생 (젤다/동물의 숲 공식 방식).
  - 파이썬 오프라인 배치 스크립트(`pydub`)를 통해 반음(Semitone) 피치, 템포, EQ를 적용한 100개 이상의 음소 풀 무료 사전 생성.
- **유료 옵션 (선택적 DLC / 프리미엄 팩):**
  - 전문 성우 녹음 기반의 직업/성격/종족별 고음질 의성어 보이스 팩 DLC.
  - 선택적 고품질 프로시저럴 음향 합성 엔진(FMOD/Wwise 고급 가상 음소 신디사이저) 플러그인 연동.

---

## 8. 로드맵 및 스코프 게이트 (Scope Gate)
- **원칙 (Relocated from AGENTS.md):** TTS, 3D, sound/BGM, 캐릭터 일러스트는 최종 단계로 동결/연기한다. 핵심 시뮬레이션 엔진이 완전히 배선되고 안정화되기 전까지는 스캐폴딩 작업을 진행하지 않는다.

---

## 9. 디자인/아키텍처 결정 및 Q&A 기록 (Design Decisions & Q&A)
- **Q. 옥토패스 트래블러 스타일 2D-3D HD-2D 도트 그래픽 구현 시, 2D 좌표와 노드-엣지 그래프만으로 장비/건물/몬스터/외형 모델링 및 그래픽 표현이 가능한가?**:
  - **A. 공간 위상(Topology)과 시각 표현(Visual Presentation)의 분리 원칙**:
    1) 2D 유클리드 좌표 + 노드-엣지 그래프는 **"세계의 뼈대와 연결 구조(어디에 무엇이 있고 어떻게 이동/충돌하는가)"**를 정의하는 순수 데이터 레이어임.
    2) 외형(시각적 렌더링)은 좌표 자체가 아니라 엔티티 데이터에 부여된 **결정론적 태그(`traits`), 메타데이터 템플릿(`visual_profile`, 재질, 양식, 손상도), 프로시저럴 타일셋/페이퍼돌 스프라이트 조립 규칙**을 통해 생성됨.
    3) **건물/맵**: 좌표(x, y, w, h) + 연결 노드(문/벽/창문) + 건축 테마(예: '고딕 양식 석조', '퇴색된 참나무') -> 타일셋 자동 배치 및 2.5D 깊이감(Z-축 빌보드/스프라이트) 부여.
    4) **장비/캐릭터**: 장비 부위 + 소재(강철, 미스릴) + 제작 양식 + 상태(녹슨, 피묻은) -> 도트 레이어 합성(Paper-Doll 스프라이트 시스템: 몸체 베이스 + 의복 레이어 + 무기 오버레이).
    5) **LLM의 역할**: LLM은 픽셀을 직접 그리는 것이 아니라 100% 결정론적 팩트시트를 받아 시각적/감각적 서사(Pass 2)를 묘사하며, 실제 그래픽 렌더러는 파이썬 월드 스테이트의 결정론적 시각 데이터 구조를 읽어 스프라이트/도트 그래픽을 화면에 렌더링함.