import re

with open('C:/Quilltale/src/agents/prompts.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if 'Incantation' in line and '###' in line:
        start_idx = i
        break

if start_idx != -1:
    for i in range(start_idx + 1, len(lines)):
        if line.startswith('### ['):
            end_idx = i
            break
        # Sometimes there might be a match with just '###'
        if lines[i].strip().startswith('###'):
            end_idx = i
            break

if start_idx != -1 and end_idx != -1:
    magic_rules_lines = lines[start_idx:end_idx]
    magic_rules_str = "".join(magic_rules_lines)
    
    # Remove these lines from original
    del lines[start_idx:end_idx]
    
    # Write back
    with open('C:/Quilltale/src/agents/prompts.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
        f.write('\n\nMAGIC_SYSTEM_PROMPT = """\n')
        f.write(magic_rules_str.strip())
        f.write('\n"""\n')
    print(f"Extracted from line {start_idx} to {end_idx}")
else:
    print(f"Could not find boundaries. start={start_idx}, end={end_idx}")
