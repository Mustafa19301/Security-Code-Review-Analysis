import re

import pandas as pd
import plotly.express as px
import streamlit as st

from app_utils.data_loader import load_model

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
    "INTERACTIVE MODEL DEMO",
    "Code Review Analyzer",
    "Explore how our integrated machine learning model from Gerrit classifier screens code changes "
    "for patterns associated with Security wise modifications and verify if vulnerability exists.",
)


@st.cache_resource
def get_gerrit_model():
    return load_model("gerrit_expanded_code_diff")


model_bundle = get_gerrit_model()

if model_bundle is None:
    st.error(
        "The expanded Gerrit model could not be found. Verify that "
        "results/machine_learning/gerrit_expanded/models/"
        "gerrit_expanded_tfidf_logistic_regression.joblib exists."
    )
    st.stop()


vectorizer = model_bundle["vectorizer"]
model = model_bundle["model"]

positive_label = model_bundle.get(
    "positive_class",
    1,
)

label_mapping = model_bundle.get(
    "label_mapping",
    {
        0: "Not security wise",
        1: "Security wise",
    },
)

positive_description = model_bundle.get(
    "positive_class_description",
    "Security wise",
)

model_name = model_bundle.get(
    "model_name",
    "TF-IDF + Random Oversampling",
)


if not hasattr(model, "predict_proba"):
    st.error(
        "The loaded model does not support probability predictions. "
        "The analyzer requires the saved Logistic Regression model."
    )
    st.stop()


if not hasattr(model, "classes_"):
    st.error(
        "The loaded model does not contain its expected class information."
    )
    st.stop()


if positive_label not in model.classes_:
    st.error(
        "The configured positive class was not found in the loaded model."
    )
    st.stop()


