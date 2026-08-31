"""
Living World Graph Engine for Quilltale TRPG Engine.
Integrates:
1. GraphRAG Knowledge Graph (World <-> Region <-> Monster <-> Material <-> Skill)
2. Physics and Chemistry Interaction Matrix (16 Fundamental Laws)
3. Bidirectional Ecological Feedback Loop (Actions -> Terraforming and Faction Ripples)
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from src.core.config import TEMPLATES_DIR

logger = logging.getLogger(__name__)

# 16 Fundamental Physics & Chemistry Laws
PHYSICS_CHEMISTRY_RULES = [
    {
        'rule_id': 'acid_mineral_corrosion',
        'source_keys': ['산성', '소화액', '부식', 'acid'],
        'target_keys': ['광물', '흑요석', '키틴질', '철', '강철', '방어구', '갑옷', '거인', '골렘'],
        'result_name': '화학적 산성 용해 (Corrosive Melt)',
        'description': '강산성 화학 반응으로 대상의 표면 장갑과 외골격이 급속도로 녹아내려 방어력이 무력화됩니다.',
        'damage_bonus': 1.5,
        'tag': '방어구 파괴'
    },
    {
        'rule_id': 'thermal_shock_shatter',
        'source_keys': ['극저온', '빙결', '냉기', '글라키에', 'cold', 'frost'],
        'target_keys': ['용암', '마그마', '고열', '흑요석', '유리', '가마', '백자'],
        'result_name': '열충격 급랭 파쇄 (Thermal Shock)',
        'description': '초고열 상태의 물체에 극저온 냉기가 닿아 급격한 부피 수축으로 내부 응력이 폭주하여 산산조각 납니다.',
        'damage_bonus': 2.0,
        'tag': '열충격 분쇄'
    },
    {
        'rule_id': 'superconductive_discharge',
        'source_keys': ['번개', '전기', '전류', '풀구르', 'lightning'],
        'target_keys': ['수은', '초전도', '전류신경', '액체금속'],
        'result_name': '초전도 광역 방전 (Area Discharge)',
        'description': '액체 도체 및 신경 매질을 타고 고전압 전류가 순간적으로 확산되어 범위 내 모든 대상에게 치명적인 감전 마비를 일으킵니다.',
        'damage_bonus': 1.6,
        'tag': '광역 감전'
    },
    {
        'rule_id': 'methane_chain_explosion',
        'source_keys': ['화염', '불꽃', '이그니스', '폭발', 'fire'],
        'target_keys': ['메탄', '인화성 가스', '늪지', '부패가스', '유황가스'],
        'result_name': '유기물 연쇄 기화 폭발 (Chain Explosion)',
        'description': '인화성 가스와 지방질 층에 불꽃이 닿아 산소가 급격히 연소하며 대규모 연쇄 폭발을 일으키고 지형을 불태웁니다.',
        'damage_bonus': 2.2,
        'tag': '지형 연쇄 폭발'
    },
    {
        'rule_id': 'resonance_frequency_shatter',
        'source_keys': ['음파', '진동', '공진', '소리굽쇠', 'sound', 'vibration'],
        'target_keys': ['유리', '거울', '백자', '도자기', '결정체', '수정'],
        'result_name': '고유 진동수 공진 파쇄 (Frequency Shatter)',
        'description': '물체의 고유 진동수와 일치하는 강력한 음파 파동이 취성(Brittle) 구조를 내부에서부터 공명 분쇄합니다.',
        'damage_bonus': 1.8,
        'tag': '공진 분쇄'
    },
    {
        'rule_id': 'ceramic_complete_insulation',
        'source_keys': ['번개', '전기', '감전', '풀구르'],
        'target_keys': ['백자', '도자기', '절연', '점토'],
        'result_name': '완전 절연 차단 (Complete Insulation)',
        'description': '도자기 및 백자 유약 코팅 층이 전하의 흐름을 100% 차단하여 전기 피해를 완전 무효화합니다.',
        'damage_bonus': 0.0,
        'tag': '전기 면역'
    },
    {
        'rule_id': 'wax_rapid_melting',
        'source_keys': ['화염', '열기', '고열', '이그니스'],
        'target_keys': ['밀랍', '양초', '심지'],
        'result_name': '밀랍 급속 융해 및 봉인 해제 (Rapid Melting)',
        'description': '밀랍 구조물이 고열에 녹아내려 굳어있던 대상을 해방하거나 통로가 개방됩니다.',
        'damage_bonus': 1.4,
        'tag': '밀랍 융해'
    },
    {
        'rule_id': 'mercury_freeze_solid',
        'source_keys': ['빙결', '극저온', '냉기', '글라키에'],
        'target_keys': ['수은', '액체금속'],
        'result_name': '수은 동결 경화 (Mercury Solidification)',
        'description': '영하 38.8도 이하로 냉각된 수은이 단단한 고체 금속으로 굳어 유동성을 잃고 발판이나 무기로 변합니다.',
        'damage_bonus': 1.3,
        'tag': '유체 고체화'
    },
    {
        'rule_id': 'prism_refraction_split',
        'source_keys': ['빛', '광선', '룩스', 'light', 'laser'],
        'target_keys': ['프리즘', '거울', '분광', '유리'],
        'result_name': '프리즘 분광 굴절 (Spectral Refraction)',
        'description': '단일 광선이 열선(적외선)과 냉선(자외선)으로 갈라져 다중 속성 파동으로 증폭 확산됩니다.',
        'damage_bonus': 1.7,
        'tag': '분광 증폭'
    },
    {
        'rule_id': 'water_ink_dissolution',
        'source_keys': ['수류', '물', '홍수', '아쿠아'],
        'target_keys': ['먹물', '종이', '활판', '오리가미'],
        'result_name': '잉크 및 종이 수용성 해체 (Dissolution)',
        'description': '대량의 수류가 잉크와 종이의 결합을 분해하여 활자와 결계를 씻어내고 소멸시킵니다.',
        'damage_bonus': 1.6,
        'tag': '결계 용해'
    },
    {
        'rule_id': 'confined_heat_trap',
        'source_keys': ['화염', '불꽃', '이그니스', '폭발', '화염구', '열기'],
        'target_keys': ['밀폐', '석실', '동굴', '지하', '방', '실내', '감옥', '성채 내부'],
        'result_name': '밀폐 공간 엔트로피 열기 축적 (Heat Trap Exhaustion)',
        'description': '밀폐된 공간에서 빠져나가지 못한 열기가 갇혀 실내 기온이 80도 이상으로 치솟아 시전자와 대상 모두 급격한 열사병 및 산소 결핍에 노출됩니다.',
        'damage_bonus': 1.4,
        'tag': '엔트로피 열사병'
    },
    {
        'rule_id': 'kinetic_recoil_strain',
        'source_keys': ['강타', '초중량', '대검', '철퇴', '둔기', '폭쇄', '골렘', '거인', '충격파'],
        'target_keys': ['방패', '가드', '철제 방패', '금속 방패', '막기', '방어'],
        'result_name': '운동 에너지 전이 및 관절 과부하 (Kinetic Recoil Strain)',
        'description': '방패 자체는 파손되지 않으나 막대한 운동 에너지가 사용자의 손목 및 어깨 관절로 100% 전이되어 관절 탈구 및 다음 턴 조작 페널티가 발생합니다.',
        'damage_bonus': 1.3,
        'tag': '관절 탈구 반동'
    },
    {
        'rule_id': 'toxic_gas_settling',
        'source_keys': ['산성', '소화액', '독안개', '부패', '연기'],
        'target_keys': ['바닥', '지면', '저지대', '하수도', '동굴 바닥', '웅덩이'],
        'result_name': '고밀도 독성 가스 침강 (Dense Gas Settling)',
        'description': '반응 후 생성된 무거운 유독 가스가 바닥으로 가라앉아 엎드리거나 넘어진 대상에게 치명적인 호흡기 중독을 일으킵니다.',
        'damage_bonus': 1.5,
        'tag': '저지대 독가스'
    },
    {
        'rule_id': 'brittle_overstrain',
        'source_keys': ['극저온', '급랭', '글라키에', '빙결', '냉기'],
        'target_keys': ['강철검', '칼날', '창', '금속 무기', '단검', '검'],
        'result_name': '저온 취성 파손 위험 (Low-Temperature Brittleness)',
        'description': '극저온에 노출된 금속 무기는 인성을 잃고 유리처럼 부서지기 쉬운 취성 상태로 변해 강한 타격 시 무기가 파손될 위험이 있습니다.',
        'damage_bonus': 1.2,
        'tag': '저온 취성'
    },
    {
        'rule_id': 'wet_conductive_spread',
        'source_keys': ['번개', '전격', '풀구르', '전기', 'lightning'],
        'target_keys': ['젖은', '물 웅덩이', '폭우', '비에 젖은', '수류'],
        'result_name': '수분 매질 초전도 확산 (Wet Conductive Spread)',
        'description': '물과 수분에 젖은 매질을 타고 전류가 순간적으로 번져 주변의 아군과 적 모두에게 무차별 감전을 일으킵니다.',
        'damage_bonus': 1.6,
        'tag': '광역 감전 연쇄'
    },
    {
        'rule_id': 'oil_flame_wall',
        'source_keys': ['화염', '불꽃', '이그니스', '횃불', 'fire'],
        'target_keys': ['기름통', '기름 바닥', '유착제', '기름 웅덩이'],
        'result_name': '유류 급속 착화 화염벽 (Oil Flame Wall)',
        'description': '바닥에 누출된 기름에 불이 붙어 즉시 2미터 높이의 거대한 화염벽이 형성되어 통로가 완전히 차단됩니다.',
        'damage_bonus': 1.8,
        'tag': '화염벽 차단'
    },
    {
        'rule_id': 'dust_methane_explosion',
        'source_keys': ['횃불', '불꽃', '화염', '스파크', '점화'],
        'target_keys': ['분진', '밀폐 광산', '메탄가스 구역', '유황 동굴'],
        'result_name': '밀폐 분진/가스 폭발 (Dust/Gas Explosion)',
        'description': '공기 중의 부유 분진이나 메탄 층에 불꽃이 닿아 공간 전체가 연쇄 폭발하며 갱도가 붕괴됩니다.',
        'damage_bonus': 2.5,
        'tag': '공간 분진 폭발'
    },
    {
        'rule_id': 'spatial_weapon_interference',
        'source_keys': ['긴 창', '대검', '장창', '할버드', '양손검'],
        'target_keys': ['좁은 동굴', '환풍구', '비좁은 통로', '석실 모퉁이', '밀실'],
        'result_name': '공간 간섭 무기 휘두르기 불능 (Spatial Weapon Interference)',
        'description': '무기의 물리적 길이가 좁은 벽면에 걸려 정상적인 베기/휘두르기가 불가능하며 선제공격권을 상실합니다.',
        'damage_bonus': 0.3,
        'tag': '공간 간섭 불능'
    },
    {
        'rule_id': 'hypothermia_incant_fail',
        'source_keys': ['저체온증', '폭설', '눈보라', '젖은 옷 방치'],
        'target_keys': ['손끝', '영창', '마력 제어', '시전'],
        'result_name': '저체온증 말초신경 마비 (Hypothermia Incant Fail)',
        'description': '손끝 감각이 마비되고 턱이 떨려 정확한 고대어 발음이 불가능해져 영창 실패율이 급증하고 마나 회복이 중단됩니다.',
        'damage_bonus': 0.5,
        'tag': '영창 제어 실패'
    },
    {
        'rule_id': 'blade_dulling_armor',
        'source_keys': ['참격', '도검', '검', '단검', '베기'],
        'target_keys': ['두꺼운 판금', '판금 갑옷', '암석 골렘', '강철 흉갑'],
        'result_name': '칼날 이 빠짐 및 둔화 (Blade Dulling)',
        'description': '경도가 높은 금속 갑옷이나 암석에 칼날이 부딪혀 이가 빠지고 무뎌져 참격 피해가 둔기 수준으로 반토막 납니다.',
        'damage_bonus': 0.5,
        'tag': '칼날 손상'
    },
    {
        'rule_id': 'scent_leakage_aggro',
        'source_keys': ['피 냄새', '오물', '썩은 체취', '피투성이'],
        'target_keys': ['야수', '식인 마수', '늑대 떼', '괴수'],
        'result_name': '체취 누출 야수 추적 유인 (Scent Leakage Aggro)',
        'description': '몸에 밴 피와 오물 냄새가 바람을 타고 확산되어 인근 구역의 굶주린 야수들을 자극해 기습을 유발합니다.',
        'damage_bonus': 1.4,
        'tag': '야수 기습 유인'
    },
    {
        'rule_id': 'water_incant_suffocation',
        'source_keys': ['수중 영창', '연기 속 발성', '물속 주문'],
        'target_keys': ['수중', '물속', '유독 연기 속', '화재 건물'],
        'result_name': '호흡 매질 폐 유입 급성 질식 (Acute Suffocation)',
        'description': '수중이나 농연 속에서 소리를 내어 영창하는 순간 물과 유독 가스가 기도로 유입되어 즉각 질식 기절에 빠집니다.',
        'damage_bonus': 2.0,
        'tag': '급성 질식'
    }
]


class PhysicsChemistryMatrix:
    @staticmethod
    def evaluate_interaction(action_or_spell: str, target_desc: str) -> Optional[Dict[str, Any]]:
        """
        Evaluate physical and chemical interaction between action/spell and target materials.
        """
        action_lower = action_or_spell.lower()
        target_lower = target_desc.lower()

        for rule in PHYSICS_CHEMISTRY_RULES:
            src_match = any(k in action_lower for k in rule['source_keys'])
            tgt_match = any(k in target_lower for k in rule['target_keys'])
            if src_match and tgt_match:
                return rule
        return None


class LivingWorldGraph:
    def __init__(self, data_path: Optional[Path] = None):
        self.path = data_path or (TEMPLATES_DIR / 'ecosystem_graph.json')
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self._load_graph()

    def _load_graph(self):
        if not self.path.exists():
            logger.warning(f'Ecosystem graph file not found: {self.path}')
            return
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for node in data:
                    self.nodes[node['region_id']] = node
            logger.info(f'Loaded {len(self.nodes)} ecosystem graph nodes')
        except Exception as e:
            logger.error(f'Failed to load ecosystem graph: {e}')

    def get_regional_ecosystem(self, region_id: str) -> Optional[Dict[str, Any]]:
        return self.nodes.get(region_id)

    def find_cross_regional_synergies(
        self,
        inventory_item_names: List[str],
        current_region_name: str,
        current_monsters: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Detect if items carried from other regions trigger physical/chemical counter-synergies here.
        """
        synergies = []
        target_context = f'{current_region_name} ' + ' '.join(current_monsters)

        for item in inventory_item_names:
            interaction = PhysicsChemistryMatrix.evaluate_interaction(item, target_context)
            if interaction:
                synergies.append({
                    'item': item,
                    'target': target_context,
                    'rule': interaction
                })
        return synergies


