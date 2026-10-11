"""TerraQuest: The AI Forager. Run:  python app.py   then open the printed URL (phone on the same Wi-Fi works)."""
import os
import gradio as gr
import threading
from forager import vision
from forager.graph import build_graph, new_session

graph = build_graph()

CSS = """
.gradio-container{max-width:560px!important;margin:auto}
.bounty{background:#e6ebdf;color:#1c2a22;border-radius:20px;padding:18px}
.bounty h2{margin:0 0 6px;font-size:22px;color:#1f5a35 !important}
.bounty p{margin:0;color:#566659 !important}
.msg,.msg *{color:#1c2a22 !important}
.pill{display:inline-block;background:#e5a11a;color:#1c2a22;border-radius:99px;padding:2px 12px;font-weight:700;margin-right:6px}
.v-pass{border-left:8px solid #2e6b45}.v-fail{border-left:8px solid #b4472d}.v-unsure{border-left:8px solid #8a8f7a}
.msg{background:#e6ebdf;color:#1c2a22;border-radius:16px;padding:14px;margin-top:8px;font-size:17px;white-space:pre-wrap}
"""


def bounty_html(s):
    b = s.get("bounty")
    if not b:
        return ""
    return (f"<div class='bounty'><span class='pill'>Score {s.get('score', 0)}</span><span class='pill'>Streak {s.get('streak', 0)}</span>"
            f"<h2 style='margin:10px 0 6px;color:#1f5a35 !important'>Find: {b['text']}</h2>"
            f"<p style='margin:0;color:#566659 !important'>{b['hint']}</p></div>")


def msg_html(s):
    v = (s.get("verdict") or {}).get("verdict", "")
    return f"<div class='msg v-{v}' style='color:#1c2a22 !important'>{s.get('message', '')}</div>"

def rows(s):
    return [[t["species"], t["family"] or "unknown", f"{t['score']:.0%}", "yes" if t.get("fits") else "no"] for t in s.get("taxa", [])]


def out(s):
    return s, bounty_html(s), msg_html(s), rows(s)


def start(_):
    return out(graph.invoke(new_session()))


def submit(s, img):
    if img is None:
        s = {**s, "message": "Take or upload a photo first.", "verdict": None}
        return out(s)
    res = graph.invoke({**s, "image": img})
    res.pop("image", None)
    return out(res)


def skip(s):
    return out(graph.invoke({**s, "streak": 0, "image": None}))


with gr.Blocks(css=CSS, title="TerraQuest: The AI Forager", theme=gr.themes.Base(primary_hue="amber", neutral_hue="green")) as demo:
    gr.Markdown("# 🌿 TerraQuest\nFind it outside, snap it, and let the Game Master judge you. Vision and AI both run on this machine.")
    state = gr.State(new_session())
    card, msg = gr.HTML(), gr.HTML()
    img = gr.Image(type="pil", sources=["webcam", "upload"], label="Snap your find (one leaf, fill the frame)", height=340)
    go = gr.Button("Judge my find", variant="primary")
    skipb = gr.Button("Skip this bounty (resets streak)", size="sm")
    table = gr.Dataframe(headers=["Species seen", "Family", "Confidence", "Fits bounty"], interactive=False, label="What the vision model saw (top 5)")
    outs = [state, card, msg, table]
    demo.load(start, state, outs)
    go.click(submit, [state, img], outs)
    skipb.click(skip, state, outs)

threading.Thread(target=vision._classifier, daemon=True).start()  # warm up in background
if __name__ == "__main__":
        demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)))
