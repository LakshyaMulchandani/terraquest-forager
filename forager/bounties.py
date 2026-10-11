"""Bounty menu built from the local taxonomy data. Qwen picks and phrases; it can only choose from the menu."""
import json
import random
import re

from . import llm
from .taxonomy import TAXA, TRAITS

FAMILIES = {
    "Rosaceae": "Roses, brambles, strawberries, wild plums. Look for five-petalled flowers and toothed leaves.",
    "Asteraceae": "The daisy family. Each 'flower' is really a cluster of tiny florets: dandelions, tridax, marigolds.",
    "Fabaceae": "The pea family. Look for pods and leaves split into many leaflets.",
    "Lamiaceae": "Mints and basils. Square stems and often a strong smell when crushed.",
    "Moraceae": "Figs, banyan and peepal. Break a stem gently and look for milky sap.",
    "Euphorbiaceae": "Spurges. Milky sap and odd little flowers.",
    "Malvaceae": "Hibiscus and relatives. Showy flowers with a central column of stamens.",
    "Poaceae": "True grasses. Narrow blades, jointed stems.",
    "Solanaceae": "Nightshades. Think tomato, brinjal and datura flowers.",
    "Convolvulaceae": "Morning glories. Twining vines with funnel-shaped flowers.",
    "Amaranthaceae": "Amaranths and goosefoots. Tiny clustered flowers, often on common weeds.",
}
TRAIT_BOUNTIES = [
    ("weed", {"weed": True}, "A common weed", "Whatever grows at path edges and in cracks, uninvited."),
    ("serrated", {"leaf_margin": "serrated"}, "A plant with serrated (saw-toothed) leaves", "Run a finger along the leaf edge: teeth like a saw."),
    ("weed_serrated", {"weed": True, "leaf_margin": "serrated"}, "A weed with serrated leaves", "Uninvited guest, toothed leaf edges."),
    ("compound", {"compound_leaf": True}, "A plant with compound leaves", "One leaf split into separate leaflets on a shared stalk."),
    ("grass", {"habit": "grass"}, "A grass", "Narrow blades, no real petals."),
    ("tree", {"habit": "tree"}, "A tree (a low branch or fallen leaf will do)", "Look up, then look at the ground beneath."),
]


def _satisfiable(criteria):
    return sum(all(t.get(k) == v for k, v in criteria.items()) for t in TRAITS.values()) >= 2


def menu():
    items = [{"id": f"family_{f}", "text": f"A plant from the {f} family", "hint": h, "criteria": {"family": f}}
             for f, h in FAMILIES.items() if f in set(TAXA.values())]
    items += [{"id": f"trait_{i}", "text": t, "hint": h, "criteria": c} for i, c, t, h in TRAIT_BOUNTIES if _satisfiable(c)]
    return items


def pick(recent_ids=()):
    items = [m for m in menu() if m["id"] not in recent_ids] or menu()
    choice, intro = random.choice(items), None
    if llm.available():
        listing = "\n".join(f"{m['id']}: {m['text']}" for m in items)
        raw = llm.chat(
            "You are the Game Master of a foraging scavenger hunt. Choose ONE target from the list and write a one-sentence "
            'dare to the player. Reply ONLY with JSON: {"id": "<id from list>", "intro": "<one sentence>"}.',
            f"Targets:\n{listing}", max_tokens=100)
        m = re.search(r"\{.*\}", raw or "", re.DOTALL)
        try:
            d = json.loads(m.group(0))
            found = next((x for x in items if x["id"] == d.get("id")), None)
            if found:
                choice, intro = found, str(d.get("intro", ""))[:200]
        except Exception:
            pass
    return choice, intro or f"Go outside and find: {choice['text'][0].lower()}{choice['text'][1:]}."
