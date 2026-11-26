import re

import pandas as pd
import plotly.express as px
import streamlit as st

from app_utils.data_loader import (
    DATA_FILES,
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
    "Explore finalized GitHub and Gerrit datasets used in the research. "
    "Inspect record counts, missing values, duplicate rows, columns, "
    "class distributions, and sample records.",
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

    Returns
    -------
    pandas.DataFrame
        Total occurrences and number of revisions containing
        each API indicator category.
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

dataset_options = {
    "GitHub — Finalized Dataset": "github_final",
    "Gerrit — Finalized Expanded Dataset": "gerrit_expanded_final",
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
    st.error("The selected dataset file could not be found.")
    st.code(DATA_FILES[file_key])
    st.stop()

with st.spinner("Loading selected research dataset..."):
    df = load_csv(file_key)

if df is None:
    st.error("Unable to load the selected dataset.")
    st.stop()


excluded_missing_columns = [
    "label_evidence_categories",
    "matched_strong",
    "matched_weak",
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
    f"`{file_info['path']}` · {file_info['size_mb']} MB"
)

metric_cols = st.columns(4)

dataset_metrics = [
    ("Total records", row_count, "Rows in selected dataset"),
    ("Total columns", column_count, "Dataset fields"),
    ("Missing values", missing_count, "Null or empty cells"),
    ("Duplicate rows", duplicate_count, "Fully duplicated records"),
]

for col, (label, value, note) in zip(metric_cols, dataset_metrics):
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
        use_container_width=True,
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
            use_container_width=True,
        )

st.write("")

if (
    file_key == "gerrit_expanded_final"
    and "security_label_binary" in df.columns
):

    section_heading(
        "Gerrit security label distribution",
        "Distribution of security related and non security related revisions.",
    )

    label_counts = (
        df["security_label_binary"]
        .value_counts(dropna=False)
        .rename_axis("Label")
        .reset_index(name="Records")
    )

    label_names = {
        0: "Not security related",
        1: "Security related",
    }

    label_counts["Category"] = (
        label_counts["Label"]
        .map(label_names)
        .fillna("Other / missing")
    )

    label_counts["Category"] = (
        label_counts["Category"].astype(str)
    )

    distribution_col, summary_col = st.columns([1.4, 1])

    with distribution_col:

        fig = px.bar(
            label_counts,
            x="Category",
            y="Records",
            color="Category",
            text="Records",
            title="Gerrit classification labels",
            template="plotly_dark",
        )

        fig.update_layout(
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with summary_col:

        valid_labels = (
            df["security_label_binary"].dropna()
        )

        positive_count = int(
            (valid_labels == 1).sum()
        )

        negative_count = int(
            (valid_labels == 0).sum()
        )

        total_labelled = (
            positive_count + negative_count
        )

        if total_labelled > 0:

            st.metric(
                "Security related",
                f"{positive_count:,}",
                f"{positive_count / total_labelled * 100:.1f}% of labelled records",
            )

            st.metric(
                "Not security related",
                f"{negative_count:,}",
                f"{negative_count / total_labelled * 100:.1f}% of labelled records",
            )

        st.caption(
            "Binary labels: 0 = Not security related; "
            "1 = Security related."
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
                use_container_width=True,
            )

        with table_col:

            st.markdown("**Indicator breakdown**")

            st.dataframe(
                api_statistics,
                use_container_width=True,
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

display_df = df

if search_text.strip():

    matches = df.astype(str).apply(
        lambda column: column.str.contains(
            search_text.strip(),
            case=False,
            na=False,
            regex=False,
        )
    ).any(axis=1)

    display_df = df[matches]

preview_limit = st.select_slider(
    "Preview rows",
    options=[50, 100, 250, 500],
    value=250,
)

st.caption(
    f"Showing {min(preview_limit, len(display_df)):,} "
    f"of {len(display_df):,} matching records."
)

st.dataframe(
    display_df.head(preview_limit),
    use_container_width=True,
    height=430,
)

csv_bytes = (
    display_df.head(5000)
    .to_csv(index=False)
    .encode("utf-8")
)

st.download_button(
    "Download filtered preview (up to 5,000 rows)",
    data=csv_bytes,
    file_name=f"{file_key}_preview.csv",
    mime="text/csv",
)

st.write("")


section_heading(
    "Column information",
    "Data types, missing values, and unique values for each dataset field.",
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
        missing_value_display = int(
            missing_counts.get(column, 0)
        )

    column_info_records.append(
        {
            "Column": column,
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
    use_container_width=True,
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
            use_container_width=True,
            hide_index=True,
        )

    if excluded_columns_present:

        st.caption(
            "Excluded internal metadata columns: "
            + ", ".join(excluded_columns_present)
            + ". Their missing values are not included in this report."
        )


st.caption(
    "Dataset statistics are calculated from the selected processed "
    "CSV loaded by the application."
)