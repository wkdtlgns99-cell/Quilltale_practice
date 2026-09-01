import re

with open('C:/Quilltale/src/agents/prompts.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Look for the section starting with '### [마법' and ending at the next '### ['
match = re.search(r'(### \[마법 영창\(Incantation\) & 기적 체계\].*?)(?=\n### \[)', text, flags=re.DOTALL)

if match:
    magic_rules = match.group(1)
    
    # Remove from original text
    new_text = text.replace(magic_rules, '')
    
    # Append as a new variable
    new_text += '\n\nMAGIC_SYSTEM_PROMPT = """\n' + magic_rules.strip() + '\n"""\n'
    
    with open('C:/Quilltale/src/agents/prompts.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print('Extraction successful.')
else:
    print('Magic rules section not found again.')
