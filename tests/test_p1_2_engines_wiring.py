"""
Integration tests for P1-2: Wiring 3 previously unreachable engines into live turn path.
1. MerchantBarterEngine (barter, relic appraisal, coin clipping, smuggling, regional arbitrage)
2. CombatDistanceManager & ActionTimeTrackEngine (meter distance, zones, approach/retreat, Option A perception interrupt)
3. SiegeWarfareEngine (fortress multi-layer durability, artillery phase, breach clash, commando infiltration)
"""
import pytest
from src.world.state import WorldState, Player, Item, NPC, Location
from src.world.two_pass_engine import TwoPassEngine
from src.world.infrastructure import Settlement
from src.world.combat_time_track_engine import CombatDistanceManager


@pytest.fixture
def base_world_state():
    state = WorldState()
    player = Player(
        name="영웅",
        health=100,
        max_health=100,
        mana=50,
        max_mana=50,
        gold=200,
        location="loc_town",
        perception=16,
        strength=14,
        agility=14,
        intelligence=12
    )
    player.stats = {"strength": 14, "dexterity": 14, "intelligence": 12, "perception": 16, "charisma": 14}
    state.player = player

    loc = Location(
        id="loc_town",
        name="평원의 관문 마을",
        description="상인들과 모험가들이 북적이는 교역 거점 마을.",
        terrain="plains_farm",
        npcs=["npc_merchant", "npc_bandit"],
        exits={"east": "loc_forest"}
    )
    state.locations["loc_town"] = loc
    state.current_location_id = "loc_town"

    merchant = NPC(
        id="npc_merchant",
        name="호박석 상인 길버트",
        description="이곳저곳을 누비는 노련한 상인.",
        location="loc_town",
        disposition="friendly"
    )
    bandit = NPC(
        id="npc_bandit",
        name="붉은 도적단 두목",
        description="험상궂은 인상의 도적 두목.",
        location="loc_town",
        disposition="hostile"
    )
    state.npcs["npc_merchant"] = merchant
    state.npcs["npc_bandit"] = bandit

    # Items for barter & appraisal
    item_relic = Item(
        id="item_old_dagger",
        name="흙 묻은 고대 쇠붙이",
        description="정체불명의 녹슨 단검 형태 유물.",
        location="inventory",
        value=10,
        traits=["unidentified", "relic"],
        is_identified=False
    )
    item_salt = Item(
        id="item_rock_salt",
        name="정제 암염 한 자루",
        description="교역용 고급 소금.",
        location="inventory",
        value=40,
        traits=["trade_good"]
    )
    state.items["item_old_dagger"] = item_relic
    state.items["item_rock_salt"] = item_salt
    player.inventory.extend(["item_old_dagger", "item_rock_salt"])

    return state


def test_merchant_barter_engine_live_pass1(base_world_state):
    """Verify barter, appraisal, coin clipping, smuggling, and regional prices in Pass 1."""
    state = base_world_state

    # 1. Barter Exchange
    fs_barter = TwoPassEngine.compute_pass1("상인과 소금 자루를 건네고 물물교환을 진행한다", state)
    assert fs_barter.is_valid is True
    assert fs_barter.barter_summary is not None
    assert "물물교환" in fs_barter.barter_summary
    prompt_ctx = fs_barter.to_prompt_context()
    assert "[물물교환 / 유물 감정 / 암시장 금융 판정 (Barter & Trade)]" in prompt_ctx

    # 2. Relic Appraisal
    initial_gold = state.player.gold
    fs_appraise = TwoPassEngine.compute_pass1("상인에게 유물 감정을 의뢰한다", state)
    assert fs_appraise.is_valid is True
    assert fs_appraise.barter_summary is not None
    assert "감정 성공" in fs_appraise.barter_summary
    assert state.player.gold == initial_gold - 30
    appraised_item = state.items["item_old_dagger"]
    assert appraised_item.name == "고대 성자의 축복받은 은장도"
    assert appraised_item.value == 350
    assert appraised_item.is_identified is True

    # 3. Coin Clipping
    fs_clip = TwoPassEngine.compute_pass1("상인의 눈을 피해 금화 깎기를 시도한다", state)
    assert fs_clip.is_valid is True
    assert fs_clip.barter_summary is not None
    assert "금화 깎기" in fs_clip.barter_summary or "사기" in fs_clip.barter_summary

    # 4. Regional Price Check
    fs_price = TwoPassEngine.compute_pass1("이 마을 시장의 시세와 물가를 조사한다", state)
    assert fs_price.is_valid is True
    assert fs_price.barter_summary is not None
    assert "소금" in fs_price.barter_summary and "시세표" in fs_price.barter_summary

    # 5. Smuggling Inspection
    contraband_item = Item(
        id="item_darkweed",
        name="암흑초 추출액",
        description="치명적인 제국 금지 마약.",
        location="inventory",
        value=500,
        traits=["contraband", "darkweed"]
    )
    state.items["item_darkweed"] = contraband_item
    state.player.inventory.append("item_darkweed")
    fs_smuggle = TwoPassEngine.compute_pass1("성문 경비대 앞에서 밀수를 시도하며 검문소를 지난다", state)
    assert fs_smuggle.is_valid is True
    assert fs_smuggle.barter_summary is not None
    assert "검문" in fs_smuggle.barter_summary or "밀수" in fs_smuggle.barter_summary


