import pandas as pd

REVIEW_FILE = "data/processed/security_review_sample.csv"

print("=" * 70)
print("ANALYZING MANUAL SECURITY LABELS")
print("=" * 70)

df = pd.read_csv(REVIEW_FILE)

print(f"\nTotal reviewed comments: {len(df):,}")

print("\nColumns found:")
for column in df.columns:
    print(f"  - {column}")


df["manual_label"] = pd.to_numeric(
    df["manual_label"],
    errors="coerce"
)

df = df.dropna(subset=["manual_label"]).copy()
df["manual_label"] = df["manual_label"].astype(int)


print("\n" + "-" * 70)
print("OVERALL MANUAL LABEL DISTRIBUTION")
print("-" * 70)

label_counts = df["manual_label"].value_counts().sort_index()

label_names = {
    0: "Not security-related",
    1: "Clearly security-related",
    2: "Possibly security-related",
}

for label, count in label_counts.items():
    label_name = label_names.get(label, "Unknown label")
    percentage = count / len(df) * 100

    print(
        f"Label {label} - {label_name}: "
        f"{count:,} ({percentage:.2f}%)"
    )

print("\n" + "-" * 70)
print("REVIEW GROUP VS MANUAL LABEL")
print("-" * 70)

group_table = pd.crosstab(
    df["review_group"],
    df["manual_label"]
)

print(group_table)

print("\n" + "-" * 70)
print("PERCENTAGES WITHIN EACH REVIEW GROUP")
print("-" * 70)

group_percentage_table = pd.crosstab(
    df["review_group"],
    df["manual_label"],
    normalize="index"
) * 100

print(group_percentage_table.round(2))

print("\n" + "-" * 70)
print("CANDIDATE QUALITY")
print("-" * 70)

candidate_rows = df[
    df["review_group"].isin(
        ["strong_candidate", "weak_candidate"]
    )
]

clearly_security_count = (
    candidate_rows["manual_label"] == 1
).sum()

candidate_precision = (
    clearly_security_count / len(candidate_rows) * 100
)

print(
    "Percentage of keyword-selected candidates that were "
    f"clearly security-related: {candidate_precision:.2f}%"
)

for group_name in [
    "strong_candidate",
    "weak_candidate",
]:
    group_rows = df[
        df["review_group"] == group_name
    ]

    if len(group_rows) == 0:
        continue

    clearly_security = (
        group_rows["manual_label"] == 1
    ).sum()

    precision = clearly_security / len(group_rows) * 100

    print(
        f"{group_name}: "
        f"{clearly_security}/{len(group_rows)} clearly security-related "
        f"({precision:.2f}%)"
    )

print("\n" + "-" * 70)
print("EXAMPLES OF FALSE POSITIVES")
print("-" * 70)

false_positives = df[
    (
        df["review_group"].isin(
            ["strong_candidate", "weak_candidate"]
        )
    )
    &
    (df["manual_label"] == 0)
]

for _, row in false_positives.head(10).iterrows():
    print("\nComment ID:", row["comment_id"])
    print("Review group:", row["review_group"])
    print("Matched strong:", row["matched_strong"])
    print("Matched weak:", row["matched_weak"])
    print("Comment:", row["comment"])
    print("Review notes:", row["review_notes"])


output_file = "data/processed/security_review_sample_clean.csv"

df.to_csv(
    output_file,
    index=False
)

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)

print(f"\nCleaned review file saved to:")
print(output_file)