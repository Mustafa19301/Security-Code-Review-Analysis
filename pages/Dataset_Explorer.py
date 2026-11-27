import re

import pandas as pd
import plotly.express as px
import streamlit as st

from app_utils.data_loader import (
    get_file_information,
    load_csv,
)

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
    "DATA INSPECTION",
    "Dataset Explorer",
    "Finalized GitHub and Gerrit datasets used in the research. "
    "Inspect record counts, missing values, duplicate rows, columns, "
    "class distributions and sample records.",
)

API_INDICATOR_PATTERNS = {
    "Cryptography": (
        r"\b(?:Cipher|MessageDigest|SecretKey|KeyGenerator|"
        r"Mac|Signature|SecureRandom|KeyStore)\b"
    ),

    "Authentication": (
        r"\b(?:Authenticator|Credentials|Principal|Authentication|"
        r"LoginContext|PasswordAuthentication)\b"
    ),

    "Authorization": (
        r"\b(?:Permission|AccessController|AccessControlContext|"
        r"ACL|Role|Authorization)\b"
    ),

    "Secure communication": (
        r"\b(?:SSLContext|SSLSocket|TrustManager|X509TrustManager|"
        r"HostnameVerifier|TLS|HttpsURLConnection)\b"
    ),

    "SQL protection": (
        r"\b(?:PreparedStatement|prepareStatement|setString|"
        r"setInt|CallableStatement)\b"
    ),

    "Input validation": (
        r"\b(?:validate\w*|sanitize\w*|Pattern\.compile|"
        r"Matcher|checkNotNull|requireNonNull|"
        r"IllegalArgumentException)\b"
    ),
}


DISPLAY_COLUMN_NAMES = {
    "expanded_security_label": "final_security_label",
}


def prepare_display_dataframe(dataframe):
    """
    Prepare a presentation copy of the dataset.

    The original dataframe and CSV are not modified.
    """

    display_dataframe = dataframe.rename(
        columns=DISPLAY_COLUMN_NAMES
    ).copy()

    if "label_source" in display_dataframe.columns:
        display_dataframe["label_source"] = (
            display_dataframe["label_source"]
            .astype("string")
            .str.replace(
                r"(?i)expanded keyword-based candidate label",
                "Keyword-based candidate label",
                regex=True,
            )
        )

    return display_dataframe


def extract_added_lines(code_diff):
    """
    Extract added lines from a unified code diff.

    Deleted lines and diff header lines are ignored.
    """

    if pd.isna(code_diff):
        return ""

    added_lines = []

    for line in str(code_diff).splitlines():

        if line.startswith("+++") or line.startswith("---"):
            continue

        if line.startswith("+"):
            added_lines.append(line[1:])

    return "\n".join(added_lines)


def calculate_api_indicator_statistics(dataframe):
    """
    Calculate security sensitive API indicator statistics
    from added lines in code diffs.
    """

    if "code_diff" not in dataframe.columns:
        return None

    results = []

    for category, pattern in API_INDICATOR_PATTERNS.items():

        total_occurrences = 0
        revisions_with_indicator = 0

        for code_diff in dataframe["code_diff"]:

            added_text = extract_added_lines(code_diff)

            matches = re.findall(
                pattern,
                added_text,
                flags=re.IGNORECASE,
            )

            occurrence_count = len(matches)
            total_occurrences += occurrence_count

            if occurrence_count > 0:
                revisions_with_indicator += 1

        results.append(
            {
                "API Category": category,
                "Revisions with Indicator": revisions_with_indicator,
                "Total Occurrences": total_occurrences,
            }
        )

    return pd.DataFrame(results)

