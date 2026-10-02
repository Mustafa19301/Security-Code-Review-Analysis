import os
import pandas as pd

FILE_PATH = "data/processed/unique_comments.csv"
CHUNK_SIZE = 50_000

if not os.path.exists(FILE_PATH):
    print("ERROR: File not found:")
    print(FILE_PATH)
    raise SystemExit

print("=" * 70)
print("UNIQUE COMMENTS DATASET PROFILE")
print("=" * 70)

total_rows = 0
unique_comment_ids = set()
unique_pr_ids = set()
unique_commit_ids = set()

language_counts = {}
missing_values = {}
comment_lengths = []

print("\nReading processed dataset...")
print("-" * 70)

for chunk_number, chunk in enumerate(
    pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE),
    start=1
):

    total_rows += len(chunk)

    unique_comment_ids.update(
        chunk["comment_id"].dropna().astype(str)
    )

    unique_pr_ids.update(
        chunk["pr_id"].dropna().astype(str)
    )

    unique_commit_ids.update(
        chunk["c_id"].dropna().astype(str)
    )

    # Count languages
    language_counts.update(
        chunk["language"].fillna("Unknown").value_counts().to_dict()
    )

    # Count missing values
    for column in chunk.columns:
        missing_values[column] = (
            missing_values.get(column, 0)
            + int(chunk[column].isna().sum())
        )

    # Comment length statistics
    lengths = (
        chunk["comment"]
        .fillna("")
        .astype(str)
        .str.len()
        .tolist()
    )

    comment_lengths.extend(lengths)

    if chunk_number % 20 == 0:
        print(f"Processed {total_rows:,} rows...")

print("\n")
print("=" * 70)
print("PROFILE RESULTS")
print("=" * 70)

print(f"\nTotal rows:              {total_rows:,}")
print(f"Unique comment IDs:      {len(unique_comment_ids):,}")
print(f"Unique PR IDs:           {len(unique_pr_ids):,}")
print(f"Unique commit IDs:       {len(unique_commit_ids):,}")

print("\n")
print("LANGUAGE DISTRIBUTION")
print("")

language_series = pd.Series(language_counts).sort_values(
    ascending=False
)

for language, count in language_series.items():
    percentage = count / total_rows * 100

    print(
        f"{str(language):<20} "
        f"{count:>12,} "
        f"({percentage:6.2f}%)"
    )

print("\n")
print("MISSING VALUES")

for column, count in missing_values.items():
    percentage = count / total_rows * 100

    print(
        f"{column:<20} "
        f"{count:>12,} "
        f"({percentage:6.2f}%)"
    )

print("\n")
print("COMMENT LENGTHS")

length_series = pd.Series(comment_lengths)

print(f"Average length:         {length_series.mean():.2f}")
print(f"Median length:          {length_series.median():.2f}")
print(f"Minimum length:         {length_series.min():,}")
print(f"Maximum length:         {length_series.max():,}")

print("\n" + "=" * 70)
print("PROFILE COMPLETE")
print("=" * 70)