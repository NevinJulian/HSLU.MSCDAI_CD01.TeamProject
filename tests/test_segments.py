import numpy as np

from src.data import load_customer_table
from src.features import build_customer_features
from src.segments import CLUSTER_FEATURES, cluster_matrix, fit_kmeans, profile, relabel_by_spend


def test_cluster_pipeline_is_stable():
    feats = build_customer_features(load_customer_table())
    Z, _ = cluster_matrix(feats)
    assert Z.shape == (len(feats), len(CLUSTER_FEATURES))
    assert np.isfinite(Z).all()
    labels = relabel_by_spend(fit_kmeans(Z, 6).labels_, feats)
    assert set(labels) == set(range(6))
    prof = profile(feats, labels)
    assert prof["total_amount"].is_monotonic_decreasing
    assert prof["n"].min() >= 100
    assert abs(prof["share_spend"].sum() - 1) < 1e-9
