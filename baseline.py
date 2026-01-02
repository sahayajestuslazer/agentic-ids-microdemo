# baseline.py
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

def zscore_baseline(df, features, thresh=3.0, weighted=False):
    X = df[features].values.astype(float)
    mu = X.mean(axis=0)
    sd = X.std(axis=0) + 1e-9
    z = np.abs((X - mu) / sd)
    if weighted:
        # Heavier weight to syn_rate and failed_conn_rate
        w = np.ones(len(features))
        for i, f in enumerate(features):
            if f in ("syn_rate", "failed_conn_rate"):
                w[i] = 1.6
        score = (z * w).mean(axis=1)
    else:
        score = z.mean(axis=1)
    pred = (score >= thresh).astype(int)
    return pred, score

def iforest_baseline(df, features, contamination=0.1, seed=42):
    X = df[features].values.astype(float)
    Xs = StandardScaler().fit_transform(X)
    clf = IsolationForest(
        n_estimators=200, max_samples="auto", contamination=contamination,
        random_state=seed, n_jobs=-1
    )
    clf.fit(Xs)
    # predict: -1 anomaly, 1 normal
    pred = (clf.predict(Xs) == -1).astype(int)
    score = -clf.decision_function(Xs)  # higher = more anomalous
    return pred, score