def build_security_distribution(
    dataframe,
    label_column,
    label_names,
):
    """
    Build a consistent security label distribution.

    Missing labels are displayed separately and are not included
    in the labelled record percentage denominator.
    """

    if label_column not in dataframe.columns:
        return None

    raw_counts = dataframe[label_column].value_counts(
        dropna=False
    )

    results = []

    for raw_label, count in raw_counts.items():

        if pd.isna(raw_label):
            category = "Missing"

        else:
            normalized_label = raw_label

            try:
                numeric_label = float(raw_label)

                if numeric_label.is_integer():
                    normalized_label = int(numeric_label)

            except (ValueError, TypeError):
                pass

            category = label_names.get(
                normalized_label,
                f"Other / unrecognized ({raw_label})",
            )

        results.append(
            {
                "Label": raw_label,
                "Category": category,
                "Records": int(count),
            }
        )

    distribution_df = pd.DataFrame(results)

    total_labelled = int(
        dataframe[label_column].notna().sum()
    )

    if total_labelled > 0:

        distribution_df["Percentage"] = (
            distribution_df.apply(
                lambda row: (
                    row["Records"] / total_labelled * 100
                    if row["Category"] != "Missing"
                    else 0
                ),
                axis=1,
            )
        )

    else:
        distribution_df["Percentage"] = 0.0

    return distribution_df


def display_security_distribution(
    dataframe,
    label_column,
    label_names,
    chart_title,
    section_title,
    section_description,
    metric_definitions,
):
    """
    Display a security distribution chart and summary metrics.
    """

    if label_column not in dataframe.columns:

        st.info(
            "The selected dataset does not contain the expected "
            "security classification field."
        )

        return

    distribution_df = build_security_distribution(
        dataframe,
        label_column,
        label_names,
    )

    if distribution_df is None or distribution_df.empty:

        st.info(
            "No security label information is available."
        )

        return

    section_heading(
        section_title,
        section_description,
    )

    distribution_col, summary_col = st.columns([1.4, 1])

    with distribution_col:

        fig = px.bar(
            distribution_df,
            x="Category",
            y="Records",
            color="Category",
            text="Records",
            title=chart_title,
            template="plotly_dark",
        )

        fig.update_layout(
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Security classification",
            yaxis_title="Number of records",
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )

    with summary_col:

        valid_labels = dataframe[label_column].dropna()
        total_labelled = len(valid_labels)

        for label_value, metric_name in metric_definitions:

            count = int(
                (valid_labels == label_value).sum()
            )

            percentage = (
                count / total_labelled * 100
                if total_labelled > 0
                else 0
            )

            st.metric(
                metric_name,
                f"{count:,}",
                f"{percentage:.1f}% of labelled records",
            )

        st.caption(
            f"Total labelled records: {total_labelled:,}"
        )

        missing_count = int(
            dataframe[label_column].isna().sum()
        )

        if missing_count > 0:

            st.caption(
                f"Records with missing labels: {missing_count:,}"
            )

    st.markdown("**Security distribution breakdown**")

    display_distribution = distribution_df.copy()

    display_distribution["Percentage"] = (
        display_distribution["Percentage"].map(
            lambda value: f"{value:.2f}%"
        )
    )

    display_distribution = display_distribution[
        ["Category", "Records", "Percentage"]
    ]

    st.dataframe(
        display_distribution,
        width="stretch",
        hide_index=True,
    )

dataset_options = {
    "GitHub — Finalized Dataset": "github_final",
    "Gerrit — Finalized Dataset": "gerrit_expanded_final",
    "Gerrit — Original Dataset": "gerrit_final",
    "Gerrit — Structured Features": "gerrit_features",
}

choice_col, info_col = st.columns([1.2, 2])

with choice_col:

    dataset_choice = st.selectbox(
        "Select dataset",
        list(dataset_options.keys()),
    )

file_key = dataset_options[dataset_choice]
file_info = get_file_information(file_key)

if not file_info["exists"]:

    st.error(
        "The selected dataset file could not be found. "
        "Please check the dataset configuration."
    )

    st.stop()


with st.spinner("Loading selected research dataset..."):

    df = load_csv(file_key)

if df is None:

    st.error(
        "Unable to load the selected dataset."
    )

    st.stop()

