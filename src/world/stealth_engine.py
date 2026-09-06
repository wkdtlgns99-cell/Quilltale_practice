"""
Realistic Physical Stealth, Infiltration & Acoustic Eavesdropping Engine for Quilltale TRPG.
Simulates lux lighting inverse-square decay, floor material acoustics, stride stance dampening,
ambient noise masking, ground seismic micro-vibrations, wind-borne scent dispersion,
and barrier sound transmission loss.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
import math

from src.world.state import WorldState
from src.world.dice import DiceEngine
from src.world.stat_engine import StatEngine


# 1. Floor Material Base Impact Acoustics (dB at 1 meter)
FLOOR_ACOUSTICS_DB: Dict[str, Dict[str, Any]] = {
    "carpet_soft": {
        "name_ko": "부드러운 양탄자/융단",
        "base_db": 10.0,
        "vibration_transmission": 0.2, # 충격 분산으로 진동 매우 낮음
        "description": "발소리와 지면 충격을 완벽히 흡수하는 푹신한 카펫",
    },
    "dirt_mud": {
        "name_ko": "부드러운 진흙/흙길",
        "base_db": 20.0,
        "vibration_transmission": 0.5,
        "description": "발소리는 죽으나 찰박거림과 젖은 발자국 흔적 유발",
    },
    "stone_flagstone": {
        "name_ko": "매끄러운 화강암 석판",
        "base_db": 28.0,
        "vibration_transmission": 0.8, # 석판을 타고 전도되는 경도 높은 진동
        "description": "단단한 석재 바닥으로 뒤꿈치 마찰음과 충격 전달",
    },
    "water_puddle": {
        "name_ko": "찰랑이는 침수 바닥/웅덩이",
        "base_db": 42.0,
        "vibration_transmission": 0.6,
        "description": "발을 내디딜 때마다 물방울이 튀며 찰박거리는 파열음 발생",
    },
    "wood_creaky": {
        "name_ko": "삐걱이는 노후 목재 마루",
        "base_db": 48.0,
        "vibration_transmission": 0.9, # 목재 판재 삐걱임 및 진동 울림 극대화
        "description": "체중이 실릴 때마다 마룻바닥 틈새가 비명을 지르듯 삐걱거림",
    },
    "dry_straw_leaves": {
        "name_ko": "마른 짚단 및 낙엽층",
        "base_db": 52.0,
        "vibration_transmission": 0.4,
        "description": "스치는 순간 바스락거리는 고주파 마찰음 발생",
    },
    "broken_glass": {
        "name_ko": "깨진 유리 파편 및 자갈",
        "base_db": 68.0,
        "vibration_transmission": 0.7,
        "description": "파편이 짓이겨지며 날카로운 쨍그랑 파쇄음 발생",
    },
}


# 2. Stride Stance & Pacing Modifiers
STRIDE_STANCE_MODIFIERS: Dict[str, Dict[str, Any]] = {
    "creeping_toe": {
        "name_ko": "발끝 살금살금 보행 (포복/극저속)",
        "speed_mps": 0.5,
        "db_modifier": -20.0,
        "vibration_modifier": -0.5,
        "description": "발뒤꿈치를 들고 발끝으로 관절을 굽혀 체중을 극도로 분산",
    },
    "cautious_walk": {
        "name_ko": "조심스러운 서행",
        "speed_mps": 1.0,
        "db_modifier": -10.0,
        "vibration_modifier": -0.2,
        "description": "바닥의 굴곡을 눈으로 살피며 천천히 발을 디딤",
    },
    "normal_walk": {
        "name_ko": "일반 보행 (저벅저벅)",
        "speed_mps": 1.5,
        "db_modifier": 0.0,
        "vibration_modifier": 0.0,
        "description": "일상적인 평상 걸음걸이",
    },
    "running_sprint": {
        "name_ko": "달리기 및 전력 질주",
        "speed_mps": 6.0,
        "db_modifier": 28.0,
        "vibration_modifier": 0.8,
        "description": "바닥을 박차고 질주하여 강한 바닥 충격음과 지면 진동 유발",
    },
}


# 3. Barrier Acoustic Transmission Loss (dB Reduction)
BARRIER_OCCLUSION_DB: Dict[str, Dict[str, Any]] = {
    "door_crack": {
        "name_ko": "문틈 및 열쇠구멍 밀착",
        "attenuation_db": 8.0,
        "description": "문틈 사이로 새어나오는 공기를 통해 직접 청취",
    },
    "thin_wood": {
        "name_ko": "얇은 판자벽/칸막이",
        "attenuation_db": 15.0,
        "description": "나무 판자 틈새로 소리가 상당 부분 투과됨",
    },
    "thick_wood_door": {
        "name_ko": "두꺼운 오크 원목문",
        "attenuation_db": 25.0,
        "description": "목재 문짝에 귀를 바짝 대고 집중하면 키워드 청취 가능",
    },
    "glass_window": {
        "name_ko": "유리 창문",
        "attenuation_db": 20.0,
        "description": "유리의 미세 진동으로 소리가 전달됨",
    },
    "stone_wall": {
        "name_ko": "두꺼운 석벽/성벽",
        "attenuation_db": 45.0,
        "description": "육중한 석재 층이 음파를 대부분 흡수하여 맨귀 청취 불가",
    },
}


@dataclass
class StealthAttemptResult:
    success: bool
    detected_by_sight: bool
    detected_by_hearing: bool
    detected_by_vibration: bool
    detected_by_scent: bool
    generated_footstep_db: float
    perceived_sound_db: float
    ambient_noise_db: float
    was_sound_masked: bool
    distance_m: float
    lighting_lux: float
    floor_material: str
    stride_stance: str
    narrative_ko: str
    detection_reasons: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=lambda: ["은신 잠입 결과", "물리 음향 판정", "지면 진동 역학"])


@dataclass
class EavesdropAttemptResult:
    success: bool
    clarity_level: str  # "crystal_clear", "audible_keywords", "muffled_murmur", "inaudible"
    perceived_db: float
    barrier_type: str
    barrier_occlusion_db: float
    eavesdropped_content_ko: str
    narrative_ko: str
    traits: List[str] = field(default_factory=lambda: ["도청 결과", "음향 투과 판정"])


@dataclass
class StealthInfiltrationEngine:
    TRAITS: List[str] = field(default_factory=lambda: [
        "물리 은신 잠입",
        "음향 데시벨 감쇠",
        "보법 관절 완충",
        "지면 미세 진동 감지",
        "풍향 체취 확산",
        "벽체 도청 차폐"
    ])
    traits: List[str] = field(default_factory=lambda: [
        "물리 은신 잠입",
        "음향 데시벨 감쇠",
        "보법 관절 완충",
        "지면 미세 진동 감지",
        "풍향 체취 확산",
        "벽체 도청 차폐"
    ])

    @classmethod
    def calculate_footstep_sound_db(
        cls,
        infiltrator: Any,
        floor_material: str = "stone_flagstone",
        stride_stance: str = "normal_walk"
    ) -> float:
        """
        침투자의 발소리 발생 데시벨(dB) 산출:
        dB = Floor_Base + Stance_Mod + Armor_Mod + Weight_Mod - Agility_Dampening
        """
        # 1. 바닥 재질 기본 dB
        floor_info = FLOOR_ACOUSTICS_DB.get(floor_material, FLOOR_ACOUSTICS_DB["stone_flagstone"])
        base_db = floor_info["base_db"]

        # 2. 보행 보법 자세 dB
        stance_info = STRIDE_STANCE_MODIFIERS.get(stride_stance, STRIDE_STANCE_MODIFIERS["normal_walk"])
        stance_db = stance_info["db_modifier"]

        # 3. 착용 갑옷 금속 마찰음
        armor_db = 0.0
        eq_armor = getattr(infiltrator, "equipped_armor", None)
        eq_def = getattr(infiltrator, "equipment_defense", 0)
        if eq_def >= 15:
            armor_db = 20.0  # 육중한 전신 풀 플레이트 판금갑옷
        elif eq_def >= 8:
            armor_db = 10.0  # 짤랑거리는 사슬갑옷(체인메일)
        elif eq_def > 0:
            armor_db = 2.0   # 가죽 갑옷

        # 4. 체중/적재량 보정
        str_val = getattr(infiltrator, "effective_strength", getattr(infiltrator, "strength", 10))
        weight_db = max(0.0, (str_val - 10) * 0.5)

        # 5. 민첩(AGI) 관절 완충 상쇄 (Agility Dampening)
        # 훈련된 암살자/고수는 발목과 무릎으로 착지 충격을 깃털처럼 흡수
        agi_val = getattr(infiltrator, "effective_agility", getattr(infiltrator, "agility", 10))
        agility_dampening = max(0.0, (agi_val - 10) * 2.0)
        if agi_val >= 15:
            agility_dampening += 4.0  # 인간 정점 고양이 보법 보너스

        total_db = base_db + stance_db + armor_db + weight_db - agility_dampening
        return max(5.0, round(total_db, 1))

    @classmethod
    def calculate_distance_sound_attenuation(cls, source_db: float, distance_m: float) -> float:
        """거리(m)에 따른 음향 감쇠 공식: dB_r = dB_0 - 20 * log10(r)."""
        dist = max(1.0, distance_m)
        attenuation = 20.0 * math.log10(dist)
        return max(0.0, round(source_db - attenuation, 1))

    @classmethod
    def evaluate_stealth_approach(
        cls,
        state: WorldState,
        infiltrator: Any,
        observer: Any,
        floor_material: str = "stone_flagstone",
        stride_stance: str = "cautious_walk",
        distance_m: float = 8.0,
        lighting_lux: float = 20.0,
        ambient_noise_db: float = 35.0,
        wind_angle_degrees: float = 0.0,  # 0도: 침투자가 풍상(바람을 등짐 -> 냄새 전달), 180도: 침투자가 풍하(냄새 차단)
        is_observer_distracted: bool = False
    ) -> StealthAttemptResult:
        """
        초정밀 물리 잠입 시뮬레이션:
        1. 발소리 음향 계산 및 거리 감쇠
        2. 음향 마스킹 vs 지면 미세 진동 감지
        3. 조도 및 룩스 거리 역제곱 시각 감지
        4. 풍향 및 체취 확산 감지
        """
        detected_sight = False
        detected_hearing = False
        detected_vibration = False
        detected_scent = False
        reasons = []

        observer_per = getattr(observer, "effective_perception", getattr(observer, "perception", 10))
        observer_per_mod = (observer_per - 10) // 2
        infiltrator_agi = getattr(infiltrator, "effective_agility", getattr(infiltrator, "agility", 10))
        infiltrator_agi_mod = (infiltrator_agi - 10) // 2

        # ------------------------------------------------------------------
        # 1. 청각 & 발소리 음향 마스킹
        # ------------------------------------------------------------------
        source_footstep_db = cls.calculate_footstep_sound_db(
            infiltrator=infiltrator,
            floor_material=floor_material,
            stride_stance=stride_stance
        )
        perceived_sound_db = cls.calculate_distance_sound_attenuation(source_footstep_db, distance_m)
        was_masked = (perceived_sound_db <= ambient_noise_db)

        if not was_masked:
            # 배경 소음보다 크게 들림 -> 청각 감지 판정
            noise_margin = perceived_sound_db - ambient_noise_db
            dc = max(5, int(15 - noise_margin * 0.5))
            roll = DiceEngine.roll_d20()
            if roll + observer_per_mod >= dc:
                detected_hearing = True
                reasons.append(f"발소리 청취 ({perceived_sound_db:.1f} dB > 배경 {ambient_noise_db:.1f} dB)")

        # ------------------------------------------------------------------
        # 2. [현실성 보완 1]: 음향 마스킹 시 [지면 미세 진동 (Micro-Vibration)] 감지
        # 소음이 파묻혀도 발걸음이 지면에 전하는 충격을 감각(PER)으로 감지!
        # ------------------------------------------------------------------
        floor_info = FLOOR_ACOUSTICS_DB.get(floor_material, FLOOR_ACOUSTICS_DB["stone_flagstone"])
        vibration_trans = floor_info["vibration_transmission"]
        stance_info = STRIDE_STANCE_MODIFIERS.get(stride_stance, STRIDE_STANCE_MODIFIERS["normal_walk"])
        stance_vib_mod = stance_info["vibration_modifier"]

        # 진동은 12m 이내 근거리에서만 지면을 타고 유효 전달
        if distance_m <= 12.0 and (vibration_trans + stance_vib_mod) > 0.3:
            # 체중 및 충격량에 비례한 진동 감지 난이도
            vib_dc = int(14 + distance_m * 0.8 - (vibration_trans + stance_vib_mod) * 5.0)
            if is_observer_distracted:
                vib_dc += 4
            roll_vib = DiceEngine.roll_d20()
            if roll_vib + observer_per_mod >= vib_dc:
                detected_vibration = True
                reasons.append(f"바닥 미세 진동 감지 (거리 {distance_m:.1f}m, 지면 충격파 감지)")

        # ------------------------------------------------------------------
        # 3. 조도 및 시각 감지 (Lighting Lux & Line of Sight)
        # ------------------------------------------------------------------
        if lighting_lux <= 10.0:
            # 칠흑 같은 암흑: 비암시 생물은 육안 식별 불가 (2m 초과 시 완전 불가)
            if distance_m > 2.0:
                detected_sight = False
            else:
                # 2m 이내 극초근접 시 윤곽 감지 시도: 관찰자가 높은 감각(DC 18)을 뚫어야 함
                roll_sight = DiceEngine.roll_d20() + observer_per_mod
                if roll_sight >= 18:
                    detected_sight = True
                    reasons.append(f"초근접 암흑 속 윤곽 감지 (거리 {distance_m:.1f}m)")
        else:
            # 조도가 있을 때: 관찰자의 감각 vs 침투자의 은신 대결 판정
            infiltrator_stealth = DiceEngine.roll_d20() + infiltrator_agi_mod
            if lighting_lux <= 30.0:
                infiltrator_stealth += 6   # 희미한 그림자 은신 보너스
            elif lighting_lux >= 70.0:
                infiltrator_stealth -= 8   # 눈부신 조명 노출 페널티

            # 거리 및 집중도에 따른 관찰자 탐지치
            observer_spot = 10 + observer_per_mod + (0 if is_observer_distracted else 4) - int(distance_m * 0.4)
            if observer_spot > infiltrator_stealth and distance_m <= 30.0:
                detected_sight = True
                reasons.append(f"시각 포착 (조도 {lighting_lux:.0f} lx, 은신 간파)")

        # ------------------------------------------------------------------
        # 4. 풍향 & 체취 확산 (Wind Vector & Scent Dispersion)
        # ------------------------------------------------------------------
        # 0도 근처(풍상: 바람을 등짐): 침투자의 체취가 관찰자 방향으로 분산
        # 180도 근처(풍하: 바람을 마주봄): 체취가 등 뒤로 날아가 완전 차단
        is_upwind = (wind_angle_degrees <= 60.0 or wind_angle_degrees >= 300.0)
        hygiene = getattr(infiltrator, "hygiene_level", 100)
        has_bloody_items = any("피" in getattr(item, "name", "") or "유골" in getattr(item, "name", "") for item in state.player_inventory_items())

        if is_upwind and distance_m <= 25.0:
            scent_dc = 15
            if hygiene < 40:
                scent_dc -= 6  # 악취 누출
            if has_bloody_items:
                scent_dc -= 5  # 피비린내

            roll_scent = DiceEngine.roll_d20()
            if roll_scent + observer_per_mod >= scent_dc:
                detected_scent = True
                reasons.append("풍상에서 실려온 체취/피비린내 포착")

        # ------------------------------------------------------------------
        # 5. 최종 판정 결합
        # ------------------------------------------------------------------
        is_detected = detected_sight or detected_hearing or detected_vibration or detected_scent
        success = not is_detected

        if success:
            narrative = (
                f"완벽한 정적 유지! [{floor_info['name_ko']}] 위를 [{stance_info['name_ko']}]로 "
                f"바람과 그림자를 타며 흔적 없이 통과했습니다. (발소리: {perceived_sound_db:.1f} dB / 마스킹: {'성공' if was_masked else '자연 소멸'})"
            )
        else:
            reason_str = ", ".join(reasons)
            narrative = (
                f"🚨 잠입 발각! ({reason_str}) 관찰자가 예리하게 고개를 돌리며 당신의 기척을 알아챘습니다!"
            )

        return StealthAttemptResult(
            success=success,
            detected_by_sight=detected_sight,
            detected_by_hearing=detected_hearing,
            detected_by_vibration=detected_vibration,
            detected_by_scent=detected_scent,
            generated_footstep_db=source_footstep_db,
            perceived_sound_db=perceived_sound_db,
            ambient_noise_db=ambient_noise_db,
            was_sound_masked=was_masked,
            distance_m=distance_m,
            lighting_lux=lighting_lux,
            floor_material=floor_material,
            stride_stance=stride_stance,
            narrative_ko=narrative,
            detection_reasons=reasons,
        )

    @classmethod
    def evaluate_eavesdropping(
        cls,
        state: WorldState,
        listener: Any,
        speaker: Any,
        barrier_type: str = "door_crack",
        distance_m: float = 2.0,
        speech_source_db: float = 55.0,  # 일반적인 대화 육성 음량 (55~60 dB)
        secret_dialogue: str = "내일 밤 자정, 북쪽 성문 수비대가 교대하는 틈을 타 암호를 전하고 빠져나가야 한다."
    ) -> EavesdropAttemptResult:
        """
        차폐 매질(문, 석벽, 판자벽)을 통한 물리적 도청 판정.
        """
        barrier_info = BARRIER_OCCLUSION_DB.get(barrier_type, BARRIER_OCCLUSION_DB["thick_wood_door"])
        attenuation_db = barrier_info["attenuation_db"]

        # 거리 감쇠
        dist_attenuation = 20.0 * math.log10(max(1.0, distance_m))
        perceived_db = max(0.0, speech_source_db - attenuation_db - dist_attenuation)

        listener_per = getattr(listener, "effective_perception", getattr(listener, "perception", 10))
        per_mod = (listener_per - 10) // 2

        # 가청 데시벨에 따른 도청 선명도(Clarity) 판정
        roll = DiceEngine.roll_d20()
        total_check = roll + per_mod

        if perceived_db >= 35.0:
            # 매우 선명한 청취
            if total_check >= 8:
                clarity = "crystal_clear"
                content = secret_dialogue
                narrative = f"[{barrier_info['name_ko']}] 너머의 밀담이 토씨 하나 빠짐없이 귀에 똑똑히 꽂힙니다."
                success = True
            else:
                clarity = "audible_keywords"
                content = "내일 밤... 북쪽 성문... 수비대 교대... 암호..."
                narrative = f"웅성거림 속에서 중요한 핵심 단어들을 확실하게 건져냈습니다."
                success = True
        elif perceived_db >= 20.0:
            # 약하게 웅얼거림
            if total_check >= 13:
                clarity = "audible_keywords"
                content = "자정... 성문... 수비대 교대..."
                narrative = f"미세하게 떨려오는 음파에 온 신경을 집중하여 몇 가지 단어를 알아들었습니다."
                success = True
            else:
                clarity = "muffled_murmur"
                content = "...수군거리는 소리... (내용 식별 불가)"
                narrative = f"사람 목소리가 오가는 것은 느껴지나, 차폐가 두터워 무슨 말인지 알아듣지 못했습니다."
                success = False
        else:
            # 거의 무음
            clarity = "inaudible"
            content = ""
            narrative = f"[{barrier_info['name_ko']}]의 두터운 차폐로 인해 아무런 소리도 새어나오지 않습니다."
            success = False

        return EavesdropAttemptResult(
            success=success,
            clarity_level=clarity,
            perceived_db=round(perceived_db, 1),
            barrier_type=barrier_type,
            barrier_occlusion_db=attenuation_db,
            eavesdropped_content_ko=content,
            narrative_ko=narrative,
        )
