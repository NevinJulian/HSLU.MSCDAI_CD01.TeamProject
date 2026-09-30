"""Scores all customers with the tuned XGBoost churn model. Usage: python src/score_customers.py"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
from xgboost import XGBClassifier

from src.churn import RESULTS, feature_matrix, train_predict_split
from src.data import PROCESSED, load_customer_table
from src.features import build_customer_features

OUT = PROCESSED / "customer_churn_scores.csv"


def score_all(feature_set: str = "engineered", params_file: Path = RESULTS / "best_params.json") -> pd.DataFrame:
    params = json.loads(params_file.read_text())["xgboost"]
    feats = build_customer_features(load_customer_table())
    X_train, y_train, _, _ = train_predict_split(feats, feature_set)
    model = XGBClassifier(**params, random_state=0, n_jobs=-1, tree_method="hist", eval_metric="logloss")
    model.fit(X_train, y_train)

    out = feats[["customer_id", "split", "churned"]].copy()
    out["churn_probability"] = model.predict_proba(feature_matrix(feats, feature_set))[:, 1].astype(float)
    out["source"] = "model"

    # labelled customers get their out-of-fold probability, in-sample ones are too confident
    oof_file = RESULTS / "oof_predictions_v2.csv"
    if oof_file.exists():
        oof = pd.read_csv(oof_file).set_index("customer_id")["oof_xgboost"]
        is_train = out["split"] == "train"
        out.loc[is_train, "churn_probability"] = out.loc[is_train, "customer_id"].map(oof).to_numpy()
        out.loc[is_train, "source"] = "oof"
    out["churn_probability"] = out["churn_probability"].round(4)
    return out


def main() -> None:
    scores = score_all()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(OUT, index=False)
    print(f"written {OUT.relative_to(ROOT)}, {len(scores)} customers, mean probability {scores['churn_probability'].mean():.3f}")


if __name__ == "__main__":
    main()
