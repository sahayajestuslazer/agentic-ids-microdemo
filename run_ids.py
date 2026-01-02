# run_ids.py — PAPER MODE: fixed evaluation subset + tidy summary
import os
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

from baseline import zscore_baseline, iforest_baseline
from metrics import auroc_safe, full_report, explanation_scores
from governance import policy_gate

# ---- Paper-mode constants (LOCK THESE FOR THE PAPER) -------------------------
EVAL_N = 50              # <- choose & freeze for the paper
EVAL_MODE = "head"       # "head" or "sample" (deterministic seed below)
SAMPLE_SEED = 42         # used only if EVAL_MODE == "sample"
Z_THRESH_DEFAULT = 3.0
IFOREST_CONTAM_DEFAULT = 0.12
# -----------------------------------------------------------------------------

# Optional agent (LLM)
USE_LLM = True
try:
    from agents import llm_label
except Exception:
    USE_LLM = False

DATA = Path(__file__).parent / "data" / "netflow_windows.csv"
OUT  = Path(__file__).parent / "ids_results.csv"
AUDIT_LOG_PATH = Path(__file__).parent / "audit_log_ids.txt"

def main():
    parser = argparse.ArgumentParser(description="Anomaly/IDS micro-demo (paper mode)")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM agent")
    parser.add_argument("--iforest", action="store_true", help="Add IsolationForest baseline")
    parser.add_argument("--thresh", type=float, default=Z_THRESH_DEFAULT, help="Z-score threshold")
    parser.add_argument("--contam", type=float, default=IFOREST_CONTAM_DEFAULT, help="IsolationForest contamination")
    args = parser.parse_args()

    enable_llm = USE_LLM and (not args.no_llm)
    model = os.environ.get("MODEL", "mistral") if enable_llm else ""
    ollama_ver = os.environ.get("OLLAMA_VER", "")  # optional manual note
    run_ts = datetime.utcnow().isoformat() + "Z"

    # Governance: data read
    policy_gate("read_data", {"path": str(DATA)})

    if not DATA.exists():
        from generate_netflow import synth
        df_all = synth()  # default n=300, anomaly_frac=0.12
        DATA.parent.mkdir(parents=True, exist_ok=True)
        df_all.to_csv(DATA, index=False)

    df_all = pd.read_csv(DATA)

    # ---- Fixed evaluation subset (paper-mode) --------------------------------
    if len(df_all) < EVAL_N:
        raise ValueError(f"Dataset has only {len(df_all)} rows; need at least {EVAL_N} for paper mode.")
    if EVAL_MODE == "head":
        df = df_all.head(EVAL_N).copy()
    elif EVAL_MODE == "sample":
        df = df_all.sample(EVAL_N, random_state=SAMPLE_SEED).sort_values("window_id").copy()
    else:
        raise ValueError("EVAL_MODE must be 'head' or 'sample'")
    # -------------------------------------------------------------------------

    features = ["bytes_per_sec", "pkts_per_sec", "syn_rate", "failed_conn_rate"]
    y_true = df["label"].astype(int).tolist()

    # Baseline: Z-score
    z_pred, z_score = zscore_baseline(df, features, thresh=args.thresh, weighted=True)

    # Optional Baseline: IsolationForest
    if args.iforest:
        i_pred, i_score = iforest_baseline(df, features, contamination=args.contam)
    else:
        i_pred, i_score = None, None

    # Agent predictions + rationales
    agent_pred, rationales = [], []
    for _, row in df.iterrows():
        stats = {
            "window_id": int(row["window_id"]),
            "bytes_per_sec": float(row["bytes_per_sec"]),
            "pkts_per_sec": float(row["pkts_per_sec"]),
            "syn_rate": float(row["syn_rate"]),
            "failed_conn_rate": float(row["failed_conn_rate"]),
        }
        if enable_llm:
            lbl, rat = llm_label(stats)
        else:
            # Mirror z-score when LLM disabled to keep schema stable
            lbl, rat = int(z_pred[stats["window_id"]]), "LLM disabled; using z-score baseline."
        agent_pred.append(lbl)
        rationales.append(rat)

    # Metrics
    z_auroc = auroc_safe(y_true, z_score)
    z_rep   = full_report(y_true, z_pred)
    if args.iforest:
        i_auroc = auroc_safe(y_true, i_score)
        i_rep   = full_report(y_true, i_pred)
    a_rep   = full_report(y_true, agent_pred)
    exp_rep = explanation_scores(rationales, y_true, df[features].to_dict("records"))

    # Save per-window results (append with header-if-new)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    need_header = (not OUT.exists()) or OUT.stat().st_size == 0
    dd = df.copy()
    dd["run_ts"]       = run_ts
    dd["eval_n"]       = EVAL_N
    dd["eval_mode"]    = EVAL_MODE
    dd["llm_enabled"]  = int(enable_llm)
    dd["llm_model"]    = model
    dd["ollama_ver"]   = ollama_ver
    dd["z_thresh"]     = args.thresh
    dd["z_pred"]       = z_pred
    dd["z_score"]      = z_score
    if args.iforest:
        dd["iforest_contam"] = args.contam
        dd["iforest_pred"]   = i_pred
        dd["iforest_score"]  = i_score
    else:
        dd["iforest_contam"] = ""
        dd["iforest_pred"]   = ""
        dd["iforest_score"]  = ""
    dd["agent_pred"]      = agent_pred
    dd["agent_rationale"] = rationales
    dd.to_csv(OUT, mode="a", index=False, header=need_header)

    # ---- Tidy summary (pasteable into the paper) -----------------------------
    print("\n=== IDS Micro-Demo: Paper Mode Summary ===")
    print({
        "run_ts": run_ts,
        "eval_n": EVAL_N,
        "eval_mode": EVAL_MODE,
        "llm_enabled": enable_llm,
        "llm_model": model,
        "ollama_ver": ollama_ver
    })

    print("\n--- Baseline: Z-score ---")
    print({
        "AUROC": round(z_auroc, 3),
        "precision": round(z_rep["precision"], 3),
        "recall": round(z_rep["recall"], 3),
        "f1": round(z_rep["f1"], 3),
        "z_thresh": args.thresh
    })

    if args.iforest:
        print("\n--- Baseline: IsolationForest ---")
        print({
            "AUROC": round(i_auroc, 3),
            "precision": round(i_rep["precision"], 3),
            "recall": round(i_rep["recall"], 3),
            "f1": round(i_rep["f1"], 3),
            "contam": args.contam
        })

    print("\n--- Agent (LLM-assisted) ---")
    print({
        "precision": round(a_rep["precision"], 3),
        "recall": round(a_rep["recall"], 3),
        "f1": round(a_rep["f1"], 3)
    })

    print("\n--- Explanation Usefulness (LLM rationales) ---")
    print({
        "consistency_rate": round(exp_rep["consistency_rate"], 3),
        "specificity_rate": round(exp_rep["specificity_rate"], 3)
    })

    print(f"\nSaved per-window results to: {OUT}")
    print(f"Audit log: {AUDIT_LOG_PATH}")
    # -------------------------------------------------------------------------

if __name__ == "__main__":
    main()
