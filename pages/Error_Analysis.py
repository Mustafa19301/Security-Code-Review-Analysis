import re

import pandas as pd
import plotly.express as px
import streamlit as st

from app_utils.data_loader import load_csv

from components.ui import (
    inject_theme,
    sidebar_brand,
    page_header,
    section_heading,
    animated_metric_card,
)

st.set_page_config(
    page_title="Error Analysis | CodeReview Sentinel",
    layout="wide",
)

inject_theme()
sidebar_brand()

page_header(
    "MODEL DIAGNOSTICS",
    "Error Analysis",
    "Inspect expanded Gerrit classification errors to understand "
    "where the selected model struggles and identify opportunities "
    "for future improvement.",
)


def normalized(name):
    return re.sub(
        r"[^a-z0-9]+",
        "_",
        str(name).strip().lower(),
    ).strip("_")


def find_column(df, names):
    if df is None or df.empty:
        return None

    lookup = {
        normalized(column): column
        for column in df.columns
    }

    for name in names:
        if normalized(name) in lookup:
            return lookup[normalized(name)]

    return None


def search_records(df, query):
    if df.empty or not query:
        return df

    mask = df.astype(str).apply(
        lambda col: col.str.contains(
            query,
            case=False,
            na=False,
            regex=False,
        )
    ).any(axis=1)

    return df[mask]


def get_error_columns(records):
    review_col = find_column(
        records,
        [
            "review_number",
            "review_id",
            "change_id",
        ],
    )

    revision_col = find_column(
        records,
        [
            "revision_number",
            "revision_id",
            "patchset",
        ],
    )

    score_col = find_column(
        records,
        [
            "predicted_probability",
            "prediction_probability",
            "security_probability",
            "positive_probability",
            "probability",
            "prediction_score",
            "model_score",
            "score",
            "y_score",
        ],
    )

    diff_col = find_column(
        records,
        [
            "code_diff",
            "diff",
            "patch",
            "diff_text",
            "code",
            "text",
        ],
    )

    return review_col, revision_col, score_col, diff_col

def exclude_large_false_positive(records):
    """
    Exclude Review 12050, Revision 2 from false-positive inspection.
    Does not modify the original evaluation counts.
    """

    review_col, revision_col, _, _ = get_error_columns(records)

    if review_col is None or revision_col is None:
        return records

    review_values = records[review_col].astype(str).str.strip()
    revision_values = records[revision_col].astype(str).str.strip()

    excluded = (
        review_values.eq("12050")
        & revision_values.eq("2")
    )

    return records.loc[~excluded].copy()


