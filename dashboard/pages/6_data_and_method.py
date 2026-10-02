import pandas as pd
import streamlit as st

from shared import ROOT, load

st.set_page_config(page_title="Data & method", layout="wide")
st.title("Data & method")

TABLES = {
    "customer_data_clean": "processed",
    "customer_features": "processed",
    "sow_category_clean": "processed",
    "sow_category_counterpart_clean": "processed",
    "churn_models": "results",
    "churn_predictions": "results",
}

DOCS = {
    "Cleaning": ROOT / "docs" / "data_preparation.md",
    "Assumptions": ROOT / "docs" / "assumptions.md",
}

sources, *doc_tabs = st.tabs(["Sources", *DOCS])

with sources:
    rows = []
    for name, source in TABLES.items():
        try:
            df = load(name, source)
            rows.append({"table": name, "from": source, "rows": len(df), "columns": df.shape[1]})
        except FileNotFoundError:
            rows.append({"table": name, "from": source, "rows": None, "columns": None})
    st.dataframe(pd.DataFrame(rows), width="stretch")
    st.caption(
        "Cleaned tables come from `python src/clean_data.py`, model output from the churn "
        "notebooks. data/ and results/ are gitignored, so no customer ids live in the repo."
    )

for tab, path in zip(doc_tabs, DOCS.values()):
    with tab:
        st.markdown(path.read_text(encoding="utf-8"))
