"""
Dynamic World Generator for Quilltale TRPG Engine.
Uses LLM to generate a completely unique fantasy continent/world each session.
World base is rich Fantasy (High Fantasy, Dark Fantasy, Medieval Fantasy, Mythic, etc.),
containing diverse, richly-themed regional locations within the same world.
"""
import json
import uuid
import random
import logging
from typing import Optional, List, Dict
from src.core.config import BASE_DIR, TEMPLATES_DIR
from src.world.skills import SkillSystem

logger = logging.getLogger(__name__)

# Broad Fantasy World Genres
FANTASY_WORLD_GENRES = [
    "정통 하이 판타지",
    "다크 판타지",
    "중세 모험 판타지",
    "신화적 영웅 판타지",
    "검과 마법의 모험 판타지",
    "황혼의 고대 판타지",
    "비전 마법 판타지"
]

# Rich Regional Theme Inspiration Examples (Used as inspiration pool for locations within the world)
REGION_THEME_INSPIRATIONS: List[Dict[str, any]] = [
    # 1. 산업 & 연금술
    {
        "id": "theme_alchemy_slum",
        "name": "유황 연기 자욱한 산업 연금술 슬럼과 증기 운하",
        "elements": [
            "산성비 내리는 붉은 벽돌 골목",
            "고압 파이프라인 증기 기계 장치",
            "유독성 폐수 운하",
            "불법 인조인간(호문쿨루스) 암시장",
            "유리 비커 첨탑의 연금술 길드"
        ]
    },
    # 2. 코스믹 & 신화
    {
        "id": "theme_god_corpse",
        "name": "거대 신의 석화된 시체와 골수 채굴 광산",
        "elements": [
            "대지에 쓰러진 신의 거대한 갈비뼈 협곡",
            "신의 핏줄(신성 에테르 광맥)을 파내는 광부 거주지",
            "굳어버린 심장 제단",
            "석화된 피 파편에서 태어난 이형 생명체"
        ]
    },
    # 3. 오리엔탈 판타지
    {
        "id": "theme_ghost_bazaar",
        "name": "비단길 카라반과 유령 바자르",
        "elements": [
            "황혼 이후에만 열리는 차원 교역 시장",
            "환각을 유발하는 향신료 연막",
            "공중에 매달린 양탄자 골목",
            "모래 정령과 결탁한 상인 길드",
            "항아리에 봉인된 고대 마신"
        ]
    },
    # 4. 아포칼립스 & 황무지
    {
        "id": "theme_salt_wasteland",
        "name": "뼈와 소금으로 뒤덮인 마른 소금사막과 망령 해협",
        "elements": [
            "햇빛에 하얗게 바랜 소금 평원",
            "바다가 증발해 드러난 거대 산호 골격",
            "소금 결정체 골렘",
            "바퀴 달린 모래 돛단배(랜드세일러) 선단"
        ]
    },
    # 5. SF 판타지 & 외계
    {
        "id": "theme_glass_crater",
        "name": "유성 낙하지대와 유리화된 분화구 크레이터",
        "elements": [
            "운석 충돌열로 녹아내려 굳은 푸른 유리 대지",
            "우주 방사능을 방출하는 외계 유성석",
            "푸른빛으로 변이된 외계 생태계",
            "크레이터 가장자리의 천문 관측 요새"
        ]
    },
    # 6. 고딕 기계장치
    {
        "id": "theme_automaton_theater",
        "name": "인형술사의 저택과 오토마톤 극장",
        "elements": [
            "촛불과 붉은 벨벳 커튼의 거대 극장식 저택",
            "정교한 태엽 장치 기계인형",
            "미동도 없이 앉아있는 목각 관객들",
            "마력 실로 통제되는 꼭두각시 무대",
            "지하 태엽 태동 공방"
        ]
    },
    # 7. 다크 판타지 늪지
    {
        "id": "theme_toxic_swamp",
        "name": "끝없이 침몰하는 맹독 늪지와 침엽수림",
        "elements": [
            "발이 푹푹 꺼지는 이끼 진흙탕",
            "썩은 고목 내부의 맹독성 포자 가스",
            "가라앉아 기울어진 고대 목조 요새",
            "늪지 마녀들의 수상 오두막",
            "안개 속을 배회하는 거대 늪지 생물"
        ]
    },
    # 8. 공간 왜곡 & 거울
    {
        "id": "theme_mirror_palace",
        "name": "거울과 왜곡된 차원의 유리 미궁 궁전",
        "elements": [
            "빛의 굴절로 원근감이 깨진 은빛 회랑",
            "거울 표면을 뚫고 나오는 도플갱어",
            "공중에 흩날리는 예리한 유리 파편 폭풍",
            "스펙트럼을 분광시키는 프리즘 결계실"
        ]
    },
    # 9. 북유럽 설원
    {
        "id": "theme_frost_fjord",
        "name": "얼어붙은 피오르드와 서리 거인의 룬 제단",
        "elements": [
            "오로라가 비추는 빙하 협곡",
            "고대 서리 거인의 빙결 유골",
            "고래 기름 등불이 켜진 목조 롱하우스",
            "룬 문자가 새겨진 얼음 비석"
        ]
    },
    # 10. 해양 & 산호 군도
    {
        "id": "theme_coral_archipelago",
        "name": "산호초 군도와 침몰한 해저 유적 항구",
        "elements": [
            "에메랄드빛 산호초 요새",
            "조수 간만에 따라 드러나는 고대 해저 신전 기둥",
            "거대 진주 제단과 심해 생물",
            "난파선 목재로 지어진 해적 교역항"
        ]
    },
    # 11. 거대 세계수 원시림
    {
        "id": "theme_world_tree_forest",
        "name": "영혼의 세계수 뿌리와 드루이드 거석 원형진",
        "elements": [
            "하늘을 가리는 거대한 세계수의 뿌리 동굴",
            "밤이면 스스로 빛나는 발광 버섯과 이끼 군락",
            "야생 정령과 교감하는 고대 거석(스톤헨지)",
            "나무 껍질과 덩굴로 엮은 공중 회랑"
        ]
    },
    # 12. 지하 드워프 마그마 성채
    {
        "id": "theme_magma_forge",
        "name": "끓어오르는 용암 폭포와 고대 골렘 제련소",
        "elements": [
            "붉은 마그마가 쏟아져 내리는 단층 절벽",
            "수천 년 된 고대 드워프의 거대 모루와 망치",
            "흑요석과 화염 정령이 깃든 골렘 작업장",
            "열기를 식히는 지하 심도 수로"
        ]
    }
]

