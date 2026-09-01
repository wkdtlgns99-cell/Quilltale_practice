import pytest
from src.world.state import WorldState, Location, NPC, Player, Item
from src.world.audio_engine import AudioEngine
from src.world.two_pass_engine import DeterministicFactSheet


def create_test_state() -> WorldState:
    loc = Location(
        id="loc_tavern",
        name="달빛 선술집",
        description="따뜻한 모닥불과 취객들의 웅성거림이 가득한 선술집",
        exits={"north": "loc_street"},
        npcs=["npc_barkeep"]
    )
    npc = NPC(
        id="npc_barkeep",
        name="주점 주인 톰",
        description="술잔을 닦고 있는 선술집 주인",
        location="loc_tavern",
        health=40,
        max_health=40,
        disposition="neutral",
        alive=True
    )
    player = Player(
        name="테스트용병",
        titles=["방랑자"],
        active_title="방랑자",
        location="loc_tavern",
        health=100,
        max_health=100,
        mana=50,
        max_mana=50,
        inventory=["item_potion"],
        strength=12,
        agility=12,
        constitution=12,
        intelligence=12,
        wisdom=12,
        luck=12,
        reputation=0
    )
    state = WorldState(
        session_id="test_audio_session",
        player=player,
        locations={"loc_tavern": loc},
        npcs={"npc_barkeep": npc},
        items={}
    )
    return state


def test_audio_templates_loading():
    templates = AudioEngine.load_templates()
    assert "bgm_tracks" in templates
    assert "sfx_cues" in templates
    assert len(templates["bgm_tracks"]) >= 5
    assert len(templates["sfx_cues"]) >= 10


def test_audio_engine_tavern_bgm():
    state = create_test_state()
    audio_res = AudioEngine.determine_turn_audio(state, action="주인에게 술 한 잔을 주문한다")
    
    assert audio_res["current_bgm"] is not None
    assert audio_res["current_bgm"]["id"] == "bgm_tavern_warmth"


def test_audio_engine_combat_and_sfx_trigger():
    state = create_test_state()
    # Add hostile enemy
    hostile_npc = NPC(
        id="npc_goblin",
        name="광폭한 고블린",
        description="도끼를 든 흉악한 고블린",
        location="loc_tavern",
        health=30,
        max_health=30,
        disposition="hostile",
        alive=True
    )
    state.npcs["npc_goblin"] = hostile_npc
    state.locations["loc_tavern"].npcs.append("npc_goblin")

    fact_sheet = DeterministicFactSheet(
        action="검으로 고블린을 베어버린다",
        dice_result={
            "action_type": "combat",
            "is_success": True,
            "is_critical_success": True,
            "summary_ko": "치명타 성공"
        },
        combat_outcome={
            "damage_dealt": 35,
            "killed": True,
            "hp_after": 0
        }
    )

    audio_res = AudioEngine.determine_turn_audio(state, fact_sheet=fact_sheet, action="검으로 고블린을 베어버린다")
    
    # Combat BGM check
    assert audio_res["current_bgm"]["id"] == "bgm_combat_blades"
    
    # SFX triggers check
    sfx_ids = [s["id"] for s in audio_res["triggered_sfx"]]
    assert "sfx_dice_roll" in sfx_ids
    assert "sfx_critical_hit" in sfx_ids
    assert "sfx_death_groan" in sfx_ids
    assert "sfx_sword_slash" in sfx_ids


def test_audio_engine_magic_sfx():
    state = create_test_state()
    audio_res = AudioEngine.determine_turn_audio(state, action="이그니스 화염구를 발사한다")
    sfx_ids = [s["id"] for s in audio_res["triggered_sfx"]]
    assert "sfx_fireball_cast" in sfx_ids


def test_audio_engine_html_formatting():
    state = create_test_state()
    audio_res = AudioEngine.determine_turn_audio(state, action="금화를 주고 치유 포션을 구매한다")
    html = AudioEngine.format_audio_html(audio_res)
    
    assert "🎵" in html
    assert "따뜻한 선술집의 불빛" in html
    assert "금화 짤랑임" in html or "치유" in html
