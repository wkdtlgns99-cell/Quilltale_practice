"""
Interactive CLI Launcher for Quilltale Spectator Mode.
Runs cleanly in Python with full UTF-8 support without Windows cmd encoding issues.
"""
import sys
import os
from pathlib import Path

# Ensure UTF-8 output encoding on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.spectator_runner import run_spectator_session, TerminalColors


def main():
    print(f"\n{TerminalColors.HEADER}{TerminalColors.BOLD}======================================================={TerminalColors.END}")
    print(f"{TerminalColors.CYAN}{TerminalColors.BOLD}🎮 Quilltale TRPG — AI 무인 자동 플레이 관전 런처{TerminalColors.END}")
    print(f"{TerminalColors.HEADER}{TerminalColors.BOLD}======================================================={TerminalColors.END}\n")

    print(" [1] 👑 Qwen 2.5 14B 로컬 AI (로컬 0원 / 최고 지능 / 학습 데이터 자동 수집) [추천]")
    print(" [2] 🌌 구글 제미나이 클라우드 AI (초고속 / 최고급 소설 서사)")
    print()

    try:
        choice = input("👉 원하는 모드 번호를 입력하세요 [1/2] (기본값: 1): ").strip()
    except (KeyboardInterrupt, EOFError):
        return

    if choice == "2":
        mode = "live"
    else:
        mode = "ollama_14b"

    print("\n [성향 선택]")
    print("  1. curious_scholar (호기심 많은 학자 / 탐색형)")
    print("  2. aggressive_warrior (호쾌한 돌격 전사 / 전투형)")
    print("  3. cautious_mage (원소 마법사 / 영창형)")
    print("  4. shadow_rogue (은밀한 도적 / 잠입형)")

    try:
        p_choice = input("👉 봇의 플레이 성향을 선택하세요 [1~4] (기본값: 1): ").strip()
    except (KeyboardInterrupt, EOFError):
        return

    persona_map = {
        "1": "curious_scholar",
        "2": "aggressive_warrior",
        "3": "cautious_mage",
        "4": "shadow_rogue"
    }
    persona = persona_map.get(p_choice, "curious_scholar")

    try:
        turns_input = input("\n👉 몇 턴 동안 관전하시겠습니까? (기본값: 5): ").strip()
        turns = int(turns_input) if turns_input.isdigit() and int(turns_input) > 0 else 5
    except (KeyboardInterrupt, EOFError):
        return

    try:
        delay_input = input("👉 턴당 딜레이 시간(초)을 입력하세요 (기본값: 0.5): ").strip()
        delay = float(delay_input) if delay_input else 0.5
    except (KeyboardInterrupt, EOFError):
        delay = 0.5

    print(f"\n{TerminalColors.GREEN}🚀 관전을 시작합니다... (모드: {mode}, 턴 수: {turns}, 성향: {persona}){TerminalColors.END}\n")

    try:
        run_spectator_session(turns=turns, mode=mode, persona=persona, delay=delay)
    except KeyboardInterrupt:
        print(f"\n{TerminalColors.YELLOW}사용자에 의해 관전이 중단되었습니다.{TerminalColors.END}")
    except Exception as e:
        print(f"\n{TerminalColors.RED}관전 중 오류가 발생했습니다: {e}{TerminalColors.END}")


if __name__ == "__main__":
    main()
