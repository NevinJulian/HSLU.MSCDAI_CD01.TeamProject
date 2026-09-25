"""Churn modelling helpers: feature matrix, cross-validation, threshold, hand-in.

    from src.churn import feature_matrix, cross_validate, best_threshold, write_handin

Everything is deliberately plain scikit-learn so every model in the comparison
runs on identical folds and the numbers in results/churn_models.csv are
comparable. Models are passed in, this module does not choose them.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold

from src.data import ROOT, load_predict

ID, TARGET, SPLIT = "customer_id", "churned", "split"
RESULTS = ROOT / "results"

# The columns of customer_data.csv after cleaning, i.e. what the course gave us.
RAW_COLUMNS_PREFIX = ("n_", "total_amount", "days_active", "pos_perc", "ecom_perc", "cat_", "cur_", "country_")

# Everything that encodes how long or how recently the card was used. Dropped in
# the "no_tenure" set to see how much of the label is tenure alone.
TENURE_COLUMNS = ["days_active", "log_days_active", "tx_per_day", "amt_per_day", "tenure_bucket", "is_one_day"]

FEATURE_SETS = {
    "raw": "the original customer columns only",
    "engineered": "raw + ratios, shares, leakage, international, logs, tenure bucket",
    "no_tenure": "engineered without days_active and everything derived from it",
}


# --------------------------------------------------------------------------- features
def feature_matrix(feats: pd.DataFrame, feature_set: str = "engineered") -> pd.DataFrame:
    """Numeric feature matrix from build_customer_features() output.

    Booleans become 0/1, the ordered tenure bucket becomes its code (0..8).
    Label and split columns are never included.
    """
    if feature_set not in FEATURE_SETS:
        raise ValueError(f"feature_set must be one of {list(FEATURE_SETS)}")
    X = feats.drop(columns=[c for c in (ID, TARGET, SPLIT) if c in feats.columns]).copy()

    if feature_set == "raw":
        raw = [c for c in X.columns if c.startswith(RAW_COLUMNS_PREFIX) and not c.endswith("_share")
               and not c.startswith("n_categories") and not c.startswith("n_currencies")]
        X = X[raw]
    elif feature_set == "no_tenure":
        X = X.drop(columns=[c for c in TENURE_COLUMNS if c in X.columns])

    if "tenure_bucket" in X.columns:
        X["tenure_bucket"] = X["tenure_bucket"].cat.codes.astype(int)
    for c in X.columns[X.dtypes == bool]:
        X[c] = X[c].astype(int)
    return X.astype(float)


def train_predict_split(feats: pd.DataFrame, feature_set: str = "engineered"):
    """(X_train, y_train, X_predict, predict_ids) from a feature table with split."""
    train, pred = feats[feats[SPLIT] == "train"], feats[feats[SPLIT] == "predict"]
    X_train = feature_matrix(train, feature_set)
    y_train = train[TARGET].astype(bool).astype(int).to_numpy()
    X_pred = feature_matrix(pred, feature_set)
    return X_train, y_train, X_pred, pred[ID].to_numpy()


# --------------------------------------------------------------------------- evaluation
def cross_validate(model, X: pd.DataFrame, y: np.ndarray, n_splits: int = 5, n_repeats: int = 3,
                   seed: int = 0) -> tuple[np.ndarray, dict]:
    """Repeated stratified k-fold. Returns out-of-fold probabilities (averaged over
    repeats) and metrics as mean ± std over repeats at threshold 0.5."""
    cv = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=n_repeats, random_state=seed)
    oof = np.zeros((n_repeats, len(y)))
    per_repeat = []
    for i, (tr, te) in enumerate(cv.split(X, y)):
        r = i // n_splits
        m = clone(model).fit(X.iloc[tr], y[tr])
        oof[r, te] = m.predict_proba(X.iloc[te])[:, 1]
        if (i + 1) % n_splits == 0:
            per_repeat.append(oof_metrics(y, oof[r]))
    summary = {k: (np.mean([d[k] for d in per_repeat]), np.std([d[k] for d in per_repeat])) for k in per_repeat[0]}
    return oof.mean(axis=0), summary


def oof_metrics(y: np.ndarray, p: np.ndarray, threshold: float = 0.5) -> dict:
    return {
        "accuracy": accuracy_score(y, p >= threshold),
        "auc": roc_auc_score(y, p),
        "log_loss": log_loss(y, np.clip(p, 1e-6, 1 - 1e-6)),
        "brier": brier_score_loss(y, p),
    }


def best_threshold(y: np.ndarray, p: np.ndarray, grid: np.ndarray | None = None) -> tuple[float, float]:
    """Threshold that maximises accuracy on out-of-fold probabilities. Ties go to
    the value closest to 0.5."""
    grid = np.round(np.arange(0.30, 0.701, 0.005), 3) if grid is None else grid
    acc = np.array([accuracy_score(y, p >= t) for t in grid])
    best = np.flatnonzero(acc == acc.max())
    t = grid[best[np.argmin(np.abs(grid[best] - 0.5))]]
    return float(t), float(acc.max())


def summary_row(name: str, feature_set: str, metrics: dict, threshold: float | None = None,
                accuracy_at_threshold: float | None = None) -> dict:
    row = {"model": name, "feature_set": feature_set}
    for k, (m, s) in metrics.items():
        row[k] = round(m, 4)
        row[f"{k}_std"] = round(s, 4)
    row["threshold"] = threshold
    row["accuracy_at_threshold"] = None if accuracy_at_threshold is None else round(accuracy_at_threshold, 4)
    return row


def save_results(rows: list[dict], path: Path = RESULTS / "churn_models.csv") -> pd.DataFrame:
    """Append rows to the results table (results/ is gitignored)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    new = pd.DataFrame(rows)
    new.insert(0, "run", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))
    if path.exists():
        new = pd.concat([pd.read_csv(path), new], ignore_index=True)
    new.to_csv(path, index=False)
    return new


