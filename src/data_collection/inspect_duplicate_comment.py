import pandas as pd

FILE_PATH = "data/raw/ghtorrent-2019-05-20.csv"
CHUNK_SIZE = 50_000

# We will find the first comment ID that appears more than once
found_comment_id = None

print("Searching for a duplicated comment ID...")
print("-" * 60)

for chunk_number, chunk in enumerate(
    pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE),
    start=1
):

    duplicate_ids = chunk.loc[
        chunk["comment_id"].duplicated(keep=False),
        "comment_id"
    ]

    if not duplicate_ids.empty:
        found_comment_id = duplicate_ids.iloc[0]
        break

    if chunk_number % 20 == 0:
        print(f"Processed {chunk_number * CHUNK_SIZE:,} rows...")


if found_comment_id is None:
    print("No duplicated comment ID found.")
    exit()


print("\nFound duplicated comment ID:")
print(found_comment_id)

print("\nSearching for all rows containing this comment ID...")
print("-" * 60)

matching_rows = []

for chunk in pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE):

    matches = chunk[
        chunk["comment_id"] == found_comment_id
    ]

    if not matches.empty:
        matching_rows.append(matches)


result = pd.concat(matching_rows, ignore_index=True)

print("\n" + "=" * 80)
print("DUPLICATE COMMENT INVESTIGATION")
print("=" * 80)

print(f"\nComment ID: {found_comment_id}")
print(f"Number of rows: {len(result)}")

print("\nFull rows:")
print(result.to_string(index=False))

print("\n" + "=" * 80)