"""Qwen 2.5 Coder through Ollama. If Ollama is not running, callers fall back to templates."""
import time
import urllib.request

from .config import LLM_MODEL, OLLAMA_URL

_state = {"t": 0.0, "ok": False}
_model = None


def available() -> bool:
    if time.time() - _state["t"] < 30:
        return _state["ok"]
    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=1.5)
        _state["ok"] = True
    except Exception:
        _state["ok"] = False
    _state["t"] = time.time()
    return _state["ok"]


def chat(system: str, user: str, max_tokens: int = 120, temperature: float = 0.8):
    global _model
    if not available():
        return None
    try:
        if _model is None:
            from langchain_ollama import ChatOllama
            _model = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_URL, temperature=temperature, num_predict=max_tokens)
        return _model.invoke([("system", system), ("human", user)]).content.strip()
    except Exception as e:
        print("LLM call failed:", e)
        return None
