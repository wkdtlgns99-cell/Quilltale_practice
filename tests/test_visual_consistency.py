"""
Unit tests for Visual Consistency Anchor System in Quilltale TRPG.
Tests:
1. FacialDetails (eyelids, eyelashes, eyebrows, nose bridge, lips, cheeks/jaw, ears).
2. BodyMeasurements (head ratio, shoulder width, bust size, waist-hip ratio S-curve, leg length, muscle definition).
3. ClothingLayer extensions (fabric materials, color palette, fit silhouette, inner silhouette reveal).
4. ItemVisualProfile (blade shape, guard/hilt, damascus finish, ethereal aura, scabbard, wear condition).
5. NPC & Player visual integration and prompt generation.
6. OutfitMechanicsEngine.build_consistent_character_prompt unified anchor generation.
7. Save/Load JSON serialization and backward compatibility.
"""
import pytest
from src.world.state import (
    WorldState, Location, NPC, Player, Item, EquipmentSlots,
    NPCVisualDetails, ClothingLayer, FacialDetails, BodyMeasurements, ItemVisualProfile
)
from src.world.outfit_engine import OutfitMechanicsEngine


def test_facial_details_korean_summary_and_prompt_keywords():
    """Validates granular micro-facial feature anchoring."""
    face = FacialDetails(
        eye_lids="인아웃라인 쌍꺼풀",
        eye_lashes="길고 짙은 속눈썹",
        eyebrows="단정한 완만한 아치형",
        nose_bridge="오똑하고 곧은 높은 콧대",
        lips_and_mouth="도톰하고 붉은 앵두 입술",
        cheeks_and_jaw="통통한 볼살(젖살)",
        ear_shape="끝이 뾰족한 엘프형 귀"
    )

    # Korean summary check
    ko_sum = face.to_korean_summary()
    assert "콧대: 오똑하고 곧은 높은 콧대" in ko_sum
    assert "단정한 완만한 아치형" in ko_sum
    assert "인아웃라인 쌍꺼풀" in ko_sum
    assert "도톰하고 붉은 앵두 입술" in ko_sum
    assert "통통한 볼살(젖살)" in ko_sum
    assert "끝이 뾰족한 엘프형 귀" in ko_sum

    # English prompt keywords check
    en_kw = face.to_prompt_keywords()
    assert "delicate in-out double eyelids" in en_kw
    assert "long dark eyelashes" in en_kw
    assert "neat arched eyebrows" in en_kw
    assert "high defined straight nose bridge" in en_kw
    assert "plump reddish cherry lips" in en_kw
    assert "soft youthful round cheeks with baby fat" in en_kw
    assert "pointed elven ears" in en_kw

    # Mandatory traits check
    assert len(face.traits) > 0
    assert "이목구비" in face.traits


def test_body_measurements_korean_summary_and_prompt_keywords():
    """Validates body proportions, bust size, and waist-hip ratio (S-curve)."""
    body = BodyMeasurements(
        head_ratio=7.5,
        shoulder_width="가냘프고 좁은 어깨",
        bust_size="풍만한 볼륨감(D~E컵)",
        waist_hip_ratio="잘록한 허리와 도드라진 골반 S라인(WHR 0.68)",
        leg_length_ratio="상하체 4:6 비율의 긴 롱다리",
        muscle_definition="린매스(슬림 근육)"
    )

    # Korean summary check
    ko_sum = body.to_korean_summary()
    assert "7.5등신" in ko_sum
    assert "어깨: 가냘프고 좁은 어깨" in ko_sum
    assert "흉부: 풍만한 볼륨감(D~E컵)" in ko_sum
    assert "골반/허리: 잘록한 허리와 도드라진 골반 S라인(WHR 0.68)" in ko_sum
    assert "다리비율: 상하체 4:6 비율의 긴 롱다리" in ko_sum
    assert "근육: 린매스(슬림 근육)" in ko_sum

    # English prompt keywords check
    en_kw = body.to_prompt_keywords()
    assert "7.5 head-to-body proportion" in en_kw
    assert "narrow delicate shoulders" in en_kw
    assert "voluptuous well-endowed bust" in en_kw or "full bust size D-cup" in en_kw
    assert "hourglass figure with narrow waist and curvy hips (0.68 WHR)" in en_kw
    assert "long slender legs with 4:6 upper-to-lower body ratio" in en_kw
    assert "lean toned physique" in en_kw

    # Mandatory traits check
    assert len(body.traits) > 0
    assert "신체 치수" in body.traits


