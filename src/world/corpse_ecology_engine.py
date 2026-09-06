"""
Deterministic Battlefield Corpse Ecology & Decay Engine for Quilltale TRPG.
Models post-combat battlefield dynamics: corpse decay stages (fresh -> bloated -> rotting -> skeleton),
scavenger attraction (crows, wolves, ghouls), hybrid loot degradation (food/textile rot + scavenger tearing),
and sanitary disposal (cremation/burial) preventing epidemic disease outbreaks.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import random
import logging

logger = logging.getLogger(__name__)


@dataclass
class CorpseInstance:
    corpse_id: str
    origin_npc_id: str
    origin_name: str
    location_id: str
    time_since_death_minutes: int = 0
    decay_stage: str = "fresh"  # "fresh" (0~60m), "bloated" (61~180m), "rotting" (181~360m), "skeleton" (361m+)
    inventory_loot: List[Dict[str, Any]] = field(default_factory=list)
    gold: int = 0
    is_harvested: bool = False
    is_looted: bool = False
    is_buried: bool = False
    is_burned: bool = False
    attracted_scavengers: List[str] = field(default_factory=list)
    decay_fever_spread: bool = False
    traits: List[str] = field(default_factory=lambda: ["corpse", "decay_ecology", "battlefield_remains"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "corpse_id": self.corpse_id,
            "origin_npc_id": self.origin_npc_id,
            "origin_name": self.origin_name,
            "location_id": self.location_id,
            "time_since_death_minutes": self.time_since_death_minutes,
            "decay_stage": self.decay_stage,
            "inventory_loot": [dict(it) for it in self.inventory_loot],
            "gold": self.gold,
            "is_harvested": self.is_harvested,
            "is_looted": self.is_looted,
            "is_buried": self.is_buried,
            "is_burned": self.is_burned,
            "attracted_scavengers": list(self.attracted_scavengers),
            "decay_fever_spread": self.decay_fever_spread,
            "traits": list(self.traits),
        }

    @classmethod
    def from_dict(cls, data: Any) -> "CorpseInstance":
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            data = {}
        return cls(
            corpse_id=data.get("corpse_id", "corpse_unknown"),
            origin_npc_id=data.get("origin_npc_id", ""),
            origin_name=data.get("origin_name", "이름 모를 망자"),
            location_id=data.get("location_id", ""),
            time_since_death_minutes=int(data.get("time_since_death_minutes", 0)),
            decay_stage=data.get("decay_stage", "fresh"),
            inventory_loot=list(data.get("inventory_loot", [])),
            gold=int(data.get("gold", 0)),
            is_harvested=bool(data.get("is_harvested", False)),
            is_looted=bool(data.get("is_looted", False)),
            is_buried=bool(data.get("is_buried", False)),
            is_burned=bool(data.get("is_burned", False)),
            attracted_scavengers=list(data.get("attracted_scavengers", [])),
            decay_fever_spread=bool(data.get("decay_fever_spread", False)),
            traits=list(data.get("traits", ["corpse", "decay_ecology", "battlefield_remains"])),
        )


class CorpseEcologyEngine:
    """
    Deterministic battlefield corpse ecology system:
    Handles decay timeline, scavenger attraction, hybrid loot degradation, and sanitation disposal.
    """

    ORGANIC_KEYWORDS = ["고기", "식량", "빵", "약초", "포션", "가죽", "천", "양피지", "붕대", "허브", "meat", "ration", "herb", "potion", "cloth"]

    @classmethod
    def register_corpse_from_killed_actor(
        cls,
        state: Any,
        victim: Any,
        killer: Any = None,
        location_id: Optional[str] = None
    ) -> CorpseInstance:
        """Creates and registers a CorpseInstance in state.active_corpses when an actor dies."""
        corpse_id = f"corpse_{getattr(victim, 'id', 'actor')}_{state.turn}"
        loc = location_id or getattr(victim, "location", getattr(state.player, "location", "unknown"))
        victim_name = getattr(victim, "name", "이름 모를 자")

        loot: List[Dict[str, Any]] = []
        raw_inv = getattr(victim, "inventory", [])
        for item_entry in raw_inv:
            if isinstance(item_entry, str):
                if hasattr(state, "items") and item_entry in state.items:
                    item_obj = state.items[item_entry]
                    loot.append({
                        "id": getattr(item_obj, "id", item_entry),
                        "name": getattr(item_obj, "name", item_entry),
                        "type": getattr(item_obj, "item_type", "misc"),
                        "spoiled": False,
                    })
                else:
                    loot.append({"id": item_entry, "name": item_entry, "type": "misc", "spoiled": False})
            elif isinstance(item_entry, dict):
                loot.append(dict(item_entry))

        corpse = CorpseInstance(
            corpse_id=corpse_id,
            origin_npc_id=getattr(victim, "id", "npc_unknown"),
            origin_name=victim_name,
            location_id=loc,
            time_since_death_minutes=0,
            decay_stage="fresh",
            inventory_loot=loot,
            gold=getattr(victim, "gold", 0),
        )

        if not hasattr(state, "active_corpses") or state.active_corpses is None:
            state.active_corpses = {}
        state.active_corpses[corpse_id] = corpse
        return corpse

    @classmethod
    def process_turn_corpse_decay(
        cls,
        state: Any,
        delta_minutes: int = 30,
        rng: Optional[random.Random] = None
    ) -> List[str]:
        """
        Advances decay of all unburied, unburned corpses.
        Implements User Decision Q1 (Hybrid Option A + B with scavenger probability):
        - Rotting stage (181~360m): Perishable goods rot (A), scavengers may spawn (B), damaging or scattering loot.
        - Skeleton stage (361m+): Only bones and hardened metal remains.
        """
        if not hasattr(state, "active_corpses") or not state.active_corpses:
            return []

        dice = rng or random.Random(state.turn * 1337 + delta_minutes)
        logs: List[str] = []

        for corpse_id, corpse_data in list(state.active_corpses.items()):
            corpse = corpse_data if isinstance(corpse_data, CorpseInstance) else CorpseInstance.from_dict(corpse_data)

            if corpse.is_buried or corpse.is_burned:
                continue

            corpse.time_since_death_minutes += delta_minutes
            elapsed = corpse.time_since_death_minutes
            old_stage = corpse.decay_stage

            # 1. Decay Stage Transition
            if elapsed <= 60:
                corpse.decay_stage = "fresh"
            elif 61 <= elapsed <= 180:
                corpse.decay_stage = "bloated"
            elif 181 <= elapsed <= 360:
                corpse.decay_stage = "rotting"
            else:
                corpse.decay_stage = "skeleton"

            if old_stage != corpse.decay_stage:
                if corpse.decay_stage == "bloated":
                    corpse.attracted_scavengers.append("검은 까마귀 떼")
                    logs.append(
                        f"🪰 [시체 부패 진행] {corpse.origin_name}의 시신에서 복부 팽창 가스와 악취가 피어오르며 하늘에 까마귀 떼가 선회합니다."
                    )
                elif corpse.decay_stage == "rotting":
                    logs.append(
                        f"☣️ [시체 3단계 부패 (Rotting)] {corpse.origin_name}의 시신이 구더기와 부패액에 침식되어 극심한 악취를 풍기기 시작합니다."
                    )
                elif corpse.decay_stage == "skeleton":
                    logs.append(
                        f"💀 [시체 백골화 (Skeleton)] {corpse.origin_name}의 시신에서 모든 유기물 연조직이 부식되어 창백한 뼈와 금속 장구류만 남았습니다."
                    )

            # 2. Rotting Stage Mechanics (User Decision Q1: Option A + B hybrid)
            if corpse.decay_stage == "rotting":
                # Option A: Spoil organic goods (food, rations, textiles, cloth)
                for item in corpse.inventory_loot:
                    item_name = item.get("name", "").lower()
                    if any(kw in item_name for kw in cls.ORGANIC_KEYWORDS):
                        if not item.get("spoiled", False):
                            item["spoiled"] = True
                            item["name"] = f"부패해 썩어문드러진 {item['name']}"

                # Option B + Scavenger check: 45% chance to attract terrestrial scavengers (wolves, ghouls, rats)
                if "굶주린 들개 및 늑대 무리" not in corpse.attracted_scavengers:
                    if dice.random() < 0.45:
                        corpse.attracted_scavengers.append("굶주린 들개 및 늑대 무리")
                        # Scavengers tear at the corpse and scatter/damage remaining loot
                        if corpse.gold > 0:
                            scattered = max(1, int(corpse.gold * 0.35))
                            corpse.gold = max(0, corpse.gold - scattered)
                        # Damage 1 random item or drag it away
                        if corpse.inventory_loot and dice.random() < 0.6:
                            ruined_idx = dice.randint(0, len(corpse.inventory_loot) - 1)
                            ruined_item = corpse.inventory_loot[ruined_idx]
                            ruined_item["ruined_by_beast"] = True
                            ruined_item["name"] = f"야수에게 짓물려 훼손된 {ruined_item.get('name', '장비')}"

                        logs.append(
                            f"🐺 [청소 야수 유인] {corpse.origin_name}의 썩어가는 시체 악취를 맡고 들개와 맹수들이 몰려와 시신과 봇짐을 사납게 훼손했습니다!"
                        )

                # Epidemic Disease Vector check (linking with disease_engine)
                if not corpse.decay_fever_spread:
                    corpse.decay_fever_spread = True
                    logs.append(
                        f"⚠️ [전염병 오염원 경고] {corpse.location_id} 지역에 방치된 시체로 인해 '시체열병(corpse_decay_fever)' 및 수인성 역병 발생 위험이 급증했습니다!"
                    )

            # Sync back
            state.active_corpses[corpse_id] = corpse.to_dict()

        return logs

    @classmethod
    def loot_corpse(
        cls,
        state: Any,
        character: Any,
        corpse_id: str
    ) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Loots an active corpse. Respects organic decay and beast damage.
        """
        if not hasattr(state, "active_corpses") or corpse_id not in state.active_corpses:
            return False, "대상 시체를 찾을 수 없습니다.", []

        raw_c = state.active_corpses[corpse_id]
        corpse = raw_c if isinstance(raw_c, CorpseInstance) else CorpseInstance.from_dict(raw_c)

        if corpse.is_looted:
            return False, f"{corpse.origin_name}의 유해는 이미 누군가에 의해 샅샅이 수색되어 남은 소지품이 없습니다.", []

        if corpse.is_buried:
            return False, f"{corpse.origin_name}의 유해는 땅속 깊이 매장되어 파헤치지 않고는 수색할 수 없습니다.", []

        if corpse.is_burned:
            return False, f"{corpse.origin_name}의 유해는 화염에 전소되어 재와 잿더미만 남았습니다.", []

        looted_items: List[Dict[str, Any]] = []
        looted_gold = corpse.gold

        # Transfer gold
        if looted_gold > 0:
            cur_gold = getattr(character, "gold", 0)
            setattr(character, "gold", cur_gold + looted_gold)
            corpse.gold = 0

        # Transfer items
        char_inv = getattr(character, "inventory", [])
        for item in corpse.inventory_loot:
            if item.get("spoiled", False):
                looted_items.append({"name": item.get("name"), "status": "spoiled"})
            elif item.get("ruined_by_beast", False):
                looted_items.append({"name": item.get("name"), "status": "ruined"})
            else:
                looted_items.append({"name": item.get("name"), "status": "intact"})

            item_id = item.get("id")
            if item_id:
                if isinstance(char_inv, list):
                    char_inv.append(item_id)

        corpse.is_looted = True
        state.active_corpses[corpse_id] = corpse.to_dict()

        summary_msg = f"🎒 [{corpse.origin_name}의 유해 수색] {looted_gold} 골드와 {len(looted_items)}개의 소지품을 회수했습니다."
        if corpse.decay_stage in ("rotting", "skeleton"):
            summary_msg += f" (부패 단계: {corpse.decay_stage} - 유기물 및 일부 장비가 훼손됨)"
        return True, summary_msg, looted_items

    @classmethod
    def dispose_corpse(
        cls,
        state: Any,
        character: Any,
        corpse_id: str,
        method: str = "burn"
    ) -> Tuple[bool, str]:
        """
        Disposes of a corpse either by incineration ('burn') or sacred burial ('bury').
        Extinguishes epidemic disease vectors and clears scavenger attraction.
        """
        if not hasattr(state, "active_corpses") or corpse_id not in state.active_corpses:
            return False, "처리할 시체를 발견하지 못했습니다."

        raw_c = state.active_corpses[corpse_id]
        corpse = raw_c if isinstance(raw_c, CorpseInstance) else CorpseInstance.from_dict(raw_c)

        if corpse.is_burned:
            return False, "이미 화장되어 잿더미만 남은 시체입니다."
        if corpse.is_buried:
            return False, "이미 경건하게 매장된 시체입니다."

        if method == "burn":
            corpse.is_burned = True
            corpse.decay_stage = "ashes"
            state.active_corpses[corpse_id] = corpse.to_dict()
            return True, f"🔥 [시신 소각 화장] {corpse.origin_name}의 유해를 불길에 태워 정화했습니다. 악취와 역병 전염 위험이 완전히 소멸되었습니다."
        elif method == "bury":
            corpse.is_buried = True
            state.active_corpses[corpse_id] = corpse.to_dict()
            if hasattr(character, "sanity"):
                character.sanity = min(100, getattr(character, "sanity", 100) + 5)
            return True, f"🪦 [경건한 가매장] {corpse.origin_name}의 시신을 땅을 파 정중히 묻고 흙무덤을 세웠습니다. 들개와 벌레의 침탈을 막았습니다."
        else:
            return False, f"지원하지 않는 시체 처리 방식입니다: {method}"
