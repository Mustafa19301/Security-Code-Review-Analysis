import pandas as pd
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from sklearn.metrics import confusion_matrix

from app_utils.data_loader import load_csv

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
    "MODEL EVALUATION",
    "Model Performance",
    "Comparing the saved GitHub and Gerrit evaluation results.",
)

github_df = load_csv("github_model_comparison")

if github_df is None:
    st.error("GitHub model comparison file could not be found.")
    st.stop()

section_heading(
    "GitHub model evaluation",
    "Results from the GitHub review comment classification experiment.",
)

github_metrics = [
    "accuracy",
    "balanced_accuracy",
    "precision",
    "recall",
    "f1_score",
]

required_github = ["model"] + github_metrics

missing_github = [
    column
    for column in required_github
    if column not in github_df.columns
]

if missing_github:
    st.error(
        "GitHub comparison file is missing columns: "
        + ", ".join(missing_github)
    )
    st.stop()


best_github = github_df.loc[
    github_df["f1_score"].idxmax()
]

g1, g2, g3 = st.columns(3)

with g1:
    animated_metric_card(
        "Best F1 score",
        float(best_github["f1_score"]) * 100,
        suffix="%",
        decimals=2,
        note="Highest GitHub F1",
    )

with g2:
    animated_metric_card(
        "Best accuracy",
        float(best_github["accuracy"]) * 100,
        suffix="%",
        decimals=2,
        note=str(best_github["model"]),
    )

with g3:
    animated_metric_card(
        "Models evaluated",
        len(github_df),
        note="GitHub experiment",
    )


st.caption(
    f"Top GitHub model by F1: {best_github['model']}"
)


github_chart_data = github_df.melt(
    id_vars="model",
    value_vars=[
        "precision",
        "recall",
        "f1_score",
    ],
    var_name="Metric",
    value_name="Score",
)

github_chart_data["Score"] *= 100

fig = px.bar(
    github_chart_data,
    x="model",
    y="Score",
    color="Metric",
    barmode="group",
    text_auto=".1f",
    title="GitHub: precision, recall, and F1",
    labels={
        "model": "Model",
        "Score": "Score (%)",
    },
    template="plotly_dark",
)

fig.update_layout(
    yaxis_range=[0, 105],
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)

st.plotly_chart(
    fig,
    use_container_width=True,
)


github_display = github_df[required_github].copy()

for metric in github_metrics:
    github_display[metric] = (
        github_display[metric] * 100
    ).round(2)

github_display = github_display.rename(
    columns={
        "model": "Model",
        "accuracy": "Accuracy (%)",
        "balanced_accuracy": "Balanced Accuracy (%)",
        "precision": "Precision (%)",
        "recall": "Recall (%)",
        "f1_score": "F1 Score (%)",
    }
)

with st.expander("View GitHub evaluation table"):
    st.dataframe(
        github_display,
        use_container_width=True,
        hide_index=True,
    )



st.success(
    f"Best GitHub model by F1 score: "
    f"{best_github['model']} "
    f"({best_github['f1_score'] * 100:.2f}%)."
)


st.divider()

section_heading(
    "GitHub confusion matrix",
    "Predictions from the best-performing GitHub model.",
)

github_predictions_path = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "processed"
    / "model_comparison"
    / "model_predictions.csv"
)

if not github_predictions_path.exists():
    st.error("GitHub prediction file could not be found.")