def test_clothing_layer_innerwear_silhouette_reveal():
    """Validates user-requested faint innerwear line visibility under skin-tight garments."""
    # 1. Faint underwear line
    outfit_faint = ClothingLayer(
        base_upper="스킨타이트 실크 셔츠",
        fit_silhouette="몸에 밀착되는 슬림핏/스킨타이트",
        inner_silhouette_reveal="faint_underwear_line"
    )
    ko_sum = outfit_faint.to_korean_summary()
    en_kw = outfit_faint.to_prompt_keywords()
    assert "비침: 얇고 밀착된 옷감 너머 은은한 속옷 라인" in ko_sum
    assert "skin-tight form-fitting silhouette" in en_kw
    assert "faint underwear seam line visible through form-fitting fabric" in en_kw

    # 2. Subtle bra contour
    outfit_bra = ClothingLayer(
        base_upper="밀착 리브 니트",
        inner_silhouette_reveal="subtle_bra_contour"
    )
    assert "비침: 딱 붙는 상의 위로 은근하게 드러나는 브라 윤곽" in outfit_bra.to_korean_summary()
    assert "subtle contour of innerwear bra straps visible under skin-tight top" in outfit_bra.to_prompt_keywords()

    # 3. Visible panty line
    outfit_panty = ClothingLayer(
        base_lower="가죽 스키니 팬츠",
        inner_silhouette_reveal="visible_panty_line"
    )
    assert "비침: 달라붙는 하의 위로 살짝 드러나는 팬티 라인" in outfit_panty.to_korean_summary()
    assert "subtle panty line contour showing through tight leggings" in outfit_panty.to_prompt_keywords()

    # 4. Corset ribs ridge
    outfit_corset = ClothingLayer(
        outerwear="이브닝 드레스",
        inner_silhouette_reveal="corset_ribs_ridge"
    )
    assert "비침: 의상 위로 비치는 코르셋 뼈대 굴곡 자국" in outfit_corset.to_korean_summary()
    assert "faint corset boning ridges showing under dress" in outfit_corset.to_prompt_keywords()


def test_item_visual_profile_weapon_anatomy():
    """Validates weapon visual modeling: blade, hilt, damascus finish, aura, scabbard."""
    weapon_vis = ItemVisualProfile(
        blade_or_head="혈조가 파인 양날 직검",
        guard_and_hilt="황동 사자 머리 가드와 흑가죽 손잡이",
        finish_and_material="물결치는 다마스쿠스 강철 무늬",
        glow_or_aura="칼날을 타고 흐르는 은은한 푸른빛 에테르 기운",
        sheath_appearance="놋쇠 띠를 두른 흑가죽 칼집",
        wear_condition="면도날처럼 시퍼렇게 연마된 날"
    )

    ko_sum = weapon_vis.to_korean_summary()
    assert "날/헤드: 혈조가 파인 양날 직검" in ko_sum
    assert "가드/손잡이: 황동 사자 머리 가드와 흑가죽 손잡이" in ko_sum
    assert "재질: 물결치는 다마스쿠스 강철 무늬" in ko_sum
    assert "오라: 칼날을 타고 흐르는 은은한 푸른빛 에테르 기운" in ko_sum
    assert "칼집: 놋쇠 띠를 두른 흑가죽 칼집" in ko_sum
    assert "상태: 면도날처럼 시퍼렇게 연마된 날" in ko_sum

    en_kw = weapon_vis.to_prompt_keywords()
    assert "double-edged straight blade with deep fuller groove" in en_kw
    assert "lion-headed ornate brass crossguard and leather-wrapped hilt" in en_kw
    assert "flowing damascus steel wave patterns" in en_kw
    assert "ethereal faint blue aura radiating along the blade" in en_kw
    assert "black leather scabbard with brass fittings" in en_kw
    assert "razor-sharp polished edge" in en_kw

    # Item binding & tooltip test
    item = Item(
        id="wep_damascus_sword",
        name="사자왕의 다마스쿠스 장검",
        description="고대 사자 문양이 새겨진 명품 검",
        location="inventory",
        item_type="weapon",
        damage=25,
        visual=weapon_vis
    )
    assert "사자왕의 다마스쿠스 장검" in item.to_korean_visual_summary()
    assert "다마스쿠스 강철" in item.to_korean_visual_summary()
    assert "flowing damascus steel wave patterns" in item.to_image_prompt_keywords()
    assert "조형:" in item.tooltip_text


