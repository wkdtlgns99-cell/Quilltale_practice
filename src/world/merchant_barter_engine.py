"""
Deterministic Regional Arbitrage, Barter, Smuggling & Financial Mechanics Engine.
Features:
1. 10 Terrain Economic Multipliers (Salt, Water, Firewood, Ore, etc. 0.3x ~ 5.0x).
2. Safe Fallback for Unknown Terrains (1.0x standard baseline).
3. Barter Exchange Rate Calculation with Charisma/Persuasion DC checks.
4. Contraband Tier & Checkpoint Smuggling Inspection (Stealth vs Guard Perception).
5. Black Market Multipliers (Tier 1: 3x, Tier 2: 10x).
6. Merchant Credit Ledger & Loan Enforcer Ambush on Default.
7. Unidentified Relic Appraisal (10G unappraised vs true artifact value).
8. Coin Clipping & Counterfeit Fraud (Gold dust skimming vs Merchant Scale Perception).
"""
from enum import IntEnum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import math

from src.world.dice import DiceEngine


class ContrabandTier(IntEnum):
    LEGAL = 0           # Standard items (food, regular weapons, tools)
    RESTRICTED = 1      # Military arms, unregistered poisons, poached beast hides (3x in black market, confiscated)
    ILLICIT = 2         # Darkweed narcotics, demonic idols, stolen imperial seals (10x in black market, arrest & 500G bounty)


# 10 Terrain Economic Matrix
# Multipliers applied to base item prices based on local abundance / scarcity.
TERRAIN_PRICE_MULTIPLIERS: Dict[str, Dict[str, float]] = {
    "coastal_port": {
        "salt": 0.5, "fish": 0.5, "pearls": 0.6,
        "ore": 2.0, "wood": 1.8, "coal": 1.7, "firewood": 1.5,
    },
    "mountain_mine": {
        "ore": 0.4, "coal": 0.4, "stone": 0.3,
        "salt": 3.5, "grain": 2.5, "fish": 3.0, "clean_water": 1.8,
    },
    "plains_farm": {
        "grain": 0.4, "vegetables": 0.4, "meat": 0.5, "cheese": 0.5,
        "gems": 2.2, "spices": 2.0, "ore": 1.8, "salt": 1.5,
    },
    "dense_forest": {
        "wood": 0.4, "herbs": 0.4, "fur": 0.5, "venison": 0.5,
        "ore": 2.0, "metal_goods": 2.2, "luxury_clothes": 2.0,
    },
    "frozen_tundra": {
        "fur": 0.4, "ice_fish": 0.5, "whale_oil": 0.6,
        "firewood": 4.0, "clean_water": 3.0, "vegetables": 3.5, "grain": 3.0,
    },
    "volcanic_ridge": {
        "sulfur": 0.3, "obsidian": 0.3, "fire_crystal": 0.4,
        "clean_water": 5.0, "herbs": 3.0, "vegetables": 3.0, "ice": 4.5,
    },
    "subterranean": {
        "glowing_mushrooms": 0.4, "gems": 0.5, "bat_guano": 0.4,
        "grain": 4.0, "firewood": 3.5, "clean_water": 2.0, "torches": 3.0,
    },
    "desert_oasis": {
        "dates": 0.4, "sand_glass": 0.5, "camel_hide": 0.6,
        "clean_water": 4.0, "fur": 3.0, "firewood": 2.8, "vegetables": 2.5,
    },
    "toxic_swamp": {
        "antidote": 0.4, "herbs": 0.5, "leech_oil": 0.4,
        "clean_water": 2.5, "metal_goods": 2.0, "bandages": 2.2,
    },
    "capital_metropolis": {
        "magic_scrolls": 0.7, "luxury_clothes": 0.6, "potions": 0.8,
        "wood": 1.8, "ore": 1.8, "coal": 1.6, "raw_materials": 1.5,
    },
}


@dataclass
class DebtLedgerEntry:
    shop_id: str
    principal: int
    interest_rate: float
    total_due: int
    due_turn: int
    defaulted: bool = False


