"""Checks on the churn helpers: feature matrix hygiene and hand-in validation."""

import numpy as np
import pytest

from src.churn import FEATURE_SETS, TENURE_COLUMNS, feature_matrix, train_predict_split, write_handin
from src.data import load_customer_table, load_predict
from src.features import build_customer_features


@pytest.fixture(scope="module")
def feats():
    return build_customer_features(load_customer_table())


def test_feature_matrix_is_numeric_and_label_free(feats):
    for fs in FEATURE_SETS:
        X = feature_matrix(feats, fs)
        assert len(X) == len(feats)
        assert (X.dtypes == float).all()
        assert np.isfinite(X.to_numpy()).all()
        assert not {"customer_id", "churned", "split"} & set(X.columns)


def test_no_tenure_set_drops_tenure(feats):
    X = feature_matrix(feats, "no_tenure")
    assert not set(TENURE_COLUMNS) & set(X.columns)
    assert "n_transactions" in X.columns


def test_train_predict_split(feats):
    X_train, y, X_pred, ids = train_predict_split(feats)
    assert len(X_train) == len(y) == 3903
    assert len(X_pred) == len(ids) == 1673
    assert set(ids) == set(load_predict()["customer_id"])
    assert set(np.unique(y)) == {0, 1}


def test_write_handin_validates_ids(feats, tmp_path):
    _, _, _, ids = train_predict_split(feats)
    proba = np.full(len(ids), 0.6)
    out = write_handin(ids, proba, 0.5, path=tmp_path / "p.csv")
    assert out["churned"].all() and len(out) == 1673
    with pytest.raises(AssertionError):
        write_handin(ids[:-1], proba[:-1], 0.5, path=tmp_path / "bad.csv")
    with pytest.raises(AssertionError):
        write_handin(np.append(ids[:-1], -1), proba, 0.5, path=tmp_path / "bad2.csv")


def test_rank_average_and_stack():
    import pandas as pd

    from src.churn import fit_stack, rank_average

    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 500)
    p1 = np.clip(y * 0.6 + rng.normal(0, 0.3, 500), 0, 1)
    p2 = np.clip(y * 0.5 + rng.normal(0, 0.3, 500), 0, 1)
    r = rank_average([p1, p2])
    assert r.min() >= 0 and r.max() <= 1 and len(r) == 500
    meta = fit_stack(pd.DataFrame({"a": p1, "b": p2}), y)
    assert meta.predict_proba(pd.DataFrame({"a": p1, "b": p2})).shape == (500, 2)
