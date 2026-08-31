# Quilltale TRPG Engine - AI Developer & GM Rules

## 1. Core Mission & Philosophy
- **Anti-Yes-Man Rule:** Do not be an agreeable 'yes-man'. The player is a grounded mortal character. Absurd, power-scaling, or impossible actions must realistically fail.
- **Deterministic Truth (WorldState):** The JSON `WorldState` is the single source of truth. LLM narration must never contradict recorded facts, stats, locations, or items.
- **100% Korean Player-Facing UI:** All text shown to the player (narration, NPC dialogue, item names, stats, location names, UI status) must be in natural, atmospheric Korean. Internal codes/data keys can be in English.

## 2. Memory & RAG Architecture
- **Episodic & Long-term Memory:** Use a hybrid architecture of JSON WorldState + Local RAG (Qdrant & Jina Embeddings).
- **5-Scale Significance:** Memory entries use a 1-5 scale. Level 4-5 memories represent world-shaping events and are anchored for permanent retention.
- **Reputation & Rumors:** Global world facts and player reputation affect NPC initial disposition across locations.

## 3. Strict Dice & Stat Rules
- Combat and skill checks are resolved through deterministic Python mechanics (d20 + stat modifier vs DC). LLMs describe the narrative outcome based on the deterministic roll result.

## 4. Magic Language & Skill Book Rules
- **Korean Pronunciation for Ancient Words (怨좊????쒓? 諛쒖쓬 ?쒓린 ?먯튃):** All ancient magic vocabulary words must be written in Korean phonetic transcriptions with their conceptual roles (e.g. `諛붾Ⅴ(諛쒗솕/?댁뿉?덉?)`, `移대Ⅴ(媛뺤젣/臾쇰━?대룞)`, `?닿렇?덉뒪(?붿뿼)`), NEVER in raw Latin/English alphabets (`barre`, `motus`, etc.).
- **Skill Book UI & No-Spoiler Formula:** The skill book header must maintain the crisp 2-tier white/high-contrast layout. Magic combination tips must only show the abstract formula `[?먯냼] + [?뺥깭] + [湲곕룞]` without concrete spoiler examples so players can discover spell combinations themselves.

## 5. Storytelling & World Reactivity Rules
- **No Invisible Walls (?щ챸 踰?湲덉?):** ?뚮젅?댁뼱???대룞怨??좏깮??媛뺤젣濡?留됱? ?딅뒗?? 臾댁“嫄댁쟻??吏??泥대쪟 媛뺤슂??湲덉??쒕떎.
- **Strict Causality & Butterfly Effect (泥좎????멸낵?④낵 ?섎퉬?④낵):** ?뚮젅?댁뼱媛 ?섏뒪?몃? 臾댁떆?섍굅???ㅻⅨ 吏??쑝濡??좊굹硫? ?쒓컙???먮쫫???곕씪 洹?諛⑹튂???ш굔? 媛李??놁씠 ?낇솕?쒕떎(留덉쓣 ?뚭눼, NPC ?щ쭩 ??. ?좏깮怨?諛⑷??먮뒗 諛섎뱶???꾩떎?곸씤 ?媛媛 ?곕Ⅸ??
- **NPC Independence (NPC ?낆옄???앺깭怨?:** NPC???섏뒪???먰뙋湲곌? ?꾨땲?? ?뚮젅?댁뼱媛 ??蹂??뚮룄 媛곸옄???뺣쭩怨???꾨씪?몄뿉 ?곕씪 ?諛???吏곸씠硫? ?뚮줈???뚮젅?댁뼱???ㅽ넻?섎? 移섍굅??紐⑺몴? 異⑸룎?쒕떎.
- **Dilemmas & Flawed Victories (?쒕젅留덉? 遺덉셿?꾪븳 ?밸━):** ?덈????덈??? ?꾨꼍???댄뵾?붾뵫??吏?묓븳?? ?뺣떟 ?녿뒗 ?ㅻ━???쒕젅留덈? 媛뺤슂?섍퀬, 臾댁뼵媛瑜??살쑝硫??ㅻⅨ 寃껋쓣 ?껊뒗 ?곸벝???ъ슫???④릿??
- **Micro & Macro Blend (誘몄떆? 嫄곗떆??援먯감):** 嫄곕???硫몃쭩???꾪삊? 諛곌꼍(?먭꼍)?쇰줈 源붿븘?먭퀬, ?뱀옣??紐⑺몴??'?숈깮 李얘린', '媛蹂??뚯닔' ??吏洹뱁엳 媛쒖씤?곸씠怨?諛???믪? ?ш굔??吏묒쨷?쒗궓 ???먯쭊?곸쑝濡??ㅼ??쇱쓣 ??뼱?몃떎.
- **Resource & Physical Constraints:** ?κ굅由??대룞 ???쇰줈?? ?앸웾 ?뚮え, ?좎뵪 蹂????臾쇰━???쒖빟???꾧꺽???곸슜?쒕떎. 鍮좊Ⅸ ?대룞??吏?묓븯怨??앹〈??臾닿쾶瑜?遺?ы븳??
- **Failing Forward (?섎? ?덈뒗 ?ㅽ뙣):** 二쇱궗???먯젙 ?ㅽ뙣 ??"?꾨Т ?쇰룄 ?놁뿀??濡??섍린吏 ?딅뒗?? ?곹솴 ?낇솕???덈줈???꾪삊(臾닿린 ?뚯넀, ?뚯쓬 諛쒖깮 ???쇰줈 ?댁뼱吏寃?臾섏궗?쒕떎.
- **NPC Consistency:** NPC???쇨????깃꺽怨??쒕룄瑜??좎??댁빞 ?섎ŉ, ?좎??먭쾶 臾댁“嫄??몄쓽瑜?踰좏?嫄곕굹 ?뺣낫 ?먰뙋湲곗쿂??援댁? ?딅뒗??
- **Dynamic Focalization (상황적 시야 제한 및 오감 극대화): 내러티브 묘사는 플레이어의 상태를 반영한다. 1. 전투/도주는 시야가 좁아져 생존 직결 요소만 거칠게 묘사. 2. 잠입/긴장 상태는 오감(청각, 후각, 촉각)을 극도로 예민하게 미친 디테일로 묘사. 3. 여유로운 탐색은 넓고 세밀하게 묘사. 객관식 선택지 금지.
