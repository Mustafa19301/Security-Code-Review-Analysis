import pandas as pd

FILE_PATH = "data/raw/ghtorrent-2019-05-20.csv"
CHUNK_SIZE = 50_000

total_rows = 0

unique_comment_ids = set()
unique_pr_ids = set()
unique_commit_ids = set()

duplicate_comment_ids = 0

print("Investigating dataset structure...")
print("-" * 60)

for chunk_number, chunk in enumerate(
    pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE),
    start=1
):

    total_rows += len(chunk)

    # Count duplicate IDs within each chunk
    duplicate_comment_ids += chunk["comment_id"].duplicated().sum()

    # Store unique IDs
    unique_comment_ids.update(
        chunk["comment_id"].dropna().astype(str)
    )

    unique_pr_ids.update(
        chunk["pr_id"].dropna().astype(str)
    )

    unique_commit_ids.update(
        chunk["c_id"].dropna().astype(str)
    )

    if chunk_number % 20 == 0:
        print(
            f"Processed {total_rows:,} rows..."
        )


print("\n")
print("=" * 60)
print("STRUCTURE INVESTIGATION")
print("=" * 60)

print(f"\nTotal rows:              {total_rows:,}")

print(
    f"Unique comment IDs:      "
    f"{len(unique_comment_ids):,}"
)

print(
    f"Unique PR IDs:            "
    f"{len(unique_pr_ids):,}"
)

print(
    f"Unique commit IDs:        "
    f"{len(unique_commit_ids):,}"
)

print(
    f"Duplicate comment IDs "
    f"within chunks:           "
    f"{duplicate_comment_ids:,}"
)

print("\nAverage rows per unique comment:")
print(
    f"{total_rows / len(unique_comment_ids):.2f}"
)

print("\nAverage rows per unique PR:")
print(
    f"{total_rows / len(unique_pr_ids):.2f}"
)

print("\nAverage rows per unique commit:")
print(
    f"{total_rows / len(unique_commit_ids):.2f}"
)

print("\n" + "=" * 60)