INTRO_STRUCTURES = {
    "A": {
        "title": "일상 속 기묘한 균열 (호빗, 센과 치히로 스타일)",
        "guide": "평화롭고 서정적인 삶의 터전(마을, 장터, 공방, 사원)에 일상과 어울리지 않는 이질적인 존재/유물/손님이 침투하는 도입부.",
        "start_loc_type": "평화로운 마을, 활기찬 장터, 공방, 사원 안뜰, 선술집",
        "detail": """[오프닝 연출 구조 A: 일상 속 기묘한 균열]
1. 원경: 판타지 세계의 서정적인 자연 풍경, 계절의 변화, 평화로운 거시 환경 묘사.
2. 중경: 규칙적인 일상이 돌아가는 삶의 터전(마을, 일터, 장터, 사원)의 활기찬 분위기.
3. 근경: 일상과 어울리지 않는 이질적인 존재(기묘한 손님, 떠내려온 궤짝, 핏빛 표식, 신비한 유물 등)의 침투와 지인 NPC의 당황스러운 반응.
4. 줌인: 일상적인 소지품을 쥔 주인공의 감각과 이물질이 뿜어내는 기운 묘사."""
    },
    "B": {
        "title": "거대한 외부 세력의 도래 (해리 포터, 스타워즈 스타일)",
        "guide": "평범하거나 고립된 장소 상공/입구에 거대 세력의 군대, 이형의 사절단, 혹은 신수가 들이닥치며 위압감이 발생하는 도입부.",
        "start_loc_type": "외곽 요새, 언덕 위 관측소, 협곡 보초소, 사원 대문",
        "detail": """[오프닝 연출 구조 B: 거대한 외부 세력의 도래]
1. 원경: 웅장하거나 압도적인 지형, 하늘의 거대한 이변이나 안개를 가르는 거대 세력의 실루엣.
2. 중경: 고립되거나 평범한 장소 상공/입구에 이형의 사절단이나 거대 군세가 들이닥치며 생기는 물리적 위압감.
3. 근경: 외부 세력이 남긴 기이한 표식, 룬 문자, 통제관 NPC들의 다급한 명령이나 경고문.
4. 줌인: 플레이어가 느끼는 살갗의 위압감과 비정상적으로 요동치는 소지품."""
    },
    "C": {
        "title": "재난과 조난의 소용돌이 (극한 생존 스타일)",
        "guide": "해당 지역 환경에 어울리는 조난/재난 현장(난파된 잔해, 무너진 유적 석실, 눈보라 고립 산장, 모래폭풍 속 매몰지 등)에서 깨어나는 도입부.",
        "start_loc_type": "난파된 잔해, 무너진 고대 석실, 눈보라 고립 산장, 모래폭풍 속 폐허",
        "detail": """[오프닝 연출 구조 C: 재난과 조난의 소용돌이]
1. 원경: 험난하고 위험한 미지의 환경(폭풍우 치는 바다, 마력 폭풍의 사막, 눈보라 치는 설산, 붕괴하는 유적 등).
2. 중경: 해당 지역에 맞는 조난/붕괴 현장(난파선 잔해, 무너진 석실, 파손된 캐러밴 마차).
3. 근경: 파손된 잔해 틈새로 새어 나오는 위험 요소(연기, 마력, 냉기, 괴성), 생존자 NPC의 다급한 외침.
4. 줌인: 충격으로 인한 신체적 고통이나 잔향, 손에 쥐어진 손상된 도구의 감각."""
    },
    "D": {
        "title": "사건의 잔해와 남겨진 족적 (위쳐, 반지의 제왕 스타일)",
        "guide": "방금 전까지 참변이나 마수 습격이 벌어졌던 장소(약탈당한 야영지, 불탄 보초탑, 핏자국이 낭자한 제단)에서 단서를 추적하는 도입부.",
        "start_loc_type": "약탈당한 야영지, 훼손된 제단, 습격당한 폐허",
        "detail": """[오프닝 연출 구조 D: 사건의 잔해와 남겨진 족적]
1. 원경: 스산하고 황량한 분위기, 낮게 깔린 안개, 까마귀 떼 등 불길한 징조가 맴도는 거시 배경.
2. 중경: 방금 전까지 참변이나 격투가 벌어졌던 장소(약탈당한 야영지, 파괴된 보초탑, 불탄 흔적).
3. 근경: 핏자국, 바닥에 찍힌 기이한 발자국, 숨이 넘어가는 목격자 NPC의 결정적 단서 한마디.
4. 줌인: 손에 쥔 무기나 추적 도구의 감각과 바람을 타고 오는 냄새."""
    },
    "E": {
        "title": "단절된 공간과 미지의 표식 (디스코 엘리시움, 큐브 스타일)",
        "guide": "외부와 철저히 차단된 밀폐 공간(고대 봉인 석실, 지하 감옥, 마법 결계실)에서 흐릿한 의식으로 깨어나는 도입부.",
        "start_loc_type": "봉인된 고대 석실, 잊혀진 지하 감옥, 신비로운 결계방",
        "detail": """[오프닝 연출 구조 E: 단절된 공간과 미지의 표식]
1. 원경: 외부와 철저히 차단된 밀폐 공간의 전체적인 구조와 차가운 공기감, 기이한 조명.
2. 중경: 방 한가운데 놓인 주체(깨진 마법진, 작동 중인 신비한 장치, 잠긴 석문 등)의 기괴한 상태.
3. 근경: 벽면에 새겨진 경고문, 널브러진 서적의 일기장 한 페이지, 멀리서 들려오는 심장 박동음.
4. 줌인: 흐릿한 의식에서 깨어난 플레이어의 신체 감각과 손에 쥐어진 정체불명의 유물."""
    },
    "F": {
        "title": "수군거리는 소문과 의혹의 발단 (스카이림, 셜록 홈즈 스타일)",
        "guide": "주변 인물들이 주고받는 의문의 소문이나 대화로 즉각 시작하며 사건에 휘말리는 도입부.",
        "start_loc_type": "사람들로 붐비는 선술집 구석, 야간 모닥불 앞, 대상들의 천막",
        "detail": """[오프닝 연출 구조 F: 수군거리는 소문과 의혹의 발단]
1. 대화(Hook): 주변 인물들이 주고받는 의문의 소문이나 대화로 배경 설명 없이 즉각 시작.
2. 배경 확장: 대화가 오가는 장소(선술집 구석, 모닥불 앞, 시장통 등)의 소음과 바깥 풍경으로 시야를 넓히며 상황 제시.
3. 단서 포착: 대화 속 내용과 직접적으로 연관된 이질적인 인물의 등장이나 밖에서 들려오는 이상 징후/충격적인 목격담.
4. 줌인: 대화를 엿듣거나 참여 중이던 주인공의 위치와 손에 쥔 물건."""
    },
}


