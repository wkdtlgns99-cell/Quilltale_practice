"""
Deterministic Pupil Adaptation & Sensory Light Transition Physics Engine for Quilltale TRPG.
Models human retinal rhodopsin adaptation across sudden lux transitions:
- Bright to Pitch Darkness: 20.0s adaptation delay (DC +6, speed -50%).
- Pirate Eye-Patch Tactic (User Decision Q2): Pre-adapted dark eye under patch swaps instantly (0s penalty).
- Pitch Darkness to Blinding Flash: 2.0s flash blindness stunned, prevented by Shaded Goggles.
- Non-combat eye adaptation action ('adapt_eyes_action') to safely adjust vision in seconds.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class PupilAdaptationState:
    adapted_lux: float = 500.0              # 현재 동공/망막이 완전히 적응된 조도 (lx)
    target_lux: float = 500.0               # 현재 위치한 환경의 조도 (lx)
    seconds_remaining: float = 0.0          # 완전 적응까지 남은 초 단위 시간
    is_impaired: bool = False               # 시각적 제약/실명 여부
    impairment_reason: str = ""             # 시각 제약 사유
    has_eye_patch: bool = False             # 해적식 애꾸눈 안대 착용 여부
    has_shaded_goggles: bool = False        # 차광 고글 / 흑색 색안경 착용 여부
    traits: List[str] = field(default_factory=lambda: ["pupil_adaptation", "sensory_physics", "visual_acuity"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adapted_lux": self.adapted_lux,
            "target_lux": self.target_lux,
            "seconds_remaining": round(self.seconds_remaining, 2),
            "is_impaired": self.is_impaired,
            "impairment_reason": self.impairment_reason,
            "has_eye_patch": self.has_eye_patch,
            "has_shaded_goggles": self.has_shaded_goggles,
            "traits": list(self.traits),
        }

    @classmethod
    def from_dict(cls, data: Any) -> "PupilAdaptationState":
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            data = {}
        return cls(
            adapted_lux=float(data.get("adapted_lux", 500.0)),
            target_lux=float(data.get("target_lux", 500.0)),
            seconds_remaining=float(data.get("seconds_remaining", 0.0)),
            is_impaired=bool(data.get("is_impaired", False)),
            impairment_reason=str(data.get("impairment_reason", "")),
            has_eye_patch=bool(data.get("has_eye_patch", False)),
            has_shaded_goggles=bool(data.get("has_shaded_goggles", False)),
            traits=list(data.get("traits", ["pupil_adaptation", "sensory_physics", "visual_acuity"])),
        )


class PupilAdaptationEngine:
    """
    Deterministic sensory physics engine for pupil adaptation, retinal light/dark transitions,
    and specialized eyewear gear tactics.
    """

    DARK_LUX_THRESHOLD = 15.0       # 칠흑 같은 암흑 기준치 (lx)
    BRIGHT_LUX_THRESHOLD = 800.0    # 눈부신 대낮/직사광 기준치 (lx)
    FLASH_LUX_THRESHOLD = 3000.0    # 마법 섬광 / 섬광탄 기준치 (lx)

    @classmethod
    def get_state(cls, character: Any) -> PupilAdaptationState:
        raw = getattr(character, "pupil_state", None)
        if raw is None or not isinstance(raw, (dict, PupilAdaptationState)):
            state_obj = PupilAdaptationState()
            character.pupil_state = state_obj.to_dict()
            return state_obj
        if isinstance(raw, dict):
            state_obj = PupilAdaptationState.from_dict(raw)
            return state_obj
        return raw

    @classmethod
    def sync_state(cls, character: Any, state_obj: PupilAdaptationState):
        character.pupil_state = state_obj.to_dict()

    @classmethod
    def equip_eye_patch(cls, character: Any, equip: bool = True) -> str:
        state = cls.get_state(character)
        state.has_eye_patch = equip
        cls.sync_state(character, state)
        if equip:
            return "🏴‍☠️ [안대 착용] 한쪽 눈에 가죽 안대를 둘렀습니다. 어둠 진입 시 즉각 안대를 넘겨 시야를 확보할 수 있습니다."
        else:
            return "안대를 벗었습니다."

    @classmethod
    def equip_shaded_goggles(cls, character: Any, equip: bool = True) -> str:
        state = cls.get_state(character)
        state.has_shaded_goggles = equip
        cls.sync_state(character, state)
        if equip:
            return "🕶️ [차광 고글 착용] 편광 착색 고글을 착용했습니다. 돌발적인 섬광이나 직사광에 의한 실명을 100% 방호합니다."
        else:
            return "차광 고글을 벗었습니다."

    @classmethod
    def swap_eye_patch_action(cls, character: Any) -> str:
        """
        Swaps eye-patch to opposite eye in darkness, immediately canceling dark adaptation delay.
        """
        state = cls.get_state(character)
        if not state.has_eye_patch:
            return "착용 중인 안대가 없습니다."

        if state.is_impaired and "암적응" in state.impairment_reason:
            state.seconds_remaining = 0.0
            state.is_impaired = False
            state.impairment_reason = ""
            state.adapted_lux = state.target_lux
            cls.sync_state(character, state)
            return (
                "🏴‍☠️ [안대 전술 (Eye Patch Tactic)] 어둠 속에서 가죽 안대를 반대편 눈으로 젖혔습니다! "
                "안대 밑에서 미리 어둠에 완벽히 적응해 있던 반대편 눈으로 즉시 칠흑 같은 암흑을 꿰뚫어 봅니다! (암적응 지연 0초)"
            )
        else:
            return "안대를 반대쪽 눈으로 넘겼습니다."

    @classmethod
    def check_illumination_transition(
        cls,
        character: Any,
        from_lux: float,
        to_lux: float,
        is_flash: bool = False
    ) -> Tuple[bool, str]:
        """
        Evaluates pupil light transition physics strictly in time units (seconds).
        Implements User Decision Q2:
        - Bright -> Pitch Dark: 20.0s rhodopsin adaptation delay (or 0s with eye patch tactic).
        - Dark -> Blinding Flash: 2.0s flash blindness (or 0s with shaded goggles).
        """
        state = cls.get_state(character)
        state.adapted_lux = from_lux
        state.target_lux = to_lux

        # 1. Sudden Blinding Flash or Dark -> Blinding Light
        if is_flash or (from_lux <= cls.DARK_LUX_THRESHOLD and to_lux >= cls.FLASH_LUX_THRESHOLD):
            if state.has_shaded_goggles:
                state.seconds_remaining = 0.0
                state.is_impaired = False
                state.impairment_reason = ""
                cls.sync_state(character, state)
                return True, "🕶️ [차광 고글 (Shaded Goggles)] 렌즈가 폭발적인 섬광을 차단하여 눈부심 없이 시야를 온전히 보존했습니다."
            else:
                state.seconds_remaining = 2.0
                state.is_impaired = True
                state.impairment_reason = "강렬한 섬광으로 인한 일시적 망막 백화/실명 (2.0초간 행동 불가)"
                cls.sync_state(character, state)
                return False, "⚡ [섬광 눈부심 (Flash Blindness)] 시신경이 강렬한 빛에 마비되어 2.0초간 눈앞이 새하얗게 탈색되며 완전 실명 상태에 빠집니다!"

        # 2. Bright -> Pitch Dark Adaptation
        if from_lux >= cls.BRIGHT_LUX_THRESHOLD and to_lux <= cls.DARK_LUX_THRESHOLD:
            # Eye Patch Tactic (User Decision Q2)
            if state.has_eye_patch:
                state.seconds_remaining = 0.0
                state.is_impaired = False
                state.impairment_reason = ""
                cls.sync_state(character, state)
                return True, (
                    "🏴‍☠️ [안대 전술 (Eye Patch Tactic)] 어둠에 들어서자마자 안대를 반대쪽 눈으로 넘겼습니다! "
                    "미리 어둠에 길들여진 눈으로 즉시 시야를 확보하여 암적응 페널티 없이 행동합니다! (지연 0초)"
                )
            else:
                state.seconds_remaining = 20.0
                state.is_impaired = True
                state.impairment_reason = "동공 암적응 지연 (20.0초간 명중 DC +6, 이동속도 50% 감쇄)"
                cls.sync_state(character, state)
                return False, (
                    "🌑 [동공 암적응 지연 (Dark Adaptation)] 밝은 곳에서 칠흑 같은 암흑으로 급격히 진입하여 동공이 적응하지 못했습니다! "
                    "로돕신 색소가 합성되는 20초간 시야가 제한됩니다 (명중 DC +6, 이동속도 -50%)."
                )

        # 3. Normal gradual change: no penalty
        state.seconds_remaining = 0.0
        state.is_impaired = False
        state.impairment_reason = ""
        cls.sync_state(character, state)
        return True, "조도 변화에 자연스럽게 시야가 순응했습니다."

    @classmethod
    def adapt_eyes_action(cls, character: Any, wait_seconds: float = 20.0) -> str:
        """
        Voluntary action: Stand still, close/blink eyes for wait_seconds, and adapt vision.
        """
        state = cls.get_state(character)
        if not state.is_impaired:
            return "현재 시야에 아무런 제약이 없습니다."

        state.seconds_remaining = max(0.0, state.seconds_remaining - wait_seconds)
        if state.seconds_remaining <= 0.0:
            state.is_impaired = False
            state.impairment_reason = ""
            state.adapted_lux = state.target_lux
            cls.sync_state(character, state)
            return (
                f"👁️ [동공 암적응 완료] 벽을 짚고 {wait_seconds:.0f}초간 눈을 깜빡이며 적응했습니다. "
                "동공이 활짝 열려 어둠 속의 지형과 사물 윤곽이 선명하게 눈에 들어옵니다."
            )
        else:
            cls.sync_state(character, state)
            return f"👁️ [동공 적응 진행 중] 눈을 깜빡이며 조도에 순응하는 중입니다 (남은 시간: {state.seconds_remaining:.1f}초)."

    @classmethod
    def tick_adaptation_seconds(cls, character: Any, delta_seconds: float) -> List[str]:
        """
        Advances time-based pupil adaptation in seconds.
        """
        state = cls.get_state(character)
        if not state.is_impaired or state.seconds_remaining <= 0.0:
            return []

        logs: List[str] = []
        state.seconds_remaining = max(0.0, state.seconds_remaining - delta_seconds)

        if state.seconds_remaining <= 0.0:
            state.is_impaired = False
            prev_reason = state.impairment_reason
            state.impairment_reason = ""
            state.adapted_lux = state.target_lux
            logs.append(f"👁️ [시각 회복] 동공이 현장 조도에 완전히 적응했습니다 ({prev_reason} 해제).")

        cls.sync_state(character, state)
        return logs
