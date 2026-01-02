# retriever.py
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

DATA = Path(__file__).parent / "data" / "rag_corpus.txt"

def load_corpus():
    if not DATA.exists():
        DATA.write_text(
            "- Volumetric anomalies: sharp spikes in bytes_per_sec AND pkts_per_sec.\n"
            "- SYN flood indicators: large syn_rate increase with moderate pkt surge.\n"
            "- Brute-force / failed auth: elevated failed_conn_rate over baseline.\n"
            "- Benign periodicity: slow sinusoidal drift in pkts_per_sec/bytes_per_sec.\n"
            "- Multi-signal anomalies are more suspicious than single-metric noise.\n",
            encoding="utf-8"
        )
    lines = [ln.strip() for ln in DATA.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return lines

def build_vect(corpus):
    vec = TfidfVectorizer()
    X = vec.fit_transform(corpus)
    return vec, X

def retrieve_snippets(stats_dict, topk=2):
    # Make a terse query from the window stats
    q = (
        f"bytes_per_sec={stats_dict['bytes_per_sec']:.0f} "
        f"pkts_per_sec={stats_dict['pkts_per_sec']:.0f} "
        f"syn_rate={stats_dict['syn_rate']:.2f} "
        f"failed_conn_rate={stats_dict['failed_conn_rate']:.3f}"
    )
    corpus = load_corpus()
    vec, X = build_vect(corpus)
    qv = vec.transform([q])
    sims = linear_kernel(qv, X)[0]
    idx = sims.argsort()[::-1][:topk]
    return [corpus[i] for i in idx]
