import pandas as pd
from collections import Counter, defaultdict
import os

# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = "data/raw/ghtorrent-2019-05-20.csv"
OUTPUT_FILE = "data/processed/unique_comments.csv"

CHUNK_SIZE = 50_000


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs("data/processed", exist_ok=True)


# ============================================================
# DATA STRUCTURES
# ============================================================

# For each comment_id, store:
#
# comment
# pr_id
# c_id
#
# These should remain consistent based on our investigation.

comment_text = {}
comment_pr = {}
comment_commit = {}

# Count how frequently each repository and language
# occurs for each comment_id.
#
# We will use the most common value as the canonical value.

repo_counts = defaultdict(Counter)
language_counts = defaultdict(Counter)


# ============================================================
# PASS 1
# ============================================================

print("=" * 70)
print("CREATING UNIQUE COMMENT DATASET")
print("=" * 70)

print("\nInput file:")
print(INPUT_FILE)

print("\nPass 1: Reading raw dataset...")
print("-" * 70)

total_rows = 0

for chunk_number, chunk in enumerate(
    pd.read_csv(INPUT_FILE, chunksize=CHUNK_SIZE),
    start=1
):

    total_rows += len(chunk)

    for row in chunk.itertuples(index=False):

        comment_id = row.comment_id

        # ----------------------------------------------------
        # Store comment text
        # ----------------------------------------------------

        if comment_id not in comment_text:

            comment_text[comment_id] = row.comment

        # ----------------------------------------------------
        # Store PR ID
        # ----------------------------------------------------

        if comment_id not in comment_pr:

            comment_pr[comment_id] = row.pr_id

        # ----------------------------------------------------
        # Store commit ID
        # ----------------------------------------------------

        if comment_id not in comment_commit:

            comment_commit[comment_id] = row.c_id

        # ----------------------------------------------------
        # Count repositories
        # ----------------------------------------------------

        if pd.notna(row.repo):

            repo_counts[comment_id][str(row.repo)] += 1

        # ----------------------------------------------------
        # Count languages
        # ----------------------------------------------------

        if pd.notna(row.language):

            language_counts[comment_id][str(row.language)] += 1

    if chunk_number % 20 == 0:

        print(
            f"Processed {total_rows:,} rows..."
        )


print("\nPass 1 complete.")

print(
    f"\nTotal raw rows processed: "
    f"{total_rows:,}"
)

print(
    f"Unique comment IDs found: "
    f"{len(comment_text):,}"
)


# ============================================================
# CREATE UNIQUE DATASET
# ============================================================

print("\nCreating canonical records...")
print("-" * 70)

records = []

for comment_id in comment_text:

    # --------------------------------------------------------
    # Determine canonical repository
    # --------------------------------------------------------

    if repo_counts[comment_id]:

        canonical_repo = repo_counts[comment_id].most_common(1)[0][0]

    else:

        canonical_repo = None

    # --------------------------------------------------------
    # Determine canonical language
    # --------------------------------------------------------

    if language_counts[comment_id]:

        canonical_language = (
            language_counts[comment_id]
            .most_common(1)[0][0]
        )

    else:

        canonical_language = None

    # --------------------------------------------------------
    # Create record
    # --------------------------------------------------------

    records.append(
        {
            "comment_id": comment_id,
            "comment": comment_text[comment_id],
            "repo": canonical_repo,
            "language": canonical_language,
            "pr_id": comment_pr[comment_id],
            "c_id": comment_commit[comment_id]
        }
    )


# ============================================================
# CREATE DATAFRAME
# ============================================================

df = pd.DataFrame(records)


# ============================================================
# SAVE DATASET
# ============================================================

print("\nSaving processed dataset...")
print("-" * 70)

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n")
print("=" * 70)
print("UNIQUE COMMENT DATASET CREATED")
print("=" * 70)

print(
    f"\nRaw rows:              {total_rows:,}"
)

print(
    f"Unique comments:      {len(df):,}"
)

print(
    f"Reduction:             "
    f"{(1 - len(df) / total_rows) * 100:.2f}%"
)

print(
    f"\nOutput file:"
)

print(
    OUTPUT_FILE
)

print(
    f"\nOutput shape:"
)

print(
    df.shape
)

print(
    "\nColumns:"
)

for column in df.columns:

    print(
        f"  - {column}"
    )


# ============================================================
# MISSING VALUES
# ============================================================

print("\n")
print("=" * 70)
print("MISSING VALUES")
print("=" * 70)

for column in df.columns:

    missing = df[column].isna().sum()

    percentage = (
        missing / len(df) * 100
        if len(df) > 0
        else 0
    )

    print(
        f"{column:<15}"
        f"{missing:>10,}"
        f" ({percentage:6.2f}%)"
    )


# ============================================================
# SAMPLE
# ============================================================

print("\n")
print("=" * 70)
print("FIRST 10 RECORDS")
print("=" * 70)

print(
    df.head(10).to_string(index=False)
)


print("\n")
print("=" * 70)
print("PROCESSING COMPLETE")
print("=" * 70)