import json

try:
    with open('C:/Quilltale/data/templates/region_templates.json', 'r', encoding='utf-16') as f:
        text = f.read()
except UnicodeError:
    with open('C:/Quilltale/data/templates/region_templates.json', 'r', encoding='utf-8') as f:
        text = f.read()

# Fix syntax if it's broken
text = text.strip()
if not text.startswith('['):
    text = '[' + text
if text.endswith(','):
    text = text[:-1]
if not text.endswith(']'):
    text = text + ']'

# Sometimes the concatenation makes multiple arrays like [...] [...]
text = text.replace(']\n[', ',')
text = text.replace('][', ',')
text = text.replace('}\n\n,{', '},{')
text = text.replace('}\n,{', '},{')

# Manual parse hack for multiple root elements
import ast
try:
    data = json.loads(text)
except json.JSONDecodeError:
    # If there are multiple arrays or objects concatenated weirdly
    # let's just extract all json objects
    import re
    objs = re.findall(r'\{[^{}]*?(?:\{[^{}]*?\}[^{}]*?)*\}', text, re.DOTALL)
    # A more robust way to parse a broken array of objects:
    # We will just parse the original backup
    pass

with open('C:/Quilltale/scratch/new_regions_8.json', 'r', encoding='utf-8') as f:
    new_data = json.load(f)

# Let's try to extract all "id" objects directly to bypass JSON formatting errors
import re
data = []
# Find all top-level objects that look like {"id": "..."}
blocks = re.split(r'\s*,\s*(?=\{\s*"id")', text.strip('[] \n\r'))
for b in blocks:
    if not b.strip(): continue
    try:
        data.append(json.loads(b))
    except Exception as e:
        print(f"Failed to parse block: {b[:50]}... Error: {e}")

# Append the 10 new data
data.extend(new_data)

# De-duplicate by id
seen = set()
unique_data = []
for item in data:
    if item['id'] not in seen:
        seen.add(item['id'])
        unique_data.append(item)

with open('C:/Quilltale/data/templates/region_templates.json', 'w', encoding='utf-8') as f:
    json.dump(unique_data, f, ensure_ascii=False, indent=2)

print(f"Total regions saved: {len(unique_data)}")