examples = {
    "TLS certificate and hostname verification": """diff --git a/src/main/java/com/couchbase/client/core/env/EndpointVerification.java b/src/main/java/com/couchbase/client/core/env/EndpointVerification.java
index 1234567..abcdef0 100644
--- a/src/main/java/com/couchbase/client/core/env/EndpointVerification.java
+++ b/src/main/java/com/couchbase/client/core/env/EndpointVerification.java
@@ -1,24 +1,51 @@
 package com.couchbase.client.core.env;

+import javax.net.ssl.SSLContext;
+import javax.net.ssl.SSLParameters;
+import javax.net.ssl.TrustManagerFactory;
+import java.security.KeyStore;
+import java.security.cert.CertificateException;
+import java.security.cert.X509Certificate;
+
 public class EndpointVerification {

-    public static SSLContext createContext() throws Exception {
-        TrustManager[] trustAllCertificates = new TrustManager[] {
-            new X509TrustManager() {
-                public X509Certificate[] getAcceptedIssuers() {
-                    return new X509Certificate[0];
-                }
-
-                public void checkClientTrusted(
-                    X509Certificate[] certs, String authType) {
-                }
-
-                public void checkServerTrusted(
-                    X509Certificate[] certs, String authType) {
-                }
-            }
-        };
-
-        SSLContext context = SSLContext.getInstance("TLS");
-        context.init(null, trustAllCertificates, new SecureRandom());
-        return context;
+    public static SSLContext createContext(KeyStore trustStore)
+            throws Exception {
+
+        TrustManagerFactory trustManagerFactory =
+            TrustManagerFactory.getInstance(
+                TrustManagerFactory.getDefaultAlgorithm()
+            );
+
+        trustManagerFactory.init(trustStore);
+
+        SSLContext context = SSLContext.getInstance("TLS");
+
+        context.init(
+            null,
+            trustManagerFactory.getTrustManagers(),
+            new SecureRandom()
+        );
+
+        return context;
+    }
+
+    public static SSLParameters createSecureParameters() {
+        SSLParameters parameters = new SSLParameters();
+
+        parameters.setEndpointIdentificationAlgorithm("HTTPS");
+        parameters.setProtocols(new String[] {"TLSv1.3", "TLSv1.2"});
+
+        return parameters;
     }
 }
""",

    "Prevent insecure credential handling": """diff --git a/src/main/java/com/couchbase/client/core/auth/CredentialProvider.java b/src/main/java/com/couchbase/client/core/auth/CredentialProvider.java
index 1234567..abcdef0 100644
--- a/src/main/java/com/couchbase/client/core/auth/CredentialProvider.java
+++ b/src/main/java/com/couchbase/client/core/auth/CredentialProvider.java
@@ -15,19 +15,35 @@
 public class CredentialProvider {

     public void authenticate(String username, String password) {
-        logger.debug("Authenticating user " + username
-            + " with password " + password);
-
-        String credentials = username + ":" + password;
-        String encoded = Base64.getEncoder().encodeToString(
-            credentials.getBytes(StandardCharsets.UTF_8)
-        );
-
-        connection.setHeader("Authorization", "Basic " + encoded);
+        if (username == null || username.isBlank()) {
+            throw new IllegalArgumentException(
+                "Username must not be empty"
+            );
+        }
+
+        if (password == null || password.isEmpty()) {
+            throw new IllegalArgumentException(
+                "Password must not be empty"
+            );
+        }
+
+        logger.debug("Starting authentication for user {}", username);
+
+        String credentials = username + ":" + password;
+
+        String encoded = Base64.getEncoder().encodeToString(
+            credentials.getBytes(StandardCharsets.UTF_8)
+        );
+
+        connection.setHeader(
+            "Authorization",
+            "Basic " + encoded
+        );
+
+        logger.debug("Authentication credentials prepared securely");
     }
 }
""",

    "Validate server certificates": """diff --git a/src/main/java/com/couchbase/client/core/io/CertificateValidator.java b/src/main/java/com/couchbase/client/core/io/CertificateValidator.java
index 1234567..abcdef0 100644
--- a/src/main/java/com/couchbase/client/core/io/CertificateValidator.java
+++ b/src/main/java/com/couchbase/client/core/io/CertificateValidator.java
@@ -1,18 +1,42 @@
 package com.couchbase.client.core.io;

+import java.security.cert.Certificate;
+import java.security.cert.X509Certificate;
+import java.security.cert.CertificateException;
+
 public class CertificateValidator {

     public boolean validate(Certificate certificate) {
-        return true;
+        if (!(certificate instanceof X509Certificate)) {
+            return false;
+        }
+
+        X509Certificate x509Certificate =
+            (X509Certificate) certificate;
+
+        try {
+            x509Certificate.checkValidity();
+            x509Certificate.verify(
+                trustedCertificate.getPublicKey()
+            );
+
+            return trustedCertificate.equals(
+                x509Certificate.getIssuerX500Principal()
+            );
+
+        } catch (CertificateException
+                 | GeneralSecurityException exception) {
+            logger.warn(
+                "Server certificate validation failed",
+                exception
+            );
+
+            return false;
+        }
     }
 }
""",

    "SQL injection prevention": """diff --git a/src/main/java/com/couchbase/client/core/query/QueryService.java b/src/main/java/com/couchbase/client/core/query/QueryService.java
index 1234567..abcdef0 100644
--- a/src/main/java/com/couchbase/client/core/query/QueryService.java
+++ b/src/main/java/com/couchbase/client/core/query/QueryService.java
@@ -20,12 +20,24 @@
 public class QueryService {

     public Result executeQuery(String username) {
-        String query = "SELECT * FROM users WHERE username = '"
-            + username + "'";
-
-        return database.execute(query);
+        String query =
+            "SELECT * FROM users WHERE username = $username";
+
+        Map<String, Object> parameters = new HashMap<>();
+        parameters.put("username", username);
+
+        QueryOptions options = QueryOptions.queryOptions()
+            .parameters(parameters);
+
+        return database.query(query, options);
     }
 }
""",

    "Ordinary refactoring": """diff --git a/src/main/java/com/couchbase/client/core/util/ConnectionUtils.java b/src/main/java/com/couchbase/client/core/util/ConnectionUtils.java
index 1234567..abcdef0 100644
--- a/src/main/java/com/couchbase/client/core/util/ConnectionUtils.java
+++ b/src/main/java/com/couchbase/client/core/util/ConnectionUtils.java
@@ -10,9 +10,7 @@
 public class ConnectionUtils {

     public String getConnectionName(Connection connection) {
-        String hostname = connection.getHostname();
-        int port = connection.getPort();
-        return hostname + ":" + port;
+        return connection.getHostname()
+            + ":" + connection.getPort();
     }
 }
""",
}


