import pytest
import json
from pathlib import Path
from src.core.config import TEMPLATES_DIR
from src.memory.memory_manager import MemoryManager
from src.world.generator import WorldGenerator
from src.world.state import WorldState, Player
from src.llm.base import BaseLLM

class DummyLLM(BaseLLM):
    def generate(self, prompt: str, system: str = '') -> str:
        return '{}'
    def generate_json(self, prompt: str, system: str = '') -> str:
        if '신규 지역' in prompt or 'DYNAMIC_REGION' in system:
            return json.dumps({
                'id': 'rag_magma_chamber',
                'name': '마그마 제련소 외곽',
                'description': '용암 폭포가 흐르는 거대한 지하 석실.',
                'environmental_hazards': ['극심한 열기'],
                'exits': {'돌아가기': 'start'},
                'items': [],
                'npcs': [],
                'is_point_of_no_return': False,
                'hidden_twist': '고대 골렘의 핵이 숨겨져 있음.',
                'ticking_clock': '용암 수위 상승'
            }, ensure_ascii=False)
        with open(TEMPLATES_DIR / 'world_template.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return json.dumps(data, ensure_ascii=False)

def test_region_templates_file_validity():
    template_file = TEMPLATES_DIR / 'region_templates.json'
    assert template_file.exists(), 'region_templates.json should exist'
    with open(template_file, 'r', encoding='utf-8') as f:
        templates = json.load(f)
    assert len(templates) == 30, f'Expected 30 templates, got {len(templates)}'
    for t in templates:
        assert 'id' in t
        assert 'name' in t
        assert 'environment' in t
        assert 'origin_event' in t
        assert 'hidden_twist' in t

def test_memory_manager_region_templates_rag():
    mm = MemoryManager()
    count = mm.index_region_templates()
    assert count == 30, f'Indexed {count} region templates'
    results = mm.search_region_templates('용암 폭포와 화염 대장간 골렘', limit=3)
    assert len(results) >= 1
    for r in results:
        assert 'name' in r
        assert 'environment' in r
        assert 'hidden_twist' in r

def test_world_generator_dynamic_region_rag():
    llm = DummyLLM()
    mm = MemoryManager()
    gen = WorldGenerator(llm, mm)
    state = WorldState(world_name='테스트 판타지', player=Player(location='start'))
    new_loc = gen.generate_dynamic_region(state, '용암 폭포 대장간')
    assert new_loc is not None
    assert new_loc['id'] == 'rag_magma_chamber'
    assert '마그마' in new_loc['name']
