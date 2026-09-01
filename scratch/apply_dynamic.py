import re

with open('C:/Quilltale/src/agents/game_master.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = """        prompt = GM_TURN_PROMPT_TEMPLATE.format(
            environmental_anchoring=environmental_anchoring,
            npc_bdi_context=npc_bdi_context,
            world_context=state.to_context_summary(),
            map_context=state.to_map_summary(),
            off_screen_context=off_screen_context,
            skills_context=self._format_skills_context(state),
            titles_context=self._format_titles_context(state),
            rag_memory_context=rag_context,
            graph_context=graph_context,
            dice_roll_context=dice_context,
            interrupt_context=interrupt_context,
            incant_context=incant_context,
            recent_history=recent_history_str,
            parsed_action_summary=parsed_action_summary,
            action=action,
        )"""

replacement = """        # --- DYNAMIC INJECTION LOGIC ---
        action_str = action.lower() if action else ""
        
        # 1. Skills
        skill_names = [s.name.lower() for s in state.player.skills] if state.player.skills else []
        uses_skill = any(sn in action_str for sn in skill_names) or any(k in action_str for k in ["공격", "마법", "스킬", "사용", "영창", "주문", "때린다", "베기", "쏜다"])
        dyn_skills = self._format_skills_context(state) if uses_skill else ""
        
        # 2. Titles (Social Interaction)
        social_keywords = ["대화", "인사", "위협", "묻다", "질문", "말한다", "설득", "다가간다", "바라본다", "npc"]
        is_social = any(k in action_str for k in social_keywords)
        dyn_titles = self._format_titles_context(state) if is_social else ""
        
        # 3. World Context (Lore/Rumors)
        lore_keywords = ["소문", "역사", "흔적", "조사", "책", "문자", "묻다", "주변", "기록", "살핀다", "단서"]
        is_lore = any(k in action_str for k in lore_keywords)
        dyn_world = state.to_context_summary() if is_lore else ""
        
        # 4. Off-screen
        is_travel = any(k in action_str for k in ["이동", "간다", "도착", "들어간다", "나간다"])
        dyn_off_screen = off_screen_context if (is_social or is_travel) else ""
        
        # 5. Graph / Ecosystem
        graph_keywords = ["이동", "지도", "세력", "생태", "흔적", "주변", "탐색", "관찰"]
        is_graph = any(k in action_str for k in graph_keywords)
        dyn_graph = graph_context if is_graph else ""
        
        prompt = GM_TURN_PROMPT_TEMPLATE.format(
            environmental_anchoring=environmental_anchoring,
            npc_bdi_context=npc_bdi_context,
            world_context=dyn_world,
            map_context=state.to_map_summary(),
            off_screen_context=dyn_off_screen,
            skills_context=dyn_skills,
            titles_context=dyn_titles,
            rag_memory_context=rag_context,
            graph_context=dyn_graph,
            dice_roll_context=dice_context,
            interrupt_context=interrupt_context,
            incant_context=incant_context,
            recent_history=recent_history_str,
            parsed_action_summary=parsed_action_summary,
            action=action,
        )"""

text = text.replace(target, replacement)

with open('C:/Quilltale/src/agents/game_master.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Dynamic injection applied successfully.")