display_df = prepare_display_dataframe(df)

excluded_missing_columns = [
    "label_evidence_categories",
    "matched_strong",
    "matched_weak",
    "matched_security_categories",
]

missing_report_df = df.drop(
    columns=excluded_missing_columns,
    errors="ignore",
)

row_count = len(df)
column_count = len(df.columns)

missing_count = int(
    missing_report_df.isna().sum().sum()
)

duplicate_count = int(
    df.duplicated().sum()
)

st.markdown(
    f'<span class="cr-pill">{dataset_choice.upper()}</span>',
    unsafe_allow_html=True,
)

st.caption(
    f"Dataset size: {file_info['size_mb']} MB"
)

metric_cols = st.columns(4)

dataset_metrics = [
    ("Total records", row_count, "Rows in selected dataset"),
    ("Total columns", column_count, "Dataset fields"),
    ("Missing values", missing_count, "Null or empty cells"),
    ("Duplicate rows", duplicate_count, "Fully duplicated records"),
]

for col, (label, value, note) in zip(
    metric_cols,
    dataset_metrics,
):

    with col:

        animated_metric_card(
            label,
            value,
            note=note,
            duration=1100,
        )

st.write("")

section_heading(
    "Dataset profile",
    "A quick view of the selected file's structure and completeness.",
)

profile_left, profile_right = st.columns([1.1, 1])

with profile_left:

    type_counts = (
        df.dtypes.astype(str)
        .value_counts()
        .rename_axis("Data type")
        .reset_index(name="Columns")
    )

    fig = px.bar(
        type_counts,
        x="Data type",
        y="Columns",
        color="Data type",
        text="Columns",
        title="Column data types",
        template="plotly_dark",
    )

    fig.update_layout(
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


with profile_right:

    missing_data = (
        missing_report_df.isna()
        .sum()
        .reset_index()
    )

    missing_data.columns = [
        "Column",
        "Missing Values",
    ]

    missing_data = missing_data[
        missing_data["Missing Values"] > 0
    ].sort_values(
        "Missing Values",
        ascending=False,
    )

    if missing_data.empty:

        st.success(
            "No missing values were found in this dataset."
        )

    else:

        missing_data["Column"] = (
            missing_data["Column"].replace(
                DISPLAY_COLUMN_NAMES
            )
        )

        fig = px.bar(
            missing_data.head(15),
            x="Missing Values",
            y="Column",
            orientation="h",
            title="Columns with missing values",
            template="plotly_dark",
            text="Missing Values",
        )

        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )

st.write("")

if file_key == "github_final":

    github_label_names = {
        0: "Not security related",
        1: "Security related",
        2: "Uncertain",
    }

    display_security_distribution(
        dataframe=df,
        label_column="security_label",
        label_names=github_label_names,
        chart_title="GitHub security classification distribution",
        section_title="GitHub security label distribution",
        section_description=(
            "Distribution of security related, non security related, "
            "and uncertain GitHub records."
        ),
        metric_definitions=[
            (1, "Security related"),
            (0, "Not security related"),
            (2, "Uncertain"),
        ],
    )


elif file_key == "gerrit_expanded_final":

    gerrit_label_names = {
        0: "Not security related",
        1: "Security related",
    }

    display_security_distribution(
        dataframe=df,
        label_column="expanded_security_label",
        label_names=gerrit_label_names,
        chart_title="Gerrit security classification distribution",
        section_title="Gerrit security label distribution",
        section_description=(
            "Distribution of security related and "
            "non security related Gerrit revisions."
        ),
        metric_definitions=[
            (1, "Security related"),
            (0, "Not security related"),
        ],
    )

