import pytest
from src.world.generator import WorldGenerator
from src.world.state import WorldState
from src.llm.base import BaseLLM
from src.world.event_perspective import EventPerspectiveEngine


class DummyLLM(BaseLLM):
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return '{"narration": "테스트", "scene_image_prompt": "test"}'
    def generate_json(self, prompt: str, system_prompt: str = "") -> str:
        return '{"name": "테스트"}'


def test_cosmology_template_injection():
    llm = DummyLLM()
    generator = WorldGenerator(llm)
    world_data, intro_key = generator.generate_new_world()

    state = WorldState.from_dict(world_data)

    assert state.cosmology_template is not None
    assert isinstance(state.cosmology_template, dict)
    assert "world_name" in state.cosmology_template
    assert "era_background" in state.cosmology_template

    assert len(state.factions) >= 1
    for fac_id, faction in state.factions.items():
        assert faction.id == fac_id
        assert faction.name
        assert faction.system

    assert "loc_1" in state.locations
    start_loc = state.locations["loc_1"]
    assert len(start_loc.name) > 0
    assert len(start_loc.npcs) >= 1

    guide_npc_id = start_loc.npcs[0]
    assert guide_npc_id in state.npcs
    guide_npc = state.npcs[guide_npc_id]
    assert guide_npc.alive is True
    assert len(guide_npc.name) > 0
    assert len(guide_npc.job) > 0

    # Verify 12-axis perspective beliefs are injected
    assert len(guide_npc.beliefs) >= 1
    has_event_belief = any("에 대한 생각" in str(b) or "입장" in str(b) for b in guide_npc.beliefs)
    assert has_event_belief is True

    ctx_summary = state.to_context_summary()
    assert "WORLD STATE" in ctx_summary
    assert "GROUND TRUTH" in ctx_summary
    assert state.player.name in ctx_summary
    assert start_loc.name in ctx_summary
    assert "NPC Beliefs & Perspective Bias" in ctx_summary


def test_event_perspective_engine_resolution():
    """Verify that different NPC traits produce distinctly different beliefs."""
    cosmology = {
        "world_name": "에델가르드",
        "era_background": "발리리아 제국의 대화재 멸망 사건",
        "censored_history": "황제의 마지막 유언 말소"
    }

    # 1. Noble Scholar Elf Male
    npc_noble = {
        "job": "수석 대마법사",
        "tier": "legend",
        "education_level": "고등 아카데미",
        "visual": {"species": "하이 엘프", "gender": "남성"}
    }
    beliefs_noble = EventPerspectiveEngine.generate_event_beliefs(npc_noble, cosmology)
    assert any("지배귀족_영주" in b for b in beliefs_noble)
    assert any("장수종_엘프" in b for b in beliefs_noble)
    assert any("고등_아카데미_학자" in b for b in beliefs_noble)

    # 2. Peasant Illiterate Human Female
    npc_peasant = {
        "job": "노예 하녀",
        "tier": "commoner",
        "education_level": "완전 문맹",
        "visual": {"species": "인간", "gender": "여성"}
    }
    beliefs_peasant = EventPerspectiveEngine.generate_event_beliefs(npc_peasant, cosmology)
    assert any("농노_빈민_노예" in b for b in beliefs_peasant)
    assert any("생존_수호_여성" in b for b in beliefs_peasant)
    assert any("완전_문맹_무지자" in b for b in beliefs_peasant)
    assert any("순혈_인간" in b for b in beliefs_peasant)


def test_cosmology_serialization_roundtrip():
    llm = DummyLLM()
    generator = WorldGenerator(llm)
    world_data, _ = generator.generate_new_world()
    state1 = WorldState.from_dict(world_data)

    json_str = state1.to_json()
    state2 = WorldState.from_json(json_str)

    assert state2.world_name == state1.world_name
    assert state2.cosmology_template.get("id") == state1.cosmology_template.get("id")
    assert len(state2.factions) == len(state1.factions)
    assert len(state2.locations) == len(state1.locations)
