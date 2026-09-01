"""
Living Physics & Chemistry Matrix Engine for Quilltale TRPG Engine.
Replaces vector embedding lookups with fast deterministic Python keyword & tag matching.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class PhysicsReactionResult:
    rule_id: str
    result_name: str
    description: str
    damage_bonus: float = 1.0
    tag: str = ""
    status_to_apply: Optional[str] = None  # e.g., "burn", "freeze", "corrosion"
    status_duration: int = 0
    status_potency: int = 0

    @property
    def description_ko(self) -> str:
        return self.description


# Deterministic Matrix of Fundamental Physical & Chemical Laws
PHYSICS_RULES: List[Dict[str, Any]] = [
    {
        "rule_id": "acid_mineral_corrosion",
        "source_keys": ["산성", "소화액", "부식", "강산", "acid"],
        "target_keys": ["광물", "흑요석", "키틴질", "철", "강철", "방어구", "갑옷", "거인", "골렘", "방패"],
        "result_name": "화학적 산성 용해 (Corrosive Melt)",
        "description": "강산성 화학 반응으로 대상의 표면 장갑과 외골격이 급속도로 녹아내려 방어력이 무력화됩니다.",
        "damage_bonus": 1.5,
        "tag": "방어구 파괴",
        "status_to_apply": "corrosion",
        "status_duration": 3,
        "status_potency": 3,
    },
    {
        "rule_id": "thermal_shock_shatter",
        "source_keys": ["극저온", "빙결", "냉기", "글라키에", "cold", "frost", "얼음"],
        "target_keys": ["용암", "마그마", "고열", "흑요석", "유리", "가마", "백자", "화염"],
        "result_name": "열충격 급랭 파쇄 (Thermal Shock)",
        "description": "초고열 상태의 물체에 극저온 냉기가 닿아 급격한 부피 수축으로 내부 응력이 폭주하여 산산조각 납니다.",
        "damage_bonus": 2.0,
        "tag": "열충격 분쇄",
        "status_to_apply": "shattered",
        "status_duration": 2,
        "status_potency": 5,
    },
    {
        "rule_id": "superconductive_discharge",
        "source_keys": ["번개", "전기", "전류", "풀구르", "lightning", "낙뢰"],
        "target_keys": ["수은", "초전도", "전류신경", "액체금속", "물", "습지", "수류", "아쿠아"],
        "result_name": "초전도 광역 방전 (Area Discharge)",
        "description": "액체 도체 및 전도성 매질을 타고 고전압 전류가 순간적으로 확산되어 범위 내 모든 대상에게 치명적인 감전 마비를 일으킵니다.",
        "damage_bonus": 1.6,
        "tag": "광역 감전",
        "status_to_apply": "paralysis",
        "status_duration": 2,
        "status_potency": 4,
    },
    {
        "rule_id": "methane_chain_explosion",
        "source_keys": ["화염", "불꽃", "이그니스", "폭발", "fire", "불"],
        "target_keys": ["메탄", "인화성 가스", "늪지", "부패가스", "유황가스", "기름", "오일", "알코올"],
        "result_name": "유기물 연쇄 기화 폭발 (Chain Explosion)",
        "description": "인화성 가스와 기름 층에 불꽃이 닿아 산소가 급격히 연소하며 대규모 연쇄 폭발을 일으키고 지형을 불태웁니다.",
        "damage_bonus": 2.2,
        "tag": "지형 연쇄 폭발",
        "status_to_apply": "burn",
        "status_duration": 3,
        "status_potency": 8,
    },
    {
        "rule_id": "resonance_frequency_shatter",
        "source_keys": ["음파", "진동", "공진", "소리굽쇠", "sound", "vibration"],
        "target_keys": ["유리", "거울", "백자", "도자기", "결정체", "수정", "수정체"],
        "result_name": "고유 진동수 공진 파쇄 (Frequency Shatter)",
        "description": "물체의 고유 진동수와 일치하는 강력한 음파 파동이 취성(Brittle) 구조를 내부에서부터 공명 분쇄합니다.",
        "damage_bonus": 1.8,
        "tag": "공진 분쇄",
        "status_to_apply": "stun",
        "status_duration": 1,
        "status_potency": 0,
    },
    {
        "rule_id": "ceramic_complete_insulation",
        "source_keys": ["번개", "전기", "감전", "풀구르"],
        "target_keys": ["백자", "도자기", "절연", "점토", "고무"],
        "result_name": "완전 절연 차단 (Complete Insulation)",
        "description": "도자기 및 백자 유약 코팅 층이 전하의 흐름을 100% 차단하여 전기 피해를 완전 무효화합니다.",
        "damage_bonus": 0.0,
        "tag": "전기 면역",
        "status_to_apply": None,
        "status_duration": 0,
        "status_potency": 0,
    },
    {
        "rule_id": "wax_rapid_melting",
        "source_keys": ["화염", "열기", "고열", "이그니스", "불"],
        "target_keys": ["밀랍", "양초", "심지", "봉랍"],
        "result_name": "밀랍 급속 융해 및 봉인 해제 (Rapid Melting)",
        "description": "밀랍 구조물이 고열에 녹아내려 굳어있던 대상을 해방하거나 통로가 개방됩니다.",
        "damage_bonus": 1.4,
        "tag": "밀랍 융해",
        "status_to_apply": None,
        "status_duration": 0,
        "status_potency": 0,
    },
    {
        "rule_id": "mercury_freeze_solid",
        "source_keys": ["빙결", "극저온", "냉기", "글라키에", "얼음"],
        "target_keys": ["수은", "액체금속"],
        "result_name": "수은 동결 경화 (Mercury Solidification)",
        "description": "영하 38.8도 이하로 냉각된 수은이 단단한 고체 금속으로 굳어 유동성을 잃고 발판이나 무기로 변합니다.",
        "damage_bonus": 1.3,
        "tag": "유체 고체화",
        "status_to_apply": "freeze",
        "status_duration": 2,
        "status_potency": 3,
    },
    {
        "rule_id": "prism_refraction_split",
        "source_keys": ["빛", "광선", "룩스", "light", "laser"],
        "target_keys": ["프리즘", "거울", "분광", "유리", "수정"],
        "result_name": "프리즘 분광 굴절 (Spectral Refraction)",
        "description": "단일 광선이 열선(적외선)과 냉선(자외선)으로 갈라져 다중 속성 파동으로 증폭 확산됩니다.",
        "damage_bonus": 1.7,
        "tag": "분광 증폭",
        "status_to_apply": "blind",
        "status_duration": 2,
        "status_potency": 0,
    },
    {
        "rule_id": "water_ink_dissolution",
        "source_keys": ["수류", "물", "홍수", "아쿠아"],
        "target_keys": ["먹물", "종이", "활판", "오리가미", "두루마리", "서책"],
        "result_name": "잉크 및 종이 수용성 해체 (Dissolution)",
        "description": "대량의 수류가 잉크와 종이의 결합을 분해하여 활자와 결계를 씻어내고 소멸시킵니다.",
        "damage_bonus": 1.6,
        "tag": "결계 용해",
        "status_to_apply": None,
        "status_duration": 0,
        "status_potency": 0,
    },
    {
        "rule_id": "confined_heat_trap",
        "source_keys": ["화염", "불꽃", "이그니스", "폭발", "화염구", "열기"],
        "target_keys": ["밀폐", "석실", "동굴", "지하", "방", "실내", "감옥", "성채 내부"],
        "result_name": "밀폐 공간 열기 축적 (Heat Trap Exhaustion)",
        "description": "밀폐된 공간에서 빠져나가지 못한 열기가 갇혀 실내 기온이 급상승하여 시전자와 대상 모두 산소 결핍과 열사병에 노출됩니다.",
        "damage_bonus": 1.4,
        "tag": "엔트로피 열사병",
        "status_to_apply": "burn",
        "status_duration": 2,
        "status_potency": 4,
    },
    {
        "rule_id": "kinetic_recoil_strain",
        "source_keys": ["강타", "초중량", "대검", "철퇴", "둔기", "폭쇄", "골렘", "거인", "충격파"],
        "target_keys": ["방패", "가드", "철제 방패", "금속 방패", "막기", "방어"],
        "result_name": "운동 에너지 전이 및 관절 과부하 (Kinetic Recoil Strain)",
        "description": "방패 자체는 파손되지 않으나 막대한 운동 에너지가 사용자의 관절로 전이되어 관절 탈구 및 다음 턴 조작 페널티가 발생합니다.",
        "damage_bonus": 1.3,
        "tag": "관절 탈구 반동",
        "status_to_apply": "fracture",
        "status_duration": 3,
        "status_potency": 2,
    },
    {
        "rule_id": "toxic_gas_settling",
        "source_keys": ["산성", "소화액", "독안개", "부패", "연기", "독"],
        "target_keys": ["바닥", "지면", "저지대", "하수도", "동굴 바닥", "웅덩이"],
        "result_name": "고밀도 독성 가스 침강 (Dense Gas Settling)",
        "description": "반응 후 생성된 무거운 유독 가스가 바닥으로 가라앉아 엎드리거나 넘어진 대상에게 치명적인 호흡기 중독을 일으킵니다.",
        "damage_bonus": 1.5,
        "tag": "저지대 독가스",
        "status_to_apply": "poison",
        "status_duration": 3,
        "status_potency": 5,
    },
    {
        "rule_id": "brittle_overstrain",
        "source_keys": ["극저온", "급랭", "글라키에", "빙결", "냉기", "얼음"],
        "target_keys": ["강철검", "칼날", "창", "금속 무기", "단검", "검"],
        "result_name": "저온 취성 파손 위험 (Low-Temperature Brittleness)",
        "description": "극저온에 노출된 금속 무기는 인성을 잃고 유리처럼 부서지기 쉬운 취성 상태로 변해 강한 타격 시 파손될 위험이 있습니다.",
        "damage_bonus": 1.2,
        "tag": "저온 취성",
        "status_to_apply": None,
        "status_duration": 0,
        "status_potency": 0,
    },
    {
        "rule_id": "mana_overheat_bleed",
        "source_keys": ["과충전", "오버차지", "폭주", "막시무스"],
        "target_keys": ["마나", "체내", "혈관", "마법진", "지팡이"],
        "result_name": "마력 회로 과부하 및 역류 (Mana Circuit Overload)",
        "description": "한계를 초과한 마력 방출로 마도맥이 손상되어 시전자 신체에 내장 출혈과 마나 번을 유발합니다.",
        "damage_bonus": 1.5,
        "tag": "마력 역류",
        "status_to_apply": "bleed",
        "status_duration": 2,
        "status_potency": 4,
    },
]


class PhysicsMatrixEngine:
    """
    High-performance, pure-Python deterministic physics & chemistry matrix.
    Fast keyword matching without vector database calls.
    """

    @classmethod
    def evaluate(
        cls,
        action_text: str,
        environment_text: str = "",
        target_tags: Optional[List[str]] = None,
    ) -> List[PhysicsReactionResult]:
        """
        Matches source action text and target environment/items against physics rules.
        """
        combined_source = action_text.lower()
        combined_target = (environment_text + " " + " ".join(target_tags or [])).lower()
        matched: List[PhysicsReactionResult] = []

        for rule in PHYSICS_RULES:
            # Check source trigger
            source_matched = any(k in combined_source for k in rule["source_keys"])
            if not source_matched:
                continue

            # Check target/environment trigger (or check if target is also in action text)
            target_matched = any(k in combined_target for k in rule["target_keys"]) or any(
                k in combined_source for k in rule["target_keys"]
            )
            if not target_matched:
                continue

            matched.append(
                PhysicsReactionResult(
                    rule_id=rule["rule_id"],
                    result_name=rule["result_name"],
                    description=rule["description"],
                    damage_bonus=rule.get("damage_bonus", 1.0),
                    tag=rule.get("tag", ""),
                    status_to_apply=rule.get("status_to_apply"),
                    status_duration=rule.get("status_duration", 0),
                    status_potency=rule.get("status_potency", 0),
                )
            )

        return matched

    @classmethod
    def format_reactions_for_prompt(cls, reactions: List[PhysicsReactionResult]) -> str:
        """Formats matched physical reactions for dynamic GM prompt injection."""
        if not reactions:
            return ""
        lines = ["[🔬 물리/화학/환경 상호작용 법칙 적용 (DETERMINISTIC PHYSICS)]"]
        for r in reactions:
            lines.append(f"- **{r.result_name}** (피해 배율 x{r.damage_bonus}): {r.description}")
            if r.status_to_apply:
                lines.append(f"  *부여되는 상태이상: [{r.status_to_apply}] (지속: {r.status_duration}턴)*")
        return "\n".join(lines)
