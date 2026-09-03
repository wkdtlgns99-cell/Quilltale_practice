"""
Deterministic Rumor & Reputation Diffusion Engine for Quilltale TRPG.
Propagates rumors and reputation across the geographic road network based on:
1. In-game elapsed time (minutes/hours) rather than arbitrary turn counts.
2. Event significance (Level 1~5) defining maximum diffusion radius.
3. Carrier speed (refugees, merchants, couriers, magical beacons).
4. Distance/Hop-based whisper distortion.
5. Global + Regional reputation synthesis (Global 100 grants >= 75 recognition in remote villages).
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import logging
from src.world.geography import GeographyEngine, RoadType

logger = logging.getLogger(__name__)

# Diffusion max ranges in km based on 5-scale significance
SIGNIFICANCE_MAX_RANGES: Dict[int, float] = {
    1: 3.0,      # Lv.1: 골목/마을 내부 (3km 이내)
    2: 15.0,     # Lv.2: 인근 농가/초소 (15km 이내)
    3: 60.0,     # Lv.3: 인접 거점 도시 (60km 이내)
    4: 200.0,    # Lv.4: 국가 영지 전역 (200km 이내)
    5: 9999.0    # Lv.5: 대륙 전역 무제한
}

CARRIER_MODES: Dict[str, str] = {
    "refugee": "foot",          # 피난민 (도보 4 km/h)
    "merchant": "carriage",     # 상단 마차 (10 km/h)
    "courier": "courier",       # 급보 전령마 (25 km/h)
    "beacon": "magical_beacon"  # 마법 통신/봉화 (200 km/h)
}


@dataclass
class RumorWave:
    rumor_id: str
    origin_location: str
    event_text: str
    significance: int = 3
    reputation_delta: int = 10
    carrier: str = "merchant"
    max_range_km: float = 60.0
    start_minute: int = 480
    scheduled_arrivals: Dict[str, int] = field(default_factory=dict)  # loc_id -> arrival_total_minute
    destination_hops: Dict[str, int] = field(default_factory=dict)     # loc_id -> hop count
    destination_distances: Dict[str, float] = field(default_factory=dict) # loc_id -> distance km
    reached_locations: List[str] = field(default_factory=list)

    def get_distorted_text_for_hops(self, hops: int, distance_km: float) -> str:
        """
        Applies progressive whisper distortion based on geographic hops and distance.
        """
        base = self.event_text
        if hops <= 0 or distance_km < 1.0:
            return f"[목격 팩트] {base}"
        elif hops == 1 or distance_km <= 15.0:
            if any(k in base for k in ["처치", "살해", "승리", "제압"]):
                return f"[인근 소문] {base} (홀로 다수의 적을 손쉽게 압도했다고 전해짐)"
            return f"[인근 소문] {base}"
        elif hops == 2 or distance_km <= 60.0:
            if any(k in base for k in ["처치", "살해", "승리"]):
                return f"[원정 영웅담/괴담] 일기당천의 괴물 같은 전사가 나타나 {base.replace('처치', '단칼에 참수')}"
            return f"[확산된 풍문] {base}에 대한 기이하고 놀라운 소문"
        else:
            # 3+ hops or > 60km: Myth / Legend
            return f"[대륙 전설] 머나먼 변경에서 {base}에 얽힌 신화적 무용담이 시인들의 노래로 퍼져나감"


class RumorDiffusionEngine:
    @classmethod
    def get_effective_reputation(cls, state: Any, location_id: str) -> int:
        """
        Calculates NPC perceived reputation in a specific location:
        Perceived Reputation = local_reputation + int(global_reputation * 0.75)
        At global reputation 100 (Legendary), even remote villages have >= 75 recognition.
        """
        player = state.player
        local_rep = player.regional_reputation.get(location_id, 0) if hasattr(player, "regional_reputation") else 0
        global_rep = getattr(player, "reputation", 0)
        return local_rep + int(global_rep * 0.75)

    @classmethod
    def dispatch_event_rumor(
        cls,
        state: Any,
        origin_loc: str,
        event_text: str,
        significance: int = 3,
        reputation_delta: int = 10,
        carrier: str = "merchant"
    ) -> RumorWave:
        """
        Creates and schedules a new rumor wave originating from origin_loc.
        Computes arrival times for all reachable locations within max_range_km using the road graph.
        """
        sig = max(1, min(5, significance))
        max_range = SIGNIFICANCE_MAX_RANGES.get(sig, 60.0)
        travel_mode = CARRIER_MODES.get(carrier, "carriage")
        start_min = getattr(state, "total_minutes", 480)

        import uuid
        rumor_id = f"rumor_{uuid.uuid4().hex[:8]}"

        wave = RumorWave(
            rumor_id=rumor_id,
            origin_location=origin_loc,
            event_text=event_text,
            significance=sig,
            reputation_delta=reputation_delta,
            carrier=carrier,
            max_range_km=max_range,
            start_minute=start_min,
            reached_locations=[origin_loc]
        )

        # 1. Apply immediately to origin location
        if hasattr(state.player, "regional_reputation"):
            curr_reg = state.player.regional_reputation.get(origin_loc, 0)
            state.player.regional_reputation[origin_loc] = curr_reg + reputation_delta

        # Global reputation also receives partial increase based on significance
        global_bonus = int(reputation_delta * (sig / 5.0))
        state.player.reputation = max(-100, min(100, state.player.reputation + global_bonus))

        # Origin location NPCs immediately know the direct fact
        if origin_loc in state.locations:
            for nid in state.locations[origin_loc].npcs:
                if nid in state.npcs:
                    state.npcs[nid].beliefs.append(f"[직접 목격] {event_text}")

        # 2. Compute arrival schedules for all other reachable locations
        reachables = GeographyEngine.get_all_reachable_locations_with_distances(
            state, origin_loc, travel_mode=travel_mode
        )

        for dest_id, (hours, km, hops) in reachables.items():
            if dest_id == origin_loc:
                continue
            if km <= max_range and hours < float('inf'):
                arrival_min = start_min + int(hours * 60)
                wave.scheduled_arrivals[dest_id] = arrival_min
                wave.destination_hops[dest_id] = hops
                wave.destination_distances[dest_id] = km

        if not hasattr(state, "active_rumors"):
            state.active_rumors = []
        state.active_rumors.append(wave)

        return wave

    @classmethod
    def advance_time_tick(cls, state: Any, elapsed_minutes: int) -> List[str]:
        """
        Advances in-game time for all active rumor waves.
        Delivers rumors to locations whose scheduled arrival time has been reached.
        """
        logs = []
        if not hasattr(state, "active_rumors") or not state.active_rumors:
            return logs

        current_min = getattr(state, "total_minutes", 480)
        remaining_waves = []

        for wave in state.active_rumors:
            all_delivered = True
            for dest_id, arr_min in list(wave.scheduled_arrivals.items()):
                if dest_id in wave.reached_locations:
                    continue

                if current_min >= arr_min:
                    # Rumor arrived at dest_id!
                    wave.reached_locations.append(dest_id)
                    hops = wave.destination_hops.get(dest_id, 1)
                    dist_km = wave.destination_distances.get(dest_id, 5.0)
                    distorted_text = wave.get_distorted_text_for_hops(hops, dist_km)

                    # Update destination NPCs' beliefs
                    if dest_id in state.locations:
                        dest_loc = state.locations[dest_id]
                        for nid in dest_loc.npcs:
                            if nid in state.npcs:
                                state.npcs[nid].beliefs.append(distorted_text)

                    # Update regional reputation with distance decay
                    decay = max(0.2, 1.0 - (hops * 0.2))
                    reg_rep_delta = int(wave.reputation_delta * decay)
                    if hasattr(state.player, "regional_reputation"):
                        c_rep = state.player.regional_reputation.get(dest_id, 0)
                        state.player.regional_reputation[dest_id] = c_rep + reg_rep_delta

                    loc_name = state.locations[dest_id].name if dest_id in state.locations else dest_id
                    arrival_log = f"📢 [{loc_name}]에 소문 도달: {distorted_text} (지역 명성 +{reg_rep_delta})"
                    logs.append(arrival_log)
                    state.world_facts.append(arrival_log)
                else:
                    all_delivered = False

            # Keep wave in circulation if there are still pending arrivals
            if not all_delivered and len(wave.reached_locations) < len(wave.scheduled_arrivals) + 1:
                remaining_waves.append(wave)

        state.active_rumors = remaining_waves
        return logs
