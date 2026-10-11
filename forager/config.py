import os

VISION_MODEL = os.getenv("TQ_VISION_MODEL", "Sisigoks/FloraSense")   # Hugging Face ViT, ~10k species
LLM_MODEL = os.getenv("TQ_LLM", "qwen2.5-coder:7b")                  # served locally by Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
TOP_K = int(os.getenv("TQ_TOP_K", "5"))
# With 10k classes the probability mass is spread thin, so we judge on the top-K together.
PASS_MASS = float(os.getenv("TQ_PASS_MASS", "0.25"))      # share of top-K probability that must fit the bounty
UNSURE_BELOW = float(os.getenv("TQ_UNSURE_BELOW", "0.05"))  # top-1 below this = blurry/no plant, retake without roast
