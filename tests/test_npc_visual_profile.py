import pytest
from src.world.state import WorldState, Location, NPC, Player, NPCVisualDetails


def test_npc_visual_profile_defaults():
    npc = NPC(
        id="npc_alicia",
        name="약초사 알리시아",
        description="숲속 오두막에서 약초를 달이는 엘프 소녀 약초사",
        location="loc_hut",
        visual=NPCVisualDetails(
            species="엘프",
            life_stage="청소년 소녀",
            build_archetype="왜소하고 가냘픈 체형",
            height_cm=158,
            age_apparent="10대 중반",
            gender="여성",
            hair_color="백금발",
            hair_style="어깨 위로 땋아 내린 헤어스타일",
            eye_color="연보라색(Amethyst)",
            eye_shape="크고 순한 눈매",
            skin_tone="창백하고 투명한 백옥 피부",
            facial_features=["콧등의 옅은 주근깨", "왼쪽 뺨의 작은 점"],
            clothing_style="약초 얼룩이 묻은 린넨 원피스와 초록색 모직 망토",
            distinctive_accessories=["유리 물약병이 달린 가죽 허리띠", "은색 약초 가위"],
            posture_and_vibe="호기심 어린 눈빛으로 차분하게 약초를 다듬는 모습"
        ),
        blackmail_secret="사실 성국에서 금지된 마녀의 금서 '달빛 약초지'를 몰래 숨겨두고 연구하고 있음"
    )

    # Korean sensory summary test
    summary_ko = npc.to_korean_visual_summary()
    assert "엘프" in summary_ko
    assert "청소년 소녀" in summary_ko
    assert "158cm" in summary_ko
    assert "백금발" in summary_ko
    assert "콧등의 옅은 주근깨" in summary_ko
    assert "연보라색" in summary_ko

    # Image prompt keywords test for Flux / Stable Diffusion
    prompt_en = npc.to_image_prompt_keywords()
    assert "cinematic fantasy portrait" in prompt_en
    assert "엘프" in prompt_en
    assert "청소년 소녀" in prompt_en
    assert "158cm" in prompt_en
    assert "masterpiece, 8k" in prompt_en


def test_npc_visual_profile_serialization():
    loc = Location(id="loc_hut", name="약초 오두막", description="풀향기가 가득한 오두막", exits={})
    npc = NPC(
        id="npc_alicia",
        name="약초사 알리시아",
        description="숲속 약초사",
        location="loc_hut",
        visual=NPCVisualDetails(
            age_apparent="20대 초반",
            gender="여성",
            hair_color="백금발",
            eye_color="연보라색",
            facial_features=["주근깨", "뺨의 점"]
        ),
        blackmail_secret="금지된 마녀의 비전서 은닉"
    )
    player = Player(name="방랑자", location="loc_hut")
    state = WorldState(
        session_id="test_visual_session",
        player=player,
        locations={"loc_hut": loc},
        npcs={"npc_alicia": npc}
    )

    # Round trip JSON
    raw_json = state.to_json()
    loaded_state = WorldState.from_json(raw_json)

    loaded_npc = loaded_state.npcs["npc_alicia"]
    assert loaded_npc.visual.hair_color == "백금발"
    assert loaded_npc.visual.eye_color == "연보라색"
    assert "주근깨" in loaded_npc.visual.facial_features
    assert loaded_npc.blackmail_secret == "금지된 마녀의 비전서 은닉"
