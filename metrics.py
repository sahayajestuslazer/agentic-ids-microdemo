# metrics.py
import numpy as np
from sklearn.metrics import roc_auc_score, f1_score, precision_recall_fscore_support

def auroc_safe(y_true, scores):
    try:
        return float(roc_auc_score(y_true, scores))
    except Exception:
        return float("nan")

def f1(y_true, y_pred):
    return float(f1_score(y_true, y_pred))

def full_report(y_true, y_pred):
    p, r, f1v, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)
    return {"precision": float(p), "recall": float(r), "f1": float(f1v)}

# Tiny heuristic rubric for explanation “usefulness”
# Consistency: mentions the *right* driver(s) when anomaly present (or avoids spurious claims when normal)
# Specificity: references at least one concrete metric by name.
KEYS = ["bytes_per_sec", "pkts_per_sec", "syn_rate", "failed_conn_rate"]

def explanation_scores(rationales, y_true, features_by_window):
    # features_by_window: list of dicts with the actual values (used for weak inference)
    cons, spec = [], []
    for i, rat in enumerate(rationales):
        rlow = (rat or "").lower()
        # Specificity: mentions any known metric
        spec.append(any(k in rlow for k in KEYS))
        # Consistency: if positive label, rationale should hint at spikes (or high rates);
        # if negative label, rationale should not claim spikes.
        if y_true[i] == 1:
            cons.append(any(term in rlow for term in ["spike", "elevat", "surge", "high", "anomal"]))
        else:
            cons.append(not any(term in rlow for term in ["spike", "surge", "massive"]))
    return {
        "consistency_rate": float(np.mean(cons) if cons else 0.0),
        "specificity_rate": float(np.mean(spec) if spec else 0.0)
    }
