import re

with open('C:/Quilltale/src/agents/game_master.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the specific line in process_turn
target = 'dynamic_system_prompt = GM_SYSTEM_PROMPT + "\\n" + self._scenario_manager.get_prompt_injection(state)'

replacement = '''dynamic_system_prompt = GM_SYSTEM_PROMPT + "\\n" + self._scenario_manager.get_prompt_injection(state)
        
        magic_keywords = ["마법", "영창", "주문", "캐스팅", "마나", "원소", "형태", "기동"]
        is_magic = any(k in action for k in magic_keywords) if action else False
        if is_magic:
            from src.agents.prompts import MAGIC_SYSTEM_PROMPT
            dynamic_system_prompt += "\\n\\n" + MAGIC_SYSTEM_PROMPT
'''

# Note: there are two occurrences. One in process_turn, one in process_opening.
# We will only apply it where 'action' variable exists (process_turn).
# So we use a regex that matches the try block in process_turn.

# Let's just do a simple replacement for all, but for process_opening action is not defined.
# We need to make sure we don't break process_opening.
# In process_opening, there is no `action` variable. We can just catch NameError.
replacement_safe = '''dynamic_system_prompt = GM_SYSTEM_PROMPT + "\\n" + self._scenario_manager.get_prompt_injection(state)
            try:
                action_text = action if "action" in locals() else ""
                magic_keywords = ["마법", "영창", "주문", "캐스팅", "마나", "원소", "형태", "기동"]
                if any(k in action_text for k in magic_keywords):
                    from src.agents.prompts import MAGIC_SYSTEM_PROMPT
                    dynamic_system_prompt += "\\n\\n" + MAGIC_SYSTEM_PROMPT
            except Exception:
                pass
'''

text = text.replace(target, replacement_safe)

with open('C:/Quilltale/src/agents/game_master.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("game_master.py updated.")
