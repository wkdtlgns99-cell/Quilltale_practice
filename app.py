"""
Quilltale — AI Game Master with Persistent World State, Local RAG & Legacy Characters
"""

from pathlib import Path
import gradio as gr
import json

from src.llm import get_llm
from src.agents.game_master import GameMasterAgent
from src.world.persistence import PersistenceManager
from src.world.state import WorldState, DISPOSITION_KO_MAP
from src.world.legacy import LegacyManager
from src.world.skills import SkillSystem
from src.world.incantation import IncantationSystem
from src.world.chronicle import ChronicleManager
try:
    from src.image.flux import generate_scene_image
except ImportError:
    def generate_scene_image(prompt):
        return None

LLM_NAME = "gemini"


def create_new_world() -> tuple:
    """Generate a completely new random world via LLM WorldGenerator."""
    llm = get_llm(LLM_NAME)
    gm = GameMasterAgent(llm)
    state = gm.generate_new_game()
    opening = gm.generate_opening(state)
    narration = opening["narration"]
    chat_history = [{"role": "assistant", "content": narration}]
    return (
        chat_history,
        None,
        state.to_json(),
        state.to_player_summary_html(),
        state.to_skills_html(),
        state.to_inventory_html(),
    )


def get_save_choices() -> list[tuple[str, str]]:
    """Return save slot choices formatted as (display_label, world_id)."""
    try:
        saves = PersistenceManager.list_saved_worlds()
        choices = []
        for s in saves:
            label = f"{s['world_name']} — {s['player_name']} (턴 {s['turn']})"
            choices.append((label, s["world_id"]))
        return choices if choices else [("저장된 슬롯 없음", "")]
    except Exception:
        return [("저장된 슬롯 없음", "")]


def save_game(world_state_json: str):
    """Manual save and immediately update dropdown with current world selected."""
    try:
        state = WorldState.from_json(world_state_json)
        PersistenceManager.manual_save(state)
        gr.Info(f"💾 [{state.world_name}] 저장이 완료되었습니다! (턴 {state.turn})")
        choices = get_save_choices()
        curr_id = getattr(state, "world_id", state.session_id)
        return gr.update(choices=choices, value=curr_id)
    except Exception as e:
        gr.Warning(f"저장 실패: {e}")
        return gr.update()


def delete_save_game(world_id: str):
    """Delete selected save file and immediately refresh dropdown."""
    if not world_id:
        gr.Warning("삭제할 저장 슬롯을 선택해주세요.")
        return gr.update()
    try:
        deleted = PersistenceManager.delete_manual_save(world_id)
        if deleted:
            gr.Info("🗑️ 저장된 세계관 파일이 삭제되었습니다.")
        else:
            gr.Warning("삭제할 저장 파일을 찾을 수 없습니다.")
        choices = get_save_choices()
        new_val = choices[0][1] if choices and choices[0][1] else ""
        return gr.update(choices=choices, value=new_val)
    except Exception as e:
        gr.Warning(f"삭제 실패: {e}")
        return gr.update()


def load_game(world_id: str) -> tuple:
    """Load a saved world by world_id."""
    if not world_id:
        gr.Warning("불러올 슬롯을 선택해주세요.")
        return (gr.update(),) * 6
    try:
        state = PersistenceManager.load_manual_save(world_id)
        if state is None:
            gr.Warning(f"저장 파일을 찾을 수 없습니다.")
            return (gr.update(),) * 6
        LegacyManager.spawn_legacy_npcs_to_world(state)
        chat_history = []
        for h in state.history[-20:]:
            chat_history.append({"role": "user", "content": h.get("action", "")})
            chat_history.append({"role": "assistant", "content": h.get("narration", "")})
        gr.Info(f"📖 [{state.world_name}] 불러오기 완료! (턴 {state.turn})")
        return (
            chat_history,
            None,
            state.to_json(),
            state.to_player_summary_html(),
            state.to_skills_html(),
            state.to_inventory_html(),
        )
    except Exception as e:
        gr.Warning(f"불러오기 실패: {e}")
        return (gr.update(),) * 6



def release_character_action(chatbot, world_state_json, current_image):
    action = "이곳을 떠난다"
    return take_action(action, chatbot, world_state_json, current_image)


