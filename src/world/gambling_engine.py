"""
Gambling Den & Tavern Dice Mini-Game Engine for Quilltale TRPG.
Provides deterministic dice mini-games:
1. Chinchiro (3d6 Showdown: Pinzoro 5x, Shigoro 2x, Arashi 3x, Pair Points, Hifumi -2x, Menashi 0).
2. High-Low / Lucky 7 Duel (2d6 prediction).
3. Sleight of Hand & Cheating mechanics (AGI vs Dealer PER contest).
4. Tavern Brawl Aggro & Blacklist mechanics on cheating exposure.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
import logging
import random

logger = logging.getLogger(__name__)


# =====================================================================
# 1. Gambling Data Models (Rule 5: traits list included)
# =====================================================================
@dataclass
class GamblingOutcome:
    """Deterministic result of a single gambling round."""
    game_type: str                      # "chinchiro", "high_low"
    bet_gold: int
    payout_gold: int
    net_gold: int                       # payout_gold - bet_gold
    player_dice: List[int]
    dealer_dice: List[int]
    player_hand: str
    dealer_hand: str
    result: str                         # "win", "loss", "draw", "caught_cheating"
    is_cheating_attempted: bool = False
    is_caught: bool = False
    tavern_brawl_triggered: bool = False
    narrative_log: str = ""
    traits: List[str] = field(default_factory=list)  # System Rule 5

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "GamblingOutcome":
        clean = dict(data)
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


@dataclass
class PlayerGamblingRecord:
    """Persistent player gambling statistics and blacklist registry."""
    total_games: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    total_winnings: int = 0
    total_losses: int = 0
    net_profit: int = 0
    cheating_attempts: int = 0
    cheating_caught: int = 0
    brawls_started: int = 0
    blacklisted_locations: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)  # System Rule 5

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PlayerGamblingRecord":
        clean = dict(data)
        return cls(**{k: v for k, v in clean.items() if k in cls.__dataclass_fields__})


# =====================================================================
# 2. Gambling Den & Tavern Dice Engine
# =====================================================================
class GamblingDenEngine:
    """
    100% deterministic tavern dice gambling, cheating, and tavern brawl engine.
    """

    @classmethod
    def get_gambling_record(cls, state: Any) -> PlayerGamblingRecord:
        """Retrieves or instantiates PlayerGamblingRecord on WorldState."""
        if not hasattr(state, "gambling_record") or state.gambling_record is None:
            state.gambling_record = PlayerGamblingRecord(traits=["초심자_도박꾼"])
        elif isinstance(state.gambling_record, dict):
            state.gambling_record = PlayerGamblingRecord.from_dict(state.gambling_record)
        return state.gambling_record

    # -----------------------------------------------------------------
    # Chinchiro Hand Evaluator
    # -----------------------------------------------------------------
    @classmethod
    def evaluate_chinchiro_hand(cls, dice: List[int]) -> Tuple[int, str, float]:
        """
        Evaluates 3d6 roll in Chinchiro rules.
        Returns: (rank_score, hand_name_ko, payout_multiplier)
        """
        sorted_dice = sorted(dice)

        # 1. 핀조로 (Pinzoro: 1-1-1) -> 5배 대박
        if sorted_dice == [1, 1, 1]:
            return 100, "핀조로 (1-1-1)", 5.0

        # 2. 시고로 (Shigoro: 4-5-6) -> 2배 승리
        if sorted_dice == [4, 5, 6]:
            return 90, "시고로 (4-5-6)", 2.0

        # 3. 아라시 (Arashi: Triple 2~6) -> 3배 승리
        if sorted_dice[0] == sorted_dice[1] == sorted_dice[2]:
            val = sorted_dice[0]
            return 80 + val, f"아라시 ({val} 트리플)", 3.0

        # 4. 페어 (One Pair: 두 눈이 같고 하나가 다름) -> 남은 한 눈이 1~6점 (1배 승부)
        if sorted_dice[0] == sorted_dice[1]:
            score = sorted_dice[2]
            return 60 + score, f"페어 ({score}의 눈)", 1.0
        elif sorted_dice[1] == sorted_dice[2]:
            score = sorted_dice[0]
            return 60 + score, f"페어 ({score}의 눈)", 1.0

        # 5. 히후미 (Hifumi: 1-2-3) -> 패배 및 2배 손실 (피박)
        if sorted_dice == [1, 2, 3]:
            return -50, "히후미 (1-2-3)", -2.0

        # 6. 메나시 (Menashi: No hand / 무점수) -> 0점
        return 0, "메나시 (무점수)", 0.0

    # -----------------------------------------------------------------
    # High-Low Hand Evaluator
    # -----------------------------------------------------------------
    @classmethod
    def evaluate_high_low_hand(cls, dice: List[int]) -> Tuple[int, str]:
        """Evaluates 2d6 roll for High-Low."""
        total = sum(dice)
        if total > 7:
            return total, f"하이 (High, {total})"
        elif total < 7:
            return total, f"로우 (Low, {total})"
        else:
            return total, f"럭키 세븐 (Lucky 7, {total})"

    # -----------------------------------------------------------------
    # Cheating & Sleight of Hand Mechanics
    # -----------------------------------------------------------------
    @classmethod
    def attempt_cheat(
        cls,
        state: Any,
        technique: str = "sleight_of_hand",
    ) -> Tuple[bool, bool, str]:
        """
        Attempts a sleight of hand cheating trick.
        Contest: Player AGI + Luck modifier vs Dealer DC (Base 13 + perception bonus).
        Returns: (success, is_caught, message)
        """
        player = state.player
        agi_mod = getattr(player, "agi_mod", (getattr(player, "agility", 10) - 10) // 2)
        luck_bonus = max(0, (getattr(player, "luck", 10) - 10) // 4)

        # Traits bonus
        trait_bonus = 0
        p_traits = getattr(player, "traits", [])
        for t in ["도적", "소매치기", "타짜", "날렵한_손", "사기꾼", "그림자"]:
            if t in p_traits:
                trait_bonus += 3
                break

        d20_roll = random.randint(1, 20)
        total_roll = d20_roll + agi_mod + luck_bonus + trait_bonus

        # Tavern Dealer / Sharper difficulty DC
        dc = 13
        curr_loc = state.current_location()
        if curr_loc and hasattr(curr_loc, "security_level"):
            dc += max(0, (curr_loc.security_level - 50) // 15)

        if total_roll >= dc:
            return True, False, "소매 속 밑장빼기 손기술이 완벽하게 성공했습니다!"
        else:
            # Caught cheating!
            return False, True, "주사위를 바꿔치기하려던 찰나, 타짜의 서슬 퍼런 눈과 마주치며 손목을 낚아채였습니다!"

    # -----------------------------------------------------------------
    # Tavern Brawl & Aggro Trigger
    # -----------------------------------------------------------------
    @classmethod
    def trigger_tavern_brawl(cls, state: Any, reason: str = "도박 사기 적발") -> List[str]:
        """
        Triggers an immediate tavern brawl when cheating is exposed or dispute escalates:
        1. Non-allied NPCs at location become hostile.
        2. Player loses 15 reputation.
        3. Current location is blacklisted in gambling record.
        4. Ambient tables/chairs smashed.
        """
        logs = []
        loc_id = getattr(state.player, "location", "")
        record = cls.get_gambling_record(state)
        record.cheating_caught += 1
        record.brawls_started += 1

        if loc_id and loc_id not in record.blacklisted_locations:
            record.blacklisted_locations.append(loc_id)

        # 1. Reputation drop
        state.player.reputation = max(-100, getattr(state.player, "reputation", 0) - 15)
        logs.append(f"🚨 [사기 발각 및 평판 추락]: '{reason}'(으)로 인해 세간의 평판이 15 하락했습니다. (현재 평판: {state.player.reputation})")

        # 2. Tavern NPCs hostile conversion
        if loc_id in state.locations:
            loc_npcs = state.npcs_in_location(loc_id)
            for npc in loc_npcs:
                if npc.alive and npc.disposition not in ["allied", "companion"]:
                    npc.disposition = "hostile"
                    logs.append(f"💢 [주점 난투극 발발]: [{npc.name}](이)가 술상을 걷어차고 무기를 뽑아 들며 당신을 죽일 듯 노려봅니다!")

        # 3. Ambient chaos
        logs.append("💥 주점 안의 도박꾼들과 경비병들이 고함을 지르며 의자와 술병을 집어 던지기 시작합니다! (도박장 영구 출입 금지)")
        return logs

    # -----------------------------------------------------------------
    # Play Chinchiro (주사위 섯다 / 친치로)
    # -----------------------------------------------------------------
    @classmethod
    def play_chinchiro(
        cls,
        state: Any,
        bet_gold: int,
        cheat_technique: Optional[str] = None,
    ) -> GamblingOutcome:
        """
        Executes a deterministic round of Chinchiro.
        """
        record = cls.get_gambling_record(state)
        record.total_games += 1

        loc_id = getattr(state.player, "location", "")
        if loc_id in record.blacklisted_locations:
            return GamblingOutcome(
                game_type="chinchiro",
                bet_gold=bet_gold,
                payout_gold=0,
                net_gold=0,
                player_dice=[0, 0, 0],
                dealer_dice=[0, 0, 0],
                player_hand="출입 금지",
                dealer_hand="출입 금지",
                result="loss",
                narrative_log="🚫 [도박장 출입 정지]: 과거 사기 전적으로 인해 이 주점의 도박판에 발을 들일 수 없습니다!",
                traits=["출입금지_거부"],
            )

        if state.player.gold < bet_gold:
            return GamblingOutcome(
                game_type="chinchiro",
                bet_gold=bet_gold,
                payout_gold=0,
                net_gold=0,
                player_dice=[0, 0, 0],
                dealer_dice=[0, 0, 0],
                player_hand="판돈 부족",
                dealer_hand="판돈 부족",
                result="loss",
                narrative_log=f"⚠️ 판돈이 부족합니다. (소지금: {state.player.gold}G, 필요 판돈: {bet_gold}G)",
                traits=["골드부족_거부"],
            )

        # Cheating resolution
        is_cheating = bool(cheat_technique)
        is_caught = False
        tavern_brawl = False
        brawl_logs = []

        if is_cheating:
            record.cheating_attempts += 1
            cheat_ok, cheat_caught, cheat_msg = cls.attempt_cheat(state, technique=cheat_technique or "sleight_of_hand")
            if cheat_caught:
                is_caught = True
                tavern_brawl = True
                state.player.gold = max(0, state.player.gold - bet_gold)  # Gold forfeited
                brawl_logs = cls.trigger_tavern_brawl(state, reason="친치로 주사위 밑장빼기 적발")
                full_log = f"🚨 {cheat_msg}\n" + "\n".join(brawl_logs)
                return GamblingOutcome(
                    game_type="chinchiro",
                    bet_gold=bet_gold,
                    payout_gold=0,
                    net_gold=-bet_gold,
                    player_dice=[1, 1, 1],
                    dealer_dice=[0, 0, 0],
                    player_hand="사기 적발",
                    dealer_hand="판돈 몰수",
                    result="caught_cheating",
                    is_cheating_attempted=True,
                    is_caught=True,
                    tavern_brawl_triggered=True,
                    narrative_log=full_log,
                    traits=["사기적발", "난투극"],
                )
            else:
                # Cheating succeeded! Force 1-1-1 (Pinzoro)
                p_dice = [1, 1, 1]
        else:
            p_dice = [random.randint(1, 6) for _ in range(3)]

        d_dice = [random.randint(1, 6) for _ in range(3)]

        p_score, p_hand, p_mult = cls.evaluate_chinchiro_hand(p_dice)
        d_score, d_hand, d_mult = cls.evaluate_chinchiro_hand(d_dice)

        # Outcome evaluation
        if p_score == -50:
            # Player got Hifumi -> double loss
            net_gold = -int(bet_gold * 2)
            state.player.gold = max(0, state.player.gold + net_gold)
            record.losses += 1
            record.total_losses += abs(net_gold)
            res_str = "loss"
            log = f"🎲 [친치로 패배 (피박)]: 플레이어 [{p_hand}] vs 딜러 [{d_hand}]. 베팅액의 2배인 {abs(net_gold)}G를 잃었습니다!"

        elif d_score == -50:
            # Dealer got Hifumi -> player double win
            net_gold = int(bet_gold * 2)
            state.player.gold += net_gold
            record.wins += 1
            record.total_winnings += net_gold
            res_str = "win"
            log = f"🎲 [친치로 대승!]: 딜러의 뼈아픈 실책 [{d_hand}]! 베팅액의 2배인 {net_gold}G를 획득했습니다!"

        elif p_score > d_score:
            mult = max(1.0, p_mult)
            net_gold = int(bet_gold * mult)
            state.player.gold += net_gold
            record.wins += 1
            record.total_winnings += net_gold
            res_str = "win"
            log = f"🎲 [친치로 승리!]: 플레이어 [{p_hand}] vs 딜러 [{d_hand}]. (배당 {mult:.1f}배) 순수익 +{net_gold}G!"

        elif p_score < d_score:
            net_gold = -bet_gold
            state.player.gold = max(0, state.player.gold - bet_gold)
            record.losses += 1
            record.total_losses += bet_gold
            res_str = "loss"
            log = f"🎲 [친치로 패배]: 플레이어 [{p_hand}] vs 딜러 [{d_hand}]. 판돈 {bet_gold}G를 잃었습니다."

        else:
            net_gold = 0
            record.draws += 1
            res_str = "draw"
            log = f"🎲 [친치로 무승부]: 플레이어 [{p_hand}] vs 딜러 [{d_hand}]. 판돈이 반환되었습니다."

        record.net_profit = record.total_winnings - record.total_losses

        return GamblingOutcome(
            game_type="chinchiro",
            bet_gold=bet_gold,
            payout_gold=bet_gold + net_gold if net_gold >= 0 else 0,
            net_gold=net_gold,
            player_dice=p_dice,
            dealer_dice=d_dice,
            player_hand=p_hand,
            dealer_hand=d_hand,
            result=res_str,
            is_cheating_attempted=is_cheating,
            is_caught=False,
            tavern_brawl_triggered=False,
            narrative_log=log,
            traits=["친치로", res_str],
        )

    # -----------------------------------------------------------------
    # Play High-Low (하이-로우 베팅 대결)
    # -----------------------------------------------------------------
    @classmethod
    def play_high_low(
        cls,
        state: Any,
        bet_gold: int,
        prediction: str = "high",  # "high", "low", "seven"
        cheat_technique: Optional[str] = None,
    ) -> GamblingOutcome:
        """
        Executes a deterministic round of High-Low (2d6).
        """
        record = cls.get_gambling_record(state)
        record.total_games += 1

        loc_id = getattr(state.player, "location", "")
        if loc_id in record.blacklisted_locations:
            return GamblingOutcome(
                game_type="high_low",
                bet_gold=bet_gold,
                payout_gold=0,
                net_gold=0,
                player_dice=[0, 0],
                dealer_dice=[0, 0],
                player_hand="출입 금지",
                dealer_hand="출입 금지",
                result="loss",
                narrative_log="🚫 [도박장 출입 정지]: 과거 사기 전적으로 인해 이 주점의 도박판에 발을 들일 수 없습니다!",
                traits=["출입금지_거부"],
            )

        if state.player.gold < bet_gold:
            return GamblingOutcome(
                game_type="high_low",
                bet_gold=bet_gold,
                payout_gold=0,
                net_gold=0,
                player_dice=[0, 0],
                dealer_dice=[0, 0],
                player_hand="판돈 부족",
                dealer_hand="판돈 부족",
                result="loss",
                narrative_log=f"⚠️ 판돈이 부족합니다. (소지금: {state.player.gold}G, 필요 판돈: {bet_gold}G)",
                traits=["골드부족_거부"],
            )

        is_cheating = bool(cheat_technique)
        if is_cheating:
            record.cheating_attempts += 1
            cheat_ok, cheat_caught, cheat_msg = cls.attempt_cheat(state, technique=cheat_technique or "weighted_dice")
            if cheat_caught:
                state.player.gold = max(0, state.player.gold - bet_gold)
                brawl_logs = cls.trigger_tavern_brawl(state, reason="하이로우 무게추 주사위 적발")
                full_log = f"🚨 {cheat_msg}\n" + "\n".join(brawl_logs)
                return GamblingOutcome(
                    game_type="high_low",
                    bet_gold=bet_gold,
                    payout_gold=0,
                    net_gold=-bet_gold,
                    player_dice=[0, 0],
                    dealer_dice=[0, 0],
                    player_hand="사기 적발",
                    dealer_hand="판돈 몰수",
                    result="caught_cheating",
                    is_cheating_attempted=True,
                    is_caught=True,
                    tavern_brawl_triggered=True,
                    narrative_log=full_log,
                    traits=["사기적발", "난투극"],
                )
            else:
                # Cheating success! Rig dice to match prediction
                if prediction == "high":
                    dice = [5, 6]
                elif prediction == "low":
                    dice = [1, 2]
                else:
                    dice = [3, 4]
        else:
            dice = [random.randint(1, 6), random.randint(1, 6)]

        total, hand_name = cls.evaluate_high_low_hand(dice)

        is_win = False
        mult = 1.0

        if prediction == "seven" and total == 7:
            is_win = True
            mult = 4.0
        elif prediction == "high" and total > 7:
            is_win = True
            mult = 1.0
        elif prediction == "low" and total < 7:
            is_win = True
            mult = 1.0

        if is_win:
            net_gold = int(bet_gold * mult)
            state.player.gold += net_gold
            record.wins += 1
            record.total_winnings += net_gold
            res_str = "win"
            log = f"🎲 [하이-로우 적중!]: 주사위 눈 ({dice[0]}, {dice[1]}) 합산 [{hand_name}]! (배당 {mult:.1f}배) 순수익 +{net_gold}G!"
        else:
            net_gold = -bet_gold
            state.player.gold = max(0, state.player.gold - bet_gold)
            record.losses += 1
            record.total_losses += bet_gold
            res_str = "loss"
            log = f"🎲 [하이-로우 불발]: 주사위 눈 ({dice[0]}, {dice[1]}) 합산 [{hand_name}] (예측: {prediction}). 판돈 {bet_gold}G를 잃었습니다."

        record.net_profit = record.total_winnings - record.total_losses

        return GamblingOutcome(
            game_type="high_low",
            bet_gold=bet_gold,
            payout_gold=bet_gold + net_gold if net_gold >= 0 else 0,
            net_gold=net_gold,
            player_dice=dice,
            dealer_dice=dice,
            player_hand=hand_name,
            dealer_hand=f"예측: {prediction}",
            result=res_str,
            is_cheating_attempted=is_cheating,
            is_caught=False,
            tavern_brawl_triggered=False,
            narrative_log=log,
            traits=["하이로우", res_str],
        )

    # -----------------------------------------------------------------
    # FactSheet Summary Formatter
    # -----------------------------------------------------------------
    @classmethod
    def get_gambling_status_summary(cls, state: Any, outcome: Optional[GamblingOutcome] = None) -> str:
        """Generates a concise Korean deterministic status briefing string."""
        record = cls.get_gambling_record(state)
        lines = [
            f"=== 🎲 주점 도박 및 주사위 대결 현황 ===",
            f"- 전적: {record.total_games}전 {record.wins}승 {record.losses}패 {record.draws}무 (순수익: {record.net_profit:+d}G)",
            f"- 사기 시도: {record.cheating_attempts}회 (적발 {record.cheating_caught}회, 난투극 {record.brawls_started}회)",
        ]
        if outcome:
            lines.append(f"- 최근 대결: [{outcome.game_type.upper()}] 결과: {outcome.result.upper()} (손익: {outcome.net_gold:+d}G)")
            lines.append(f"  * 판정: {outcome.narrative_log}")
        return "\n".join(lines)
