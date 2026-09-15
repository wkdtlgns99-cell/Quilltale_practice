"""
Two-Pass GM Engine for Quilltale TRPG.
Pass 1: Deterministic Truth Computation (Dice, Combat, HP, Status, Quests, Party, Economy).
Pass 2: Literary Narration Validation and State Delta Reconciliation.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import logging
import re
import random

from src.world.state import WorldState, Item, NPC
from src.world.validator import ActionValidator
from src.world.skills import SkillSystem
from src.world.status_engine import StatusEffectEngine
from src.world.physics_matrix import PhysicsMatrixEngine
from src.world.object_physics_engine import UniversalObjectPhysicsEngine
from src.world.quest_engine import QuestEngine
from src.world.economy_engine import EconomyEngine
from src.world.party_engine import PartyEngine
from src.world.graph_engine import EcologicalFeedbackLoop
from src.world.weather_engine import WeatherEngine
from src.world.bounty_engine import BountyEngine
from src.world.puzzle_engine import PuzzleEngine
from src.world.celestial_engine import CelestialEngine
from src.world.enchant_engine import EnchantEngine
from src.world.stealth_engine import StealthInfiltrationEngine
from src.world.mana_burn_engine import ManaBurnEngine
from src.world.harvest_engine import AnatomyHarvestEngine, HarvestOutcome
from src.world.attack_physics_engine import AttackPhysicsEngine
from src.world.campsite_engine import CampsiteRestEngine
from src.world.alcohol_engine import AlcoholIntoxicationEngine, ALCOHOL_DRINK_REGISTRY
from src.world.botany_engine import HerbalismBotanyEngine, PLANT_REGISTRY
from src.world.vein_restoration_engine import ManaVeinRestorationEngine, VEIN_SURGERY_REGISTRY
from src.world.time_calendar_engine import TimeCalendarEngine

logger = logging.getLogger(__name__)


@dataclass
class DeterministicFactSheet:
    """Immutable truth computed by Python engine during Pass 1."""
    action: str
    is_valid: bool = True
    rejection_reason: Optional[str] = None
    extra_flags: Dict[str, Any] = field(default_factory=dict)
    
    # 1. Status Ticks & Timers
    status_tick_logs: List[str] = field(default_factory=list)
    quest_timer_logs: List[str] = field(default_factory=list)
    
    # 2. Dice & Combat
    dice_result: Optional[Dict[str, Any]] = None
    combat_outcome: Optional[Dict[str, Any]] = None
    
    # 3. Physics & Chemistry Reactions
    physics_reactions: List[str] = field(default_factory=list)
    
    # 4. Quests & Progress
    quest_progress_logs: List[str] = field(default_factory=list)
    
    # 5. Party & Companions
    companion_combat_logs: List[str] = field(default_factory=list)
    
    # 6. Ecology & World Feedback
    eco_feedback: Dict[str, Any] = field(default_factory=dict)
    
    # 7. Extended World Mechanics (5 Engines)
    weather_logs: List[str] = field(default_factory=list)
    celestial_logs: List[str] = field(default_factory=list)
    puzzle_logs: List[str] = field(default_factory=list)
    bounty_logs: List[str] = field(default_factory=list)
    enchant_logs: List[str] = field(default_factory=list)

    # 8. Pre-computed State Delta (Single Source of Truth)
    pre_computed_state_delta: Dict[str, Any] = field(default_factory=dict)
    dropped_skill_name: Optional[str] = None
    npc_skill_logs: List[str] = field(default_factory=list)
    anti_yesman_verdict: Optional[Dict[str, Any]] = None
    turn_duration_minutes: int = 30
    power_scale_summary: Optional[str] = None
    stealth_summary: Optional[str] = None
    eavesdrop_summary: Optional[str] = None
    mana_burn_summary: Optional[str] = None
    harvest_summary: Optional[str] = None
    attack_physics_summary: Optional[str] = None
    campsite_summary: Optional[str] = None
    alcohol_summary: Optional[str] = None
    botany_summary: Optional[str] = None
    vein_restoration_summary: Optional[str] = None

    def to_prompt_context(self) -> str:
        """Serializes the fact sheet into a high-priority prompt section for the LLM."""
        if not self.is_valid:
            return (
                f"[❌ 행동 거부/불가 판정 (CRITICAL FAILURE)]\n"
                f"시스템 사유: {self.rejection_reason}\n"
                f"⚠️ [절대 규칙]: 플레이어의 행동은 물리적/논리적으로 가로막혔습니다. "
                f"당신은 이 실패를 100% 반영하여 길막힘, 거절, 문턱 걸림 등 참담하게 실패한 상황만을 묘사해야 합니다. "
                f"절대 목적지에 도착했다고 긍정적으로 묘사하거나, 막힌 문을 뚫고 지나갔다는 억지 소설을 쓰지 마십시오."
            )

        lines = [
            "=================================================================",
            "⚡ [확정된 100% 물리/규칙적 진실 (IMMUTABLE FACT SHEET - PASS 1)]",
            "당신은 아래의 확정 연산 팩트를 단 1의 오차도 없이 문학적 서사로 묘사해야 합니다.",
            "팩트를 왜곡, 번복, 날조(사망하지 않은 적을 사망 처리, 실패를 성공으로 변경 등)하는 것은 엄격히 금지됩니다.",
            "=================================================================",
        ]

        if self.power_scale_summary:
            lines.append("⚡ [세계관 성장 규격 및 위계 (Power Scale)]")
            lines.append(f"- {self.power_scale_summary}")

        if self.anti_yesman_verdict:
            lines.append("🛡️ [안티 예스맨 현실성 검증 및 서사 지침 (Anti-Yes-Man Reality Check)]")
            lines.append(f"- 대상: {self.anti_yesman_verdict.get('target_npc_name')} | 판정: {self.anti_yesman_verdict.get('verdict')} (타당도 {self.anti_yesman_verdict.get('plausibility_score')}%)")
            lines.append(f"- GM 지침: {self.anti_yesman_verdict.get('gm_anti_yesman_verdict')}")

        if self.celestial_logs:
            lines.append("🌌 [천문 이변 및 대륙 축제 이벤트]")
            for clog in self.celestial_logs:
                lines.append(f"- {clog}")

        if self.weather_logs:
            lines.append("🌦️ [날씨 환경 물리 및 생존 틱]")
            for wlog in self.weather_logs:
                lines.append(f"- {wlog}")

        if self.status_tick_logs:
            lines.append("🩸 [턴 시작 상태이상 및 지속 피해/회복 연산]")
            for log in self.status_tick_logs:
                lines.append(f"- {log}")

        if self.puzzle_logs:
            lines.append("🧩 [고대 유적 퍼즐 기믹 해결]")
            for plog in self.puzzle_logs:
                lines.append(f"- {plog}")

        if self.bounty_logs:
            lines.append("📜 [현상수배 및 사냥꾼 추적]")
            for blog in self.bounty_logs:
                lines.append(f"- {blog}")

        if self.dice_result:
            res = self.dice_result
            status_str = "성공 (SUCCESS)" if res.get("is_success") else "실패 (FAILURE)"
            lines.append(f"🎲 [주사위 판정]: {res.get('summary_ko', '')} -> 결과: [{status_str}]")

        if self.combat_outcome:
            co = self.combat_outcome
            t_name = co.get("target_name", "대상")
            lines.append(f"⚔️ [전투 피해 연산]: {t_name}에게 {co.get('damage_dealt', 0)} 피해 적용.")
            lines.append(f"   - {t_name} 남은 체력: {co.get('hp_after', 0)}/{co.get('max_hp', 0)} (생존: {'생존함' if co.get('target_alive') else '☠️ 사망함'})")
            if co.get("killed"):
                lines.append(f"   - ☠️ {t_name}(이)가 치명상을 입고 쓰러져 사망했습니다.")
                if self.dropped_skill_name:
                    lines.append(f"   - ✨ [고유 스킬 전리품 발생]: '{self.dropped_skill_name}' 스킬 획득.")

        if self.npc_skill_logs:
            lines.append("⚡ [현장 NPC 자율 스킬 및 기회주의적 행동 확정 연산]")
            for nlog in self.npc_skill_logs:
                lines.append(f"- {nlog}")
            lines.append("*GM 절대 서사 강제 지침*: 당신은 위 NPC의 행동 결과(반격 피해, 소매치기 성공/실패, 기습 등)를 100% 반영하여 서사를 작성해야 합니다.")

        if self.enchant_logs:
            lines.append("✨ [장비 룬 인챈트 및 내구도 효과]")
            for elog in self.enchant_logs:
                lines.append(f"- {elog}")

        if self.companion_combat_logs:
            lines.append("👥 [동료 자율 전투 및 지원 행동]")
            for clog in self.companion_combat_logs:
                lines.append(f"- {clog}")

        if self.physics_reactions:
            lines.append("⚗️ [환경 물리/화학 상호작용]")
            for pr in self.physics_reactions:
                lines.append(f"- {pr}")

        if self.quest_progress_logs:
            lines.append("📜 [퀘스트 진행 갱신]")
            for qlog in self.quest_progress_logs:
                lines.append(f"- {qlog}")

        if self.eco_feedback:
            ef = self.eco_feedback
            if ef.get("terraforming"):
                lines.append(f"🌍 [지형 변화]: {ef['terraforming']}")
        if self.stealth_summary:
            lines.append("🥷 [물리 잠입 및 은신 판정 (Stealth Infiltration)]")
            lines.append(f"- {self.stealth_summary}")
            lines.append("*GM 서사 지침*: 은신 성공 시 그림자와 정적을 타고 흔적 없이 숨어든 상태를 묘사하고, 발각 시 관찰자가 고개를 돌려 기척을 알아채고 경계/대치에 돌입한 긴박한 상황을 사실적으로 서술하십시오.")

        if self.eavesdrop_summary:
            lines.append("👂 [물리 음향 도청 및 밀담 청취 (Acoustic Eavesdropping)]")
            lines.append(f"- {self.eavesdrop_summary}")
            lines.append("*GM 서사 지침*: 청취 선명도(Clarity)에 따라 식별된 대화 내용을 정확하게 서술에 반영하십시오.")

        if self.mana_burn_summary:
            lines.append("⚡ [마나 과부하 및 회로 상태 (Mana Burn & Circuit)]")
            lines.append(f"- {self.mana_burn_summary}")
            lines.append("*GM 서사 지침*: 생명력 연소 과충전, 마나 회로 파열, 마나 폭주 충격파 및 에테르 변이 발현을 극적이고 처절한 문학적 묘사로 서술하십시오. 확정 연산된 회로 손상과 신체 변화를 숨기거나 축소하지 마십시오.")

        if self.harvest_summary:
            lines.append("🥩 [몬스터 부위 파괴 및 갈무리/도축 (Anatomy & Harvesting)]")
            lines.append(f"- {self.harvest_summary}")
            lines.append("*GM 서사 지침*: 부위 파괴 및 꼬리 절단, 사체 도축/갈무리의 감각적이고 처절한 물리적 과정을 문학적으로 서술하십시오. 수확된 전리품과 칼날의 마모를 서사에 사실적으로 반영하십시오.")

        if self.attack_physics_summary:
            lines.append("⚔️ [물리 공격 역학 및 피격 반응 (Attack Physics & Stagger)]")
            lines.append(f"- {self.attack_physics_summary}")
            lines.append("*GM 서사 지침*: 물리 타격 유형(찌르기/베기/둔기/잽/사격)에 따른 운동에너지 충격량, 방어구 관통, 출혈, 뼈 골절 및 피격 저지력으로 인한 적의 행동 캔슬을 박진감 넘치고 처절한 물리 묘사로 서술하십시오.")

        if self.campsite_summary:
            lines.append("⛺ [야영지 및 야간 숙영 판정 (Campsite & Night Rest)]")
            lines.append(f"- {self.campsite_summary}")
            lines.append("*GM 서사 지침*: 야영지 구축, 모닥불의 온기와 피어오르는 연기, 불침번의 고요한 긴장감, 혹은 어둠을 뚫고 덮쳐오는 기습과 이에 맞선 요격 태세를 현장감 넘치고 생생하게 서술하십시오.")

        if self.alcohol_summary:
            lines.append("🍺 [주류 음용 및 취기/숙취/실신 판정 (Alcohol Intoxication & Blackout)]")
            lines.append(f"- {self.alcohol_summary}")
            lines.append("*GM 서사 지침*: 음용된 주류의 맛과 목넘김, 체내 알코올 대사로 인한 열기와 감각 둔화, 만취 시의 비틀거림이나 블랙아웃 시 동료의 든든한 호송 또는 뒷골목 방치/소매치기 피습 위기를 처절하고 생생하게 서술하십시오.")

        if self.botany_summary:
            lines.append("🌿 [야생 식물학 채집/감별/섭취 판정 (Herbalism & Botany)]")
            lines.append(f"- {self.botany_summary}")
            lines.append("*GM 서사 지침*: 수풀을 헤치며 발견한 약초나 버섯의 생생한 외형과 냄새, 채집 시의 손맛, 감별을 통해 드러난 진실(진짜 명약 vs 위험한 맹독 유사종의 소름 돋는 위장), 또는 섭취 시의 신체 치유나 치명적 중독 반응을 감각적이고 사실적인 문학으로 서술하십시오.")

        if self.vein_restoration_summary:
            lines.append("🩺 [마나 혈맥 수술 및 회로 복구 (Mana Vein Restoration Surgery)]")
            lines.append(f"- {self.vein_restoration_summary}")
            lines.append("*GM 서사 지침*: 집도의의 섬세한 손끝에서 전해지는 긴장감, 은침의 냉기 혹은 비전 수술 도구의 빛 튐, 수술 성공 시 막혔던 마나 회로가 뚫리는 황홀한 해방감 또는 실패 시 에테르 역류로 인한 전신 경련과 신경 타는 고통을 처절하고 생생하게 서술하십시오.")

        lines.append("=================================================================")
        return "\n".join(lines)


class TwoPassEngine:
    """
    Executes Pass 1 (Deterministic Truth Computation)
    and validates Pass 2 (Narrative & State Delta Reconciliation).
    """

    @classmethod
    def resolve_action_movement(cls, action: str, state: WorldState) -> Optional[Dict[str, Any]]:
        """
        Parses movement intent, matching exit direction/target location,
        and computes deterministic road distance, condition, travel hours, and minutes.
        Supports single-hop exits, pending waypoints auto-advance, and multi-hop Dijkstra shortest paths.
        Returns travel info dict if valid movement, None otherwise.
        """
        curr_loc = state.current_location()
        if not curr_loc:
            return None

        action_lower = action.lower()
        is_move_action = any(v in action_lower for v in [
            "이동", "걸어", "향해", "달려", "들어", "나선", "오르", "내려", "나간", "떠난",
            "발걸음", "간다", "가자", "가려", "향한다", "내려간다", "올라간다", "접근",
            "가본다", "밑바닥으로", "도착", "계속", "전진", "여정", "가던 길", "여행",
            "move", "go", "enter", "exit", "continue", "forward", "travel", "journey"
        ])
        if not is_move_action:
            return None

        from src.world.geography import GeographyEngine

        # Case 0: Auto-advance on pending_travel_waypoints if continuing journey
        is_continue_intent = any(k in action_lower for k in ["계속", "가던 길", "다음", "전진", "continue", "next"])
        if is_continue_intent and getattr(state, "pending_travel_waypoints", None):
            next_wp_id = state.pending_travel_waypoints[0]
            remaining_wps = list(state.pending_travel_waypoints[1:])
            next_loc = state.locations.get(next_wp_id)
            if next_loc:
                road = GeographyEngine.get_road(state, curr_loc.id, next_wp_id)
                dist_km = road.distance_km if road else 5.0
                r_type = road.road_type if road else "dirt_road"
                cond_info = GeographyEngine.get_effective_road_condition(road, state.environment) if road else {
                    "condition": "normal", "speed_multiplier": 1.0, "name_ko": "정상 도로", "fatigue_bonus": 0, "warning_ko": ""
                }
                cond_speed = cond_info["speed_multiplier"] / road.speed_multiplier if (road and road.speed_multiplier > 0) else 1.0
                hours = GeographyEngine.calculate_segment_travel_hours(dist_km, r_type, travel_mode="foot", condition_speed_mult=cond_speed)
                mins = max(15, int(hours * 60))
                fatigue_inc = max(1, int(mins / 30) + cond_info.get("fatigue_bonus", 0))
                road_warn = f" ({cond_info['warning_ko']})" if cond_info.get("warning_ko") else ""

                return {
                    "target_loc_id": next_wp_id,
                    "target_name": next_loc.name,
                    "dist_km": dist_km,
                    "mins": mins,
                    "fatigue_inc": fatigue_inc,
                    "cond_info": cond_info,
                    "road_warn": road_warn,
                    "pending_waypoints": remaining_wps,
                    "is_waypoint_advance": True
                }

        # Case 1: Check direct exits (1-hop)
        direction_keywords = {
            "north": ["북쪽", "북", "north", "앞으로", "정면"],
            "south": ["남쪽", "남", "south", "뒤로", "남문"],
            "east": ["동쪽", "동", "east", "오른쪽"],
            "west": ["서쪽", "서", "west", "왼쪽"],
            "upstairs": ["2층", "계단", "위층", "upstairs", "올라"],
            "downstairs": ["지하", "아래층", "지하실", "downstairs", "내려"]
        }

        if hasattr(curr_loc, "exits") and curr_loc.exits:
            for exit_dir, target_loc_id in curr_loc.exits.items():
                keywords = direction_keywords.get(exit_dir.lower(), [exit_dir.lower()])
                target_loc = state.locations.get(target_loc_id)
                loc_name_match = bool(target_loc and target_loc.name.lower() in action_lower)
                dir_match = any(k in action_lower for k in keywords)

                # Contextual match: if player mentions '수문' or '운하' and exit is north/subterranean
                context_match = False
                if exit_dir in ["north", "downstairs"] and any(w in action_lower for w in ["수문", "운하", "밑바닥", "지하"]):
                    context_match = True

                if dir_match or loc_name_match or context_match:
                    if target_loc_id in state.locations:
                        if context_match and target_loc:
                            if "비유클리드" in target_loc.name or "미지의" in target_loc.name:
                                target_loc.name = "도시 북쪽 외곽의 폐기된 운하 수문 지하"

                        target_name = target_loc.name if target_loc else target_loc_id

                        road = GeographyEngine.get_road(state, curr_loc.id, target_loc_id)
                        dist_km = road.distance_km if road else 1.5
                        r_type = road.road_type if road else "dirt_road"
                        cond_info = GeographyEngine.get_effective_road_condition(road, state.environment) if road else {
                            "condition": "normal", "speed_multiplier": 1.0, "name_ko": "정상 도로", "fatigue_bonus": 0, "warning_ko": ""
                        }
                        cond_speed = cond_info["speed_multiplier"] / road.speed_multiplier if (road and road.speed_multiplier > 0) else 1.0
                        hours = GeographyEngine.calculate_segment_travel_hours(dist_km, r_type, travel_mode="foot", condition_speed_mult=cond_speed)
                        mins = max(15, int(hours * 60))
                        fatigue_inc = max(1, int(mins / 30) + cond_info.get("fatigue_bonus", 0))
                        road_warn = f" ({cond_info['warning_ko']})" if cond_info.get("warning_ko") else ""

                        return {
                            "target_loc_id": target_loc_id,
                            "target_name": target_name,
                            "dist_km": dist_km,
                            "mins": mins,
                            "fatigue_inc": fatigue_inc,
                            "cond_info": cond_info,
                            "road_warn": road_warn,
                            "pending_waypoints": []
                        }

        # Case 2: Multi-hop destination search via Dijkstra shortest path!
        candidate_destinations = []
        for loc_id, loc_obj in state.locations.items():
            if loc_id == curr_loc.id:
                continue
            if loc_obj.name and loc_obj.name.lower() in action_lower:
                candidate_destinations.append(loc_obj)
            elif loc_id.lower() in action_lower:
                candidate_destinations.append(loc_obj)

        if candidate_destinations:
            candidate_destinations.sort(key=lambda l: len(l.name), reverse=True)
            chosen_dest = candidate_destinations[0]

            hours, km, path = GeographyEngine.dijkstra_shortest_travel(
                state, curr_loc.id, chosen_dest.id, travel_mode="foot", environment=state.environment
            )

            if hours < float('inf') and len(path) >= 2:
                mins = max(15, int(hours * 60))
                fatigue_inc = max(1, int(mins / 30))
                waypoints = path[1:]

                return {
                    "target_loc_id": chosen_dest.id,
                    "target_name": chosen_dest.name,
                    "dist_km": km,
                    "mins": mins,
                    "fatigue_inc": fatigue_inc,
                    "cond_info": {"name_ko": "다중 도로망 연결로", "warning_ko": ""},
                    "road_warn": "",
                    "waypoints": waypoints,
                    "is_multi_hop": True,
                    "pending_waypoints": []
                }

        return None

    @classmethod
    def resolve_action_eavesdrop(cls, action: str, state: WorldState) -> Optional[Dict[str, Any]]:
        """
        도청/엿듣기 의도 파싱 및 StealthInfiltrationEngine.evaluate_eavesdropping 결정론적 판정.
        """
        eavesdrop_keywords = ["엿듣", "도청", "훔쳐듣", "귀를 기울", "귀 기울", "밀담을 듣", "소리를 엿", "eavesdrop"]
        if not any(k in action for k in eavesdrop_keywords):
            return None

        curr_loc = state.current_location()
        if not curr_loc:
            return None

        # 관찰/청취 대상 NPC 검색
        loc_npcs = state.npcs_in_location(curr_loc.id)
        if not loc_npcs:
            loc_npcs = [n for n in state.npcs.values() if getattr(n, "location", "") == curr_loc.id]
        target_speaker = None
        for n in loc_npcs:
            if n.name in action or n.id in action:
                target_speaker = n
                break
        if not target_speaker:
            if loc_npcs:
                target_speaker = loc_npcs[0]
            else:
                target_speaker = NPC(id="shadow_speaker", name="그림자 속 인물", description="밀담을 나누는 자", location=curr_loc.id)

        # 차폐 매질 감지
        barrier_type = "thick_wood_door"
        if any(k in action for k in ["문틈", "열쇠구멍", "crack"]):
            barrier_type = "door_crack"
        elif any(k in action for k in ["석벽", "돌벽", "stone_wall"]):
            barrier_type = "stone_wall"
        elif any(k in action for k in ["판자", "목재벽", "board", "나무벽"]):
            barrier_type = "board_partition"
        elif any(k in action for k in ["창문", "유리창", "window"]):
            barrier_type = "thick_wood_door"

        # 비밀 대화 내용 (NPC의 dialogue, intention, 또는 지역 특화 밀담)
        secret = getattr(target_speaker, "dialogue", None)
        if not secret or len(secret) < 5:
            secret = f"오늘 밤, {curr_loc.name} 외곽에서 비밀 접선이 예정되어 있다."

        res = StealthInfiltrationEngine.evaluate_eavesdropping(
            state=state,
            listener=state.player,
            speaker=target_speaker,
            barrier_type=barrier_type,
            distance_m=2.0,
            secret_dialogue=secret
        )

        return {
            "speaker_name": target_speaker.name,
            "barrier_type": barrier_type,
            "result": res
        }

    @classmethod
    def resolve_action_stealth(cls, action: str, state: WorldState) -> Optional[Dict[str, Any]]:
        """
        은신/잠입 의도 파싱 및 StealthInfiltrationEngine.evaluate_stealth_approach 결정론적 판정.
        """
        stealth_keywords = [
            "숨는", "숨어", "잠입", "은신", "살금살금", "기척을 죽이", "몰래 다가가",
            "포복", "발소리를 죽이", "숨죽이", "발끝으로", "stealth", "sneak", "creep"
        ]
        if not any(k in action for k in stealth_keywords):
            return None

        curr_loc = state.current_location()
        if not curr_loc:
            return None

        # 관찰자 NPC 검색
        loc_npcs = state.npcs_in_location(curr_loc.id)
        if not loc_npcs:
            loc_npcs = [n for n in state.npcs.values() if getattr(n, "location", "") == curr_loc.id]
        observer = None
        for n in loc_npcs:
            if n.name in action or n.id in action:
                observer = n
                break
        if not observer:
            # 적대적 or 경계 중인 NPC 우선
            for n in loc_npcs:
                if getattr(n, "disposition", "") == "hostile" or getattr(n, "alert_level", "") in ["alert", "suspicious"]:
                    observer = n
                    break
        if not observer:
            if loc_npcs:
                observer = loc_npcs[0]
            else:
                observer = NPC(id="ambient_patrol", name="순찰병", description="순찰 중인 경비", location=curr_loc.id, perception=10)

        # 바닥 재질 감지
        floor_material = getattr(curr_loc, "floor_material", None)
        if not floor_material:
            if any(k in action for k in ["양탄자", "카펫", "융단"]):
                floor_material = "carpet_soft"
            elif any(k in action for k in ["깨진 유리", "유리 파편", "자갈"]):
                floor_material = "broken_glass"
            elif any(k in action for k in ["나무", "마루", "목재", "복도"]):
                floor_material = "wood_creaky"
            elif any(k in action for k in ["진흙", "흙길", "웅덩이"]):
                floor_material = "dirt_mud"
            else:
                floor_material = "stone_flagstone"

        # 보행 보법 감지
        if any(k in action for k in ["발끝", "포복", "극저속", "기는", "기어서"]):
            stride_stance = "creeping_toe"
        elif any(k in action for k in ["달려", "전력", "질주", "sprint"]):
            stride_stance = "running_sprint"
        elif any(k in action for k in ["저벅", "평상", "보통"]):
            stride_stance = "normal_walk"
        else:
            stride_stance = "cautious_walk"

        # 조도 감지 (시간대 및 위치 특성)
        is_night = getattr(state.time, "is_night", False) if hasattr(state, "time") else False
        if is_night:
            lighting_lux = getattr(curr_loc, "lighting_lux", 8.0)
        else:
            lighting_lux = getattr(curr_loc, "lighting_lux", 500.0)

        # 주변 소음
        ambient_noise_db = getattr(curr_loc, "ambient_noise_db", 35.0)

        # 풍향 감지: 실내/지하는 체취 바람 차단(180도), 키워드 지정 반영, 기본 측풍(90도)
        if any(k in action for k in ["풍하", "바람을 마주", "바람을 안고", "바람 아래", "냄새를 숨기"]):
            wind_angle = 180.0
        elif any(k in action for k in ["풍상", "바람을 등지"]):
            wind_angle = 0.0
        elif curr_loc and (getattr(curr_loc, "location_category", "") != "surface" or any(w in curr_loc.name for w in ["복도", "회랑", "방", "실", "지하", "던전", "동굴", "성내"])):
            wind_angle = 180.0  # 실내/밀폐 공간 풍향 차단
        else:
            wind_angle = 90.0   # 기본 측풍

        res = StealthInfiltrationEngine.evaluate_stealth_approach(
            state=state,
            infiltrator=state.player,
            observer=observer,
            floor_material=floor_material,
            stride_stance=stride_stance,
            distance_m=5.0,
            lighting_lux=lighting_lux,
            ambient_noise_db=ambient_noise_db,
            wind_angle_degrees=wind_angle
        )

        return {
            "observer": observer,
            "floor_material": floor_material,
            "stride_stance": stride_stance,
            "result": res
        }

    @classmethod
    def resolve_action_harvest(cls, action: str, state: WorldState) -> Optional[Dict[str, Any]]:
        """
        Parses harvest/butchering intent on monster corpses or severed parts.
        Returns dict with outcome and target info if valid harvest intent, None otherwise.
        """
        curr_loc = state.current_location()
        if not curr_loc:
            return None

        action_lower = action.lower()
        harvest_keywords = [
            "갈무리", "도축", "해체", "carve", "harvest",
            "가죽을 벗", "살점을 베", "살점을 발라", "발라낸", "떼어낸", "적출",
            "부위를 베", "고기를 도축", "시체를 갈무리", "사체를 갈무리"
        ]
        if not any(k in action_lower for k in harvest_keywords):
            return None

        # Detect knife if explicitly named in action
        knife_item_id = None
        for i_id in state.player.inventory:
            if i_id in state.items:
                it = state.items[i_id]
                if it.name.lower() in action_lower or i_id.lower() in action_lower:
                    knife_item_id = i_id
                    break

        # Case 1: Check severed parts dropped on the floor
        severed_items = []
        for it_id in getattr(curr_loc, "items", []):
            if it_id in state.items:
                it = state.items[it_id]
                props = getattr(it, "properties", {}) or {}
                if props.get("severed_part"):
                    severed_items.append(it)
        if not severed_items:
            for it in state.items.values():
                if getattr(it, "location", "") == curr_loc.id:
                    props = getattr(it, "properties", {}) or {}
                    if props.get("severed_part"):
                        severed_items.append(it)

        # Match specific severed item or pick first
        target_severed = None
        if severed_items:
            for sit in severed_items:
                if sit.name.lower() in action_lower or sit.id in action_lower:
                    target_severed = sit
                    break
            if not target_severed and any(k in action_lower for k in ["꼬리", "잔해", "절단", "토막", "바닥"]):
                target_severed = severed_items[0]

        if target_severed:
            outcome = AnatomyHarvestEngine.harvest_severed_object(state.player, target_severed.id, state, knife_item_id=knife_item_id)
            return {
                "type": "severed_part",
                "target_name": target_severed.name,
                "outcome": outcome
            }

        # Case 2: Check dead monsters / corpses in location
        dead_monsters = []
        for n in state.npcs.values():
            if getattr(n, "location", "") == curr_loc.id and not getattr(n, "alive", True):
                if getattr(n, "anatomy_parts", None):
                    dead_monsters.append(n)
        if not dead_monsters and curr_loc:
            for nid in getattr(curr_loc, "npcs", []):
                if nid in state.npcs:
                    n = state.npcs[nid]
                    if not getattr(n, "alive", True) and getattr(n, "anatomy_parts", None):
                        if n not in dead_monsters:
                            dead_monsters.append(n)

        if not dead_monsters:
            return None

        # Match specific dead monster
        target_monster = None
        for m in dead_monsters:
            if m.name.lower() in action_lower or m.id in action_lower:
                target_monster = m
                break
        if not target_monster:
            target_monster = dead_monsters[0]

        # Match specific part in monster.anatomy_parts
        target_part_id = None
        for pid, pobj in target_monster.anatomy_parts.items():
            p_name = pobj.name_ko.lower() if hasattr(pobj, "name_ko") else pobj.get("name_ko", "").lower()
            tokens = [t for t in re.split(r'[\s_]+', p_name) if len(t) >= 2]
            if p_name in action_lower or pid.lower() in action_lower or any(t in action_lower for t in tokens):
                target_part_id = pid
                break

        if not target_part_id:
            # Check weak point aliases / keywords
            for pid, pobj in target_monster.anatomy_parts.items():
                p_name = pobj.name_ko.lower() if hasattr(pobj, "name_ko") else pobj.get("name_ko", "").lower()
                combined = f"{p_name} {pid.lower()}"
                if any(k in action_lower for k in ["뿔", "뇌각", "각"]) and any(k in combined for k in ["뿔", "각", "horn"]):
                    target_part_id = pid
                    break
                if any(k in action_lower for k in ["꼬리", "미부"]) and any(k in combined for k in ["꼬리", "tail"]):
                    target_part_id = pid
                    break
                if any(k in action_lower for k in ["날개", "익부"]) and any(k in combined for k in ["날개", "wing"]):
                    target_part_id = pid
                    break
                if any(k in action_lower for k in ["머리", "두부"]) and any(k in combined for k in ["머리", "head"]):
                    target_part_id = pid
                    break

        # Fallback: pick first unharvested part
        if not target_part_id:
            harvested = getattr(target_monster, "harvested_parts", []) or []
            for pid in target_monster.anatomy_parts.keys():
                if pid not in harvested:
                    target_part_id = pid
                    break

        if not target_part_id:
            # All parts already harvested
            return {
                "type": "corpse",
                "target_name": target_monster.name,
                "outcome": HarvestOutcome(
                    success=False,
                    part_id="",
                    part_name_ko="",
                    item_id="",
                    item_name_ko="",
                    is_ruined=False,
                    knife_durability_lost=0,
                    remaining_knife_durability=100,
                    narration_ko=f"[{target_monster.name}]의 모든 신체 부위는 이미 갈무리가 완료되어 더 이상 떼어낼 소재가 없습니다."
                )
            }

        outcome = AnatomyHarvestEngine.harvest_part(state.player, target_monster, target_part_id, state, knife_item_id=knife_item_id)
        return {
            "type": "corpse",
            "target_name": target_monster.name,
            "outcome": outcome
        }

    @classmethod
    def resolve_action_campsite(cls, action: str, state: WorldState) -> Optional[Dict[str, Any]]:
        """
        야영지 구축, 모닥불 점화, 불침번 배정, 야간 숙영/수면 의도 파싱 및 CampsiteRestEngine 결정론적 판정.
        """
        action_lower = action.lower()
        curr_loc = state.current_location()
        if not curr_loc:
            return None

        # 1. 야영지 구축 (구축, 설치, 텐트, 마련)
        setup_keywords = ["야영지 구축", "캠프 구축", "캠프 설치", "텐트 친다", "텐트를 친", "야영지를 만든", "캠프를 친다", "야영지를 마련", "campsite", "setup camp", "야영지 설치", "텐트를 치고"]
        if any(k in action_lower for k in setup_keywords):
            has_tent = any("tent" in i.lower() or "텐트" in getattr(state.items.get(i), "name", "").lower() for i in state.player.inventory)
            has_traps = any(k in action_lower for k in ["덫", "방울", "방어선", "트랩", "경보선", "tripwire"])
            success, msg = CampsiteRestEngine.setup_campsite(state, has_tent=has_tent, has_perimeter_traps=has_traps)
            camp = CampsiteRestEngine.get_campsite(state)
            return {
                "type": "setup",
                "success": success,
                "summary": msg,
                "camp": camp,
                "logs": [msg]
            }

        # 2. 모닥불 점화
        fire_keywords = ["모닥불", "장작불", "캠프파이어", "campfire", "불을 지핀", "불을 피운", "불피운"]
        light_verbs = ["피운", "지핀", "붙인", "점화", "light", "피우", "지피", "붙여"]
        if any(k in action_lower for k in fire_keywords) and any(v in action_lower for v in light_verbs):
            # 장작 소모 (인벤토리에 있으면 식별)
            firewood_id = None
            for i_id in state.player.inventory:
                if i_id in state.items:
                    it = state.items[i_id]
                    if any(w in it.name.lower() or w in i_id.lower() for w in ["장작", "firewood", "나뭇가지", "목재"]):
                        firewood_id = i_id
                        break
            success, msg = CampsiteRestEngine.light_campfire(state, duration_minutes=240)
            camp = CampsiteRestEngine.get_campsite(state)
            return {
                "type": "campfire",
                "success": success,
                "summary": msg,
                "camp": camp,
                "consumed_firewood_id": firewood_id,
                "logs": [msg]
            }

        # 3. 불침번 배정
        sentry_keywords = ["불침번", "경계 근무", "보초", "sentry", "경계를 서", "불침번을 배정", "경계 배정"]
        if any(k in action_lower for k in sentry_keywords):
            # 플레이어 및 동행 동료 수집
            shifts = [{"shift_number": 1, "companion_id": "player", "companion_name": state.player.name}]
            loc_npcs = state.npcs_in_location(curr_loc.id)
            allies = [n for n in loc_npcs if n.alive and (getattr(n, "disposition", "") in ["allied", "friendly"] or n.id in state.party)]
            for idx, ally in enumerate(allies[:2], start=2):
                shifts.append({
                    "shift_number": idx,
                    "companion_id": ally.id,
                    "companion_name": ally.name
                })
            logs = CampsiteRestEngine.assign_sentry_shifts(state, shifts)
            camp = CampsiteRestEngine.get_campsite(state)
            summary = " / ".join(logs)
            return {
                "type": "sentry",
                "success": True,
                "summary": f"🛡️ [불침번 편성 완료] {summary}",
                "camp": camp,
                "logs": logs
            }

        # 4. 야간 숙영 / 수면 / 휴식
        rest_keywords = [
            "야영지에서 휴식", "야영지에서 잠", "캠프에서 잠", "캠프에서 휴식", "모닥불 곁에서 잠",
            "모닥불 옆에서 잠", "노숙", "야영하며 밤", "침낭을 펴고", "야영 수면", "숙영",
            "야영한다", "캠프에서 쉰다", "rest at camp", "sleep at camp", "캠프에서 하룻밤",
            "야영 휴식", "캠프 휴식", "모닥불 가에서 잠"
        ]
        if any(k in action_lower for k in rest_keywords):
            # 침낭 식별
            bedding_id = "leather_bedroll"
            for i_id in state.player.inventory:
                if i_id in state.items:
                    it_name = state.items[i_id].name.lower()
                    if "모피" in it_name or "fur" in it_name:
                        bedding_id = "fur_bedroll"
                        break
                    elif "침낭" in it_name or "bedroll" in it_name:
                        bedding_id = "leather_bedroll"

            # CampsiteRestEngine 실행
            night_res = CampsiteRestEngine.resolve_campsite_night(state, hours=8, bedding_id=bedding_id)
            camp = CampsiteRestEngine.get_campsite(state)

            spawned_npcs = []
            if night_res.get("ambush_triggered"):
                spec = night_res.get("ambush_spec", {})
                count = spec.get("attacker_count", 2)
                ambush_name = spec.get("name_ko", "야간 습격자")
                for i in range(count):
                    e_id = f"ambush_{spec.get('ambush_id', 'enemy')}_{state.turn}_{i+1}"
                    e_npc = NPC(
                        id=e_id,
                        name=f"{ambush_name} #{i+1}",
                        description="어둠을 틈타 야영지를 습격한 야간 침입자.",
                        location=curr_loc.id,
                        alive=True,
                        disposition="hostile",
                        health=30,
                        max_health=30,
                        armor_class=12,
                        perception=spec.get("attacker_perception", 10),
                        traits=spec.get("traits", ["ambush", "hostile"])
                    )
                    state.npcs[e_id] = e_npc
                    if curr_loc and e_id not in curr_loc.npcs:
                        curr_loc.npcs.append(e_id)
                    spawned_npcs.append(e_npc)

            summary = " ".join(night_res.get("logs", []))
            return {
                "type": "night_rest",
                "success": True,
                "summary": summary,
                "camp": camp,
                "night_res": night_res,
                "spawned_npcs": spawned_npcs,
                "logs": night_res.get("logs", [])
            }

        return None

    @classmethod
    def resolve_action_drink(cls, action: str, state: WorldState, fixed_theft_roll: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Parses drinking intent (alcohol beverages), handles tavern purchase vs inventory consumption,
        updates BAC, intoxication stages, User Q3 companion safe escort vs solo street mugging/hypothermia.
        """
        action_lower = action.lower()
        non_alc_words = ["수술", "기술", "전술", "마술", "예술", "요술", "학술", "서술", "상술", "주술", "시술", "권술", "검술", "창술", "궁술", "의술", "인술", "화술"]
        action_cleaned_for_alc = action_lower
        for nw in non_alc_words:
            action_cleaned_for_alc = action_cleaned_for_alc.replace(nw, " ")

        alcohol_keywords = [
            "술을", "술이", "술 마", "술마", "맥주", "에일", "와인", "포도주", "뱅쇼",
            "위스키", "독주", "증류주", "감청주", "술 한 잔", "술 한잔", "술잔을", "한잔 마",
            "술을 들이", "술을 벌컥", "주류를", "drink ale", "drink beer", "drink wine", "drink alcohol"
        ]
        is_potion = any(k in action_lower for k in ["포션", "물약", "치료약", "해독제", "비약", "potion", "elixir"])
        if not any(k in action_cleaned_for_alc for k in alcohol_keywords) or is_potion:
            return None

        # 1. Check if drinking from inventory
        consumed_inv_id = None
        drink_id = None

        # Try to find matching drink in player's inventory first
        for i_id in state.player.inventory:
            if i_id in state.items:
                it = state.items[i_id]
                it_name = it.name.lower()
                it_traits = getattr(it, "traits", [])

                # Direct match to registry keys or Korean names
                if i_id in ALCOHOL_DRINK_REGISTRY:
                    consumed_inv_id = i_id
                    drink_id = i_id
                    break
                for reg_id, spec in ALCOHOL_DRINK_REGISTRY.items():
                    if spec.name_ko.lower() in it_name or reg_id in it_name or reg_id in i_id.lower():
                        consumed_inv_id = i_id
                        drink_id = reg_id
                        break
                if consumed_inv_id:
                    break

                # General keyword match in inventory item
                if any(w in it_name for w in ["맥주", "에일", "ale", "beer"]):
                    consumed_inv_id = i_id
                    drink_id = "barley_ale"
                    break
                elif any(w in it_name for w in ["와인", "포도주", "뱅쇼", "wine"]):
                    consumed_inv_id = i_id
                    drink_id = "spiced_wine"
                    break
                elif any(w in it_name for w in ["독주", "증류주", "불꽃", "firewater"]):
                    consumed_inv_id = i_id
                    drink_id = "dwarven_firewater"
                    break
                elif any(w in it_name for w in ["감청주", "달빛", "nectar"]):
                    consumed_inv_id = i_id
                    drink_id = "elven_moon_nectar"
                    break
                elif "alcohol" in it_traits or "beverage" in it_traits:
                    consumed_inv_id = i_id
                    drink_id = "barley_ale"
                    break

        # 2. If not from inventory, determine tavern order
        if not drink_id:
            if any(w in action_lower for w in ["독주", "증류주", "불꽃", "firewater"]):
                drink_id = "dwarven_firewater"
            elif any(w in action_lower for w in ["와인", "포도주", "뱅쇼", "wine"]):
                drink_id = "spiced_wine"
            elif any(w in action_lower for w in ["감청주", "달빛", "엘프", "nectar"]):
                drink_id = "elven_moon_nectar"
            else:
                drink_id = "barley_ale"

        spec = ALCOHOL_DRINK_REGISTRY.get(drink_id, ALCOHOL_DRINK_REGISTRY["barley_ale"])

        # If from inventory, temporarily credit gold to bypass purchase cost check
        prev_gold = getattr(state.player, "gold", 0)
        if consumed_inv_id:
            if prev_gold < spec.cost_gold:
                state.player.gold += spec.cost_gold

        # Execute drink consumption
        success, msg, data = AlcoholIntoxicationEngine.consume_drink(
            state, state.player, drink_id, fixed_theft_roll=fixed_theft_roll
        )

        # Restore gold if consumed from inventory
        if consumed_inv_id:
            state.player.gold = prev_gold

        if not success:
            return {
                "success": False,
                "summary": msg,
                "drink_id": drink_id,
                "logs": [msg]
            }

        return {
            "success": True,
            "summary": msg,
            "drink_id": drink_id,
            "consumed_inventory_item_id": consumed_inv_id,
            "stage": data.get("stage", 0),
            "bac": data.get("bac", 0.0),
            "blackout": data.get("blackout", False),
            "logs": msg.split("\n")
        }

    @classmethod
    def resolve_action_botany(
        cls,
        action: str,
        state: WorldState,
        fixed_forage_roll: Optional[int] = None,
        fixed_id_roll: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Parses botany intent: wild plant foraging, precise plant identification, and plant consumption.
        """
        action_lower = action.lower()
        curr_loc = state.current_location()

        # 1. Identify intent (식물 감별)
        id_keywords = ["약초 감별", "식물 감별", "버섯 감별", "감별한다", "정밀 감별", "약초를 조사", "버섯을 조사", "식물을 조사", "identify plant", "identify herb"]
        is_id_action = any(k in action_lower for k in id_keywords)
        if is_id_action:
            # Find an uninspected or foraged plant in player inventory
            target_item = None
            for i_id in state.player.inventory:
                if i_id in state.items:
                    it = state.items[i_id]
                    if getattr(it, "true_spec_id", "") or "botany_foraged" in getattr(it, "traits", []) or "unidentified" in getattr(it, "traits", []):
                        target_item = it
                        break

            if not target_item:
                return None

            plant_dict = {
                "id": target_item.id,
                "name": target_item.name,
                "true_spec_id": getattr(target_item, "true_spec_id", ""),
                "is_identified": getattr(target_item, "is_identified", False),
                "is_poisonous_lookalike": getattr(target_item, "is_poisonous_lookalike", False),
                "origin_target_name": getattr(target_item, "origin_target_name", target_item.name),
                "traits": list(getattr(target_item, "traits", []))
            }
            success, msg = HerbalismBotanyEngine.identify_plant(state.player, plant_dict, fixed_roll=fixed_id_roll)
            if success:
                target_item.is_identified = True
                if plant_dict.get("is_poisonous_lookalike"):
                    target_item.name = plant_dict["name"]
                    target_item.is_poisonous_lookalike = True
                    if "unidentified" in target_item.traits:
                        target_item.traits.remove("unidentified")
                    if "poison" not in target_item.traits:
                        target_item.traits.append("poison")
                else:
                    if "unidentified" in target_item.traits:
                        target_item.traits.remove("unidentified")

            return {
                "type": "identify",
                "success": success,
                "summary": msg,
                "item_id": target_item.id,
                "logs": [msg]
            }

        # 2. Consume intent (Eating / Brewing foraged plant)
        consume_verbs = ["먹는", "먹어", "삼킨", "삼켜", "섭취", "달여", "씹어", "eat", "consume"]
        if any(v in action_lower for v in consume_verbs):
            # Check if matching a botany item in player inventory
            target_item = None
            for i_id in state.player.inventory:
                if i_id in state.items:
                    it = state.items[i_id]
                    it_name = it.name.lower()
                    it_traits = getattr(it, "traits", [])
                    has_spec = bool(getattr(it, "true_spec_id", ""))
                    is_botany = "botany_foraged" in it_traits or has_spec or any(p.name_ko.lower() in it_name for p in PLANT_REGISTRY.values())
                    if is_botany and (it_name in action_lower or any(w in action_lower for w in ["약초", "버섯", "풀", "이끼", "나물", "plant", "herb", "mushroom"])):
                        target_item = it
                        break

            if target_item:
                plant_dict = {
                    "id": target_item.id,
                    "name": target_item.name,
                    "true_spec_id": getattr(target_item, "true_spec_id", ""),
                    "is_identified": getattr(target_item, "is_identified", True),
                    "is_poisonous_lookalike": getattr(target_item, "is_poisonous_lookalike", False),
                    "origin_target_name": getattr(target_item, "origin_target_name", target_item.name),
                    "traits": list(getattr(target_item, "traits", []))
                }
                # If true_spec_id was empty, try to match by name
                if not plant_dict["true_spec_id"]:
                    for spec_id, spec in PLANT_REGISTRY.items():
                        if spec.name_ko.lower() in target_item.name.lower() or spec_id in target_item.id.lower():
                            plant_dict["true_spec_id"] = spec_id
                            break

                logs = HerbalismBotanyEngine.consume_plant(state.player, plant_dict, state=state)
                summary = "\n".join(logs)
                if target_item.id in state.player.inventory:
                    state.player.inventory.remove(target_item.id)
                return {
                    "type": "consume",
                    "success": True,
                    "summary": summary,
                    "consumed_item_id": target_item.id,
                    "logs": logs
                }

        # 3. Forage intent
        forage_keywords = [
            "약초 채집", "식물 채집", "버섯 채집", "약초를 캐", "약초를 캔", "약초를 찾",
            "풀을 뜯", "식물을 캔", "버섯을 딴", "버섯을 채집", "약초를 뜯", "forage", "gather herb",
            "채집한다", "약초 채취", "식물 채취", "버섯 채취", "풀을 채취"
        ]
        is_forage_action = any(k in action_lower for k in forage_keywords) and not any(v in action_lower for v in ["갈무리", "도축", "해체", "carve", "harvest", "광석", "채광"])
        if is_forage_action:
            if not curr_loc:
                return None

            # Detect targeted plant if any
            target_plant_id = None
            for p_id, spec in PLANT_REGISTRY.items():
                if spec.name_ko.lower() in action_lower or spec.name_ko.replace(" ", "").lower() in action_lower.replace(" ", ""):
                    target_plant_id = p_id
                    break

            res = HerbalismBotanyEngine.forage(
                gatherer=state.player,
                location=curr_loc,
                state=state,
                target_plant_id=target_plant_id,
                fixed_roll=fixed_forage_roll
            )

            created_item_id = None
            if res.get("success") and res.get("plant_data"):
                p_data = res["plant_data"]
                item_id = p_data["id"]
                item_name = p_data["name"]
                true_spec = PLANT_REGISTRY.get(p_data["true_spec_id"])
                item_desc = true_spec.description if true_spec else "야생에서 채집한 식물 표본."

                new_item = Item(
                    id=item_id,
                    name=item_name,
                    description=item_desc,
                    location="inventory",
                    item_type="consumable",
                    traits=p_data.get("traits", ["botany_foraged"]),
                    true_spec_id=p_data.get("true_spec_id", ""),
                    is_identified=p_data.get("is_identified", True),
                    is_poisonous_lookalike=p_data.get("is_poisonous_lookalike", False),
                    origin_target_name=p_data.get("origin_target_name", item_name)
                )
                state.items[item_id] = new_item
                state.player.inventory.append(item_id)
                created_item_id = item_id

            return {
                "type": "forage",
                "success": res.get("success", False),
                "is_lookalike": res.get("is_lookalike", False),
                "summary": res.get("message_ko", ""),
                "created_item_id": created_item_id,
                "logs": [res.get("message_ko", "")]
            }

        return None

    @classmethod
    def compute_pass1(cls, action: str, state: WorldState) -> DeterministicFactSheet:
        """
        Pass 1: Computes all deterministic mechanics in strict logical order.
        """
        fact_sheet = DeterministicFactSheet(action=action)
        state_delta: Dict[str, Any] = {}

        # 0. Pre-evaluate Travel Duration for Time-Scaled Survival Ticks
        curr_loc = state.current_location()
        travel_info = cls.resolve_action_movement(action, state)
        if travel_info:
            elapsed_minutes = travel_info["mins"]
            default_fatigue_delta = 0  # travel path handles its own fatigue
        else:
            # P1-6: replace hardcoded flat-30 with keyword-matched variable action duration
            _act_key, elapsed_minutes, default_fatigue_delta = TimeCalendarEngine.determine_action_duration(action)
        fact_sheet.turn_duration_minutes = elapsed_minutes

        # 0.1 Determine World Power Scale Preset (Deterministic Reader)
        preset = state.get_power_scale_preset()
        fact_sheet.power_scale_summary = (
            f"{preset.name_ko} (최대 Lv.{preset.max_level}, 스탯 상한 {preset.stat_cap}, "
            f"대미지 배율 x{preset.damage_scale_multiplier})"
        )

        # 1. Status Ticks, Weather Survival & Celestial Cycles
        from src.world.npc_skill_engine import NPCSkillEngine
        NPCSkillEngine.tick_all_skill_cooldowns(state)

        tick_result = StatusEffectEngine.process_turn_ticks(state)
        fact_sheet.status_tick_logs = tick_result.get("logs", [])
        
        # Weather survival ticks (Hypothermia / Heatstroke)
        weather_ticks = WeatherEngine.process_turn_survival_ticks(state, delta_minutes=elapsed_minutes)
        fact_sheet.weather_logs = weather_ticks
        fact_sheet.status_tick_logs.extend(weather_ticks)

        # Epidemic & Disease progression ticks
        from src.world.disease_engine import EpidemicEngine
        disease_ticks = EpidemicEngine.process_turn_infections(state, delta_minutes=elapsed_minutes)
        fact_sheet.status_tick_logs.extend(disease_ticks)

        # Ration & Food Spoilage ticks
        from src.world.ration_engine import RationSpoilageEngine
        spoilage_ticks = RationSpoilageEngine.process_turn_spoilage(state, delta_minutes=elapsed_minutes)
        fact_sheet.status_tick_logs.extend(spoilage_ticks)

        # Sleep Deprivation & Circadian Clock ticks
        from src.world.sleep_engine import SleepDeprivationEngine
        circadian_ticks = SleepDeprivationEngine.process_turn_circadian(state, delta_minutes=elapsed_minutes)
        fact_sheet.status_tick_logs.extend(circadian_ticks)

        # Active Weather Magic Anomalies ticks (Blizzards, Hail, Acid Rain, etc.)
        from src.world.weather_magic_engine import WeatherMagicSimulationEngine
        weather_magic_logs = WeatherMagicSimulationEngine.tick_anomalies(state, delta_minutes=elapsed_minutes)
        if weather_magic_logs:
            fact_sheet.weather_logs.extend(weather_magic_logs)
            fact_sheet.status_tick_logs.extend(weather_magic_logs)

        # Toxicology & Liver Metabolism time progression (User Q1: Real in-game time decay)
        from src.world.toxicology_engine import ToxicologyToleranceEngine
        tox_time_logs = ToxicologyToleranceEngine.process_time_metabolism(state.player, elapsed_minutes=elapsed_minutes)
        if tox_time_logs:
            fact_sheet.status_tick_logs.extend(tox_time_logs)

        # Alcohol Metabolism & Hangover decay time progression
        alc_time_logs = AlcoholIntoxicationEngine.tick_metabolism(state.player, delta_minutes=elapsed_minutes)
        if alc_time_logs:
            fact_sheet.status_tick_logs.extend(alc_time_logs)

        # Celestial & Festival cycle turns
        celestial_logs = CelestialEngine.advance_celestial_turn(state)
        fact_sheet.celestial_logs = celestial_logs

        # Advance quest timers (scaled by elapsed_minutes)
        quest_timer_logs = QuestEngine.check_turn_time_limits(state, delta_minutes=elapsed_minutes)
        fact_sheet.status_tick_logs.extend(quest_timer_logs)
        fact_sheet.quest_timer_logs = quest_timer_logs

        # Economy shop restock
        EconomyEngine.restock_turn_ticks(state, delta_turns=max(1, round(elapsed_minutes / 30.0)))

        # Stamina natural recovery per turn (Player and NPCs in current location)
        from src.world.stamina_engine import StaminaEngine
        StaminaEngine.recover_turn(state.player)
        for npc in state.npcs.values():
            if getattr(npc, "location", "") == state.player.location:
                StaminaEngine.recover_turn(npc)

        # Posture/Poise natural Sekiro-style recovery per turn
        from src.world.poise_engine import PosturePoiseEngine
        poise_rec_logs = PosturePoiseEngine.recover_posture_turn(state.player)
        if poise_rec_logs:
            fact_sheet.status_tick_logs.extend(poise_rec_logs)
        for npc in state.npcs.values():
            if getattr(npc, "location", "") == state.player.location:
                PosturePoiseEngine.recover_posture_turn(npc)

        # Battlefield Corpse Ecology & Decay progression (scaled by elapsed_minutes)
        from src.world.corpse_ecology_engine import CorpseEcologyEngine
        corpse_decay_logs = CorpseEcologyEngine.process_turn_corpse_decay(state, delta_minutes=elapsed_minutes)
        if corpse_decay_logs:
            fact_sheet.status_tick_logs.extend(corpse_decay_logs)

        # Pupil Adaptation time tick (scaled by elapsed_minutes)
        from src.world.pupil_adaptation_engine import PupilAdaptationEngine
        pupil_logs = PupilAdaptationEngine.tick_adaptation_seconds(state.player, delta_seconds=elapsed_minutes * 60.0)
        if pupil_logs:
            fact_sheet.status_tick_logs.extend(pupil_logs)

        # Party & Companion Mental Sanity ticks (Darkness stress, safe recovery, breakdown counters)
        from src.world.party_sanity_engine import PartySanityEngine
        sanity_logs = PartySanityEngine.process_turn_sanity(state, delta_minutes=elapsed_minutes)
        fact_sheet.status_tick_logs.extend(sanity_logs)

        # Subterranean Cave Collapse & Environmental dynamics (Oxygen, toxic gas, floor hazard)
        from src.world.cave_in_engine import CaveCollapseEngine
        env_hazard_logs = CaveCollapseEngine.process_turn_environment(state)
        fact_sheet.status_tick_logs.extend(env_hazard_logs)

        # Mana circuit burnout cooling ticks (Player and NPCs in current location)
        p_circuit = ManaBurnEngine.get_circuit_state(state.player)
        if p_circuit.burnout_turns > 0:
            p_circuit.burnout_turns = max(0, p_circuit.burnout_turns - 1)
            if p_circuit.burnout_turns == 0:
                fact_sheet.status_tick_logs.append("✨ [마나 회로 냉각] 타버렸던 마나 회로의 열기가 식어 다시 마법을 영창할 수 있습니다.")
            else:
                fact_sheet.status_tick_logs.append(f"⚠️ [마나 회로 과열 지속] 마나 회로가 식는 중입니다. (잔여 침묵: {p_circuit.burnout_turns}턴)")
        for npc in state.npcs.values():
            if getattr(npc, "location", "") == state.player.location:
                n_circuit = ManaBurnEngine.get_circuit_state(npc)
                if n_circuit.burnout_turns > 0:
                    n_circuit.burnout_turns = max(0, n_circuit.burnout_turns - 1)

        # Advance world simulation
        state.advance_world_simulation()
        state.advance_information_waves()
        state.check_and_publish_periodicals()

        # 2. Action Pre-validation & Dice check
        is_valid, error_msg, dice_res, extra_flags = ActionValidator.pre_validate_action(action, state)
        fact_sheet.is_valid = is_valid
        fact_sheet.rejection_reason = error_msg
        fact_sheet.extra_flags = extra_flags or {}

        if not is_valid:
            fact_sheet.pre_computed_state_delta = {}
            return fact_sheet

        # 2.2 Delayed Theft Discovery Check (PerceptionEngine)
        from src.world.perception_engine import PerceptionEngine
        discovered_thefts = PerceptionEngine.check_delayed_theft_discovery(state, action)
        if discovered_thefts:
            for d_info in discovered_thefts:
                fact_sheet.quest_progress_logs.append(d_info["log_ko"])
                if d_info.get("gm_directive"):
                    fact_sheet.npc_skill_logs.append(f"   * [도난 발각 서사 지침]: {d_info['gm_directive']}")

        # 2.3 Anti-Yes-Man Hypothesis Validation (NPCCognitiveDeductionEngine)
        hypothesis_patterns = [
            "인 것 같", "인 거 같", "하려는 거 아니", "하려는 거 아닌", "일지도 몰",
            "독살", "배신", "훔치", "거짓말", "의심", "수상", "흉계", "음모", "속이", "함정"
        ]
        if any(p in action for p in hypothesis_patterns):
            from src.world.cognitive_engine import NPCCognitiveDeductionEngine
            curr_loc = state.current_location()
            target_cand = None
            if curr_loc:
                loc_npcs = state.npcs_in_location(curr_loc.id)
                for n in loc_npcs:
                    if n.name in action or n.id in action:
                        target_cand = n
                        break
                if not target_cand and loc_npcs:
                    target_cand = loc_npcs[0]
            if not target_cand:
                for n in state.npcs.values():
                    if n.name in action:
                        target_cand = n
                        break
            if target_cand:
                hypo_res = NPCCognitiveDeductionEngine.evaluate_player_hypothesis(target_cand, action, state)
                fact_sheet.anti_yesman_verdict = hypo_res.to_dict()
                fact_sheet.npc_skill_logs.append(f"🔍 [안티 예스맨 가설 검증]: {target_cand.name} - {hypo_res.verdict} ({hypo_res.plausibility_score}%)")
                fact_sheet.npc_skill_logs.append(f"   * [GM 서사 지침]: {hypo_res.gm_anti_yesman_verdict}")

        # 2.4 Micro-Leakage & NPC Observation (PerceptionEngine + NPCCognitiveDeductionEngine)
        observe_keywords = ["관찰", "살펴", "눈여겨", "주시", "표정", "기색", "속내", "눈빛", "observe", "study"]
        if any(k in action for k in observe_keywords):
            curr_loc = state.current_location()
            if curr_loc:
                loc_npcs = state.npcs_in_location(curr_loc.id)
                obs_target = None
                for n in loc_npcs:
                    if n.name in action or n.id in action:
                        obs_target = n
                        break
                if not obs_target and loc_npcs:
                    obs_target = loc_npcs[0]
                if obs_target:
                    obs_res = PerceptionEngine.observe_npc_micro_leakage(state.player, obs_target, state)
                    fact_sheet.npc_skill_logs.append(f"👁️ [인물 관찰 및 속내 간파]: {obs_target.name}")
                    fact_sheet.npc_skill_logs.append(f"   * [신체 언어 복선]: {obs_res['leakage_clue']}")
                    fact_sheet.npc_skill_logs.append(f"   * [GM 서사 지침]: {obs_res['gm_directive']}")

        # 2.45 Physical Eavesdropping Resolution (StealthInfiltrationEngine)
        eavesdrop_info = cls.resolve_action_eavesdrop(action, state)
        if eavesdrop_info:
            e_res = eavesdrop_info["result"]
            fact_sheet.eavesdrop_summary = f"{e_res.narrative_ko} (식별된 핵심 밀담: '{e_res.eavesdropped_content_ko}')"
            fact_sheet.quest_progress_logs.append(
                f"밀담 도청 ({e_res.clarity_level}): {eavesdrop_info['speaker_name']}의 대화 청취 (체감 음압: {e_res.perceived_db:.1f} dB)"
            )

        # 2.46 Physical Stealth & Infiltration Resolution (StealthInfiltrationEngine)
        stealth_info = cls.resolve_action_stealth(action, state)
        if stealth_info:
            s_res = stealth_info["result"]
            s_obs = stealth_info["observer"]
            fact_sheet.stealth_summary = s_res.narrative_ko
            if s_res.success:
                fact_sheet.quest_progress_logs.append(f"🥷 잠입 성공: {s_res.narrative_ko}")
                if "player" not in state_delta:
                    state_delta["player"] = {}
                state_delta["player_stealthed"] = True
            else:
                fact_sheet.quest_progress_logs.append(f"🚨 잠입 발각: {s_res.narrative_ko}")
                if s_obs and getattr(s_obs, "id", None) in state.npcs:
                    if "npc_state" not in state_delta:
                        state_delta["npc_state"] = {}
                    if s_obs.id not in state_delta["npc_state"]:
                        state_delta["npc_state"][s_obs.id] = {}
                    state_delta["npc_state"][s_obs.id]["disposition"] = "hostile"

        # 2.47 Field Harvesting & Butchering Resolution (AnatomyHarvestEngine)
        harvest_info = cls.resolve_action_harvest(action, state)
        if harvest_info:
            h_out = harvest_info["outcome"]
            fact_sheet.harvest_summary = h_out.narration_ko
            fact_sheet.quest_progress_logs.append(h_out.narration_ko)
            if h_out.success:
                if "player" not in state_delta:
                    state_delta["player"] = {}
                state_delta["player"]["inventory"] = list(state.player.inventory)
                QuestEngine.progress_event(state, "harvest", h_out.item_id)

        # 2.48 Campsite Setup, Campfire, Sentry & Night Rest Resolution (CampsiteRestEngine)
        campsite_info = cls.resolve_action_campsite(action, state)
        if campsite_info:
            fact_sheet.campsite_summary = campsite_info["summary"]
            fact_sheet.quest_progress_logs.extend(campsite_info.get("logs", []))
            if "active_campsite" not in state_delta:
                state_delta["active_campsite"] = campsite_info["camp"].to_dict()

            if campsite_info["type"] == "setup":
                state_delta["time_minutes"] = 30
            elif campsite_info["type"] == "sentry":
                state_delta["time_minutes"] = 10
            elif campsite_info["type"] == "campfire":
                state_delta["time_minutes"] = 15
                f_id = campsite_info.get("consumed_firewood_id")
                if f_id and f_id in state.player.inventory:
                    if "player" not in state_delta:
                        state_delta["player"] = {}
                    new_inv = list(state.player.inventory)
                    new_inv.remove(f_id)
                    state_delta["player"]["inventory"] = new_inv
            elif campsite_info["type"] == "night_rest":
                n_res = campsite_info.get("night_res", {})
                if n_res.get("ambush_triggered"):
                    state_delta["time_minutes"] = 180  # 자정 기습까지 3시간
                    if n_res.get("is_surprise_attack"):
                        StatusEffectEngine.apply_status(state.player, "stunned", duration=1, potency=1)
                        fact_sheet.quest_progress_logs.append("💥 [불시 기습 피격] 잠결에 무방비로 기습당해 1턴간 충격(Stun) 상태에 빠집니다!")
                else:
                    state_delta["time_minutes"] = 480  # 8시간 완전 숙면
                    heal_hp = int(state.player.max_health * 0.3)
                    heal_mp = int(state.player.max_mana_effective * 0.5)
                    state.player.health = min(state.player.max_health, state.player.health + heal_hp)
                    state.player.mana = min(state.player.max_mana_effective, state.player.mana + heal_mp)
                    if "player" not in state_delta:
                        state_delta["player"] = {}
                    state_delta["player"]["health"] = state.player.health
                    state_delta["player"]["mana"] = state.player.mana
                    state_delta["player"]["fatigue"] = state.player.fatigue
                    state_delta["player"]["alcohol_state"] = dict(state.player.alcohol_state)

            QuestEngine.progress_event(state, "campsite", campsite_info["type"])

        # 2.49 Alcohol Drinking Resolution (AlcoholIntoxicationEngine)
        drink_info = cls.resolve_action_drink(action, state)
        if drink_info:
            fact_sheet.alcohol_summary = drink_info["summary"]
            fact_sheet.quest_progress_logs.extend(drink_info.get("logs", []))
            state_delta["time_minutes"] = 15

            if "player" not in state_delta:
                state_delta["player"] = {}
            state_delta["player"]["alcohol_state"] = dict(state.player.alcohol_state)
            state_delta["player"]["gold"] = state.player.gold
            state_delta["player"]["fatigue"] = state.player.fatigue
            state_delta["player"]["body_temperature"] = state.player.body_temperature
            if hasattr(state.player, "wetness"):
                state_delta["player"]["wetness"] = state.player.wetness

            consumed_inv_id = drink_info.get("consumed_inventory_item_id")
            if consumed_inv_id and consumed_inv_id in state.player.inventory:
                new_inv = list(state.player.inventory)
                new_inv.remove(consumed_inv_id)
                state.player.inventory = new_inv
                state_delta["player"]["inventory"] = new_inv

            QuestEngine.progress_event(state, "drink", drink_info["drink_id"])

        # 2.495 Wild Botany & Herbalism Resolution (HerbalismBotanyEngine)
        botany_info = cls.resolve_action_botany(action, state)
        if botany_info:
            fact_sheet.botany_summary = botany_info["summary"]
            fact_sheet.quest_progress_logs.extend(botany_info.get("logs", []))

            b_type = botany_info.get("type")
            if b_type == "forage":
                state_delta["time_minutes"] = 20
            else:
                state_delta["time_minutes"] = 10

            if "player" not in state_delta:
                state_delta["player"] = {}
            state_delta["player"]["inventory"] = list(state.player.inventory)
            state_delta["player"]["health"] = state.player.health
            if hasattr(state.player, "stamina"):
                state_delta["player"]["stamina"] = state.player.stamina
            if hasattr(state.player, "hunger"):
                state_delta["player"]["hunger"] = state.player.hunger
            if hasattr(state.player, "mana"):
                state_delta["player"]["mana"] = state.player.mana

            QuestEngine.progress_event(state, "botany", b_type)

        # 2.5 Deterministic Movement Resolution (Guarantees actual location change)
        if travel_info:
            if "player" not in state_delta:
                state_delta["player"] = {}
            state_delta["player"]["location"] = travel_info["target_loc_id"]
            state_delta["time_minutes"] = travel_info["mins"]
            state_delta["fatigue_delta"] = travel_info["fatigue_inc"]

            # Update pending waypoints in state delta
            if "pending_waypoints" in travel_info:
                state_delta["pending_travel_waypoints"] = travel_info["pending_waypoints"]

            target_name = travel_info["target_name"]
            dist_km = travel_info["dist_km"]
            mins = travel_info["mins"]
            cond_info = travel_info["cond_info"]
            road_warn = travel_info["road_warn"]

            if travel_info.get("is_waypoint_advance"):
                rem_count = len(travel_info.get("pending_waypoints", []))
                rem_msg = f" (남은 경유지: {rem_count}개)" if rem_count > 0 else " (최종 목적지 도달)"
                fact_sheet.quest_progress_logs.append(
                    f"여정 전진: 이전 여로를 따라 [{target_name}]에 도착함 ({dist_km:.1f}km 이동, {mins}분 소요){rem_msg}"
                )
            elif travel_info.get("is_multi_hop") and travel_info.get("waypoints") and len(travel_info["waypoints"]) > 1:
                wp_names = " ➔ ".join([state.locations[wid].name if wid in state.locations else wid for wid in travel_info["waypoints"]])
                from_name = curr_loc.name if curr_loc else "현재 위치"
                fact_sheet.quest_progress_logs.append(
                    f"다중 구간 가도 이동 완료: [{from_name}]에서 최단 경로({wp_names})를 거쳐 [{target_name}]에 도착함 ({dist_km:.1f}km 이동, {mins}분 소요, 노면: {cond_info.get('name_ko', '정상')}){road_warn}"
                )
            else:
                fact_sheet.quest_progress_logs.append(
                    f"장소 이동 완료: [{target_name}]에 도착함 ({dist_km:.1f}km 이동, {mins}분 소요, 노면: {cond_info.get('name_ko', '정상')}){road_warn}"
                )

        # Default passage of time for minor actions if not moving
        # P1-6: uses TimeCalendarEngine.determine_action_duration() result instead of flat 10
        if "time_minutes" not in state_delta:
            state_delta["time_minutes"] = elapsed_minutes
        # Apply default_fatigue_delta from calendar engine (non-travel actions)
        if "fatigue_delta" not in state_delta and default_fatigue_delta != 0:
            state_delta["fatigue_delta"] = default_fatigue_delta

        # 2.5 Equipment Equip / Unequip Intent Execution
        equip_intent = fact_sheet.extra_flags.get("equip_intent")
        if equip_intent:
            e_act = equip_intent.get("action")
            e_item_id = equip_intent.get("item_id")
            e_item_name = equip_intent.get("item_name")
            e_slot = equip_intent.get("slot")
            if e_act == "equip":
                state_delta["equip_slot"] = {"item_id": e_item_id, "slot": e_slot}
                fact_sheet.quest_progress_logs.append(f"장비 착용: [{e_item_name}]을(를) {e_slot} 부위에 장착했습니다.")
            elif e_act == "unequip":
                state_delta["unequip_slot"] = {"item_id": e_item_id, "slot": e_slot}
                fact_sheet.quest_progress_logs.append(f"장비 해제: [{e_item_name}]을(를) {e_slot} 부위에서 해제했습니다.")

        # 2.6 Stat Allocation Intent Execution (WorldPowerScalePresets Integration)
        if any(k in action for k in ["스탯 투자", "스탯 분배", "능력치 투자", "스탯 올리기"]):
            stat_name_target = None
            for s_k, s_names in [
                ("strength", ["근력", "힘", "str"]),
                ("agility", ["민첩", "민", "dex", "agi"]),
                ("constitution", ["체질", "체력", "con"]),
                ("intelligence", ["지능", "int"]),
                ("wisdom", ["지혜", "wis"]),
                ("perception", ["감각", "인지", "per"]),
                ("luck", ["행운", "luk", "운"]),
            ]:
                if any(n in action for n in s_names):
                    stat_name_target = s_k
                    break
            if stat_name_target:
                state_delta["allocate_stat"] = {"stat_name": stat_name_target, "amount": 1}
                fact_sheet.quest_progress_logs.append(
                    f"스탯 투자 신청: [{stat_name_target}]에 스탯 포인트 1점 투자 (상한: {preset.stat_cap})"
                )

        # 2.7 Medical Treatment Execution
        treatment_intent = fact_sheet.extra_flags.get("treatment_intent")
        if treatment_intent:
            from src.world.injury_engine import InjuryEngine
            t_type = treatment_intent.get("type")
            inj_name = treatment_intent.get("injury_name")

            if t_type == "item":
                i_id = treatment_intent.get("item_id")
                if i_id and i_id in state.items:
                    item_obj = state.items[i_id]
                    success, msg, d_mod = InjuryEngine.apply_item_treatment(state, state.player, inj_name, item_obj)
                    if success:
                        fact_sheet.quest_progress_logs.append(msg)
                        if "player" not in state_delta:
                            state_delta["player"] = {}
                        if "inventory" not in state_delta["player"]:
                            new_inv = list(state.player.inventory)
                            if i_id in new_inv:
                                new_inv.remove(i_id)
                            state_delta["player"]["inventory"] = new_inv

                        if d_mod.get("cured"):
                            state_delta["remove_player_injury"] = inj_name
                        elif d_mod.get("splinted"):
                            state_delta["splint_player_injury"] = {
                                "injury_name": inj_name,
                                "turns_needed": d_mod.get("turns_needed", 2)
                            }
            elif t_type == "doctor":
                doc_id = treatment_intent.get("doctor_id")
                fee = treatment_intent.get("fee", 50)
                if doc_id and doc_id in state.npcs:
                    doc_npc = state.npcs[doc_id]
                    success, msg, d_mod = InjuryEngine.apply_doctor_surgery(state, doc_npc, state.player, inj_name, fee=fee)
                    fact_sheet.quest_progress_logs.append(msg)
                    if success:
                        if "player" not in state_delta:
                            state_delta["player"] = {}
                        state_delta["player"]["gold"] = max(0, state.player.gold - fee)
                        state_delta["remove_player_injury"] = inj_name

        # 2.75 Mana Circuit Repair Intent Execution
        # Sub-path A: quick item-based repair (mana stabilizer, silver needle, holy water)
        if any(k in action for k in ["마나 안정제", "마나안정제", "은침", "침술", "성수 정화", "성수", "회로 치료", "회로 수리"]):
            remedy = None
            if any(k in action for k in ["마나 안정제", "마나안정제", "안정제"]):
                remedy = "mana_stabilizer"
            elif any(k in action for k in ["은침", "침술", "소통술"]):
                remedy = "silver_needle_acupuncture"
            elif any(k in action for k in ["성수"]):
                remedy = "holy_water_purge"
            if remedy:
                rep_ok, rep_msg = ManaBurnEngine.repair_circuit(state.player, remedy)
                if rep_ok:
                    fact_sheet.quest_progress_logs.append(rep_msg)
                    p_circuit = ManaBurnEngine.get_circuit_state(state.player)
                    if "player" not in state_delta:
                        state_delta["player"] = {}
                    state_delta["player"]["mana_burn_state"] = p_circuit.to_dict()

        # Sub-path B: full surgical restoration (arcane surgery / herbal tonic / divine miracle)
        # Requires MANA-CIRCUIT-SPECIFIC keywords — must NOT fire on generic physical surgery.
        # Guard: only triggers when player's mana circuit has actual damage (vein_integrity_pct < 100).
        MANA_SURGERY_KEYWORDS = [
            "탕약", "투석", "기적 봉합", "회로 재건", "혈맥 수술",
            "비전 의사", "에테르 투석", "성맥 재건", "회로 복구 수술",
            "마나 회로 수술", "마나 혈맥 수술",
        ]
        if any(k in action for k in MANA_SURGERY_KEYWORDS):
            # Pre-guard: only trigger if circuit is actually damaged
            _circuit_check = getattr(state.player, "mana_burn_state", None)
            _has_damage = False
            if _circuit_check is not None:
                if isinstance(_circuit_check, dict):
                    _has_damage = _circuit_check.get("vein_integrity_pct", 100.0) < 100.0
                elif hasattr(_circuit_check, "vein_integrity_pct"):
                    _has_damage = _circuit_check.vein_integrity_pct < 100.0

            if _has_damage:
                # 1. Pick surgeon: first doctor/healer NPC in current location, else player self-treatment
                surgeon = state.player
                curr_loc_id = state.player.location
                for npc_id, npc in state.npcs.items():
                    if npc.location == curr_loc_id:
                        npc_traits = set(getattr(npc, "traits", []))
                        if npc_traits.intersection({"doctor", "healer", "arcane_surgeon", "priest", "cleric", "의사", "사제", "집도의"}):
                            surgeon = npc
                            break

                # 2. Determine surgery_id from keywords
                surgery_id = "silver_needle_acupuncture"  # default
                if any(k in action for k in ["탕약", "영지", "농축"]):
                    surgery_id = "herbal_vein_decoction"
                elif any(k in action for k in ["투석", "비전 의사", "에테르 투석"]):
                    surgery_id = "arcane_dialysis_surgery"
                elif any(k in action for k in ["성맥", "기적 봉합", "성령", "성직자", "사제"]):
                    surgery_id = "divine_artery_miracle"

                # Only run if surgery type exists in registry
                if surgery_id in VEIN_SURGERY_REGISTRY:
                    surg_ok, surg_msg, surg_data = ManaVeinRestorationEngine.perform_surgery(
                        state, state.player, surgeon, surgery_id
                    )
                    fact_sheet.quest_progress_logs.append(surg_msg)
                    fact_sheet.vein_restoration_summary = surg_msg

                    if "player" not in state_delta:
                        state_delta["player"] = {}
                    # Sync gold change (perform_surgery already mutated patient.gold)
                    state_delta["player"]["gold"] = state.player.gold
                    state_delta["player"]["health"] = state.player.health
                    # Persist circuit state
                    p_circuit = ManaVeinRestorationEngine.get_circuit_state(state.player)
                    state_delta["player"]["mana_burn_state"] = (
                        p_circuit.to_dict() if hasattr(p_circuit, "to_dict") else p_circuit
                    )

        # 3. Environmental Puzzles & Mechanisms
        puzzle_res = PuzzleEngine.evaluate_puzzle_action(state, action)
        if puzzle_res and puzzle_res.get("is_solved"):
            fact_sheet.puzzle_logs.append(puzzle_res["solve_message"])
            fact_sheet.quest_progress_logs.append(f"퍼즐 해결: {puzzle_res['puzzle_name']} (경험치 +{puzzle_res['reward_exp']})")

        # 4. Bounty Hunter Ambushes
        ambush_info = BountyEngine.check_bounty_hunter_ambush(state, action)
        if ambush_info:
            fact_sheet.bounty_logs.append(ambush_info["summary_ko"])

        # 5. Physics & Chemistry Matrix evaluation
        curr_loc = state.current_location()
        loc_desc = f"{curr_loc.name} {curr_loc.description}" if curr_loc else ""
        inv_item_names = [state.items[i].name for i in state.player.inventory if i in state.items]
        physics_reactions = PhysicsMatrixEngine.evaluate(action, loc_desc, inv_item_names)
        fact_sheet.physics_reactions = [getattr(rx, "description", getattr(rx, "description_ko", str(rx))) for rx in physics_reactions]

        for rx in physics_reactions:
            if rx.status_to_apply:
                target_obj = state.npcs[dice_res.target_npc_id] if (dice_res and dice_res.target_npc_id and dice_res.target_npc_id in state.npcs) else state.player
                StatusEffectEngine.apply_status(target_obj, rx.status_to_apply, duration=rx.status_duration, potency=rx.status_potency)

        # 5.1 Universal Object Physics & Durability Engine (Destruction / Burning)
        burn_keywords = ["태운다", "불태", "소각", "burn", "화염으로", "불지른", "불을 지른"]
        smash_keywords = ["부순다", "박살", "파괴", "smash", "destroy", "부수", "깨뜨", "깨부", "망가뜨", "후려쳐"]
        
        is_burn_act = any(k in action for k in burn_keywords)
        is_smash_act = any(k in action for k in smash_keywords)

        if is_burn_act or is_smash_act:
            cand_items = []
            if curr_loc:
                for it_id in getattr(curr_loc, "items", []):
                    if it_id in state.items and state.items[it_id] not in cand_items:
                        cand_items.append(state.items[it_id])
                for it in state.items.values():
                    if getattr(it, "location", "") == curr_loc.id and it not in cand_items:
                        cand_items.append(it)
            for it_id in state.player.inventory:
                if it_id in state.items and state.items[it_id] not in cand_items:
                    cand_items.append(state.items[it_id])

            target_obj_item = None
            sorted_cand = sorted(cand_items, key=lambda x: len(x.name), reverse=True)
            for c_item in sorted_cand:
                if c_item.name and (c_item.name in action or c_item.id in action):
                    target_obj_item = c_item
                    break
                for w in c_item.name.split():
                    if len(w) >= 2 and w in action:
                        target_obj_item = c_item
                        break
                if target_obj_item:
                    break

            if not target_obj_item and curr_loc:
                ambient_keywords = ["의자", "탁자", "책상", "상자", "궤짝", "문짝", "술통", "나무통", "유리병", "횃불", "창문"]
                for kw in ambient_keywords:
                    if kw in action:
                        ambient_id = f"env_{kw}_{state.turn}_{random.randint(100, 999)}"
                        ambient_item = Item(
                            id=ambient_id,
                            name=f"{curr_loc.name} {kw}",
                            description=f"{curr_loc.name}에 놓여 있던 {kw}.",
                            location=curr_loc.id,
                            durability=50,
                            max_durability=50
                        )
                        state.items[ambient_id] = ambient_item
                        if ambient_id not in curr_loc.items:
                            curr_loc.items.append(ambient_id)
                        target_obj_item = ambient_item
                        break

            if target_obj_item:
                if is_burn_act:
                    obj_res = UniversalObjectPhysicsEngine.ignite_object(state, target_obj_item)
                else:
                    raw_dmg = 50.0
                    eq_wep = state.get_equipped_weapon_item()
                    if eq_wep and getattr(eq_wep, "damage", 0) > 0:
                        raw_dmg = max(30.0, float(eq_wep.damage * 3.0))
                    obj_res = UniversalObjectPhysicsEngine.damage_object(
                        state=state,
                        item_or_id=target_obj_item,
                        raw_damage=raw_dmg,
                        damage_type="blunt",
                        attacker_name=state.player.name
                    )

                if obj_res.narrative_log:
                    fact_sheet.physics_reactions.append(obj_res.narrative_log)

                if obj_res.is_destroyed:
                    if "destroyed_items" not in state_delta:
                        state_delta["destroyed_items"] = []
                    state_delta["destroyed_items"].append(target_obj_item.id)
                if obj_res.debris_spawned:
                    if "spawned_debris" not in state_delta:
                        state_delta["spawned_debris"] = []
                    state_delta["spawned_debris"].extend([d.id for d in obj_res.debris_spawned])

        # 6. Dice & Combat Mechanics
        target_npc = None
        if dice_res:
            fact_sheet.dice_result = {
                "action_type": dice_res.action_type,
                "d20_roll": dice_res.d20_roll,
                "modifier": dice_res.modifier,
                "total": dice_res.total,
                "dc": dice_res.dc,
                "is_success": dice_res.is_success,
                "damage_dealt": dice_res.damage_dealt,
                "target_npc_id": dice_res.target_npc_id,
                "summary_ko": dice_res.summary_ko,
            }

            if dice_res.target_npc_id and dice_res.target_npc_id in state.npcs:
                target_npc = state.npcs[dice_res.target_npc_id]
                target_npc.stats_revealed = True
                
                # Combat damage computation
                if dice_res.is_success and dice_res.damage_dealt > 0:
                    raw_damage = dice_res.damage_dealt
                    target_part = fact_sheet.extra_flags.get("target_part", "")

                    # 1. Physics Tags & Kinetic Momentum Extraction
                    eq_wep = state.get_equipped_weapon_item()
                    atk_tags = []
                    action_lower_comb = action.lower()
                    if eq_wep:
                        w_tags = getattr(eq_wep, "physics_tags", []) or []
                        w_name = eq_wep.name.lower()
                        w_props = getattr(eq_wep, "properties", {}) or {}
                        w_type = w_props.get("weapon_type", "") or getattr(eq_wep, "weapon_type", "")
                        for t in w_tags:
                            if t not in atk_tags:
                                atk_tags.append(t)
                        if any(k in w_type or k in w_name for k in ["sword", "axe", "dagger", "blade", "도", "검", "도끼", "참격"]):
                            if "slash" not in atk_tags:
                                atk_tags.append("slash")
                        if any(k in w_type or k in w_name for k in ["mace", "hammer", "club", "둔기", "망치", "타격"]):
                            if "blunt" not in atk_tags:
                                atk_tags.append("blunt")
                        if any(k in w_type or k in w_name for k in ["spear", "bow", "arrow", "thrust", "창", "활", "관통", "레이피어"]):
                            if any(k in w_type or k in w_name for k in ["bow", "arrow", "활"]):
                                if "projectile" not in atk_tags:
                                    atk_tags.append("projectile")
                            else:
                                if "thrust" not in atk_tags:
                                    atk_tags.append("thrust")

                    # Action keywords for attack types
                    if any(k in action_lower_comb for k in ["찌른", "찔러", "관통", "내지른", "thrust"]):
                        if "thrust" not in atk_tags:
                            atk_tags.append("thrust")
                    if any(k in action_lower_comb for k in ["베어", "베는", "참격", "가르고", "휘둘러", "slash"]):
                        if "slash" not in atk_tags:
                            atk_tags.append("slash")
                    if any(k in action_lower_comb for k in ["내려친", "후려친", "둔기", "강타", "망치", "blunt", "strike"]):
                        if "blunt" not in atk_tags:
                            atk_tags.append("blunt")
                    if any(k in action_lower_comb for k in ["잽", "견제타", "빠르게 찔러", "간보기", "jab"]):
                        if "jab" not in atk_tags:
                            atk_tags.append("jab")
                    if any(k in action_lower_comb for k in ["정권", "스트레이트", "체중을 실어", "straight"]):
                        if "straight" not in atk_tags:
                            atk_tags.append("straight")
                    if any(k in action_lower_comb for k in ["활을", "화살", "석궁", "사격", "발사", "투척", "projectile", "shoot"]):
                        if "projectile" not in atk_tags:
                            atk_tags.append("projectile")

                    if not atk_tags:
                        atk_tags.append("slash")

                    # Charge momentum
                    charge_dist = 0.0
                    if any(k in action_lower_comb for k in ["돌진", "달려들며", "뛰어들며", "돌격"]):
                        charge_dist = 5.0

                    target_action = getattr(target_npc, "current_intent", "") or getattr(target_npc, "action", "")

                    # Evaluate attack physics
                    phys_res = AttackPhysicsEngine.evaluate_attack_physics(
                        attacker=state.player,
                        defender=target_npc,
                        weapon=eq_wep,
                        attack_tags=atk_tags,
                        distance_charge_m=charge_dist,
                        target_current_action=target_action
                    )
                    fact_sheet.attack_physics_summary = phys_res.summary_ko
                    fact_sheet.quest_progress_logs.append(f"⚔️ [물리 타격] {phys_res.summary_ko}")
                    raw_damage = max(1, int(round(raw_damage + phys_res.physics_damage_bonus)))

                    # Check if AoE skill or whole-body attack
                    skill_info = fact_sheet.extra_flags.get("player_skill_used")
                    is_aoe = False
                    sk_obj = None
                    if skill_info:
                        sk_id = skill_info.get("skill_id")
                        sk_obj = state.skills_db.get(sk_id)
                        if sk_obj and (sk_obj.area_shape in ["circle", "cone", "line", "sphere"] or getattr(sk_obj, "area_radius_meters", 0) > 0):
                            is_aoe = True

                    from src.world.equipment import EquipmentEngine
                    matched_part_id = None
                    if hasattr(target_npc, "anatomy_parts") and target_npc.anatomy_parts:
                        for pid, pobj in target_npc.anatomy_parts.items():
                            p_name = pobj.name_ko if hasattr(pobj, "name_ko") else pobj.get("name_ko", "")
                            tokens = [t for t in re.split(r'[\s_]+', p_name) if len(t) >= 2]
                            if (target_part and (target_part in p_name or p_name in target_part or pid == target_part)) or p_name in action or pid in action or any(t in action for t in tokens):
                                matched_part_id = pid
                                break
                        if not matched_part_id:
                            for pid, pobj in target_npc.anatomy_parts.items():
                                p_name = pobj.name_ko if hasattr(pobj, "name_ko") else pobj.get("name_ko", "")
                                combined = f"{p_name} {pid.lower()}"
                                if any(k in action or k in target_part for k in ["뿔", "뇌각", "각"]) and any(k in combined for k in ["뿔", "각", "horn"]):
                                    matched_part_id = pid
                                    break
                                if any(k in action or k in target_part for k in ["꼬리", "미부"]) and any(k in combined for k in ["꼬리", "tail"]):
                                    matched_part_id = pid
                                    break
                                if any(k in action or k in target_part for k in ["날개", "익부"]) and any(k in combined for k in ["날개", "wing"]):
                                    matched_part_id = pid
                                    break
                                if any(k in action or k in target_part for k in ["머리", "두부"]) and any(k in combined for k in ["머리", "head"]):
                                    matched_part_id = pid
                                    break

                    # If AoE: cannot pinpoint specific anatomy, hits full body (chest/cape)
                    if is_aoe:
                        actual_part = "chest"
                        mitigated_dmg, armor_logs = EquipmentEngine.apply_armor_durability_and_mitigation(
                            state, target_npc, raw_damage, target_part="chest", armor_penetration_pct=phys_res.armor_penetration_pct
                        )
                        elem = sk_obj.element if sk_obj else "물리"
                        injury_name = "전신 화상" if "화염" in elem else ("폭압 타박상" if "대지" in elem or "충격" in elem else "파편 열상")
                        if injury_name not in target_npc.injuries:
                            target_npc.injuries.append(injury_name)
                        target_npc.morale = max(0, target_npc.morale - 20)
                    elif matched_part_id:
                        # 몬스터 해부학 부위 타격 판정 (AnatomyHarvestEngine)
                        actual_part = target_npc.anatomy_parts[matched_part_id].name_ko if hasattr(target_npc.anatomy_parts[matched_part_id], "name_ko") else matched_part_id
                        part_res = AnatomyHarvestEngine.attack_targeted_part(
                            target_npc, matched_part_id, raw_damage, attack_tags=atk_tags, state=state
                        )
                        mitigated_dmg = part_res.effective_damage
                        fact_sheet.quest_progress_logs.append(part_res.combat_log_ko)

                        if part_res.is_now_severed:
                            fact_sheet.harvest_summary = f"💥【신체 절단!】 [{target_npc.name}]의 [{part_res.part_name_ko}]이(가) 날카로운 참격에 잘려나가 바닥에 떨어졌습니다!"
                            target_npc.morale = max(0, target_npc.morale - 30)
                        elif part_res.is_now_broken:
                            fact_sheet.harvest_summary = f"💥【부위 파괴!】 [{target_npc.name}]의 [{part_res.part_name_ko}]이(가) 완전히 파괴되어 큰 경직에 빠졌습니다!"
                            target_npc.morale = max(0, target_npc.morale - 20)
                        elif part_res.stagger_inflicted:
                            target_npc.morale = max(0, target_npc.morale - 15)
                    elif target_part:
                        actual_part = target_part
                        mitigated_dmg, armor_logs = EquipmentEngine.apply_armor_durability_and_mitigation(
                            state, target_npc, raw_damage, target_part=target_part, armor_penetration_pct=phys_res.armor_penetration_pct
                        )
                        injury_map = {
                            "머리": ("머리 충격(뇌진탕)", 20),
                            "목": ("경추 손상", 25),
                            "눈": ("안구 손상(시력 감퇴)", 30),
                            "가슴": ("흉부 관통상", 25),
                            "심장": ("흉부 치명상", 35),
                            "팔": ("팔 관절 손상", 15),
                            "손": ("손목 골절", 15),
                            "다리": ("다리 골절/힘줄 파열", 20),
                            "발": ("발목 부상", 15),
                            "꼬리": ("꼬리 손상", 15),
                            "뿔": ("뿔 손상", 15),
                            "날개": ("날개 파열", 20),
                        }
                        inj_name, morale_loss = injury_map.get(target_part, (f"{target_part} 부상", 15))
                        if inj_name not in target_npc.injuries:
                            target_npc.injuries.append(inj_name)
                        target_npc.morale = max(0, target_npc.morale - morale_loss)
                    else:
                        actual_part = "chest"
                        mitigated_dmg, armor_logs = EquipmentEngine.apply_armor_durability_and_mitigation(
                            state, target_npc, raw_damage, target_part="chest", armor_penetration_pct=phys_res.armor_penetration_pct
                        )

                    # Apply physics combat side effects
                    if phys_res.bleed_inflicted:
                        StatusEffectEngine.apply_status(target_npc, "bleeding", duration=3, potency=max(3, int(raw_damage * 0.2)))
                        fact_sheet.status_tick_logs.append(f"🩸 [출혈 유발] 예리한 참격이 혈관을 갈라 [{target_npc.name}]에게 출혈 상태이상을 유발했습니다!")
                    if phys_res.bone_fracture_risk:
                        fracture_name = f"{actual_part} 타박 골절"
                        if fracture_name not in target_npc.injuries:
                            target_npc.injuries.append(fracture_name)
                            fact_sheet.quest_progress_logs.append(f"🦴 [골절 유발] 육중한 둔기 충격으로 [{target_npc.name}]의 {actual_part}에 골절이 발생했습니다!")
                    if phys_res.interrupted_action:
                        target_npc.current_intent = ""
                        target_npc.morale = max(0, target_npc.morale - 15)
                        fact_sheet.quest_progress_logs.append(f"⚡ [행동 캔슬] {phys_res.interrupt_reason}")
                    if hasattr(target_npc, "poise") and phys_res.stagger_inflicted > 0:
                        target_npc.poise = max(0.0, target_npc.poise - phys_res.stagger_inflicted)

                    hp_before = target_npc.health
                    hp_after = max(0, hp_before - mitigated_dmg)
                    is_alive = hp_after > 0
                    killed = (hp_before > 0 and hp_after <= 0)

                    fact_sheet.combat_outcome = {
                        "target_id": target_npc.id,
                        "target_name": target_npc.name,
                        "damage_dealt": mitigated_dmg,
                        "raw_damage": raw_damage,
                        "target_part": actual_part,
                        "is_aoe": is_aoe,
                        "target_injuries": list(target_npc.injuries),
                        "hp_before": hp_before,
                        "hp_after": hp_after,
                        "max_hp": target_npc.max_health,
                        "target_alive": is_alive,
                        "killed": killed,
                    }

                    if "npc_state" not in state_delta:
                        state_delta["npc_state"] = {}
                    state_delta["npc_state"][target_npc.id] = {
                        "health": hp_after,
                        "alive": is_alive,
                        "disposition": "hostile",
                        "stats_revealed": True,
                        "injuries": list(target_npc.injuries),
                        "morale": target_npc.morale,
                    }

                    # Equipment Wear & Rune Effects on Weapon
                    eq_wep = state.get_equipped_weapon_item()
                    if eq_wep:
                        dur_warn = EnchantEngine.consume_durability(eq_wep, loss=1)
                        if dur_warn:
                            fact_sheet.enchant_logs.append(dur_warn)
                        rune_logs = EnchantEngine.evaluate_rune_combat_effects(state, eq_wep, dice_res.damage_dealt, target_npc=target_npc)
                        fact_sheet.enchant_logs.extend(rune_logs)

                    # Kill events & Unique skill drops
                    if killed:
                        QuestEngine.progress_event(state, "kill", target_npc.id)
                        from src.world.corpse_ecology_engine import CorpseEcologyEngine
                        CorpseEcologyEngine.register_corpse_from_killed_actor(state, target_npc, killer=state.player)
                        fact_sheet.quest_progress_logs.append(f"전장 시체 발생: [{target_npc.name}]의 유해가 쓰러졌습니다.")

                        # --- Witness Gate: 현장에 생존한 제3자 NPC 목격자 검사 (완전 범죄 밀실 암살 지원) ---
                        event_loc = getattr(target_npc, "location", "") or state.player.location
                        candidate_npc_ids = set()
                        for loc_key in filter(None, [event_loc, state.player.location]):
                            if loc_key in state.locations:
                                candidate_npc_ids.update(getattr(state.locations[loc_key], "npcs", []))
                            for nid, n_obj in state.npcs.items():
                                if getattr(n_obj, "location", "") == loc_key:
                                    candidate_npc_ids.add(nid)

                        party_ids = set()
                        if hasattr(state, "party") and state.party:
                            for p in state.party:
                                pid = getattr(p, "companion_id", None) or getattr(p, "id", None)
                                if pid:
                                    party_ids.add(pid)

                        witnesses = []
                        for nid in candidate_npc_ids:
                            if nid == target_npc.id or nid in party_ids:
                                continue
                            w_obj = state.npcs.get(nid)
                            if not w_obj:
                                continue
                            if getattr(w_obj, "alive", True) and getattr(w_obj, "health", 1) > 0:
                                witnesses.append(w_obj)

                        if witnesses:
                            from src.world.rumor_diffusion_engine import RumorDiffusionEngine
                            sig = 3 if getattr(target_npc, "tier", "commoner") in ["elite", "boss", "noble", "legendary"] else 2
                            rep_delta = 15 if target_npc.disposition == "hostile" else -20
                            RumorDiffusionEngine.dispatch_event_rumor(
                                state=state,
                                origin_loc=state.player.location,
                                event_text=f"플레이어가 [{target_npc.name}]을(를) 치명적 결투 끝에 처치함",
                                significance=sig,
                                reputation_delta=rep_delta,
                                carrier="merchant"
                            )
                            witness_names = ", ".join([w.name for w in witnesses[:3]])
                            fact_sheet.quest_progress_logs.append(
                                f"소문 확산 시작: 현장 목격자({witness_names} 등 {len(witnesses)}명)에 의해 [{target_npc.name}] 처치 소식이 상단 가도를 타고 퍼져나갑니다. (파급력 Lv.{sig})"
                            )
                        else:
                            fact_sheet.quest_progress_logs.append(
                                f"은밀한 처치: 현장에 목격자가 없어 [{target_npc.name}] 처치 소문이 퍼지지 않았습니다. (완전 범죄)"
                            )

                        dropped_skill_id = SkillSystem.roll_unique_skill_drop(target_npc, state.player)
                        if dropped_skill_id:
                            sk_obj = state.skills_db.get(dropped_skill_id)
                            fact_sheet.dropped_skill_name = sk_obj.name if sk_obj else dropped_skill_id
                            if "grant_skill" not in state_delta:
                                state_delta["grant_skill"] = {}
                            state_delta["grant_skill"]["player"] = dropped_skill_id

                        # EXP reward scaled by PowerScalePreset
                        base_exp = 50 if getattr(target_npc, "tier", "") in ["elite", "boss", "legendary"] else 25
                        exp_earned = int(base_exp * preset.exp_multiplier)
                        lvl_res = state.player.add_exp(exp_earned, preset)
                        if lvl_res.get("leveled_up"):
                            if "player" not in state_delta:
                                state_delta["player"] = {}
                            state_delta["player"]["level"] = state.player.level
                            state_delta["player"]["stat_points"] = state.player.stat_points
                            state_delta["player"]["max_health"] = state.player.max_health
                            state_delta["player"]["max_mana"] = state.player.max_mana
                            fact_sheet.quest_progress_logs.append(
                                f"⭐ [레벨업]: +{exp_earned} EXP 획득! 레벨 {state.player.level} 달성 (세계관 규격: {preset.name_ko})"
                            )
                            if lvl_res.get("current_realm"):
                                fact_sheet.quest_progress_logs.append(
                                    f"⚡ [선협 경지 돌파]: {lvl_res.get('current_realm')} 경지에 도달하여 전신 스탯이 {preset.breakthrough_multiplier}배 폭증했습니다!"
                                )
                        else:
                            fact_sheet.quest_progress_logs.append(
                                f"⭐ [경험치 획득]: +{exp_earned} EXP"
                            )

        # 6.5 Player Skill Resource Deduction & Cooldown Application
        skill_info = fact_sheet.extra_flags.get("player_skill_used")
        if skill_info:
            sk_id = skill_info.get("skill_id")
            sk_name = skill_info.get("skill_name", "스킬")
            sk_res_type = skill_info.get("resource_type", "mana")
            sk_cost = skill_info.get("resource_cost", 0)
            sk_cd = skill_info.get("cooldown_turns", 0)

            if sk_res_type == "mana":
                overchannel_res = fact_sheet.extra_flags.get("overchannel")
                if overchannel_res:
                    # 과충전 생명력 연소 및 반동 처리
                    logs = ManaBurnEngine.apply_overchannel_consequences(state.player, overchannel_res, state)
                    p_circuit = ManaBurnEngine.get_circuit_state(state.player)
                    state.player.mana = 0
                    if "player" not in state_delta:
                        state_delta["player"] = {}
                    state_delta["player"]["mana"] = 0
                    state_delta["player"]["health"] = state.player.health
                    state_delta["player"]["mana_burn_state"] = p_circuit.to_dict()
                    fact_sheet.mana_burn_summary = "\n".join(logs)
                    fact_sheet.quest_progress_logs.extend(logs)
                else:
                    state.player.mana = max(0, state.player.mana - sk_cost)
                    if "player" not in state_delta:
                        state_delta["player"] = {}
                    state_delta["player"]["mana"] = state.player.mana

                    # 손상된 회로로 인한 신경통/기력 소모 페널티
                    p_circuit = ManaBurnEngine.get_circuit_state(state.player)
                    if p_circuit.stamina_drain_on_cast > 0:
                        from src.world.stamina_engine import StaminaEngine
                        StaminaEngine.consume(state.player, p_circuit.stamina_drain_on_cast)
                        fact_sheet.status_tick_logs.append(
                            f"⚡ [회로 신경통] 손상된 마나 회로의 과부하로 기력이 {p_circuit.stamina_drain_on_cast} 소모되었습니다."
                        )
            elif sk_res_type == "hp":
                state.player.health = max(1, state.player.health - sk_cost)
                if "player" not in state_delta:
                    state_delta["player"] = {}
                state_delta["player"]["health"] = state.player.health
            elif sk_res_type == "stamina":
                from src.world.stamina_engine import StaminaEngine
                c_res = StaminaEngine.consume(state.player, sk_cost)
                if "player" not in state_delta:
                    state_delta["player"] = {}
                state_delta["player"]["stamina"] = state.player.stamina
                if c_res.get("triggered_exhaustion"):
                    fact_sheet.status_tick_logs.append("⚠️ [기력 고갈] 신체 한계에 도달하여 탈진(Exhaustion) 상태에 빠졌습니다! (방어력/행동 제약)")

            if sk_id in state.skills_db:
                state.skills_db[sk_id].current_cooldown = sk_cd

            # Subterranean impact & oxygen consumption (CaveCollapseEngine)
            curr_loc = state.current_location()
            if curr_loc and (getattr(curr_loc, "location_category", "") == "dungeon" or getattr(curr_loc, "floor_depth", 0) > 0 or "지하" in getattr(curr_loc, "name", "")):
                from src.world.cave_in_engine import CaveCollapseEngine
                sk_name = skill_info.get("name", "")
                sk_elem = skill_info.get("element", "")
                is_fire = any(f in (sk_name + sk_elem) for f in ["화염", "불꽃", "폭발", "이그니스", "fire"])
                is_blunt = any(b in (sk_name + sk_elem) for b in ["강타", "둔기", "파쇄", "대지", "earth"])

                if is_fire:
                    oxy_logs = CaveCollapseEngine.consume_oxygen(state, amount=5.0, reason=sk_name)
                    fact_sheet.status_tick_logs.extend(oxy_logs)
                    _, _, vib_logs = CaveCollapseEngine.apply_vibration(curr_loc, "fireball_explosion", magic_circle=skill_info.get("magic_circle", 2), state=state)
                    fact_sheet.status_tick_logs.extend(vib_logs)
                elif is_blunt:
                    _, _, vib_logs = CaveCollapseEngine.apply_vibration(curr_loc, "heavy_blunt_strike", state=state)
                    fact_sheet.status_tick_logs.extend(vib_logs)

            # Conceptual Magic: Rule modifications
            if fact_sheet.extra_flags.get("conceptual_distance_zero"):
                if hasattr(state, "combat_distances"):
                    target_id = target_npc.id if target_npc else ""
                    state.combat_distances.set_distance("player", target_id, 0.0)
                fact_sheet.status_tick_logs.append("🌌 [개념마법] 「거리」라는 개념을 소멸시켜 적과 칼끝을 영거리(0m)로 겹쳤습니다!")

            if fact_sheet.extra_flags.get("conceptual_sound_seal"):
                fact_sheet.extra_flags["noise_level"] = "silent"
                fact_sheet.status_tick_logs.append("🌌 [개념마법] 「소리」라는 개념을 봉인하여 절대 무음 상태를 전개했습니다.")

            if fact_sheet.extra_flags.get("conceptual_wound_erase"):
                state.player.injuries.clear()
                fact_sheet.status_tick_logs.append("🌌 [개념마법] 「상처」라는 개념을 제거하여 모든 골절과 외상을 말소했습니다.")

            # Spatiotemporal Magic: Space severance / time lag
            if fact_sheet.extra_flags.get("spatiotemporal_space_severance") and target_npc and target_npc.alive:
                StatusEffectEngine.apply_status(target_npc, "stun", duration=1, potency=1)
                fact_sheet.status_tick_logs.append(f"⏳ [시공간마법] 대상 [{target_npc.name}]의 시공간 좌표를 절단하여 방어력을 100% 무시하고 1턴간 시공간 정지(기절) 부여!")

            # If attack hit living target, apply inflicted status effects
            if dice_res and dice_res.is_success and target_npc and target_npc.alive:
                inflicted = skill_info.get("inflicted_status", [])
                for st in inflicted:
                    s_name = st.get("status")
                    dur = st.get("duration_turns", st.get("duration", 2))
                    pot = st.get("dot_damage_per_turn", st.get("potency", 5))
                    if s_name:
                        StatusEffectEngine.apply_status(target_npc, s_name, duration=dur, potency=pot)
                        fact_sheet.status_tick_logs.append(f"적 [{target_npc.name}]에게 [{sk_name}] 효과로 상태이상 [{s_name}]({dur}턴) 부여")

        # 7. Quest Progress Hooks (location reach)
        QuestEngine.progress_event(state, "reach", state.player.location)

        # 7.5 Deterministic Gold Payment / Expense Detection
        gold_match = re.search(r'(\d+)\s*(?:골드|은화|플로린|닢|G|g)(?:를|을|의|로|)?\s*(?:던져|건네|지불|내놓|주며|주고|내며|바치)', action)
        if gold_match:
            paid_amount = int(gold_match.group(1))
            if state.player.gold >= paid_amount:
                state.player.gold -= paid_amount
                if "player" not in state_delta:
                    state_delta["player"] = {}
                state_delta["player"]["gold"] = state.player.gold
                fact_sheet.quest_progress_logs.append(f"💰 {paid_amount}G 지불 완료 (잔여 골드: {state.player.gold}G)")
                if target_npc:
                    target_npc.gold = getattr(target_npc, "gold", 0) + paid_amount

        # 7.6 Logos Indiscriminate Friendly Fire AoE
        if fact_sheet.extra_flags.get("is_friendly_fire_aoe") and dice_res and dice_res.is_success:
            loc_id = state.player.location
            for n_id, n_obj in state.npcs.items():
                if n_obj.location == loc_id and n_obj.alive and n_id != (target_npc.id if target_npc else ""):
                    StatusEffectEngine.apply_status(n_obj, "stun", duration=1, potency=1)
                    n_obj.health = max(1, n_obj.health - 10)
                    fact_sheet.status_tick_logs.append(f"💥 [언령 무차별 광역] 진명 없는 원초 포효가 주변의 [{n_obj.name}]에게도 작렬하여 10 피해 및 기절(1턴)을 입혔습니다!")

        # 7.7 Backfire Damage on Failed Magic / Logos Backlash
        if dice_res and not dice_res.is_success and fact_sheet.extra_flags.get("backfire_risk"):
            unk_cnt = fact_sheet.extra_flags.get("unknown_count", 1)
            backfire_dmg = max(5, unk_cnt * 4)
            if fact_sheet.extra_flags.get("logos_backlash"):
                backfire_dmg = max(15, backfire_dmg * 2)
                StatusEffectEngine.apply_status(state.player, "silence", duration=2, potency=1)
                fact_sheet.status_tick_logs.append("⚠️ [언령 반작용] 대상의 영혼 격에 언령이 튕겨 나와 시전자의 성대가 파열되고 침묵(2턴) 상태가 되었습니다!")
            state.player.health = max(1, state.player.health - backfire_dmg)
            if "player" not in state_delta:
                state_delta["player"] = {}
            state_delta["player"]["health"] = state.player.health
            fact_sheet.quest_progress_logs.append(
                f"⚡ [마나 역류 자해!] 고대어/언령 반작용으로 마력이 시전자에게 역류하여 {backfire_dmg} 자해 피해를 입었습니다! (현재 체력: {state.player.health}/{state.player.max_health})"
            )

            # Mana circuit backlash & damage integration
            backlash_logs = ManaBurnEngine.trigger_mana_backlash(state.player, severity=max(1, unk_cnt), state=state)
            p_circuit = ManaBurnEngine.get_circuit_state(state.player)
            state_delta["player"]["mana_burn_state"] = p_circuit.to_dict()
            state_delta["player"]["health"] = state.player.health

            backlash_text = "\n".join(backlash_logs)
            if fact_sheet.mana_burn_summary:
                fact_sheet.mana_burn_summary += "\n" + backlash_text
            else:
                fact_sheet.mana_burn_summary = backlash_text
            fact_sheet.quest_progress_logs.extend(backlash_logs)

        # 7.8 Trap Search & Disarm Handling
        action_lower_act = action.lower()
        if fact_sheet.extra_flags.get("is_trap_search"):
            from src.world.trap_engine import TrapEngine
            detected = TrapEngine.detect_traps_in_location(
                state.player, state.player.location, state, is_active_search=True
            )
            if detected:
                for d in detected:
                    fact_sheet.status_tick_logs.append(d["message_ko"])
            else:
                fact_sheet.status_tick_logs.append("🔍 주변 바닥과 벽면을 세심히 수색했으나 드러난 함정은 발견되지 않았습니다.")

        elif fact_sheet.extra_flags.get("is_trap_disarm"):
            from src.world.trap_engine import TrapEngine
            curr_loc = state.locations.get(state.player.location)
            traps = getattr(curr_loc, "traps", [])
            active_traps = getattr(state, "active_traps", {})
            disarmed_any = False
            for t_id in traps:
                t_inst = active_traps.get(t_id)
                if t_inst and t_inst.status == "revealed":
                    res = TrapEngine.disarm_trap(state.player, t_id, state)
                    fact_sheet.status_tick_logs.append(res["message_ko"])
                    disarmed_any = True
                    break
            if not disarmed_any:
                fact_sheet.status_tick_logs.append("⚠️ 해체할 수 있는 발견된 함정(Revealed)이 시야에 없습니다. 먼저 함정을 수색하여 발견하십시오.")

        # 7.9 Dungeon Navigation (Descend / Ascend)
        if fact_sheet.extra_flags.get("is_dungeon_nav"):
            from src.world.dungeon_engine import DungeonEngine
            if any(k in action_lower_act for k in ["지하로", "아래층", "다음 층", "하강"]):
                ok, nav_msg = DungeonEngine.descend_floor(state)
            else:
                ok, nav_msg = DungeonEngine.ascend_floor(state)
            fact_sheet.status_tick_logs.append(nav_msg)

        # 7.10 Ventilation Shaft Interaction
        if "환기구" in action_lower_act and any(v in action_lower_act for v in ["열", "개방", "가동", "확보", "open"]):
            curr_loc = state.current_location()
            if curr_loc:
                from src.world.cave_in_engine import CaveCollapseEngine
                _, vent_msg = CaveCollapseEngine.open_ventilation(curr_loc)
                fact_sheet.status_tick_logs.append(vent_msg)

        # 8. Party & Companion Autonomous Turns
        is_combat = (dice_res is not None and any(k in getattr(dice_res, "action_type", "") for k in ["combat", "magic", "공격", "전투", "스킬"]))
        if is_combat and target_npc:
            companion_logs = PartyEngine.process_companion_combat_turns(state, target_npc=target_npc)
            fact_sheet.companion_combat_logs = companion_logs

        # 8.5 Hostile NPC Combat Counter-Attack / Skill Turns
        if is_combat:
            curr_loc = state.current_location()
            if curr_loc:
                loc_npcs = state.npcs_in_location(curr_loc.id)
                for h_npc in loc_npcs:
                    if h_npc.alive and h_npc.disposition == "hostile":
                        if target_npc and h_npc.id == target_npc.id and not target_npc.alive:
                            continue
                        npc_outcome = NPCSkillEngine.process_npc_combat_turn(h_npc, state, player_ac=getattr(state.player, "armor_class", 10))
                        if npc_outcome:
                            fact_sheet.npc_skill_logs.append(npc_outcome["summary_ko"])
                            if "player" not in state_delta:
                                state_delta["player"] = {}
                            state_delta["player"]["health"] = state.player.health

        # 8.6 Unified Autonomous Cognitive & Opportunistic NPC Actions
        elif curr_loc:
            from src.world.cognitive_engine import NPCCognitiveDeductionEngine
            loc_npcs = state.npcs_in_location(curr_loc.id)
            for o_npc in loc_npcs:
                if o_npc.alive and o_npc.disposition != "hostile":
                    opp_outcome = NPCCognitiveDeductionEngine.process_npc_cognitive_turn(o_npc, state, action)
                    if opp_outcome:
                        fact_sheet.npc_skill_logs.append(opp_outcome["summary_ko"])
                        if opp_outcome.get("gm_directive"):
                            fact_sheet.npc_skill_logs.append(f"   * [서사 지침]: {opp_outcome['gm_directive']}")
                        if opp_outcome.get("action_type", "").startswith("opportunistic_theft"):
                            if "player" not in state_delta:
                                state_delta["player"] = {}
                            state_delta["player"]["gold"] = state.player.gold
                            state_delta["player"]["inventory"] = list(state.player.inventory)
                            if "npc_state" not in state_delta:
                                state_delta["npc_state"] = {}
                            state_delta["npc_state"][o_npc.id] = {
                                "gold": o_npc.gold,
                                "inventory": list(o_npc.inventory),
                                "disposition": o_npc.disposition
                            }
                        elif opp_outcome.get("disposition_changed"):
                            if "npc_state" not in state_delta:
                                state_delta["npc_state"] = {}
                            state_delta["npc_state"].setdefault(o_npc.id, {})["disposition"] = o_npc.disposition
                        break  # Limit to 1 opportunistic action per turn

        # 8.7 Deterministic Hidden Boss / Elite Monster Encounter Check
        from src.world.hidden_encounter_engine import HiddenEncounterEngine
        hidden_enc = HiddenEncounterEngine.evaluate_encounter(state, action)
        if hidden_enc:
            fact_sheet.quest_progress_logs.append(hidden_enc["encounter_log"])
            fact_sheet.npc_skill_logs.append(f"🚨 [{hidden_enc['tier'].upper()} 강림]: {hidden_enc['appearance_narration']}")
            fact_sheet.npc_skill_logs.append(f"   * [보스 약점 공략 힌트]: {hidden_enc['weakness']}")
            if hidden_enc.get("extractable_skill"):
                fact_sheet.npc_skill_logs.append(f"   * [처치 시 획득 가능 비기]: {hidden_enc['extractable_skill']}")

        # 8.8 Autonomous Next Intent Prediction for Off-Screen NPCs
        from src.world.cognitive_engine import NPCCognitiveDeductionEngine
        p_loc = state.player.location
        for off_npc in state.npcs.values():
            if off_npc.alive and off_npc.location != p_loc:
                pred_action = NPCCognitiveDeductionEngine.predict_autonomous_next_intent(off_npc, state)
                log_entry = f"[Turn {state.turn}] {pred_action.concrete_plan} (위험도: {pred_action.execution_risk})"
                off_npc.off_screen_logs.append(log_entry)
                # Cap logs to prevent unbounded growth (Rule 6)
                if len(off_npc.off_screen_logs) > 30:
                    off_npc.off_screen_logs = off_npc.off_screen_logs[-30:]

        # 9. Ecological Feedback
        loc_name = curr_loc.name if curr_loc else "미지의 지대"
        dice_success = dice_res.is_success if dice_res else True
        eco_feedback = EcologicalFeedbackLoop.calculate_feedback(action, dice_success, loc_name, state)
        fact_sheet.eco_feedback = eco_feedback

        if eco_feedback.get("terraforming"):
            state.world_facts.append(f"[지형 변형] {eco_feedback['terraforming']}")
        if eco_feedback.get("world_news"):
            state.pending_breaking_news.append(eco_feedback["world_news"])
        if eco_feedback.get("reputation_delta"):
            state.player.reputation = max(-100, min(100, state.player.reputation + eco_feedback["reputation_delta"]))

        fact_sheet.pre_computed_state_delta = state_delta
        return fact_sheet

    @classmethod
    def reconcile_narration_with_fact_sheet(
        cls,
        narration: str,
        fact_sheet: DeterministicFactSheet
    ) -> str:
        """
        Validates narrative text against deterministic Pass 1 truth.
        Detects contradictions (jailbreaks/hallucinations) and enforces deterministic facts:
        1. Action Rejection (Anti-Yes-Man): Overrides narration if action is physically/logically invalid.
        2. Dice Failure Contradiction: Appends deterministic failure correction if narration falsely claims success.
        3. Alive NPC Falsely Reported Killed: Appends survival correction if target is still alive.
        4. Killed NPC Falsely Reported Alive: Appends lethal kill confirmation if target is dead.
        """
        if not narration:
            return narration

        # 1. Action Rejection (Anti-Yes-Man Reality Check)
        if not fact_sheet.is_valid:
            reason = fact_sheet.rejection_reason or "물리적 또는 논리적 제약으로 인해 행동이 가로막혔습니다."
            logger.warning(f"[⚠️ 서사-판정 모순 감지] 거부된 행동(is_valid=False)에 대한 서사 교정 적용: {reason}")
            return f"당신의 행동은 현실적인 제약으로 가로막혔습니다.\n사유: {reason}"

        # 2. Dice Failure Contradiction Check
        if fact_sheet.dice_result and fact_sheet.dice_result.get("is_success") is False:
            success_keywords = ["성공", "돌파", "격파", "관통", "제압", "처치", "숨통을 끊", "목을 베", "쓰러뜨", "명중"]
            has_positive_success = any(kw in narration for kw in success_keywords)
            has_failure_context = any(neg in narration for neg in [
                "실패", "빗나", "막혔", "튕겨", "가로막", "피했", "못하", "못했", "않았", "못한", "않은"
            ])

            if has_positive_success and not has_failure_context:
                logger.warning(
                    f"[⚠️ 서사-판정 모순 감지] 판정 실패(FAILURE)이나 LLM 서사에 성공 묘사가 감지되었습니다. "
                    f"판정: {fact_sheet.dice_result.get('summary_ko')}"
                )
                correction_note = "\n\n*(⚠️ 판정 결과: 실패 — 실제 판정에서는 목표를 달성하지 못하고 빗나가거나 가로막혔습니다.)*"
                if correction_note not in narration:
                    narration += correction_note

        # 3. Combat Outcome Contradiction Check
        if fact_sheet.combat_outcome:
            co = fact_sheet.combat_outcome
            t_name = co.get("target_name", "대상")
            is_killed = co.get("killed", False)
            hp_after = co.get("hp_after", 0)
            max_hp = co.get("max_hp", 0)

            if not is_killed:
                lethal_keywords = ["숨통을 끊", "처치", "사망", "목숨을 잃", "시체가 되", "숨을 거두", "절명"]
                claims_kill = any(kw in narration for kw in lethal_keywords)
                has_alive_context = any(neg in narration for neg in [
                    "살아", "버텨", "남은", "부상", "비틀거", "숨이 붙어", "쓰러지지", "죽지", "아직", "실패", "못했"
                ])

                if claims_kill and not has_alive_context:
                    logger.warning(
                        f"[⚠️ 서사-판정 모순 감지] 대상({t_name}) 생존(HP: {hp_after}/{max_hp})이나 서사에 사망 처치 묘사가 포함되었습니다."
                    )
                    survival_note = f"\n\n*(⚠️ 전투 지속: {t_name}은(는) 큰 부상을 입었으나 아직 쓰러지지 않고 생존해 있습니다. 남은 체력: {hp_after}/{max_hp})*"
                    if survival_note not in narration:
                        narration += survival_note
            else:
                survival_keywords = ["도망", "도주", "자리를 피", "상처 하나 없이", "여유롭게 웃"]
                claims_survival = any(kw in narration for kw in survival_keywords)
                has_death_context = any(neg in narration for neg in [
                    "사망", "쓰러", "숨을 거", "죽", "처치", "피를 흘리며 쓰러", "절명", "숨통이 끊"
                ])

                if claims_survival and not has_death_context:
                    logger.warning(
                        f"[⚠️ 서사-판정 모순 감지] 대상({t_name}) 사망 판정이나 서사에 생존/도주 묘사가 포함되었습니다."
                    )
                    death_note = f"\n\n*(⚠️ 처치 확인: {t_name}은(는) 치명상을 입고 완전히 쓰러져 사망했습니다.)*"
                    if death_note not in narration:
                        narration += death_note

        return narration

    @classmethod
    def sanitize_pass2_result(
        cls,
        raw_llm_result: Dict[str, Any],
        fact_sheet: DeterministicFactSheet,
        state: WorldState
    ) -> Dict[str, Any]:
        """
        Pass 2: Reconciles LLM output with deterministic Pass 1 truth.
        Ensures state updates and narration adhere 100% to deterministic mechanics.
        """
        narration = raw_llm_result.get("narration", "").strip()
        narration = cls.reconcile_narration_with_fact_sheet(narration, fact_sheet)
        llm_state_update = raw_llm_result.get("state_update", {})
        final_state_update = dict(fact_sheet.pre_computed_state_delta)

        # Allow safe/benign LLM updates (e.g. npc_memory, clues, environment notes, reveal_npc_name)
        safe_keys = ["npc_memory", "record_clue", "update_environment", "reveal_npc_name", "world_ended"]
        for k in safe_keys:
            if k in llm_state_update:
                final_state_update[k] = llm_state_update[k]

        # Merge grant_skill / grant_title if present
        if "grant_skill" in llm_state_update:
            if "grant_skill" not in final_state_update:
                final_state_update["grant_skill"] = {}
            final_state_update["grant_skill"].update(llm_state_update["grant_skill"])

        if "grant_title" in llm_state_update:
            final_state_update["grant_title"] = llm_state_update["grant_title"]

        # Ensure unique skill drop notice is appended to narration if generated in Pass 1
        if fact_sheet.dropped_skill_name and fact_sheet.dropped_skill_name not in narration:
            narration += f"\n\n✨ **[고유 스킬 획득]** '{fact_sheet.dropped_skill_name}' 스킬을 빼앗았습니다!"

        # Sanitize NPC state: Pass 1 deterministic HP and alive status ALWAYS override LLM
        if "npc_state" in final_state_update and "npc_state" in llm_state_update:
            for npc_id, npc_data in llm_state_update["npc_state"].items():
                if npc_id not in final_state_update["npc_state"]:
                    # Benign disposition/memory update
                    final_state_update["npc_state"][npc_id] = npc_data

        # Process skills / titles acquisition via SkillSystem
        if "grant_skill" in final_state_update:
            for target_id, skill_id in final_state_update["grant_skill"].items():
                if target_id == "player":
                    SkillSystem.acquire_skill(state, skill_id)

        if "grant_title" in final_state_update:
            for target_id, title_id in final_state_update["grant_title"].items():
                if target_id == "player":
                    SkillSystem.grant_title(state, title_id)

        return {
            "narration": narration,
            "state_update": final_state_update,
            "scene_changed": raw_llm_result.get("scene_changed", False),
            "image_prompt": raw_llm_result.get("image_prompt"),
            "npc_action": raw_llm_result.get("npc_action"),
        }
