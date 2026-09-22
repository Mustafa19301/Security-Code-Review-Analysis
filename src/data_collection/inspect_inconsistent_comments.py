import pandas as pd

FILE_PATH = "data/raw/ghtorrent-2019-05-20.csv"
CHUNK_SIZE = 50_000

# Number of inconsistent comment IDs to inspect
MAX_IDS_TO_INSPECT = 10


# ============================================================
# PASS 1: Find inconsistent comment IDs
# ============================================================

print("=" * 70)
print("PASS 1: FINDING INCONSISTENT COMMENT IDs")
print("=" * 70)

comment_info = {}

total_rows = 0

for chunk_number, chunk in enumerate(
    pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE),
    start=1
):
    total_rows += len(chunk)

    for row in chunk.itertuples(index=False):

        comment_id = row.comment_id

        info = (
            row.comment,
            row.repo,
            row.language,
            row.pr_id,
            row.c_id
        )

        if comment_id not in comment_info:
            comment_info[comment_id] = info

        elif comment_info[comment_id] != info:
            # Mark this comment ID as inconsistent
            comment_info[comment_id] = None

    if chunk_number % 20 == 0:
        print(f"Processed {total_rows:,} rows...")


# Get the inconsistent IDs
inconsistent_ids = [
    comment_id
    for comment_id, info in comment_info.items()
    if info is None
]

print("\n" + "=" * 70)
print("INCONSISTENT COMMENT IDs FOUND")
print("=" * 70)

print(f"\nTotal inconsistent comment IDs: {len(inconsistent_ids):,}")

ids_to_inspect = inconsistent_ids[:MAX_IDS_TO_INSPECT]

print(
    f"Inspecting first {len(ids_to_inspect)} "
    f"inconsistent comment IDs..."
)

print("\nIDs:")
for comment_id in ids_to_inspect:
    print(f"  {comment_id}")


# ============================================================
# PASS 2: Collect all rows for selected IDs
# ============================================================

print("\n" + "=" * 70)
print("PASS 2: INSPECTING SELECTED COMMENT IDs")
print("=" * 70)

selected_rows = []

for chunk in pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE):

    matches = chunk[
        chunk["comment_id"].isin(ids_to_inspect)
    ]

    if not matches.empty:
        selected_rows.append(matches)


if selected_rows:

    result = pd.concat(
        selected_rows,
        ignore_index=True
    )

    # Sort so identical comment IDs are grouped together
    result = result.sort_values(
        by=[
            "comment_id",
            "pr_id",
            "c_id",
            "repo",
            "language"
        ]
    )

    # Print each comment ID separately
    for comment_id in ids_to_inspect:

        group = result[
            result["comment_id"] == comment_id
        ]

        if group.empty:
            continue

        print("\n")
        print("=" * 70)
        print(f"COMMENT ID: {comment_id}")
        print("=" * 70)

        print(f"Number of rows: {len(group):,}")

        print("\nUnique values:")
        print(
            f"  Comments:   {group['comment'].nunique(dropna=False):,}"
        )
        print(
            f"  Repos:      {group['repo'].nunique(dropna=False):,}"
        )
        print(
            f"  Languages:  {group['language'].nunique(dropna=False):,}"
        )
        print(
            f"  PR IDs:     {group['pr_id'].nunique(dropna=False):,}"
        )
        print(
            f"  Commit IDs: {group['c_id'].nunique(dropna=False):,}"
        )

        print("\nUnique repositories:")
        for value in group["repo"].drop_duplicates().tolist():
            print(f"  {value}")

        print("\nUnique languages:")
        for value in group["language"].drop_duplicates().tolist():
            print(f"  {value}")

        print("\nUnique PR IDs:")
        for value in group["pr_id"].drop_duplicates().tolist():
            print(f"  {value}")

        print("\nUnique commit IDs:")
        for value in group["c_id"].drop_duplicates().tolist():
            print(f"  {value}")

        print("\nComment text:")
        for value in group["comment"].drop_duplicates().tolist():
            print(f"  {value}")

        print("\nFirst 20 rows:")
        print(
            group[
                [
                    "actor_login",
                    "comment_id",
                    "comment",
                    "repo",
                    "language",
                    "author_login",
                    "pr_id",
                    "c_id",
                    "commit_date"
                ]
            ].head(20).to_string(index=False)
        )


else:
    print("\nNo matching rows were found.")


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)