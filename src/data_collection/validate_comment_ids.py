import pandas as pd

FILE_PATH = "data/raw/ghtorrent-2019-05-20.csv"
CHUNK_SIZE = 50_000

# Track whether each comment ID is associated
# with different values for important fields.
comment_info = {}

total_rows = 0
duplicate_rows = 0

print("Validating comment ID consistency...")
print("-" * 60)

for chunk_number, chunk in enumerate(
    pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE),
    start=1
):

    total_rows += len(chunk)

    # Keep only the columns we need
    relevant = chunk[
        [
            "comment_id",
            "comment",
            "repo",
            "pr_id",
            "c_id"
        ]
    ]

    for row in relevant.itertuples(index=False):

        comment_id = row.comment_id

        current_info = (
            row.comment,
            row.repo,
            row.pr_id,
            row.c_id
        )

        if comment_id in comment_info:

            duplicate_rows += 1

            if comment_info[comment_id] != current_info:
                # Store a special marker for inconsistent IDs
                comment_info[comment_id] = "INCONSISTENT"

        else:
            comment_info[comment_id] = current_info

    if chunk_number % 20 == 0:
        print(f"Processed {total_rows:,} rows...")


# Count inconsistent IDs
inconsistent_ids = sum(
    1
    for value in comment_info.values()
    if value == "INCONSISTENT"
)

print("\n")
print("=" * 60)
print("COMMENT ID VALIDATION")
print("=" * 60)

print(f"\nTotal rows:                {total_rows:,}")
print(f"Unique comment IDs:       {len(comment_info):,}")
print(f"Repeated comment rows:    {duplicate_rows:,}")

print(
    f"\nComment IDs with "
    f"inconsistent information: {inconsistent_ids:,}"
)

if inconsistent_ids == 0:
    print("\nRESULT:")
    print(
        "Every comment ID consistently maps to the same "
        "comment/repo/PR/commit."
    )
else:
    print("\nRESULT:")
    print(
        "Some comment IDs have different information "
        "across rows and require further investigation."
    )

print("\n" + "=" * 60)