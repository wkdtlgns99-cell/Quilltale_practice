"""
Bounty & Disguise System for Quilltale TRPG.
Tracks faction-specific bounties, generates wanted posters, handles disguises/aliases,
and deterministically spawns bounty hunters and guard checkpoints.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from src.world.state import WorldState, Player, NPC

logger = logging.getLogger(__name__)


class BountyEngine:
    """
    Manages wanted status, hunter ambushes, and undercover disguises.
    """

    @classmethod
    def add_bounty(cls, state: WorldState, faction_id: str, amount: int, crime_desc: str = "") -> str:
        """
        Adds bounty to the player for a specific faction and issues a wanted notice.
        """
        player = state.player
        curr_bounty = player.bounties.get(faction_id, 0)
        player.bounties[faction_id] = curr_bounty + amount

        # Record wanted poster
        fac_name = state.factions[faction_id].name if faction_id in state.factions else faction_id
        notice = {
            "faction_id": faction_id,
            "faction_name": fac_name,
            "bounty": player.bounties[faction_id],
            "target_name": player.name,
            "crime": crime_desc or "치안 방해 및 불법 무력 행사",
            "issued_turn": state.turn
        }
        state.bounties_board.append(notice)
        msg = f"📜 [현상수배 발령] [{fac_name}]에서 당신에게 현상금 {amount}G를 책정했습니다! (누적: {player.bounties[faction_id]}G)"
        state.pending_breaking_news.append(f"주요 수배령: 현상금 {player.bounties[faction_id]}G의 수배자 [{player.name}] 추적 개시")
        return msg

    @classmethod
    def check_guard_inspection(cls, state: WorldState, guard_npc: NPC) -> Tuple[bool, str]:
        """
        Guards check player's bounty. If player is disguised, checks disguise quality.
        Returns (is_busted, message_ko).
        """
        player = state.player
        faction_id = guard_npc.faction_id or "default"
        bounty = player.bounties.get(faction_id, 0)

        if bounty <= 0:
            return False, "경비병이 무심하게 당신을 지나쳐 보냅니다."

        if player.disguise:
            # Player is wearing a disguise (e.g. mask, cultist robe)
            alias_str = f"'{player.active_alias}'(으)로 위장하여" if player.active_alias else "변장한 채로"
            return False, f"🎭 [위장 성공] {alias_str} 경비병의 의심을 피해 검문소를 무사히 통과했습니다."

        # Busted!
        return True, f"🚨 [수배자 발각!] 경비병 [{guard_npc.name}]이 당신의 몽타주를 알아보고 무기를 빼 들었습니다! (현상금 {bounty}G)"

    @classmethod
    def check_bounty_hunter_ambush(cls, state: WorldState, action: str) -> Optional[Dict[str, Any]]:
        """
        If bounty is high (> 500G) and traveling in dangerous areas, triggers a bounty hunter ambush.
        """
        total_bounty = sum(state.player.bounties.values())
        if total_bounty < 500:
            return None

        if state.player.disguise:
            return None

        # Check travel keywords
        if any(k in action for k in ["이동", "길을 떠난다", "외곽", "골목", "숲으로"]):
            hunter_name = "그림자 사냥꾼 발터" if total_bounty >= 1000 else "현상금 용병단"
            return {
                "hunter_name": hunter_name,
                "bounty_target": total_bounty,
                "summary_ko": f"⚔️ [현상금 사냥꾼 기습] 당신의 목에 걸린 {total_bounty}G를 노린 [{hunter_name}]이 길목을 가로막았습니다!"
            }

        return None

    @classmethod
    def format_bounty_context_for_prompt(cls, state: WorldState) -> str:
        """
        Formats player's wanted status and active disguise for LLM narration.
        """
        player = state.player
        active_bounties = [f"{fac}: {amt}G" for fac, amt in player.bounties.items() if amt > 0]
        if not active_bounties and not player.disguise:
            return ""

        lines = ["[📜 현상수배 및 위장 상태]"]
        if active_bounties:
            lines.append(f"- 수배 현상금: {', '.join(active_bounties)}")
        if player.disguise:
            lines.append(f"- 착용 중인 변장: {player.disguise} (가명: {player.active_alias or '없음'})")
        return "\n".join(lines)
