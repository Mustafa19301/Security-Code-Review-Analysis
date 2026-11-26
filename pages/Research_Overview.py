import streamlit as st

from components.ui import (
    inject_theme,
    sidebar_brand,
    page_header,
    section_heading,
    animated_metric_card,
)

inject_theme()
sidebar_brand()

page_header(
    "PROJECT CONTEXT",
    "Research Overview",
    "Analyzing Code Review Dataset for Security Vulnerability Detection. "
    "This project investigates machine learning methods for identifying "
    "security related code review activity across GitHub and Gerrit.",
)

section_heading(
    "Research objectives",
    "The project focuses on data preparation, feature analysis, and model evaluation.",
)

objectives = [
    "Collect and prepare code review data from GitHub and Gerrit.",
    "Extract code diffs and relevant features for analysis.",
    "Investigate patterns associated with security related changes.",
    "Compare machine learning approaches for identifying security related records.",
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
            indicators of security related discussions.
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
    "not a direct head to head comparison."
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
        "Cleaned records, expanded the security related dataset, "
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
    ("Not security related", 1382),
    ("Security related", 392),
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
        "Not security related",
        f"{negative_percentage:.1f}%",
        help="1,382 revisions",
    )

with distribution_col2:
    st.metric(
        "Security related",
        f"{positive_percentage:.1f}%",
        help="392 revisions",
    )

st.progress(
    positive_percentage / 100,
    text="Proportion of security related revisions",
)

st.caption(
    "The finalized modelling dataset contains 1,774 revisions "
    "with non empty code diffs. Each revision is assigned to a "
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
    "whether a comment is security related. This is separate from "
    "the Gerrit code-diff model."
)

st.write("")

section_heading(
    "Gerrit feature extension experiments",
    "Additional experiments investigated whether alternative text representations "
    "and security sensitive code indicators could improve classification performance.",
)

st.write(
    "The original Gerrit model used TF-IDF to represent code diffs. "
    "The feature extension experiments explored Word2Vec embeddings "
    "and manually engineered indicators based on security sensitive "
    "Java APIs and coding patterns."
)

feature_col1, feature_col2 = st.columns(2)

