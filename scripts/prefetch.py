"""Run once while online: downloads the ViT so the hike works offline."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from huggingface_hub import snapshot_download
from forager.config import VISION_MODEL
print("Downloading", VISION_MODEL)
print(snapshot_download(VISION_MODEL))
print("Done. Also run:  ollama pull qwen2.5-coder:7b")
