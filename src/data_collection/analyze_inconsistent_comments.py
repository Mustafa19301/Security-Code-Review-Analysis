import pandas as pd
from collections import defaultdict

FILE_PATH = "data/raw/ghtorrent-2019-05-20.csv"
CHUNK_SIZE = 50_000

print("=" * 70)
print("ANALYZING INCONSISTENT COMMENT IDs")
print("=" * 70)

# ------------------------------------------------------------
# PASS 1: Find comment IDs with inconsistent core information
# ------------------------------------------------------------

comment_info = {}

inconsistent_ids = set()

total_rows = 0

print("\nPass 1: Finding inconsistent comment IDs...")
print("-" * 70)

for chunk_number, chunk in enumerate(
    pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE),
    start=1
):

    total_rows += len(chunk)

    for row in chunk.itertuples(index=False):

        comment_id = row.comment_id

        current_info = (
            row.comment,
            row.repo,
            row.language,
            row.pr_id,
            row.c_id
        )

        if comment_id not in comment_info:
            comment_info[comment_id] = current_info

        elif comment_info[comment_id] != current_info:
            inconsistent_ids.add(comment_id)

    if chunk_number % 20 == 0:
        print(f"Processed {total_rows:,} rows...")

print("\nPass 1 complete.")

print(f"\nTotal rows:              {total_rows:,}")
print(f"Inconsistent comment IDs: {len(inconsistent_ids):,}")

# ------------------------------------------------------------
# PASS 2: Analyze every inconsistent comment ID
# ------------------------------------------------------------

print("\nPass 2: Analyzing inconsistent comments...")
print("-" * 70)

# Store unique values for each field
analysis = defaultdict(
    lambda: {
        "rows": 0,
        "comments": set(),
        "repos": set(),
        "languages": set(),
        "pr_ids": set(),
        "commit_ids": set()
    }
)

for chunk_number, chunk in enumerate(
    pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE),
    start=1
):

    matching = chunk[
        chunk["comment_id"].isin(inconsistent_ids)
    ]

    for row in matching.itertuples(index=False):

        comment_id = row.comment_id

        analysis[comment_id]["rows"] += 1

        analysis[comment_id]["comments"].add(
            str(row.comment)
        )

        analysis[comment_id]["repos"].add(
            str(row.repo)
        )

        analysis[comment_id]["languages"].add(
            str(row.language)
        )

        analysis[comment_id]["pr_ids"].add(
            str(row.pr_id)
        )

        analysis[comment_id]["commit_ids"].add(
            str(row.c_id)
        )

    if chunk_number % 20 == 0:
        print(f"Analyzed {total_rows:,} rows...")

print("\nPass 2 complete.")

# ------------------------------------------------------------
# CLASSIFY INCONSISTENCIES
# ------------------------------------------------------------

categories = {
    "Only language differs": 0,
    "Only repository differs": 0,
    "Only comment differs": 0,
    "Only PR ID differs": 0,
    "Only commit ID differs": 0,
    "Multiple fields differ": 0
}

for comment_id, info in analysis.items():

    differences = []

    if len(info["comments"]) > 1:
        differences.append("comment")

    if len(info["repos"]) > 1:
        differences.append("repo")

    if len(info["languages"]) > 1:
        differences.append("language")

    if len(info["pr_ids"]) > 1:
        differences.append("pr_id")

    if len(info["commit_ids"]) > 1:
        differences.append("c_id")

    if differences == ["language"]:
        categories["Only language differs"] += 1

    elif differences == ["repo"]:
        categories["Only repository differs"] += 1

    elif differences == ["comment"]:
        categories["Only comment differs"] += 1

    elif differences == ["pr_id"]:
        categories["Only PR ID differs"] += 1

    elif differences == ["c_id"]:
        categories["Only commit ID differs"] += 1

    else:
        categories["Multiple fields differ"] += 1

# ------------------------------------------------------------
# PRINT RESULTS
# ------------------------------------------------------------

print("\n")
print("=" * 70)
print("INCONSISTENCY ANALYSIS RESULTS")
print("=" * 70)

print(
    f"\nTotal inconsistent comment IDs: "
    f"{len(analysis):,}"
)

print("\nCategories:")
print("-" * 70)

for category, count in categories.items():

    percentage = (
        count / len(analysis) * 100
        if len(analysis) > 0
        else 0
    )

    print(
        f"{category:<30} "
        f"{count:>8,} "
        f"({percentage:6.2f}%)"
    )

# ------------------------------------------------------------
# SUMMARY OF FIELD DIFFERENCES
# ------------------------------------------------------------

field_counts = {
    "Comment": 0,
    "Repository": 0,
    "Language": 0,
    "PR ID": 0,
    "Commit ID": 0
}

for comment_id, info in analysis.items():

    if len(info["comments"]) > 1:
        field_counts["Comment"] += 1

    if len(info["repos"]) > 1:
        field_counts["Repository"] += 1

    if len(info["languages"]) > 1:
        field_counts["Language"] += 1

    if len(info["pr_ids"]) > 1:
        field_counts["PR ID"] += 1

    if len(info["commit_ids"]) > 1:
        field_counts["Commit ID"] += 1

print("\n")
print("=" * 70)
print("FIELD-LEVEL DIFFERENCES")
print("=" * 70)

for field, count in field_counts.items():

    percentage = (
        count / len(analysis) * 100
        if len(analysis) > 0
        else 0
    )

    print(
        f"{field:<20} "
        f"{count:>8,} "
        f"({percentage:6.2f}%)"
    )

# ------------------------------------------------------------
# SHOW EXAMPLES
# ------------------------------------------------------------

print("\n")
print("=" * 70)
print("EXAMPLE INCONSISTENT COMMENT IDs")
print("=" * 70)

example_count = 0

for comment_id, info in analysis.items():

    print("\n" + "-" * 70)
    print(f"Comment ID: {comment_id}")
    print(f"Rows:       {info['rows']}")

    print(f"\nComments ({len(info['comments'])}):")

    for value in list(info["comments"])[:3]:
        print(f"  {value[:200]}")

    if len(info["comments"]) > 3:
        print("  ...")

    print(f"\nRepositories ({len(info['repos'])}):")

    for value in list(info["repos"])[:10]:
        print(f"  {value}")

    if len(info["repos"]) > 10:
        print("  ...")

    print(f"\nLanguages ({len(info['languages'])}):")

    for value in list(info["languages"])[:10]:
        print(f"  {value}")

    if len(info["languages"]) > 10:
        print("  ...")

    print(f"\nPR IDs ({len(info['pr_ids'])}):")

    for value in list(info["pr_ids"])[:10]:
        print(f"  {value}")

    print(f"\nCommit IDs ({len(info['commit_ids'])}):")

    for value in list(info["commit_ids"])[:10]:
        print(f"  {value}")

    example_count += 1

    if example_count >= 10:
        break

print("\n")
print("=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)