with feature_col1:
    st.markdown(
        """
        <div class="cr-card" style="min-height:230px">
          <div class="cr-eyebrow">TEXT REPRESENTATION</div>
          <h3>Word2Vec embeddings</h3>
          <p>
            Word2Vec learned 100-dimensional word representations
            from the training-fold code diffs. The word vectors
            were averaged to create a numerical representation
            for each code diff.
          </p>
          <span class="cr-pill">100-DIMENSIONAL VECTORS</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with feature_col2:
    st.markdown(
        """
        <div class="cr-card" style="min-height:230px">
          <div class="cr-eyebrow">FEATURE ENGINEERING</div>
          <h3>Security sensitive API indicators</h3>
          <p>
            Regex-based indicators counted selected security related
            API references and coding patterns in added code lines.
            These features provided additional information beyond
            general TF-IDF text representation.
          </p>
          <span class="cr-pill">6 FEATURE CATEGORIES</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("**Security sensitive API indicator categories**")

api_categories = [
    (
        "Cryptography",
        "References to APIs such as Cipher, MessageDigest, SecretKey, "
        "KeyGenerator, Signature, and SecureRandom.",
    ),
    (
        "Authentication",
        "References to authentication related APIs such as Authenticator, "
        "Credentials, Principal, and LoginContext.",
    ),
    (
        "Authorization",
        "References to permission and access control APIs such as "
        "Permission, AccessController, ACL, and Role.",
    ),
    (
        "Secure communication",
        "References to TLS, SSLContext, TrustManager, and related "
        "secure communication APIs.",
    ),
    (
        "SQL protection",
        "References to PreparedStatement, prepareStatement, and "
        "parameterized SQL operations.",
    ),
    (
        "Input validation",
        "References to validation and sanitization patterns, including "
        "validate, sanitize, Pattern.compile, and requireNonNull.",
    ),
]

for category, description in api_categories:
    with st.container(border=True):
        st.markdown(f"**{category}**")
        st.write(description)

st.caption(
    "The indicators were extracted from added lines in code diffs. "
    "They represent selected API and coding pattern occurrences, "
    "not a complete assessment of whether a change is secure."
)

st.write("")

st.markdown("**Compared feature configurations**")

feature_comparison = [
    (
        "TF-IDF baseline",
        "TF-IDF code-diff features.",
    ),
    (
        "Word2Vec",
        "Averaged Word2Vec embeddings with Logistic Regression.",
    ),
    (
        "TF-IDF + API indicators",
        "TF-IDF text features combined with six API indicator categories.",
    ),
    (
        "TF-IDF + Word2Vec + API indicators",
        "A combined representation using all three feature approaches.",
    ),
]

for name, description in feature_comparison:
    with st.container(border=True):
        left, right = st.columns([1, 2])

        with left:
            st.markdown(f"**{name}**")

        with right:
            st.write(description)

st.write("")

st.markdown("**Feature extension experiment results**")

st.write(
    "The following results are mean scores across five grouped "
    "cross-validation folds."
)

extension_results = [
    {
        "Configuration": "TF-IDF baseline",
        "F1-score": 0.7623,
        "PR-AUC": 0.8616,
        "Balanced accuracy": 0.8662,
    },
    {
        "Configuration": "Word2Vec",
        "F1-score": 0.5895,
        "PR-AUC": 0.6126,
        "Balanced accuracy": 0.7685,
    },
    {
        "Configuration": "TF-IDF + API indicators",
        "F1-score": 0.7763,
        "PR-AUC": 0.8459,
        "Balanced accuracy": 0.8661,
    },
    {
        "Configuration": "TF-IDF + Word2Vec + API indicators",
        "F1-score": 0.7678,
        "PR-AUC": 0.8551,
        "Balanced accuracy": 0.8672,
    },
]

st.dataframe(
    extension_results,
    use_container_width=True,
    hide_index=True,
    column_config={
        "F1-score": st.column_config.NumberColumn(
            format="%.4f"
        ),
        "PR-AUC": st.column_config.NumberColumn(
            format="%.4f"
        ),
        "Balanced accuracy": st.column_config.NumberColumn(
            format="%.4f"
        ),
    },
)

best_f1 = max(
    extension_results,
    key=lambda result: result["F1-score"],
)

best_pr_auc = max(
    extension_results,
    key=lambda result: result["PR-AUC"],
)

result_col1, result_col2 = st.columns(2)

with result_col1:
    st.metric(
        "Highest F1-score",
        f"{best_f1['F1-score']:.2%}",
        help=best_f1["Configuration"],
    )

with result_col2:
    st.metric(
        "Highest PR-AUC",
        f"{best_pr_auc['PR-AUC']:.2%}",
        help=best_pr_auc["Configuration"],
    )

st.info(
    "The TF-IDF + API indicators configuration achieved the highest "
    "F1-score (77.63%), while the original TF-IDF baseline achieved "
    "the highest mean PR-AUC (86.16%). Since PR-AUC was the primary "
    "model selection criterion, the TF-IDF baseline remains the "
    "selected Gerrit deployment model."
)

st.markdown("**Research interpretation**")

st.write(
    "The API indicators improved precision and F1-score compared "
    "with the TF-IDF baseline, although recall and PR-AUC decreased "
    "slightly. Word2Vec alone performed considerably worse, while "
    "combining Word2Vec with the other features did not outperform "
    "the API-indicator configuration on F1-score or the baseline "
    "on PR-AUC."
)

st.caption(
    "These experiments provide an initial comparison of alternative "
    "feature representations. Further validation on independently "
    "labelled data and additional code review projects would help "
    "establish how well the observed improvements generalize."
)

st.write("")

st.divider()

section_heading("Research scope and interpretation")

st.info(
    "CodeReview Sentinel is a research prototype intended to "
    "support the identification of potentially security related "
    "code changes. A security related prediction does not "
    "independently confirm that a code change contains an "
    "exploitable vulnerability. Predictions require developer review."
)