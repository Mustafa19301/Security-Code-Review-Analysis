import pandas as pd
from collections import Counter

FILE_PATH = "data/raw/ghtorrent-2019-05-20.csv"
CHUNK_SIZE = 50_000

# Counters
total_rows = 0
unique_comments = set()
unique_repos = set()
unique_prs = set()
unique_commits = set()

language_counts = Counter()

missing_counts = Counter()

duplicate_comment_count = 0

comment_lengths = []

min_date = None
max_date = None

print("Starting full dataset profiling...")
print(f"Chunk size: {CHUNK_SIZE:,}")
print("-" * 60)

for chunk_number, chunk in enumerate(
    pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE),
    start=1
):

    total_rows += len(chunk)

    # Unique identifiers
    unique_comments.update(
        chunk["comment_id"].dropna().astype(str)
    )

    unique_repos.update(
        chunk["repo"].dropna().astype(str)
    )

    unique_prs.update(
        chunk["pr_id"].dropna().astype(str)
    )

    unique_commits.update(
        chunk["c_id"].dropna().astype(str)
    )

    # Language distribution
    language_counts.update(
        chunk["language"].fillna("Unknown").astype(str)
    )

    # Missing values
    for column in chunk.columns:
        missing_counts[column] += chunk[column].isna().sum()

    # Duplicate comments within the chunk
    duplicate_comment_count += chunk["comment"].duplicated().sum()

    # Comment lengths
    lengths = chunk["comment"].fillna("").astype(str).str.len()
    comment_lengths.extend(lengths.tolist())

    # Dates
    dates = pd.to_datetime(
        chunk["commit_date"],
        errors="coerce",
        utc=True
    )

    chunk_min_date = dates.min()
    chunk_max_date = dates.max()

    if pd.notna(chunk_min_date):
        if min_date is None or chunk_min_date < min_date:
            min_date = chunk_min_date

    if pd.notna(chunk_max_date):
        if max_date is None or chunk_max_date > max_date:
            max_date = chunk_max_date

    # Progress
    print(
        f"Processed chunk {chunk_number:,} "
        f"| {total_rows:,} rows"
    )

print("\n")
print("=" * 60)
print("DATASET PROFILE")
print("=" * 60)

print(f"\nTotal rows:              {total_rows:,}")
print(f"Unique comments:         {len(unique_comments):,}")
print(f"Unique repositories:     {len(unique_repos):,}")
print(f"Unique pull requests:    {len(unique_prs):,}")
print(f"Unique commits:          {len(unique_commits):,}")

print("\n" + "-" * 60)
print("LANGUAGE DISTRIBUTION")
print("-" * 60)

for language, count in language_counts.most_common(30):
    percentage = (count / total_rows) * 100
    print(f"{language:<20} {count:>12,}  ({percentage:6.2f}%)")

print("\n" + "-" * 60)
print("MISSING VALUES")
print("-" * 60)

for column in missing_counts:
    count = missing_counts[column]
    percentage = (count / total_rows) * 100
    print(
        f"{column:<20} "
        f"{count:>12,}  "
        f"({percentage:6.2f}%)"
    )

print("\n" + "-" * 60)
print("COMMENT STATISTICS")
print("-" * 60)

comment_series = pd.Series(comment_lengths)

print(f"Average length:         {comment_series.mean():,.2f} characters")
print(f"Median length:          {comment_series.median():,.2f} characters")
print(f"Minimum length:         {comment_series.min():,} characters")
print(f"Maximum length:         {comment_series.max():,} characters")

print("\n" + "-" * 60)
print("DATES")
print("-" * 60)

print(f"Earliest commit date:   {min_date}")
print(f"Latest commit date:     {max_date}")

print("\n" + "-" * 60)
print("DUPLICATES")
print("-" * 60)

print(
    f"Duplicate comments within chunks: "
    f"{duplicate_comment_count:,}"
)

print("\n" + "=" * 60)
print("PROFILING COMPLETE")
print("=" * 60)