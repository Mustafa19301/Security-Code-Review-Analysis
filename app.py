import streamlit as st

st.set_page_config(
    page_title="CodeReview Sentinel",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = {
    "RESEARCH WORKFLOW": [
        st.Page(
            "pages/Home.py",
            title="Home",
            url_path="home",
            default=True,
        ),
        st.Page(
            "pages/Research_Overview.py",
            title="Research Overview",
        ),
        st.Page(
            "pages/Dataset_Explorer.py",
            title="Dataset Explorer",
        ),
        st.Page(
            "pages/Model_Performance.py",
            title="Model Performance",
        ),
        st.Page(
            "pages/Code_Review_Analyzer.py",
            title="Code Review Analyzer",
        ),
        st.Page(
            "pages/Error_Analysis.py",
            title="Error Analysis",
        ),
    ],
}

navigation = st.navigation(pages, position="sidebar")
navigation.run()