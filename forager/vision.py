"""Local ViT inference with Hugging Face transformers. After the first download it runs fully offline
(set HF_HUB_OFFLINE=1 to guarantee no network calls)."""
from functools import lru_cache

import torch
from PIL import Image
from transformers import pipeline

from .config import TOP_K, VISION_MODEL


@lru_cache(maxsize=1)
def _classifier():
    return pipeline("image-classification", model=VISION_MODEL, device=0 if torch.cuda.is_available() else -1)


def classify(img: Image.Image, k: int = TOP_K):
    out = _classifier()(img.convert("RGB"), top_k=k)
    return [{"label": o["label"], "score": float(o["score"])} for o in out]
