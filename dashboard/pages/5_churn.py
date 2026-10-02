import plotly.express as px
import streamlit as st

from shared import PALETTE, require

st.set_page_config(page_title="Churn", layout="wide")
st.title("Churn")
st.caption(
    "Model comparison and risk ranking from results/, written by the churn notebooks. "
    "Churn means no card transaction for about a year (docs/assumptions.md, A2)."
)

models = require("churn_models", source="results")
preds = require("churn_predictions", source="results")

models = models[models["run"] == models["run"].max()]
best = models.sort_values("accuracy_at_threshold", ascending=False).iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Best model", f"{best['model']} / {best['feature_set']}")
c2.metric("Accuracy", f"{best['accuracy_at_threshold']:.1%}", help=f"at threshold {best['threshold']}")
c3.metric("AUC", f"{best['auc']:.3f}")
c4.metric("Predicted churn rate", f"{preds['churned'].mean():.1%}", help=f"{len(preds):,} customers to predict")

st.subheader("Model comparison")
metric = st.selectbox("Metric", ["accuracy", "auc", "log_loss", "brier"])
fig = px.bar(
    models, x="model", y=metric, color="feature_set", barmode="group", color_discrete_sequence=PALETTE
)
fig.update_layout(legend_title_text="feature set")
if metric in ("accuracy", "auc"):
    fig.update_yaxes(range=[models[metric].min() - 0.02, models[metric].max() + 0.01])
st.plotly_chart(fig, width="stretch")
st.caption(f"Run {best['run']}, 5-fold x 3 repeats on identical folds.")

st.subheader("Risk ranking")
fig = px.histogram(preds, x="churn_probability", nbins=50, color="churned", color_discrete_sequence=PALETTE)
fig.update_layout(legend_title_text="predicted churned")
st.plotly_chart(fig, width="stretch")

st.write("Highest risk customers")
top = preds.nlargest(20, "churn_probability").drop(columns="customer_id").reset_index(drop=True)
top.insert(0, "rank", top.index + 1)
st.dataframe(top, width="stretch")
st.caption(
    "Customer ids are withheld. Issue 12 allows aggregated or masked ids only, and these "
    "pages get screenshotted for the submission (README, Workflow)."
)

with st.expander("Show all models"):
    st.dataframe(models)
