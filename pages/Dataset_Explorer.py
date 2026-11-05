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

st.set_page_config(
    page_title="Dataset Explorer | CodeReview Sentinel",
    layout="wide",
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

# Exclude internal metadata from missing-value reporting
# GitHub: matched_strong, matched_weak
# Gerrit: label_evidence_categories
missing_report_df = df.drop(
    columns=[
        "label_evidence_categories",
        "matched_strong",
        "matched_weak",
    ],
    errors="ignore",
)

row_count = len(df)
column_count = len(df.columns)
missing_count = int(missing_report_df.isna().sum().sum())
duplicate_count = int(df.duplicated().sum())

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
    missing_data = missing_report_df.isna().sum().reset_index()
    missing_data.columns = ["Column", "Missing Values"]

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

# Gerrit expanded dataset class distribution
if (
    file_key == "gerrit_expanded_final"
    and "security_label_binary" in df.columns
):
    section_heading(
        "Gerrit security-label distribution",
        "Distribution of security-related and non-security-related revisions.",
    )

    label_counts = (
        df["security_label_binary"]
        .value_counts(dropna=False)
        .rename_axis("Label")
        .reset_index(name="Records")
    )

    label_names = {
        0: "Not security-related",
        1: "Security-related",
    }

    label_counts["Category"] = (
        label_counts["Label"]
        .map(label_names)
        .fillna("Other / missing")
    )

    label_counts["Category"] = label_counts["Category"].astype(str)

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
        valid_labels = df["security_label_binary"].dropna()

        positive_count = int(
            (valid_labels == 1).sum()
        )

        negative_count = int(
            (valid_labels == 0).sum()
        )

        total_labelled = positive_count + negative_count

        if total_labelled > 0:
            st.metric(
                "Security-related",
                f"{positive_count:,}",
                f"{positive_count / total_labelled * 100:.1f}% of labelled records",
            )

            st.metric(
                "Not security-related",
                f"{negative_count:,}",
                f"{negative_count / total_labelled * 100:.1f}% of labelled records",
            )

        st.caption(
            "Binary labels: 0 = Not security-related; "
            "1 = Security-related."
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

section_heading("Column information")

column_info = pd.DataFrame(
    {
        "Column": df.columns,
        "Data Type": df.dtypes.astype(str).values,
        "Missing Values": missing_report_df.isna().sum().values,
        "Unique Values": df.nunique(dropna=True).values,
    }
)

st.dataframe(
    column_info,
    use_container_width=True,
    hide_index=True,
)

with st.expander("View full missing-value report"):
    if missing_data.empty:
        st.success("No missing values were found.")
    else:
        st.dataframe(
            missing_data,
            use_container_width=True,
            hide_index=True,
        )

st.caption(
    "Dataset statistics are calculated from the selected processed "
    "CSV loaded by the application."
)