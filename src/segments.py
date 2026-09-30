"""Customer segmentation: feature selection, k-means, stable labels, profiles."""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from src.data import PROCESSED

CLUSTER_FEATURES = [
    "log_n_transactions", "log_days_active", "amt_per_tx", "cp_per_tx", "ecom_perc", "foreign_tx_share",
    "cat_groceries_share", "cat_restaurants_share", "cat_shopping_share", "cat_holidays_share",
    "cat_transport_share", "cat_entertainment_share", "cat_communication_share",
]

PROFILE_COLUMNS = {
    "total_amount": "median", "n_transactions": "median", "days_active": "median", "amt_per_tx": "median",
    "ecom_perc": "median", "foreign_tx_share": "median", "n_categories": "median",
    "cat_groceries_share": "mean", "cat_restaurants_share": "mean", "cat_shopping_share": "mean",
    "cat_holidays_share": "mean", "cat_transport_share": "mean", "cat_entertainment_share": "mean",
    "cat_communication_share": "mean", "leak_share": "mean", "cat_savings_share": "mean",
}


def cluster_matrix(feats: pd.DataFrame) -> tuple[np.ndarray, StandardScaler]:
    X = feats[CLUSTER_FEATURES].copy()
    X["amt_per_tx"] = np.log1p(X["amt_per_tx"])
    scaler = StandardScaler().fit(X)
    return scaler.transform(X), scaler


def kmeans_scan(Z: np.ndarray, ks=range(3, 10), seeds=(1, 2, 3), sample: int = 2500, seed: int = 0) -> pd.DataFrame:
    """Silhouette, Davies-Bouldin and seed stability (ARI) per k."""
    idx = np.random.default_rng(seed).choice(len(Z), min(sample, len(Z)), replace=False)
    rows = []
    for k in ks:
        km = KMeans(k, n_init=10, random_state=seed).fit(Z)
        ari = np.mean([adjusted_rand_score(km.labels_, KMeans(k, n_init=10, random_state=s).fit_predict(Z)) for s in seeds])
        rows.append({"k": k, "inertia": km.inertia_, "silhouette": silhouette_score(Z[idx], km.labels_[idx]),
                     "davies_bouldin": davies_bouldin_score(Z, km.labels_), "ari_seeds": ari,
                     "smallest": int(np.bincount(km.labels_).min())})
    return pd.DataFrame(rows).set_index("k")


def fit_kmeans(Z: np.ndarray, k: int, seed: int = 0) -> KMeans:
    return KMeans(k, n_init=10, random_state=seed).fit(Z)


def relabel_by_spend(labels: np.ndarray, feats: pd.DataFrame) -> np.ndarray:
    """Renumber clusters 0..k-1 by descending median total_amount so ids are stable."""
    order = feats.assign(_c=labels).groupby("_c")["total_amount"].median().sort_values(ascending=False).index
    mapping = {old: new for new, old in enumerate(order)}
    return np.array([mapping[c] for c in labels])


def profile(feats: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    df = feats.assign(cluster=labels)
    out = df.groupby("cluster").agg(n=("customer_id", "size"), **{c: (c, f) for c, f in PROFILE_COLUMNS.items()})
    out["share_customers"] = out["n"] / len(df)
    out["share_spend"] = df.groupby("cluster")["total_amount"].sum() / df["total_amount"].sum()
    if "churned" in df:
        out["churn_rate"] = df.groupby("cluster")["churned"].apply(lambda s: s.dropna().astype(bool).mean())
    return out


def save_clusters(feats: pd.DataFrame, labels: np.ndarray, names: dict[int, str], path=PROCESSED / "customer_clusters.csv") -> pd.DataFrame:
    out = pd.DataFrame({"customer_id": feats["customer_id"], "cluster": labels})
    out["cluster_name"] = out["cluster"].map(names)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(path, index=False)
    return out
