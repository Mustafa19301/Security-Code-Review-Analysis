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
            Code review comments and associated project information
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
            revisions, review messages, patch metadata and extracted
            code diffs. Dataset is used for code-diff
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
        "describing code changes. Additional features like Word2Vec embeddings and security sensitive API indicators.",
        "Python · Scikit-learn",
    ),
    (
        "06",
        "Model Training and Evaluation",
        "Compared class imbalance strategies using grouped "
        "cross validation and evaluated model performance.",
        "Scikit-learn · Imbalanced-learn",
    ),
]

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
            Word2Vec learned 100 dimensional word representations
            from the training fold code diffs. The word vectors
            were averaged to create a numerical representation
            for each code diff.
          </p>
          <span class="cr-pill">100 DIMENSIONAL VECTORS</span>
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
            Regex based indicators counted selected security related
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
        "KeyGenerator, Signature and SecureRandom.",
    ),
    (
        "Authentication",
        "References to authentication related APIs such as Authenticator, "
        "Credentials, Principal and LoginContext.",
    ),
    (
        "Authorization",
        "References to permission and access control APIs such as "
        "Permission, AccessController, ACL and Role.",
    ),
    (
        "Secure communication",
        "References to TLS, SSLContext, TrustManager and related "
        "secure communication APIs.",
    ),
    (
        "SQL protection",
        "References to PreparedStatement, prepareStatement and "
        "parameterized SQL operations.",
    ),
    (
        "Input validation",
        "References to validation and sanitization patterns, including "
        "validate, sanitize, Pattern.compile and requireNonNull.",
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

st.divider()

section_heading("Research scope and interpretation")

st.info(
    "Our project CodeReview Sentinel is a research prototype intended to "
    "support the identification of potentially security related "
    "code changes. A security related prediction does not "
    "independently confirm that a code change contains an "
    "exploitable vulnerability but needs to be identified properly as it requires developer review."
)