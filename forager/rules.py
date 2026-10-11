"""Deterministic judging. The LLM only narrates the verdict; it can never change it."""
from .config import PASS_MASS, UNSURE_BELOW


def fits(taxon: dict, criteria: dict) -> bool:
    return all(taxon.get(k) == v for k, v in criteria.items())


def evaluate(taxa: list, criteria: dict, pass_mass: float = PASS_MASS, unsure_below: float = UNSURE_BELOW) -> dict:
    for t in taxa:
        t["fits"] = fits(t, criteria)
    top = taxa[0]
    mass = sum(t["score"] for t in taxa if t["fits"])
    best = next((t for t in taxa if t["fits"]), None)
    if top["score"] < unsure_below:
        return {"verdict": "unsure", "mass": mass, "reason": "no clear plant in frame", "top": top, "best": None}
    if best and mass >= pass_mass:
        return {"verdict": "pass", "mass": mass, "reason": "match", "top": top, "best": best}
    if any(top.get(k) is None for k in criteria):
        return {"verdict": "unsure", "mass": mass, "reason": "species not in my taxonomy notes", "top": top, "best": None}
    return {"verdict": "fail", "mass": mass, "reason": "mismatch", "top": top, "best": None}
