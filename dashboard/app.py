import streamlit as st

st.set_page_config(page_title="Customer Analytics", layout="wide")

st.title("Customer Analytics Dashboard")
st.caption("HSLU MSc Applied Data Science & AI · CD01 Team Project")

st.markdown(
    """
    Use the pages in the sidebar.

    - **Overview** — activity, leakage and churn at a glance, who the customers are
    - **Share of wallet** — how the card wallet splits across categories and counterparts
    - **Wallet leakage** — where money leaves, who sends it, and how it relates to churn
    - **Segments** — six customer segments, their spend mix, leakage and churn
    - **Churn** — model comparison, risk ranking, churn by segment
    - **Data & method** — sources, cleaning, assumptions, findings per issue

    Controls live on each page: a period slider in the sidebar for the charts over
    time, highlight and break-down selectors next to the charts.
    """
)
