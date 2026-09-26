import os
import pandas as pd
from collections import Counter


# ------------------------------------------------------------
# FILE PATHS
# ------------------------------------------------------------

INPUT_FILE = "data/processed/security_review_sample_clean.csv"
OUTPUT_FILE = "data/processed/false_positive_analysis.csv"


# ------------------------------------------------------------
# LOAD REVIEWED DATA
# ------------------------------------------------------------

print("=" * 70)
print("ANALYZING SECURITY-CANDIDATE FALSE POSITIVES")
print("=" * 70)

print("\nLoading reviewed sample...")

df = pd.read_csv(INPUT_FILE)

print(f"Loaded {len(df):,} reviewed comments.")


# ------------------------------------------------------------
# CLEAN LABELS
# ------------------------------------------------------------

df["manual_label"] = pd.to_numeric(
    df["manual_label"],
    errors="coerce"
)

df = df.dropna(subset=["manual_label"]).copy()
df["manual_label"] = df["manual_label"].astype(int)


# ------------------------------------------------------------
# SELECT FALSE POSITIVES
# ------------------------------------------------------------

# False positives are comments selected as candidates
# but manually labeled as not security-related.

false_positives = df[
    (
        df["review_group"].isin(
            ["strong_candidate", "weak_candidate"]
        )
    )
    &
    (df["manual_label"] == 0)
].copy()

print(
    f"\nFalse positives found: "
    f"{len(false_positives):,}"
)


# ------------------------------------------------------------
# FALSE POSITIVES BY REVIEW GROUP
# ------------------------------------------------------------

print("\n" + "-" * 70)
print("FALSE POSITIVES BY REVIEW GROUP")
print("-" * 70)

group_counts = false_positives["review_group"].value_counts()

for group, count in group_counts.items():
    print(f"{group}: {count:,}")


# ------------------------------------------------------------
# FALSE POSITIVES BY STRONG MATCH
# ------------------------------------------------------------

print("\n" + "-" * 70)
print("FALSE POSITIVES BY MATCHED STRONG KEYWORD")
print("-" * 70)


def split_keywords(value):
    """
    Converts a semicolon-separated keyword field into a list.
    Handles missing values and empty strings.
    """
    if pd.isna(value):
        return []

    value = str(value).strip()

    if not value or value.lower() == "nan":
        return []

    return [
        keyword.strip()
        for keyword in value.split(";")
        if keyword.strip()
    ]


strong_counter = Counter()

for value in false_positives["matched_strong"]:
    keywords = split_keywords(value)

    for keyword in keywords:
        strong_counter[keyword] += 1

if strong_counter:
    for keyword, count in strong_counter.most_common():
        print(f"{keyword:<30} {count:>5}")
else:
    print("No strong-keyword matches found.")


# ------------------------------------------------------------
# FALSE POSITIVES BY WEAK MATCH
# ------------------------------------------------------------

print("\n" + "-" * 70)
print("FALSE POSITIVES BY MATCHED WEAK KEYWORD")
print("-" * 70)

weak_counter = Counter()

for value in false_positives["matched_weak"]:
    keywords = split_keywords(value)

    for keyword in keywords:
        weak_counter[keyword] += 1

if weak_counter:
    for keyword, count in weak_counter.most_common():
        print(f"{keyword:<30} {count:>5}")
else:
    print("No weak-keyword matches found.")


# ------------------------------------------------------------
# FALSE POSITIVES BY SECURITY CATEGORY
# ------------------------------------------------------------

print("\n" + "-" * 70)
print("FALSE POSITIVES BY SECURITY CATEGORY")
print("-" * 70)

category_counter = Counter()

for value in false_positives["security_categories"]:
    categories = split_keywords(value)

    for category in categories:
        category_counter[category] += 1

if category_counter:
    for category, count in category_counter.most_common():
        print(f"{category:<30} {count:>5}")
else:
    print("No security categories found.")


# ------------------------------------------------------------
# FALSE POSITIVES BY CANDIDATE SCORE
# ------------------------------------------------------------

print("\n" + "-" * 70)
print("FALSE POSITIVES BY CANDIDATE SCORE")
print("-" * 70)

score_counts = (
    false_positives["candidate_score"]
    .value_counts()
    .sort_index()
)

for score, count in score_counts.items():
    print(f"Score {score}: {count:,}")


# ------------------------------------------------------------
# FALSE POSITIVE RATE BY SCORE
# ------------------------------------------------------------

print("\n" + "-" * 70)
print("FALSE-POSITIVE RATE BY CANDIDATE SCORE")
print("-" * 70)

score_summary = (
    df[
        df["review_group"].isin(
            ["strong_candidate", "weak_candidate"]
        )
    ]
    .groupby("candidate_score")
    .agg(
        total_comments=("comment_id", "count"),
        false_positives=("manual_label", lambda values: (values == 0).sum())
    )
    .reset_index()
)

score_summary["false_positive_rate_percent"] = (
    score_summary["false_positives"]
    / score_summary["total_comments"]
    * 100
)

print(score_summary.to_string(index=False))


# ------------------------------------------------------------
# SAVE FALSE POSITIVE DATA
# ------------------------------------------------------------

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

false_positives.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 70)
print("FALSE-POSITIVE ANALYSIS COMPLETE")
print("=" * 70)

print("\nSaved false-positive comments to:")
print(OUTPUT_FILE)

print("\nUse this output to identify:")
print("  1. Overly broad security keywords")
print("  2. Categories that produce false positives")
print("  3. Candidate-score thresholds")
print("  4. Rules that should be refined")