"""
Quilltale Distributed Batch Data Collector.
Runs multi-persona, multi-account automated play sessions and merges high-quality logs into training datasets.
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.world.state import WorldState
from src.world.generator import WorldGenerator
from src.agents.game_master import GameMasterAgent
from src.agents.player_bot import PlayerBotAgent
from src.llm.gemini import GeminiLLM
from src.llm.resilience import JSONRepairEngine


def run_single_collector_worker(
    worker_name: str,
    api_key: str,
    persona: str,
    turns: int,
    output_log_path: Path
) -> List[Dict[str, Any]]:
    """Runs an automated play session for a specific persona and records clean turn data."""
    print(f"\n=======================================================")
    print(f"🚀 [워커 시작: {worker_name}] 성향: {persona} | 목표: {turns}턴")
    print(f"=======================================================")

    # Initialize Gemini LLM with specific API key
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
    try:
        gm_llm = GeminiLLM(api_key=api_key)
        bot_llm = GeminiLLM(api_key=api_key)
    except TypeError:
        gm_llm = GeminiLLM()
        bot_llm = GeminiLLM()

    gm = GameMasterAgent(llm=gm_llm)
    state = gm.generate_new_game()
    bot = PlayerBotAgent(llm=bot_llm, persona_key=persona)

    # 1. Opening
    opening = gm.generate_opening(state)
    recent_narr = opening.get("narration", "")
    print(f"[{worker_name}] 오프닝 생성 완료: {recent_narr[:60]}...")

    recorded_turns: List[Dict[str, Any]] = []

    for t in range(1, turns + 1):
        try:
            loc = state.current_location()
            loc_name = loc.name if loc else "미지의 장소"

            bot_action = bot.decide_action(state, recent_narration=recent_narr)
            turn_start = time.time()
            result = gm.process_turn(bot_action, state)
            elapsed = time.time() - turn_start

            clean_narr = JSONRepairEngine.extract_clean_prose(result.get("narration", ""))
            recent_narr = clean_narr

            turn_record = {
                "worker": worker_name,
                "persona": persona,
                "turn": t,
                "location": loc_name,
                "player_action": bot_action,
                "gm_narration": clean_narr,
                "dice_result": result.get("dice_result"),
                "changes_applied": result.get("changes_applied", []),
                "elapsed_sec": round(elapsed, 2)
            }
            recorded_turns.append(turn_record)

            print(f"[{worker_name} T{t}/{turns}] 🏰 {loc_name} | 🤖 행동: {bot_action[:30]}... | ⏱️ {elapsed:.2f}s")
            time.sleep(0.5)
        except Exception as e:
            print(f"\n⚠️ [{worker_name}] 턴 {t} 진행 중 일시 정지 (토큰 소진 또는 네트워크): {e}")
            print(f"[{worker_name}] 지금까지 진행된 {len(recorded_turns)}개 턴을 안전하게 저장하고 다음 단계로 진행합니다.")
            break

    # Save worker raw log
    output_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_log_path, "w", encoding="utf-8") as f:
        json.dump(recorded_turns, f, ensure_ascii=False, indent=2)

    print(f"✅ [{worker_name}] 완료! {len(recorded_turns)}개 턴 로그 저장됨 -> {output_log_path}")
    return recorded_turns


def convert_logs_to_finetune_dataset(all_turn_logs: List[Dict[str, Any]], dataset_output_path: Path):
    """Converts recorded turns into Gemini & Qwen fine-tuning JSONL format (Instruction / Response)."""
    dataset_output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0

    with open(dataset_output_path, "w", encoding="utf-8") as f:
        for t in all_turn_logs:
            action = t.get("player_action", "").strip()
            narration = t.get("gm_narration", "").strip()

            # Filter out overly short or corrupted turns
            if len(action) < 3 or len(narration) < 40:
                continue

            # Standard instruction-response pair for Fine-Tuning
            item = {
                "system_instruction": "당신은 100% 한국어로 묘사하는 정통 다크 판타지 TRPG의 전속 게임 마스터(GM)입니다. 플레이어의 선언에 맞춰 사실적이고 몰입감 넘치는 서사를 작성하십시오.",
                "user_input": f"[위치: {t.get('location')}] 플레이어 행동: {action}",
                "model_output": narration
            }
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            count += 1

    print(f"\n🎉 [최종 합체 데이터셋 생성 완료] 총 {count}개의 고품질 학습 데이터 추출 -> {dataset_output_path}")


def main():
    parser = argparse.ArgumentParser(description="Quilltale Distributed Batch Collector")
    parser.add_argument("--key1", type=str, default="", help="Gemini API Key for Warrior")
    parser.add_argument("--key2", type=str, default="", help="Gemini API Key for Mage")
    parser.add_argument("--key3", type=str, default="", help="Gemini API Key for Rogue")
    parser.add_argument("--turns", type=int, default=10, help="Turns per persona worker")
    args = parser.parse_args()

    # Use env fallback if keys omitted
    default_key = os.environ.get("GEMINI_API_KEY", "")
    k1 = args.key1 or default_key
    k2 = args.key2 or default_key
    k3 = args.key3 or default_key

    all_logs = []
    log_dir = Path("data/collector_logs")

    # Worker 1: Warrior
    if k1:
        w1_logs = run_single_collector_worker("전사_Worker1", k1, "aggressive_warrior", args.turns, log_dir / "warrior_logs.json")
        all_logs.extend(w1_logs)

    # Worker 2: Mage
    if k2:
        w2_logs = run_single_collector_worker("마법사_Worker2", k2, "cautious_mage", args.turns, log_dir / "mage_logs.json")
        all_logs.extend(w2_logs)

    # Worker 3: Rogue
    if k3:
        w3_logs = run_single_collector_worker("도적_Worker3", k3, "shadow_rogue", args.turns, log_dir / "rogue_logs.json")
        all_logs.extend(w3_logs)

    # Merge all into final dataset
    final_dataset_path = Path("data/dataset_master_combined.jsonl")
    convert_logs_to_finetune_dataset(all_logs, final_dataset_path)


if __name__ == "__main__":
    main()
