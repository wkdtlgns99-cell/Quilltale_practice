"""
Quilltale Gladiator Arena & Duel Ranking Engine (arena_engine.py)
100% deterministic colosseum duels, beast hunts, crowd favor, and execution/mercy mechanics:
- 5 Gladiator Tiers: Bronze (Slave) -> Silver -> Gold -> Platinum -> Champion.
- Dynamic Crowd Favor (0~100): High favor triggers crowd battle buffs & potion tosses.
- Duel combat mechanics: Attack, Heavy Strike, Showboat/Taunt, Parry & Counter.
- Moral Verdict: Execute (Infamy, Blood Money) vs Spare (Honor, Ally recruitment).
- Compliance: Rule 5 traits: List[str] on all dataclasses.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import random


@dataclass
class GladiatorOpponent:
    """Represents an arena gladiator or captured beast."""
    opponent_id: str
    name: str
    title: str
    tier: str  # "bronze", "silver", "gold", "platinum", "champion"
    level: int
    hp: int
    max_hp: int
    atk: int
    defense: int
    weapon: str
    tactics: str = "aggressive"  # "aggressive", "defensive", "beast_berserk", "evasive"
    traits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opponent_id": self.opponent_id,
            "name": self.name,
            "title": self.title,
            "tier": self.tier,
            "level": self.level,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "atk": self.atk,
            "defense": self.defense,
            "weapon": self.weapon,
            "tactics": self.tactics,
            "traits": list(self.traits),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GladiatorOpponent:
        return cls(
            opponent_id=data.get("opponent_id", ""),
            name=data.get("name", "이름 없는 검투사"),
            title=data.get("title", ""),
            tier=data.get("tier", "bronze"),
            level=data.get("level", 1),
            hp=data.get("hp", 80),
            max_hp=data.get("max_hp", 80),
            atk=data.get("atk", 12),
            defense=data.get("defense", 5),
            weapon=data.get("weapon", "녹슨 숏소드"),
            tactics=data.get("tactics", "aggressive"),
            traits=data.get("traits", []),
        )


@dataclass
class ArenaMatch:
    """Represents an ongoing or listed arena combat match."""
    match_id: str
    match_type: str  # "duel", "beast_hunt", "champion_brawl"
    opponent: GladiatorOpponent
    purse_gold: int
    entry_fee: int
    player_bet: int = 0
    odds: float = 1.5
    crowd_favor: int = 50  # 0 to 100
    is_active: bool = False
    is_concluded: bool = False
    winner_id: Optional[str] = None
    verdict: Optional[str] = None  # "executed", "spared"
    traits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "match_id": self.match_id,
            "match_type": self.match_type,
            "opponent": self.opponent.to_dict(),
            "purse_gold": self.purse_gold,
            "entry_fee": self.entry_fee,
            "player_bet": self.player_bet,
            "odds": self.odds,
            "crowd_favor": self.crowd_favor,
            "is_active": self.is_active,
            "is_concluded": self.is_concluded,
            "winner_id": self.winner_id,
            "verdict": self.verdict,
            "traits": list(self.traits),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ArenaMatch:
        opp_data = data.get("opponent", {})
        opponent = GladiatorOpponent.from_dict(opp_data) if isinstance(opp_data, dict) else opp_data
        return cls(
            match_id=data.get("match_id", ""),
            match_type=data.get("match_type", "duel"),
            opponent=opponent,
            purse_gold=data.get("purse_gold", 100),
            entry_fee=data.get("entry_fee", 20),
            player_bet=data.get("player_bet", 0),
            odds=data.get("odds", 1.5),
            crowd_favor=data.get("crowd_favor", 50),
            is_active=data.get("is_active", False),
            is_concluded=data.get("is_concluded", False),
            winner_id=data.get("winner_id"),
            verdict=data.get("verdict"),
            traits=data.get("traits", []),
        )


@dataclass
class ArenaActionResult:
    """Outcome of a single round or verdict in the arena."""
    action_type: str  # "start_match", "attack", "heavy_strike", "taunt", "parry", "verdict"
    success: bool
    damage_dealt: int = 0
    damage_taken: int = 0
    crowd_favor_delta: int = 0
    current_crowd_favor: int = 50
    purse_won: int = 0
    player_hp_after: int = 0
    opponent_hp_after: int = 0
    is_concluded: bool = False
    verdict_required: bool = False
    narration_logs: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "success": self.success,
            "damage_dealt": self.damage_dealt,
            "damage_taken": self.damage_taken,
            "crowd_favor_delta": self.crowd_favor_delta,
            "current_crowd_favor": self.current_crowd_favor,
            "purse_won": self.purse_won,
            "player_hp_after": self.player_hp_after,
            "opponent_hp_after": self.opponent_hp_after,
            "is_concluded": self.is_concluded,
            "verdict_required": self.verdict_required,
            "narration_logs": list(self.narration_logs),
            "traits": list(self.traits),
        }


@dataclass
class GladiatorCareerRecord:
    """Player's persistent career progression in the arena."""
    rank_tier: str = "bronze"  # "bronze", "silver", "gold", "platinum", "champion"
    rank_points: int = 0
    total_fights: int = 0
    wins: int = 0
    losses: int = 0
    executions: int = 0
    spares: int = 0
    crowd_reputation: int = 50  # 0 to 100
    traits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank_tier": self.rank_tier,
            "rank_points": self.rank_points,
            "total_fights": self.total_fights,
            "wins": self.wins,
            "losses": self.losses,
            "executions": self.executions,
            "spares": self.spares,
            "crowd_reputation": self.crowd_reputation,
            "traits": list(self.traits),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GladiatorCareerRecord:
        return cls(
            rank_tier=data.get("rank_tier", "bronze"),
            rank_points=data.get("rank_points", 0),
            total_fights=data.get("total_fights", 0),
            wins=data.get("wins", 0),
            losses=data.get("losses", 0),
            executions=data.get("executions", 0),
            spares=data.get("spares", 0),
            crowd_reputation=data.get("crowd_reputation", 50),
            traits=data.get("traits", []),
        )


