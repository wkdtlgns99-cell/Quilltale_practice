"""
Macro Calendar & Dynamic Action Duration Engine for Quilltale TRPG.
Manages flexible daily action durations (min~max minutes), dynamic start year resolution,
cosmology epochs, seasonal shifts, and environmental butterfly effects (lighting, temperature, shop hours).
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
import random

from src.world.state import WorldState


# Comprehensive In-Game Daily Action Duration Matrix (min_minutes, max_minutes, default_minutes)
DAILY_ACTION_DURATIONS: Dict[str, Dict[str, Any]] = {
    "stealth_creeping": {
        "name_ko": "잠입 및 은밀 보행",
        "keywords": ["잠입", "은밀", "숨죽이", "살금살금", "기척을 숨기", "은폐", "포복", "stealth", "creep"],
        "min_m": 15,
        "max_m": 30,
        "default_m": 20,
        "fatigue_cost": 3,
        "description": "극도의 긴장 속에 발소리를 죽이며 이동",
    },
    "study_reading": {
        "name_ko": "연구 및 서적 독서",
        "keywords": ["연구", "독서", "읽", "책", "고문서", "마도서", "해독", "기록을 살피", "study", "read"],
        "min_m": 60,
        "max_m": 180,
        "default_m": 90,
        "fatigue_cost": 2,
        "description": "난해한 고문서나 마법서의 집중 열독",
    },
    "martial_training": {
        "name_ko": "무술 훈련 및 초식 연마",
        "keywords": ["훈련", "수련", "검술 연습", "초식", "단련", "타격 연습", "training", "practice"],
        "min_m": 60,
        "max_m": 120,
        "default_m": 60,
        "fatigue_cost": 15,
        "description": "전신 근육을 혹사하는 실전 무예 단련",
    },
    "meditation_prayer": {
        "name_ko": "기도 및 명상",
        "keywords": ["기도", "명상", "단전 호흡", "마나 조율", "묵상", "신에게", "meditation", "pray"],
        "min_m": 30,
        "max_m": 60,
        "default_m": 45,
        "fatigue_cost": -5,
        "description": "정신을 가다듬고 내면의 마나 순환을 정돈",
    },
    "corpse_looting": {
        "name_ko": "시체 수색 및 루팅",
        "keywords": ["시체", "루팅", "뒤지", "소지품을 털", "수색해 챙기", "전리품 수습", "loot"],
        "min_m": 5,
        "max_m": 10,
        "default_m": 5,
        "fatigue_cost": 1,
        "description": "피 묻은 장구류와 안주머니 속 귀중품 수색",
    },
    "field_harvesting": {
        "name_ko": "야수 도축 및 채집",
        "keywords": ["도축", "가죽 채취", "약초 채집", "약초를 캐", "해체", "무두질", "harvest", "gather"],
        "min_m": 15,
        "max_m": 45,
        "default_m": 30,
        "fatigue_cost": 5,
        "description": "정밀한 칼질로 가죽을 벗기거나 약초 뿌리 보존",
    },
    "barter_shopping": {
        "name_ko": "상점 흥정 및 구매",
        "keywords": ["상점", "구매", "산다", "흥정", "가격을 깎", "장보기", "거래", "shop", "buy", "barter"],
        "min_m": 10,
        "max_m": 20,
        "default_m": 15,
        "fatigue_cost": 1,
        "description": "상인과 눈치를 보며 가격을 조율하고 결제",
    },
    "interrogation": {
        "name_ko": "포로 심문 및 추궁",
        "keywords": ["심문", "자백", "추궁", "고문", "캐묻", "자백을 받아", "interrogate"],
        "min_m": 20,
        "max_m": 60,
        "default_m": 30,
        "fatigue_cost": 4,
        "description": "거짓말을 간파하며 진실을 실토하도록 압박",
    },
    "cooking_eating": {
        "name_ko": "요리 및 식사",
        "keywords": ["요리", "밥", "식사", "먹", "조리", "고기를 굽", "식사를 하", "cook", "eat"],
        "min_m": 30,
        "max_m": 60,
        "default_m": 40,
        "fatigue_cost": -10,
        "description": "불을 피워 음식을 조리하고 영양 보충",
    },
    "camp_setup": {
        "name_ko": "야영지 구축 및 방호벽 설치",
        "keywords": ["야영", "캠프", "텐트", "방호벽", "모닥불", "야영지", "camp", "setup"],
        "min_m": 30,
        "max_m": 45,
        "default_m": 35,
        "fatigue_cost": 8,
        "description": "바람을 막고 맹수를 경계할 방호 설비 구축",
    },
    "weapon_sharpening": {
        "name_ko": "장비 손질 및 숫돌 연마",
        "keywords": ["숫돌", "칼을 갈", "무기 손질", "연마", "갑옷 수선", "날을 세", "sharpen", "repair"],
        "min_m": 15,
        "max_m": 30,
        "default_m": 20,
        "fatigue_cost": 3,
        "description": "무딘 칼날을 세우고 결속 가죽 끈 정비",
    },
    "general_exploration": {
        "name_ko": "주변 정찰 및 탐색",
        "keywords": ["탐색", "조사", "살펴", "주변을 둘러", "정찰", "search", "explore", "look"],
        "min_m": 15,
        "max_m": 30,
        "default_m": 20,
        "fatigue_cost": 3,
        "description": "방이나 숲 주변의 이상 징후 정찰",
    },
    "deep_investigation": {
        "name_ko": "정밀 수색 및 감식",
        "keywords": ["정밀 수색", "샅샅이", "단서 감식", "벽을 두드리", "비밀 통로 찾", "investigate"],
        "min_m": 30,
        "max_m": 60,
        "default_m": 45,
        "fatigue_cost": 6,
        "description": "벽 틈새와 바닥 장판 밑까지 집요하게 수색",
    },
    "short_rest": {
        "name_ko": "짧은 휴식 및 숨고르기",
        "keywords": ["휴식", "잠시 쉬", "숨을 고르", "앉아서 쉬", "short rest", "rest"],
        "min_m": 30,
        "max_m": 60,
        "default_m": 30,
        "fatigue_cost": -25,
        "description": "호흡을 진정시키고 체력 회복",
    },
    "long_rest": {
        "name_ko": "숙면 및 긴 휴식",
        "keywords": ["숙면", "잠을 잔", "자고 일어", "아침까지 잔", "밤을 보낸", "long rest", "sleep"],
        "min_m": 480,
        "max_m": 480,
        "default_m": 480,
        "fatigue_cost": -100,
        "description": "8시간 완전 숙면",
    },
}


@dataclass
class TimeCalendarEngine:
    TRAITS: List[str] = field(default_factory=lambda: [
        "거시 역법 엔진",
        "가변 시간 매트릭스",
        "나비효과 연동",
        "동적 기년법"
    ])
    traits: List[str] = field(default_factory=lambda: [
        "거시 역법 엔진",
        "가변 시간 매트릭스",
        "나비효과 연동",
        "동적 기년법"
    ])

    @classmethod
    def resolve_world_start_year(cls, cosmology_template: Dict[str, Any], world_id: str = "") -> int:
        """
        세계관 시작 연도 결정 (1024년 고정 탈피).
        템플릿에 명시된 값이 있으면 사용, 없으면 시드 기반 1~3000년 자율 할당.
        """
        if cosmology_template and "start_year" in cosmology_template:
            try:
                return int(cosmology_template["start_year"])
            except (ValueError, TypeError):
                pass

        seed_str = world_id or cosmology_template.get("name", "quilltale_default")
        val = sum(ord(c) * (i + 1) for i, c in enumerate(seed_str))
        return 1 + (val % 3000)

    @classmethod
    def determine_action_duration(cls, action_text: str) -> Tuple[str, int, int]:
        """
        자연어 행동 텍스트를 분석하여 일치하는 일상 행동 유형과 경과 시간(분), 피로도 변화 반환.
        반환: (action_key, minutes_elapsed, fatigue_delta)
        """
        action_lower = action_text.lower()

        # 우선순위 매칭: 키워드 검색
        for a_key, data in DAILY_ACTION_DURATIONS.items():
            for kw in data["keywords"]:
                if kw in action_lower:
                    return (a_key, data["default_m"], data["fatigue_cost"])

        # 기본 일반 행동: 10분 소요
        return ("default_action", 10, 1)

    @classmethod
    def advance_time(
        cls,
        state: WorldState,
        minutes: int,
        fatigue_delta: int = 0
    ) -> Dict[str, Any]:
        """
        인게임 시간을 경과시키고, 나비효과(조도, 기온, 상점 영업시간, 신문 발간)를 갱신.
        """
        prior_day = state.current_day
        prior_hour = state.current_hour

        # 1. 시간 및 피로도 적용
        state.player.time_elapsed_minutes += minutes
        if fatigue_delta != 0:
            state.player.fatigue = max(0, min(100, state.player.fatigue + fatigue_delta))

        # 2. 조도 및 시간대(time_of_day) 나비효과
        cur_hour = state.current_hour
        season = state.current_season

        if 6 <= cur_hour < 18:
            state.environment.time_of_day = "낮"
            state.environment.lighting = "적당한 밝기"
        elif 18 <= cur_hour < 21:
            state.environment.time_of_day = "황혼"
            state.environment.lighting = "희미한 황혼빛"
        elif 21 <= cur_hour or cur_hour < 5:
            state.environment.time_of_day = "심야"
            state.environment.lighting = "칠흑 같은 어둠"
        else:
            state.environment.time_of_day = "새벽"
            state.environment.lighting = "푸르스름한 여명"

        # 3. 계절 및 밤낮 기온 보정
        base_temp = 20
        if "겨울" in season:
            base_temp = 2
        elif "여름" in season:
            base_temp = 28
        elif "가을" in season:
            base_temp = 15
        else: # 봄
            base_temp = 16

        # 심야에는 기온 5도 급강하
        if state.environment.time_of_day == "심야":
            base_temp -= 5
        state.environment.temperature_celsius = base_temp

        # 4. 상점 영업시간 (07:00 ~ 22:00) 판정
        is_shops_open = (7 <= cur_hour < 22)

        # 5. 일자 변경 감지
        day_changed = (state.current_day > prior_day)

        return {
            "minutes_advanced": minutes,
            "current_time_display": state.calendar_display_ko,
            "time_of_day": state.environment.time_of_day,
            "lighting": state.environment.lighting,
            "temperature_celsius": state.environment.temperature_celsius,
            "is_shops_open": is_shops_open,
            "day_changed": day_changed,
            "current_season": season,
            "player_fatigue": state.player.fatigue,
        }