if file_key in (
    "github_final",
    "gerrit_expanded_final",
):

    with st.expander(
        "How is the security distribution determined?"
    ):

        if file_key == "github_final":

            st.markdown(
                """
                ### GitHub: Three class annotation scheme

                The finalized GitHub dataset uses three labels to
                distinguish security-related changes from changes
                that do not have identifiable security relevance
                and cases where the available evidence is insufficient.

                | Label | Classification | Interpretation |
                |---|---|---|
                | 0 | Not security related | No identifiable security relevance in the available change context. |
                | 1 | Security related | Evidence indicates a security focused change or an attempt to address a vulnerability. |
                | 2 | Uncertain | Available information is insufficient to confidently assign either binary classification. |

                ### How the classification is interpreted

                Security relevance should be assessed using the available
                change context, including commit or pull request
                descriptions and the associated code changes.

                Examples of potentially relevant evidence include:

                - Authentication and authorization changes.
                - Credential and password handling.
                - Cryptographic operations and secure communication.
                - Input validation and sanitization.
                - SQL injection prevention and other security-focused fixes.

                **Keywords are candidate signals, not proof of security
                relevance.** A keyword appearing in a description or
                code change does not automatically make that record
                security related nor a vulnerability present.
                """
            )

        else:

            st.markdown(
                """
                ### Gerrit: Binary classification scheme

                The finalized Gerrit dataset uses two classes to
                represent whether a revision is security related.

                | Label | Classification | Interpretation |
                |---|---|---|
                | 0 | Not security related | The revision is assigned to the non security related class. |
                | 1 | Security related | The revision is assigned to the security related class. |

                ### How the labels were determined

                The finalized Gerrit dataset contains 2,635 revisions.

                ### Security related indicators

                The candidate review considered indicators associated
                with areas such as:

                - Secrets and sensitive data.
                - Authorization and access control.
                - Authentication.
                - Secure communication.
                - Injection and input validation.
                - Cryptography.

                These indicators were used to identify potentially
                relevant revisions. A keyword match alone does not
                independently prove that a revision fixes a
                vulnerability or introduces a security improvement.

                ### Understanding the distribution

                The chart counts the final binary classifications
                across all 2,635 records.

                Percentages are calculated using the number of
                records with non missing final security labels.
                """
            )

        st.info(
            "The Dataset Explorer reports the labels already stored "
            "in the selected finalized dataset. It does not generate, "
            "change, or independently verify security labels."
        )

st.write("")

if file_key == "gerrit_expanded_final":

    section_heading(
        "Security sensitive API indicator statistics",
        "Occurrences of selected security sensitive Java APIs and coding patterns "
        "in added code lines.",
    )

    api_statistics = calculate_api_indicator_statistics(df)

    if api_statistics is None:

        st.info(
            "API indicator statistics require a code_diff column "
            "in the selected dataset."
        )

    else:

        total_api_occurrences = int(
            api_statistics["Total Occurrences"].sum()
        )

        categories_found = int(
            (
                api_statistics["Total Occurrences"] > 0
            ).sum()
        )

        revisions_with_any_indicator = 0

        if "code_diff" in df.columns:

            for code_diff in df["code_diff"]:

                added_text = extract_added_lines(code_diff)

                found_indicator = any(
                    re.search(
                        pattern,
                        added_text,
                        flags=re.IGNORECASE,
                    )
                    for pattern in API_INDICATOR_PATTERNS.values()
                )

                if found_indicator:
                    revisions_with_any_indicator += 1

        api_metric_cols = st.columns(3)

        api_metrics = [
            (
                "Total occurrences",
                total_api_occurrences,
                "Across all six categories",
            ),
            (
                "Categories detected",
                categories_found,
                "Categories with at least one match",
            ),
            (
                "Revisions with indicators",
                revisions_with_any_indicator,
                "At least one matching indicator",
            ),
        ]

        for col, (label, value, note) in zip(
            api_metric_cols,
            api_metrics,
        ):

            with col:

                animated_metric_card(
                    label,
                    value,
                    note=note,
                    duration=1100,
                )

        st.write("")

        indicator_col, table_col = st.columns([1.3, 1])

        with indicator_col:

            fig = px.bar(
                api_statistics,
                x="API Category",
                y="Total Occurrences",
                color="API Category",
                text="Total Occurrences",
                title="API indicator occurrences by category",
                template="plotly_dark",
            )

            fig.update_layout(
                showlegend=False,
                xaxis_tickangle=-25,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )

            st.plotly_chart(
                fig,
                width="stretch",
            )

        with table_col:

            st.markdown("**Indicator breakdown**")

            st.dataframe(
                api_statistics,
                width="stretch",
                hide_index=True,
            )

        st.caption(
            "Statistics are calculated from added lines in code diffs. "
            "Each matching API or pattern occurrence is counted. "
            "A revision is counted once per category when it contains "
            "at least one matching occurrence."
        )

        st.info(
            "These indicators identify selected API references and "
            "coding patterns. Their presence does not independently "
            "establish whether a code change is vulnerable or secure."
        )

