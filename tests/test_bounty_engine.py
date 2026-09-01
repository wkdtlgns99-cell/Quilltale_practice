import pytest
from src.world.state import WorldState, Location, Player, NPC, Faction
from src.world.bounty_engine import BountyEngine


def test_bounty_add_and_wanted_notice():
    state = WorldState(
        session_id="test_bounty_session",
        player=Player(name="수배자"),
        factions={"fac_royal": Faction(id="fac_royal", name="로열 가드")}
    )

    msg = BountyEngine.add_bounty(state, "fac_royal", 1000, "상단 마차 습격")
    assert "1000G" in msg
    assert state.player.bounties["fac_royal"] == 1000
    assert len(state.bounties_board) == 1
    assert state.bounties_board[0]["crime"] == "상단 마차 습격"


def test_bounty_guard_inspection_with_disguise():
    state = WorldState(
        session_id="test_bounty_session",
        player=Player(name="수배자", bounties={"fac_royal": 1200}, disguise="까마귀 가면과 로브", active_alias="그림자 신사"),
        factions={"fac_royal": Faction(id="fac_royal", name="로열 가드")}
    )
    guard = NPC(id="npc_guard", name="성문 경비병", description="검문 중인 경비병", location="gate", faction_id="fac_royal")

    # With disguise: passes inspection
    is_busted, msg = BountyEngine.check_guard_inspection(state, guard)
    assert is_busted is False
    assert "위장 성공" in msg

    # Remove disguise: gets busted
    state.player.disguise = None
    is_busted, msg = BountyEngine.check_guard_inspection(state, guard)
    assert is_busted is True
    assert "수배자 발각" in msg


def test_bounty_hunter_ambush():
    state = WorldState(
        session_id="test_bounty_session",
        player=Player(name="수배자", bounties={"fac_royal": 1500})
    )

    ambush = BountyEngine.check_bounty_hunter_ambush(state, "도시 외곽 숲으로 이동한다")
    assert ambush is not None
    assert "현상금 사냥꾼" in ambush["summary_ko"]
