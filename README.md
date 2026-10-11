# TerraQuest: The AI Forager

A LangGraph Game Master (Qwen 2.5 Coder via Ollama) gives you a foraging bounty ("find a plant from the Rosaceae
family", "a weed with serrated leaves"). You photograph a plant; a Hugging Face ViT
([`Sisigoks/FloraSense`](https://huggingface.co/Sisigoks/FloraSense), ~10k species) identifies it locally; rules check the
species against the bounty; Qwen congratulates or roasts you.

```
app.py                 Gradio UI (mobile friendly)
forager/graph.py       LangGraph: perceive -> taxonomize -> judge -> (award) -> narrate
forager/vision.py      transformers image-classification pipeline (local)
forager/taxonomy.py    label -> genus/family/traits (local tables, GBIF fallback when online)
forager/rules.py       deterministic verdict (the LLM cannot change it)
forager/bounties.py    bounty menu; Qwen picks + phrases, rules define success
forager/llm.py         Ollama client; falls back to templates if Ollama is down
data/                  taxa.json (genus->family), traits.json (coarse genus traits)
scripts/               prefetch.py, inspect_labels.py
tests/                 pytest for the rules
```

## Setup (online, once)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/prefetch.py          # downloads the ViT into the Hugging Face cache
ollama pull qwen2.5-coder:7b        # install Ollama first: https://ollama.com
python scripts/inspect_labels.py    # check label format + taxonomy coverage
pytest -q
```

## Run
```bash
HF_HUB_OFFLINE=1 python app.py      # no network calls after setup
```
Open http://localhost:7860. For a phone, open `http://<laptop-ip>:7860` on the same Wi-Fi or the phone's hotspot (no
internet needed). The browser blocks the live webcam on plain http for non-localhost addresses, but the image box's
upload button opens the phone camera, so that path works. For live webcam use an HTTPS tunnel.

## How judging works
1. ViT returns the top 5 labels with probabilities.
2. Each label becomes genus/family/traits via the local tables (GBIF is used only when online and the genus is unknown).
3. `rules.evaluate`: pass if the probability mass of top-5 labels that fit the bounty is >= `TQ_PASS_MASS` (0.25).
   If the top label is below `TQ_UNSURE_BELOW` (0.05) or its taxonomy is unknown, you get a retake tip, no roast.
4. Qwen narrates the verdict. If Ollama is off, canned lines are used.
Tune the thresholds on real photos; 10k classes spread probability thin.

## Known limits (be upfront about these in the write-up)
- Accuracy: the FloraSense model card itself calls the accuracy moderate across 10k look-alike species. Expect wrong IDs.
- Label format: run `scripts/inspect_labels.py`. The parser assumes scientific names (genus first). Common-name labels
  fall back to GBIF (online only) or "unknown".
- Taxonomy and trait tables are small (136 genera, 41 trait rows) and trait data is coarse and genus-level. Extend
  `data/*.json`; bounties only use traits that at least two genera satisfy.
- Qwen 2.5 Coder is a code model; the 7B is fine for short quips but may ignore the JSON format sometimes (handled by fallbacks).
- A leaf photo is hard; ask for flowers/whole plant when possible.

## Field test for the DEV.to post
Load everything online, switch off Wi-Fi/data on the laptop (keep the phone hotspot as a LAN), run with `HF_HUB_OFFLINE=1`,
and screen-record a scan with the network indicators visible.
