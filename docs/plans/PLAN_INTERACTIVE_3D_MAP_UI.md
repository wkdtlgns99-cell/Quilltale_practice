# [설계 계획서] 인터랙티브 3D 오버월드 지도 UI (Interactive Pin & Flag Map)

> **문서 상태**: 계획 수립 완료 (보관 / 향후 구현 예정)  
> **생성일시**: 2026-09-21  
> **관련 모듈**: `src/world/map_blueprint_engine.py`, `src/world/state.py`, `app.py`

---

## 1. 개요 및 목적
- **목적**: 16:9 순수 2D-3D HD-2D 배경 맵 아트 위에 게임 엔진이 계산한 (X, Y, Z) 좌표를 결합하여, 마우스 클릭 시 세부 정보(거점명, 해발 고도, 5계층 시설, 도로 경사도, 소속 국가 등)가 팝업되는 인터랙티브 지도 시스템 구축.
- **핵심 철학**:
  1. **배경과 텍스트 분리**: 배경 맵 그림에는 글자를 직접 새기지 않고 순수 고화질 아트로 유지 (다국어 지원 및 텍스처 재활용).
  2. **동적 핀/깃발 UI 오버레이**: 게임 엔진이 5계층 인프라 좌표를 읽어 HTML/SVG 인터랙티브 핀과 도로망을 오버레이.
  3. **Zero Business Logic in UI (`Code_Hygiene Rule 6`)**: `app.py`는 I/O 및 렌더링만 담당하며, 모든 지도 데이터 바인딩 및 HTML 컴파일은 순수 파이썬 엔진 모듈(`MapInteractiveRenderer`)이 처리.

---

## 2. 아키텍처 및 세부 설계

### 1) 신규 모듈: `src/world/map_interactive_renderer.py`
- **책임**: 3D 지도 청사진(`Map3DBlueprint`)과 월드 상태(`WorldState`)를 받아 마우스 인터랙션이 가능한 고성능 HTML/CSS/JS 문자열 생성.
- **주요 기능**:
  1. **좌표 정규화 (Normalization)**:
     - 월드 좌표 `(x_km, y_km)` 및 바운드 `(min_x, min_y, max_x, max_y)`를 16:9 컨테이너 기준 백분율 `(left_pct, top_pct)`로 1:1 투영 (8% ~ 92% 여백 클램핑).
  2. **아키타입별 3D 입체 핀 (Custom Pins & Flags)**:
     - 🏰 수도/성채 (`capital_metropolis`)
     - 🌋 화산마을 (`volcanic_settlement`)
     - ❄️ 설산 수도원 (`monastic_town`)
     - ⚓ 항구 포구 (`fishing_cove`, `coastal_port`)
     - 🌳 수관마을 (`treetop_village`)
     - 🏜️ 오아시스 (`oasis_crossroad`)
     - ⛏️ 지하도시 (`underground_excavation`)
     - ★ 플레이어 현재 거점 (황금빛 파동 펄스 애니메이션)
  3. **3D 도로망 SVG 오버레이**:
     - 정주지 간 도로를 연결하는 반투명 점선 궤적 렌더링.
  4. **마우스 호버 & 클릭 팝업 카드 (Detail Inspector)**:
     - **호버**: 지명 + 해발 고도 툴팁 (`서리줄기 수도촌 (해발 1,250m)`).
     - **클릭**: 지도 하단 인스펙터 패널에 상세 정보 카드 전개:
       - 지명, 격식, 인구, 치안도, 소속 국가 및 관세율
       - 해발 고도 Z축 및 지형 바이옴
       - 5계층 시설 목록(주점, 대장간, 성당 등) 및 상주 NPC
       - 연결된 도로망 거리(km) 및 경사도(°)
       - `[📍 이곳으로 이동 선언]` 빠른 입력 지원 버튼 (액션 입력창 자동 연동)

### 2) 월드 상태 연동: `src/world/state.py` & `src/world/map_blueprint_engine.py`
- `WorldState.active_map_image: str = "data/maps/default_overworld.jpg"` 필드 추가 (하위 호환 기본값 보장).
- `WorldState.to_map_html()` 편의 메서드 제공.
- `MapBlueprintEngine.to_interactive_html()` 정적 메서드 제공.

### 3) Gradio UI 연동: `app.py`
- 좌측 HUD 탭(`with gr.Tabs():`)에 `🗺️ 3D 오버월드 지도` 탭 추가:
  ```python
  with gr.TabItem("🗺️ 3D 지도"):
      map_display = gr.HTML(elem_classes="qt-accord")
  ```
- 턴 진행 및 세이브 로드 시 `state.to_map_html()`을 `map_display`로 전달.

---

## 3. 검증 계획
1. 단위 테스트: `tests/test_map_interactive_renderer.py` (좌표 정규화, 핀 생성, 카드 데이터 바인딩).
2. 전체 회귀 테스트: `pytest tests/` (681+ passed 유지).
3. 무효 전이율 평가: `python eval_runner.py --no-judge` (0.0% 유지).
4. 수동 브라우저 테스트: Gradio UI에서 핀 클릭 및 팝업 카드 정상 렌더링 확인.
