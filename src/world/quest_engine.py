"""
Deterministic Quest Journal & Tracker Engine for Quilltale TRPG Engine.
Tracks active, available, completed, and failed quests, objective progression,
multi-stage branching choices, time limits/deadlines, and rewards/faction impacts in 100% pure Python.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
import copy

from src.core.config import TEMPLATES_DIR


@dataclass
class QuestStage:
    stage_id: int
    type: str                               # "kill" | "collect" | "talk" | "reach" | "condition"
    target: str                             # ID of monster, NPC, item, or location
    required_count: int = 1
    current_count: int = 0
    description_ko: str = ""
    completed: bool = False

    def to_dict(self) -> dict:
        return {
            "stage_id": self.stage_id,
            "type": self.type,
            "target": self.target,
            "required_count": self.required_count,
            "current_count": self.current_count,
            "description_ko": self.description_ko,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuestStage":
        return cls(
            stage_id=int(data.get("stage_id", 1)),
            type=str(data.get("type", "talk")),
            target=str(data.get("target", "")),
            required_count=int(data.get("required_count", 1)),
            current_count=int(data.get("current_count", 0)),
            description_ko=str(data.get("description_ko", "")),
            completed=bool(data.get("completed", False)),
        )


@dataclass
class QuestChoice:
    choice_id: str
    description_ko: str
    requirements: Dict[str, Any] = field(default_factory=dict) # e.g. {"stats": {"INT": 14}, "gold_min": 200}
    outcome: Dict[str, Any] = field(default_factory=dict)      # rewards, faction_impact, stages

    def to_dict(self) -> dict:
        return {
            "choice_id": self.choice_id,
            "description_ko": self.description_ko,
            "requirements": self.requirements,
            "outcome": self.outcome,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuestChoice":
        return cls(
            choice_id=str(data.get("choice_id", "")),
            description_ko=str(data.get("description_ko", "")),
            requirements=dict(data.get("requirements", {})),
            outcome=dict(data.get("outcome", {})),
        )


@dataclass
class QuestOptional:
    objective_id: str
    type: str = "condition"
    target: str = ""
    required_count: int = 1
    current_count: int = 0
    description_ko: str = ""
    completed: bool = False
    bonus_rewards: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "objective_id": self.objective_id,
            "type": self.type,
            "target": self.target,
            "required_count": self.required_count,
            "current_count": self.current_count,
            "description_ko": self.description_ko,
            "completed": self.completed,
            "bonus_rewards": self.bonus_rewards,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QuestOptional":
        return cls(
            objective_id=str(data.get("objective_id", "")),
            type=str(data.get("type", "condition")),
            target=str(data.get("target", "")),
            required_count=int(data.get("required_count", 1)),
            current_count=int(data.get("current_count", 0)),
            description_ko=str(data.get("description_ko", "")),
            completed=bool(data.get("completed", False)),
            bonus_rewards=dict(data.get("bonus_rewards", {})),
        )


@dataclass
class Quest:
    id: str
    title: str
    category: str                           # "hunt" | "gather" | "escort" | "investigation" | "delivery" | "rescue"
    giver_npc_id: str = ""
    description: str = ""
    prerequisites: Dict[str, Any] = field(default_factory=dict)
    status: str = "available"               # "available" | "active" | "completed" | "failed"
    current_stage_idx: int = 0
    stages: List[QuestStage] = field(default_factory=list)
    branch_choices: List[QuestChoice] = field(default_factory=list)
    selected_choice_id: Optional[str] = None
    optional_objectives: List[QuestOptional] = field(default_factory=list)
    time_limit_minutes: int = 0             # 0 = unlimited
    time_elapsed_minutes: int = 0
    rewards: Dict[str, Any] = field(default_factory=dict)
    faction_impact: Dict[str, int] = field(default_factory=dict)
    failure_penalty: Dict[str, Any] = field(default_factory=dict)
    accepted_turn: int = 0
    completed_turn: int = 0

    @property
    def current_stage(self) -> Optional[QuestStage]:
        if 0 <= self.current_stage_idx < len(self.stages):
            return self.stages[self.current_stage_idx]
        return None

    @property
    def is_time_limited(self) -> bool:
        return self.time_limit_minutes > 0

    @property
    def remaining_minutes(self) -> int:
        if not self.is_time_limited:
            return 999999
        return max(0, self.time_limit_minutes - self.time_elapsed_minutes)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "giver_npc_id": self.giver_npc_id,
            "description": self.description,
            "prerequisites": self.prerequisites,
            "status": self.status,
            "current_stage_idx": self.current_stage_idx,
            "stages": [s.to_dict() for s in self.stages],
            "branch_choices": [c.to_dict() for c in self.branch_choices],
            "selected_choice_id": self.selected_choice_id,
            "optional_objectives": [o.to_dict() for o in self.optional_objectives],
            "time_limit_minutes": self.time_limit_minutes,
            "time_elapsed_minutes": self.time_elapsed_minutes,
            "rewards": self.rewards,
            "faction_impact": self.faction_impact,
            "failure_penalty": self.failure_penalty,
            "accepted_turn": self.accepted_turn,
            "completed_turn": self.completed_turn,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Quest":
        stages = [QuestStage.from_dict(s) for s in data.get("stages", []) if isinstance(s, dict)]
        choices = [QuestChoice.from_dict(c) for c in data.get("branch_choices", []) if isinstance(c, dict)]
        optionals = [QuestOptional.from_dict(o) for o in data.get("optional_objectives", []) if isinstance(o, dict)]

        return cls(
            id=str(data.get("id", "")),
            title=str(data.get("title", "")),
            category=str(data.get("category", "investigation")),
            giver_npc_id=str(data.get("giver_npc_id", "")),
            description=str(data.get("description", "")),
            prerequisites=dict(data.get("prerequisites", {})),
            status=str(data.get("status", "available")),
            current_stage_idx=int(data.get("current_stage_idx", 0)),
            stages=stages,
            branch_choices=choices,
            selected_choice_id=data.get("selected_choice_id"),
            optional_objectives=optionals,
            time_limit_minutes=int(data.get("time_limit_minutes", 0)),
            time_elapsed_minutes=int(data.get("time_elapsed_minutes", 0)),
            rewards=dict(data.get("rewards", {})),
            faction_impact=dict(data.get("faction_impact", {})),
            failure_penalty=dict(data.get("failure_penalty", {})),
            accepted_turn=int(data.get("accepted_turn", 0)),
            completed_turn=int(data.get("completed_turn", 0)),
        )


class QuestEngine:
    """
    Core Deterministic Quest Management System.
    Loads JSON templates, checks prerequisites, tracks objective increments,
    evaluates branches, delivers rewards, and synchronizes with WorldState.
    """

    _templates_cache: Optional[Dict[str, Quest]] = None

    @classmethod
    def load_templates(cls, path: Optional[Path] = None) -> Dict[str, Quest]:
        """Loads and caches all quest definitions from quest_templates.json."""
        target_path = path or (TEMPLATES_DIR / "quest_templates.json")
        if not target_path.exists():
            return {}

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                raw_list = json.load(f)
            quests = {}
            for q_data in raw_list:
                q = Quest.from_dict(q_data)
                if q.id:
                    quests[q.id] = q
            cls._templates_cache = quests
            return quests
        except Exception:
            return {}

    @classmethod
    def get_template(cls, quest_id: str) -> Optional[Quest]:
        if cls._templates_cache is None:
            cls.load_templates()
        if cls._templates_cache and quest_id in cls._templates_cache:
            return copy.deepcopy(cls._templates_cache[quest_id])
        return None

    @classmethod
    def check_prerequisites(cls, quest: Quest, state: Any) -> Tuple[bool, str]:
        """
        Checks if player satisfies quest prerequisites (level, stats, reputation).
        Returns (is_eligible, reason_ko).
        """
        player = state.player
        req = quest.prerequisites

        # 1. Level check
        if "level_min" in req and player.level < req["level_min"]:
            return False, f"필요 레벨 미달 (필요: Lv.{req['level_min']}, 현재: Lv.{player.level})"

        # 2. Stat check
        if "stats" in req:
            for stat_name, min_val in req["stats"].items():
                stat_lower = stat_name.lower()
                player_stat = 10
                if stat_lower in ["str", "strength"]:
                    player_stat = getattr(player, "effective_strength", player.strength)
                elif stat_lower in ["dex", "agi", "agility"]:
                    player_stat = getattr(player, "effective_agility", player.agility)
                elif stat_lower in ["int", "intelligence"]:
                    player_stat = getattr(player, "effective_intelligence", player.intelligence)
                elif stat_lower in ["wis", "wisdom"]:
                    player_stat = player.wisdom
                elif stat_lower in ["con", "constitution"]:
                    player_stat = getattr(player, "effective_constitution", player.constitution)
                elif stat_lower in ["cha", "luk", "luck"]:
                    player_stat = player.luck

                if player_stat < min_val:
                    return False, f"스탯 부족 ({stat_name} {min_val} 이상 필요, 현재: {player_stat})"

        # 3. Reputation check
        if "reputation" in req:
            for fac_name, req_rep in req["reputation"].items():
                curr_rep = player.reputation
                if curr_rep < req_rep:
                    return False, f"평판 부족 ({fac_name} 평판 {req_rep} 이상 필요, 현재: {curr_rep})"

        return True, "수락 가능"

    @classmethod
    def get_available_quests_for_location(cls, state: Any) -> List[Quest]:
        """Returns quests available from NPCs at the player's current location."""
        if not hasattr(state, "quests"):
            state.quests = {}

        if cls._templates_cache is None:
            cls.load_templates()

        curr_loc = state.current_location()
        present_npcs = curr_loc.npcs if curr_loc else []

        available = []
        for q_id, q_tmpl in (cls._templates_cache or {}).items():
            # If already in state and not available status, skip
            if q_id in state.quests and state.quests[q_id].status != "available":
                continue

            # Check if quest giver is present or giver is empty
            if q_tmpl.giver_npc_id and q_tmpl.giver_npc_id not in present_npcs:
                continue

            eligible, _ = cls.check_prerequisites(q_tmpl, state)
            if eligible:
                q_instance = copy.deepcopy(q_tmpl)
                q_instance.status = "available"
                available.append(q_instance)

        return available

    @classmethod
    def accept_quest(cls, state: Any, quest_id: str) -> Tuple[bool, str]:
        """Player accepts a quest. Transitions status to 'active'."""
        if not hasattr(state, "quests"):
            state.quests = {}

        quest = state.quests.get(quest_id) or cls.get_template(quest_id)
        if not quest:
            return False, f"존재하지 않는 퀘스트 ID: {quest_id}"

        if quest.status == "active":
            return False, f"이미 진행 중인 퀘스트입니다: '{quest.title}'"
        if quest.status == "completed":
            return False, f"이미 완료한 퀘스트입니다: '{quest.title}'"

        eligible, reason = cls.check_prerequisites(quest, state)
        if not eligible:
            return False, f"수락 불가: {reason}"

        quest.status = "active"
        quest.accepted_turn = state.turn
        quest.current_stage_idx = 0
        state.quests[quest.id] = quest

        return True, f"📜 [퀘스트 수락] '{quest.title}' 의뢰를 시작합니다!"

    @classmethod
    def progress_event(
        cls,
        state: Any,
        event_type: str,
        target_id: str,
        count: int = 1,
    ) -> List[str]:
        """
        Deterministic event hook called when player kills a monster, picks up an item,
        talks to an NPC, or enters a location.
        event_type: 'kill' | 'collect' | 'talk' | 'reach' | 'condition'
        Returns list of progress / completion notification messages in Korean.
        """
        if not hasattr(state, "quests") or not state.quests:
            return []

        logs = []
        target_lower = target_id.lower()

        for q_id, quest in list(state.quests.items()):
            if quest.status != "active":
                continue

            stage = quest.current_stage
            if stage and not stage.completed:
                # Match stage event
                type_matches = (stage.type == event_type) or (stage.type == "talk" and event_type == "talk")
                target_matches = (
                    stage.target.lower() in target_lower
                    or target_lower in stage.target.lower()
                    or stage.target == target_id
                )

                if type_matches and target_matches:
                    stage.current_count = min(stage.required_count, stage.current_count + count)
                    logs.append(
                        f"📜 [{quest.title}] 진행도 갱신: {stage.description_ko} ({stage.current_count}/{stage.required_count})"
                    )

                    # Stage completion check
                    if stage.current_count >= stage.required_count:
                        stage.completed = True
                        logs.append(f"✅ [{quest.title}] 단계 완료: {stage.description_ko}")

                        # Check if more stages remain
                        quest.current_stage_idx += 1
                        next_stage = quest.current_stage

                        if next_stage is not None:
                            logs.append(f"➡️ [{quest.title}] 다음 목표: {next_stage.description_ko}")
                        else:
                            # All stages complete! If no pending branch choices, finish quest
                            if not quest.branch_choices or quest.selected_choice_id:
                                complete_logs = cls.complete_quest(state, quest.id)
                                logs.extend(complete_logs)
                            else:
                                logs.append(
                                    f"⚖️ [{quest.title}] 모든 기본 목표 완료! 최종 분기 선택을 결정하십시오."
                                )

            # Also check optional objectives
            for opt in quest.optional_objectives:
                if not opt.completed and opt.type == event_type:
                    if opt.target.lower() in target_lower or target_lower in opt.target.lower():
                        opt.current_count = min(opt.required_count, opt.current_count + count)
                        if opt.current_count >= opt.required_count:
                            opt.completed = True
                            logs.append(f"⭐ [{quest.title}] 추가 보너스 목표 달성: {opt.description_ko}")

        return logs

    @classmethod
    def choose_branch(
        cls,
        state: Any,
        quest_id: str,
        choice_id: str,
    ) -> Tuple[bool, str, List[str]]:
        """
        Executes a branching narrative choice for an active quest.
        """
        if not hasattr(state, "quests") or quest_id not in state.quests:
            return False, "퀘스트를 찾을 수 없습니다.", []

        quest = state.quests[quest_id]
        if quest.status != "active":
            return False, "진행 중인 퀘스트가 아닙니다.", []

        choice = next((c for c in quest.branch_choices if c.choice_id == choice_id), None)
        if not choice:
            return False, f"유효하지 않은 선택지 ID: {choice_id}", []

        # Check choice requirements
        reqs = choice.requirements
        player = state.player

        if "gold_min" in reqs and player.gold < reqs["gold_min"]:
            return False, f"골드 부족 (필요: {reqs['gold_min']}G, 보유: {player.gold}G)", []

        if "stats" in reqs:
            for stat_name, val in reqs["stats"].items():
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
                    p_val = getattr(player, "effective_constitution", player.constitution)
                elif stat_lower in ["cha", "luk", "luck"]:
                    p_val = player.luck
                else:
                    p_val = getattr(player, stat_lower, 10)

                if p_val < val:
                    return False, f"스탯 부족 ({stat_name} {val} 필요)", []

        quest.selected_choice_id = choice_id
        logs = [f"⚖️ [{quest.title}] 분기 선택: '{choice.description_ko}'"]

        # Apply choice outcome
        outcome = choice.outcome
        if "stages" in outcome:
            new_stages = [QuestStage.from_dict(s) for s in outcome["stages"] if isinstance(s, dict)]
            quest.stages.extend(new_stages)
            logs.append(f"➡️ 새로운 분기 목표가 추가되었습니다: {quest.current_stage.description_ko if quest.current_stage else ''}")
        else:
            # Direct resolution of choice outcome rewards
            complete_logs = cls.complete_quest(state, quest_id, custom_rewards=outcome.get("rewards"), custom_factions=outcome.get("faction_impact"))
            logs.extend(complete_logs)

        return True, "분기 선택 완료", logs

    @classmethod
    def complete_quest(
        cls,
        state: Any,
        quest_id: str,
        custom_rewards: Optional[Dict[str, Any]] = None,
        custom_factions: Optional[Dict[str, int]] = None,
    ) -> List[str]:
        """
        Completes a quest deterministically, rewarding Player with Gold, EXP, Items,
        and adjusting Faction / World Reputation.
        """
        if not hasattr(state, "quests") or quest_id not in state.quests:
            return []

        quest = state.quests[quest_id]
        quest.status = "completed"
        quest.completed_turn = state.turn

        rewards = custom_rewards or quest.rewards
        faction_impact = custom_factions or quest.faction_impact
        player = state.player
        logs = [f"🎉 **[퀘스트 완료: {quest.title}]**"]

        # 1. Gold reward
        gold_gain = rewards.get("gold", 0)
        if gold_gain != 0:
            player.gold = max(0, player.gold + gold_gain)
            logs.append(f"💰 골드 {'+' if gold_gain > 0 else ''}{gold_gain}G (현재: {player.gold}G)")

        # 2. EXP reward
        exp_gain = rewards.get("exp", 0)
        if exp_gain > 0:
            player.exp += exp_gain
            logs.append(f"✨ 경험치 +{exp_gain} EXP (현재: {player.exp}/100)")
            while player.exp >= 100:
                player.exp -= 100
                player.level += 1
                player.max_health += 10
                player.health = player.max_health
                player.stat_points += 2
                logs.append(f"🏆 레벨 업! 현재 레벨: Lv.{player.level}")

        # 3. Item rewards
        item_ids = rewards.get("items", [])
        for item_id in item_ids:
            if item_id in state.items:
                item = state.items[item_id]
                item.location = "inventory"
                if item_id not in player.inventory:
                    player.inventory.append(item_id)
                logs.append(f"🎁 보상 아이템 획득: [{item.name}]")
            else:
                # Create basic item entry if missing
                from src.world.state import Item
                new_item = Item(id=item_id, name=item_id, description="퀘스트 보상 물품", location="inventory")
                state.items[item_id] = new_item
                player.inventory.append(item_id)
                logs.append(f"🎁 보상 아이템 획득: [{new_item.name}]")

        # 4. Reputation & Faction impacts
        rep_gain = rewards.get("reputation", 0)
        if rep_gain != 0:
            player.reputation = max(-100, min(100, player.reputation + rep_gain))
            logs.append(f"👑 명성/평판 {'+' if rep_gain > 0 else ''}{rep_gain} (현재: {player.reputation})")

        for fac_id, fac_delta in faction_impact.items():
            if hasattr(state, "apply_faction_ripple"):
                state.apply_faction_ripple(fac_id, fac_delta, f"퀘스트 [{quest.title}] 완수")
            logs.append(f"🏛️ 세력 영향 [{fac_id}]: {'+' if fac_delta > 0 else ''}{fac_delta}")

        # 5. Optional bonus rewards
        for opt in quest.optional_objectives:
            if opt.completed and opt.bonus_rewards:
                b_gold = opt.bonus_rewards.get("gold", 0)
                b_exp = opt.bonus_rewards.get("exp", 0)
                if b_gold > 0:
                    player.gold += b_gold
                    logs.append(f"⭐ 추가 보너스 골드: +{b_gold}G")
                if b_exp > 0:
                    player.exp += b_exp
                    logs.append(f"⭐ 추가 보너스 경험치: +{b_exp} EXP")

        return logs

    @classmethod
    def fail_quest(cls, state: Any, quest_id: str, reason: str = "") -> List[str]:
        """Fails a quest and applies penalties."""
        if not hasattr(state, "quests") or quest_id not in state.quests:
            return []

        quest = state.quests[quest_id]
        quest.status = "failed"
        penalty = quest.failure_penalty
        logs = [f"❌ **[퀘스트 실패: {quest.title}]** ({reason or '기한 초과 또는 실패'})"]

        rep_loss = penalty.get("reputation", 0)
        if rep_loss != 0:
            state.player.reputation = max(-100, min(100, state.player.reputation + rep_loss))
            logs.append(f"👑 평판 하락: {rep_loss} (현재: {state.player.reputation})")

        world_news = penalty.get("world_news")
        if world_news:
            state.pending_breaking_news.append(world_news)
            logs.append(f"📰 세계 정세 변화: '{world_news}'")

        return logs

    @classmethod
    def check_turn_time_limits(cls, state: Any, delta_minutes: int) -> List[str]:
        """Advances quest timers and triggers timeouts."""
        if not hasattr(state, "quests") or not state.quests:
            return []

        logs = []
        for q_id, quest in list(state.quests.items()):
            if quest.status != "active" or not quest.is_time_limited:
                continue

            quest.time_elapsed_minutes += delta_minutes
            if quest.time_elapsed_minutes >= quest.time_limit_minutes:
                fail_logs = cls.fail_quest(state, quest.id, reason="제한 시간 초과")
                logs.extend(fail_logs)
            elif quest.remaining_minutes <= 120 and quest.remaining_minutes > 0:
                logs.append(f"⏳ [마감 임박 경고] '{quest.title}' 마감까지 {quest.remaining_minutes}분 남았습니다!")

        return logs

    @classmethod
    def format_journal_html(cls, state: Any) -> str:
        """Renders rich, responsive HTML Quest Journal with category badges and stages."""
        if not hasattr(state, "quests"):
            state.quests = {}

        active_quests = [q for q in state.quests.values() if q.status == "active"]
        completed_quests = [q for q in state.quests.values() if q.status == "completed"]
        available_quests = cls.get_available_quests_for_location(state)

        category_ko = {
            "hunt": "⚔️ 토벌", "gather": "🌿 채집", "escort": "🛡️ 호위",
            "investigation": "🔍 조사", "delivery": "✉️ 배달", "rescue": "🤝 구조"
        }

        def render_quest_card(q: Quest, is_active: bool = True) -> str:
            cat_str = category_ko.get(q.category, "📜 임무")
            time_str = f"⏳ 남은 시간: {q.remaining_minutes // 60}시간 {q.remaining_minutes % 60}분" if q.is_time_limited else "⏳ 기한: 무제한"

            stage_lines = []
            for s in q.stages:
                check_box = "☑️" if s.completed else "⬜"
                prog_str = f" ({s.current_count}/{s.required_count})" if s.required_count > 1 else ""
                stage_lines.append(f"<li style='margin:2px 0;'>{check_box} {s.description_ko}{prog_str}</li>")

            reward_items = ", ".join(q.rewards.get("items", []))
            rewards_str = f"골드 {q.rewards.get('gold', 0)}G | EXP {q.rewards.get('exp', 0)}" + (f" | 아이템: {reward_items}" if reward_items else "")

            card_border = "#e2e8f0"
            if q.status == "active":
                card_border = "#3182ce"
            elif q.status == "completed":
                card_border = "#38a169"

            return f"""
            <div style="background:var(--panel-bg, #ffffff); border:1px solid {card_border}; border-radius:6px; padding:12px; margin-bottom:10px; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span style="font-weight:bold; font-size:14px; color:#1a202c;">[{cat_str}] {q.title}</span>
                <span style="font-size:11px; color:#718096;">{time_str}</span>
              </div>
              <p style="font-size:12px; color:#4a5568; margin:0 0 8px 0; line-height:1.4;">{q.description}</p>
              <ul style="font-size:12px; color:#2d3748; padding-left:18px; margin:0 0 8px 0;">
                {''.join(stage_lines)}
              </ul>
              <div style="font-size:11px; color:#4a5568; border-top:1px dashed #e2e8f0; padding-top:6px;">
                🎁 <b>완료 보상:</b> {rewards_str}
              </div>
            </div>
            """

        html_parts = ["<div class='qt-journal-panel' style='padding:8px;'>"]

        # Active Quests Section
        html_parts.append("<h4 style='margin:8px 0 6px 0; color:#2b6cb0; font-size:14px;'>📌 진행 중인 퀘스트</h4>")
        if active_quests:
            for q in active_quests:
                html_parts.append(render_quest_card(q, is_active=True))
        else:
            html_parts.append("<div style='font-size:12px; color:#a0aec0; margin-bottom:12px;'>현재 진행 중인 퀘스트가 없습니다.</div>")

        # Available Quests Section
        html_parts.append("<h4 style='margin:12px 0 6px 0; color:#4a5568; font-size:14px;'>📜 현재 장소에서 수락 가능한 의뢰</h4>")
        if available_quests:
            for q in available_quests:
                html_parts.append(render_quest_card(q, is_active=False))
        else:
            html_parts.append("<div style='font-size:12px; color:#a0aec0; margin-bottom:12px;'>현재 위치에서 받을 수 있는 새로운 의뢰가 없습니다.</div>")

        # Completed Quests count summary
        if completed_quests:
            html_parts.append(f"<div style='font-size:12px; color:#38a169; margin-top:8px;'>✨ 완료된 의뢰 총 {len(completed_quests)}건</div>")

        html_parts.append("</div>")
        return "".join(html_parts)

    @classmethod
    def format_prompt_context(cls, state: Any) -> str:
        """Formats active quest objectives for GM dynamic prompt injection."""
        if not hasattr(state, "quests") or not state.quests:
            return ""

        active_quests = [q for q in state.quests.values() if q.status == "active"]
        if not active_quests:
            return ""

        lines = ["[📜 현재 진행 중인 퀘스트 목표 (ACTIVE QUEST OBJECTIVES)]"]
        for q in active_quests:
            stage = q.current_stage
            stage_desc = stage.description_ko if stage else "모든 기본 목표 완료 (최종 분기 선택 대기)"
            prog = f" ({stage.current_count}/{stage.required_count})" if stage and stage.required_count > 1 else ""
            time_warning = f" | ⚠️ 남은 시간: {q.remaining_minutes}분" if q.is_time_limited else ""
            lines.append(f"- **[{q.title}]** 현재 목표: {stage_desc}{prog}{time_warning}")

        return "\n".join(lines)