GENERATOR_SYSTEM_PROMPT = """
당신은 최고 수준의 창의성과 치밀한 개연성을 갖춘 정통 판타지 TRPG 세계관 마스터입니다.

### [세계관 & 지역 설계 원칙]
1. **판타지 기반의 거대 대륙(World):**
   - 세계관 자체는 풍요롭고 광대한 정통 판타지 대륙(중세 판타지, 다크 판타지, 신화 판타지 등)을 기반으로 합니다.
   - 세계 전체가 하나의 좁은 테마로 획일화되지 않도록, 대륙 내에 제국, 왕국, 길드, 부족, 신전 등 다양한 세력과 문화가 공존하게 하십시오.

2. **다채로운 지역(Locations/Regions)의 개성 융합:**
   - 대륙 내의 각 장소(4~6개 Location)들은 저마다 독특하고 개성 넘치는 지형, 생태계, 문화, 환경 기믹을 가집니다.
   - 아래에 제공되는 [지역 설계 영감 예시]들을 참고하여, 지역마다 서로 다른 신선한 분위기(예: 어떤 곳은 연금술 슬럼, 어떤 곳은 거대 신의 뼈 광산, 어떤 곳은 유령 바자르 사막 등)가 대륙 안에서 유기적으로 조화를 이루도록 설계하십시오.

3. **물리 과학 기반 마법 & 100% 한국어 플레이어 텍스트:**
   - 마법은 화학, 열역학, 마찰, 중력, 생물학적 인과관계와 유기적으로 결합합니다.
   - 고유명사, 지명, 묘사, 대사는 몰입감 높은 한국어로 작성하십시오.
"""

