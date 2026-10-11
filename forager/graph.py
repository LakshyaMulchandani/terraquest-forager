"""The Game Master: a LangGraph state machine.

          ┌──────────────► new_bounty ──► END          (no photo yet)
 START ───┤
          └─► perceive ─► taxonomize ─► judge ─┬─ pass ─► award ─► narrate ─► END
                (ViT)                  (rules)  └─ fail/unsure ───► narrate ─► END
Verdicts come from rules.py. Qwen only writes the words."""
from typing import Any, List, TypedDict

from langgraph.graph import END, StateGraph

from . import bounties, llm, vision
from .rules import evaluate
from .taxonomy import resolve


class State(TypedDict, total=False):
    image: Any
    bounty: dict
    prev_bounty: dict
    preds: List[dict]
    taxa: List[dict]
    verdict: dict
    message: str
    score: int
    streak: int
    history: List[str]


def new_session() -> State:
    return {"score": 0, "streak": 0, "history": []}


def _recent(s):
    return tuple(s.get("history", [])[-3:])


def new_bounty(s: State) -> State:
    b, intro = bounties.pick(_recent(s))
    return {"bounty": b, "message": intro, "verdict": None, "taxa": []}


def perceive(s: State) -> State:
    return {"preds": vision.classify(s["image"])}


def taxonomize(s: State) -> State:
    return {"taxa": [resolve(p["label"], p["score"]) for p in s["preds"]]}


def judge(s: State) -> State:
    v = evaluate(s["taxa"], s["bounty"]["criteria"])
    out = {"verdict": v}
    if v["verdict"] == "fail":
        out["streak"] = 0
    return out


def award(s: State) -> State:
    nxt, intro = bounties.pick(_recent(s) + (s["bounty"]["id"],))
    return {"score": s.get("score", 0) + 1, "streak": s.get("streak", 0) + 1,
            "history": s.get("history", []) + [s["bounty"]["id"]], "prev_bounty": s["bounty"], "bounty": nxt}


SYSTEM = ("You are Warden Neem, a dry-witted forager and Game Master of a scavenger hunt. Write 1-2 short sentences "
          "(under 40 words). Roast the player's botanical skills playfully, never their looks or intelligence, no profanity. "
          "Use ONLY the facts given. Do not change the verdict.")


def _templates(kind, f):
    if kind == "pass":
        return f"Fine, that is {f['species_seen']} ({f['family_seen'] or 'family unknown'}). Point earned. New dare below."
    if kind == "unsure":
        return f"I can't make out a plant ({f['reason']}). One leaf, filling the frame, steady hands."
    return f"That's {f['species_seen']}. I asked for: {f['wanted']}. Back into the dirt with you."


def narrate(s: State) -> State:
    v = s["verdict"]
    kind = v["verdict"]
    shown = s.get("prev_bounty") or s["bounty"]
    top = v["best"] or v["top"]
    facts = {"verdict": kind, "wanted": shown["text"], "species_seen": top["species"], "family_seen": top["family"],
             "reason": v["reason"], "confidence": round(top["score"], 2)}
    prompt = {"pass": "The player succeeded. Congratulate with one fun fact about the species_seen.",
              "fail": "The player failed. Roast them, name the species_seen and what was wanted, send them back out.",
              "unsure": "The photo was unclear or the species is unknown. Do NOT roast. Give one tip."}[kind]
    text = llm.chat(SYSTEM, f"{prompt}\nFacts: {facts}", max_tokens=90) or _templates(kind, facts)
    if kind == "pass":
        text += f"\n\nNEXT: {s['bounty']['text']}"
    return {"message": text}


def build_graph():
    g = StateGraph(State)
    for name, fn in [("new_bounty", new_bounty), ("perceive", perceive), ("taxonomize", taxonomize),
                     ("judge", judge), ("award", award), ("narrate", narrate)]:
        g.add_node(name, fn)
    g.set_conditional_entry_point(lambda s: "perceive" if s.get("image") is not None else "new_bounty",
                                  {"perceive": "perceive", "new_bounty": "new_bounty"})
    g.add_edge("new_bounty", END)
    g.add_edge("perceive", "taxonomize")
    g.add_edge("taxonomize", "judge")
    g.add_conditional_edges("judge", lambda s: "award" if s["verdict"]["verdict"] == "pass" else "narrate",
                            {"award": "award", "narrate": "narrate"})
    g.add_edge("award", "narrate")
    g.add_edge("narrate", END)
    return g.compile()
