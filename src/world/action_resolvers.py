"""
Domain-specific Action Resolvers for Quilltale TRPG.
Decomposed from TwoPassEngine to preserve Single Responsibility Principle.

Provides mixins for:
- MovementResolverMixin (movement, road dynamics, navigation)
- StealthResolverMixin (eavesdropping, infiltration)
- SurvivalResolverMixin (anatomy harvest, camping/rest, alcohol drinking, botany)
- TacticalCombatResolverMixin (merchant barter, combat timing/distance, siege warfare)
- ActionResolversMixin (combined mixin)
"""
from typing import Dict, Any, List, Optional
import re
import logging

from src.world.state import WorldState, Item, NPC
from src.world.skills import SkillSystem
from src.world.geography import GeographyEngine
from src.world.weather_engine import WeatherEngine
from src.world.stealth_engine import StealthInfiltrationEngine
from src.world.harvest_engine import AnatomyHarvestEngine, HarvestOutcome
from src.world.campsite_engine import CampsiteRestEngine
from src.world.alcohol_engine import AlcoholIntoxicationEngine, ALCOHOL_DRINK_REGISTRY
from src.world.botany_engine import HerbalismBotanyEngine, PLANT_REGISTRY
from src.world.merchant_barter_engine import MerchantBarterEngine, ContrabandTier
from src.world.combat_time_track_engine import CombatDistanceManager, ActionTimeTrackEngine, CombatAction
from src.world.siege_engine import SiegeWarfareEngine
from src.world.bounty_engine import BountyEngine
from src.world.dice import DiceEngine
from src.world.infrastructure import Settlement

logger = logging.getLogger(__name__)


class MovementResolverMixin:
    """Action resolver mixin for player movement and navigation."""
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
            "north": ["북쪽", "북으로", "북편", "north", "앞으로", "정면"],
            "south": ["남쪽", "남으로", "남편", "south", "뒤로", "남문"],
            "east": ["동쪽", "동으로", "동편", "east", "오른쪽"],
            "west": ["서쪽", "서로", "서편", "west", "왼쪽"],
            "upstairs": ["2층", "계단", "위층", "upstairs", "올라"],
            "downstairs": ["지하", "아래층", "지하실", "downstairs", "내려"]
        }

        # Strip common action suffix verbs like '이동' for direction keyword matching
        action_for_dir = re.sub(r'[이|기|작|변|율]동', ' ', action_lower)

        if hasattr(curr_loc, "exits") and curr_loc.exits:
            for exit_dir, target_loc_id in curr_loc.exits.items():
                keywords = direction_keywords.get(exit_dir.lower(), [exit_dir.lower()])
                target_loc = state.locations.get(target_loc_id)
                loc_name_match = bool(target_loc and target_loc.name.lower() in action_lower)
                dir_match = any(k in action_for_dir for k in keywords)

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


class StealthResolverMixin:
    """Action resolver mixin for eavesdropping and stealth infiltration."""
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


class SurvivalResolverMixin:
    """Action resolver mixin for wilderness survival: harvesting, camping, drinking, botany."""
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