GENERATOR_PROMPT = """
정통 판타지 대륙을 무대로 하되, 내부 지역들이 저마다 독특한 테마와 개성을 가진 완전히 새로운 판타지 TRPG 세계를 JSON으로 설계하십시오.

==================================================
★ [이번 세계의 거시 장르]: {world_genre}

★ [RAG 검색된 판타지 생체·물리 법칙 영감 풀 (Arcane Physics Inspiration Reference)]:
{arcane_laws_text}

★ [RAG 검색된 현실성·인과성 메커니즘 영감 풀 (Realism Causality Inspiration Reference)]:
{realism_laws_text}

★ [RAG 검색된 필드 준보스 & 보스 몬스터 영감 풀 (Gimmick Boss Inspiration Reference)]:
{monster_inspiration_text}
==================================================

★ [★ 절대 규칙: 템플릿 단순 복제 금지 & 테마 맞춤 변형 재창조]:
1. 위 템플릿들은 인과율과 부작용 설계를 위한 '영감 예시'일 뿐입니다.
2. 위 명칭이나 텍스트를 그대로 복사하여 사용하지 마십시오.
3. 이번 세계의 거시 장르({world_genre})와 세부 배경에 어울리도록, 독창적인 이름과 생생한 부작용을 가진 [고유 판타지 생체·물리 법칙] 2~3개를 새롭게 창조하여 world_lore.arcane_laws에 담으십시오.

★ [세계 속 지역 설계를 위한 영감 예시 풀 (Inspiration Examples)]:
다음 예시들을 자유롭게 참고하거나 변형하여, 대륙 내 4~6개 장소들이 저마다 다채로운 개성을 갖도록 설계하십시오:
{region_inspiration_text}
==================================================

★ [이번 세계의 오프닝 연출 구조]:
{intro_detail}

★ [시작 장소(player.location) 일치 원칙]:
1. 플레이어의 시작 위치(`player.location`)는 위 오프닝 연출 구조에 부합하는 '{start_loc_type}'이어야 합니다.
2. 시작 장소의 `id`, `name`, `description`은 위 오프닝 상황의 직접적인 무대여야 하며, 시작 장소에 배치되는 NPC들도 오프닝 사건에 직결된 인물들로 구성하십시오.

[세계관 생성 상세 규칙]
- 국가/세력(factions): 2~3개 (대립/동맹 관계, 사회적 금기 포함)
- 거시 설정(world_lore): 대륙의 신화, 종족 특성, 마법 기원
- 장소(locations): 4~6개, **각 장소마다 서로 다른 독창적인 지형과 환경 기믹(environmental_hazards)을 갖추어 다채롭게 구성**
- NPC: 4~6명, 13대 인간 심층 팩터 의무 탑재 (욕망, 약점, 관계망, 트라우마, 버릇, 금기, 스케줄 등)
- 아이템: 8~12개, 유틸리티 도구 및 전설급 아이템 1개 이상
- 세계관 비밀(world_secrets): 거대 미스터리와 단서 조각(clues) 1개 이상
- 과학 기반 마법 지식: 인게임 서적/안내문/낙서 형태로 2개
- 플레이어 초기 스탯: 8개 핵심 스탯 각각 8~16 사이 무작위
- 고유 스킬 및 마법 체계 (Modular Incantations & Ancient Words):
  * NPC 중 2~3명은 고유 스킬(unique skill) 보유
  * 모듈러 슬롯형 고대어 단어 (1구 원소, 2구 형태, 3구 기동, 수식어 등)
  * [고대어 한글 발음 표기 원칙]: 모든 고대어 어휘는 영문 알파벳(barre, motus 등)이 아닌 자연스러운 한국어 한글 발음과 역할 설명(예: '바르(발화/열에너지)', '카르(강제/물리운동)', '이그니스(화염)')으로 100% 표기
  * 플레이어 초기 `known_magic_words` 역시 위 한글 발음 형식의 고대어 단어 2~3개 부여
  * 도서관/서적 아이템(`document_text`)에도 미지의 고대어를 배울 수 있는 힌트와 지식을 자연스럽게 수록
- 칭호: NPC 중 1~2명은 칭호(title) 보유

[필수 출력 JSON 규격]
아래 구조를 정확히 따르십시오:

{world_template}

위 예시의 구조만 참고하되, 이름/장소/스토리/아이템/스킬/칭호를 완전히 새롭게 창조하십시오.
"""


DYNAMIC_REGION_SYSTEM_PROMPT = """
당신은 판타지 TRPG의 지역 설계자입니다.
기존 세계관의 설정과 현재 플레이어의 상황에 부합하는 새로운 지역(Location) 1개를 JSON으로 설계하십시오.
반드시 제공된 [RAG 검색된 지역 템플릿]의 독창적인 환경 기믹과 5단계 심층 요소를 창의적으로 녹여내십시오.
모든 플레이어 텍스트는 몰입감 높은 한국어로 작성하십시오.
"""

DYNAMIC_REGION_PROMPT = """
현재 세계관에 새롭게 편입될 미지의 신규 지역 1개를 JSON으로 설계하십시오.

[현재 세계관 정보]
- 세계 이름: {world_name}
- 거시 장르: {world_genre}
- 현재 플레이어 위치: {current_location}

[RAG 검색된 지역 테마 템플릿 (영감 레퍼런스)]:
- 템플릿 이름: {template_name}
- 환경 묘사: {template_env}
- 형성 기원: {template_origin}
- 핵심 기믹 & 위험: {template_gimmick} | {template_hazard}
- 숨겨진 반전: {template_twist}

[필수 출력 JSON 규격]:
{{
  "id": "new_location_id",
  "name": "새로운 지역 한국어 이름",
  "description": "지역의 시각적·공간적 묘사 (2~3문장)",
  "environmental_hazards": ["환경 위험 요소 1", "환경 위험 요소 2"],
  "exits": {{"돌아가기": "{current_location}"}},
  "items": [],
  "npcs": [],
  "is_point_of_no_return": false,
  "hidden_twist": "이 지역의 비밀",
  "ticking_clock": "환경적 붕괴 압박"
}}
"""


