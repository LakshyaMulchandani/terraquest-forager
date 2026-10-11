"""Turn a ViT label into genus / family / traits.
1. Local table (data/taxa.json, data/traits.json): works offline.
2. GBIF name-match API as an online fallback, cached to data/gbif_cache.json.
Unknown stays None; the rules never guess."""
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
TAXA = json.loads((DATA / "taxa.json").read_text())        # genus -> family (curated)
_full = DATA / "taxa_full.json"
if _full.exists():
    TAXA = {**json.loads(_full.read_text()), **TAXA}        # curated entries win
TRAITS = json.loads((DATA / "traits.json").read_text())    # genus -> coarse traits
_CACHE_FILE = DATA / "gbif_cache.json"
_cache = json.loads(_CACHE_FILE.read_text()) if _CACHE_FILE.exists() else {}


def parse_label(label: str):
    """'Cirsium arvense (L.) Scop.' -> ('Cirsium', 'Cirsium arvense')"""
    words = re.sub(r"\(.*?\)", "", label).replace("_", " ").split()
    if not words:
        return None, label
    words = [w for w in words if w.lower() not in ("x", "×")]
    genus = words[0].capitalize()
    species = " ".join([genus] + [w.lower() for w in words[1:2]])
    return genus, species


def _gbif_family(name: str):
    if name in _cache:
        return _cache[name]
    fam = None
    try:
        url = "https://api.gbif.org/v1/species/match?" + urllib.parse.urlencode({"name": name, "kingdom": "Plantae"})
        with urllib.request.urlopen(url, timeout=4) as r:
            d = json.load(r)
        if d.get("matchType") in ("EXACT", "FUZZY", "HIGHERRANK"):
            fam = d.get("family")
    except Exception:
        return None  # offline: don't cache the failure
    _cache[name] = fam
    try:
        _CACHE_FILE.write_text(json.dumps(_cache, indent=1))
    except OSError:
        pass
    return fam


def resolve(label: str, score: float = 0.0) -> dict:
    genus, species = parse_label(label)
    family = TAXA.get(genus) or _gbif_family(species)
    return {"label": label, "species": species, "genus": genus, "family": family, "score": score,
            **{k: None for k in ("weed", "leaf_margin", "compound_leaf", "habit")}, **TRAITS.get(genus, {})}
