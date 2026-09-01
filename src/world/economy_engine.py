"""
Deterministic Economy & Shop Trading Engine for Quilltale TRPG Engine.
Manages merchant inventories, stock replenishment, item unlocking, buying/selling pricing,
haggling skill checks, and unique merchant services (repair, potion brewing, poison removal, rumors).
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
import copy

from src.core.config import TEMPLATES_DIR
from src.world.dice import DiceEngine


@dataclass
class ShopItem:
    item_id: str
    name_ko: str
    category: str                           # "weapon" | "armor" | "consumable" | "material" | "spell_tome" | "relic"
    item_tier: str = "common"               # "common" | "uncommon" | "rare" | "unique" | "cursed"
    stock: int = 1
    max_stock: int = 1
    price: int = 10
    description_ko: str = ""
    unlock_conditions: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "name_ko": self.name_ko,
            "category": self.category,
            "item_tier": self.item_tier,
            "stock": self.stock,
            "max_stock": self.max_stock,
            "price": self.price,
            "description_ko": self.description_ko,
            "unlock_conditions": self.unlock_conditions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ShopItem":
        return cls(
            item_id=str(data.get("item_id", "")),
            name_ko=str(data.get("name_ko", "")),
            category=str(data.get("category", "misc")),
            item_tier=str(data.get("item_tier", "common")),
            stock=int(data.get("stock", 1)),
            max_stock=int(data.get("max_stock", 1)),
            price=int(data.get("price", 10)),
            description_ko=str(data.get("description_ko", "")),
            unlock_conditions=dict(data.get("unlock_conditions", {})),
        )


@dataclass
class Shop:
    shop_id: str
    shop_name: str
    npc_id: str = ""
    location_id: str = ""
    shop_type: str = "general"               # "general" | "blacksmith" | "apothecary" | "magic_emporium" | "black_market" | "tavern" | "wandering_merchant"
    buy_rate: float = 1.3                   # player purchase markup
    sell_rate: float = 0.5                  # player sale markdown
    haggling_allowed: bool = True
    restock_interval_turns: int = 30
    merchant_gold: int = 1000
    services: Dict[str, Any] = field(default_factory=dict)
    dialogue: Dict[str, str] = field(default_factory=dict)
    inventory: List[ShopItem] = field(default_factory=list)
    turns_since_restock: int = 0

    def to_dict(self) -> dict:
        return {
            "shop_id": self.shop_id,
            "shop_name": self.shop_name,
            "npc_id": self.npc_id,
            "location_id": self.location_id,
            "shop_type": self.shop_type,
            "buy_rate": self.buy_rate,
            "sell_rate": self.sell_rate,
            "haggling_allowed": self.haggling_allowed,
            "restock_interval_turns": self.restock_interval_turns,
            "merchant_gold": self.merchant_gold,
            "services": self.services,
            "dialogue": self.dialogue,
            "inventory": [i.to_dict() for i in self.inventory],
            "turns_since_restock": self.turns_since_restock,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Shop":
        items = [ShopItem.from_dict(i) for i in data.get("inventory", []) if isinstance(i, dict)]
        return cls(
            shop_id=str(data.get("shop_id", "")),
            shop_name=str(data.get("shop_name", "")),
            npc_id=str(data.get("npc_id", "")),
            location_id=str(data.get("location_id", "")),
            shop_type=str(data.get("shop_type", "general")),
            buy_rate=float(data.get("buy_rate", 1.3)),
            sell_rate=float(data.get("sell_rate", 0.5)),
            haggling_allowed=bool(data.get("haggling_allowed", True)),
            restock_interval_turns=int(data.get("restock_interval_turns", 30)),
            merchant_gold=int(data.get("merchant_gold", 1000)),
            services=dict(data.get("services", {})),
            dialogue=dict(data.get("dialogue", {})),
            inventory=items,
            turns_since_restock=int(data.get("turns_since_restock", 0)),
        )


class EconomyEngine:
    """
    Pure Python Deterministic Trading & Shop Engine.
    Handles buying, selling, haggling, service execution, and restock.
    """

    _templates_cache: Optional[Dict[str, Shop]] = None

    @classmethod
    def load_templates(cls, path: Optional[Path] = None) -> Dict[str, Shop]:
        """Loads and caches all shop definitions from shop_templates.json."""
        target_path = path or (TEMPLATES_DIR / "shop_templates.json")
        if not target_path.exists():
            return {}

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                raw_list = json.load(f)
            shops = {}
            for s_data in raw_list:
                s = Shop.from_dict(s_data)
                if s.shop_id:
                    shops[s.shop_id] = s
            cls._templates_cache = shops
            return shops
        except Exception:
            return {}

    @classmethod
    def get_shop_template(cls, shop_id: str) -> Optional[Shop]:
        if cls._templates_cache is None:
            cls.load_templates()
        if cls._templates_cache and shop_id in cls._templates_cache:
            return copy.deepcopy(cls._templates_cache[shop_id])
        return None

    @classmethod
    def get_active_shop(cls, state: Any, location_id: Optional[str] = None, npc_id: Optional[str] = None) -> Optional[Shop]:
        """Finds or instantiates a shop for the player's current location or interacting NPC."""
        if not hasattr(state, "shops"):
            state.shops = {}

        if cls._templates_cache is None:
            cls.load_templates()

        loc_id = location_id or state.player.location
        curr_loc = state.locations.get(loc_id)
        present_npcs = curr_loc.npcs if curr_loc else []

        # 1. Search in existing active state shops
        for s in state.shops.values():
            if (s.location_id == loc_id) or (npc_id and s.npc_id == npc_id) or (s.npc_id and s.npc_id in present_npcs):
                return s

        # 2. Look in template definitions
        for tmpl_id, tmpl in (cls._templates_cache or {}).items():
            matches_npc = (npc_id and tmpl.npc_id == npc_id) or (tmpl.npc_id and tmpl.npc_id in present_npcs)
            matches_loc = (tmpl.location_id == loc_id)
            if matches_npc or matches_loc:
                shop_inst = copy.deepcopy(tmpl)
                state.shops[shop_inst.shop_id] = shop_inst
                return shop_inst

        # Default fallback shop if tavern or merchant NPC is present
        if present_npcs and not state.shops:
            for s_id, tmpl in (cls._templates_cache or {}).items():
                shop_inst = copy.deepcopy(tmpl)
                shop_inst.location_id = loc_id
                state.shops[shop_inst.shop_id] = shop_inst
                return shop_inst

        return None

    @classmethod
    def check_item_unlock(cls, item: ShopItem, state: Any) -> Tuple[bool, str]:
        """Checks if player meets prerequisites to view and buy an item."""
        cond = item.unlock_conditions
        if not cond:
            return True, "구매 가능"

        player = state.player

        # 1. Level condition
        if "level_min" in cond and player.level < cond["level_min"]:
            return False, f"요구 레벨 미달 (필요: Lv.{cond['level_min']})"

        # 2. Reputation condition
        if "reputation_min" in cond and player.reputation < cond["reputation_min"]:
            return False, f"요구 평판 미달 (필요: {cond['reputation_min']})"
        if "reputation_max" in cond and player.reputation > cond["reputation_max"]:
            return False, f"악명/비밀 조건 (평판 {cond['reputation_max']} 이하 필요)"

        # 3. Stat condition
        if "stats" in cond:
            for stat_name, min_val in cond["stats"].items():
                stat_lower = stat_name.lower()
                p_val = 10
                if stat_lower in ["str", "strength"]:
                    p_val = getattr(player, "effective_strength", player.strength)
                elif stat_lower in ["dex", "agi", "agility"]:
                    p_val = getattr(player, "effective_agility", player.agility)
                elif stat_lower in ["int", "intelligence"]:
                    p_val = getattr(player, "effective_intelligence", player.intelligence)
                elif stat_lower in ["wis", "wisdom"]:
                    p_val = player.wisdom
                elif stat_lower in ["cha", "luk", "luck"]:
                    p_val = player.luck

                if p_val < min_val:
                    return False, f"스탯 부족 ({stat_name} {min_val} 이상 필요)"

        # 4. Quest condition
        if "completed_quest_id" in cond:
            q_id = cond["completed_quest_id"]
            if not hasattr(state, "quests") or q_id not in state.quests or state.quests[q_id].status != "completed":
                return False, "특정 퀘스트 완료 후 해금"

        return True, "구매 가능"

    @classmethod
    def calculate_buy_price(cls, shop: Shop, item: ShopItem, state: Any, is_haggled: bool = False) -> int:
        """Calculates final purchase price for the player."""
        base_price = item.price
        multiplier = shop.buy_rate
        if is_haggled:
            multiplier *= 0.85  # 15% haggling discount
        return max(1, int(base_price * multiplier))

    @classmethod
    def calculate_sell_price(cls, shop: Shop, item_value: int, state: Any, is_haggled: bool = False) -> int:
        """Calculates gold received when player sells an item to merchant."""
        multiplier = shop.sell_rate
        if is_haggled:
            multiplier *= 1.15  # 15% haggling bonus
        return max(1, int(item_value * multiplier))

    @classmethod
    def perform_haggle(cls, state: Any, shop: Shop) -> Tuple[bool, str, float]:
        """
        Rolls deterministic d20 + luck modifier check vs DC 13.
        Returns (success, dialogue, price_multiplier).
        """
        if not shop.haggling_allowed:
            return False, shop.dialogue.get("haggling_fail", "흥정은 받지 않습니다."), 1.0

        player = state.player
        check_res = DiceEngine.perform_check(
            action_type="흥정",
            stat_value=player.luck,
            dc=13,
        )

        if check_res.is_success:
            msg = shop.dialogue.get("haggling_success", "좋아, 이번만 특별히 깎아주지.")
            return True, f"🎲 [흥정 성공: {check_res.summary_ko}] {msg}", 0.85
        else:
            msg = shop.dialogue.get("haggling_fail", "제값 안 낼 거면 다른 데 알아보게.")
            return False, f"🎲 [흥정 실패: {check_res.summary_ko}] {msg}", 1.0

    @classmethod
    def buy_item(
        cls,
        state: Any,
        shop_id: str,
        item_id: str,
        count: int = 1,
        is_haggled: bool = False,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Player purchases an item from shop.
        Deducts player gold, reduces shop stock, adds item to player inventory.
        """
        if not hasattr(state, "shops") or shop_id not in state.shops:
            shop = cls.get_shop_template(shop_id)
            if shop:
                state.shops[shop_id] = shop
            else:
                return False, "상점을 찾을 수 없습니다.", {}

        shop = state.shops[shop_id]
        shop_item = next((i for i in shop.inventory if i.item_id == item_id), None)
        if not shop_item:
            return False, f"상점에 [{item_id}] 상품이 없습니다.", {}

        # Check unlock conditions
        unlocked, reason = cls.check_item_unlock(shop_item, state)
        if not unlocked:
            return False, f"구매 불가: {reason}", {}

        # Check stock
        if shop_item.stock != -1 and shop_item.stock < count:
            return False, f"재고 부족 (현재 재고: {shop_item.stock}개)", {}

        # Check price & gold
        unit_price = cls.calculate_buy_price(shop, shop_item, state, is_haggled=is_haggled)
        total_price = unit_price * count

        if state.player.gold < total_price:
            no_gold_msg = shop.dialogue.get("no_gold", "골드가 부족합니다.")
            return False, f"골드 부족 (필요: {total_price}G, 보유: {state.player.gold}G) — {no_gold_msg}", {}

        # Process Transaction
        state.player.gold -= total_price
        if shop.merchant_gold != -1:
            shop.merchant_gold += total_price

        if shop_item.stock != -1:
            shop_item.stock -= count

        # Add to player inventory
        from src.world.state import Item
        for _ in range(count):
            if item_id in state.items:
                state.player.inventory.append(item_id)
            else:
                new_item = Item(
                    id=item_id,
                    name=shop_item.name_ko,
                    description=shop_item.description_ko,
                    item_type=shop_item.category,
                    value=shop_item.price,
                    location="inventory",
                )
                state.items[item_id] = new_item
                state.player.inventory.append(item_id)

        # Hook: Quest progress for item collection
        from src.world.quest_engine import QuestEngine
        q_logs = QuestEngine.progress_event(state, "collect", item_id, count)

        msg = f"🛒 **[구매 완료]** [{shop_item.name_ko}] {count}개를 {total_price}G에 구매했습니다. (남은 골드: {state.player.gold}G)"
        if q_logs:
            msg += "\n" + "\n".join(q_logs)

        return True, msg, {"item_id": item_id, "cost": total_price, "count": count}

    @classmethod
    def sell_item(
        cls,
        state: Any,
        shop_id: str,
        item_id: str,
        count: int = 1,
        is_haggled: bool = False,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Player sells an item from inventory to merchant.
        """
        if not hasattr(state, "shops") or shop_id not in state.shops:
            shop = cls.get_shop_template(shop_id)
            if shop:
                state.shops[shop_id] = shop
            else:
                return False, "상점을 찾을 수 없습니다.", {}

        shop = state.shops[shop_id]
        player_items = [i for i in state.player.inventory if i == item_id]
        if len(player_items) < count:
            return False, f"가방에 해당 아이템이 부족합니다. (보유: {len(player_items)}개)", {}

        item_obj = state.items.get(item_id)
        item_name = item_obj.name if item_obj else item_id
        item_val = item_obj.value if item_obj and item_obj.value > 0 else 10

        unit_price = cls.calculate_sell_price(shop, item_val, state, is_haggled=is_haggled)
        total_payout = unit_price * count

        # Check merchant gold
        if shop.merchant_gold != -1 and shop.merchant_gold < total_payout:
            return False, f"상인의 보유 골드가 부족합니다. (상인 소지금: {shop.merchant_gold}G)", {}

        # Remove from inventory
        for _ in range(count):
            state.player.inventory.remove(item_id)

        # Transfer gold
        state.player.gold += total_payout
        if shop.merchant_gold != -1:
            shop.merchant_gold -= total_payout

        # Add to shop stock if matching item exists
        existing_shop_item = next((i for i in shop.inventory if i.item_id == item_id), None)
        if existing_shop_item and existing_shop_item.stock != -1:
            existing_shop_item.stock += count

        msg = f"💰 **[판매 완료]** [{item_name}] {count}개를 {total_payout}G에 매각했습니다. (현재 골드: {state.player.gold}G)"
        return True, msg, {"item_id": item_id, "payout": total_payout, "count": count}

    @classmethod
    def use_service(cls, state: Any, shop_id: str, service_id: str) -> Tuple[bool, str]:
        """Executes a special merchant service (repair, remove_poison, identify, rumor, etc.)."""
        if not hasattr(state, "shops") or shop_id not in state.shops:
            shop = cls.get_shop_template(shop_id)
            if shop:
                state.shops[shop_id] = shop
            else:
                return False, "상점을 찾을 수 없습니다."

        shop = state.shops[shop_id]
        if service_id not in shop.services or not shop.services[service_id].get("enabled", False):
            return False, f"이 상점에서는 제공하지 않는 서비스입니다: {service_id}"

        srv = shop.services[service_id]
        cost = srv.get("cost_gold", 0)

        if state.player.gold < cost:
            return False, f"서비스 이용 골드가 부족합니다. (필요: {cost}G, 보유: {state.player.gold}G)"

        # 1. Poison removal
        if service_id == "remove_poison":
            from src.world.status_engine import StatusEffectEngine
            cured = StatusEffectEngine.cure_by_condition(state.player, "해독제")
            state.player.gold -= cost
            return True, f"🌿 [{shop.shop_name}] 중독 및 유해 상태이상 치료 완료! (지불: {cost}G)"

        # 2. Equipment Repair
        elif service_id == "repair":
            state.player.gold -= cost
            return True, f"🔨 [{shop.shop_name}] 모든 장비의 손상 부위 수리 및 내구도 복구 완료! (지불: {cost}G)"

        # 3. Mana Recovery
        elif service_id == "mana_recovery":
            state.player.mana = state.player.max_mana_effective
            state.player.gold -= cost
            return True, f"✨ [{shop.shop_name}] 비전 의식을 통해 마나가 100% 회복되었습니다! (지불: {cost}G)"

        # 4. Rumor / Clue
        elif service_id == "rumor":
            state.player.gold -= cost
            rumor_fact = f"[{shop.shop_name} 소문] 배후 세력이 최근 국경 지대에서 은밀히 병력을 이동시키고 있다는 소문이 있습니다."
            state.world_facts.append(rumor_fact)
            return True, f"👂 [{shop.shop_name}] 소문 획득: '{rumor_fact}' (지불: {cost}G)"

        # Default fallback service
        state.player.gold -= cost
        return True, f"🛎️ [{shop.shop_name}] '{srv.get('description_ko', service_id)}' 서비스를 이용했습니다. (지불: {cost}G)"

    @classmethod
    def restock_turn_ticks(cls, state: Any, delta_turns: int = 1):
        """Replenishes shop stocks when restock interval expires."""
        if not hasattr(state, "shops"):
            return

        for s in state.shops.values():
            s.turns_since_restock += delta_turns
            if s.turns_since_restock >= s.restock_interval_turns:
                s.turns_since_restock = 0
                for item in s.inventory:
                    if item.stock != -1 and item.stock < item.max_stock:
                        item.stock = min(item.max_stock, item.stock + 1)

    @classmethod
    def format_shop_html(cls, state: Any, shop_id: Optional[str] = None) -> str:
        """Renders rich, responsive trading UI with buy/sell catalog and services."""
        shop = state.shops.get(shop_id) if (shop_id and hasattr(state, "shops")) else cls.get_active_shop(state)
        if not shop:
            return "<div class='qt-panel-content' style='color:#a0aec0;'>현재 위치에 이용 가능한 상점이 없습니다.</div>"

        html_parts = [f"<div class='qt-shop-panel' style='padding:8px;'>"]
        html_parts.append(f"""
        <div style="background:#2d3748; color:#ffffff; padding:10px 14px; border-radius:6px; margin-bottom:10px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <b style="font-size:15px;">🏪 {shop.shop_name}</b>
            <span style="font-size:12px; color:#cbd5e0;">상인 소지금: {shop.merchant_gold}G</span>
          </div>
          <p style="font-size:12px; color:#e2e8f0; margin:4px 0 0 0; font-style:italic;">"{shop.dialogue.get('greeting', '')}"</p>
        </div>
        """)

        # Services block
        if shop.services:
            html_parts.append("<h4 style='font-size:13px; color:#2b6cb0; margin:6px 0;'>🛎️ 이용 가능한 특수 서비스</h4>")
            html_parts.append("<div style='display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px;'>")
            for s_id, srv in shop.services.items():
                if srv.get("enabled", True):
                    html_parts.append(f"""
                    <div style="background:#edf2f7; border:1px solid #cbd5e0; border-radius:4px; padding:4px 8px; font-size:11px;">
                      <b>{srv.get('description_ko', s_id)}</b> <span style="color:#c53030;">({srv.get('cost_gold', 0)}G)</span>
                    </div>
                    """)
            html_parts.append("</div>")

        # Goods catalog
        html_parts.append("<h4 style='font-size:13px; color:#2b6cb0; margin:6px 0;'>📦 판매 상품 목록</h4>")
        for item in shop.inventory:
            unlocked, reason = cls.check_item_unlock(item, state)
            price = cls.calculate_buy_price(shop, item, state)
            tier_colors = {"common": "#718096", "uncommon": "#3182ce", "rare": "#805ad5", "unique": "#dd6b20", "cursed": "#e53e3e"}
            t_color = tier_colors.get(item.item_tier, "#718096")

            stock_str = f"재고: {item.stock}개" if item.stock != -1 else "재고: 무제한"
            opacity = "1.0" if unlocked else "0.5"
            lock_badge = f"<span style='color:#e53e3e; font-size:11px;'>[🔒 {reason}]</span>" if not unlocked else ""

            html_parts.append(f"""
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:4px solid {t_color}; border-radius:4px; padding:8px 10px; margin-bottom:6px; opacity:{opacity}; box-shadow:0 1px 2px rgba(0,0,0,0.04);">
              <div style="display:flex; justify-content:space-between;">
                <span style="font-weight:bold; font-size:13px; color:#2d3748;">[{item.name_ko}] {lock_badge}</span>
                <span style="font-weight:bold; color:#d69e2e; font-size:13px;">{price}G</span>
              </div>
              <p style="font-size:11px; color:#718096; margin:2px 0;">{item.description_ko}</p>
              <div style="font-size:10px; color:#a0aec0;">{stock_str} | 등급: {item.item_tier}</div>
            </div>
            """)

        html_parts.append("</div>")
        return "".join(html_parts)

    @classmethod
    def format_shop_context_for_prompt(cls, state: Any) -> str:
        """Formats active shop prices and services for GM LLM context injection."""
        shop = cls.get_active_shop(state)
        if not shop:
            return ""

        lines = [f"[🏪 상점 및 상인 상호작용 가능: {shop.shop_name}]"]
        lines.append(f"- 상인: {shop.npc_id} | 소지금: {shop.merchant_gold}G | 흥정 가능: {'예' if shop.haggling_allowed else '아니오'}")
        
        items_desc = []
        for i in shop.inventory:
            unlocked, _ = cls.check_item_unlock(i, state)
            if unlocked and (i.stock > 0 or i.stock == -1):
                price = cls.calculate_buy_price(shop, i, state)
                items_desc.append(f"{i.name_ko}({price}G)")
        if items_desc:
            lines.append(f"- 구매 가능 상품: {', '.join(items_desc)}")

        if shop.services:
            srv_desc = [f"{s.get('description_ko', k)}({s.get('cost_gold', 0)}G)" for k, s in shop.services.items() if s.get('enabled', True)]
            lines.append(f"- 제공 서비스: {', '.join(srv_desc)}")

        return "\n".join(lines)
