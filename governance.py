# governance.py
from datetime import datetime
from pathlib import Path

LOG = Path(__file__).parent / "audit_log_ids.txt"
ALLOWED_ACTIONS = {"read_data", "retrieve_notes", "propose_label", "write_results"}

def log(line):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def policy_gate(action, meta=None):
    allowed = action in ALLOWED_ACTIONS
    meta = meta or {}
    log(f"{datetime.utcnow().isoformat()}Z | ACTION={action} | ALLOWED={allowed} | META={meta}")
    return allowed

def log_step(step, detail):
    log(f"{datetime.utcnow().isoformat()}Z | STEP={step} | DETAIL={detail}")