example_descriptions = {
    "TLS certificate and hostname verification":
        "Replaces trust-all certificate handling with a trust store and "
        "secure TLS endpoint verification.",

    "Prevent insecure credential handling":
        "Improves credential validation and removes password exposure "
        "from debug logging.",

    "Validate server certificates":
        "Adds certificate type, validity, and trust checks instead of "
        "automatically accepting certificates.",

    "SQL injection prevention":
        "Replaces string concatenation in a database query with "
        "parameterized query options.",

    "Ordinary refactoring":
        "Simplifies a connection utility method without introducing "
        "an obvious security-focused change.",
}


def is_valid_git_diff(text):
    """
    Validate recognizable unified Git diff structure.

    Requires:
    - A Git diff header or unified file headers.
    - At least one hunk header.
    - At least one actual added or removed line inside a hunk.

    This checks input format only. It does not assess security.
    """

    if not text or not text.strip():
        return False

    lines = text.splitlines()

    has_git_header = any(
        line.startswith("diff --git ")
        for line in lines
    )

    has_old_file_header = any(
        line.startswith("--- ")
        for line in lines
    )

    has_new_file_header = any(
        line.startswith("+++ ")
        for line in lines
    )

    has_unified_file_headers = (
        has_old_file_header and has_new_file_header
    )

    has_hunk = False
    has_actual_change = False

    for line in lines:

        if re.match(r"^@@\s.*@@", line):
            has_hunk = True
            continue

        if not has_hunk:
            continue

        if line.startswith("diff --git "):
            has_hunk = False
            continue

        if (
            line.startswith("+")
            and not line.startswith("+++")
        ) or (
            line.startswith("-")
            and not line.startswith("---")
        ):
            has_actual_change = True

    return (
        (has_git_header or has_unified_file_headers)
        and re.search(
            r"^@@\s.*@@",
            text,
            re.MULTILINE,
        ) is not None
        and has_actual_change
    )


LOW_INFORMATION_TERMS = {
    "example",
    "src",
    "source",
    "main",
    "test",
    "tests",
    "testing",
    "java",
    "class",
    "classes",
    "com",
    "org",
    "net",
    "io",
    "github",
    "package",
    "packages",
    "path",
    "file",
    "files",
    "diff",
    "index",
    "public",
    "private",
    "protected",
    "static",
    "void",
    "return",
    "new",
    "true",
    "false",
    "null",
    "string",
    "int",
    "long",
    "boolean",
    "final",
    "override",
    "import",
}


def filter_explanation_terms(contribution_df):
    """
    Remove low-information terms from the human-readable
    explanation display.

    This function does not modify the model input,
    predictions, TF-IDF features, or model coefficients.
    """

    if contribution_df is None or contribution_df.empty:
        return contribution_df, 0

    def is_informative(term):
        tokens = re.findall(
            r"[a-zA-Z0-9_]+",
            str(term).lower(),
        )

        if not tokens:
            return False

        return not all(
            token in LOW_INFORMATION_TERMS
            for token in tokens
        )

    filtered_df = contribution_df[
        contribution_df["Term"].apply(is_informative)
    ].copy()

    hidden_count = len(contribution_df) - len(filtered_df)

    return filtered_df, hidden_count


def get_feature_contributions(
    vectorizer,
    model,
    transformed_features,
    positive_label=1,
):
    """
    Calculate per-feature TF-IDF contributions using the
    fitted binary Logistic Regression coefficients.

    Positive contributions support the Security wise class.
    Negative contributions push the prediction away from it.

    These are model feature contributions, not proof of
    vulnerability or causal explanations.
    """

    if not hasattr(model, "coef_"):
        return None

    if not hasattr(model, "classes_"):
        return None

    classes = list(model.classes_)

    if positive_label not in classes:
        return None

    if len(classes) != 2:
        return None

    positive_index = classes.index(positive_label)

    coefficients = model.coef_[0]

    if positive_index == 0:
        coefficients = -coefficients

    feature_names = vectorizer.get_feature_names_out()

    sparse_row = transformed_features.tocsr()

    feature_indices = sparse_row.indices
    feature_values = sparse_row.data

    contributions = (
        feature_values * coefficients[feature_indices]
    )

    contribution_df = pd.DataFrame(
        {
            "Term": feature_names[feature_indices],
            "Contribution": contributions,
        }
    )

    contribution_df = contribution_df[
        contribution_df["Contribution"] != 0
    ].copy()

    return contribution_df.sort_values(
        "Contribution",
        ascending=False,
    )