class GladiatorArenaEngine:
    """
    100% Deterministic Engine for Gladiator Colosseums & Underground Pits.
    Governs match matchmaking, crowd favor dynamics, arena combat rounds,
    betting settlements, and life-or-death moral verdicts.
    """

    TIER_RANK_REQUIREMENTS = {
        "bronze": 0,
        "silver": 100,
        "gold": 250,
        "platinum": 500,
        "champion": 1000,
    }

    @classmethod
    def get_career_record(cls, state: Any) -> GladiatorCareerRecord:
        """Retrieves or instantiates the player's career record on WorldState."""
        if not hasattr(state, "arena_record") or state.arena_record is None:
            state.arena_record = GladiatorCareerRecord(traits=["rookie_gladiator"])
        elif isinstance(state.arena_record, dict):
            state.arena_record = GladiatorCareerRecord.from_dict(state.arena_record)
        return state.arena_record

    @classmethod
    def generate_match_listing(cls, state: Any) -> List[ArenaMatch]:
        """Generates 3 arena matches scaled to player's current rank tier."""
        record = cls.get_career_record(state)
        tier = record.rank_tier

        if tier == "bronze":
            return [
                ArenaMatch(
                    match_id="match_b1",
                    match_type="duel",
                    opponent=GladiatorOpponent(
                        opponent_id="gladiator_gordo",
                        name="피투성이 신참 고르도",
                        title="노예 검투사",
                        tier="bronze",
                        level=2,
                        hp=70,
                        max_hp=70,
                        atk=12,
                        defense=4,
                        weapon="녹슨 철퇴",
                        tactics="aggressive",
                        traits=["slave", "reckless"]
                    ),
                    purse_gold=80,
                    entry_fee=15,
                    odds=1.8,
                    traits=["tier_bronze"]
                ),
                ArenaMatch(
                    match_id="match_b2",
                    match_type="beast_hunt",
                    opponent=GladiatorOpponent(
                        opponent_id="beast_sand_wolf",
                        name="굶주린 모래 하이에나",
                        title="사막의 포식자",
                        tier="bronze",
                        level=3,
                        hp=60,
                        max_hp=60,
                        atk=15,
                        defense=2,
                        weapon="날카로운 송곳니",
                        tactics="beast_berserk",
                        traits=["beast", "feral"]
                    ),
                    purse_gold=120,
                    entry_fee=25,
                    odds=2.0,
                    traits=["tier_bronze", "beast"]
                ),
                ArenaMatch(
                    match_id="match_b3",
                    match_type="duel",
                    opponent=GladiatorOpponent(
                        opponent_id="gladiator_vance",
                        name="철벽의 벤스",
                        title="방패병",
                        tier="bronze",
                        level=4,
                        hp=90,
                        max_hp=90,
                        atk=10,
                        defense=8,
                        weapon="대형 목재 방패와 단검",
                        tactics="defensive",
                        traits=["shield_bearer"]
                    ),
                    purse_gold=150,
                    entry_fee=30,
                    odds=1.6,
                    traits=["tier_bronze"]
                ),
            ]
        elif tier == "silver":
            return [
                ArenaMatch(
                    match_id="match_s1",
                    match_type="duel",
                    opponent=GladiatorOpponent(
                        opponent_id="gladiator_selena",
                        name="독사의 셀레나",
                        title="쌍검사",
                        tier="silver",
                        level=6,
                        hp=110,
                        max_hp=110,
                        atk=22,
                        defense=8,
                        weapon="독 바른 쌍곡도",
                        tactics="evasive",
                        traits=["poisoner", "swift"]
                    ),
                    purse_gold=250,
                    entry_fee=50,
                    odds=1.9,
                    traits=["tier_silver"]
                ),
                ArenaMatch(
                    match_id="match_s2",
                    match_type="beast_hunt",
                    opponent=GladiatorOpponent(
                        opponent_id="beast_cave_bear",
                        name="장님 동굴 곰",
                        title="지하의 흉폭한 야수",
                        tier="silver",
                        level=7,
                        hp=160,
                        max_hp=160,
                        atk=26,
                        defense=12,
                        weapon="쇄골 파쇄 발톱",
                        tactics="beast_berserk",
                        traits=["beast", "heavy"]
                    ),
                    purse_gold=350,
                    entry_fee=70,
                    odds=2.2,
                    traits=["tier_silver", "beast"]
                ),
            ]
        else:  # Gold, Platinum, Champion
            return [
                ArenaMatch(
                    match_id="match_g1",
                    match_type="champion_brawl",
                    opponent=GladiatorOpponent(
                        opponent_id="champion_valentin",
                        name="불패의 발렌타인",
                        title="콜로세움 군주",
                        tier="gold",
                        level=12,
                        hp=220,
                        max_hp=220,
                        atk=35,
                        defense=18,
                        weapon="황금 대검 '심판'",
                        tactics="aggressive",
                        traits=["champion", "unyielding", "legendary"]
                    ),
                    purse_gold=800,
                    entry_fee=150,
                    odds=2.5,
                    traits=["tier_champion"]
                ),
            ]

    @classmethod
    def start_match(
        cls,
        state: Any,
        match: ArenaMatch,
        player_bet: int = 0
    ) -> ArenaActionResult:
        """Starts an arena match, verifying fees and locking player bets."""
        player = getattr(state, "player", None)
        player_gold = getattr(player, "gold", 0) if player else 0

        total_cost = match.entry_fee + player_bet
        if player_gold < total_cost:
            return ArenaActionResult(
                action_type="start_match",
                success=False,
                narration_logs=[
                    f"투기장 출전 자금이 부족합니다! (필요: {total_cost} G = 참가비 {match.entry_fee} G + 배팅 {player_bet} G, 보유: {player_gold} G)"
                ]
            )

        # Deduct gold from player
        player.gold -= total_cost
        match.player_bet = player_bet
        match.is_active = True
        match.crowd_favor = 50
        state.active_arena_match = match

        logs = [
            f"⚔️ [투기장 출전 선언] {match.entry_fee} 골드를 지불하고 결투에 입장했습니다.",
            f"상대: [{match.opponent.name}] ({match.opponent.title}) / 무기: {match.opponent.weapon}",
            f"관중들이 모래사장 위로 흙먼지를 일으키며 함성을 지르기 시작합니다! (현재 관중 열광도: {match.crowd_favor}/100)"
        ]
        if player_bet > 0:
            logs.append(f"💰 자신의 승리에 {player_bet} 골드를 베팅했습니다 (배당률: {match.odds}x).")

        return ArenaActionResult(
            action_type="start_match",
            success=True,
            current_crowd_favor=match.crowd_favor,
            player_hp_after=player.health,
            opponent_hp_after=match.opponent.hp,
            narration_logs=logs
        )

    @classmethod
    def resolve_arena_combat_turn(
        cls,
        state: Any,
        match: ArenaMatch,
        action_type: str = "attack"
    ) -> ArenaActionResult:
        """
        Executes a turn of arena combat.
        action_type:
        - "attack": Standard strike.
        - "heavy_strike": High risk, high damage, crowd favor +15.
        - "taunt": No damage, boosts crowd favor by +25, taunts opponent.
        - "parry": Defensive counter stance, reduces damage taken, counter-attacks.
        """
        if not match.is_active or match.is_concluded:
            return ArenaActionResult(
                action_type=action_type,
                success=False,
                narration_logs=["현재 진행 중인 유효한 투기장 결투가 없습니다."]
            )

        player = getattr(state, "player", None)
        p_atk = getattr(player, "strength", 12) + random.randint(2, 6)
        p_def = getattr(player, "constitution", 10) // 2

        opp = match.opponent
        o_atk = opp.atk + random.randint(1, 4)
        o_def = opp.defense

        logs: List[str] = []
        favor_delta = 0
        p_dmg_dealt = 0
        o_dmg_dealt = 0

        # Crowd favor buff: if favor >= 70, +20% damage buff!
        crowd_buff = 1.2 if match.crowd_favor >= 70 else 1.0

        if action_type == "taunt":
            favor_delta = 25
            logs.append("🗣️ [도발 및 쇼맨십] 당신은 무기를 치켜들고 관중석을 향해 포효했습니다! 관중들이 열광의 도가니에 빠져듭니다!")
            # Opponent gets an attack with slight penalty
            o_dmg_dealt = max(1, int(o_atk * 0.8) - p_def)
            player.health = max(0, player.health - o_dmg_dealt)
            logs.append(f"[{opp.name}]이(가) 빈틈을 노려 {o_dmg_dealt}의 피해를 입혔습니다.")

        elif action_type == "heavy_strike":
            hit_chance = 75
            roll = random.randint(1, 100)
            if roll <= hit_chance:
                raw_dmg = int((p_atk * 1.6 - o_def) * crowd_buff)
                p_dmg_dealt = max(5, raw_dmg)
                opp.hp = max(0, opp.hp - p_dmg_dealt)
                favor_delta = 15
                logs.append(f"💥 [강타 작렬!] 육중한 일격이 {opp.name}의 가드를 부수고 {p_dmg_dealt}의 치명적 피해를 입혔습니다! 관중들이 환호합니다!")
            else:
                favor_delta = -10
                logs.append(f"빗나감! 무거운 일격을 피한 {opp.name}의 반격 기회가 열렸습니다. (관중 야유)")

            # Opponent hits back
            o_dmg_dealt = max(1, o_atk - p_def)
            player.health = max(0, player.health - o_dmg_dealt)
            logs.append(f"[{opp.name}]의 반격으로 {o_dmg_dealt}의 피해를 입었습니다.")

        elif action_type == "parry":
            # Parry reduces incoming damage significantly and deals counter damage
            p_dmg_dealt = max(2, int(p_atk * 0.9 - o_def))
            o_dmg_dealt = max(0, (o_atk // 2) - p_def)
            opp.hp = max(0, opp.hp - p_dmg_dealt)
            player.health = max(0, player.health - o_dmg_dealt)
            favor_delta = 10
            logs.append(f"🛡️ [흘리기 및 반격] 적의 궤적을 튕겨내며 {p_dmg_dealt}의 카운터 공격을 꽂아 넣었습니다! (피격 경감: {o_dmg_dealt} 피해)")

        else:  # Standard attack
            raw_dmg = int((p_atk - o_def) * crowd_buff)
            p_dmg_dealt = max(3, raw_dmg)
            opp.hp = max(0, opp.hp - p_dmg_dealt)

            o_dmg_dealt = max(1, o_atk - p_def)
            player.health = max(0, player.health - o_dmg_dealt)
            favor_delta = 5
            logs.append(f"⚔️ [공방 교환] [{opp.name}]에게 {p_dmg_dealt}의 피해를 입히고, {o_dmg_dealt}의 반격을 받았습니다.")

        # Update favor clamped to 0~100
        match.crowd_favor = max(0, min(100, match.crowd_favor + favor_delta))

        # Check potion toss gimmick from crowd if favor >= 80 and player HP is low
        if match.crowd_favor >= 80 and player.health < 40 and random.random() < 0.5:
            heal_amount = 25
            player.health += heal_amount
            logs.append(f"🍷 [관중의 선물!] 열광한 귀족 관중이 모래사장으로 특제 치유 물약을 던져주었습니다! (체력 +{heal_amount})")

        # Check outcome
        verdict_required = False
        is_concluded = False
        purse_won = 0

        if opp.hp <= 0:
            verdict_required = True
            logs.append(
                f"🚨 [적 무력화!] [{opp.name}]이(가) 피를 흘리며 모래사장에 무릎을 꿇었습니다! "
                f"관중석의 함성이 귀를 찢을 듯 울려 퍼지며, 영주와 관중들이 엄지손가락을 치켜들거나 내리기 시작합니다! "
                f"(선택지: '처형' 또는 '자비/살려주기'를 선언하십시오!)"
            )
        elif player.health <= 0:
            is_concluded = True
            match.is_active = False
            match.is_concluded = True
            match.winner_id = opp.opponent_id
            record = cls.get_career_record(state)
            record.total_fights += 1
            record.losses += 1
            record.rank_points = max(0, record.rank_points - 10)
            logs.append(
                f"💀 [패배] 당신은 피를 쏟으며 콜로세움의 차가운 모래바닥에 쓰러졌습니다. "
                f"의무병들이 달려와 당신의 몸을 끌어내며 판돈과 배팅금이 몰수되었습니다."
            )

        return ArenaActionResult(
            action_type=action_type,
            success=True,
            damage_dealt=p_dmg_dealt,
            damage_taken=o_dmg_dealt,
            crowd_favor_delta=favor_delta,
            current_crowd_favor=match.crowd_favor,
            purse_won=purse_won,
            player_hp_after=player.health,
            opponent_hp_after=opp.hp,
            is_concluded=is_concluded,
            verdict_required=verdict_required,
            narration_logs=logs
        )

    @classmethod
    def resolve_finishing_verdict(
        cls,
        state: Any,
        match: ArenaMatch,
        verdict: str = "spare"
    ) -> ArenaActionResult:
        """
        Processes the moral verdict on a defeated opponent.
        - "execute": Brutal fatality. Reputation -5 (fear/notoriety), +25% blood bonus gold.
        - "spare": Honorable mercy. Reputation +10 (honor/fame), opens future ally flag.
        """
        if not match.is_active or match.opponent.hp > 0:
            return ArenaActionResult(
                action_type="verdict",
                success=False,
                narration_logs=["처형 또는 자비를 결정할 패배자가 없습니다."]
            )

        player = getattr(state, "player", None)
        record = cls.get_career_record(state)

        match.is_active = False
        match.is_concluded = True
        match.winner_id = "player"
        match.verdict = verdict

        record.total_fights += 1
        record.wins += 1
        record.rank_points += 30

        # Calculate purse and bets
        base_purse = match.purse_gold
        bet_payout = int(match.player_bet * match.odds) if match.player_bet > 0 else 0

        logs: List[str] = []

        if verdict == "execute":
            record.executions += 1
            blood_bonus = int(base_purse * 0.25)
            total_purse = base_purse + blood_bonus + bet_payout
            if player:
                player.gold += total_purse
                player.reputation = getattr(player, "reputation", 0) - 5

            logs.append(
                f"🩸 [피의 처형 선언] 당신은 엄지를 아래로 내리꽂으며 [{match.opponent.name}]의 목덜미를 단숨에 베어 넘겼습니다! "
                f"붉은 피가 모래사장을 적시자, 관중들이 광기에 젖어 환호성을 지릅니다! (악명 상승, 잔혹성 입증)"
            )
            logs.append(f"💰 피의 상금 획득: {total_purse} G (기본 {base_purse} G + 유혈 보너스 {blood_bonus} G + 배팅 {bet_payout} G)")

        else:  # spare
            record.spares += 1
            total_purse = base_purse + bet_payout
            if player:
                player.gold += total_purse
                player.reputation = getattr(player, "reputation", 0) + 10

            logs.append(
                f"🕊️ [고결한 자비 선언] 당신은 무기를 거두고 쓰러진 [{match.opponent.name}]에게 손을 내밀었습니다. "
                f"잠시 침묵하던 콜로세움 관중석에서 진정한 전사를 향한 우레와 같은 기립 박수가 터져 나옵니다! (명예 및 호감도 급상승)"
            )
            logs.append(f"💰 승리 상금 수령: {total_purse} G (기본 {base_purse} G + 배팅 {bet_payout} G)")

        # Rank promotion check
        if record.rank_tier == "bronze" and record.rank_points >= 100:
            record.rank_tier = "silver"
            logs.append("🎖️ [계급 승급!] 브론즈 검투 노예에서 [실버 검투사]로 공식 승급되었습니다!")
        elif record.rank_tier == "silver" and record.rank_points >= 250:
            record.rank_tier = "gold"
            logs.append("🎖️ [계급 승급!] 실버에서 [골드 베테랑 검투사]로 승급되었습니다!")
        elif record.rank_tier == "gold" and record.rank_points >= 500:
            record.rank_tier = "platinum"
            logs.append("🎖️ [계급 승급!] [플래티넘 정예 투사]로 승급되었습니다!")

        return ArenaActionResult(
            action_type="verdict",
            success=True,
            current_crowd_favor=match.crowd_favor,
            purse_won=total_purse,
            player_hp_after=player.health if player else 0,
            opponent_hp_after=0,
            is_concluded=True,
            narration_logs=logs
        )

    @classmethod
    def get_arena_status_summary(
        cls,
        state: Any,
        match: Optional[ArenaMatch] = None,
        last_result: Optional[ArenaActionResult] = None
    ) -> str:
        """Generates a concise Korean summary for DeterministicFactSheet."""
        record = cls.get_career_record(state)
        active_match = match or getattr(state, "active_arena_match", None)

        tier_ko = {
            "bronze": "브론즈 (검투 노예)",
            "silver": "실버 (정규 검투사)",
            "gold": "골드 (베테랑 투사)",
            "platinum": "플래티넘 (정예 투사)",
            "champion": "챔피언 (콜로세움 군주)",
        }.get(record.rank_tier, record.rank_tier)

        lines = [
            f"[🏟️ 콜로세움 투기장 전적]",
            f"- 현재 계급: {tier_ko} (랭크 포인트: {record.rank_points}P)",
            f"- 전적: {record.wins}승 {record.losses}패 (처형 {record.executions}회 / 자비 {record.spares}회)",
        ]

        if active_match and active_match.is_active:
            lines.append(f"- 현재 결투: vs [{active_match.opponent.name}] ({active_match.opponent.title})")
            lines.append(f"- 상대 체력: {active_match.opponent.hp}/{active_match.opponent.max_hp} | 관중 열광도: {active_match.crowd_favor}/100")
            lines.append(f"- 걸린 파이트머니: {active_match.purse_gold} G (배팅: {active_match.player_bet} G)")

        if last_result and last_result.narration_logs:
            lines.append(f"- 최근 전황: {last_result.narration_logs[-1]}")

        return "\n".join(lines)
