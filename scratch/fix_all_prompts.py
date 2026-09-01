import re

with open('C:/Quilltale/src/agents/prompts.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix failing forward
text = re.sub(
    r'무기가 부러지거나, 적의 증원이 오거나, 함정이 작동하는 등 상황을 최악으로 치닫게 만드십시오\.',
    '단, 무조건 최악의 재앙을 묘사하지 말고 소음 발생, 시간 낭비, 체력 소모를 동반한 부분적 성공 등 개연성 있고 현실적인 결과를 묘사하십시오.',
    text
)

# 2. Fix Dynamic Focalization
text = re.sub(
    r'객관식 선택지 제시는 절대 금지입니다\. 플레이어의 \'현재 심리/신체 상태\'에 맞춰 묘사를 변주하십시오\.',
    '플레이어의 \'현재 심리/신체 상태\'에 맞춰 묘사를 변주하십시오.',
    text
)
text = re.sub(
    r'생존에 직결된 요소\(무기 궤적, 숨소리\)만 짧고 거칠게 묘사 \(시야 좁아짐\)\.',
    '생존에 직결된 요소와 전술적 지형지물(엄폐물, 폭발물, 함정 등)을 빠르고 날카롭게 묘사하여 자유도와 전략성을 부여하십시오.',
    text
)
text = re.sub(
    r'상황적 시야 제한 및 오감 극대화',
    '상황적 오감 극대화',
    text
)

# 3. Fix Multiple Choice duplication
text = re.sub(
    r'모든 서사\(narration\) 마지막에 \'당신의 선택지 A, B, C\'와 같은 인위적인 객관식 선택지 목록을 나열하지 마십시오\.\n플레이어가 주어진 보기의 텍스트 의도에 갇히지 않고, 오롯이 자신의 직관과 창의적 판단으로 다음 행동을 선언할 수 있도록 상황의 현장감과 긴장감만 생생하게 묘사하고 열린 결말의 문장으로 맺으십시오\.',
    '모든 서사(narration) 마지막에 선택지(A, B, C) 목록을 절대 나열하지 마십시오. 상황의 현장감과 긴장감만 묘사하고 자연스러운 서사로 끝맺어 플레이어의 창의적 판단을 유도하십시오.',
    text
)

text = re.sub(
    r'인위적인 객관식 선택지는 절대 배열하지 말고, 현장 분위기와 인물의 반응을 생생하게 묘사하십시오\.',
    '현장 분위기와 인물의 반응을 생생하게 묘사하십시오.',
    text
)

# 4. Extract Incantation rules
lines = text.split('\n')
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if 'Incantation' in line and '###' in line:
        start_idx = i
        break

if start_idx != -1:
    for i in range(start_idx + 1, len(lines)):
        if lines[i].strip().startswith('###'):
            end_idx = i
            break

if start_idx != -1 and end_idx != -1:
    magic_rules_lines = lines[start_idx:end_idx]
    magic_rules_str = "\n".join(magic_rules_lines)
    
    # Remove these lines from original
    del lines[start_idx:end_idx]
    
    # Write back
    with open('C:/Quilltale/src/agents/prompts.py', 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
        f.write('\n\nMAGIC_SYSTEM_PROMPT = """\n')
        f.write(magic_rules_str.strip())
        f.write('\n"""\n')
    print(f"Extraction successful: lines {start_idx} to {end_idx}")
else:
    print(f"Extraction failed: {start_idx}, {end_idx}")
