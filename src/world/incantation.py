"""
Magic Incantation System for Quilltale TRPG Engine.
Modular Keyword Slot System (Element + Form + Vector + Modifier + Pact / Sentence).
Enforces character limits per turn, tracks learned magic vocabulary.
Science-based & Classical Fantasy Magic: spells interact with real physics & narrative causalities.
"""
import re
from typing import Tuple, List, Optional, Dict
from src.core.config import BASE_INCANTATION_CHARS, WISDOM_INCANT_BONUS

# Comprehensive Modular Incantation Lexicon
INCANTATION_LEXICON: Dict[str, Dict[str, dict]] = {
    "modifiers": {
        "암플리피코": {"latin": "Amplifico", "role": "대폭 증폭", "power_mult": 2.0, "mana_add": 15},
        "그랜드": {"latin": "Grand", "role": "대형/광역", "power_mult": 1.7, "mana_add": 12},
        "막시무스": {"latin": "Maximus", "role": "최대 출력", "power_mult": 2.2, "mana_add": 18},
        "마이크로": {"latin": "Micro", "role": "극소 압축/관통", "power_mult": 1.6, "mana_add": 10},
        "콘센트로": {"latin": "Concentro", "role": "초집중", "power_mult": 1.8, "mana_add": 12},
        "엑스트라": {"latin": "Extra", "role": "과충전", "power_mult": 1.9, "mana_add": 14},
        "오버차지": {"latin": "Overcharge", "role": "한계 돌파", "power_mult": 2.5, "mana_add": 20},
    },
    "elements": {
        "이그니스": {"latin": "Ignis", "role": "화염", "element": "fire"},
        "글라키에": {"latin": "Glacies", "role": "빙결", "element": "ice"},
        "글라키에스": {"latin": "Glacies", "role": "빙결", "element": "ice"},
        "풀구르": {"latin": "Fulgur", "role": "번개", "element": "lightning"},
        "풀멘": {"latin": "Fulmen", "role": "낙뢰", "element": "lightning"},
        "움브라": {"latin": "Umbra", "role": "암흑", "element": "dark"},
        "아쿠아": {"latin": "Aqua", "role": "수류", "element": "water"},
        "벤투스": {"latin": "Ventus", "role": "바람", "element": "wind"},
        "룩스": {"latin": "Lux", "role": "빛", "element": "light"},
        "테라": {"latin": "Terra", "role": "대지", "element": "earth"},
        "모르티스": {"latin": "Mortis", "role": "사령/죽음", "element": "dark"},
        "상투스": {"latin": "Sanctus", "role": "신성", "element": "holy"},
        "에테르": {"latin": "Aether", "role": "비전/공허", "element": "arcane"},
    },
    "forms": {
        "사기타": {"latin": "Sagitta", "role": "화살/관통", "form": "arrow"},
        "스페라": {"latin": "Sphaera", "role": "구체/탄환", "form": "orb"},
        "오브": {"latin": "Orb", "role": "구체", "form": "orb"},
        "무루스": {"latin": "Murus", "role": "장벽/방벽", "form": "shield"},
        "실드": {"latin": "Shield", "role": "방호막", "form": "shield"},
        "엔시스": {"latin": "Ensis", "role": "도검/참격", "form": "blade"},
        "블레이드": {"latin": "Blade", "role": "검기", "form": "blade"},
        "란시아": {"latin": "Lancia", "role": "창/돌파", "form": "spear"},
        "볼텍스": {"latin": "Vortex", "role": "소용돌이/회오리", "form": "vortex"},
        "메테오": {"latin": "Meteo", "role": "거대 낙하체/운석", "form": "meteor"},
        "필드": {"latin": "Field", "role": "영역/결계", "form": "field"},
    },
    "vectors": {
        "볼란스": {"latin": "Volans", "role": "투사/직진 날아감", "action": "shot"},
        "샷": {"latin": "Shot", "role": "발사", "action": "shot"},
        "임팩투스": {"latin": "Impactus", "role": "충돌 격발/폭발", "action": "burst"},
        "버스트": {"latin": "Burst", "role": "폭발", "action": "burst"},
        "트랙투스": {"latin": "Tractus", "role": "인력/끌어당김", "action": "pull"},
        "인챈트": {"latin": "Enchant", "role": "무기/신체 부여", "action": "enchant"},
        "레인": {"latin": "Rain", "role": "상공 낙하", "action": "rain"},
        "호밍": {"latin": "Homing", "role": "유도 추적", "action": "homing"},
        "딜레이": {"latin": "Delay", "role": "시차 지연 폭발", "action": "delay"},
        "체인": {"latin": "Chain", "role": "연쇄 전이", "action": "chain"},
    },
    "triggers": {
        "임팩트": {"latin": "Impact", "role": "충돌 시 격발", "trigger": "on_impact"},
        "에어": {"latin": "Air", "role": "공중 작열", "trigger": "mid_air"},
        "언더풋": {"latin": "Underfoot", "role": "발밑 기습", "trigger": "ground"},
    },
    "pacts": {
        "상구이스": {"latin": "Sanguis", "role": "피/체력 대가", "cost_type": "hp"},
        "템푸스": {"latin": "Tempus", "role": "시간/지연 대가", "cost_type": "turn"},
        "옥시젠": {"latin": "Oxygen", "role": "호흡/체력 대가", "cost_type": "fatigue"},
        "샬라": {"latin": "Shala", "role": "화염 군주 계약", "pact_god": "shala"},
        "타나토스": {"latin": "Thanatos", "role": "사멸의 신 계약", "pact_god": "thanatos"},
        "아에테르": {"latin": "Aether", "role": "공허의 지배자 계약", "pact_god": "aether"},
        "아우라": {"latin": "Aura", "role": "폭풍 현상", "result_form": "storm"},
        "카게": {"latin": "Kage", "role": "그림자 구속", "result_form": "bind"},
    }
}