st.write("")

section_heading(
    "Dataset preview",
    "Search across columns and inspect a manageable sample of records.",
)

search_text = st.text_input(
    "Search records",
    placeholder="Enter a keyword to filter records...",
)

filtered_df = display_df

if search_text.strip():

    matches = display_df.astype(str).apply(
        lambda column: column.str.contains(
            search_text.strip(),
            case=False,
            na=False,
            regex=False,
        )
    ).any(axis=1)

    filtered_df = display_df[matches]


preview_limit = st.select_slider(
    "Preview rows",
    options=[50, 100, 250, 500],
    value=250,
)

st.caption(
    f"Showing {min(preview_limit, len(filtered_df)):,} "
    f"of {len(filtered_df):,} matching records."
)

st.dataframe(
    filtered_df.head(preview_limit),
    width="stretch",
    height=430,
)

csv_bytes = (
    filtered_df.head(5000)
    .to_csv(index=False)
    .encode("utf-8")
)

download_names = {
    "github_final": "github_finalized_preview.csv",
    "gerrit_expanded_final": "gerrit_finalized_preview.csv",
    "gerrit_final": "gerrit_original_preview.csv",
    "gerrit_features": "gerrit_structured_features_preview.csv",
}

st.download_button(
    "Download filtered preview (up to 5,000 rows)",
    data=csv_bytes,
    file_name=download_names.get(
        file_key,
        "dataset_preview.csv",
    ),
    mime="text/csv",
)

st.write("")

section_heading(
    "Column information",
    "Data types, missing values and unique values for each dataset field.",
)

excluded_columns_present = [
    column
    for column in excluded_missing_columns
    if column in df.columns
]

missing_counts = (
    missing_report_df.isna()
    .sum()
)

column_info_records = []

for column in df.columns:

    if column in excluded_columns_present:
        missing_value_display = "Not reported"

    else:
        missing_value_display = str(
            int(missing_counts.get(column, 0))
        )

    display_column_name = DISPLAY_COLUMN_NAMES.get(
        column,
        column,
    )

    column_info_records.append(
        {
            "Column": display_column_name,
            "Data Type": str(df[column].dtype),
            "Missing Values": missing_value_display,
            "Unique Values": int(
                df[column].nunique(dropna=True)
            ),
        }
    )

column_info = pd.DataFrame(
    column_info_records
)

st.dataframe(
    column_info,
    width="stretch",
    hide_index=True,
)

with st.expander("View full missing-value report"):

    if missing_data.empty:

        st.success(
            "No missing values were found in the reported columns."
        )

    else:

        st.dataframe(
            missing_data,
            width="stretch",
            hide_index=True,
        )

    if excluded_columns_present:

        display_excluded_columns = [
            DISPLAY_COLUMN_NAMES.get(column, column)
            for column in excluded_columns_present
        ]

        st.caption(
            "Excluded internal metadata columns: "
            + ", ".join(display_excluded_columns)
            + ". Their missing values are not included in this report."
        )


st.caption(
    "Dataset statistics are calculated from the selected processed "
    "CSV loaded by the application."
)