def test_npc_and_player_visual_integration():
    """Validates NPC and Player to_korean_visual_summary and to_image_prompt_keywords."""
    npc = NPC(
        id="npc_seraphina",
        name="세라피나",
        description="성왕국 기사단장",
        location="loc_citadel",
        visual=NPCVisualDetails(
            species="인간",
            life_stage="성인 여성",
            build_archetype="탄탄하고 슬림한 체형",
            height_cm=172,
            age_apparent="20대 중반",
            gender="여성",
            hair_color="은발",
            hair_style="포니테일",
            eye_color="청람색",
            eye_shape="날렵하고 또렷한 눈매",
            skin_tone="결 고운 하얀 피부",
            face_details=FacialDetails(
                eye_lids="인아웃라인 쌍꺼풀",
                eye_lashes="길고 짙은 속눈썹",
                eyebrows="날카로운 일자 눈썹",
                nose_bridge="오똑하고 곧은 높은 콧대",
                lips_and_mouth="도톰하고 붉은 앵두 입술",
                cheeks_and_jaw="갸름하고 날렵한 V라인 턱선"
            ),
            body_measurements=BodyMeasurements(
                head_ratio=8.0,
                shoulder_width="자연스러운 표준 어깨",
                bust_size="풍만한 볼륨감(D~E컵)",
                waist_hip_ratio="잘록한 허리와 도드라진 골반 S라인(WHR 0.68)",
                leg_length_ratio="상하체 4:6 비율의 긴 롱다리",
                muscle_definition="선명한 복근과 잔근육"
            ),
            outfit=ClothingLayer(
                outerwear="백은의 성기사 흉갑",
                fit_silhouette="몸에 밀착되는 슬림핏/스킨타이트",
                inner_silhouette_reveal="faint_underwear_line"
            )
        )
    )

    ko_sum = npc.to_korean_visual_summary()
    assert "세라피나" in npc.name
    assert "172cm" in ko_sum
    assert "8.0등신" in ko_sum
    assert "오똑하고 곧은 높은 콧대" in ko_sum
    assert "비침: 얇고 밀착된 옷감 너머 은은한 속옷 라인" in ko_sum

    en_kw = npc.to_image_prompt_keywords()
    assert "cinematic fantasy portrait" in en_kw
    assert "172cm" in en_kw
    assert "8.0 head-to-body proportion" in en_kw
    assert "delicate in-out double eyelids" in en_kw
    assert "high defined straight nose bridge" in en_kw
    assert "faint underwear seam line visible through form-fitting fabric" in en_kw

    # Player test
    player = Player(
        name="아리아",
        visual=NPCVisualDetails(
            species="엘프",
            height_cm=165,
            face_details=FacialDetails(nose_bridge="날렵한 버선코"),
            body_measurements=BodyMeasurements(head_ratio=7.5),
            outfit=ClothingLayer(fit_silhouette="슬림핏")
        )
    )
    p_ko = player.to_korean_visual_summary()
    p_en = player.to_image_prompt_keywords()
    assert "아리아" in p_ko
    assert "7.5등신" in p_ko
    assert "버선코" in p_ko
    assert "refined dainty upturned nose" in p_en