class EcologicalFeedbackLoop:
    @staticmethod
    def calculate_feedback(
        action: str,
        dice_success: bool,
        current_region: str,
        state: Any
    ) -> Dict[str, Any]:
        """
        Calculate bidirectional environmental mutations and ripple effects across the continent.
        """
        impact = {
            'terraforming': '',
            'reputation_delta': 0,
            'world_news': '',
            'corruption_change': 0
        }

        # Major destruction or chemical chain reaction
        if dice_success and any(k in action for k in ['대폭발', '화염구', '암플리피코', '화쇄류']):
            if '늪' in current_region or '숲' in current_region:
                impact['terraforming'] = f'{current_region}의 식생과 메탄 층이 대규모로 불타며 잿더미 지형으로 영구 변이됨.'
                impact['world_news'] = f'{state.player.name}의 대규모 화염 마법으로 인해 {current_region} 일대에 거대한 연기 기둥이 솟아올랐습니다.'
                impact['reputation_delta'] = -5
            elif '빙하' in current_region or '피오르드' in current_region:
                impact['terraforming'] = f'{current_region}의 영구 빙하가 급격히 녹아내려 숨겨진 고대 침몰 수로가 드러남.'
                impact['world_news'] = f'{current_region}의 빙하 붕괴로 인해 하류 해안 도시들의 수위가 상승했습니다.'

        elif dice_success and any(k in action for k in ['산성', '용해', '소화액']):
            if '성채' in current_region or '광산' in current_region:
                impact['terraforming'] = f'{current_region}의 견고한 암반과 성벽이 산성 화학 반응으로 녹아내려 새로운 지하 샛길이 뚫림.'

        return impact


