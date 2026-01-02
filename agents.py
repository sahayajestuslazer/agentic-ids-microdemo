# agents.py
import os, json, requests
from retriever import retrieve_snippets
from governance import policy_gate, log_step

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.environ.get("MODEL", "mistral")

PROMPT_TMPL = """You are a network IDS analyst.
Given a window-level NetFlow summary and a few notes, decide if the window is ANOMALOUS (1) or NORMAL (0).
Return strict JSON: {{"label": 0 or 1, "rationale": "<one sentence>"}}

Window stats: {stats}
Notes:
{notes}
"""

def llm_label(stats_dict):
    if not policy_gate("propose_label", {"window_id": int(stats_dict["window_id"])}):
        return 0, "Denied by policy gate."
    # Retrieve 2 short notes
    notes = retrieve_snippets(stats_dict, topk=2)
    if policy_gate("retrieve_notes", {"k": len(notes)}):
        pass
    prompt = PROMPT_TMPL.format(stats=stats_dict, notes="\n".join(f"- {n}" for n in notes))
    log_step("prompt", prompt[:600])

    try:
        r = requests.post(OLLAMA_URL, json={"model": MODEL, "prompt": prompt, "stream": False}, timeout=60)
        r.raise_for_status()
        text = r.json().get("response", "").strip()
        log_step("llm_response", text[:600])
        try:
            j = json.loads(text)
            return int(j.get("label", 0)), j.get("rationale", "N/A")
        except Exception:
            # Fallback keyword parse
            lbl = 1 if "anom" in text.lower() or "suspicious" in text.lower() else 0
            return lbl, text[:160]
    except Exception as e:
        log_step("llm_error", str(e))
        return 0, f"LLM error: {e}"