def test_combat_distance_and_perception_interrupt_live_pass1(base_world_state):
    """Verify meter combat distance manager and Option A perception interrupt in Pass 1."""
    state = base_world_state
    player_id = getattr(state.player, "id", getattr(state.player, "name", "player"))
    enemy_id = "npc_bandit"

    # Set initial distance
    CombatDistanceManager.set_distance(state, player_id, enemy_id, 15.0)
    assert CombatDistanceManager.get_distance(state, player_id, enemy_id) == 15.0
    assert "중거리" in CombatDistanceManager.get_distance_zone_ko(15.0)

    # 1. Move Towards (돌진/접근)
    fs_charge = TwoPassEngine.compute_pass1("적을 향해 칼을 빼들고 돌진한다", state)
    assert fs_charge.is_valid is True
    assert fs_charge.combat_distance_summary is not None
    assert "대치 거리" in fs_charge.combat_distance_summary
    new_dist = CombatDistanceManager.get_distance(state, player_id, enemy_id)
    assert new_dist < 15.0  # Distance decreased

    # Check prompt context
    prompt_ctx = fs_charge.to_prompt_context()
    assert "[미터 기반 상대 교전 거리 (Combat Distance Zone)]" in prompt_ctx

    # 2. Move Away (거리 벌리기/후퇴)
    prev_dist = new_dist
    fs_retreat = TwoPassEngine.compute_pass1("적의 사거리 밖으로 거리 벌리기를 하며 뒤로 물러선다", state)
    assert fs_retreat.is_valid is True
    assert fs_retreat.combat_distance_summary is not None
    after_retreat_dist = CombatDistanceManager.get_distance(state, player_id, enemy_id)
    assert after_retreat_dist > prev_dist  # Distance increased

    # 3. Option A Perception Interrupt Check
    # High PER player (PER 16 -> modifier +3) reacting to attack
    CombatDistanceManager.set_distance(state, player_id, enemy_id, 8.0)
    fs_interrupt = TwoPassEngine.compute_pass1("적과 대치하며 전투 공격을 감행한다", state)
    assert fs_interrupt.is_valid is True
    assert fs_interrupt.combat_distance_summary is not None
    if fs_interrupt.interrupt_event:
        assert "narrative_ko" in fs_interrupt.interrupt_event
        assert "options_ko" in fs_interrupt.interrupt_event
        prompt_with_interrupt = fs_interrupt.to_prompt_context()
        assert "[A안 위기 인지 인터럽트 (Perception Interrupt Reaction)]" in prompt_with_interrupt


def test_siege_warfare_engine_live_pass1(base_world_state):
    """Verify fortress multi-layer defense, siege turn advance, and commando infiltration in Pass 1."""
    state = base_world_state
    from src.world.infrastructure import InfrastructureRegistry
    state.infrastructure = InfrastructureRegistry()

    settlement = Settlement(
        id="settlement_iron_gate",
        name="아이언게이트 성채",
        nation_id="nat_1",
        region_id="reg_1",
        wall_defense_tier=2
    )
    state.infrastructure.settlements[settlement.id] = settlement
    state.current_location().settlement_id = settlement.id

    # 1. Artillery Siege Bombardment Turn Advance
    fs_siege = TwoPassEngine.compute_pass1("투석기와 트레뷰셋을 동원해 성벽 공격과 포격을 개시한다", state)
    assert fs_siege.is_valid is True
    assert fs_siege.siege_summary is not None
    assert "공성전" in fs_siege.siege_summary or "성벽" in fs_siege.siege_summary
    assert "active_sieges" in fs_siege.pre_computed_state_delta or len(state.active_sieges) > 0

    prompt_ctx = fs_siege.to_prompt_context()
    assert "[대규모 공성전 및 요새 방호 시뮬레이션 (Siege Warfare)]" in prompt_ctx

    # 2. Commando Special Infiltration Action (별동대 침투 작전)
    fs_commando = TwoPassEngine.compute_pass1("별동대를 이끌고 야간에 성문 열기 침투 작전을 결행한다", state)
    assert fs_commando.is_valid is True
    assert fs_commando.siege_summary is not None
    assert "특공" in fs_commando.siege_summary or "성문" in fs_commando.siege_summary


def test_game_master_agent_process_turn_p1_2_integration(base_world_state):
    """Verify live turn execution through GameMasterAgent.process_turn for P1-2 features."""
    from src.agents.game_master import GameMasterAgent
    from src.llm.base import BaseLLM

    class DummyLLM(BaseLLM):
        def generate(self, prompt: str, system_prompt: str = "") -> str:
            return '{"narration": "호박석 상인 길버트와 성공적으로 물물교환을 마쳤습니다.", "scene_image_prompt": "market barter scene"}'

        def generate_json(self, prompt: str, system_prompt: str = "") -> str:
            return '{"narration": "호박석 상인 길버트와 성공적으로 물물교환을 마쳤습니다."}'

    llm = DummyLLM()
    gm = GameMasterAgent(llm)
    state = base_world_state

    # Execute barter turn through GameMasterAgent
    result = gm.process_turn("상인과 소금 자루를 건네고 물물교환을 진행한다", state)
    assert result is not None
    assert "narration" in result
    assert state.turn > 0 or len(state.history) > 0

