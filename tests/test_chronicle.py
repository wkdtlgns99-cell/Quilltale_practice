import pytest
import json
from pathlib import Path
from src.world.chronicle import ChronicleManager
from src.core.config import CHRONICLES_DIR

class DummyState:
    def __init__(self):
        self.world_genre = '판타지'
        self.turn = 100

def test_save_chronicle():
    state = DummyState()
    path = ChronicleManager.save_chronicle('test_world_id', '테스트세계', '용사', '옛날 옛적에...', state)
    assert path.exists()
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    assert data['world_id'] == 'test_world_id'
    assert data['world_name'] == '테스트세계'
    assert data['player_name'] == '용사'
    assert data['chronicle'] == '옛날 옛적에...'
    
def test_load_chronicles_for_world():
    chronicles = ChronicleManager.load_chronicles_for_world('test_world_id')
    assert len(chronicles) >= 1
    found = any(c['world_id'] == 'test_world_id' for c in chronicles)
    assert found is True

def test_get_library_entries():
    entries = ChronicleManager.get_library_entries()
    assert len(entries) >= 1
    found = any('[고대 기록: 테스트세계의 용사] 옛날 옛적에...' in e for e in entries)
    assert found is True
