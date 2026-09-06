"""
Realistic Multi-Dimensional Stat Engine for Quilltale TRPG.
Anchors human peak at stat 15 (Olympic record/historical peak), average at stat 10.
Supports 7 core stats, derived combat mechanics, infinite sub-stats dictionary,
and deterministic leveling EXP curves.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


# Anchor Constants
AVERAGE_HUMAN_STAT: int = 10
HUMAN_PEAK_STAT: int = 15      # Olympic gold / historical human record
SUPERHUMAN_THRESHOLD: int = 16 # Superhuman / fantasy transcendence

# 7 Core Stats Metadata & Anchors
CORE_STATS_KO: Dict[str, Dict[str, Any]] = {
    "strength": {
        "name_ko": "근력",
        "description": "근접 타격력, 활 한계 인장력(lbs), 중량 적재, 넉백 저항",
        "human_peak_desc": "올림픽 역도 금메달 / 중세 영국 장궁 150 lbs 완발 장력 / 헤비급 강펀치",
    },
    "agility": {
        "name_ko": "민첩",
        "description": "이동 속도(m/s), 초기 가속력, 공격 선딜레이 단축, 도약력, 회피",
        "human_peak_desc": "우사인 볼트 최고 전력 질주 속도 10.5 m/s, 반사 신경 0.12초",
    },
    "constitution": {
        "name_ko": "체질",
        "description": "최대 체력, 심폐 지구력, 출혈/독/질병 저항, 피격 저지력 내성(강인도)",
        "human_peak_desc": "극지 철인 3종 경기 마라토너 (탈진/고통 무감, 뼈 밀도 상위 0.01%)",
    },
    "intelligence": {
        "name_ko": "지능",
        "description": "마나 총량, 복합 고대어 주문 해독, 마법 저항력, 공학 메커니즘 간파",
        "human_peak_desc": "폰 노이만급 천재 석학 (순간 암산, 복합 룬 기하학 찰나 판독)",
    },
    "wisdom": {
        "name_ko": "지혜",
        "description": "영창 속도 단축, 정신/공포/세뇌 저항, 마나 회복 효율, 직관력",
        "human_peak_desc": "고승의 무아지경 명상 / 찰나의 마나 조율 및 2초 초고속 고대어 영창",
    },
    "perception": {
        "name_ko": "감각",
        "description": "위험 감지 거리, 기습 포착 선제권, 찰나의 반응 속도, 은신 간파",
        "human_peak_desc": "몽골 궁수 시력 3.0, 스나이퍼의 미세 풍향·기압 육감 간파",
    },
    "luck": {
        "name_ko": "행운",
        "description": "치명타 확률(Crit Chance), 기적적 빗맞음, 전리품 품질 보너스",
        "human_peak_desc": "사선을 넘나드는 천운, 0.1%의 기적적 빗맞음 발생",
    },
}


@dataclass
class StatEngine:
    TRAITS: List[str] = field(default_factory=lambda: [
        "스탯 엔진",
        "인간계 정점 15 앵커",
        "무한 서브스탯",
        "현실 물리 연동",
        "경험치 레벨업"
    ])
    traits: List[str] = field(default_factory=lambda: [
        "스탯 엔진",
        "인간계 정점 15 앵커",
        "무한 서브스탯",
        "현실 물리 연동",
        "경험치 레벨업"
    ])

    @classmethod
    def calculate_required_exp(cls, level: int) -> int:
        """레벨업 필요 경험치 공식: req_exp(L) = int(100 * L^1.5)."""
        if level <= 0:
            return 100
        return int(100 * (level ** 1.5))

    @classmethod
    def calculate_movement_speed(cls, agility: int) -> float:
        """
        이동 속도(m/s) 계산.
        민첩 10: 4.5 m/s (성인 일반인 조깅/달리기)
        민첩 15: 10.5 m/s (우사인 볼트 최고 전력 질주 속도)
        민첩 16+: 초인 질주 (음속/탈인간)
        """
        base = 4.5 + (agility - 10) * 1.2
        return max(1.0, round(base, 2))

    @classmethod
    def calculate_max_draw_weight(cls, strength: int) -> float:
        """
        최대 활 인장력 (lbs) 계산.
        근력 10: 50 lbs (성인 일반인 당김)
        근력 15: 150 lbs (영국 중세 메리 로즈 호 장궁 최고 장력)
        근력 16+: 거인용 강궁
        """
        base = 50.0 + (strength - 10) * 20.0
        return max(10.0, round(base, 1))

    @classmethod
    def calculate_windup_multiplier(cls, agility: int) -> float:
        """
        무기 선딜레이(Wind-up) 배율.
        민첩 10: 1.0 (기본 선딜레이)
        민첩 15: 0.5 (선딜레이 50% 단축)
        """
        base = 1.0 - (agility - 10) * 0.1
        return max(0.2, round(base, 2))

    @classmethod
    def calculate_incantation_multiplier(cls, wisdom: int) -> float:
        """
        영창 속도 배율.
        지혜 10: 1.0 (기본 영창 시간)
        지혜 15: 0.5 (영창 시간 50% 단축)
        """
        base = 1.0 - (wisdom - 10) * 0.1
        return max(0.2, round(base, 2))

    @classmethod
    def calculate_poise(cls, constitution: int, armor_bonus: float = 0.0) -> float:
        """
        강인도(피격 저지력 내성) 계산.
        체질 10 기준 기본 강인도 0.0 + 체질 증가 및 갑옷 방어력 보정.
        """
        base = max(0, constitution - 10) * 2.0 + armor_bonus * 0.5
        return max(0.0, round(base, 1))

    @classmethod
    def get_sub_stat(cls, entity: Any, key: str, default: float = 0.0) -> float:
        """무한 확장 서브스탯 딕셔너리에서 값 조회."""
        sub_stats = getattr(entity, "sub_stats", None)
        if isinstance(sub_stats, dict):
            return float(sub_stats.get(key, default))
        return default

    @classmethod
    def set_sub_stat(cls, entity: Any, key: str, value: float) -> None:
        """무한 확장 서브스탯 딕셔너리에 값 설정."""
        if not hasattr(entity, "sub_stats") or not isinstance(entity.sub_stats, dict):
            entity.sub_stats = {}
        entity.sub_stats[key] = float(value)

    @classmethod
    def modify_sub_stat(cls, entity: Any, key: str, delta: float) -> float:
        """무한 확장 서브스탯 가감 수정."""
        current = cls.get_sub_stat(entity, key, 0.0)
        new_val = current + delta
        cls.set_sub_stat(entity, key, new_val)
        return new_val

    @classmethod
    def get_tier_description_ko(cls, stat_val: int) -> str:
        """스탯 수치별 인간계 위계 묘사 반환."""
        if stat_val <= 6:
            return "심각한 결손/허약 (일반인 미달)"
        elif stat_val <= 9:
            return "다소 부족 (훈련 필요)"
        elif stat_val == 10:
            return "건강한 성인 평균 (표준)"
        elif stat_val <= 14:
            return "숙련된 전문가/단련된 전사"
        elif stat_val == 15:
            return "★ 인간계 최고 정점 (올림픽 금메달/역사적 최고 기록)"
        elif stat_val <= 18:
            return "초인/영웅적 각성 (인간의 한계 초월)"
        else:
            return "신화/마수/반신급 위계"

    @classmethod
    def format_stat_sheet_ko(cls, entity: Any) -> str:
        """7대 스탯 및 주요 물리 파생 스탯의 상세 한글 시트 생성."""
        lines = ["=== [캐릭터 스탯 & 물리 역학 규격] ==="]
        lines.append(f"이름: {getattr(entity, 'name', '불명')}")
        lines.append(f"레벨: {getattr(entity, 'level', 1)} | 보유 스탯 포인트: {getattr(entity, 'stat_points', 0)}")
        lines.append("-" * 35)

        stats = [
            ("strength", getattr(entity, "effective_strength", getattr(entity, "strength", 10))),
            ("agility", getattr(entity, "effective_agility", getattr(entity, "agility", 10))),
            ("constitution", getattr(entity, "effective_constitution", getattr(entity, "constitution", 10))),
            ("intelligence", getattr(entity, "effective_intelligence", getattr(entity, "intelligence", 10))),
            ("wisdom", getattr(entity, "wis_stat", getattr(entity, "wisdom", 10))),
            ("perception", getattr(entity, "effective_perception", getattr(entity, "perception", 10))),
            ("luck", getattr(entity, "luck", 10)),
        ]

        for s_key, s_val in stats:
            info = CORE_STATS_KO.get(s_key, {"name_ko": s_key})
            tier = cls.get_tier_description_ko(s_val)
            lines.append(f"• {info['name_ko']} ({s_key[:3].upper()}): {s_val} [{tier}]")

        lines.append("-" * 35)
        lines.append("【물리 역학 파생 지표】")
        str_val = stats[0][1]
        agi_val = stats[1][1]
        con_val = stats[2][1]
        wis_val = stats[4][1]

        speed = cls.calculate_movement_speed(agi_val)
        draw_w = cls.calculate_max_draw_weight(str_val)
        windup = cls.calculate_windup_multiplier(agi_val)
        incant = cls.calculate_incantation_multiplier(wis_val)
        poise = cls.calculate_poise(con_val, getattr(entity, "equipment_defense", 0))

        lines.append(f"• 질주 속도: {speed:.1f} m/s (초기 가속 포함)")
        lines.append(f"• 최대 활 장력: {draw_w:.1f} lbs (인장 한계)")
        lines.append(f"• 공격 선딜레이 배율: x{windup:.2f}")
        lines.append(f"• 주문 영창 시간 배율: x{incant:.2f}")
        lines.append(f"• 강인도 (피격 저지력 내성): {poise:.1f}")

        sub_stats = getattr(entity, "sub_stats", {})
        if sub_stats:
            lines.append("-" * 35)
            lines.append("【특수 서브스탯】")
            for k, v in sub_stats.items():
                lines.append(f"• {k}: {v}")

        return "\n".join(lines)
