"""
Deterministic Crafting & Alchemy Engine for Quilltale TRPG Engine.
Handles recipes, ingredient matching, station/tool verification,
quality outcomes (critical/success/partial/failure), catalysts,
salvaging, and blind experimentation.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
import copy

from src.core.config import TEMPLATES_DIR
from src.world.dice import DiceEngine


@dataclass
class RecipeIngredient:
    item_id: str = ""
    tag: str = ""
    count: int = 1

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "tag": self.tag,
            "count": self.count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecipeIngredient":
        return cls(
            item_id=str(data.get("item_id", "")),
            tag=str(data.get("tag", "")),
            count=int(data.get("count", 1)),
        )


@dataclass
class RecipeOutcome:
    result_item_id: str
    name_ko: str
    count: int = 1
    quality: str = "normal"               # "masterwork" | "normal" | "flawed" | "cursed"
    description_ko: str = ""
    explosion_damage: int = 0
    status_applied: str = ""

    def to_dict(self) -> dict:
        return {
            "result_item_id": self.result_item_id,
            "name_ko": self.name_ko,
            "count": self.count,
            "quality": self.quality,
            "description_ko": self.description_ko,
            "explosion_damage": self.explosion_damage,
            "status_applied": self.status_applied,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecipeOutcome":
        return cls(
            result_item_id=str(data.get("result_item_id", "crafted_item")),
            name_ko=str(data.get("name_ko", "제작품")),
            count=int(data.get("count", 1)),
            quality=str(data.get("quality", "normal")),
            description_ko=str(data.get("description_ko", "")),
            explosion_damage=int(data.get("explosion_damage", 0)),
            status_applied=str(data.get("status_applied", "")),
        )


@dataclass
class Recipe:
    recipe_id: str
    name_ko: str
    category: str                           # "alchemy_potion" | "blacksmithing" | "arcane_crafting" | "survival_cooking" | "forbidden_transmutation"
    tier: str = "basic"                     # "basic" | "intermediate" | "master" | "forbidden" | "mythic" | "unique"
    description_ko: str = ""
    required_station: str = "none"          # "none" | "alchemy_kit" | "blacksmith_forge" | "arcane_altar" | "campfire_kitchen"
    required_tools: List[str] = field(default_factory=list)
    prerequisites: Dict[str, Any] = field(default_factory=dict)
    environmental_conditions: Dict[str, Any] = field(default_factory=dict)
    ingredients: List[RecipeIngredient] = field(default_factory=list)
    optional_catalysts: List[Dict[str, Any]] = field(default_factory=list)
    craft_time_minutes: int = 30
    mana_cost: int = 0
    craft_stat: str = "INT"
    craft_dc: int = 12
    outcomes: Dict[str, RecipeOutcome] = field(default_factory=dict)
    toxicity_cost: int = 0
    corruption_cost: int = 0
    spoilage_turns: int = -1
    salvage: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "recipe_id": self.recipe_id,
            "name_ko": self.name_ko,
            "category": self.category,
            "tier": self.tier,
            "description_ko": self.description_ko,
            "required_station": self.required_station,
            "required_tools": self.required_tools,
            "prerequisites": self.prerequisites,
            "environmental_conditions": self.environmental_conditions,
            "ingredients": [i.to_dict() for i in self.ingredients],
            "optional_catalysts": self.optional_catalysts,
            "craft_time_minutes": self.craft_time_minutes,
            "mana_cost": self.mana_cost,
            "craft_stat": self.craft_stat,
            "craft_dc": self.craft_dc,
            "outcomes": {k: v.to_dict() for k, v in self.outcomes.items()},
            "toxicity_cost": self.toxicity_cost,
            "corruption_cost": self.corruption_cost,
            "spoilage_turns": self.spoilage_turns,
            "salvage": self.salvage,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Recipe":
        ings = [RecipeIngredient.from_dict(i) for i in data.get("ingredients", []) if isinstance(i, dict)]
        outcomes_map = {}
        for k, v in data.get("outcomes", {}).items():
            if isinstance(v, dict):
                outcomes_map[k] = RecipeOutcome.from_dict(v)

        # Build fallback default outcomes if not specified
        if not outcomes_map:
            result_item_id = str(data.get("recipe_id", "crafted_item")).replace("recipe_", "")
            name_ko = str(data.get("name_ko", "제작품"))
            desc_ko = str(data.get("description_ko", ""))
            outcomes_map["success"] = RecipeOutcome(
                result_item_id=result_item_id,
                name_ko=name_ko,
                count=1,
                quality="normal",
                description_ko=desc_ko,
            )
            outcomes_map["critical_success"] = RecipeOutcome(
                result_item_id=f"perfect_{result_item_id}",
                name_ko=f"완전한 {name_ko}",
                count=2,
                quality="masterwork",
                description_ko=f"대성공! {desc_ko}",
            )
            outcomes_map["partial_success"] = RecipeOutcome(
                result_item_id=f"weak_{result_item_id}",
                name_ko=f"불완전한 {name_ko}",
                count=1,
                quality="flawed",
                description_ko=f"부분 성공. {desc_ko}",
            )
            outcomes_map["critical_failure"] = RecipeOutcome(
                result_item_id="toxic_sludge",
                name_ko="유독성 찌꺼기",
                count=1,
                quality="cursed",
                description_ko="제작 중 반응이 폭주하여 유독성 찌꺼기가 남았습니다.",
                explosion_damage=10,
            )

        return cls(
            recipe_id=str(data.get("recipe_id", "")),
            name_ko=str(data.get("name_ko", "")),
            category=str(data.get("category", "alchemy_potion")),
            tier=str(data.get("tier", "basic")),
            description_ko=str(data.get("description_ko", "")),
            required_station=str(data.get("required_station", "none")),
            required_tools=list(data.get("required_tools", [])),
            prerequisites=dict(data.get("prerequisites", {})),
            environmental_conditions=dict(data.get("environmental_conditions", {})),
            ingredients=ings,
            optional_catalysts=list(data.get("optional_catalysts", [])),
            craft_time_minutes=int(data.get("craft_time_minutes", 30)),
            mana_cost=int(data.get("mana_cost", 0)),
            craft_stat=str(data.get("craft_stat", "INT")),
            craft_dc=int(data.get("craft_dc", 12)),
            outcomes=outcomes_map,
            toxicity_cost=int(data.get("toxicity_cost", 0)),
            corruption_cost=int(data.get("corruption_cost", 0)),
            spoilage_turns=int(data.get("spoilage_turns", -1)),
            salvage=dict(data.get("salvage", {})),
        )


class CraftingEngine:
    """
    Pure Python Deterministic Crafting & Alchemy Engine.
    Handles ingredient deduction, station/tool validation, skill checks,
    quality outcomes, salvaging, and blind experimentation.
    """

    _templates_cache: Optional[Dict[str, Recipe]] = None

    @classmethod
    def load_templates(cls, path: Optional[Path] = None) -> Dict[str, Recipe]:
        """Loads recipe definitions from recipe_templates.json."""
        target_path = path or (TEMPLATES_DIR / "recipe_templates.json")
        if not target_path.exists():
            return {}

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                raw_list = json.load(f)
            recipes = {}
            for r_data in raw_list:
                r = Recipe.from_dict(r_data)
                if r.recipe_id:
                    recipes[r.recipe_id] = r
            cls._templates_cache = recipes
            return recipes
        except Exception:
            return {}

    @classmethod
    def get_recipe_template(cls, recipe_id: str) -> Optional[Recipe]:
        if cls._templates_cache is None:
            cls.load_templates()
        if cls._templates_cache and recipe_id in cls._templates_cache:
            return copy.deepcopy(cls._templates_cache[recipe_id])
        return None

    @classmethod
    def check_recipe_prerequisites(cls, recipe: Recipe, state: Any) -> Tuple[bool, str]:
        """Validates player level, stats, and completed quests for crafting."""
        reqs = recipe.prerequisites
        if not reqs:
            return True, "제작 가능"

        player = state.player

        # 1. Level check
        if "level_min" in reqs and player.level < reqs["level_min"]:
            return False, f"요구 레벨 미달 (필요: Lv.{reqs['level_min']})"

        # 2. Stat check
        if "stats" in reqs:
            for stat_name, min_val in reqs["stats"].items():
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
                elif stat_lower in ["con", "constitution"]:
                    p_val = player.constitution
                elif stat_lower in ["cha", "luk", "luck"]:
                    p_val = player.luck

                if p_val < min_val:
                    return False, f"스탯 부족 ({stat_name} {min_val} 이상 필요)"

        # 3. Quest check
        if "completed_quest_id" in reqs:
            q_id = reqs["completed_quest_id"]
            if not hasattr(state, "quests") or q_id not in state.quests or state.quests[q_id].status != "completed":
                return False, f"선행 퀘스트 미완료"

        return True, "제작 가능"

    @classmethod
    def check_recipe_ingredients(cls, recipe: Recipe, state: Any) -> Tuple[bool, List[str], str]:
        """
        Verifies if player inventory has all required items or tag substitutes.
        Returns (has_all, items_to_consume, reason).
        """
        inv_copy = list(state.player.inventory)
        to_consume: List[str] = []

        for ing in recipe.ingredients:
            if ing.item_id:
                # Fixed item check
                needed = ing.count
                found = [i for i in inv_copy if i == ing.item_id]
                if len(found) < needed:
                    item_name = state.items[ing.item_id].name if ing.item_id in state.items else ing.item_id
                    return False, [], f"재료 부족: [{item_name}] (필요: {needed}개, 보유: {len(found)}개)"
                for _ in range(needed):
                    inv_copy.remove(ing.item_id)
                    to_consume.append(ing.item_id)
            elif ing.tag:
                # Tag substitute check
                needed = ing.count
                tag_matches = []
                for item_id in inv_copy:
                    item_obj = state.items.get(item_id)
                    if item_obj and (ing.tag in item_obj.description.lower() or ing.tag in item_obj.item_type.lower() or ing.tag == item_id):
                        tag_matches.append(item_id)

                if len(tag_matches) < needed:
                    return False, [], f"태그 재료 부족: [{ing.tag}] 계열 (필요: {needed}개)"
                for m in tag_matches[:needed]:
                    inv_copy.remove(m)
                    to_consume.append(m)

        return True, to_consume, "재료 충분"

    @classmethod
    def craft_item(
        cls,
        state: Any,
        recipe_id: str,
        catalyst_id: Optional[str] = None,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Executes deterministic crafting with d20 skill roll and quality outcome.
        """
        recipe = cls.get_recipe_template(recipe_id)
        if not recipe:
            return False, f"레시피를 찾을 수 없습니다: {recipe_id}", {}

        # 1. Prerequisites
        prereq_ok, reason = cls.check_recipe_prerequisites(recipe, state)
        if not prereq_ok:
            return False, f"제작 불가: {reason}", {}

        # 2. Mana cost
        if state.player.mana < recipe.mana_cost:
            return False, f"마나 부족 (필요: {recipe.mana_cost}, 보유: {state.player.mana})", {}

        # 3. Ingredients
        has_ings, to_consume, ing_reason = cls.check_recipe_ingredients(recipe, state)
        if not has_ings:
            return False, f"제작 불가: {ing_reason}", {}

        # 4. Optional Catalyst
        catalyst_used = None
        if catalyst_id and catalyst_id in state.player.inventory:
            cat_match = next((c for c in recipe.optional_catalysts if c.get("item_id") == catalyst_id), None)
            if cat_match:
                catalyst_used = cat_match
                state.player.inventory.remove(catalyst_id)

        # Deduct ingredients & mana
        for item_to_remove in to_consume:
            if item_to_remove in state.player.inventory:
                state.player.inventory.remove(item_to_remove)

        state.player.mana -= recipe.mana_cost
        state.player.time_elapsed_minutes += recipe.craft_time_minutes

        # 5. Deterministic Skill Roll
        stat_name = recipe.craft_stat.upper()
        p_stat_val = 10
        player = state.player
        if stat_name in ["STR", "STRENGTH"]:
            p_stat_val = getattr(player, "effective_strength", player.strength)
        elif stat_name in ["DEX", "AGI", "AGILITY"]:
            p_stat_val = getattr(player, "effective_agility", player.agility)
        elif stat_name in ["INT", "INTELLIGENCE"]:
            p_stat_val = getattr(player, "effective_intelligence", player.intelligence)
        elif stat_name in ["WIS", "WISDOM"]:
            p_stat_val = player.wisdom
        elif stat_name in ["CON", "CONSTITUTION"]:
            p_stat_val = player.constitution
        elif stat_name in ["CHA", "LUCK", "LUK"]:
            p_stat_val = player.luck

        dc_val = recipe.craft_dc
        check_res = DiceEngine.perform_check(
            action_type=f"제작-{recipe.category}",
            stat_value=p_stat_val,
            dc=dc_val,
        )

        # Determine outcome
        outcome: RecipeOutcome
        if check_res.is_critical_success and "critical_success" in recipe.outcomes:
            outcome = recipe.outcomes["critical_success"]
            roll_label = "🌟 [제작 대성공!]"
        elif check_res.is_success and "success" in recipe.outcomes:
            outcome = recipe.outcomes["success"]
            roll_label = "✨ [제작 성공]"
        elif check_res.is_critical_failure and "critical_failure" in recipe.outcomes:
            outcome = recipe.outcomes["critical_failure"]
            roll_label = "💥 [제작 대실패!]"
        else:
            outcome = recipe.outcomes.get("partial_success") or recipe.outcomes.get("success") or RecipeOutcome(
                result_item_id="flawed_item", name_ko="불완전한 제작품"
            )
            roll_label = "⚠️ [제작 부분 성공]"

        # Handle Critical Failure penalties
        if check_res.is_critical_failure and outcome.explosion_damage > 0:
            state.player.health = max(1, state.player.health - outcome.explosion_damage)
        if outcome.status_applied:
            from src.world.status_engine import StatusEffectEngine
            StatusEffectEngine.apply_status(state.player, outcome.status_applied, duration=3)

        # Grant Item
        from src.world.state import Item
        result_item_id = outcome.result_item_id
        for _ in range(outcome.count):
            if result_item_id not in state.items:
                state.items[result_item_id] = Item(
                    id=result_item_id,
                    name=outcome.name_ko,
                    description=outcome.description_ko,
                    item_type=recipe.category,
                    value=50,
                    location="inventory",
                )
            state.player.inventory.append(result_item_id)

        # Quest Progress Hook
        from src.world.quest_engine import QuestEngine
        q_logs = QuestEngine.progress_event(state, "collect", result_item_id, outcome.count)

        # Build Output Log
        log_lines = [
            f"⚒️ **{roll_label}** [{recipe.name_ko}] 제작 완료! (판정: {check_res.summary_ko})",
            f"- 결과물: **[{outcome.name_ko}]** {outcome.count}개 획득 (품질: {outcome.quality})",
            f"- 소요 시간: {recipe.craft_time_minutes}분 (마나 소모: {recipe.mana_cost})",
        ]
        if catalyst_used:
            log_lines.append(f"- 🧪 [촉매 효과 발현] {catalyst_used.get('name_ko', '')}: {catalyst_used.get('effect_ko', '')}")
        if check_res.is_critical_failure and outcome.explosion_damage > 0:
            log_lines.append(f"- 🩸 [공방 폭발 피해] HP -{outcome.explosion_damage} 감소! (현재 HP: {state.player.health})")
        if q_logs:
            log_lines.extend(q_logs)

        return True, "\n".join(log_lines), {"outcome": outcome.to_dict(), "recipe_id": recipe_id}

    @classmethod
    def salvage_item(cls, state: Any, item_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Dismantles an item in player inventory to recover raw materials."""
        if item_id not in state.player.inventory:
            return False, f"가방에 해당 아이템이 없습니다: {item_id}", {}

        if cls._templates_cache is None:
            cls.load_templates()

        matched_recipe = None
        for r in (cls._templates_cache or {}).values():
            if r.salvage and r.salvage.get("enabled", False):
                # Check if item_id matches outcomes or recipe_id
                outcome_ids = [o.result_item_id for o in r.outcomes.values()]
                if item_id in outcome_ids or item_id == r.recipe_id.replace("recipe_", ""):
                    matched_recipe = r
                    break

        if not matched_recipe:
            return False, f"해당 아이템은 분해할 수 없는 구조입니다: {item_id}", {}

        salvage_info = matched_recipe.salvage
        yield_list = salvage_info.get("yield", [])
        if not yield_list:
            return False, "회수 가능한 자원이 없습니다.", {}

        # Remove dismantled item
        state.player.inventory.remove(item_id)

        from src.world.state import Item
        recovered_names = []
        for y in yield_list:
            y_id = y.get("item_id", "scrap")
            y_cnt = y.get("count", 1)
            for _ in range(y_cnt):
                if y_id not in state.items:
                    state.items[y_id] = Item(id=y_id, name=y_id, description="분해 자원", value=10, location="inventory")
                state.player.inventory.append(y_id)
            recovered_names.append(f"{state.items[y_id].name} {y_cnt}개")

        msg = f"🔧 **[분해 완료]** [{state.items.get(item_id, item_id)}]을(를) 분해하여 자원을 회수했습니다:\n- 회수 자원: {', '.join(recovered_names)}"
        return True, msg, {"recovered": yield_list}

    @classmethod
    def experiment_blind_craft(cls, state: Any, item_ids: List[str]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Blind combination: player throws random items into alchemy kit / forge without recipe!
        """
        if cls._templates_cache is None:
            cls.load_templates()

        # Count player input items
        input_counts = {}
        for i_id in item_ids:
            input_counts[i_id] = input_counts.get(i_id, 0) + 1

        # Match against recipe templates
        matched_recipe_id = None
        for r_id, r in (cls._templates_cache or {}).items():
            req_counts = {ing.item_id: ing.count for ing in r.ingredients if ing.item_id}
            if req_counts and req_counts == input_counts:
                matched_recipe_id = r_id
                break

        if matched_recipe_id:
            # Blind discovery success!
            success, msg, data = cls.craft_item(state, matched_recipe_id)
            if success:
                msg = "💡 **[미지의 레시피 발견!]** 직관적인 실험을 통해 새로운 조합법을 알아냈습니다!\n" + msg
            return success, msg, data

        # Failure: consume ingredients and leave toxic residue
        for i_id in item_ids:
            if i_id in state.player.inventory:
                state.player.inventory.remove(i_id)

        from src.world.state import Item
        state.items["toxic_sludge"] = Item(id="toxic_sludge", name="유독성 찌꺼기", description="실패한 연금 찌꺼기", value=1, location="inventory")
        state.player.inventory.append("toxic_sludge")
        state.player.health = max(1, state.player.health - 5)

        msg = "💥 **[실험 조합 실패]** 원소들이 거칠게 충돌하며 검은 연기와 함께 [유독성 찌꺼기]만 남았습니다. (HP -5 피해)"
        return False, msg, {}

    @classmethod
    def format_crafting_html(cls, state: Any) -> str:
        """Renders rich, responsive crafting recipes & workshop UI."""
        if cls._templates_cache is None:
            cls.load_templates()

        recipes = cls._templates_cache or {}
        if not recipes:
            return "<div class='qt-panel-content' style='color:#a0aec0;'>등록된 제작 레시피가 없습니다.</div>"

        html_parts = ["<div class='qt-crafting-panel' style='padding:8px;'>"]
        html_parts.append("""
        <div style="background:#1a202c; color:#ffffff; padding:10px 14px; border-radius:6px; margin-bottom:10px;">
          <b style="font-size:15px;">⚒️ 공방 및 연금술 조합소</b>
          <p style="font-size:12px; color:#cbd5e0; margin:4px 0 0 0;">보유한 재료와 지식을 바탕으로 마도구, 비전 물약, 특수 장비를 제작합니다.</p>
        </div>
        """)

        for r_id, r in list(recipes.items())[:15]:
            prereq_ok, _ = cls.check_recipe_prerequisites(r, state)
            has_ings, _, ing_reason = cls.check_recipe_ingredients(r, state)

            status_badge = "<span style='color:#38a169; font-weight:bold; font-size:11px;'>[제작 가능]</span>" if (prereq_ok and has_ings) else f"<span style='color:#e53e3e; font-size:11px;'>[{ing_reason}]</span>"
            category_names = {"alchemy_potion": "🧪 연금술", "blacksmithing": "🔨 대장기술", "arcane_crafting": "✨ 비전제작", "survival_cooking": "🍖 야영요리", "forbidden_transmutation": "🔮 금단변이"}
            cat_label = category_names.get(r.category, "⚒️ 제작")

            ing_strs = []
            for ing in r.ingredients:
                ing_name = state.items[ing.item_id].name if ing.item_id in state.items else (ing.tag or ing.item_id)
                ing_strs.append(f"{ing_name} x{ing.count}")

            html_parts.append(f"""
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-left:4px solid #4a5568; border-radius:4px; padding:8px 10px; margin-bottom:6px; box-shadow:0 1px 2px rgba(0,0,0,0.04);">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <b style="font-size:13px; color:#2d3748;">{r.name_ko} <small style="color:#718096; font-weight:normal;">({cat_label})</small></b>
                {status_badge}
              </div>
              <p style="font-size:11px; color:#4a5568; margin:3px 0;">{r.description_ko}</p>
              <div style="font-size:11px; color:#2b6cb0; margin-top:2px;">
                <b>필요 재료:</b> {', '.join(ing_strs)} | <b>난이도:</b> DC {r.craft_dc} ({r.craft_stat})
              </div>
            </div>
            """)

        html_parts.append("</div>")
        return "".join(html_parts)

    @classmethod
    def format_crafting_context_for_prompt(cls, state: Any) -> str:
        """Formats available crafting options for GM context."""
        if cls._templates_cache is None:
            cls.load_templates()

        available_names = []
        for r in (cls._templates_cache or {}).values():
            has_ings, _, _ = cls.check_recipe_ingredients(r, state)
            if has_ings:
                available_names.append(r.name_ko)

        if not available_names:
            return ""

        return f"[⚒️ 현재 재료로 즉시 제작 가능한 레시피: {', '.join(available_names[:5])}]"