class IncantationSystem:
    @staticmethod
    def get_char_limit(player) -> int:
        """Max incantation characters player can speak per turn."""
        wisdom_bonus = max(0, getattr(player, 'wisdom', 10) - 10) * WISDOM_INCANT_BONUS
        return BASE_INCANTATION_CHARS + wisdom_bonus

    @staticmethod
    def classify_magic_words(words: List[str]) -> Dict[str, List[dict]]:
        """
        Classify known magic words into modular categories for UI display.
        Returns dict keyed by category name: modifiers, elements, forms, vectors, pacts, etc.
        """
        classified: Dict[str, List[dict]] = {
            "modifiers": [],
            "elements": [],
            "forms": [],
            "vectors": [],
            "triggers": [],
            "pacts": [],
            "custom": []
        }
        for w in words:
            found = False
            for cat, lookup in INCANTATION_LEXICON.items():
                if w in lookup:
                    info = lookup[w].copy()
                    info["word"] = w
                    classified[cat].append(info)
                    found = True
                    break
            if not found:
                classified["custom"].append({"word": w, "role": "고대어", "latin": w})
        return classified

    @staticmethod
    def parse_incantation(text: str) -> Optional[dict]:
        """
        Parse a player incantation string into modular components and compute power/mechanics.
        Supports:
        - 3-slot: [Element] + [Form] + [Vector] (e.g. 이그니스 사기타 볼란스)
        - 4~5-slot: [Modifier] + [Element(s)] + [Form] + [Vector] + [Trigger]
        - Pact-based: [Cost] + [Pact] + [Result] (e.g. 상구이스 샬라 아우라)
        - Latin ritual sentences
        """
        clean = text.strip()
        tokens = re.findall(r'[가-힣a-zA-Z]+', clean)
        if not tokens:
            return None

        # Check pact-based structure
        pact_costs = [t for t in tokens if t in INCANTATION_LEXICON["pacts"] and "cost_type" in INCANTATION_LEXICON["pacts"][t]]
        pact_gods = [t for t in tokens if t in INCANTATION_LEXICON["pacts"] and "pact_god" in INCANTATION_LEXICON["pacts"][t]]
        pact_results = [t for t in tokens if t in INCANTATION_LEXICON["pacts"] and "result_form" in INCANTATION_LEXICON["pacts"][t]]

        if pact_costs and (pact_gods or pact_results):
            cost_info = INCANTATION_LEXICON["pacts"][pact_costs[0]]
            god_info = INCANTATION_LEXICON["pacts"][pact_gods[0]] if pact_gods else {}
            res_info = INCANTATION_LEXICON["pacts"][pact_results[0]] if pact_results else {}
            return {
                "type": "pact",
                "tokens": tokens,
                "cost": cost_info.get("role", "대가"),
                "cost_type": cost_info.get("cost_type", "hp"),
                "pact_god": god_info.get("role", "신격"),
                "result": res_info.get("role", "현상"),
                "power_mult": 2.5,
                "mana_cost": 5,
                "description_summary": f"시전자의 {cost_info.get('role')}를 바쳐 {god_info.get('role', '')}의 권능으로 {res_info.get('role', '')}을(를) 전개",
            }

        # Check modular slot structure
        found_mods = [t for t in tokens if t in INCANTATION_LEXICON["modifiers"]]
        found_elems = [t for t in tokens if t in INCANTATION_LEXICON["elements"]]
        found_forms = [t for t in tokens if t in INCANTATION_LEXICON["forms"]]
        found_vecs = [t for t in tokens if t in INCANTATION_LEXICON["vectors"]]
        found_trigs = [t for t in tokens if t in INCANTATION_LEXICON["triggers"]]

        if not (found_elems or found_forms or found_vecs):
            return {
                "type": "custom",
                "tokens": tokens,
                "power_mult": 1.0,
                "mana_cost": 15,
                "description_summary": f"고대어 [{clean}] 영창 발동",
            }

        power_mult = 1.0
        mana_cost = 10
        desc_parts = []

        if found_mods:
            mod_data = INCANTATION_LEXICON["modifiers"][found_mods[0]]
            power_mult *= mod_data.get("power_mult", 1.5)
            mana_cost += mod_data.get("mana_add", 10)
            desc_parts.append(mod_data.get("role", ""))

        elem_roles = [INCANTATION_LEXICON["elements"][e].get("role", e) for e in found_elems]
        if elem_roles:
            desc_parts.append("·".join(elem_roles))
            mana_cost += len(elem_roles) * 5

        form_roles = [INCANTATION_LEXICON["forms"][f].get("role", f) for f in found_forms]
        if form_roles:
            desc_parts.append("·".join(form_roles))

        vec_roles = [INCANTATION_LEXICON["vectors"][v].get("role", v) for v in found_vecs]
        if vec_roles:
            desc_parts.append("·".join(vec_roles))

        trig_roles = [INCANTATION_LEXICON["triggers"][tr].get("role", tr) for tr in found_trigs]
        if trig_roles:
            desc_parts.append(f"({', '.join(trig_roles)})")

        summary_desc = " ".join(desc_parts) + " 형태로 마력이 집중 및 격발됩니다."

        return {
            "type": "modular",
            "tokens": tokens,
            "modifiers": found_mods,
            "elements": found_elems,
            "forms": found_forms,
            "vectors": found_vecs,
            "triggers": found_trigs,
            "power_mult": round(power_mult, 2),
            "mana_cost": mana_cost,
            "description_summary": summary_desc,
        }

    @staticmethod
    def validate_incantation(
        player,
        spell_text: str,
        skill_required_words: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """
        Validate if player can cast this incantation.
        Returns (is_valid, reason_ko).
        """
        char_limit = IncantationSystem.get_char_limit(player)
        clean = spell_text.strip()

        if len(clean) > char_limit:
            return False, (
                f'영창이 너무 깁니다. 현재 당신이 1턴에 발음할 수 있는 한계는 [{char_limit}]자이며, '
                f'이 주문은 [{len(clean)}]자입니다. (지혜 스탯을 올려 영창 한계를 늘릴 수 있습니다)'
            )

        known = getattr(player, 'known_magic_words', [])
        if skill_required_words:
            unknown = [w for w in skill_required_words if w not in known]
            if unknown:
                return False, (
                    f'아직 습득하지 못한 마법 언어가 포함되어 있습니다: ["{"、".join(unknown)}"] (도서관 서적 탐독이나 스승 NPC의 가르침을 받아 습득하세요)'
                )

        tokens = re.findall(r'[가-힣a-zA-Z]+', clean)
        all_lexicon_keys = set()
        for lookup in INCANTATION_LEXICON.values():
            all_lexicon_keys.update(lookup.keys())

        used_lexicon_words = [t for t in tokens if t in all_lexicon_keys]
        if used_lexicon_words:
            unknown_used = [w for w in used_lexicon_words if w not in known]
            if unknown_used:
                return False, (
                    f'아직 온전히 체득하지 못한 고대어 키워드가 포함되어 있습니다: ["{"、".join(unknown_used)}"]. '
                    f'무리하게 영창할 경우 마력 역류 부작용이 발생할 수 있습니다.'
                )

        return True, ''

    @staticmethod
    def detect_incantation_in_action(action: str) -> bool:
        """Detect if player action involves magic casting/incantation."""
        keywords = [
            '영창', '주문', '마법을 시전', '시전한다', '외운다', '발동', '발음한다',
            'incant', 'cast', '이그니스', '글라키에', '풀구르', '움브라', '아쿠아',
            '사기타', '스페라', '무루스', '볼란스', '임팩투스', '암플리피코', '그랜드'
        ]
        return any(k in action.lower() for k in keywords)

    @staticmethod
    def can_be_cancelled_by_npc(action: str) -> bool:
        """If player is incanting, NPC may attempt to interrupt."""
        return IncantationSystem.detect_incantation_in_action(action)