class WorldGenerator:
    def __init__(self, llm, memory_manager=None):
        self._llm = llm
        self._memory = memory_manager

    def generate_new_world(self, chosen_intro_key: Optional[str] = None) -> tuple[dict, str]:
        """
        Generate a completely fresh world via LLM with a fantasy continent base and diverse regional inspirations.
        Uses Qdrant Vector RAG if memory_manager is available, otherwise falls back to random sampling.
        Returns (world_data_dict, intro_key).
        """
        if not chosen_intro_key or chosen_intro_key not in INTRO_STRUCTURES:
            chosen_intro_key = random.choice(list(INTRO_STRUCTURES.keys()))

        intro_info = INTRO_STRUCTURES[chosen_intro_key]
        world_genre = random.choice(FANTASY_WORLD_GENRES)

        # Retrieve 3-4 regional inspirations via Qdrant RAG or fallback
        sample_inspirations = []
        if self._memory:
            try:
                rag_query = f"{world_genre} {intro_info['title']}"
                rag_results = self._memory.search_region_templates(rag_query, limit=4)
                if rag_results:
                    sample_inspirations = rag_results
            except Exception as e:
                logger.warning(f"RAG search_region_templates failed, falling back to random: {e}")

        if not sample_inspirations:
            sample_inspirations = random.sample(REGION_THEME_INSPIRATIONS, min(4, len(REGION_THEME_INSPIRATIONS)))

        inspiration_lines = []
        for i, reg in enumerate(sample_inspirations, 1):
            elems = ", ".join(reg.get("elements", [])[:3]) if "elements" in reg else reg.get("environment", "")[:40]
            inspiration_lines.append(f"- 예시 {i} [{reg.get('name', '')}]: {elems}")
        region_inspiration_text = "\n".join(inspiration_lines)

        # Retrieve Arcane Physics, Realism Mechanics, and Monster inspirations via Qdrant RAG or fallback
        sample_arcane = []
        sample_realism = []
        sample_monsters = []
        if self._memory:
            try:
                sample_arcane = self._memory.search_arcane_templates(rag_query, limit=3)
                sample_realism = self._memory.search_realism_templates(rag_query, limit=3)
                sample_monsters = self._memory.search_monster_templates(rag_query, limit=3)
            except Exception as e:
                logger.warning(f"RAG search for templates failed: {e}")

        if not sample_arcane:
            arcane_path = TEMPLATES_DIR / 'arcane_physics_template.json'
            if arcane_path.exists():
                try:
                    with open(arcane_path, 'r', encoding='utf-8') as f:
                        all_a = json.load(f)
                        sample_arcane = random.sample(all_a, min(3, len(all_a)))
                except Exception:
                    pass

        if not sample_realism:
            realism_path = TEMPLATES_DIR / 'realism_mechanics_template.json'
            if realism_path.exists():
                try:
                    with open(realism_path, 'r', encoding='utf-8') as f:
                        all_r = json.load(f)
                        sample_realism = random.sample(all_r, min(3, len(all_r)))
                except Exception:
                    pass

        arcane_lines = [f"- [{a.get('name', '')}]: {' / '.join(a.get('symptoms', [])[:2])}" for a in sample_arcane]
        arcane_laws_text = "\n".join(arcane_lines) if arcane_lines else "특이 법칙 없음"

        realism_lines = [f"- [{r.get('name', '')}]: {r.get('core_principle', '')}" for r in sample_realism]
        realism_laws_text = "\n".join(realism_lines) if realism_lines else "기본 물리 법칙 적용"

        monster_lines = [f"- [{m.get('tier', 'elite').upper()} {m.get('name', '')}]: {m.get('concept_theme', '')} (약점: {m.get('weakness_exploit', '')[:80]}...)" for m in sample_monsters]
        monster_inspiration_text = "\n".join(monster_lines) if monster_lines else "표준 기믹 몬스터"

        # Infinite Variety: Procedurally assemble a completely unique world from our 30+ region templates
        # 1. Tier 1: Planet Cosmology & World Lore Selection
        cosmology_path = TEMPLATES_DIR / 'cosmology_templates.json'
        cosmology_pool = []
        if cosmology_path.exists():
            try:
                with open(cosmology_path, 'r', encoding='utf-8') as f:
                    cosmology_pool = json.load(f)
            except Exception:
                pass

        if cosmology_pool:
            chosen_cosmology = random.choice(cosmology_pool)
        else:
            chosen_cosmology = {
                "id": "cosmology_terra_arcana",
                "world_name": "테라 아르카나 (Terra Arcana)",
                "genre": "정통 하이 판타지",
                "era_background": "고대 마도 제국 멸망 후 300년이 흐른 중세 판타지 시대.",
                "continents": [{
                    "continent_name": "아발론 제국과 북부 칼날산맥",
                    "description": "은빛 성기사단과 마탑 연합이 다스리는 광활한 제국령과 험준한 산악 변경 지대",
                    "starter_settlement": {
                        "id": "start_settlement_01",
                        "name": "갈까마귀 횃불 선술집과 국경 전초기지",
                        "description": "두꺼운 참나무 기둥과 타오르는 벽난로가 있는 아늑한 국경 선술집이다. 모험가 길드의 의뢰 벽보가 붙어있고, 바텐더와 무장한 용병들이 난롯가에 모여 술잔을 기울이고 있다.",
                        "starter_job": "선술집 바텐더",
                        "starter_npc_name": "바란"
                    }
                }]
            }

        world_name = chosen_cosmology.get("world_name", "테라 아르카나")
        world_genre = chosen_cosmology.get("genre", "정통 하이 판타지")
        continents = chosen_cosmology.get("continents", [])
        chosen_continent = random.choice(continents) if continents else {}
        continent_name = chosen_continent.get("continent_name", "아발론 제국 변경령")
        # Diverse starter origins pool (Noble Mansion, Cathedral, Mage Tower, Fortress, Expedition Camp, Ship, Hideout, Hunter Lodge)
        STARTER_ORIGINS_POOL = [
            {
                "name": "고대 명문 가문의 대저택 집무실",
                "description": "고풍스러운 샹들리에와 융단이 깔린 가문의 집무실이다. 벽난로의 불꽃이 벽면의 초상화들을 비추고 있으며, 책상 위에는 가문의 존망이 걸린 비밀 서신과 봉인된 칙령이 놓여 있다.",
                "starter_job": "가문의 늙은 수석 집사",
                "starter_npc_name": "알프레드 (Alfred)"
            },
            {
                "name": "대성당 성유물 수호 기도실",
                "description": "은은한 촛불과 백리향 향로 연기가 피어오르는 엄숙한 석조 기도실이다. 스테인드글라스 너머로 은백색 달빛이 쏟아져 내리며, 제단 위에는 봉인된 성스러운 룬 석판이 놓여 있다.",
                "starter_job": "성소의 맹인 고위 사제",
                "starter_npc_name": "엘레나 (Elena)"
            },
            {
                "name": "마탑 최상층 천문 관측 서재",
                "description": "수천 권의 마도서와 회전하는 기계식 천구의가 가득한 비전 서재다. 거대한 천문 망원경 너머로 대기 중의 마나 폭풍이 푸른 번갯불처럼 번뜩이고 있다.",
                "starter_job": "수석 마도 점성학자",
                "starter_npc_name": "알버스 (Albus)"
            },
            {
                "name": "국경 요새 성벽 최상층 망루",
                "description": "차가운 칼바람이 몰아치는 깎아지른 절벽 위 요새 망루다. 망원경과 신호용 횃불 바구니가 놓여 있으며, 발아래로는 안개에 덮인 미지의 황무지가 끝없이 펼쳐져 있다.",
                "starter_job": "흉터투성이 국경 보초대장",
                "starter_npc_name": "가릭 (Garik)"
            },
            {
                "name": "고대 유적 발굴단 야간 전진 캠프",
                "description": "거대한 크레이터 유적지 틈새에 세워진 두꺼운 방수 텐트 안이다. 흙 묻은 고대 석판 조각과 측량 도구, 램프 불빛 아래로 발굴 대원들의 긴장된 숨소리가 들려온다.",
                "starter_job": "외눈박이 수석 발굴단장",
                "starter_npc_name": "브론 (Bron)"
            },
            {
                "name": "외해 탐사 범선의 조타실 및 갑판",
                "description": "거친 파도를 가르며 삐걱거리는 대형 목조 범선의 조타실이다. 탁자 위에는 낡은 해도와 떨리는 황동 나침반이 놓여 있고, 갑판 너머로 짙은 해무가 밀려오고 있다.",
                "starter_job": "파이프 담배를 문 노련한 조타수",
                "starter_npc_name": "마틴 (Martin)"
            },
            {
                "name": "도시 지하 수로망의 비밀 은신처",
                "description": "어두운 하수도 틈새를 개조해 만든 은밀한 도적 연합의 아지트다. 눅눅한 이끼 냄새와 무기를 손질하는 숫돌 소리가 울리며, 탁자 위에는 누군가의 현상금 수배지가 꽂혀 있다.",
                "starter_job": "후드를 깊게 눌러쓴 정보상",
                "starter_npc_name": "까마귀 잭 (Crow Jack)"
            },
            {
                "name": "안개 숲 사냥꾼의 튼튼한 통나무 산장",
                "description": "거대한 고대 원시림 깊은 곳에 지어진 견고한 사냥꾼 오두막이다. 타오르는 장작 난로와 벽에 걸린 맹수 모피들, 그리고 손질된 장궁과 화살촉이 든든한 분위기를 풍긴다.",
                "starter_job": "과묵한 늙은 늑대 사냥꾼",
                "starter_npc_name": "요른 (Jorn)"
            }
        ]

        # Pick continent starter or fallback to diverse origins
        cosmo_starter = chosen_continent.get("starter_settlement")
        if cosmo_starter and isinstance(cosmo_starter, dict):
            starter_settlement = cosmo_starter
        else:
            starter_settlement = random.choice(STARTER_ORIGINS_POOL)

        # 2. Tier 2 & 3: Locations Assembly [1. Starter Settlement + 2~4. Outer Dungeons]
        region_templates_path = TEMPLATES_DIR / 'region_templates.json'
        region_pool = []
        if region_templates_path.exists():
            try:
                with open(region_templates_path, 'r', encoding='utf-8') as f:
                    region_pool = json.load(f)
            except Exception:
                pass

        chosen_dungeons = random.sample(region_pool, min(3, len(region_pool))) if region_pool else []
        
        locations_dict = {}
        
        # Loc 1: Guaranteed Safe/Cozy Starter Village / Tavern
        start_loc_id = "loc_1"
        locations_dict[start_loc_id] = {
            "id": start_loc_id,
            "name": starter_settlement.get("name", "국경 선술집과 전초기지"),
            "description": starter_settlement.get("description", "따스한 모닥불과 모험가들이 머무는 안전한 전초기지다."),
            "exits": {},
            "items": [],
            "npcs": [],
            "danger_level": 1
        }

        # Loc 2~4: Outer Wilderness & Exploration Dungeons
        for idx, reg in enumerate(chosen_dungeons):
            loc_id = f"loc_{idx+2}"
            desc_obj = reg.get("description", {})
            if isinstance(desc_obj, dict):
                desc_text = f"{desc_obj.get('visual', '')} {desc_obj.get('auditory', '')}".strip()
            else:
                desc_text = str(desc_obj)
            
            locations_dict[loc_id] = {
                "id": loc_id,
                "name": reg.get("name", f"미지의 탐험 구역 {idx+2}"),
                "description": desc_text or "기이한 안개와 마력이 소용돌이치는 미지의 외곽 장소다.",
                "exits": {},
                "items": [],
                "npcs": [],
                "danger_level": idx + 2
            }

        # Connect Exits: loc_1 (Tavern) -> loc_2 (Wilderness) -> loc_3 (Ruins) -> loc_4 (Dungeon)
        loc_ids = list(locations_dict.keys())
        for i in range(len(loc_ids) - 1):
            cur_id = loc_ids[i]
            next_id = loc_ids[i+1]
            locations_dict[cur_id]["exits"]["north"] = next_id
            locations_dict[next_id]["exits"]["south"] = cur_id
        if len(loc_ids) >= 3:
            locations_dict[loc_ids[0]]["exits"]["east"] = loc_ids[2]
            locations_dict[loc_ids[2]]["exits"]["west"] = loc_ids[0]

        # Dynamic NPC generation based on start location with rich 5-factor psychology
        NPC_NAMES = ["엘릭", "바란", "카엘", "레니아", "모르건", "실비아", "타르코", "이리나", "다렌", "벨라", "로웨나", "발타자르"]
        NPC_JOBS = ["방랑 탐험가", "은둔 마도학자", "지역 길드 정보상", "퇴역 베테랑 용병", "약초 연금술사", "신전 파계승", "선술집 바텐더", "암시장 장물아비"]
        
        NPC_DESIRES = [
            "병든 여동생의 치료비 300골드를 모아 안전한 곳으로 이주하는 것",
            "빼앗긴 가문의 명예와 가보 검을 되찾는 것",
            "이 저주받은 위험 지대에서 무사히 탈출하여 자유를 얻는 것",
            "고대 금지된 마도서의 잃어버린 페이지를 손에 넣는 것",
            "자신을 배신하고 누명을 씌운 옛 상관에게 복수하는 것",
            "굶주림과 빚에서 벗어나 안전한 은신처를 마련하는 것",
            "대륙 최고의 연금술사로 인정받아 길드를 재건하는 것"
        ]
        NPC_WEAKNESSES = [
            "값비싼 귀금속이나 고액의 골드(돈) 제안에 쉽게 이성을 잃음",
            "가족이나 소중한 사람의 안위가 걸리면 극도로 동요함",
            "독한 술을 대접받으면 경계심이 풀리고 비밀을 술술 털어놓음",
            "자존심이 너무 강해 진심 어린 찬사와 아부에 쉽게 낚임",
            "신체 한쪽에 씻을 수 없는 오래된 관절 부상(오른쪽 무릎)",
            "희귀한 고대 유물이나 지식에 대한 맹목적인 탐욕"
        ]
        NPC_TABOOS = [
            "가족이나 부모를 모욕하면 즉시 칼을 뽑고 적대화됨",
            "자신의 신앙과 신성한 맹세를 모독하는 행위 절대 용납 불가",
            "동료를 배신하거나 약자를 괴롭히는 비열한 짓 극도로 혐오",
            "과거 실패했던 뼈아픈 실수를 비웃거나 조롱하는 것"
        ]
        NPC_TRAUMAS = [
            "과거 대화재로 동료들이 불타 죽은 기억 (화염 공포증)",
            "지하 동굴에 홀로 고립되어 굶주렸던 기억 (폐쇄공간 공포)",
            "믿었던 동료의 독침 배신으로 전멸했던 악몽 (타인 불신)"
        ]
        NPC_SECRETS = [
            "사실 지역 길드의 공금을 횡령하고 숨어든 지명수배자임",
            "과거 적대 마도 결사의 첩자로 일했던 어두운 과거",
            "소지한 부적이 사실 저주받은 피의 마법 아티팩트임"
        ]

        # Use starter settlement's NPC info if available
        starter_npc_name = starter_settlement.get("starter_npc_name")
        starter_npc_job = starter_settlement.get("starter_job")

        npc_name_1 = starter_npc_name if starter_npc_name else random.choice(NPC_NAMES)
        npc_job_1 = starter_npc_job if starter_npc_job else random.choice(NPC_JOBS)
        
        from src.world.event_perspective import EventPerspectiveEngine

        raw_npc_guide = {
            "id": "npc_guide_1",
            "name": f"{npc_name_1}" if (" " in str(npc_name_1) or "(" in str(npc_name_1)) else f"{npc_job_1} {npc_name_1}",
            "description": f"풍파를 겪은 눈빛과 낡은 장비를 갖춘 {npc_job_1}다. 현장의 분위기를 주시하고 있다.",
            "location": start_loc_id,
            "job": npc_job_1,
            "disposition": "neutral",
            "attitude_description": "신중하며 경계심이 강함",
            "desire": random.choice(NPC_DESIRES),
            "weakness": random.choice(NPC_WEAKNESSES),
            "taboo": random.choice(NPC_TABOOS),
            "trauma": random.choice(NPC_TRAUMAS),
            "blackmail_secret": random.choice(NPC_SECRETS),
            "affinity": 50,
            "fear": 0,
            "debt": 0,
            "alive": True,
            "health": 60,
            "max_health": 60,
            "mana": 40,
            "max_mana": 40,
            "armor_class": 12,
            "inventory": [],
            "memories": [],
            "beliefs": []
        }
        
        # Inject 12-axis perspective beliefs based on NPC traits & chosen cosmology
        raw_npc_guide["beliefs"] = EventPerspectiveEngine.generate_event_beliefs(raw_npc_guide, chosen_cosmology)

        npcs_dict = {
            "npc_guide_1": raw_npc_guide
        }
        locations_dict[start_loc_id]["npcs"].append("npc_guide_1")

        # Dynamic Starter Items
        starter_items_pool = [
            {"id": "iron_dagger", "name": "손질된 단검", "description": "날이 예리하게 선 강철 단검이다.", "location": "inventory", "item_type": "weapon", "damage": 8, "defense": 0, "value": 20, "scaling_stat": "agility", "scaling_factor": 1.2, "properties": {"weapon": True}},
            {"id": "travel_journal", "name": "낡은 여행 일지", "description": "이 대륙의 위험한 지형과 생물에 대해 조잡하게 기록된 가죽 표지의 일지다.", "location": "inventory", "item_type": "misc", "damage": 0, "defense": 0, "value": 5, "scaling_stat": "int", "scaling_factor": 1.0, "properties": {"readable": True}},
            {"id": "mana_dust", "name": "발광 마나 수정 가루", "description": "어둠 속에서 은은한 푸른빛을 발산하는 응축된 마나 수정 가루 주머니다.", "location": "inventory", "item_type": "consumable", "damage": 0, "defense": 0, "value": 30, "scaling_stat": "int", "scaling_factor": 1.0, "properties": {"glow": True}}
        ]
        
        items_dict = {it["id"]: it for it in starter_items_pool}
        player_inventory = [it["id"] for it in starter_items_pool]

        # Assemble Factions from cosmology major nations & continental factions
        factions_dict = {}
        for idx, nat in enumerate(chosen_cosmology.get("major_nations", [])):
            fac_id = f"nation_{idx+1}"
            factions_dict[fac_id] = {
                "id": fac_id,
                "name": nat.get("nation_name", f"주요 국가 {idx+1}"),
                "system": nat.get("system", "국가"),
                "power_level": "주요 국가",
                "ruling_race": "인간",
                "taboos": [],
                "relations": {"외교": nat.get("relations", "중립")},
                "emblem_animal": "사자",
                "flag_colors": ["금색", "진홍색"],
                "flag_symbol": "국가 인장",
                "motto": ""
            }

        for idx, fac in enumerate(chosen_continent.get("factions", [])):
            fac_id = fac.get("id", f"fac_{idx+1}")
            factions_dict[fac_id] = {
                "id": fac_id,
                "name": fac.get("name", f"세력 {idx+1}"),
                "system": "조직",
                "power_level": fac.get("role", "지역 세력"),
                "ruling_race": "혼합",
                "taboos": [],
                "relations": {},
                "emblem_animal": "매",
                "flag_colors": ["은색", "청색"],
                "flag_symbol": "문양",
                "motto": ""
            }

        if not factions_dict:
            factions_dict["continent_explorers"] = {
                "id": "continent_explorers",
                "name": "대륙 개척 탐사대",
                "system": "탐사 연맹",
                "power_level": "지역 개척단",
                "ruling_race": "혼합",
                "taboos": ["유적 훼손", "고대 봉인 무단 해제"],
                "relations": {}
            }

        # Build full cosmology metadata dict
        full_cosmo = dict(chosen_cosmology)
        full_cosmo["arcane_laws"] = sample_arcane

        # World facts summary
        cur_rules = chosen_cosmology.get("currency_and_laws", {})
        official_curr = cur_rules.get("official_currency", "") if isinstance(cur_rules, dict) else ""
        magic_rules = chosen_cosmology.get("magic_rules", {})
        forbidden_mag = magic_rules.get("forbidden_magic", "") if isinstance(magic_rules, dict) else ""

        world_facts_list = [
            f"[행성 세계관] {world_name} ({world_genre})",
            f"[소속 대륙/영토] {continent_name}",
            f"[시대적 배경] {chosen_cosmology.get('era_background', '')}",
            f"[거시적 세계 위협] {chosen_cosmology.get('macro_threat', '')}",
            f"[말소된 역사 미스터리] {chosen_cosmology.get('censored_history', '')}",
        ]
        if official_curr:
            world_facts_list.append(f"[통용 화폐] {official_curr}")
        if forbidden_mag:
            world_facts_list.append(f"[금지 마법] {forbidden_mag}")

        world_data = {
            "session_id": f"world_{uuid.uuid4().hex[:8]}",
            "world_id": f"world_{uuid.uuid4().hex[:8]}",
            "world_name": world_name,
            "world_genre": world_genre,
            "active_world_ended": False,
            "world_chronicle": "",
            "intro_key": chosen_intro_key,
            "player": {
                "name": "방랑자",
                "location": start_loc_id,
                "inventory": player_inventory,
                "health": 100,
                "max_health": 100,
                "mana": 50,
                "max_mana": 50,
                "level": 1,
                "exp": 0,
                "gold": 30,
                "stat_points": 0,
                "strength": 12,
                "agility": 10,
                "intelligence": 10,
                "constitution": 12,
                "wisdom": 10,
                "luck": 10,
                "crit_rate_bonus": 0,
                "crit_damage_bonus": 0,
                "reputation": 0,
                "equipment": {
                    "weapon": None, "head": None, "face": None, "chest": None,
                    "legs": None, "boots": None, "gloves": None, "cape": None,
                    "rings": [], "earrings": []
                },
                "skills": [],
                "titles": [],
                "active_title": None,
                "known_magic_words": ["바르", "카르", "이그니스"],
                "known_facts": []
            },
            "locations": locations_dict,
            "npcs": npcs_dict,
            "items": items_dict,
            "factions": factions_dict,
            "quests": {},
            "shops": {},
            "skills_db": {
                sid: {k: v for k, v in sk.__dict__.items()}
                for sid, sk in SkillSystem.load_skill_templates().items()
            } if hasattr(SkillSystem, "load_skill_templates") else {},
            "titles_db": {},
            "cosmology_template": full_cosmo,
            "world_lore": full_cosmo,
            "history": [],
            "world_facts": world_facts_list
        }

        return world_data, chosen_intro_key

    def generate_dynamic_region(self, state, target_theme_query: str) -> Optional[dict]:
        """
        Dynamically generate a new region using Qdrant RAG template search and attach to state.
        Returns the created Location dictionary.
        """
        template_payload = None
        if self._memory:
            try:
                results = self._memory.search_region_templates(target_theme_query, limit=1)
                if results:
                    template_payload = results[0]
            except Exception as e:
                logger.warning(f"RAG search for dynamic region failed: {e}")

        if not template_payload:
            template_payload = random.choice(REGION_THEME_INSPIRATIONS)

        prompt = DYNAMIC_REGION_PROMPT.format(
            world_name=state.world_name,
            world_genre=getattr(state, "world_genre", "정통 판타지"),
            current_location=state.player.location,
            template_name=template_payload.get("name", "미지의 영지"),
            template_env=template_payload.get("environment", "신비로운 판타지 지대"),
            template_origin=template_payload.get("origin_event", "고대의 마법적 사건"),
            template_gimmick=template_payload.get("environmental_gimmicks", "특수 물리 법칙"),
            template_hazard=template_payload.get("survival_hazards", "환경 오염"),
            template_twist=template_payload.get("hidden_twist", "숨겨진 진실")
        )

        try:
            raw = self._llm.generate_json(prompt, DYNAMIC_REGION_SYSTEM_PROMPT)
            loc_data = json.loads(raw)
            return loc_data
        except Exception as e:
            logger.error(f"Dynamic region generation failed: {e}")
            return None




