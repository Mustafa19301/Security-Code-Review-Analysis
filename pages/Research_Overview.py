import streamlit as st

from components.ui import (
    inject_theme,
    sidebar_brand,
    page_header,
    section_heading,
    animated_metric_card,
)

st.set_page_config(
    page_title="Research Overview | CodeReview Sentinel",
    layout="wide",
)

inject_theme()
sidebar_brand()

page_header(
    "PROJECT CONTEXT",
    "Research Overview",
    "Analyzing Code Review Dataset for Security Vulnerability Detection. "
    "This project investigates machine-learning methods for identifying "
    "security-related code-review activity across GitHub and Gerrit.",
)

section_heading(
    "Research objectives",
    "The project focuses on data preparation, feature analysis, and model evaluation.",
)

objectives = [
    "Collect and prepare code review data from GitHub and Gerrit.",
    "Extract code diffs and relevant features for analysis.",
    "Investigate patterns associated with security-related changes.",
    "Compare machine-learning approaches for identifying security-related records.",
    "Evaluate model performance, including the impact of class imbalance.",
]

for i, objective in enumerate(objectives, 1):
    st.markdown(
        f'<div class="cr-card" style="margin:.45rem 0">'
        f'<span class="cr-pill">OBJECTIVE {i:02d}</span>'
        f'<span style="margin-left:.7rem">{objective}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.write("")

section_heading(
    "Research data sources",
    "The two platforms serve different analytical purposes.",
)

github_col, gerrit_col = st.columns(2)

with github_col:
    st.markdown(
        """
        <div class="cr-card" style="min-height:205px">
          <div class="cr-eyebrow">SOURCE 01</div>
          <h3>GitHub</h3>
          <p>
            Code-review comments and associated project information
            are used to investigate whether review comments contain
            indicators of security-related discussions.
          </p>
          <span class="cr-pill">COMMENT CLASSIFICATION</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with gerrit_col:
    st.markdown(
        """
        <div class="cr-card" style="min-height:205px">
          <div class="cr-eyebrow">SOURCE 02</div>
          <h3>Gerrit</h3>
          <p>
            The Couchbase Java Client dataset contains review records,
            revisions, review messages, patch metadata, and extracted
            code diffs. The finalized dataset is used for code-diff
            classification.
          </p>
          <span class="cr-pill">CODE-DIFF CLASSIFICATION</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.info(
    "GitHub and Gerrit are analyzed separately. Their models use "
    "different inputs and evaluation setups, so their scores are "
    "not a direct head-to-head comparison."
)

st.write("")

section_heading(
    "Gerrit data collection pipeline",
    "The collection process combines the Gerrit REST API and Git.",
)

pipeline_steps = [
    (
        "01",
        "Gerrit Code Review Platform",
        "Selected the Couchbase Java Client project.",
        "Gerrit",
    ),
    (
        "02",
        "Review Data Collection",
        "Collected review records, revision information, general "
        "review messages, and patch metadata.",
        "Gerrit REST API",
    ),
    (
        "03",
        "Code Diff Extraction",
        "Fetched revisions using Git and compared code versions "
        "to extract added and deleted code.",
        "Git",
    ),
    (
        "04",
        "Data Processing",
        "Cleaned records, expanded the security-related dataset, "
        "prepared classification labels, and retained revisions "
        "with non-empty code diffs.",
        "Python · Pandas",
    ),
    (
        "05",
        "Feature Engineering",
        "Generated TF-IDF text features and structured measurements "
        "describing code changes.",
        "Python · Scikit-learn",
    ),
    (
        "06",
        "Model Training and Evaluation",
        "Compared class-imbalance strategies using grouped "
        "cross-validation and evaluated model performance.",
        "Scikit-learn · Imbalanced-learn",
    ),
]

for number, title, description, technology in pipeline_steps:
    with st.container(border=True):
        left, right = st.columns([1, 9])

        with left:
            st.markdown(
                f"""
                <div style="
                    font-family:Space Grotesk;
                    font-size:1.5rem;
                    color:#60a5fa;
                    font-weight:700
                ">
                    {number}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with right:
            st.markdown(f"**{title}**")
            st.write(description)
            st.caption(f"Tools: {technology}")

st.write("")

section_heading(
    "Gerrit collection summary",
    "Original collection totals from the Couchbase Java Client project.",
)

metrics = st.columns(4)

collection_metrics = [
    ("Reviews", 916),
    ("Revisions", 2635),
    ("Review messages", 5440),
    ("Patch-file records", 11750),
]

for col, (label, value) in zip(metrics, collection_metrics):
    with col:
        animated_metric_card(
            label,
            value,
            note="Collected records",
            duration=1300,
        )

st.caption(
    "These figures represent the original collection totals. "
    "Not every collected revision contained a usable code diff."
)

st.write("")

section_heading(
    "Finalized Gerrit modelling dataset",
    "The expanded dataset is the primary dataset used for Gerrit model training and evaluation.",
)

dataset_metrics = st.columns(4)

finalized_metrics = [
    ("Modelling revisions", 1774),
    ("Not security-related", 1382),
    ("Security-related", 392),
    ("Review groups", 808),
]

for col, (label, value) in zip(dataset_metrics, finalized_metrics):
    with col:
        animated_metric_card(
            label,
            value,
            note="Finalized dataset",
            duration=1300,
        )

negative_percentage = (1382 / 1774) * 100
positive_percentage = (392 / 1774) * 100

st.markdown("**Finalized dataset class distribution**")

distribution_col1, distribution_col2 = st.columns(2)

with distribution_col1:
    st.metric(
        "Not security-related",
        f"{negative_percentage:.1f}%",
        help="1,382 revisions",
    )

with distribution_col2:
    st.metric(
        "Security-related",
        f"{positive_percentage:.1f}%",
        help="392 revisions",
    )

st.progress(
    positive_percentage / 100,
    text="Proportion of security-related revisions",
)

st.caption(
    "The finalized modelling dataset contains 1,774 revisions "
    "with non-empty code diffs. Each revision is assigned to a "
    "review group using its review number."
)

st.warning(
    "Collection limitation: Gerrit's inline-comment endpoints "
    "required authentication and returned HTTP 403 errors. "
    "Consequently, general review messages were collected instead "
    "of inline comments."
)

st.write("")

section_heading("Machine-learning methodology")

method_left, method_right = st.columns(2)

with method_left:
    st.markdown(
        """
        <div class="cr-card">
          <div class="cr-eyebrow">GERRIT · CODE DIFF</div>
          <h3>Text processing</h3>
          <ul>
            <li>Input: extracted code diffs</li>
            <li>TF-IDF feature extraction</li>
            <li>Unigrams and bigrams</li>
            <li>Up to 5,000 text features</li>
            <li>Logistic Regression</li>
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

with method_right:
    st.markdown(
        """
        <div class="cr-card">
          <div class="cr-eyebrow">EVALUATION</div>
          <h3>Validation strategy</h3>
          <ul>
            <li>Random oversampling and class-weighting experiments</li>
            <li>Five-fold Stratified Group Cross-Validation</li>
            <li>Reviews grouped by review number</li>
            <li>Oversampling applied to training folds only</li>
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("### GitHub comment analysis")

st.write(
    "The GitHub experiments use review comment text to classify "
    "whether a comment is security-related. This is separate from "
    "the Gerrit code-diff model."
)

st.divider()

section_heading("Research scope and interpretation")

st.info(
    "CodeReview Sentinel is a research prototype intended to "
    "support the identification of potentially security-related "
    "code changes. A security-related prediction does not "
    "independently confirm that a code change contains an "
    "exploitable vulnerability. Predictions require developer review."
)