"""Run this first. Shows what the model's labels look like and how many our local taxonomy covers."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from transformers import AutoConfig
from forager.config import VISION_MODEL
from forager.taxonomy import TAXA, parse_label

labels = list(AutoConfig.from_pretrained(VISION_MODEL).id2label.values())
print(len(labels), "labels. Sample:", labels[:8])
genera = {parse_label(l)[0] for l in labels}
print(f"{len(genera)} distinct genera; {len(genera & set(TAXA))} covered by data/taxa.json (others use GBIF online, or stay unknown)")