def take_action(
    action: str,
    chat_history: list,
    world_state_json: str,
    current_image,
) -> tuple:
    if not action.strip():
        try:
            state = WorldState.from_json(world_state_json)
            s_html = state.to_player_summary_html()
            sk_html = state.to_skills_html()
            inv_html = state.to_inventory_html()
        except Exception:
            s_html = "<div class='qt-panel-content'>세계 상태를 불러올 수 없습니다.</div>"
            sk_html = ""
            inv_html = ""
        return chat_history, current_image, world_state_json, s_html, sk_html, inv_html

    try:
        state = WorldState.from_json(world_state_json)
    except Exception:
        state = None

    if state and getattr(state, "active_world_ended", False):
        return chat_history, current_image, world_state_json, state.to_player_summary_html(), state.to_skills_html(), state.to_inventory_html()

    llm = get_llm(LLM_NAME)
    gm = GameMasterAgent(llm)

    result = gm.process_turn(action, state)

    narration_with_extras = result["narration"]
    if result.get("dice_result"):
        dice_info = result["dice_result"].get("summary_ko", "")
        narration_with_extras = f"🎲 **[{dice_info}]**\n\n{narration_with_extras}"

    chat_history = chat_history + [
        {"role": "user", "content": action},
        {"role": "assistant", "content": narration_with_extras},
    ]

    if getattr(state, "active_world_ended", False):
        chronicle_text = ChronicleManager.generate_chronicle(state, llm, "완결")
        chat_history.append({"role": "assistant", "content": f"📜 **영웅 일대기**\n\n{chronicle_text}"})
        chat_history.append({"role": "assistant", "content": "🏛️ 세계가 끝났습니다. 왼쪽의 [🌍 새 세계 시작] 버튼을 눌러 새 모험을 시작하세요."})

    new_image = current_image
    if result.get("scene_changed") and result.get("image_prompt"):
        try:
            new_image = generate_scene_image(result["image_prompt"])
        except Exception:
            pass

    return (
        chat_history,
        new_image,
        state.to_json(),
        state.to_player_summary_html(),
        state.to_skills_html(),
        state.to_inventory_html(),
    )


def start_game(world_state_json: str) -> tuple:
    """On page load: try to resume a session with real progress, else generate a fresh world."""
    try:
        saved = PersistenceManager.load_session("default_session")
    except Exception:
        saved = None

    if saved and saved.turn > 0:
        try:
            LegacyManager.spawn_legacy_npcs_to_world(saved)
            chat_history = []
            for h in saved.history[-20:]:
                chat_history.append({"role": "user", "content": h.get("action", "")})
                chat_history.append({"role": "assistant", "content": h.get("narration", "")})
            return (
                chat_history,
                None,
                saved.to_json(),
                saved.to_player_summary_html(),
                saved.to_skills_html(),
                saved.to_inventory_html(),
            )
        except Exception:
            pass  # Corrupt save → fall through to new world

    # No progress / no save / corrupt save → generate a brand-new random world
    return create_new_world()




# ── Gradio UI layout ──────────────────────────────────────────

JS_THEME_TOGGLE = """
() => {
    document.body.classList.toggle('light-mode');
    const btn = document.querySelector('.qt-toggle-btn button');
    if (btn) btn.textContent = document.body.classList.contains('light-mode') ? '🌙 어둡게' : '☀ 밝게';
}
"""

