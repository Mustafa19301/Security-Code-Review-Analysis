import pandas as pd

FILE_PATH = "data/raw/ghtorrent-2019-05-20.csv"
CHUNK_SIZE = 50_000

# Number of inconsistent comment IDs we want to inspect
MAX_IDS_TO_INSPECT = 10

# ------------------------------------------------------------
# PASS 1: Find comment IDs with inconsistent information
# ------------------------------------------------------------

inconsistent_ids = set()
comment_info = {}

print("=" * 60)
print("PASS 1: FINDING INCONSISTENT COMMENT IDs")
print("=" * 60)

total_rows = 0

for chunk_number, chunk in enumerate(
    pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE),
    start=1
):
    total_rows += len(chunk)

    for _, row in chunk.iterrows():

        comment_id = row["comment_id"]

        # Ignore missing comment IDs
        if pd.isna(comment_id):
            continue

        comment_id = int(comment_id)

        current_info = (
            row["comment"],
            row["repo"],
            row["language"],
            row["pr_id"],
            row["c_id"]
        )

        # First time seeing this comment ID
        if comment_id not in comment_info:

            comment_info[comment_id] = current_info

        # We have seen this comment ID before
        elif comment_info[comment_id] != current_info:

            inconsistent_ids.add(comment_id)

            # We only need a small sample for detailed inspection
            if len(inconsistent_ids) >= MAX_IDS_TO_INSPECT:
                break

    if len(inconsistent_ids) >= MAX_IDS_TO_INSPECT:
        break

    if chunk_number % 20 == 0:
        print(f"Processed {total_rows:,} rows...")


print("\n" + "=" * 60)
print("INCONSISTENT COMMENT IDs FOUND")
print("=" * 60)

for comment_id in sorted(inconsistent_ids):
    print(comment_id)

print(f"\nNumber selected for inspection: {len(inconsistent_ids)}")


# ------------------------------------------------------------
# PASS 2: Retrieve every row for those comment IDs
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("PASS 2: INSPECTING SELECTED COMMENT IDs")
print("=" * 60)

matching_rows = []

for chunk_number, chunk in enumerate(
    pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE),
    start=1
):

    matching = chunk[
        chunk["comment_id"].isin(inconsistent_ids)
    ]

    if not matching.empty:
        matching_rows.append(matching)

    if chunk_number % 20 == 0:
        print(f"Processed {chunk_number * CHUNK_SIZE:,} rows...")


if matching_rows:

    result = pd.concat(matching_rows, ignore_index=True)

    # Sort so that rows belonging to the same comment are together
    result = result.sort_values(
        by=["comment_id", "pr_id", "c_id"]
    )

    # --------------------------------------------------------
    # Print each inconsistent comment ID separately
    # --------------------------------------------------------

    for comment_id in sorted(inconsistent_ids):

        comment_rows = result[
            result["comment_id"] == comment_id
        ]

        print("\n")
        print("=" * 100)
        print(f"COMMENT ID: {comment_id}")
        print("=" * 100)

        print(f"Number of rows: {len(comment_rows)}")

        print("\nUnique comments:")
        print(comment_rows["comment"].drop_duplicates().to_string(index=False))

        print("\nUnique repositories:")
        print(
            comment_rows["repo"]
            .drop_duplicates()
            .to_string(index=False)
        )

        print("\nUnique languages:")
        print(
            comment_rows["language"]
            .drop_duplicates()
            .to_string(index=False)
        )

        print("\nUnique PR IDs:")
        print(
            comment_rows["pr_id"]
            .drop_duplicates()
            .to_string(index=False)
        )

        print("\nUnique commit IDs:")
        print(
            comment_rows["c_id"]
            .drop_duplicates()
            .to_string(index=False)
        )

        print("\nUnique author logins:")
        print(
            comment_rows["author_login"]
            .drop_duplicates()
            .to_string(index=False)
        )

        print("\nUnique actor logins:")
        print(
            comment_rows["actor_login"]
            .drop_duplicates()
            .to_string(index=False)
        )

        print("\nUnique commit dates:")
        print(
            comment_rows["commit_date"]
            .drop_duplicates()
            .to_string(index=False)
        )

        print("\nFull rows:")
        print(
            comment_rows.to_string(index=False)
        )


print("\n")
print("=" * 100)
print("INVESTIGATION COMPLETE")
print("=" * 100)