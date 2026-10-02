import pandas as pd

FILE_PATH = "data/processed/unique_comments.csv"

CHUNK_SIZE = 100_000

print("=" * 70)
print("PROCESSED DATASET QUALITY CHECK")
print("=" * 70)

total_rows = 0

unique_comment_ids = set()

repo_counts = {}
language_counts = {}

missing_comments = 0
missing_repos = 0
missing_languages = 0
missing_pr_ids = 0
missing_commit_ids = 0

comment_length_total = 0
comment_length_min = None
comment_length_max = None

print("\nReading processed dataset...")
print("-" * 70)

for chunk_number, chunk in enumerate(
    pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE),
    start=1
):

    total_rows += len(chunk)

    unique_comment_ids.update(
        chunk["comment_id"]
        .dropna()
        .astype(str)
    )

    missing_comments += chunk["comment"].isna().sum()
    missing_repos += chunk["repo"].isna().sum()
    missing_languages += chunk["language"].isna().sum()
    missing_pr_ids += chunk["pr_id"].isna().sum()
    missing_commit_ids += chunk["c_id"].isna().sum()

    repo_chunk = chunk["repo"].dropna()

    for repo in repo_chunk:
        repo_counts[repo] = repo_counts.get(repo, 0) + 1

    language_chunk = chunk["language"].dropna()

    for language in language_chunk:
        language_counts[language] = (
            language_counts.get(language, 0) + 1
        )

    lengths = (
        chunk["comment"]
        .fillna("")
        .astype(str)
        .str.len()
    )

    comment_length_total += lengths.sum()

    chunk_min = lengths.min()
    chunk_max = lengths.max()

    if comment_length_min is None:
        comment_length_min = chunk_min
    else:
        comment_length_min = min(
            comment_length_min,
            chunk_min
        )

    if comment_length_max is None:
        comment_length_max = chunk_max
    else:
        comment_length_max = max(
            comment_length_max,
            chunk_max
        )

    if chunk_number % 10 == 0:
        print(
            f"Processed {total_rows:,} rows..."
        )

print("\n")
print("=" * 70)
print("PROCESSED DATASET QUALITY RESULTS")
print("=" * 70)

print(
    f"\nTotal rows:              "
    f"{total_rows:,}"
)

print(
    f"Unique comment IDs:      "
    f"{len(unique_comment_ids):,}"
)

print(
    f"Duplicate comment IDs:   "
    f"{total_rows - len(unique_comment_ids):,}"
)


print("\n")
print("=" * 70)
print("MISSING VALUES")
print("=" * 70)

missing_values = {
    "comment": missing_comments,
    "repo": missing_repos,
    "language": missing_languages,
    "pr_id": missing_pr_ids,
    "c_id": missing_commit_ids
}

for column, count in missing_values.items():

    percentage = (
        count / total_rows * 100
        if total_rows > 0
        else 0
    )

    print(
        f"{column:<15}"
        f"{count:>10,}"
        f" ({percentage:6.2f}%)"
    )

print("\n")
print("=" * 70)
print("REPOSITORY DISTRIBUTION")
print("=" * 70)

print(
    f"\nUnique repositories: "
    f"{len(repo_counts):,}"
)

print("\nTop 20 repositories:")

sorted_repos = sorted(
    repo_counts.items(),
    key=lambda x: x[1],
    reverse=True
)

for repo, count in sorted_repos[:20]:

    percentage = count / total_rows * 100

    print(
        f"{repo:<40}"
        f"{count:>10,}"
        f" ({percentage:6.2f}%)"
    )

print("\n")
print("=" * 70)
print("LANGUAGE DISTRIBUTION")
print("=" * 70)

print(
    f"\nUnique languages: "
    f"{len(language_counts):,}"
)

print("\nTop languages:")

sorted_languages = sorted(
    language_counts.items(),
    key=lambda x: x[1],
    reverse=True
)

for language, count in sorted_languages:

    percentage = count / total_rows * 100

    print(
        f"{language:<25}"
        f"{count:>10,}"
        f" ({percentage:6.2f}%)"
    )

print("\n")
print("=" * 70)
print("COMMENT LENGTH")
print("=" * 70)

average_length = (
    comment_length_total / total_rows
    if total_rows > 0
    else 0
)

print(
    f"\nAverage comment length: "
    f"{average_length:.2f} characters"
)

print(
    f"Minimum comment length: "
    f"{comment_length_min}"
)

print(
    f"Maximum comment length: "
    f"{comment_length_max}"
)

print("\n")
print("=" * 70)
print("FINAL VALIDATION")
print("=" * 70)

if total_rows == len(unique_comment_ids):

    print(
        "\nPASS: Every row has a unique comment_id."
    )

else:

    print(
        "\nWARNING: Duplicate comment IDs still exist."
    )

if missing_pr_ids == 0:

    print(
        "PASS: No missing PR IDs."
    )

else:

    print(
        "WARNING: Missing PR IDs detected."
    )

if missing_commit_ids == 0:

    print(
        "PASS: No missing commit IDs."
    )

else:

    print(
        "WARNING: Missing commit IDs detected."
    )

print("\n")
print("=" * 70)
print("QUALITY CHECK COMPLETE")
print("=" * 70)