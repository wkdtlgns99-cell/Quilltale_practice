"""
Quilltale AI Data Refiner (Data Laundry / Distillation Pipeline).
Takes raw, rough local TRPG logs and uses Gemini to rewrite them into pristine literary dark fantasy masterpieces.
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.llm.gemini import GeminiLLM
from src.llm.resilience import JSONRepairEngine


REFINER_PROMPT = """
당신은 최고 수준의 다크 판타지 소설 작가이자 TRPG 마스터입니다.
아래에 제공되는 [로컬 TRPG 플레이 뼈대 기록]을 읽고, 사건의 인과관계와 사실을 그대로 유지하면서
공백 제외 300~500자 분량의 유려하고 생생한 감각 묘사(오감, 긴장감, 문학적 필체)가 담긴 최고급 한국어 GM 서사로 다시 작성(윤문)하십시오.

[로컬 TRPG 플레이 뼈대 기록]
- 위치: {location}
- 플레이어 행동: {action}
- 주사위/시스템 결과: {dice}
- 기존 투박한 묘사: {raw_narration}

[지침]
1. 객관식 선택지나 시스템 괄호 없이 오직 순수한 소설 서사 본문만 출력하십시오.
2. 다른 말은 일절 붙이지 말고, 완성된 한국어 서사 텍스트만 그대로 반환하십시오.
"""


def refine_raw_logs_with_gemini(
    raw_logs_path: Path,
    output_dataset_path: Path,
    api_key: str = "",
    max_items: int = 100
) -> int:
    """Reads raw local logs, washes them with Gemini, and outputs clean fine-tuning JSONL."""
    if not raw_logs_path.exists():
        print(f"❌ 원본 로그 파일을 찾을 수 없습니다: {raw_logs_path}")
        return 0

    with open(raw_logs_path, "r", encoding="utf-8") as f:
        logs = json.load(f)

    gemini = GeminiLLM(api_key=api_key or os.environ.get("GEMINI_API_KEY", ""))
    output_dataset_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n=======================================================")
    print(f"🧼 [AI 데이터 세탁기 가동] 총 {min(len(logs), max_items)}개 턴을 최고급 문체로 윤문합니다...")
    print(f"=======================================================\n")

    refined_count = 0
    with open(output_dataset_path, "w", encoding="utf-8") as out_f:
        for idx, item in enumerate(logs[:max_items], 1):
            action = item.get("player_action", "")
            raw_narr = item.get("gm_narration", "")
            loc = item.get("location", "미지의 장소")
            dice = item.get("dice_result", {}).get("summary_ko", "일반 판정") if item.get("dice_result") else "일반 행동"

            if len(action) < 3:
                continue

            prompt = REFINER_PROMPT.format(
                location=loc,
                action=action,
                dice=dice,
                raw_narration=raw_narr
            )

            try:
                resp = gemini.generate(prompt)
                washed_text = JSONRepairEngine.extract_clean_prose(resp.text if hasattr(resp, "text") else str(resp))

                fine_tune_entry = {
                    "system_instruction": "당신은 100% 한국어로 묘사하는 정통 다크 판타지 TRPG의 전속 게임 마스터(GM)입니다. 플레이어의 선언에 맞춰 사실적이고 몰입감 넘치는 서사를 작성하십시오.",
                    "user_input": f"[위치: {loc}] 플레이어 행동: {action}",
                    "model_output": washed_text
                }
                out_f.write(json.dumps(fine_tune_entry, ensure_ascii=False) + "\n")
                refined_count += 1

                print(f"[{idx}/{min(len(logs), max_items)}] 🧼 윤문 완료 -> {washed_text[:40]}...")
                time.sleep(1.0) # Respect free quota RPM

            except Exception as e:
                print(f"⚠️ [{idx}] 윤문 중 건너뜀: {e}")
                continue

    print(f"\n🎉 [세탁 완료] 총 {refined_count}개의 최상급 명작 데이터셋 완성 -> {output_dataset_path}")
    return refined_count


def main():
    parser = argparse.ArgumentParser(description="Quilltale AI Data Laundry Refiner")
    parser.add_argument("--input", type=str, default="data/collector_logs/warrior_logs.json", help="Path to raw logs JSON")
    parser.add_argument("--output", type=str, default="data/dataset_washed_master.jsonl", help="Path to output JSONL dataset")
    parser.add_argument("--key", type=str, default="", help="Gemini API Key")
    parser.add_argument("--max", type=int, default=50, help="Max entries to refine")
    args = parser.parse_args()

    refine_raw_logs_with_gemini(
        raw_logs_path=Path(args.input),
        output_dataset_path=Path(args.output),
        api_key=args.key,
        max_items=args.max
    )


if __name__ == "__main__":
    main()
