"""
Deterministic Alcohol Intoxication & Hangover Engine for Quilltale TRPG.
Simulates Blood Alcohol Content (BAC), mellow/inebriated/blackout stages,
User Decision Q3 companion safe escort vs solo street mugging/hypothermia, and morning hangovers.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import random


@dataclass
class AlcoholDrinkSpec:
    drink_id: str
    name_ko: str
    alcohol_pct: float
    bac_increase: float
    stress_relief: int
    fatigue_relief: int
    temp_boost: float
    cost_gold: int
    description: str = ""
    traits: List[str] = field(default_factory=lambda: ["alcohol", "beverage"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "drink_id": self.drink_id,
            "name_ko": self.name_ko,
            "alcohol_pct": self.alcohol_pct,
            "bac_increase": self.bac_increase,
            "stress_relief": self.stress_relief,
            "fatigue_relief": self.fatigue_relief,
            "temp_boost": self.temp_boost,
            "cost_gold": self.cost_gold,
            "description": self.description,
            "traits": self.traits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlcoholDrinkSpec":
        return cls(
            drink_id=data.get("drink_id", ""),
            name_ko=data.get("name_ko", ""),
            alcohol_pct=float(data.get("alcohol_pct", 5.0)),
            bac_increase=float(data.get("bac_increase", 0.03)),
            stress_relief=int(data.get("stress_relief", 5)),
            fatigue_relief=int(data.get("fatigue_relief", 5)),
            temp_boost=float(data.get("temp_boost", 0.2)),
            cost_gold=int(data.get("cost_gold", 1)),
            description=data.get("description", ""),
            traits=data.get("traits", ["alcohol", "beverage"]),
        )


ALCOHOL_DRINK_REGISTRY: Dict[str, AlcoholDrinkSpec] = {
    "barley_ale": AlcoholDrinkSpec(
        drink_id="barley_ale",
        name_ko="구수한 보리 에일",
        alcohol_pct=4.5,
        bac_increase=0.03,
        stress_relief=8,
        fatigue_relief=5,
        temp_boost=0.2,
        cost_gold=1,
        description="선술집에서 흔히 마시는 시원하고 구수한 맥주. 하루의 피로를 가볍게 달래준다.",
        traits=["alcohol", "ale", "common", "tavern"]
    ),
    "spiced_wine": AlcoholDrinkSpec(
        drink_id="spiced_wine",
        name_ko="향신료 따뜻한 뱅쇼",
        alcohol_pct=12.0,
        bac_increase=0.06,
        stress_relief=15,
        fatigue_relief=10,
        temp_boost=0.6,
        cost_gold=3,
        description="정향과 계피를 넣고 끓여낸 붉은 포도주. 몸속 깊은 곳까지 훈훈하게 덥혀준다.",
        traits=["alcohol", "wine", "warmth", "medicinal"]
    ),
    "dwarven_firewater": AlcoholDrinkSpec(
        drink_id="dwarven_firewater",
        name_ko="드워프 불꽃 증류주",
        alcohol_pct=55.0,
        bac_increase=0.15,
        stress_relief=30,
        fatigue_relief=20,
        temp_boost=1.5,
        cost_gold=8,
        description="목구멍이 타들어갈 정도로 독한 드워프 전통주. 마시는 순간 고통이 둔화되지만 금방 취한다.",
        traits=["alcohol", "spirits", "dwarven", "strong"]
    ),
    "elven_moon_nectar": AlcoholDrinkSpec(
        drink_id="elven_moon_nectar",
        name_ko="엘프 달빛 감청주",
        alcohol_pct=15.0,
        bac_increase=0.07,
        stress_relief=22,
        fatigue_relief=12,
        temp_boost=0.4,
        cost_gold=6,
        description="달빛 아래 빚은 향긋한 꽃향기 술. 신비로운 마력을 은은하게 자극한다.",
        traits=["alcohol", "elven", "sweet", "mana_soothing"]
    )
}


@dataclass
class AlcoholMetabolismState:
    blood_alcohol_content: float = 0.0    # 혈중 알코올 농도 (BAC %)
    intoxication_stage: int = 0           # 0: 맨정신, 1: 알딸딸, 2: 만취, 3: 블랙아웃
    has_hangover: bool = False            # 익일 숙취 상태
    hangover_hours_remaining: int = 0     # 남은 숙취 시간
    traits: List[str] = field(default_factory=lambda: ["alcohol", "intoxication_state"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "blood_alcohol_content": self.blood_alcohol_content,
            "intoxication_stage": self.intoxication_stage,
            "has_hangover": self.has_hangover,
            "hangover_hours_remaining": self.hangover_hours_remaining,
            "traits": self.traits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlcoholMetabolismState":
        return cls(
            blood_alcohol_content=float(data.get("blood_alcohol_content", 0.0)),
            intoxication_stage=int(data.get("intoxication_stage", 0)),
            has_hangover=bool(data.get("has_hangover", False)),
            hangover_hours_remaining=int(data.get("hangover_hours_remaining", 0)),
            traits=data.get("traits", ["alcohol", "intoxication_state"]),
        )


class AlcoholIntoxicationEngine:
    """
    Deterministic Alcohol Consumption, Intoxication Stages, Blackout Resolution, and Morning Hangovers.
    """

    @classmethod
    def get_state(cls, character: Any) -> AlcoholMetabolismState:
        """Retrieves or creates AlcoholMetabolismState on character."""
        raw = getattr(character, "alcohol_state", None)
        if raw is None or not isinstance(raw, (dict, AlcoholMetabolismState)):
            state_obj = AlcoholMetabolismState()
            character.alcohol_state = state_obj.to_dict()
            return state_obj
        if isinstance(raw, dict):
            state_obj = AlcoholMetabolismState.from_dict(raw)
            return state_obj
        return raw

    @classmethod
    def sync_state(cls, character: Any, state_obj: AlcoholMetabolismState):
        """Syncs back dataclass state to character dictionary."""
        character.alcohol_state = state_obj.to_dict()

    @classmethod
    def consume_drink(
        cls,
        state: Any,
        drinker: Any,
        drink_id: str,
        fixed_theft_roll: Optional[int] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Consumes an alcoholic drink. Updates BAC and triggers intoxication stages.
        """
        spec = ALCOHOL_DRINK_REGISTRY.get(drink_id)
        if not spec:
            return False, "존재하지 않는 주류입니다.", {}

        # 1. Gold check
        current_gold = getattr(drinker, "gold", 0)
        if current_gold < spec.cost_gold:
            return False, f"❌ [소지금 부족] [{spec.name_ko}]을(를) 사 마시려면 {spec.cost_gold} 골드가 필요합니다.", {}

        drinker.gold -= spec.cost_gold
        alc_state = cls.get_state(drinker)

        # 2. BAC update
        old_bac = alc_state.blood_alcohol_content
        new_bac = round(old_bac + spec.bac_increase, 3)
        alc_state.blood_alcohol_content = new_bac

        # Warmth and fatigue relief
        if hasattr(drinker, "body_temperature"):
            drinker.body_temperature = round(min(37.5, drinker.body_temperature + spec.temp_boost), 2)
        if hasattr(drinker, "fatigue"):
            drinker.fatigue = max(0, drinker.fatigue - spec.fatigue_relief)

        logs = [
            f"🍺 [{spec.name_ko} 한 잔] 시원하게 들이켜 온몸에 열기가 돕니다. "
            f"(체온 +{spec.temp_boost}℃, 피로 -{spec.fatigue_relief}, 혈중알코올: {new_bac:.3f}%)"
        ]

        # 3. Intoxication Stage Transitions
        # Stage 0: Sober (< 0.03)
        # Stage 1: Mellow (0.03 ~ 0.07)
        # Stage 2: Inebriated (0.08 ~ 0.19)
        # Stage 3: Blackout (0.20+)
        if new_bac >= 0.20:
            alc_state.intoxication_stage = 3
            logs.append("😵 [3단계 만취: 블랙아웃] 시야가 암전되고 다리가 풀리며 바닥으로 쓰러집니다! 정신을 완전히 잃었습니다.")
            cls.sync_state(drinker, alc_state)

            # Resolve Blackout according to User Q3
            blackout_logs = cls.resolve_blackout(state, drinker, fixed_theft_roll=fixed_theft_roll)
            logs.extend(blackout_logs)

            return True, "\n".join(logs), {
                "stage": 3,
                "bac": new_bac,
                "blackout": True
            }

        elif new_bac >= 0.08:
            alc_state.intoxication_stage = 2
            logs.append("🥴 [2단계 만취: 비틀거림] 혀가 꼬이고 발걸음이 크게 흔들립니다! (민첩 -3, 소음 +20dB, 고통 둔화 방어력 +2)")
        elif new_bac >= 0.03:
            alc_state.intoxication_stage = 1
            logs.append("😊 [1단계 취기: 알딸딸] 기분이 붕 뜨고 긴장이 풀립니다. (스트레스 완화, 명중 -1)")
        else:
            alc_state.intoxication_stage = 0

        cls.sync_state(drinker, alc_state)
        return True, "\n".join(logs), {
            "stage": alc_state.intoxication_stage,
            "bac": new_bac,
            "blackout": False
        }

    @classmethod
    def resolve_blackout(
        cls,
        state: Any,
        drinker: Any,
        fixed_theft_roll: Optional[int] = None
    ) -> List[str]:
        """
        User Decision Q3:
        If party companions are present -> safe escort home to bed!
        If alone -> roll chance for pickpocket theft of 20~40% gold + street alley hypothermia/wetness.
        """
        logs = []
        loc = getattr(drinker, "location", "")

        # Check companions in party at same location
        companions_nearby = []
        if hasattr(state, "party") and state.party:
            for c_id, comp in state.party.items():
                if getattr(comp, "location", "") == loc:
                    companions_nearby.append(comp.name)
        elif hasattr(state, "npcs") and state.npcs:
            for npc in state.npcs.values():
                if getattr(npc, "location", "") == loc and getattr(npc, "affinity", 50) >= 70:
                    companions_nearby.append(npc.name)

        if companions_nearby:
            # Safe escort!
            escort_name = companions_nearby[0]
            logs.append(
                f"👥 [동료의 든든한 호송] 만취하여 바닥에 고꾸라졌으나, 함께 있던 동료 [{escort_name}]이(가) "
                f"당신을 둘러업고 안전한 숙소 침대로 옮겨 눕혔습니다. 소지품과 골드가 모두 안전합니다!"
            )
        else:
            # Solo Blackout Danger!
            logs.append("⚠️ [홀로 인사불성 실신] 동행한 동료가 없어 인적 드문 어두운 뒷골목 바닥에 무방비로 방치되었습니다.")

            # Pickpocket roll (60% chance)
            theft_roll = random.randint(1, 100) if fixed_theft_roll is None else fixed_theft_roll
            if theft_roll <= 60 and getattr(drinker, "gold", 0) > 0:
                stolen_gold = max(1, int(drinker.gold * 0.3))
                drinker.gold -= stolen_gold
                logs.append(
                    f"💸 [노상 소매치기 피습] 당신이 곯아떨어진 틈을 타 불량배들이 주머니를 뒤져 "
                    f"{stolen_gold} 골드를 훔쳐 달아났습니다! (남은 골드: {drinker.gold})"
                )
            else:
                logs.append("🍀 [천행] 지나가던 경비병이 순찰을 돌아 다행히 소지품을 털리지는 않았습니다.")

            # Hypothermia & cold alley exposure
            if hasattr(drinker, "body_temperature"):
                drinker.body_temperature = round(max(30.0, drinker.body_temperature - 1.5), 2)
            if hasattr(drinker, "wetness"):
                drinker.wetness = min(100.0, drinker.wetness + 25.0)

            logs.append(
                f"🥶 [노상 방치 저체온증] 차갑고 축축한 돌바닥에 방치되어 체온이 급격히 떨어지고 옷이 젖었습니다. "
                f"(체온: {drinker.body_temperature:.1f}℃, 젖음: {drinker.wetness:.1f}%)"
            )

        return logs

    @classmethod
    def process_morning_hangover(
        cls,
        drinker: Any,
        hours_slept: int = 8
    ) -> List[str]:
        """
        Processes awakening after drinking.
        Metabolizes BAC to 0 and applies hangover debuff if BAC was high.
        """
        logs = []
        alc_state = cls.get_state(drinker)

        had_heavy_drinking = alc_state.blood_alcohol_content >= 0.08 or alc_state.intoxication_stage >= 2

        # Alcohol fully clears after 6+ hours
        alc_state.blood_alcohol_content = 0.0
        alc_state.intoxication_stage = 0

        if had_heavy_drinking:
            alc_state.has_hangover = True
            alc_state.hangover_hours_remaining = 4

            logs.append(
                "🤕 [극심한 숙취 발생] 눈을 뜨자마자 머리가 깨질 듯한 두통과 타는 듯한 갈증이 엄습합니다!\n"
                "   * 숙취 디버프 4시간 지속: 지능/지각 -2, 탈수로 인한 기력 회복 속도 저하"
            )
        else:
            alc_state.has_hangover = False
            alc_state.hangover_hours_remaining = 0
            logs.append("🌤️ [상쾌한 기상] 가벼운 음주 후 푹 자고 일어나 머리가 맑고 개운합니다.")

        cls.sync_state(drinker, alc_state)
        return logs