class TacticalCombatResolverMixin:
    """Action resolver mixin for tactical interactions: barter, combat timing/distance, siege warfare."""
    @classmethod
    def resolve_action_barter(cls, action: str, state: WorldState) -> Optional[Dict[str, Any]]:
        """
        Parses barter, arbitrage, smuggling checkpoint, appraisal, coin-clipping and debt actions.
        Invokes MerchantBarterEngine deterministic mechanics.
        """
        act_lower = action.lower()
        curr_loc = state.current_location()
        terrain = getattr(curr_loc, "terrain", getattr(curr_loc, "biome", "plains_farm")) if curr_loc else "plains_farm"

        # 1. Coin Clipping & Gold Dust Skimming
        if any(k in act_lower for k in ["금화 깎기", "동전 깎기", "금가루", "주화 훼손", "coin clip"]):
            sleight = (state.player.stats.get("dexterity", 10) - 10) // 2
            res = MerchantBarterEngine.attempt_coin_clipping(
                payment_amount=100,
                merchant_perception=12,
                player_sleight_mod=sleight
            )
            gold_gain = res.get("gold_dust_value", 0)
            if gold_gain > 0:
                state.player.gold += gold_gain
            bounty = res.get("bounty_added", 0)
            if bounty > 0:
                BountyEngine.add_bounty(state, "local_guards", bounty, "금화 훼손 및 사기죄")
            return {
                "type": "coin_clip",
                "success": res.get("success", False),
                "gold_change": gold_gain,
                "summary": res.get("summary_ko", ""),
                "result": res
            }

        # 2. Relic & Artifact Appraisal
        if any(k in act_lower for k in ["감정", "appraise", "유물 감정", "식별"]):
            fee = 30
            if state.player.gold < fee:
                return {
                    "type": "appraise",
                    "success": False,
                    "summary": f"감정 실패: 수수료 {fee}G가 부족합니다 (현재 골드: {state.player.gold}G).",
                    "gold_change": 0
                }
            state.player.gold -= fee
            # Check for unappraised item in inventory
            unappraised_item = next(
                (item for item_id, item in state.items.items()
                 if item_id in state.player.inventory and (
                     not getattr(item, "is_identified", True) or
                     "unidentified" in getattr(item, "traits", []) or
                     "미감정" in item.name
                 )),
                None
            )
            raw_name = unappraised_item.name if unappraised_item else "흙 묻은 고대 쇠붙이"
            res = MerchantBarterEngine.appraise_unidentified_item(
                raw_name=raw_name,
                true_name="고대 성자의 축복받은 은장도",
                true_price=350,
                fee_paid=fee,
                required_fee=fee,
                is_cursed=False
            )
            if unappraised_item and res.get("success"):
                unappraised_item.name = res["revealed_name"]
                unappraised_item.value = res["price"]
                unappraised_item.is_identified = True
                if hasattr(unappraised_item, "traits") and "unidentified" in unappraised_item.traits:
                    unappraised_item.traits.remove("unidentified")
            return {
                "type": "appraise",
                "success": res.get("success", False),
                "gold_change": -fee,
                "summary": res.get("summary_ko", ""),
                "result": res
            }

        # 3. Smuggling Checkpoint Inspection
        if any(k in act_lower for k in ["밀수", "검문", "밀반입", "밀수품", "smuggle"]):
            contraband_items = []
            for iid in state.player.inventory:
                it = state.items.get(iid)
                if it:
                    tier = getattr(it, "contraband_tier", 0)
                    if any(t in getattr(it, "traits", []) for t in ["contraband", "illicit", "darkweed"]):
                        tier = ContrabandTier.ILLICIT
                    elif any(t in getattr(it, "traits", []) for t in ["restricted", "poached"]):
                        tier = ContrabandTier.RESTRICTED
                    if tier > 0:
                        contraband_items.append({
                            "id": it.id,
                            "name_ko": it.name,
                            "contraband_tier": tier
                        })
            stealth_mod = (state.player.stats.get("dexterity", 10) - 10) // 2
            res = MerchantBarterEngine.check_smuggling_checkpoint(
                contraband_items=contraband_items,
                guard_perception=12,
                player_stealth_mod=stealth_mod
            )
            if not res.get("passed", True):
                bounty = res.get("bounty_added", 0)
                if bounty > 0:
                    BountyEngine.add_bounty(state, "local_guards", bounty, "금지품 밀수 혐의")
                # Confiscate items
                confiscated_names = res.get("confiscated_items", [])
                for iid in list(state.player.inventory):
                    it = state.items.get(iid)
                    if it and (it.name in confiscated_names or it.id in confiscated_names):
                        state.player.inventory.remove(iid)
            return {
                "type": "smuggle",
                "success": res.get("passed", True),
                "summary": res.get("summary_ko", ""),
                "result": res
            }

        # 4. Regional Price / Market Arbitrage
        if any(k in act_lower for k in ["시세", "물가", "마진", "차익", "arbitrage"]):
            price_salt = MerchantBarterEngine.get_regional_price("salt", 20, terrain)
            price_grain = MerchantBarterEngine.get_regional_price("grain", 15, terrain)
            price_ore = MerchantBarterEngine.get_regional_price("ore", 30, terrain)
            summary = (
                f"[{terrain}] 지역 시세표: 소금 {price_salt}G (기준 20G), "
                f"곡물 {price_grain}G (기준 15G), 광석 {price_ore}G (기준 30G)"
            )
            return {
                "type": "price_check",
                "success": True,
                "summary": summary,
                "prices": {"salt": price_salt, "grain": price_grain, "ore": price_ore}
            }

        # 5. Merchant Credit Ledger / Black Market / Debt Check
        if any(k in act_lower for k in ["외상", "차용", "사채", "대출", "ledger", "black market", "암시장"]):
            bm_price = MerchantBarterEngine.sell_to_black_market(base_price=100, contraband_tier=ContrabandTier.RESTRICTED)
            entry = MerchantBarterEngine.record_merchant_debt(
                shop_id=f"shop_{terrain}",
                principal=100,
                current_turn=state.turn,
                duration_turns=30,
                interest_rate=0.20
            )
            debt_res = MerchantBarterEngine.check_debt_default(entry, state.turn)
            summary = (
                f"금융 거래: 암시장 매입가 {bm_price}G. {debt_res['summary_ko']}"
            )
            return {
                "type": "credit_debt",
                "success": True,
                "summary": summary,
                "entry": entry,
                "black_market_price": bm_price
            }

        # 6. Direct Barter / Item Swap
        if any(k in act_lower for k in ["물물교환", "맞바꾸", "교환", "물물 교환", "barter"]):
            offered_vals = [
                getattr(state.items[iid], "value", 20)
                for iid in state.player.inventory[:2]
                if iid in state.items
            ]
            if not offered_vals:
                offered_vals = [30]
            wanted_vals = [50]
            cha_mod = (state.player.stats.get("charisma", 10) - 10) // 2
            roll = DiceEngine.roll_d20() + cha_mod
            res = MerchantBarterEngine.calculate_barter_exchange(
                offered_item_values=offered_vals,
                wanted_item_values=wanted_vals,
                persuasion_roll=roll,
                terrain=terrain
            )
            gold_gain = res.get("change_gold_due", 0)
            if res.get("is_possible"):
                state.player.gold += gold_gain
            return {
                "type": "barter",
                "success": res.get("is_possible", False),
                "gold_change": gold_gain,
                "summary": res.get("summary_ko", ""),
                "result": res
            }

        return None

    @classmethod
    def resolve_action_combat_distance_and_timing(cls, action: str, state: WorldState) -> Optional[Dict[str, Any]]:
        """
        Parses meter-based combat distance movement (charge/retreat) and Perception-gated
        Option A reaction interrupt events.
        Invokes CombatDistanceManager and ActionTimeTrackEngine.
        """
        act_lower = action.lower()
        player_id = getattr(state.player, "id", getattr(state.player, "name", "player"))

        # Determine target enemy NPC
        target_npc = None
        curr_loc = state.current_location()
        npc_list = getattr(curr_loc, "npcs", getattr(curr_loc, "npc_ids", [])) if curr_loc else []
        for nid in npc_list:
            npc = state.npcs.get(nid)
            if npc and (getattr(npc, "disposition", "") == "hostile" or getattr(npc, "is_hostile", False)):
                target_npc = npc
                break
        if not target_npc and npc_list:
            target_npc = state.npcs.get(npc_list[0])

        target_id = target_npc.id if target_npc else "target_enemy"
        target_name = target_npc.name if target_npc else "적대적 적수"

        is_move_towards = any(k in act_lower for k in [
            "돌진", "접근", "달려들어", "다가가", "간격을 좁", "파고들", "charge", "approach", "육박"
        ])
        is_move_away = any(k in act_lower for k in [
            "거리 벌리기", "뒤로 물러나", "후퇴", "백스텝", "간격 벌", "거리 유지", "물러서", "backstep", "retreat"
        ])
        is_combat_intent = any(k in act_lower for k in [
            "전투", "공격", "베기", "찌르기", "기습", "화살", "사격", "방어", "패링", "회피", "strike", "attack"
        ])

        if not (is_move_towards or is_move_away or is_combat_intent):
            return None

        # 1. Update Distance
        if is_move_towards:
            new_dist = CombatDistanceManager.move_towards(
                state, mover_id=player_id, target_id=target_id, speed_mps=5.0, seconds=1.0
            )
            move_type = "approach"
        elif is_move_away:
            new_dist = CombatDistanceManager.move_away(
                state, mover_id=player_id, target_id=target_id, speed_mps=4.0, seconds=1.0
            )
            move_type = "retreat"
        else:
            cur_dist = CombatDistanceManager.get_distance(state, player_id, target_id, default=5.0)
            new_dist = cur_dist
            CombatDistanceManager.set_distance(state, player_id, target_id, new_dist)
            move_type = "stand"

        zone_key = CombatDistanceManager.get_distance_zone(new_dist)
        zone_ko = CombatDistanceManager.get_distance_zone_ko(new_dist)

        # 2. Check Option A Perception Interrupt on incoming threat
        combat_act = CombatAction(
            entity_id=target_id,
            action_name="급습 참격",
            start_second=0.0,
            duration_seconds=1.2,
            target_id=player_id,
            is_interruptible=True
        )
        _ = combat_act.end_second

        is_surprise = "기습" in act_lower or "암살" in act_lower
        interrupt = ActionTimeTrackEngine.check_perception_interrupt(
            state=state,
            victim=state.player,
            threat_source=target_npc or target_id,
            action=combat_act,
            distance_m=new_dist,
            is_surprise=is_surprise
        )

        summary = f"대치 거리 {new_dist:.1f}m [{zone_ko}] - {target_name}과의 상대 간격 유지."
        if interrupt:
            summary += f" ⚡ {interrupt.narrative_ko}"

        return {
            "type": move_type,
            "distance_m": new_dist,
            "zone_key": zone_key,
            "zone_ko": zone_ko,
            "interrupt": interrupt,
            "summary": summary
        }

    @classmethod
    def resolve_action_siege(cls, action: str, state: WorldState) -> Optional[Dict[str, Any]]:
        """
        Parses fortress assault, artillery bombardment, moat clearing, ram breach,
        and commando night infiltration.
        Invokes SiegeWarfareEngine deterministic simulation.
        """
        act_lower = action.lower()
        is_siege_keyword = any(k in act_lower for k in [
            "공성", "성벽 공격", "성문 돌파", "투석기", "트레뷰셋", "공성추", "포격", "발리스타", "공성탑", "siege"
        ])
        is_commando_keyword = any(k in act_lower for k in [
            "별동대", "특공", "침투", "성문 열", "투석기 방화", "군량고 파괴", "지휘관 저격", "commando", "infiltrate"
        ])

        if not (is_siege_keyword or is_commando_keyword):
            return None

        # Resolve Settlement
        settlement = None
        curr_loc = state.current_location()
        if hasattr(state, "infrastructure") and state.infrastructure and state.infrastructure.settlements:
            if curr_loc and hasattr(curr_loc, "settlement_id") and curr_loc.settlement_id:
                settlement = state.infrastructure.settlements.get(curr_loc.settlement_id)
            if not settlement:
                settlement = next(iter(state.infrastructure.settlements.values()), None)

        if not settlement:
            settlement = Settlement(
                id="fortress_frontier",
                name="변경의 국경 요새",
                nation_id="nat_frontier",
                region_id="reg_frontier",
                wall_defense_tier=2
            )

        siege_id = f"siege_{settlement.id}"
        siege_state = state.active_sieges.get(siege_id)
        if not siege_state:
            _ = SiegeWarfareEngine.initialize_fortress_defense(settlement)
            _ = SiegeWarfareEngine.create_siege_engine("trebuchet", "atk_treb_1")
            siege_state = SiegeWarfareEngine.initialize_siege(siege_id=siege_id, settlement=settlement)
            state.active_sieges[siege_id] = siege_state

        # Commando Infiltration Action
        if is_commando_keyword:
            if "투석기" in act_lower or "방화" in act_lower:
                c_action = "burn_catapult"
            elif "군량" in act_lower:
                c_action = "sabotage_supplies"
            elif "저격" in act_lower or "지휘관" in act_lower:
                c_action = "snipe_commander"
            else:
                c_action = "open_gate"

            stealth_mod = (state.player.stats.get("dexterity", 10) - 10) // 2
            commando_res = SiegeWarfareEngine.execute_commando_action(
                state=siege_state,
                action_type=c_action,
                infiltrator_stealth_mod=stealth_mod
            )
            summary = commando_res.get("log", "특공 작전 실행 완료.")
            return {
                "action_type": "commando",
                "siege_id": siege_id,
                "siege_state": siege_state,
                "commando_result": commando_res,
                "summary": summary
            }

        # Regular Siege Turn Advance
        logs = SiegeWarfareEngine.advance_siege_turn(siege_state)
        ext_prompt = SiegeWarfareEngine.generate_external_llm_prompt(siege_state, logs)
        summary = "\n".join(logs[:4]) if logs else "공성전 작전 전개 완료."

        return {
            "action_type": "turn",
            "siege_id": siege_id,
            "siege_state": siege_state,
            "logs": logs,
            "summary": summary,
            "ext_prompt": ext_prompt
        }


class ActionResolversMixin(
    MovementResolverMixin,
    StealthResolverMixin,
    SurvivalResolverMixin,
    TacticalCombatResolverMixin,
):
    """Unified mixin composing all 10 action resolvers."""
    pass


__all__ = [
    "MovementResolverMixin",
    "StealthResolverMixin",
    "SurvivalResolverMixin",
    "TacticalCombatResolverMixin",
    "ActionResolversMixin",
]