def test_build_consistent_character_prompt_engine():
    """Validates OutfitMechanicsEngine.build_consistent_character_prompt end-to-end."""
    state = WorldState()
    sword = Item(
        id="wep_rune_blade",
        name="룬 각인 흑철검",
        description="룬이 새겨진 검",
        location="inventory",
        item_type="weapon",
        visual=ItemVisualProfile(
            blade_or_head="혈조가 파인 양날 직검",
            finish_and_material="거친 단조 흑철",
            glow_or_aura="칼날을 타고 흐르는 은은한 푸른빛 에테르 기운"
        )
    )
    state.items["wep_rune_blade"] = sword

    npc = NPC(
        id="npc_elena",
        name="엘레나",
        description="마검사 엘레나",
        location="crossroads",
        equipment=EquipmentSlots(weapon="wep_rune_blade"),
        visual=NPCVisualDetails(
            species="인간",
            gender="여성",
            life_stage="청년",
            height_cm=168,
            hair_color="흑발",
            hair_style="단발",
            face_details=FacialDetails(eye_lids="무쌍", nose_bridge="오똑하고 곧은 높은 콧대"),
            body_measurements=BodyMeasurements(head_ratio=7.5, bust_size="자연스러운 볼륨(B~C컵)"),
            outfit=ClothingLayer(
                base_upper="스킨타이트 전투복",
                fit_silhouette="스킨타이트",
                inner_silhouette_reveal="faint_underwear_line"
            )
        )
    )
    state.npcs["npc_elena"] = npc

    prompt = OutfitMechanicsEngine.build_consistent_character_prompt(npc, state)
    assert "cinematic fantasy portrait of 인간 여성 청년" in prompt
    assert "168cm tall" in prompt
    assert "7.5 head-to-body proportion" in prompt
    assert "monolid eyes" in prompt
    assert "high defined straight nose bridge" in prompt
    assert "skin-tight form-fitting silhouette" in prompt
    assert "faint underwear seam line visible through form-fitting fabric" in prompt
    assert "wielding 룬 각인 흑철검" in prompt
    assert "double-edged straight blade with deep fuller groove" in prompt
    assert "ethereal faint blue aura radiating along the blade" in prompt


def test_save_load_backward_compatibility():
    """Validates that saving with new visual consistency fields and restoring preserves all values, while old JSONs load gracefully."""
    state = WorldState()
    state.player.name = "카엘"
    state.player.visual.face_details = FacialDetails(nose_bridge="오똑하고 곧은 높은 콧대")
    state.player.visual.body_measurements = BodyMeasurements(head_ratio=8.0, bust_size="다부진 대흉근")
    state.player.visual.outfit.inner_silhouette_reveal = "faint_underwear_line"

    sword = Item(
        id="test_sword",
        name="명품 검",
        description="단련된 검",
        location="inventory",
        item_type="weapon",
        visual=ItemVisualProfile(finish_and_material="물결치는 다마스쿠스 강철 무늬")
    )
    state.items["test_sword"] = sword

    # 1. Serialize to JSON
    json_str = state.to_json()

    # 2. Deserialize from JSON
    restored = WorldState.from_json(json_str)
    assert restored.player.name == "카엘"
    assert restored.player.visual.face_details.nose_bridge == "오똑하고 곧은 높은 콧대"
    assert restored.player.visual.body_measurements.head_ratio == 8.0
    assert restored.player.visual.body_measurements.bust_size == "다부진 대흉근"
    assert restored.player.visual.outfit.inner_silhouette_reveal == "faint_underwear_line"
    assert restored.items["test_sword"].visual.finish_and_material == "물결치는 다마스쿠스 강철 무늬"

    # 3. Backward compatibility test: Old legacy JSON without face_details, body_measurements, or item visual
    legacy_json = {
        "session_id": "legacy_session",
        "turn": 5,
        "player": {
            "name": "구버전 플레이어",
            "visual": {
                "species": "인간",
                "clothing_style": "낡은 모직 옷"
            }
        },
        "npcs": {
            "npc_old": {
                "name": "노인",
                "visual": {
                    "species": "인간",
                    "clothing_style": "농부 옷"
                }
            }
        },
        "items": {
            "item_old": {
                "name": "녹슨 칼",
                "item_type": "weapon"
            }
        }
    }
    legacy_state = WorldState.from_dict(legacy_json)
    assert legacy_state.player.name == "구버전 플레이어"
    assert isinstance(legacy_state.player.visual.face_details, FacialDetails)
    assert isinstance(legacy_state.player.visual.body_measurements, BodyMeasurements)
    assert isinstance(legacy_state.player.visual.outfit, ClothingLayer)
    assert legacy_state.player.visual.outfit.inner_silhouette_reveal == "none"
    assert legacy_state.items["item_old"].visual is None or isinstance(legacy_state.items["item_old"].visual, ItemVisualProfile)
