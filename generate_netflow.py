# generate_netflow.py
import numpy as np
import pandas as pd
from pathlib import Path
rng = np.random.default_rng(7)

OUT = Path(__file__).parent / "data" / "netflow_windows.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

def synth(n=300, anomaly_frac=0.12):
    t = np.arange(n)
    # Base behaviors (stationary-ish with gentle drift)
    bytes_per_sec = rng.normal(5e5 + 2e4*np.sin(t/30), 6e4, n)
    pkts_per_sec = rng.normal(1200 + 80*np.cos(t/25), 120, n)
    syn_rate = rng.normal(40 + 4*np.sin(t/12), 6, n)
    failed_rate = rng.normal(0.02, 0.01, n).clip(0, 1)

    # Inject anomalies in random windows: spikes or bursts
    y = np.zeros(n, dtype=int)
    k = int(anomaly_frac * n)
    idx = rng.choice(n, size=k, replace=False)
    for i in idx:
        mode = rng.integers(0, 3)
        if mode == 0:  # volumetric burst
            bytes_per_sec[i] *= rng.uniform(2.2, 3.5)
            pkts_per_sec[i]  *= rng.uniform(1.8, 2.5)
        elif mode == 1:  # SYN flood-like
            syn_rate[i]      *= rng.uniform(3.0, 6.0)
            pkts_per_sec[i]  *= rng.uniform(1.5, 2.2)
        else:  # failed-conn storm / brute-force
            failed_rate[i]   = min(1.0, failed_rate[i] + rng.uniform(0.2, 0.6))
            pkts_per_sec[i]  *= rng.uniform(1.2, 1.8)
        y[i] = 1

    df = pd.DataFrame({
        "window_id": np.arange(n),
        "bytes_per_sec": bytes_per_sec.clip(1e4, None),
        "pkts_per_sec":  pkts_per_sec.clip(10, None),
        "syn_rate":      syn_rate.clip(0, None),
        "failed_conn_rate": failed_rate,
        "label": y
    })
    return df

if __name__ == "__main__":
    df = synth()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Wrote {OUT} with shape {df.shape}")
