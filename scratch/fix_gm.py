import re

with open('C:/Quilltale/src/agents/game_master.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the specific dice_context line
text = re.sub(
    r'dice_context = "\[.*?\]\\n.*?\(별도 주사위 판정 없음\)"',
    'dice_context = ""',
    text
)

# And remove it if it was written in single quotes or formatted differently
text = re.sub(
    r'dice_context = "\[이번 주사위 판정\]\\n일상적인 탐색/대화 행동 \(별도 주사위 판정 없음\)"',
    'dice_context = ""',
    text
)

with open('C:/Quilltale/src/agents/game_master.py', 'w', encoding='utf-8') as f:
    f.write(text)