def render_error_inspection(fp, fn, section_name):
    """
    Display error metrics, composition, explanations,
    and individual misclassified records.
    """

    fp = fp.copy() if fp is not None else pd.DataFrame()
    fn = fn.copy() if fn is not None else pd.DataFrame()

    fp_count = len(fp)
    fn_count = len(fn)
    total = fp_count + fn_count


    metrics = st.columns(3)

    with metrics[0]:
        animated_metric_card(
            "False positives",
            fp_count,
            note="Predicted security-related, label was negative",
        )

    with metrics[1]:
        animated_metric_card(
            "False negatives",
            fn_count,
            note="Predicted negative, label was security-related",
        )

    with metrics[2]:
        animated_metric_card(
            "Total errors",
            total,
            note="Combined recorded misclassifications",
        )

    if total == 0:
        st.info(
            "No false-positive or false-negative records "
            "were found for this experiment."
        )
        return

    st.write("")

    section_heading(
        "Error composition",
        "Distribution of recorded out-of-fold misclassifications.",
    )

    chart_data = pd.DataFrame(
        {
            "Error type": [
                "False positives",
                "False negatives",
            ],
            "Records": [
                fp_count,
                fn_count,
            ],
        }
    )

    chart_col, insight_col = st.columns([1.2, 1])

    with chart_col:
        fig = px.pie(
            chart_data,
            names="Error type",
            values="Records",
            hole=0.62,
            color="Error type",
            color_discrete_map={
                "False positives": "#F59E0B",
                "False negatives": "#EF4444",
            },
            template="plotly_dark",
            title="Share of recorded errors",
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend_title=None,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with insight_col:
        st.markdown(
            f"""
            <div class="cr-card" style="margin-top:1.5rem">
              <div class="cr-eyebrow">ERROR MIX</div>
              <div class="cr-card-value">
                {fp_count / total * 100:.1f}%
              </div>
              <div class="cr-card-label">
                of recorded errors are false positives
              </div>
              <hr>
              <div class="cr-card-value">
                {fn_count / total * 100:.1f}%
              </div>
              <div class="cr-card-label">
                of recorded errors are false negatives
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    section_heading("Understanding the errors")

    false_tab, missed_tab = st.tabs(
        [
            "False positives",
            "False negatives",
        ]
    )

    with false_tab:
        st.markdown(
            """
            **Incorrect security-related prediction**

            The model predicts security-related even though the
            assigned dataset label is not security-related.

            **Potential impact:** Reviewers may spend time investigating
            changes that are not security-related.

            **Possible contributors:** security terminology in ordinary
            changes, authentication or permission tests, reliance on
            familiar keywords, and insufficient surrounding context.
            """
        )

    with missed_tab:
        st.markdown(
            """
            **Missed security-related prediction**

            The model predicts not security-related even though the
            assigned dataset label is security-related.

            **Potential impact:** A security-related change may not
            be flagged for additional review.

            **Possible contributors:** unfamiliar security terminology,
            short diffs, missing context, and the limited number of
            security-related examples available during training.
            """
        )

    st.divider()


    section_heading(
        "Inspect misclassified records",
        "Filter by error type and inspect individual scores, "
        "identifiers, and code diffs.",
    )

    error_filter = st.radio(
        "Record category",
        [
            "False positives",
            "False negatives",
        ],
        horizontal=True,
        key=f"{section_name}_error_filter",
    )

    records = (
        exclude_large_false_positive(fp)
        if error_filter == "False positives"
        else fn.copy()
    )

    if records.empty:
        st.info(
            "No records are available for this category."
        )
        return

    review_col, revision_col, score_col, diff_col = (
        get_error_columns(records)
    )


    if score_col:
        records[score_col] = pd.to_numeric(
            records[score_col],
            errors="coerce",
        )

        records = records.sort_values(
            score_col,
            ascending=(
                error_filter == "False negatives"
            ),
            na_position="last",
        )


    search_query = st.text_input(
        "Search this category",
        placeholder="Search review ID, revision, or diff text...",
        key=f"{section_name}_search",
    )

    records = search_records(
        records,
        search_query.strip(),
    )

    if records.empty:
        st.info("No records matched your search.")
        return


    if score_col and records[score_col].notna().any():
        score_values = records[score_col].dropna()

        low = float(score_values.min())
        high = float(score_values.max())

        st.caption(
            f"Model score range in filtered records: "
            f"{low:.4f}–{high:.4f}"
        )


    table_columns = [
        column
        for column in [
            review_col,
            revision_col,
            score_col,
        ]
        if column
    ]

    if table_columns:
        st.dataframe(
            records[table_columns],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.dataframe(
            records.head(100),
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        f"{len(records):,} matching records"
    )

    options = list(records.index)

    selected_index = st.selectbox(
        "Choose a record to inspect",
        options,
        format_func=lambda idx: (
            f"Review "
            f"{records.loc[idx, review_col] if review_col else idx}"
            +
            (
                f" · Revision {records.loc[idx, revision_col]}"
                if revision_col
                else ""
            )
            +
            (
                f" · Score {records.loc[idx, score_col]:.4f}"
                if score_col
                and pd.notna(records.loc[idx, score_col])
                else ""
            )
        ),
        key=f"{section_name}_selected_record",
    )

    selected = records.loc[selected_index]

    details_col, diff_col_panel = st.columns(
        [1, 1.5]
    )

    with details_col:
        st.markdown("#### Record details")

        detail_data = pd.DataFrame(
            {
                "Field": records.columns,
                "Value": [
                    str(selected[column])
                    for column in records.columns
                ],
            }
        )

        st.dataframe(
            detail_data,
            use_container_width=True,
            hide_index=True,
            height=330,
        )

    with diff_col_panel:
        st.markdown("#### Code diff")

        if (
            diff_col
            and pd.notna(selected[diff_col])
            and str(selected[diff_col]).strip()
        ):
            st.code(
                str(selected[diff_col]),
                language="diff",
            )

        else:
            st.info(
                "No code-diff text was included in this record."
            )


st.markdown(
    '<span class="cr-pill">CURRENT GERRIT EXPERIMENT</span>',
    unsafe_allow_html=True,
)

st.write("")

expanded_fp = load_csv(
    "gerrit_expanded_false_positives"
)

expanded_fn = load_csv(
    "gerrit_expanded_false_negatives"
)

if expanded_fp is None or expanded_fn is None:
    st.error(
        "The expanded Gerrit false-positive or false-negative "
        "CSV file could not be loaded. Check the expanded Gerrit "
        "paths in app_utils/data_loader.py."
    )

    st.stop()


section_heading(
    "Expanded Gerrit error analysis",
    "Out-of-fold classification errors from the expanded "
    "TF-IDF + Random Oversampling + Logistic Regression model.",
)

render_error_inspection(
    expanded_fp,
    expanded_fn,
    "expanded_gerrit",
)

st.divider()

with st.expander(
    "View original Gerrit error analysis (historical baseline)"
):
    original_fp = load_csv(
        "gerrit_false_positives"
    )

    original_fn = load_csv(
        "gerrit_false_negatives"
    )

    if original_fp is None or original_fn is None:
        st.warning(
            "The original Gerrit error files could not be loaded."
        )

    else:
        st.markdown(
            "These are the recorded errors from the original Gerrit "
            "experiment. The expanded Gerrit analysis above is the "
            "primary result for this research."
        )

        render_error_inspection(
            original_fp,
            original_fn,
            "original_gerrit",
        )


st.divider()

section_heading(
    "Research observations",
    "What the expanded Gerrit model's classification errors can tell us.",
)

st.markdown(
    """
    The expanded Gerrit dataset contains both security-related and
    non-security-related revisions. Although the expanded dataset
    provides more security-related examples than the original
    experiment, the two classes are still imbalanced.

    Text-based models can associate familiar words and programming
    patterns with the positive class even when the full change context
    does not support that interpretation. Conversely, less familiar
    security-related changes may be missed.

    Examining false positives and false negatives helps identify
    patterns that could guide future improvements to the model
    and its feature representation.
    """
)

st.info(
    "Interpretation note: these errors represent disagreement with "
    "the dataset's assigned labels. They do not independently establish "
    "whether an exploitable vulnerability was present or absent."
)


with st.expander("Evaluation methodology"):
    st.markdown(
        """
        **Dataset:** Expanded Couchbase Java Client Gerrit dataset.

        **Model configuration:** TF-IDF + Random Oversampling +
        Logistic Regression.

        **Input:** Extracted code diffs.

        **Evaluation:** Five-fold Stratified Group Cross-Validation
        grouped by review number.

        **Positive class:** Security-related (label 1).

        **Error source:** Saved out-of-fold predictions. These are
        evaluation errors, not predictions from the deployment model
        trained on the full eligible dataset.
        """
    )