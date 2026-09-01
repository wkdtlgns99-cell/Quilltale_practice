"""
Terminal Spectator Runner for Quilltale TRPG.
Allows developers/users to watch autonomous AI-vs-AI play sessions in real-time.
"""
import sys
import time
import argparse
from pathlib import Path

# Ensure UTF-8 output encoding on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure root directory in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.world.generator import WorldGenerator
from src.agents.game_master import GameMasterAgent
from src.agents.player_bot import PlayerBotAgent
from src.llm.base import BaseLLM, LLMResponse


class TerminalColors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def run_spectator_session(turns: int = 5, mode: str = "mock", persona: str = "curious_scholar", delay: float = 1.0):
    print(f"\n{TerminalColors.HEADER}{TerminalColors.BOLD}======================================================={TerminalColors.END}")
    print(f"{TerminalColors.CYAN}{TerminalColors.BOLD}🎮 Quilltale TRPG — AI 무인 자동 플레이 관전 모드{TerminalColors.END}")
    print(f"모드: {TerminalColors.YELLOW}{mode.upper()}{TerminalColors.END} | 성향: {TerminalColors.GREEN}{persona}{TerminalColors.END} | 목표: {turns}턴 관전")
    print(f"{TerminalColors.HEADER}{TerminalColors.BOLD}======================================================={TerminalColors.END}\n")

    # Setup GM and Player Bot LLMs
    if mode == "live":
        from src.llm.gemini import GeminiLLM
        gm_llm = GeminiLLM()
        bot_llm = GeminiLLM()
    elif mode == "ollama_14b":
        from src.llm.ollama import OllamaLLM
        gm_llm = OllamaLLM(model="qwen2.5:14b")
        bot_llm = OllamaLLM(model="qwen2.5:14b")
    elif mode == "ollama_7b":
        from src.llm.ollama import OllamaLLM
        gm_llm = OllamaLLM(model="qwen2.5:7b")
        bot_llm = OllamaLLM(model="qwen2.5:7b")
    elif mode == "ollama_3b":
        from src.llm.ollama import OllamaLLM
        gm_llm = OllamaLLM(model="qwen2.5:3b")
        bot_llm = OllamaLLM(model="qwen2.5:3b")
    elif mode in ["ollama", "ollama_1.5b"]:
        from src.llm.ollama import OllamaLLM
        gm_llm = OllamaLLM(model="qwen2.5:1.5b")
        bot_llm = OllamaLLM(model="qwen2.5:1.5b")
    else:
        # Mock LLM for 0-token instant testing
        class SpectatorMockLLM(BaseLLM):
            def generate(self, prompt: str, system: str = "") -> LLMResponse:
                return LLMResponse(text='{"narration": "선술집의 등불이 흔들리고, 사람들의 시선이 당신에게 쏠립니다.", "state_update": {}, "scene_changed": false}', model="mock")
            def generate_json(self, prompt: str, system: str = "") -> str:
                return '{"narration": "선술집의 등불이 흔들리고, 사람들의 시선이 당신에게 쏠립니다.", "state_update": {}, "scene_changed": false}'

            @property
            def model_name(self) -> str:
                return "mock_spectator"

        gm_llm = SpectatorMockLLM()
        bot_llm = None  # Uses smart heuristics

    gm = GameMasterAgent(llm=gm_llm)
    print(f"{TerminalColors.YELLOW}⏳ 방대한 대륙 지형, 던전 5개소, NPC 생태계를 절차적 생성 중입니다...{TerminalColors.END}")
    state = gm.generate_new_game()
    state.session_id = f"spectator_{int(time.time())}"
    print(f"{TerminalColors.GREEN}✅ 세계관 창조 완료! [{state.world_name}]{TerminalColors.END}")
    
    bot = PlayerBotAgent(llm=bot_llm, persona_key=persona)

    # Opening
    print(f"{TerminalColors.YELLOW}⏳ 프롤로그 서사를 집필하는 중입니다...{TerminalColors.END}")
    opening = gm.generate_opening(state)
    print(f"\n{TerminalColors.BOLD}[📜 오프닝 서사]{TerminalColors.END}")
    print(f"{opening.get('narration', '')}\n")
    time.sleep(delay)

    recent_narration = opening.get("narration", "")

    for t in range(1, turns + 1):
        loc = state.current_location()
        loc_name = loc.name if loc else "미지의 장소"
        
        print(f"\n{TerminalColors.YELLOW}{TerminalColors.BOLD}-------------------------------------------------------{TerminalColors.END}")
        print(f"{TerminalColors.BOLD}[TURN {state.turn + 1}/{turns}] 🏰 {loc_name} | ❤️ HP: {state.player.health}/{state.player.max_health} | 🪙 {state.player.gold}G{TerminalColors.END}")
        print(f"{TerminalColors.YELLOW}{TerminalColors.BOLD}-------------------------------------------------------{TerminalColors.END}")

        # 1. Player Bot decides action
        bot_action = bot.decide_action(state, recent_narration=recent_narration)
        print(f"\n{TerminalColors.GREEN}{TerminalColors.BOLD}🤖 [플레이어 봇 행동 선언]:{TerminalColors.END} {bot_action}")

        # 2. GM processes turn (Pass 1 -> Pass 2)
        turn_start_time = time.time()
        result = gm.process_turn(bot_action, state)
        elapsed_sec = time.time() - turn_start_time

        # 3. Print Results
        if result.get("dice_result"):
            d_res = result["dice_result"]
            status_tag = f"{TerminalColors.GREEN}✅ 성공{TerminalColors.END}" if d_res.get("is_success") else f"{TerminalColors.RED}❌ 실패{TerminalColors.END}"
            print(f"{TerminalColors.CYAN}🎲 [주사위 결과]: {d_res.get('summary_ko', '')} -> {status_tag}")

        from src.llm.resilience import JSONRepairEngine
        clean_narr = JSONRepairEngine.extract_clean_prose(result.get('narration', ''))
        print(f"\n{TerminalColors.BOLD}[📖 GM 내러티브 서사]:{TerminalColors.END}")
        print(f"{clean_narr}")

        if result.get("audio"):
            bgm = result["audio"].get("current_bgm", {})
            sfx_list = [s["name_ko"] for s in result["audio"].get("triggered_sfx", [])]
            sfx_str = f", 🔊 SFX: {', '.join(sfx_list)}" if sfx_list else ""
            print(f"{TerminalColors.BLUE}🎵 BGM: {bgm.get('name_ko', '없음')}{sfx_str}{TerminalColors.END}")

        if result.get("changes_applied"):
            changes_str = " | ".join(result["changes_applied"])
            print(f"{TerminalColors.YELLOW}⚡ [상태 변화]: {changes_str}{TerminalColors.END}")

        print(f"⏱️ 턴 처리 시간: {elapsed_sec:.2f}초")
        recent_narration = result.get("narration", "")

        # Save turn to dataset
        try:
            from src.llm.resilience import JSONRepairEngine
            dataset_file = Path(__file__).resolve().parent.parent / "data" / "collector_logs" / "spectator_dataset.jsonl"
            dataset_file.parent.mkdir(parents=True, exist_ok=True)
            with open(dataset_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "instruction": f"위치: {loc_name} | 플레이어 행동: {bot_action}",
                    "response": clean_narr,
                    "mode": mode,
                    "turn": state.turn
                }, ensure_ascii=False) + "\n")
        except Exception:
            pass

        # Check death
        if state.player.health <= 0:
            print(f"\n{TerminalColors.RED}{TerminalColors.BOLD}☠️ 플레이어가 사망하여 모험이 종료되었습니다!{TerminalColors.END}")
            break

        time.sleep(delay)

    print(f"\n{TerminalColors.HEADER}{TerminalColors.BOLD}======================================================={TerminalColors.END}")
    print(f"{TerminalColors.GREEN}🎉 관전 세션이 정상적으로 완료되었습니다! (학습 로그 자동 누적됨){TerminalColors.END}")
    print(f"{TerminalColors.HEADER}{TerminalColors.BOLD}======================================================={TerminalColors.END}\n")


if __name__ == "__main__":
    import json
    parser = argparse.ArgumentParser(description="Quilltale Spectator Runner")
    parser.add_argument("--turns", type=int, default=5, help="Number of turns to auto-play")
    parser.add_argument("--mode", type=str, default="ollama_7b", choices=["mock", "live", "ollama", "ollama_1.5b", "ollama_3b", "ollama_7b", "ollama_14b"], help="LLM mode")
    parser.add_argument("--persona", type=str, default="curious_scholar", help="Player bot persona")
    parser.add_argument("--delay", type=float, default=2.5, help="Delay in seconds between turns")
    args = parser.parse_args()

    run_spectator_session(turns=args.turns, mode=args.mode, persona=args.persona, delay=args.delay)
