import json
import random
from pathlib import Path
from typing import Dict, Any, Optional
from src.world.state import WorldState

class ScenarioManager:
    def __init__(self, templates_path: str = "data/templates/scenario_templates.json"):
        self.templates_path = Path(templates_path)
        self.scenarios: Dict[str, Any] = {}
        self._load_templates()
        
    def _load_templates(self):
        if not self.templates_path.exists():
            return
        with open(self.templates_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for sc in data:
                if "id" in sc:
                    self.scenarios[sc["id"]] = sc

    def start_random_scenario(self, world_state: WorldState) -> str:
        if not self.scenarios:
            return ""
        scenario_id = random.choice(list(self.scenarios.keys()))
        world_state.current_scenario_id = scenario_id
        world_state.current_scenario_act = "act_1_hook_and_misdirection"
        return scenario_id

    def advance_scenario(self, world_state: WorldState, success: bool = True) -> str:
        current_id = world_state.current_scenario_id
        current_act = world_state.current_scenario_act
        
        if not current_id or current_id not in self.scenarios:
            return self.start_random_scenario(world_state)

        # Act progression logic
        acts = [
            "act_1_hook_and_misdirection",
            "act_2_escalation_and_webs",
            "act_3_false_climax_and_despair",
            "act_4_dilemma_and_sacrifice"
        ]
        
        try:
            current_index = acts.index(current_act)
            if current_index < len(acts) - 1:
                # Move to next act
                world_state.current_scenario_act = acts[current_index + 1]
                return current_id
        except ValueError:
            pass # Invalid act, move to next scenario directly

        # Epilogue reached, load next scenario
        sc = self.scenarios[current_id]
        hooks = sc.get("next_campaign_hooks", {})
        
        next_id = None
        if hooks:
            next_id = hooks.get("if_success") if success else hooks.get("if_failure")
        
        # If no valid next_id is found, pick randomly
        if next_id and next_id in self.scenarios:
            world_state.current_scenario_id = next_id
        else:
            self.start_random_scenario(world_state)
            
        world_state.current_scenario_act = "act_1_hook_and_misdirection"
        return world_state.current_scenario_id

    def get_prompt_injection(self, world_state: WorldState) -> str:
        current_id = world_state.current_scenario_id
        current_act = world_state.current_scenario_act
        
        if not current_id or current_id not in self.scenarios:
            return "[NO ACTIVE SCENARIO DIRECTIVE]"
            
        sc = self.scenarios[current_id]
        meta = sc.get("meta_setup", {})
        act_data = sc.get(current_act, {})
        
        injection = f"\n=== [CURRENT SCENARIO DIRECTIVE: {current_id}] ===\n"
        injection += f"TITLE: {meta.get('scenario_title', 'Unknown')}\n"
        injection += f"THEME: {', '.join(meta.get('theme_tags', []))}\n"
        injection += f"ATMOSPHERE: {meta.get('atmosphere', '')}\n"
        injection += f"CURRENT STAGE: {current_act.upper().replace('_', ' ')}\n\n"
        injection += "[STAGE DETAILS]\n"
        
        for k, v in act_data.items():
            if isinstance(v, list):
                injection += f"- {k.upper()}:\n"
                if len(v) > 0 and isinstance(v[0], dict):
                    for item in v:
                        injection += f"  * {item.get('faction_name', 'Faction')}: {item.get('hidden_motive', '')}\n"
                else:
                    for item in v:
                        injection += f"  * {item}\n"
            else:
                injection += f"- {k.upper()}: {v}\n"
                
        injection += "\n(GM INSTRUCTION: Guide the narrative strictly towards fulfilling the conditions of this stage. Emphasize the ATMOSPHERE.)\n"
        injection += "================================================\n"
        return injection