else:
    github_predictions_df = pd.read_csv(
        github_predictions_path
    )

    github_prediction_columns = {
        "Logistic Regression": "logistic_regression_prediction",
        "Linear SVM": "linear_svm_prediction",
        "Random Forest": "random_forest_prediction",
    }

    selected_github_model = str(best_github["model"])

    prediction_column = github_prediction_columns.get(
        selected_github_model
    )

    required_prediction_columns = [
        "actual_label",
        prediction_column,
    ] if prediction_column else ["actual_label"]

    missing_prediction_columns = [
        column
        for column in required_prediction_columns
        if column not in github_predictions_df.columns
    ]

    if missing_prediction_columns:
        st.error(
            "GitHub prediction file is missing columns: "
            + ", ".join(missing_prediction_columns)
        )
    else:
        github_matrix = confusion_matrix(
            github_predictions_df["actual_label"],
            github_predictions_df[prediction_column],
            labels=[0, 1],
        )

        github_tn, github_fp, github_fn, github_tp = (
            github_matrix.ravel()
        )

        github_matrix_col, github_explanation_col = st.columns(
            [1.35, 1]
        )

        with github_matrix_col:
            fig = go.Figure(
                data=go.Heatmap(
                    z=github_matrix,
                    x=[
                        "Not security related",
                        "Security related",
                    ],
                    y=[
                        "Not security related",
                        "Security related",
                    ],
                    colorscale=[
                        [0.0, "#14243a"],
                        [0.5, "#2563a6"],
                        [1.0, "#22a6a1"],
                    ],
                    showscale=False,
                    text=github_matrix,
                    texttemplate="%{text}",
                    textfont={
                        "size": 22,
                        "color": "white",
                    },
                    hovertemplate=(
                        "Actual: %{y}<br>"
                        "Predicted: %{x}<br>"
                        "Count: %{z}"
                        "<extra></extra>"
                    ),
                )
            )

            fig.update_layout(
                title=(
                    f"Actual vs. predicted classifications "
                    f"({selected_github_model})"
                ),
                xaxis_title="Predicted label",
                yaxis_title="Actual label",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=420,
                margin={
                    "l": 25,
                    "r": 25,
                    "t": 65,
                    "b": 85,
                },
            )

            fig.update_yaxes(
                autorange="reversed"
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        with github_explanation_col:
            st.markdown("#### Prediction breakdown")

            animated_metric_card(
                "True negatives",
                int(github_tn),
                note="Correctly classified as not security related",
            )

            animated_metric_card(
                "True positives",
                int(github_tp),
                note="Correctly classified as security related",
            )

            animated_metric_card(
                "False positives",
                int(github_fp),
                note="Not security related, predicted as security related",
            )

            animated_metric_card(
                "False negatives",
                int(github_fn),
                note="Security related, predicted as not security related",
            )

        st.caption(
            f"Total GitHub predictions: "
            f"{github_tn + github_fp + github_fn + github_tp:,}"
        )

        st.info(
            "**How to read this matrix:** Rows represent the actual "
            "dataset labels, while columns represent the model's predictions. "
            "Label 0 represents not security related and label 1 represents "
            "security related."
        )


st.divider()

section_heading(
    "Gerrit model evaluation",
    "Mean results across five Stratified Group K-Fold cross validation folds.",
)

expanded_gerrit_df = pd.DataFrame([
    {
        "Model": "TF-IDF + Random Oversampling",
        "Mean_Accuracy": 0.8856,
        "Mean_Balanced_Accuracy": 0.8662,
        "Mean_Precision": 0.7057,
        "Mean_Recall": 0.8316,
        "Mean_F1": 0.7623,
        "Mean_PR_AUC": 0.8616,
    },
    {
        "Model": "TF-IDF + Class Weighting",
        "Mean_Accuracy": 0.8686,
        "Mean_Balanced_Accuracy": 0.8544,
        "Mean_Precision": 0.6648,
        "Mean_Recall": 0.8290,
        "Mean_F1": 0.7367,
        "Mean_PR_AUC": 0.8509,
    },
])

best_expanded_gerrit = expanded_gerrit_df.loc[
    expanded_gerrit_df["Mean_PR_AUC"].idxmax()
]


r1, r2, r3, r4 = st.columns(4)

with r1:
    animated_metric_card(
        "Mean PR-AUC",
        float(best_expanded_gerrit["Mean_PR_AUC"]) * 100,
        suffix="%",
        decimals=2,
        note="Highest mean PR-AUC",
    )

with r2:
    animated_metric_card(
        "Mean F1 score",
        float(best_expanded_gerrit["Mean_F1"]) * 100,
        suffix="%",
        decimals=2,
        note="Selected configuration",
    )

with r3:
    animated_metric_card(
        "Mean recall",
        float(best_expanded_gerrit["Mean_Recall"]) * 100,
        suffix="%",
        decimals=2,
        note="Security related class",
    )

with r4:
    animated_metric_card(
        "Validation folds",
        5,
        note="Stratified Group K-Fold",
    )


st.success(
    f"Selected Gerrit model: "
    f"{best_expanded_gerrit['Model']} "
    f"with a mean PR-AUC of "
    f"{best_expanded_gerrit['Mean_PR_AUC'] * 100:.2f}%."
)


expanded_chart_data = expanded_gerrit_df.melt(
    id_vars="Model",
    value_vars=[
        "Mean_Precision",
        "Mean_Recall",
        "Mean_F1",
        "Mean_PR_AUC",
    ],
    var_name="Metric",
    value_name="Score",
)

expanded_chart_data["Score"] *= 100

expanded_chart_data["Metric"] = (
    expanded_chart_data["Metric"]
    .str.replace("Mean_", "", regex=False)
    .str.replace("_", "-", regex=False)
)

fig = px.bar(
    expanded_chart_data,
    x="Model",
    y="Score",
    color="Metric",
    barmode="group",
    text_auto=".1f",
    title="Gerrit: mean cross validation metrics",
    labels={
        "Model": "Model configuration",
        "Score": "Mean score (%)",
    },
    template="plotly_dark",
)

fig.update_layout(
    yaxis_range=[0, 105],
    xaxis_tickangle=-10,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)

st.plotly_chart(
    fig,
    use_container_width=True,
)

expanded_display = expanded_gerrit_df.copy()

expanded_display_columns = [
    "Mean_Accuracy",
    "Mean_Balanced_Accuracy",
    "Mean_Precision",
    "Mean_Recall",
    "Mean_F1",
    "Mean_PR_AUC",
]

for metric in expanded_display_columns:
    expanded_display[metric] = (
        expanded_display[metric] * 100
    ).round(2)

expanded_display = expanded_display.rename(
    columns={
        "Mean_Accuracy": "Mean Accuracy (%)",
        "Mean_Balanced_Accuracy": "Mean Balanced Accuracy (%)",
        "Mean_Precision": "Mean Precision (%)",
        "Mean_Recall": "Mean Recall (%)",
        "Mean_F1": "Mean F1 (%)",
        "Mean_PR_AUC": "Mean PR-AUC (%)",
    }
)

with st.expander("View Gerrit evaluation table"):
    st.dataframe(
        expanded_display,
        use_container_width=True,
        hide_index=True,
    )


st.info(
    "PR-AUC is particularly useful for the Gerrit experiment "
    "because the security related class is less common than the "
    "non-security related class. The selected configuration "
    "achieved the highest mean PR-AUC across the five folds."
)


st.divider()

section_heading(
    "Gerrit feature extension experiments",
    "Additional experiments exploring alternative code representations "
    "and security sensitive API indicators.",
)

st.markdown(
    """
    These experiments investigated whether incorporating additional
    code level features could improve the classification of
    security related Gerrit code changes.

    Four approaches were evaluated using the same Gerrit
    dataset and five-fold Stratified Group K-Fold cross-validation.
    """
)


feature_experiments_df = pd.DataFrame([
    {
        "Model": "TF-IDF Baseline",
        "Accuracy": 0.885560,
        "Balanced Accuracy": 0.866212,
        "Precision": 0.705725,
        "Recall": 0.831581,
        "F1 Score": 0.762291,
        "PR-AUC": 0.861571,
    },
    {
        "Model": "Word2Vec",
        "Accuracy": 0.758769,
        "Balanced Accuracy": 0.768516,
        "Precision": 0.472359,
        "Recall": 0.785946,
        "F1 Score": 0.589501,
        "PR-AUC": 0.612589,
    },
    {
        "Model": "TF-IDF + API Indicators",
        "Accuracy": 0.896834,
        "Balanced Accuracy": 0.866093,
        "Precision": 0.745311,
        "Recall": 0.811068,
        "F1 Score": 0.776324,
        "PR-AUC": 0.845922,
    },
    {
        "Model": "TF-IDF + Word2Vec + API",
        "Accuracy": 0.890077,
        "Balanced Accuracy": 0.867237,
        "Precision": 0.719501,
        "Recall": 0.826388,
        "F1 Score": 0.767783,
        "PR-AUC": 0.855079,
    },
])

best_feature_f1 = feature_experiments_df.loc[
    feature_experiments_df["F1 Score"].idxmax()
]

best_feature_prauc = feature_experiments_df.loc[
    feature_experiments_df["PR-AUC"].idxmax()
]


f1_col, pr_col, models_col = st.columns(3)

with f1_col:
    animated_metric_card(
        "Highest mean F1",
        float(best_feature_f1["F1 Score"]) * 100,
        suffix="%",
        decimals=2,
        note="TF-IDF + API Indicators",
    )

with pr_col:
    animated_metric_card(
        "Highest mean PR-AUC",
        float(best_feature_prauc["PR-AUC"]) * 100,
        suffix="%",
        decimals=2,
        note="TF-IDF Baseline",
    )

with models_col:
    animated_metric_card(
        "Approaches evaluated",
        len(feature_experiments_df),
        note="Gerrit feature experiments",
    )

feature_f1_chart = feature_experiments_df[
    ["Model", "F1 Score"]
].copy()

feature_f1_chart["F1 Score"] *= 100

fig = px.bar(
    feature_f1_chart,
    x="Model",
    y="F1 Score",
    color="Model",
    text_auto=".2f",
    title="Feature extension experiments: F1 score",
    labels={
        "Model": "Feature representation",
        "F1 Score": "Mean F1 score (%)",
    },
    template="plotly_dark",
)

fig.update_layout(
    yaxis_range=[0, 100],
    showlegend=False,
    xaxis_tickangle=-15,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)

st.plotly_chart(
    fig,
    use_container_width=True,
)

feature_pr_chart = feature_experiments_df[
    ["Model", "PR-AUC"]
].copy()

feature_pr_chart["PR-AUC"] *= 100

fig = px.bar(
    feature_pr_chart,
    x="Model",
    y="PR-AUC",
    color="Model",
    text_auto=".2f",
    title="Feature extension experiments: PR-AUC",
    labels={
        "Model": "Feature representation",
        "PR-AUC": "Mean PR-AUC (%)",
    },
    template="plotly_dark",
)

fig.update_layout(
    yaxis_range=[0, 100],
    showlegend=False,
    xaxis_tickangle=-15,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)

st.plotly_chart(
    fig,
    use_container_width=True,
)

feature_display = feature_experiments_df.copy()

feature_metric_columns = [
    "Accuracy",
    "Balanced Accuracy",
    "Precision",
    "Recall",
    "F1 Score",
    "PR-AUC",
]

for metric in feature_metric_columns:
    feature_display[metric] = (
        feature_display[metric] * 100
    ).round(2)

feature_display = feature_display.rename(
    columns={
        "Accuracy": "Accuracy (%)",
        "Balanced Accuracy": "Balanced Accuracy (%)",
        "Precision": "Precision (%)",
        "Recall": "Recall (%)",
        "F1 Score": "F1 Score (%)",
        "PR-AUC": "PR-AUC (%)",
    }
)

with st.expander("View complete feature experiment results"):
    st.dataframe(
        feature_display,
        use_container_width=True,
        hide_index=True,
    )

st.markdown("#### Feature approaches explored")

approach_col1, approach_col2 = st.columns(2)

with approach_col1:
    st.markdown(
        """
        **TF-IDF**

        Represents code diff text using word and phrase
        importance scores.

        **Word2Vec**

        Learns vector representations of code tokens
        based on their surrounding context.
        """
    )

with approach_col2:
    st.markdown(
        """
        **Security sensitive API indicators**

        Extracts indicators associated with cryptography,
        authentication, authorization, SQL protection,
        and input validation from added code lines.

        **Combined representation**

        Combines TF-IDF, Word2Vec, and API indicators
        to investigate whether different representations
        complement each other.
        """
    )


st.markdown("#### Key research observations")

st.markdown(
    """
    - **TF-IDF + API Indicators:** Achieved the highest mean
      F1 score (77.63%) and accuracy (89.68%) among the
      four approaches.

    - **TF-IDF Baseline:** Retained the highest mean PR-AUC
      (86.16%), making it the strongest approach under the
      PR-AUC selection criterion.

    - **Word2Vec:** Performed below the TF-IDF baseline when
      used independently.

    - **Combined Representation:** Combining all three
      approaches did not outperform API indicators alone
      on F1 score or the TF-IDF baseline on PR-AUC.
    """
)

st.info(
    "These results are exploratory feature engineering experiments. "
    "The original TF-IDF + Random Oversampling configuration remains "
    "the selected Gerrit deployment model based on mean PR-AUC. "
    "The additional experiments are presented for research comparison "
    "and are not separate deployed prediction models."
)

st.divider()

section_heading(
    "Gerrit confusion matrix",
    "Pooled out-of-fold predictions from the five-fold grouped "
    "cross-validation experiment.",
)

expanded_oof_metrics = {
    "accuracy": 0.8856,
    "balanced_accuracy": 0.8663,
    "precision": 0.7041,
    "recall": 0.8316,
    "f1": 0.7626,
    "pr_auc": 0.8570,
}

matrix = confusion_matrix(
    [0] * (1245 + 137) + [1] * (66 + 326),
    [0] * 1245 + [1] * 137 + [0] * 66 + [1] * 326,
    labels=[0, 1],
)

tn, fp, fn, tp = matrix.ravel()

oof_col1, oof_col2, oof_col3 = st.columns(3)

with oof_col1:
    animated_metric_card(
        "Pooled OOF accuracy",
        expanded_oof_metrics["accuracy"] * 100,
        suffix="%",
        decimals=2,
        note="All out-of-fold predictions",
    )

with oof_col2:
    animated_metric_card(
        "Pooled OOF F1",
        expanded_oof_metrics["f1"] * 100,
        suffix="%",
        decimals=2,
        note="Security related class",
    )

with oof_col3:
    animated_metric_card(
        "Pooled OOF PR-AUC",
        expanded_oof_metrics["pr_auc"] * 100,
        suffix="%",
        decimals=2,
        note="All out-of-fold predictions",
    )


matrix_col, explanation_col = st.columns([1.35, 1])

with matrix_col:
    fig = go.Figure(
        data=go.Heatmap(
            z=matrix,
            x=[
                "Not security related",
                "Security related",
            ],
            y=[
                "Not security related",
                "Security related",
            ],
            colorscale=[
                [0.0, "#14243a"],
                [0.5, "#2563a6"],
                [1.0, "#22a6a1"],
            ],
            showscale=False,
            text=matrix,
            texttemplate="%{text}",
            textfont={
                "size": 22,
                "color": "white",
            },
            hovertemplate=(
                "Actual: %{y}<br>"
                "Predicted: %{x}<br>"
                "Count: %{z}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title="Actual vs. predicted classifications",
        xaxis_title="Predicted label",
        yaxis_title="Actual label",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=420,
        margin={
            "l": 25,
            "r": 25,
            "t": 65,
            "b": 85,
        },
    )

    fig.update_yaxes(
        autorange="reversed"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


with explanation_col:
    st.markdown("#### Prediction breakdown")

    animated_metric_card(
        "True negatives",
        int(tn),
        note="Correctly classified as not security related",
    )

    animated_metric_card(
        "True positives",
        int(tp),
        note="Correctly classified as security related",
    )

    animated_metric_card(
        "False positives",
        int(fp),
        note="Not security related, predicted as security related",
    )

    animated_metric_card(
        "False negatives",
        int(fn),
        note="Security related, predicted as not security related",
    )


st.caption(
    f"Total pooled out-of-fold predictions: "
    f"{tn + fp + fn + tp:,}"
)

st.info(
    "**How to read this matrix:** Rows represent the actual "
    "dataset labels, while columns represent the model's predictions. "
    "Label 0 represents not security related and label 1 represents "
    "security related."
)

st.divider()

with st.expander("View original Gerrit experiment (historical baseline)"):

    st.markdown(
        "The following results are retained for reference from the "
        "original Gerrit experiment. The Gerrit evaluation "
        "above is the primary result used in this application."
    )

    original_gerrit_df = pd.DataFrame([
        {
            "Model": "TF-IDF + Random Oversampling",
            "Mean_Precision": 0.331156,
            "Mean_Recall": 0.387637,
            "Mean_F1": 0.342396,
            "Mean_PR_AUC": 0.328699,
            "Std_PR_AUC": 0.140626,
            "Mean_Balanced_Accuracy": 0.675915,
        },
        {
            "Model": "Combined 18 Features + Random Oversampling",
            "Mean_Precision": 0.313280,
            "Mean_Recall": 0.376923,
            "Mean_F1": 0.332379,
            "Mean_PR_AUC": 0.325922,
            "Std_PR_AUC": 0.109446,
            "Mean_Balanced_Accuracy": 0.669674,
        },
        {
            "Model": "Combined 18 Features + Class Weighting",
            "Mean_Precision": 0.279355,
            "Mean_Recall": 0.361538,
            "Mean_F1": 0.309631,
            "Mean_PR_AUC": 0.308679,
            "Std_PR_AUC": 0.122216,
            "Mean_Balanced_Accuracy": 0.660514,
        },
        {
            "Model": "Structured 18 Features + Random Oversampling",
            "Mean_Precision": 0.052537,
            "Mean_Recall": 0.754258,
            "Mean_F1": 0.098195,
            "Mean_PR_AUC": 0.070210,
            "Std_PR_AUC": 0.028352,
            "Mean_Balanced_Accuracy": 0.598219,
        },
    ])

    original_best = original_gerrit_df.loc[
        original_gerrit_df["Mean_PR_AUC"].idxmax()
    ]

    animated_metric_card(
        "Original best mean PR-AUC",
        float(original_best["Mean_PR_AUC"]) * 100,
        suffix="%",
        decimals=2,
        note=str(original_best["Model"]),
    )

    original_display = original_gerrit_df.copy()

    original_metric_columns = [
        "Mean_Precision",
        "Mean_Recall",
        "Mean_F1",
        "Mean_PR_AUC",
        "Std_PR_AUC",
        "Mean_Balanced_Accuracy",
    ]

    for metric in original_metric_columns:
        original_display[metric] = (
            original_display[metric] * 100
        ).round(2)

    original_display = original_display.rename(
        columns={
            "Mean_Precision": "Mean Precision (%)",
            "Mean_Recall": "Mean Recall (%)",
            "Mean_F1": "Mean F1 (%)",
            "Mean_PR_AUC": "Mean PR-AUC (%)",
            "Std_PR_AUC": "PR-AUC Std. Dev. (percentage points)",
            "Mean_Balanced_Accuracy": "Mean Balanced Accuracy (%)",
        }
    )

    st.dataframe(
        original_display,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Original Gerrit experiment: 1,774 revisions were used "
        "for modelling, with 71 security related and 1,703 "
        "not security related revisions."
    )

st.divider()

section_heading(
    "Research interpretation",
    "Summary of the GitHub and Gerrit findings, including "
    "the additional feature-engineering experiments.",
)

left, right = st.columns(2)

with left:
    st.markdown(
        """
        <div class="cr-card">
          <div class="cr-eyebrow">GITHUB</div>
          <h3>Linear SVM</h3>
          <p>
            Linear SVM achieved the highest F1 score among the
            three evaluated GitHub models.
          </p>
          <p style="color:#94a3b8;font-size:.85rem">
            Input: GitHub pull request review comment text.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.markdown(
        """
        <div class="cr-card">
          <div class="cr-eyebrow">GERRIT</div>
          <h3>TF-IDF + Random Oversampling</h3>
          <p>
            This configuration achieved the highest mean PR-AUC
            among the two Gerrit configurations.
          </p>
          <p style="color:#94a3b8;font-size:.85rem">
            Input: extracted code diffs.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("#### Additional feature-engineering findings")

interpretation_col1, interpretation_col2 = st.columns(2)

with interpretation_col1:
    animated_metric_card(
        "Highest feature experiment F1",
        float(best_feature_f1["F1 Score"]) * 100,
        suffix="%",
        decimals=2,
        note="TF-IDF + API Indicators",
    )

with interpretation_col2:
    animated_metric_card(
        "Highest feature experiment PR-AUC",
        float(best_feature_prauc["PR-AUC"]) * 100,
        suffix="%",
        decimals=2,
        note="TF-IDF Baseline",
    )


st.markdown(
    """
    The additional Gerrit experiments investigated whether
    alternative code representations and security-sensitive
    API indicators could improve classification performance.

    - API indicators produced the highest mean F1 score and precision.
    - The original TF-IDF baseline retained the highest mean PR-AUC.
    - Word2Vec alone performed below the original TF-IDF baseline.
    - Combining all three approaches did not outperform API indicators
      alone on F1 or the baseline on PR-AUC.

    These findings show that additional features can improve certain
    evaluation metrics, but their impact depends on the metric used
    to assess model performance.
    """
)


st.info(
    "**Overall conclusion:** TF-IDF remained the strongest Gerrit "
    "approach under the mean PR-AUC selection criterion, while adding "
    "security-sensitive API indicators improved the mean F1 score. "
    "The original TF-IDF + Random Oversampling configuration therefore "
    "remains the selected Gerrit deployment model."
)

st.info(
    "**Research scope:** The models classify review comments and "
    "code changes according to the security related labels in their "
    "respective datasets."
)