# --------------------------------------------------------------------------- hand-in
def write_handin(ids: np.ndarray, proba: np.ndarray, threshold: float,
                 path: Path = RESULTS / "churn_predictions.csv") -> pd.DataFrame:
    """Write customer_id, churned, churn_probability for the predict set and
    check it against customer_data_predict.csv before writing."""
    out = pd.DataFrame({ID: ids, TARGET: proba >= threshold, "churn_probability": np.round(proba, 4)})
    expected = set(load_predict()[ID])
    assert len(out) == len(expected) == 1673, f"expected 1673 rows, got {len(out)}"
    assert out[ID].is_unique, "duplicate customer ids"
    assert set(out[ID]) == expected, "ids do not match customer_data_predict.csv"
    assert out["churn_probability"].between(0, 1).all()
    path.parent.mkdir(parents=True, exist_ok=True)
    out.sort_values(ID).to_csv(path, index=False)
    return out


# --------------------------------------------------------------------------- tuning
def tune(make_model, param_space, X: pd.DataFrame, y: np.ndarray, n_trials: int = 50,
          n_splits: int = 5, seed: int = 0, cache: Path | None = None, name: str | None = None) -> dict:
    """Optuna search minimising out-of-fold log loss on a single stratified
    k-fold. `make_model(params)` returns an estimator, `param_space(trial)` a
    params dict. With `cache` and `name`, the best params are stored in a JSON
    file and reused on the next run, so tuning happens once."""
    import json

    import optuna
    from sklearn.model_selection import StratifiedKFold

    if cache is not None and name is not None and cache.exists():
        stored = json.loads(cache.read_text())
        if name in stored:
            return stored[name]

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    folds = list(StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed).split(X, y))

    def objective(trial):
        params = param_space(trial)
        p = np.zeros(len(y))
        for tr, te in folds:
            m = make_model(params).fit(X.iloc[tr], y[tr])
            p[te] = m.predict_proba(X.iloc[te])[:, 1]
        return log_loss(y, np.clip(p, 1e-6, 1 - 1e-6))

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    best = study.best_params

    if cache is not None and name is not None:
        stored = json.loads(cache.read_text()) if cache.exists() else {}
        stored[name] = best
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(stored, indent=2))
    return best


# --------------------------------------------------------------------------- ensembles
def rank_average(probas: list[np.ndarray]) -> np.ndarray:
    """Average of per-model probability ranks, scaled to [0, 1]. Robust to
    models with different calibration."""
    from scipy.stats import rankdata

    ranks = [rankdata(p) / len(p) for p in probas]
    return np.mean(ranks, axis=0)


def fit_stack(oof: pd.DataFrame, y: np.ndarray, C: float = 1.0):
    """Logistic regression on the out-of-fold probabilities of the base models.
    The base probabilities are already out-of-sample, the meta-model's own
    cross-validation is done by the caller (cross_validate on the same table)."""
    from sklearn.linear_model import LogisticRegression

    return LogisticRegression(C=C, max_iter=2000).fit(oof, y)
