import pytest
import json
from src.world.state import WorldState, Player, NPC, EnvironmentalMetrics, PendingInformation


def test_npc_bdi_and_attitude_matrix():
    npc = NPC(
        id="elric_alchemist",
        name="엘릭",
        description="연금술사",
        location="lab",
        desire="희귀 약초를 독점하여 딸의 병을 치료함",
        intention="플레이어에게 고래 뱃속 호수의 위험성을 숨기고 의뢰함",
        affinity=60,
        fear=20,
        debt=10,
        beliefs=["플레이어가 단순한 용병이라고 믿고 있음"]
    )
    assert npc.affinity == 60
    assert npc.fear == 20
    assert npc.debt == 10
    assert len(npc.beliefs) == 1
    assert "독점" in npc.desire


def test_player_injuries_and_traumas():
    player = Player(name="아서")
    player.injuries.append("오른팔 골절 (무기 명중률 -3)")
    player.traumas.append("화염 공포증")
    assert len(player.injuries) == 1
    assert len(player.traumas) == 1


def test_environmental_metrics_and_anchoring():
    env = EnvironmentalMetrics(
        weather="폭우",
        lighting="어두운 빗줄기",
        smell="물비린내",
        noise="천둥 번개",
        oxygen_level=90,
        time_of_day="심야"
    )
    anchoring_text = env.to_anchoring_text()
    assert "폭우" in anchoring_text
    assert "심야" in anchoring_text
    assert "산소 농도: 90%" in anchoring_text


def test_information_travel_delay_waves():
    state = WorldState(world_name="테스트 대륙")
    npc_a = NPC(id="guard_bob", name="밥", description="경비병", location="gate")
    npc_b = NPC(id="boss_gordon", name="고든", description="암흑가 수장", location="mansion")
    state.npcs["guard_bob"] = npc_a
    state.npcs["boss_gordon"] = npc_b

    # Add a delayed info wave (2 turns)
    state.pending_info_waves.append(PendingInformation(
        event_desc="관문 경비병 암살 사건",
        origin_location="gate",
        target_npcs=["boss_gordon"],
        remaining_turns=2
    ))

    # Turn 1: Should not have arrived yet
    propagated_1 = state.advance_information_waves()
    assert len(propagated_1) == 0
    assert len(npc_b.beliefs) == 0

    # Turn 2: Arrives!
    propagated_2 = state.advance_information_waves()
    assert len(propagated_2) == 1
    assert "관문 경비병 암살 사건" in propagated_2[0]
    assert any("관문 경비병 암살 사건" in b for b in npc_b.beliefs)
    assert any("관문 경비병 암살 사건" in f for f in state.world_facts)


def test_apply_update_deep_realism_deltas():
    state = WorldState(world_name="테스트 대륙")
    npc = NPC(id="merchant_kyle", name="카일", description="상인", location="shop")
    state.npcs["merchant_kyle"] = npc

    delta_update = {
        "update_npc_attitude": {"merchant_kyle": {"affinity": 15, "fear": 20, "debt": -30}},
        "add_npc_belief": {"merchant_kyle": "플레이어가 도적단을 소탕한 영웅이라고 믿음"},
        "update_npc_bdi": {"merchant_kyle": {"desire": "안전한 상단 보호", "intention": "할인 혜택 제공"}},
        "add_player_injury": "갈비뼈 실금 (체력 회복 속도 저하)",
        "add_player_trauma": "산성 액체 트라우마",
        "update_environment_metrics": {"weather": "산성비", "oxygen_level": 75},
        "queue_information_wave": {"event_desc": "도적단 괴멸", "delay_turns": 1}
    }

    changes = state.apply_update(delta_update)
    assert npc.affinity == 65  # 50 + 15
    assert npc.fear == 20      # 0 + 20
    assert npc.debt == -30     # 0 - 30
    assert any("영웅" in b for b in npc.beliefs)
    assert npc.desire == "안전한 상단 보호"
    assert "갈비뼈 실금" in state.player.injuries[0]
    assert "산성 액체" in state.player.traumas[0]
    assert state.environment.weather == "산성비"
    assert state.environment.oxygen_level == 75
    assert len(state.pending_info_waves) == 1


def test_serialization_roundtrip_deep_realism():
    state = WorldState(world_name="리얼리즘 테스트")
    state.environment.weather = "농무"
    state.player.injuries.append("눈가 흉터")
    npc = NPC(id="n1", name="마르타", description="주인", location="start", affinity=75, fear=10, debt=50)
    npc.beliefs.append("플레이어를 신뢰함")
    state.npcs["n1"] = npc

    json_str = state.to_json()
    reloaded = WorldState.from_json(json_str)

    assert reloaded.environment.weather == "농무"
    assert "눈가 흉터" in reloaded.player.injuries
    assert reloaded.npcs["n1"].affinity == 75
    assert reloaded.npcs["n1"].fear == 10
    assert reloaded.npcs["n1"].debt == 50
    assert "플레이어를 신뢰함" in reloaded.npcs["n1"].beliefs
