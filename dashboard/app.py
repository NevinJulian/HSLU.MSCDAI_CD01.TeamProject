import streamlit as st

st.set_page_config(page_title="Customer Analytics", layout="wide")

st.title("Customer Analytics Dashboard")
st.caption("HSLU MSc Applied Data Science & AI · CD01 Team Project")

st.markdown(
    """
    Use the pages in the sidebar.

    - **Overview** — activity, spend, churn and leakage at a glance
    - **Share of wallet** — counterpart shares per category over time
    - **Wallet leakage** — where money leaves the wallet
    - **Segments** — cluster map and profiles
    - **Churn** — model comparison and risk ranking
    - **Data & method** — sources, cleaning, CRISP-DM mapping
    """
)