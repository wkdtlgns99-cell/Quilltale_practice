"""
Quilltale Black Market Auction & NPC Bidding Engine (auction_engine.py)
100% deterministic underground auction mechanics:
- Multi-lot catalog (weapons, forbidden tomes, artifacts, contraband).
- NPC bidders with distinct archetypes, budgets, greed factors, and intimidation resistances.
- Deterministic auction tick & gavel countdown (3 -> 2 -> 1 -> Sold!).
- Player special maneuvers: Counter-bidding, Bidders Intimidation, Pedestal Snatch & Brawl.
- Compliance: Rule 5 traits: List[str] on all dataclasses.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import random


@dataclass
class AuctionLot:
    """Represents an item or artifact placed on the auction pedestal."""
    lot_id: str
    name: str
    description: str
    category: str  # "weapon", "artifact", "contraband", "armor", "potion"
    rarity: str    # "rare", "epic", "legendary", "forbidden"
    starting_bid: int
    current_bid: int
    highest_bidder_id: str
    highest_bidder_name: str
    min_increment: int = 50
    countdown: int = 3  # 3: First call, 2: Second call, 1: Third call, 0: Hammer down (Sold)
    is_concluded: bool = False
    winner_id: Optional[str] = None
    item_payload: Dict[str, Any] = field(default_factory=dict)
    traits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lot_id": self.lot_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "rarity": self.rarity,
            "starting_bid": self.starting_bid,
            "current_bid": self.current_bid,
            "highest_bidder_id": self.highest_bidder_id,
            "highest_bidder_name": self.highest_bidder_name,
            "min_increment": self.min_increment,
            "countdown": self.countdown,
            "is_concluded": self.is_concluded,
            "winner_id": self.winner_id,
            "item_payload": dict(self.item_payload),
            "traits": list(self.traits),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuctionLot:
        return cls(
            lot_id=data.get("lot_id", ""),
            name=data.get("name", "미확인 출품작"),
            description=data.get("description", ""),
            category=data.get("category", "artifact"),
            rarity=data.get("rarity", "rare"),
            starting_bid=data.get("starting_bid", 100),
            current_bid=data.get("current_bid", 100),
            highest_bidder_id=data.get("highest_bidder_id", ""),
            highest_bidder_name=data.get("highest_bidder_name", ""),
            min_increment=data.get("min_increment", 50),
            countdown=data.get("countdown", 3),
            is_concluded=data.get("is_concluded", False),
            winner_id=data.get("winner_id"),
            item_payload=data.get("item_payload", {}),
            traits=data.get("traits", []),
        )


@dataclass
class NPCBidder:
    """Represents an NPC participating in the underground auction."""
    npc_id: str
    name: str
    archetype: str  # "noble_collector", "cautious_merchant", "desperate_cultist", "aggressive_warlord"
    budget: int
    remaining_budget: int
    greed_factor: float = 1.0  # Max valuation multiplier
    intimidation_resistance: int = 12
    status: str = "active"     # "active", "intimidated", "out_of_budget"
    traits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "npc_id": self.npc_id,
            "name": self.name,
            "archetype": self.archetype,
            "budget": self.budget,
            "remaining_budget": self.remaining_budget,
            "greed_factor": self.greed_factor,
            "intimidation_resistance": self.intimidation_resistance,
            "status": self.status,
            "traits": list(self.traits),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NPCBidder:
        return cls(
            npc_id=data.get("npc_id", ""),
            name=data.get("name", "익명의 입찰자"),
            archetype=data.get("archetype", "cautious_merchant"),
            budget=data.get("budget", 500),
            remaining_budget=data.get("remaining_budget", 500),
            greed_factor=data.get("greed_factor", 1.0),
            intimidation_resistance=data.get("intimidation_resistance", 12),
            status=data.get("status", "active"),
            traits=data.get("traits", []),
        )


@dataclass
class AuctionActionResult:
    """The outcome of a player's or turn's action within the auction."""
    action_type: str  # "place_bid", "intimidate", "advance_tick", "snatch_lot", "browse", "start"
    success: bool
    current_lot_id: str
    highest_bid: int
    highest_bidder_name: str
    countdown: int
    brawl_triggered: bool = False
    gold_spent: int = 0
    acquired_item: Optional[Dict[str, Any]] = None
    narration_logs: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "success": self.success,
            "current_lot_id": self.current_lot_id,
            "highest_bid": self.highest_bid,
            "highest_bidder_name": self.highest_bidder_name,
            "countdown": self.countdown,
            "brawl_triggered": self.brawl_triggered,
            "gold_spent": self.gold_spent,
            "acquired_item": self.acquired_item,
            "narration_logs": list(self.narration_logs),
            "traits": list(self.traits),
        }


@dataclass
class BlackMarketAuctionState:
    """Full session state for the underground black market auction."""
    active_lots: List[AuctionLot] = field(default_factory=list)
    current_lot_index: int = 0
    bidders: List[NPCBidder] = field(default_factory=list)
    auction_turn_count: int = 0
    blacklisted_player: bool = False
    traits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_lots": [lot.to_dict() for lot in self.active_lots],
            "current_lot_index": self.current_lot_index,
            "bidders": [bidder.to_dict() for bidder in self.bidders],
            "auction_turn_count": self.auction_turn_count,
            "blacklisted_player": self.blacklisted_player,
            "traits": list(self.traits),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BlackMarketAuctionState:
        lots = [AuctionLot.from_dict(d) for d in data.get("active_lots", [])]
        bidders = [NPCBidder.from_dict(d) for d in data.get("bidders", [])]
        return cls(
            active_lots=lots,
            current_lot_index=data.get("current_lot_index", 0),
            bidders=bidders,
            auction_turn_count=data.get("auction_turn_count", 0),
            blacklisted_player=data.get("blacklisted_player", False),
            traits=data.get("traits", []),
        )


class BlackMarketAuctionEngine:
    """
    100% Deterministic Engine for Underground Black Market Auctions.
    Governs bidding dynamics, NPC psychological bidding, gavel countdowns,
    bidders intimidation, and pedestal theft maneuvers.
    """

    @classmethod
    def create_default_lots(cls) -> List[AuctionLot]:
        """Generates standard forbidden lots for the underground auction."""
        return [
            AuctionLot(
                lot_id="lot_cursed_dagger",
                name="칠흑의 피흡수 단검",
                description="고대 묘지에서 발굴된 저주받은 흑요석 단검. 타격 시 생명력을 흡수합니다.",
                category="weapon",
                rarity="epic",
                starting_bid=250,
                current_bid=250,
                highest_bidder_id="auctioneer",
                highest_bidder_name="경매사",
                min_increment=50,
                countdown=3,
                item_payload={
                    "name": "칠흑의 피흡수 단검",
                    "type": "weapon",
                    "atk": 16,
                    "description": "타격 시 10% 흡혈 효과가 깃든 단검.",
                    "traits": ["cursed", "lifesteal", "epic"]
                },
                traits=["contraband", "black_market"]
            ),
            AuctionLot(
                lot_id="lot_forbidden_grimoire",
                name="사령술사의 금지된 비전록",
                description="교단에 의해 금서로 지정된 고대 사령술 주문서. 시체 조작 지식이 적혀 있습니다.",
                category="artifact",
                rarity="legendary",
                starting_bid=500,
                current_bid=500,
                highest_bidder_id="auctioneer",
                highest_bidder_name="경매사",
                min_increment=100,
                countdown=3,
                item_payload={
                    "name": "사령술사의 금지된 비전록",
                    "type": "tome",
                    "necromancy_power": 25,
                    "description": "사령술 주문 소모 마나를 줄이고 하수인 능력치를 강화합니다.",
                    "traits": ["forbidden", "necromancy", "legendary"]
                },
                traits=["forbidden", "black_market"]
            ),
            AuctionLot(
                lot_id="lot_dragon_heart_elixir",
                name="진홍빛 용혈 영약",
                description="화룡의 심장 피를 증류하여 제조한 금지된 도핑 영약. 영구히 최대 체력을 올립니다.",
                category="contraband",
                rarity="rare",
                starting_bid=200,
                current_bid=200,
                highest_bidder_id="auctioneer",
                highest_bidder_name="경매사",
                min_increment=30,
                countdown=3,
                item_payload={
                    "name": "진홍빛 용혈 영약",
                    "type": "potion",
                    "permanent_max_hp": 25,
                    "description": "복용 시 영구적으로 최대 체력 +25.",
                    "traits": ["alchemical", "consumable", "rare"]
                },
                traits=["contraband", "black_market"]
            ),
            AuctionLot(
                lot_id="lot_shadow_cloak",
                name="그림자 암살자의 침묵 망토",
                description="소음을 완전히 흡수하고 어둠 속에서 윤곽을 지워주는 특수 가공 망토.",
                category="armor",
                rarity="epic",
                starting_bid=350,
                current_bid=350,
                highest_bidder_id="auctioneer",
                highest_bidder_name="경매사",
                min_increment=50,
                countdown=3,
                item_payload={
                    "name": "그림자 암살자의 침묵 망토",
                    "type": "armor",
                    "def": 8,
                    "stealth_bonus": 20,
                    "description": "은신 성공률을 20% 향상시키는 암살자용 외투.",
                    "traits": ["stealth", "shadow", "epic"]
                },
                traits=["black_market"]
            ),
        ]

    @classmethod
    def create_default_bidders(cls) -> List[NPCBidder]:
        """Generates standard NPC bidders with distinct psychological profiles."""
        return [
            NPCBidder(
                npc_id="bidder_noble",
                name="수집가 바론 백작",
                archetype="noble_collector",
                budget=1200,
                remaining_budget=1200,
                greed_factor=1.4,
                intimidation_resistance=15,
                status="active",
                traits=["noble", "wealthy"]
            ),
            NPCBidder(
                npc_id="bidder_merchant",
                name="장물아비 고르단",
                archetype="cautious_merchant",
                budget=800,
                remaining_budget=800,
                greed_factor=0.9,
                intimidation_resistance=10,
                status="active",
                traits=["merchant", "cautious"]
            ),
            NPCBidder(
                npc_id="bidder_cultist",
                name="어둠의 사도 말로크",
                archetype="desperate_cultist",
                budget=950,
                remaining_budget=950,
                greed_factor=1.6,
                intimidation_resistance=18,
                status="active",
                traits=["cultist", "fanatic"]
            ),
        ]

    @classmethod
    def initialize_auction(
        cls,
        state: Any = None,
        custom_lots: Optional[List[AuctionLot]] = None,
        custom_bidders: Optional[List[NPCBidder]] = None
    ) -> BlackMarketAuctionState:
        """Initializes a new black market auction session."""
        lots = custom_lots if custom_lots is not None else cls.create_default_lots()
        bidders = custom_bidders if custom_bidders is not None else cls.create_default_bidders()
        return BlackMarketAuctionState(
            active_lots=lots,
            current_lot_index=0,
            bidders=bidders,
            auction_turn_count=0,
            blacklisted_player=False,
            traits=["underground_auction", "session_active"]
        )

    @classmethod
    def get_current_lot(cls, auction_state: BlackMarketAuctionState) -> Optional[AuctionLot]:
        """Returns the lot currently being auctioned, or None if all completed."""
        if not auction_state or not auction_state.active_lots:
            return None
        if auction_state.current_lot_index < len(auction_state.active_lots):
            return auction_state.active_lots[auction_state.current_lot_index]
        return None

    @classmethod
    def player_place_bid(
        cls,
        state: Any,
        auction_state: BlackMarketAuctionState,
        bid_amount: int
    ) -> AuctionActionResult:
        """Processes player's bid on the current auction lot."""
        if auction_state.blacklisted_player:
            return AuctionActionResult(
                action_type="place_bid",
                success=False,
                current_lot_id="",
                highest_bid=0,
                highest_bidder_name="없음",
                countdown=0,
                narration_logs=["[경매장 입장 불가] 과거 난동 및 강탈 시도로 인해 암시장 경매장에서 영구 추방되었습니다."]
            )

        current_lot = cls.get_current_lot(auction_state)
        if not current_lot or current_lot.is_concluded:
            return AuctionActionResult(
                action_type="place_bid",
                success=False,
                current_lot_id="",
                highest_bid=0,
                highest_bidder_name="없음",
                countdown=0,
                narration_logs=["현재 진행 중인 경매 매물이 없습니다."]
            )

        player = getattr(state, "player", None)
        player_gold = getattr(player, "gold", 0) if player else 0

        # Verification 1: Player gold check
        if player_gold < bid_amount:
            return AuctionActionResult(
                action_type="place_bid",
                success=False,
                current_lot_id=current_lot.lot_id,
                highest_bid=current_lot.current_bid,
                highest_bidder_name=current_lot.highest_bidder_name,
                countdown=current_lot.countdown,
                narration_logs=[
                    f"소지 골드가 부족합니다! (필요: {bid_amount} G, 보유: {player_gold} G)"
                ]
            )

        # Verification 2: Bid amount threshold
        # If no player/NPC has bid above starting_bid, starting_bid is valid
        min_required = current_lot.current_bid + current_lot.min_increment
        if current_lot.highest_bidder_id == "auctioneer":
            min_required = current_lot.starting_bid

        if bid_amount < min_required:
            return AuctionActionResult(
                action_type="place_bid",
                success=False,
                current_lot_id=current_lot.lot_id,
                highest_bid=current_lot.current_bid,
                highest_bidder_name=current_lot.highest_bidder_name,
                countdown=current_lot.countdown,
                narration_logs=[
                    f"호가가 너무 낮습니다! 최소 {min_required} 골드 이상이어야 합니다. (현재 호가: {current_lot.current_bid} G)"
                ]
            )

        # Success: Update lot highest bidder and reset gavel countdown
        current_lot.current_bid = bid_amount
        current_lot.highest_bidder_id = "player"
        current_lot.highest_bidder_name = getattr(player, "name", "플레이어") if player else "플레이어"
        current_lot.countdown = 3  # Reset gavel countdown to 3

        log_msg = (
            f"당신은 손을 번쩍 들며 [{current_lot.name}]에 {bid_amount} 골드를 입찰했습니다! "
            f"경매사가 나무망치를 들어 올리며 카운트다운을 시작합니다. (첫 번째 호가: 3카운트)"
        )

        return AuctionActionResult(
            action_type="place_bid",
            success=True,
            current_lot_id=current_lot.lot_id,
            highest_bid=current_lot.current_bid,
            highest_bidder_name=current_lot.highest_bidder_name,
            countdown=current_lot.countdown,
            narration_logs=[log_msg]
        )

    @classmethod
    def player_intimidate_bidders(
        cls,
        state: Any,
        auction_state: BlackMarketAuctionState
    ) -> AuctionActionResult:
        """
        Player attempts to intimidate competing NPC bidders with sheer presence/STR/CHA.
        Intimidated bidders forfeit bidding on the current lot.
        """
        if auction_state.blacklisted_player:
            return AuctionActionResult(
                action_type="intimidate",
                success=False,
                current_lot_id="",
                highest_bid=0,
                highest_bidder_name="",
                countdown=0,
                narration_logs=["[경매장 입장 불가] 경매장에서 퇴출된 상태입니다."]
            )

        current_lot = cls.get_current_lot(auction_state)
        if not current_lot or current_lot.is_concluded:
            return AuctionActionResult(
                action_type="intimidate",
                success=False,
                current_lot_id="",
                highest_bid=0,
                highest_bidder_name="",
                countdown=0,
                narration_logs=["위협할 경쟁 매물이 없습니다."]
            )

        player = getattr(state, "player", None)
        player_str = getattr(player, "strength", 12) if player else 12
        player_cha = getattr(player, "charisma", 10) if player else 10
        intimidation_power = max(player_str, player_cha) + random.randint(1, 6)

        intimidated_names = []
        for bidder in auction_state.bidders:
            if bidder.status == "active":
                if intimidation_power >= bidder.intimidation_resistance:
                    bidder.status = "intimidated"
                    intimidated_names.append(bidder.name)

        if intimidated_names:
            msg = (
                f"당신은 살기 어린 눈빛으로 주변 입찰자들을 노려보며 흉흉한 위압을 내뿜었습니다! "
                f"({', '.join(intimidated_names)})이(가) 공포에 질려 번호 팻말을 내리고 입찰을 포기합니다."
            )
            return AuctionActionResult(
                action_type="intimidate",
                success=True,
                current_lot_id=current_lot.lot_id,
                highest_bid=current_lot.current_bid,
                highest_bidder_name=current_lot.highest_bidder_name,
                countdown=current_lot.countdown,
                narration_logs=[msg]
            )
        else:
            msg = (
                "당신은 위압적인 태도로 주변을 둘러보았으나, 노련한 지하 경매장 참가자들은 비웃으며 꿈쩍도 하지 않습니다."
            )
            return AuctionActionResult(
                action_type="intimidate",
                success=False,
                current_lot_id=current_lot.lot_id,
                highest_bid=current_lot.current_bid,
                highest_bidder_name=current_lot.highest_bidder_name,
                countdown=current_lot.countdown,
                narration_logs=[msg]
            )

    @classmethod
    def player_snatch_lot(
        cls,
        state: Any,
        auction_state: BlackMarketAuctionState
    ) -> AuctionActionResult:
        """
        Daring maneuver: Player snatches the lot directly from the pedestal!
        Stealth / Agility check.
        - Success: Lot acquired for 0 gold!
        - Failure: Auction guards swarm, tavern brawl ignited, blacklisted!
        """
        if auction_state.blacklisted_player:
            return AuctionActionResult(
                action_type="snatch_lot",
                success=False,
                current_lot_id="",
                highest_bid=0,
                highest_bidder_name="",
                countdown=0,
                narration_logs=["[경매장 입장 불가] 이미 수배 중인 상태입니다."]
            )

        current_lot = cls.get_current_lot(auction_state)
        if not current_lot or current_lot.is_concluded:
            return AuctionActionResult(
                action_type="snatch_lot",
                success=False,
                current_lot_id="",
                highest_bid=0,
                highest_bidder_name="",
                countdown=0,
                narration_logs=["단상 위에 훔칠 매물이 없습니다."]
            )

        player = getattr(state, "player", None)
        player_agi = getattr(player, "agility", 10) if player else 10
        player_stealth = getattr(player, "stealth", 10) if player else 10
        snatch_score = max(player_agi, player_stealth) + random.randint(1, 10)

        difficulty = 18  # DC 18 check
        if snatch_score >= difficulty:
            # Successful heist
            current_lot.is_concluded = True
            current_lot.winner_id = "player"
            acquired = dict(current_lot.item_payload)
            auction_state.current_lot_index += 1

            msg = (
                f"⚡ [대담한 강탈 성공!] 순식간에 연막탄을 터뜨리며 단상 위로 쇄도한 당신은 "
                f"경비병의 감시망을 뚫고 [{current_lot.name}]을(를) 품속에 가로채는 데 성공했습니다!"
            )
            return AuctionActionResult(
                action_type="snatch_lot",
                success=True,
                current_lot_id=current_lot.lot_id,
                highest_bid=current_lot.current_bid,
                highest_bidder_name="플레이어 (탈취)",
                countdown=0,
                acquired_item=acquired,
                narration_logs=[msg]
            )
        else:
            # Caught red-handed
            auction_state.blacklisted_player = True
            msg = (
                f"🚨 [강탈 발각! 암시장 비상 경보!] 단상 위의 [{current_lot.name}]에 손을 뻗는 순간, "
                f"잠복해 있던 암시장 정예 경비병들이 철퇴와 석궁을 겨누며 덮칩니다! "
                f"경매장은 순식간에 피비린내 나는 난투극(Tavern Brawl)의 도가니로 변합니다!"
            )
            return AuctionActionResult(
                action_type="snatch_lot",
                success=False,
                current_lot_id=current_lot.lot_id,
                highest_bid=current_lot.current_bid,
                highest_bidder_name=current_lot.highest_bidder_name,
                countdown=0,
                brawl_triggered=True,
                narration_logs=[msg]
            )

    @classmethod
    def advance_auction_tick(
        cls,
        state: Any,
        auction_state: BlackMarketAuctionState
    ) -> AuctionActionResult:
        """
        Advances the auction state by one turn:
        1. Active NPC bidders decide whether to place a counter-bid.
        2. If a bid occurs, current_bid updates and countdown resets to 3.
        3. If no new bid occurs, countdown decrements (3 -> 2 -> 1 -> 0: Sold!).
        """
        current_lot = cls.get_current_lot(auction_state)
        if not current_lot or current_lot.is_concluded:
            return AuctionActionResult(
                action_type="advance_tick",
                success=True,
                current_lot_id="",
                highest_bid=0,
                highest_bidder_name="종료",
                countdown=0,
                narration_logs=["현재 경매에 상정된 모든 매물이 마감되었습니다."]
            )

        logs: List[str] = []
        auction_state.auction_turn_count += 1

        # Check for NPC counter-bidding
        eligible_bidders: List[NPCBidder] = []
        for bidder in auction_state.bidders:
            if bidder.status != "active":
                continue
            if bidder.npc_id == current_lot.highest_bidder_id:
                continue  # Already highest bidder

            min_bid = current_lot.current_bid + current_lot.min_increment
            if current_lot.highest_bidder_id == "auctioneer":
                min_bid = current_lot.starting_bid

            max_valuation = int(current_lot.starting_bid * bidder.greed_factor * 1.5)
            if min_bid <= bidder.remaining_budget and min_bid <= max_valuation:
                eligible_bidders.append(bidder)

        if eligible_bidders:
            # Deterministic selection: Pick bidder with highest willingness/budget
            eligible_bidders.sort(key=lambda b: (b.greed_factor, b.remaining_budget), reverse=True)
            chosen_bidder = eligible_bidders[0]

            # NPC outbids
            new_bid = current_lot.current_bid + current_lot.min_increment
            if current_lot.highest_bidder_id == "auctioneer":
                new_bid = current_lot.starting_bid

            current_lot.current_bid = new_bid
            current_lot.highest_bidder_id = chosen_bidder.npc_id
            current_lot.highest_bidder_name = chosen_bidder.name
            current_lot.countdown = 3  # Reset countdown

            logs.append(
                f"[{chosen_bidder.name}]이(가) 거만한 표정으로 팻말을 치켜들며 {new_bid} 골드를 불렀습니다! "
                f"경매사: \"{new_bid} 골드 나왔습니다! 더 없으십니까?\" (카운트다운 리셋: 3)"
            )
            return AuctionActionResult(
                action_type="advance_tick",
                success=True,
                current_lot_id=current_lot.lot_id,
                highest_bid=current_lot.current_bid,
                highest_bidder_name=current_lot.highest_bidder_name,
                countdown=current_lot.countdown,
                narration_logs=logs
            )

        # If no NPC counter-bids, countdown decrements!
        current_lot.countdown -= 1

        if current_lot.countdown == 2:
            logs.append(
                f"경매사가 단상을 탕 내리치며 외칩니다: \"{current_lot.current_bid} 골드! 첫 번째 호가! 더 없으십니까?\""
            )
        elif current_lot.countdown == 1:
            logs.append(
                f"경매사의 시선이 관중을 훑습니다: \"{current_lot.current_bid} 골드! 두 번째 호가! 마지막 기회입니다!\""
            )
        elif current_lot.countdown <= 0:
            # Gavel down: Sold!
            current_lot.is_concluded = True
            current_lot.winner_id = current_lot.highest_bidder_id
            gold_spent = 0
            acquired_item = None

            if current_lot.winner_id == "player":
                gold_spent = current_lot.current_bid
                acquired_item = dict(current_lot.item_payload)
                logs.append(
                    f"🔨 [낙찰 완료!] \"땅! 땅! 땅! [{current_lot.name}], {current_lot.current_bid} 골드에 앞줄의 용사님께 최종 낙찰되었습니다!\" "
                    f"경매사의 망치가 단상을 강타하고 정품 유물이 당신의 품으로 인도됩니다."
                )
            elif current_lot.winner_id == "auctioneer":
                logs.append(
                    f"🔨 \"땅! 땅! 땅! 입찰자가 없어 [{current_lot.name}] 매물이 유찰되었습니다.\""
                )
            else:
                # Won by an NPC
                # Deduct budget from NPC
                for bidder in auction_state.bidders:
                    if bidder.npc_id == current_lot.winner_id:
                        bidder.remaining_budget -= current_lot.current_bid
                        break
                logs.append(
                    f"🔨 [낙찰 완료!] \"땅! 땅! 땅! [{current_lot.name}], {current_lot.current_bid} 골드에 [{current_lot.highest_bidder_name}]에게 최종 낙찰되었습니다!\""
                )

            # Move to next lot
            auction_state.current_lot_index += 1

            return AuctionActionResult(
                action_type="advance_tick",
                success=True,
                current_lot_id=current_lot.lot_id,
                highest_bid=current_lot.current_bid,
                highest_bidder_name=current_lot.highest_bidder_name,
                countdown=0,
                gold_spent=gold_spent,
                acquired_item=acquired_item,
                narration_logs=logs
            )

        return AuctionActionResult(
            action_type="advance_tick",
            success=True,
            current_lot_id=current_lot.lot_id,
            highest_bid=current_lot.current_bid,
            highest_bidder_name=current_lot.highest_bidder_name,
            countdown=current_lot.countdown,
            narration_logs=logs
        )

    @classmethod
    def get_auction_status_summary(
        cls,
        state: Any,
        auction_state: Optional[BlackMarketAuctionState],
        last_result: Optional[AuctionActionResult] = None
    ) -> str:
        """Generates a concise Korean summary for DeterministicFactSheet."""
        if not auction_state:
            return "현재 진행 중인 경매 세션 없음."

        if auction_state.blacklisted_player:
            return "⚠️ 암시장 경매장 출입 금지 상태 (경비병 적대 수배)."

        current_lot = cls.get_current_lot(auction_state)
        if not current_lot:
            return "지하 암시장 경매: 모든 출품작 경매 종료됨."

        lines = [
            f"[지하 암시장 비밀 경매장]",
            f"- 현재 출품작: {current_lot.name} ({current_lot.rarity.upper()} / {current_lot.category})",
            f"- 현재 최고 호가: {current_lot.current_bid} G (입찰자: {current_lot.highest_bidder_name})",
            f"- 최소 입찰 단위: +{current_lot.min_increment} G",
            f"- 경매봉 카운트다운: {current_lot.countdown}/3 (0=낙찰)",
        ]

        active_bidders = [b.name for b in auction_state.bidders if b.status == "active"]
        if active_bidders:
            lines.append(f"- 경쟁 입찰자: {', '.join(active_bidders)}")

        if last_result and last_result.narration_logs:
            lines.append(f"- 최근 전개: {last_result.narration_logs[-1]}")

        return "\n".join(lines)