SCROLL_PRESERVATION_HEAD = """
<script>
(function() {
    let savedY = 0;
    
    // Capture scroll position before tab click
    document.addEventListener('pointerdown', (e) => {
        if (e.target.closest('button[role="tab"]') || e.target.closest('.tab-nav button') || e.target.closest('.tabitem') || e.target.closest('.tabs')) {
            savedY = window.scrollY || window.pageYOffset || document.documentElement.scrollTop;
        }
    }, true);

    // Prevent jump after tab switch
    document.addEventListener('click', (e) => {
        if (e.target.closest('button[role="tab"]') || e.target.closest('.tab-nav button') || e.target.closest('.tabitem') || e.target.closest('.tabs')) {
            const currentY = savedY;
            requestAnimationFrame(() => {
                window.scrollTo({ top: currentY, behavior: 'instant' });
            });
            setTimeout(() => {
                window.scrollTo({ top: currentY, behavior: 'instant' });
            }, 25);
            setTimeout(() => {
                window.scrollTo({ top: currentY, behavior: 'instant' });
            }, 80);
        }
    }, true);

    // PREVENT TEXT EDITING ON SAVE SLOT DROPDOWN
    document.addEventListener('keydown', function(e) {
        if (e.target && e.target.closest && e.target.closest('.qt-save-slot-dd')) {
            e.preventDefault();
            return false;
        }
    }, true);

    function enforceReadOnlyDropdowns() {
        document.querySelectorAll('.qt-save-slot-dd input').forEach(function(inp) {
            inp.readOnly = true;
            inp.setAttribute('readonly', 'readonly');
        });
    }
    document.addEventListener('DOMContentLoaded', enforceReadOnlyDropdowns);
    setInterval(enforceReadOnlyDropdowns, 500);

    // ERADICATE ALL LOADING SPINNERS INSIDE LEFT COLUMN ONLY
    function purgeLoaders() {
        document.querySelectorAll('.qt-left-col .generating, .qt-left-col [data-testid*="loading"], .qt-left-col .loading-status, .qt-left-col .loader, .qt-left-col .loading, .qt-left-col [class*="generating"], .qt-save-slot-dd svg, .qt-btn-row svg:not(.qt-toggle-btn svg), .qt-load-row svg:not(.qt-toggle-btn svg)').forEach(function(el) {
            el.style.setProperty('display', 'none', 'important');
            el.style.setProperty('visibility', 'hidden', 'important');
            el.style.setProperty('opacity', '0', 'important');
            try { el.remove(); } catch(e) {}
        });
    }
    setInterval(purgeLoaders, 50);

    const loadingCleaner = new MutationObserver(function() {
        purgeLoaders();
    });
    if (document.body) {
        loadingCleaner.observe(document.body, { childList: true, subtree: true });
    } else {
        document.addEventListener('DOMContentLoaded', function() {
            loadingCleaner.observe(document.body, { childList: true, subtree: true });
        });
    }



    // FOOLPROOF GLOBAL SCREEN TOOLTIP ENGINE
    function ensureTooltip() {
        let tip = document.getElementById('qt-master-tooltip');
        if (!tip) {
            tip = document.createElement('div');
            tip.id = 'qt-master-tooltip';
            document.body.appendChild(tip);
        }
        return tip;
    }



    document.addEventListener('mouseover', function(e) {
        let tag = e.target.closest ? e.target.closest('.qt-hover-tag') : null;
        if (tag) {
            let text = tag.getAttribute('data-tooltip');
            if (text) {
                let tip = ensureTooltip();
                tip.innerHTML = text.replace(/\\n/g, '<br>').replace(/&#10;/g, '<br>');
                tip.style.display = 'block';

                let rect = tag.getBoundingClientRect();
                let tipRect = tip.getBoundingClientRect();

                // Compute ideal position above the tag
                let top = rect.top - tipRect.height - 8;
                let left = rect.left + (rect.width / 2) - (tipRect.width / 2);

                // Flip below if not enough room on top
                if (top < 10) {
                    top = rect.bottom + 8;
                }

                // Keep within horizontal window bounds
                if (left < 10) left = 10;
                if (left + tipRect.width > window.innerWidth - 10) {
                    left = window.innerWidth - tipRect.width - 10;
                }

                tip.style.top = top + 'px';
                tip.style.left = left + 'px';
            }
        }
    }, true);

    document.addEventListener('mouseout', function(e) {
        let tag = e.target.closest ? e.target.closest('.qt-hover-tag') : null;
        if (tag) {
            let tip = document.getElementById('qt-master-tooltip');
            if (tip) {
                tip.style.display = 'none';
            }
        }
    }, true);
})();
</script>
"""