class EcologicalVacuumCollapse:
    """
    Simulates trophic cascade & ecological collapse when apex predators or keystone monsters are eradicated.
    """
    @staticmethod
    def evaluate_vacuum_collapse(defeated_monster_name: str, current_region: str, state: Any) -> Optional[Dict[str, Any]]:
        m_lower = defeated_monster_name.lower()
        r_lower = current_region.lower()

        if any(k in m_lower for k in ['거미', '누에', '포식자', '사마귀']):
            return {
                'prey_surge': '흡혈 해충 및 독나방 떼의 기하급수적 개체수 폭증',
                'hazard_mutation': f'{current_region} 일대에 천적이 사라진 흡혈 파리 떼가 창궐하여 접근 불가능한 역병 위험 지대로 변이되었습니다.',
                'quest_impact': '의뢰인이 퀘스트 완료를 기뻐하기도 전에 역병 창궐로 플레이어를 원망함',
                'news': f'{current_region}의 최상위 포식자 토벌 이후 통제 불능의 해충 떼가 창궐해 인근 마을에 경보가 발령되었습니다.'
            }
        elif any(k in m_lower for k in ['히드라', '독사', '괴수', '지네', '침식충']):
            return {
                'prey_surge': '부패성 균류 및 맹독 박테리아 막 형성',
                'hazard_mutation': f'{current_region}의 지하 수로가 썩은 유기물로 막히며 유독성 폐수 역류가 시작되었습니다.',
                'quest_impact': '지하 통로 침수로 인해 이동 경로 봉쇄',
                'news': f'{current_region}의 거대 마수 사체 주변으로 맹독성 곰팡이가 번식하여 일대 식수가 오염되었습니다.'
            }
        return None