def display_feature_explanations(contribution_df):

    section_heading(
        "What influenced this prediction?",
        "Explore the text features that pushed the model toward "
        "or away from a Security wise classification.",
    )

    if contribution_df is None or contribution_df.empty:
        st.info(
            "No usable feature contributions were available for "
            "this input."
        )
        return

    display_df, hidden_count = filter_explanation_terms(
        contribution_df
    )

    if display_df.empty:
        st.info(
            "The model generated feature contributions, but "
            "none remained after filtering generic terms. "
            "You can still inspect all terms below."
        )

    else:
        positive_terms = display_df[
            display_df["Contribution"] > 0
        ].nlargest(8, "Contribution").copy()

        negative_terms = display_df[
            display_df["Contribution"] < 0
        ].nsmallest(8, "Contribution").copy()

        positive_col, negative_col = st.columns(2)

        with positive_col:
            st.markdown("#### Supporting Security wise")

            if positive_terms.empty:
                st.caption(
                    "No positive feature contributions were identified."
                )

            else:
                positive_chart = px.bar(
                    positive_terms.sort_values(
                        "Contribution",
                        ascending=True,
                    ),
                    x="Contribution",
                    y="Term",
                    orientation="h",
                    labels={
                        "Contribution": "Model contribution",
                        "Term": "TF-IDF term",
                    },
                    template="plotly_dark",
                )

                positive_chart.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    height=350,
                    margin=dict(
                        l=10,
                        r=10,
                        t=25,
                        b=10,
                    ),
                )

                st.plotly_chart(
                    positive_chart,
                    use_container_width=True,
                )

        with negative_col:
            st.markdown("#### Pushing against Security wise")

            if negative_terms.empty:
                st.caption(
                    "No negative feature contributions were identified."
                )

            else:
                negative_chart = px.bar(
                    negative_terms.sort_values(
                        "Contribution",
                        ascending=False,
                    ),
                    x="Contribution",
                    y="Term",
                    orientation="h",
                    labels={
                        "Contribution": "Model contribution",
                        "Term": "TF-IDF term",
                    },
                    template="plotly_dark",
                )

                negative_chart.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    height=350,
                    margin=dict(
                        l=10,
                        r=10,
                        t=25,
                        b=10,
                    ),
                )

                st.plotly_chart(
                    negative_chart,
                    use_container_width=True,
                )

    st.info(
        "The charts hide generic programming and file path terms "
        "to make the explanation easier to read. These terms are "
        "still included in the original model prediction."
    )

    if not display_df.empty:
        with st.expander("View displayed feature contribution values"):
            table_df = display_df.copy()

            table_df["Contribution"] = (
                table_df["Contribution"].round(6)
            )

            table_df = table_df.rename(
                columns={
                    "Term": "TF-IDF Term",
                    "Contribution": "Logit Contribution",
                }
            )

            st.dataframe(
                table_df,
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("View all model feature contributions"):
        st.caption(
            "This table includes every non zero feature contribution, "
            "including generic terms excluded from the main charts."
        )

        full_table = contribution_df.copy()

        full_table["Contribution"] = (
            full_table["Contribution"].round(6)
        )

        full_table = full_table.rename(
            columns={
                "Term": "TF-IDF Term",
                "Contribution": "Logit Contribution",
            }
        )

        st.dataframe(
            full_table,
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Interpretation: positive contributions move the model's "
        "decision toward the Security wise class. Negative "
        "contributions move it away. These values explain the "
        "model's text based decision; they do not establish that "
        "a software vulnerability exists."
    )


def clear_analyzer():
    """
    Clear the code diff and previous analysis.
    """

    st.session_state["code_diff_input"] = ""
    st.session_state.pop("last_analysis", None)


with st.expander("View Gerrit model evaluation"):
    st.markdown(
        f"""
        **Selected model:** {model_name}

        **Classifier:** Logistic Regression

        **Text representation:** TF-IDF

        **Class balancing:** Random Oversampling during training folds

        **Evaluation:** Five-fold Stratified Group Cross-Validation,
        grouped by review number.
        """
    )

    st.markdown("#### Mean cross-validation results")

    cv_columns = st.columns(4)

    cv_metrics = [
        ("Accuracy", 88.56),
        ("Precision", 70.57),
        ("Recall", 83.16),
        ("F1-score", 76.23),
    ]

    for column, (metric, value) in zip(
        cv_columns,
        cv_metrics,
    ):
        with column:
            animated_metric_card(
                metric,
                value,
                suffix="%",
                decimals=2,
            )

    st.markdown(
        """
        **Mean fold PR-AUC:** 86.16%

        **Pooled out-of-fold PR-AUC:** 85.70%

        These are different aggregation methods: mean fold PR-AUC
        averages the five individual fold scores, while pooled
        out-of-fold PR-AUC evaluates all out-of-fold predictions together.
        """
    )



section_heading(
    "Try CodeReview Sentinel",
    "Explore prepared examples without having Git installed "
    "or knowing how to create a Git diff.",
)

st.markdown(
    """
    **New to Git diffs? No problem.**

    A Git diff is simply a view of the differences between two versions
    of a file. It shows which lines of code were added, removed, or changed.

    CodeReview Sentinel analyzes those changes and looks for patterns
    learned from its training data. Choose one of the sample changes below
    to try the analyzer, or paste a diff from your own project.
    """
)

st.markdown("#### Try a sample code change")

example_choice = st.selectbox(
    "Choose a sample",
    ["Choose an example..."] + list(examples.keys()),
)

if example_choice != "Choose an example...":
    st.caption(
        example_descriptions[example_choice]
    )

load_col, info_col = st.columns([1, 2])

with load_col:
    if st.button(
        "Load sample code change",
        type="primary",
        use_container_width=True,
    ):
        if example_choice == "Choose an example...":
            st.warning("Please choose a sample first.")

        else:
            st.session_state["code_diff_input"] = examples[
                example_choice
            ]

            st.session_state.pop("last_analysis", None)
            st.rerun()

with info_col:
    st.caption(
        "Loading a sample fills the Git diff input below. "
        "You can review or edit it before running the analysis."
    )


# Git diff input is now directly below the sample selector.

code_diff = st.text_area(
    "Git diff input",
    key="code_diff_input",
    height=330,
    placeholder=(
        "Paste a unified Git diff here, or load one of the sample "
        "code changes above..."
    ),
)


button_col, clear_col = st.columns(2)

with button_col:
    analyze_button = st.button(
        "Analyze code change",
        type="primary",
        use_container_width=True,
    )

with clear_col:
    st.button(
        "Clear input",
        use_container_width=True,
        on_click=clear_analyzer,
    )


with st.expander("How do I get a Git diff?"):
    st.markdown(
        """
        If you have a Git repository, open a terminal in your project
        directory and run:

        ```bash
        git diff
        ```

        To compare your most recent commit with the previous one, run:

        ```bash
        git diff HEAD~1 HEAD
        ```

        Copy the resulting output and paste it into the input above.

        **You do not need to remove the Git headers or change the formatting.**
        """
    )

if analyze_button:

    st.session_state.pop("last_analysis", None)

    if not code_diff.strip():
        st.warning(
            "Please load a sample code change or paste a Git diff "
            "before analyzing."
        )

    elif not is_valid_git_diff(code_diff):
        st.warning(
            "This input does not appear to be a valid unified Git diff. "
            "Please paste a Git diff containing file headers and at least "
            "one change hunk. You can also select one of the prepared "
            "examples above. Ordinary sentences and plain code cannot "
            "be analyzed."
        )

    else:
        with st.spinner(
            "Analyzing the code change with the Gerrit classifier..."
        ):
            try:
                features = vectorizer.transform(
                    [code_diff]
                )

                prediction = model.predict(
                    features
                )[0]

                classes = list(model.classes_)

                positive_index = classes.index(
                    positive_label
                )

                score = float(
                    model.predict_proba(features)[0][positive_index]
                )

                feature_contributions = get_feature_contributions(
                    vectorizer=vectorizer,
                    model=model,
                    transformed_features=features,
                    positive_label=positive_label,
                )

                st.session_state["last_analysis"] = {
                    "prediction": prediction,
                    "score": score,
                    "diff": code_diff,
                    "feature_contributions": feature_contributions,
                }

            except Exception as error:
                st.error(
                    f"An error occurred while analyzing the diff: {error}"
                )


result = st.session_state.get("last_analysis")

if result:

    st.write("")
    st.divider()

    section_heading(
        "Analysis result",
        "The result is a screening prediction, not a vulnerability verdict.",
    )

    prediction = result["prediction"]
    score = result["score"]

    is_security_wise = (
        prediction == positive_label
    )

    if is_security_wise:
        st.error("Potentially Security wise change")

        explanation = (
            "The model identified text patterns associated with "
            "Security wise code changes."
        )

    else:
        st.success("Not classified as Security wise")

        explanation = (
            "The model did not identify enough learned patterns "
            "to classify this change as Security wise."
        )

    st.write(explanation)

    score_col, class_col = st.columns(2)

    with score_col:
        animated_metric_card(
            "Security wise model score",
            score * 100,
            suffix="%",
            decimals=2,
            note="Model-estimated score for the Security wise class",
        )

    with class_col:
        class_value = (
            "Security wise"
            if is_security_wise
            else "Not security wise"
        )

        st.markdown(
            f"""
            <div class="cr-card">
              <div class="cr-card-label">Predicted class</div>
              <div class="cr-card-value" style="font-size:1.2rem">
                {class_value}
              </div>
              <div class="cr-card-note">
                Gerrit model classification output
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("#### Score visualization")

    st.progress(score)

    st.caption(
        "This is the Logistic Regression model's estimated score "
        "for the Security wise class. It is not a calibrated "
        "measure of vulnerability likelihood or severity, nor "
        "proof that an exploitable vulnerability exists."
    )

    st.divider()

    display_feature_explanations(
        result.get("feature_contributions")
    )

    with st.expander("View submitted diff"):
        st.code(
            result["diff"],
            language="diff",
        )

    with st.expander("How to interpret this prediction"):
        st.markdown(
            """
            - **Security wise:** the model found patterns resembling
              examples labelled Security wise during training.
            - **Not security wise:** the model did not find enough
              learned patterns to cross its classification threshold.
            - **Model score:** the estimated score assigned to the
              Security wise class by Logistic Regression.
            - **Feature contributions:** terms that pushed the model's
              classification toward or away from the Security wise class.
            - **Explanation filtering:** generic file path and programming
              terms may be hidden from the charts, but they remain part
              of the model's original prediction.
            - **NOTE:** review the actual code and surrounding
              context. The model can produce false positives and
              false negatives.
            """
        )


st.divider()

with st.expander("About this analyzer and its limitations"):
    st.markdown(
        f"""
        **Training source:** Couchbase Java Client Gerrit dataset

        **Model configuration:** {model_name}

        **Classifier:** Logistic Regression

        **Text representation:** TF-IDF

        **Input:** Git code diffs

        **Prediction target:** Security wise versus
        not Security wise code changes.

        **Positive class:** Security wise (label 1).

        **Evaluation:** Five-fold Stratified Group Cross-Validation,
        grouping revisions by review number.

        **Class balancing:** Random oversampling was applied to
        training folds only.

        The deployment model was subsequently trained using all
        eligible records.

        The displayed feature contributions describe how terms
        influence the fitted model's classification. Generic
        programming and file-path terms may be hidden from the
        main explanation charts for readability. The full list
        remains available.

        The model score is not a calibrated probability of a
        vulnerability. A Security wise prediction does not
        independently confirm that an exploitable vulnerability
        exists.
        """
    )