with gr.Blocks(title="Quilltale — TRPG 엔진") as demo:
    world_state = gr.State()

    # Top bar
    with gr.Row(elem_classes="qt-topbar"):
        gr.HTML("""
        <div class="qt-brand">
          <span class="qt-rune">⚔</span>
          <span class="qt-brand-name">Quilltale</span>
        </div>""")
        theme_btn = gr.Button("☀ 밝게", scale=0, elem_classes="qt-toggle-btn")

    gr.HTML('<p class="qt-tagline">당신의 선택이 세계를 빚는다 — 살아 숨쉬는 AI 판타지 TRPG</p>')


    # Main 2-column layout (Left: HUD, Right: Chatbot)
    with gr.Row(elem_classes="qt-main-row"):
        # Left column
        with gr.Column(scale=1, elem_classes="qt-left-col"):
            scene_image = gr.Image(
                label="",
                elem_classes="qt-scene",
                interactive=False,
                show_label=False,
                height=200,
            )


            gr.HTML('<div class="qt-panel-label">모험가 정보 기록부</div>')
            with gr.Tabs():
                with gr.TabItem("⚔️ 상태 기록부"):
                    status_display = gr.HTML(elem_classes="qt-accord")
                with gr.TabItem("✨ 스킬북"):
                    skills_display = gr.HTML(elem_classes="qt-accord")
                with gr.TabItem("🎒 가방"):
                    inv_display = gr.HTML(elem_classes="qt-accord")

            with gr.Row(elem_classes="qt-btn-row"):
                new_world_btn = gr.Button("🌍 새 세계", elem_classes="qt-btn-new", scale=1, min_width=0)
                save_btn = gr.Button("💾 저장", elem_classes="qt-btn-new", scale=1, min_width=0)
                release_btn = gr.Button("🕊️ 은퇴/방생", elem_classes="qt-btn-new", scale=1, min_width=0)

            with gr.Row(elem_classes="qt-btn-row qt-load-row"):
                save_slot_dd = gr.Dropdown(
                    choices=[("저장된 슬롯 없음", "")],
                    value="",
                    label="",
                    interactive=True,
                    allow_custom_value=False,
                    scale=3,
                    min_width=0,
                    elem_classes="qt-save-slot-dd"
                )
                load_btn = gr.Button("📂 불러오기", elem_classes="qt-btn-new", scale=1, min_width=0)
                delete_save_btn = gr.Button("🗑️ 삭제", elem_classes="qt-btn-new", scale=1, min_width=0)




        # Right column
        with gr.Column(scale=1, elem_classes="qt-right-col"):
            chatbot = gr.Chatbot(
                height=650,
                show_label=False,
                elem_classes="qt-chronicle",
            )




            gr.HTML('<div class="qt-input-label">다음으로 무엇을 선언하시겠습니까?</div>')
            with gr.Row(elem_classes="qt-input-row"):
                action_input = gr.Textbox(
                    placeholder="예) 선술집 주인에게 말을 건다  /  단검을 집어들고 문을 향해 달린다",
                    scale=5,
                    lines=1,
                    max_lines=2,
                    label="",
                    elem_classes="qt-action-box"
                )
                submit_btn = gr.Button(
                    "행동 선언",
                    variant="primary",
                    scale=1,
                    interactive=False,
                    elem_classes="qt-btn-act"
                )



    # Footer
    gr.HTML("""
    <div class="qt-footer">
      <span class="qt-footer-rule">✦ ✦ ✦</span>
      <span class="qt-footer-text">Quilltale — AI Game Master · 모든 선택은 영구히 기록된다</span>
      <span class="qt-footer-rule">✦ ✦ ✦</span>
    </div>
    """)

    # Event wiring
    theme_btn.click(fn=None, js=JS_THEME_TOGGLE)

    new_world_btn.click(
        fn=create_new_world,
        outputs=[chatbot, scene_image, world_state, status_display, skills_display, inv_display],
    )

    save_btn.click(
        fn=save_game,
        inputs=[world_state],
        outputs=[save_slot_dd],
        show_progress="hidden"
    )

    delete_save_btn.click(
        fn=delete_save_game,
        inputs=[save_slot_dd],
        outputs=[save_slot_dd],
        show_progress="hidden"
    )

    release_btn.click(
        fn=release_character_action,
        inputs=[chatbot, world_state, scene_image],
        outputs=[chatbot, scene_image, world_state, status_display, skills_display, inv_display],
    )

    load_btn.click(
        fn=load_game,
        inputs=[save_slot_dd],
        outputs=[chatbot, scene_image, world_state, status_display, skills_display, inv_display],
    )

    submit_btn.click(
        fn=lambda: (gr.update(interactive=False), gr.update(interactive=False)),
        outputs=[submit_btn, action_input],
        show_progress="hidden"
    ).then(
        fn=take_action,
        inputs=[action_input, chatbot, world_state, scene_image],
        outputs=[chatbot, scene_image, world_state, status_display, skills_display, inv_display],
    ).then(
        fn=lambda: ("", gr.update(interactive=True), gr.update(interactive=False)),
        outputs=[action_input, action_input, submit_btn],
        show_progress="hidden"
    )

    action_input.submit(
        fn=lambda: (gr.update(interactive=False), gr.update(interactive=False)),
        outputs=[submit_btn, action_input],
        show_progress="hidden"
    ).then(
        fn=take_action,
        inputs=[action_input, chatbot, world_state, scene_image],
        outputs=[chatbot, scene_image, world_state, status_display, skills_display, inv_display],
    ).then(
        fn=lambda: ("", gr.update(interactive=True), gr.update(interactive=False)),
        outputs=[action_input, action_input, submit_btn],
        show_progress="hidden"
    )

    action_input.change(
        fn=lambda text: gr.update(interactive=bool(text.strip())),
        inputs=[action_input],
        outputs=[submit_btn],
        show_progress="hidden"
    )

    demo.load(
        fn=lambda ws: (*start_game(ws), gr.update(choices=get_save_choices(), value=get_save_choices()[0][1] if get_save_choices() and get_save_choices()[0][1] else "")),
        inputs=[world_state],
        outputs=[chatbot, scene_image, world_state, status_display, skills_display, inv_display, save_slot_dd],
    )




if __name__ == "__main__":
    demo.launch(
        css_paths=Path("assets/styles.css"),
        head=SCROLL_PRESERVATION_HEAD,
        server_name="127.0.0.1",
        server_port=7860,
        inbrowser=True,
        ssr_mode=False,
    )




