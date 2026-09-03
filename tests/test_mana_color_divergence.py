import pytest
from src.world.state import WorldState, Location, NPC, Player, Skill
from src.agents.game_master import GameMasterAgent
from src.llm.base import BaseLLM, LLMResponse


class DummyLLM(BaseLLM):
    def generate(self, prompt: str, system: str = "") -> LLMResponse:
        return LLMResponse(content='{"narration": "테스트"}')
    def generate_json(self, prompt: str, system: str = "") -> str:
        return '{"narration": "테스트"}'


def test_skill_visual_description_divergence():
    fireball = Skill(
        id="fireball",
        name="작열 화염구",
        element="화염",
        color="#ef4444",
        visual_fx_description="거대한 화염 구체가 폭발합니다."
    )

    # 1. Default caster is None
    default_desc = fireball.get_visual_description(None)
    assert "거대한 화염 구체" in default_desc

    # 2. Player with cold blue mana
    player = Player(name="아르테미스")
    player.mana_color = "시퍼런 냉기의 청염"
    player_desc = fireball.get_visual_description(player)
    assert "아르테미스" in player_desc
    assert "시퍼런 냉기의 청염" in player_desc
    assert "작열 화염구" in player_desc

    # 3. NPC with dark purple cursed mana
    npc = NPC(id="npc_witch", name="흑마녀 모르가나", description="", location="dungeon")
    npc.mana_color = "심연의 칠흑빛 암전"
    npc_desc = fireball.get_visual_description(npc)
    assert "모르가나" in npc_desc
    assert "심연의 칠흑빛 암전" in npc_desc


def test_game_master_bdi_and_skills_mana_color_injection():
    state = WorldState()
    state.player.name = "로랜드"
    state.player.mana_color = "백금빛 신성 에테르"

    slash = Skill(id="slash", name="일도양단", element="물리", color="#94a3b8")
    state.skills_db["slash"] = slash
    state.player.skills = ["slash"]

    loc = Location(id="loc1", name="성당", description="", exits={})
    state.locations["loc1"] = loc
    state.player.location = "loc1"

    npc = NPC(id="npc1", name="성기사 가웨인", description="", location="loc1")
    npc.mana_color = "찬란한 태양빛 황금 마나"
    state.npcs["npc1"] = npc

    gm = GameMasterAgent(llm=DummyLLM())

    # Check BDI context
    bdi_ctx = gm._format_bdi_context(state, ["npc1"])
    assert "개인 마나 고유색/오라 특성: [찬란한 태양빛 황금 마나]" in bdi_ctx

    # Check player skills context
    skills_ctx = gm._format_skills_context(state)
    assert "백금빛 신성 에테르" in skills_ctx
    assert "로랜드" in skills_ctx
