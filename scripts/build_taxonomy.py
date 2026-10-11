import sys, json, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from transformers import AutoConfig
from forager.config import VISION_MODEL
from forager.taxonomy import parse_label, DATA

out = DATA / "taxa_full.json"
done = json.loads(out.read_text()) if out.exists() else {}
labels = AutoConfig.from_pretrained(VISION_MODEL).id2label.values()
genera = sorted({parse_label(l)[0] for l in labels} - set(done))
print(len(genera), "genera to look up")

def fetch(g):
    url = "https://api.gbif.org/v1/species/match?" + urllib.parse.urlencode(
        {"name": g, "rank": "genus", "kingdom": "Plantae"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                return g, json.load(r).get("family")
        except Exception:
            pass
    return g, None

with ThreadPoolExecutor(8) as ex:
    for i, (g, fam) in enumerate(ex.map(fetch, genera), 1):
        if fam:
            done[g] = fam
        if i % 200 == 0:
            print(i, "/", len(genera))
            out.write_text(json.dumps(done, indent=0))
out.write_text(json.dumps(done, indent=0))
print(len(done), "genera mapped ->", out)