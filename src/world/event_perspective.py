"""
Event Perspective Engine for Quilltale TRPG Engine.
Implements the 12-Axis Hyper-Realistic Perspective Matrix.
Enables NPCs to perceive, remember, and interpret world historical events differently
based on their Social Class, Gender/Family Role, Education, Wealth/Debt, Health, Race,
Ideology, Profession, Geographic Proximity, Generation, Stakeholder Nexus, and Info Veracity.
"""
from typing import Dict, List, Any, Optional
import random


class EventPerspectiveEngine:
    """Resolves and extracts personalized historical event beliefs for NPCs based on the 12-axis matrix."""

    @staticmethod
    def extract_npc_traits(npc_dict: dict) -> dict:
        """Extracts standard traits from an NPC dictionary or object for 12-axis matching."""
        vis = npc_dict.get("visual", {})
        if not isinstance(vis, dict):
            vis = {}

        species = str(vis.get("species", "인간")).strip()
        gender = str(vis.get("gender", "남성")).strip()
        job = str(npc_dict.get("job", "방랑자")).strip()
        tier = str(npc_dict.get("tier", "commoner")).strip()
        edu = str(npc_dict.get("education_level", "보통")).strip()
        fin = str(npc_dict.get("financial_state", "보통")).strip()
        trauma = str(npc_dict.get("trauma", "")).strip()
        phys = str(npc_dict.get("physical_condition", "")).strip()

        # Classify social class
        social_class = "소시민_자영농"
        if tier == "legend" or "귀족" in job or "영주" in job or "국왕" in job:
            social_class = "지배귀족_영주"
        elif "기사" in job or "몰락" in job:
            social_class = "몰락귀족_기사"
        elif "상인" in job or "부유" in fin or "전주" in job:
            social_class = "부유상인_자본가"
        elif "노예" in job or "빈민" in job or "농노" in job or "거지" in job:
            social_class = "농노_빈민_노예"
        elif "도적" in job or "밀수" in job or "암살" in job:
            social_class = "추방자_범죄자"

        # Classify race
        race_cat = "순혈_인간"
        if "엘프" in species:
            race_cat = "장수종_엘프"
        elif "드워프" in species:
            race_cat = "장인종_드워프"
        elif "수인" in species or "노움" in species or "하프링" in species:
            race_cat = "소형종_수인"
        elif "오크" in species or "고블린" in species:
            race_cat = "차별받는_아인종"
        elif "하프" in species or "티플링" in species:
            race_cat = "이계_혼혈_잡종"

        # Classify gender/family role
        gender_role = "생존_수호_여성" if "여" in gender else "징집_부양_남성"

        # Classify literacy
        lit_cat = "실무_문해자_서기"
        if "학자" in job or "마법" in job or "아카데미" in edu or "고등" in edu:
            lit_cat = "고등_아카데미_학자"
        elif "문맹" in edu or "무지" in edu or "노예" in job:
            lit_cat = "완전_문맹_무지자"

        return {
            "social_class": social_class,
            "race_cat": race_cat,
            "gender_role": gender_role,
            "literacy": lit_cat,
            "job": job,
            "fin": fin,
            "trauma": trauma,
            "phys": phys
        }

    @classmethod
    def generate_event_beliefs(cls, npc_dict: dict, cosmology: dict) -> List[str]:
        """
        Generates 2~4 rich, biased perspective statements for the NPC regarding
        the world's cataclysm/history based on the 12-axis matrix.
        """
        traits = cls.extract_npc_traits(npc_dict)
        beliefs = list(npc_dict.get("beliefs", []))

        historical_events = cosmology.get("historical_events", [])
        
        # If no explicit historical_events defined in template, synthesize from era_background & censored_history
        if not historical_events:
            era_bg = cosmology.get("era_background", "")
            censored = cosmology.get("censored_history", "")
            historical_events = [
                {
                    "event_name": f"{cosmology.get('world_name', '제국')}의 대참사와 역사 말소",
                    "summary": era_bg[:150] if era_bg else "고대 제국의 대참사와 말소된 역사",
                    "perspectives": cls._generate_default_perspectives(cosmology)
                }
            ]

        for ev in historical_events:
            ev_name = ev.get("event_name", "역사적 사건")
            perspectives = ev.get("perspectives", {})

            # 1. Match Social Class
            p_class = perspectives.get("1_신분_계급", {})
            class_stmt = p_class.get(traits["social_class"])
            if not class_stmt:
                class_stmt = next(iter(p_class.values())) if p_class else None
            if class_stmt:
                beliefs.append(f"[{ev_name}에 대한 생각 - {traits['social_class']} 입장]: {class_stmt}")

            # 2. Match Race / Lineage
            p_race = perspectives.get("6_종족_혈통", {})
            race_stmt = p_race.get(traits["race_cat"])
            if not race_stmt:
                race_stmt = next(iter(p_race.values())) if p_race else None
            if race_stmt:
                beliefs.append(f"[{ev_name}에 대한 생각 - {traits['race_cat']} 입장]: {race_stmt}")

            # 3. Match Gender / Family Role
            p_gender = perspectives.get("2_성별_가족역할", {})
            gender_stmt = p_gender.get(traits["gender_role"])
            if gender_stmt:
                beliefs.append(f"[{ev_name}에 대한 생각 - {traits['gender_role']} 입장]: {gender_stmt}")

            # 4. Match Literacy / Info Veracity
            p_edu = perspectives.get("3_학력_문해력", {})
            edu_stmt = p_edu.get(traits["literacy"])
            if edu_stmt:
                beliefs.append(f"[{ev_name}에 대한 생각 - {traits['literacy']} 시각]: {edu_stmt}")

        return list(dict.fromkeys(beliefs))

    @staticmethod
    def _generate_default_perspectives(cosmology: dict) -> dict:
        """Generates dynamic 12-axis perspectives for a cosmology based on its metadata."""
        w_name = cosmology.get("world_name", "대륙")
        era_bg = cosmology.get("era_background", "")
        censored = cosmology.get("censored_history", "")
        
        return {
            "1_신분_계급": {
                "지배귀족_영주": f"옛 제국의 영광을 복원하고 가문의 권세를 드높일 기회로 여김.",
                "몰락귀족_기사": f"가문의 가보와 영지를 잃고 방랑하게 된 뼈아픈 과거로 기억함.",
                "부유상인_자본가": f"혼란과 폐허 속에서 진귀한 유물과 이권을 독점할 막대한 기회로 봄.",
                "소시민_자영농": f"전쟁과 세금 폭등으로 하루 벌어 하루 먹고살기 벅찬 고통스러운 시대로 여김.",
                "농노_빈민_노예": f"오만한 지배자들이 천벌을 받아 몰락한 것을 속으로 통쾌해함.",
                "추방자_범죄자": f"치안이 무너진 틈을 타 암시장과 약탈로 한밑천 잡을 무법의 시대로 봄."
            },
            "2_성별_가족역할": {
                "징집_부양_남성": f"군대에 끌려가 개죽음당하거나 빚을 갚기 위해 칼을 쥐어야 했던 서러운 한을 품음.",
                "생존_수호_여성": f"약탈과 혼란 속에서 아이들을 먹여 살리기 위해 온갖 수모를 견뎌낸 피눈물로 기억함."
            },
            "3_학력_문해력": {
                "고등_아카데미_학자": f"마나 순환의 구조적 파탄과 제어 실패가 부른 필연적 마도공학 참사로 냉철히 분석함.",
                "실무_문해자_서기": f"지배층의 기록 조작과 역사 은폐 정황을 의심의 눈초리로 주시함.",
                "완전_문맹_무지자": f"교단의 설교대로 신의 천벌이나 사악한 마녀의 저주 때문이라 굳게 믿음."
            },
            "6_종족_혈통": {
                "순혈_인간": f"인류의 찬란했던 번영이 꺾인 불운한 비극으로 애통해함.",
                "장수종_엘프": f"인간들이 자연의 질서를 무시하고 마나를 탐욕스럽게 착취하다 자멸한 자업자득으로 여김.",
                "장인종_드워프": f"자신들이 벼려준 룬과 성벽의 은혜를 저버리고 내부에서 자폭한 어리석음으로 치부함.",
                "소형종_수인": f"거대 제국들의 충돌에 등 터져 고향을 잃고 흩어져야 했던 설움으로 기억함.",
                "차별받는_아인종": f"인간 지배자들의 군대가 무너졌으니 이제 자신들의 땅을 되찾을 기회로 봄.",
                "이계_혼혈_잡종": f"차원의 균열 속에서 태어나 차별받게 된 원죄의 날로 고뇌함."
            }
        }
