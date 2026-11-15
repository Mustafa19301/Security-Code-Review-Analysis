import streamlit as st

from components.ui import inject_theme, sidebar_brand, page_header, metric_card

st.set_page_config(
    page_title="CodeReview Sentinel",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()
sidebar_brand()

page_header(
    "SECURITY RESEARCH PLATFORM",
    "CodeReview Sentinel",
    "An interactive research workspace for exploring code review datasets "
    "and machine learning approaches to identifying security related changes.",
)

st.markdown(
    """
    <div class="cr-pill">RESEARCH PROTOTYPE · GITHUB + GERRIT</div>
    """,
    unsafe_allow_html=True,
)
st.write("")

section_col1, section_col2, section_col3 = st.columns(3)

with section_col1:
    metric_card("Research sources", "02", "GitHub and Gerrit")

with section_col2:
    metric_card("Analysis approach", "Supervised ML", "Text-based classification")

with section_col3:
    metric_card(
        "Gerrit evaluation",
        "5-fold",
        "Stratified Group Cross-Validation",
    )

st.write("")
st.markdown("## Explore the workspace")

st.markdown(
    '<div class="cr-section-note">'
    'Choose a research area from the sidebar navigation.'
    '</div>',
    unsafe_allow_html=True,
)

cards = [
    (
        "01",
        "Research Overview",
        "Research objectives, data sources, collection pipeline, and methodology.",
    ),
    (
        "02",
        "Dataset Explorer",
        "Inspect finalized GitHub and Gerrit datasets and their data quality.",
    ),
    (
        "03",
        "Model Performance",
        "Compare evaluation metrics while keeping the two datasets separate.",
    ),
    (
        "04",
        "Code Review Analyzer",
        "Submit a Git diff to receive a security related classification.",
    ),
    (
        "05",
        "Error Analysis",
        "Inspect false positives, false negatives, and model limitations.",
    ),
]

for start in range(0, len(cards), 2):
    cols = st.columns(2)

    for col, item in zip(cols, cards[start:start + 2]):
        number, title, description = item

        with col:
            st.markdown(
                f"""
                <div class="cr-card" style="margin-bottom:1rem;min-height:130px">
                  <div class="cr-card-label">{number} / RESEARCH MODULE</div>
                  <div style="font-family:'Space Grotesk';font-size:1.2rem;
                              font-weight:700;margin:.35rem 0">
                    {title}
                  </div>
                  <div style="color:#9fb0c5;font-size:.9rem">
                    {description}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.divider()

st.info(
    "Interpret model outputs as screening signals for potentially "
    "security related changes. They do not independently confirm "
    "exploitable vulnerabilities."
)

st.caption("CodeReview Sentinel · University Research Prototype")