class MerchantBarterEngine:
    """Pure Python Deterministic Trade, Barter, Smuggling & Financial Engine."""

    @classmethod
    def get_regional_price(cls, category: str, base_price: int, terrain: str) -> int:
        """
        Calculates local item price adjusted by terrain abundance/scarcity.
        Safe fallback to 1.0x if terrain or category is unrecognized.
        """
        if base_price <= 0:
            return 1

        normalized_terrain = terrain.strip().lower()
        normalized_cat = category.strip().lower()

        terrain_rules = TERRAIN_PRICE_MULTIPLIERS.get(normalized_terrain, {})
        multiplier = terrain_rules.get(normalized_cat, 1.0)

        final_price = max(1, int(math.ceil(base_price * multiplier)))
        return final_price

    @classmethod
    def calculate_barter_exchange(
        cls,
        offered_item_values: List[int],
        wanted_item_values: List[int],
        persuasion_roll: int,
        terrain: str = "plains_farm"
    ) -> Dict[str, Any]:
        """
        Calculates barter item swap.
        Persuasion check modifies player's offered valuation:
        - Critical (roll >= 18): 1.25x value (+25% favored trade)
        - Success (roll >= 12): 1.0x fair trade
        - Failure (roll < 12): 0.8x markdown (merchant drives hard bargain)
        """
        raw_offered_total = sum(offered_item_values)
        wanted_total = sum(wanted_item_values)

        if persuasion_roll >= 18:
            rate = 1.25
            crit_status = "대성공 (25% 우대 환율)"
        elif persuasion_roll >= 12:
            rate = 1.0
            crit_status = "성공 (공정 거래)"
        else:
            rate = 0.8
            crit_status = "실패 (상인의 20% 후려치기)"

        effective_offered_total = int(raw_offered_total * rate)
        diff = effective_offered_total - wanted_total

        is_possible = effective_offered_total >= wanted_total
        change_due = max(0, diff) if is_possible else 0
        shortfall = max(0, -diff) if not is_possible else 0

        return {
            "is_possible": is_possible,
            "raw_offered_total": raw_offered_total,
            "effective_offered_total": effective_offered_total,
            "wanted_total": wanted_total,
            "valuation_rate": rate,
            "bargain_status": crit_status,
            "change_gold_due": change_due,
            "shortfall_gold": shortfall,
            "summary_ko": (
                f"물물교환 성립: 플레이어 제공치 {effective_offered_total}G vs 상인 요구치 {wanted_total}G "
                f"({crit_status}, 거스름돈: {change_due}G)" if is_possible else
                f"물물교환 결렬: {shortfall}G 가치 부족 ({crit_status})"
            )
        }

    @classmethod
    def check_smuggling_checkpoint(
        cls,
        contraband_items: List[Dict[str, Any]],
        guard_perception: int = 12,
        player_stealth_mod: int = 0
    ) -> Dict[str, Any]:
        """
        Resolves gate guards inspecting for contraband.
        DC = 10 + guard_perception_mod + (highest_tier * 3)
        """
        if not contraband_items:
            return {
                "passed": True,
                "confiscated_items": [],
                "bounty_added": 0,
                "summary_ko": "검문 통과: 소지한 금지품이 없습니다."
            }

        highest_tier = max(item.get("contraband_tier", 0) for item in contraband_items)
        if highest_tier == ContrabandTier.LEGAL:
            return {
                "passed": True,
                "confiscated_items": [],
                "bounty_added": 0,
                "summary_ko": "검문 통과: 합법적인 물품들입니다."
            }

        guard_mod = (guard_perception - 10) // 2
        dc = 10 + guard_mod + (int(highest_tier) * 3)

        roll = DiceEngine.roll_d20()
        total = roll + player_stealth_mod
        passed = total >= dc

        if passed:
            return {
                "passed": True,
                "dice_roll": total,
                "dc": dc,
                "confiscated_items": [],
                "bounty_added": 0,
                "summary_ko": f"은신 검문 통과 (판정 {total} vs DC {dc}): 경비병의 눈을 속이고 밀수에 성공했습니다!"
            }
        else:
            bounty = 100 if highest_tier == ContrabandTier.RESTRICTED else 500
            confiscated = [i.get("name_ko", i.get("id", "아이템")) for i in contraband_items if i.get("contraband_tier", 0) > 0]
            return {
                "passed": False,
                "dice_roll": total,
                "dc": dc,
                "confiscated_items": confiscated,
                "bounty_added": bounty,
                "summary_ko": f"밀수 발각 (판정 {total} vs DC {dc}): 금지품 전량 압수 및 수배령 (+{bounty}G 현상금)!"
            }

    @classmethod
    def sell_to_black_market(cls, base_price: int, contraband_tier: int) -> int:
        """Calculates black market premium prices."""
        if contraband_tier == ContrabandTier.ILLICIT:
            return base_price * 10
        elif contraband_tier == ContrabandTier.RESTRICTED:
            return base_price * 3
        return max(1, int(base_price * 0.5))

    @classmethod
    def record_merchant_debt(
        cls,
        shop_id: str,
        principal: int,
        current_turn: int,
        duration_turns: int = 30,
        interest_rate: float = 0.20
    ) -> DebtLedgerEntry:
        """Records credit purchase into ledger."""
        total_due = int(principal * (1.0 + interest_rate))
        return DebtLedgerEntry(
            shop_id=shop_id,
            principal=principal,
            interest_rate=interest_rate,
            total_due=total_due,
            due_turn=current_turn + duration_turns,
            defaulted=False
        )

    @classmethod
    def check_debt_default(cls, entry: DebtLedgerEntry, current_turn: int) -> Dict[str, Any]:
        """Checks if loan has defaulted and triggers debt collection enforcer ambush."""
        if current_turn > entry.due_turn and not entry.defaulted:
            entry.defaulted = True
            overdue_penalty = int(entry.total_due * 0.5)
            entry.total_due += overdue_penalty
            return {
                "defaulted": True,
                "trigger_enforcer_ambush": True,
                "total_due": entry.total_due,
                "summary_ko": f"⚠️ 외상 변제 기한 초과! 원리금 {entry.total_due}G로 폭등. 상인이 해결사 깡패를 보냈습니다!"
            }
        return {
            "defaulted": entry.defaulted,
            "trigger_enforcer_ambush": False,
            "total_due": entry.total_due,
            "summary_ko": f"외상 정상 유지 중 (납기 {entry.due_turn}턴 / 잔여 {entry.due_turn - current_turn}턴)"
        }

    @classmethod
    def appraise_unidentified_item(
        cls,
        raw_name: str,
        true_name: str,
        true_price: int,
        fee_paid: int,
        required_fee: int = 30,
        is_cursed: bool = False
    ) -> Dict[str, Any]:
        """Resolves appraisal of unidentified relics/artifacts."""
        if fee_paid < required_fee:
            return {
                "success": False,
                "revealed_name": raw_name,
                "price": 10,
                "is_cursed": False,
                "summary_ko": f"감정 거부: 수수료 {required_fee}G가 부족합니다 (지불액: {fee_paid}G)."
            }

        return {
            "success": True,
            "revealed_name": true_name,
            "price": true_price,
            "is_cursed": is_cursed,
            "summary_ko": (
                f"감정 성공: 흙 묻은 쇠붙이의 정체는 [{true_name}](가치 {true_price}G)입니다!"
                if not is_cursed else
                f"⚠️ 감정 성공: [{true_name}](가치 {true_price}G)은 사악한 원혼이 깃든 [저주받은 유물]입니다!"
            )
        }

    @classmethod
    def attempt_coin_clipping(
        cls,
        payment_amount: int,
        merchant_perception: int = 12,
        player_sleight_mod: int = 0
    ) -> Dict[str, Any]:
        """
        Attempts to clip edges of gold coins for gold dust shavings.
        Skims 15% gold value.
        """
        skimmed_dust_value = max(1, int(payment_amount * 0.15))
        merchant_mod = (merchant_perception - 10) // 2
        dc = 12 + merchant_mod

        roll = DiceEngine.roll_d20()
        total = roll + player_sleight_mod
        success = total >= dc

        if success:
            return {
                "success": True,
                "gold_dust_value": skimmed_dust_value,
                "bounty_added": 0,
                "summary_ko": f"금화 깎기 성공 (판정 {total} vs DC {dc}): 상인 몰래 {skimmed_dust_value}G 상당의 금가루를 깎아냈습니다!"
            }
        else:
            return {
                "success": False,
                "gold_dust_value": 0,
                "bounty_added": 150,
                "summary_ko": f"사기 들통 (판정 {total} vs DC {dc}): 상인이 저울 무게 미달을 알아채고 경비병을 부릅니다 (+150G 사기죄 현상금)!"
            }
