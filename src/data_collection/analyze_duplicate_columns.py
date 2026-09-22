import pandas as pd

FILE_PATH = "data/raw/ghtorrent-2019-05-20.csv"
CHUNK_SIZE = 50_000

# ------------------------------------------------------------
# PASS 1
# Find which comment IDs are duplicated
# ------------------------------------------------------------

print("=" * 70)
print("ANALYZING DUPLICATED COMMENT IDs")
print("=" * 70)

comment_counts = {}

total_rows = 0

print("\nPass 1: Counting rows for each comment ID...")
print("-" * 70)

for chunk_number, chunk in enumerate(
    pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE),
    start=1
):

    total_rows += len(chunk)

    counts = chunk["comment_id"].value_counts()

    for comment_id, count in counts.items():

        if comment_id in comment_counts:
            comment_counts[comment_id] += count
        else:
            comment_counts[comment_id] = count

    if chunk_number % 20 == 0:
        print(f"Processed {total_rows:,} rows...")

print("\nPass 1 complete.")

# ------------------------------------------------------------
# Find duplicated comment IDs
# ------------------------------------------------------------

duplicated_ids = {
    comment_id
    for comment_id, count in comment_counts.items()
    if count > 1
}

print(f"\nTotal rows:              {total_rows:,}")
print(f"Unique comment IDs:      {len(comment_counts):,}")
print(f"Duplicated comment IDs:  {len(duplicated_ids):,}")

# ------------------------------------------------------------
# PASS 2
# Analyze which columns vary
# ------------------------------------------------------------

print("\nPass 2: Analyzing duplicated comment IDs...")
print("-" * 70)

# For every duplicated comment ID, remember the first
# value encountered for each column.

first_values = {}

# Count how many comment IDs have differences
# in each column.

different_actor_login = set()
different_actor_id = set()
different_comment = set()
different_repo = set()
different_language = set()
different_author_login = set()
different_author_id = set()
different_pr_id = set()
different_c_id = set()
different_commit_date = set()

processed_rows = 0

for chunk_number, chunk in enumerate(
    pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE),
    start=1
):

    processed_rows += len(chunk)

    matching = chunk[
        chunk["comment_id"].isin(duplicated_ids)
    ]

    for row in matching.itertuples(index=False):

        comment_id = row.comment_id

        current_values = (
            row.actor_login,
            row.actor_id,
            row.comment,
            row.repo,
            row.language,
            row.author_login,
            row.author_id,
            row.pr_id,
            row.c_id,
            row.commit_date
        )

        if comment_id not in first_values:

            first_values[comment_id] = current_values

        else:

            previous_values = first_values[comment_id]

            if previous_values[0] != current_values[0]:
                different_actor_login.add(comment_id)

            if previous_values[1] != current_values[1]:
                different_actor_id.add(comment_id)

            if previous_values[2] != current_values[2]:
                different_comment.add(comment_id)

            if previous_values[3] != current_values[3]:
                different_repo.add(comment_id)

            if previous_values[4] != current_values[4]:
                different_language.add(comment_id)

            if previous_values[5] != current_values[5]:
                different_author_login.add(comment_id)

            if previous_values[6] != current_values[6]:
                different_author_id.add(comment_id)

            if previous_values[7] != current_values[7]:
                different_pr_id.add(comment_id)

            if previous_values[8] != current_values[8]:
                different_c_id.add(comment_id)

            if previous_values[9] != current_values[9]:
                different_commit_date.add(comment_id)

    if chunk_number % 20 == 0:
        print(f"Analyzed {processed_rows:,} rows...")

print("\nPass 2 complete.")

# ------------------------------------------------------------
# RESULTS
# ------------------------------------------------------------

total_duplicated = len(duplicated_ids)

print("\n")
print("=" * 70)
print("DUPLICATE COLUMN ANALYSIS")
print("=" * 70)

print(
    f"\nDuplicated comment IDs: "
    f"{total_duplicated:,}"
)

print("\nColumn differences:")
print("-" * 70)

results = [
    ("actor_login", different_actor_login),
    ("actor_id", different_actor_id),
    ("comment", different_comment),
    ("repo", different_repo),
    ("language", different_language),
    ("author_login", different_author_login),
    ("author_id", different_author_id),
    ("pr_id", different_pr_id),
    ("c_id", different_c_id),
    ("commit_date", different_commit_date)
]

for column_name, ids in results:

    count = len(ids)

    percentage = (
        count / total_duplicated * 100
        if total_duplicated > 0
        else 0
    )

    print(
        f"{column_name:<20} "
        f"{count:>10,} "
        f"({percentage:6.2f}%)"
    )

# ------------------------------------------------------------
# DUPLICATION DISTRIBUTION
# ------------------------------------------------------------

print("\n")
print("=" * 70)
print("DUPLICATION DISTRIBUTION")
print("=" * 70)

counts_series = pd.Series(comment_counts)

print("\nRows per comment ID:")

print(
    f"Minimum:       {counts_series.min():,}"
)

print(
    f"Median:        {counts_series.median():,.0f}"
)

print(
    f"Mean:          {counts_series.mean():,.2f}"
)

print(
    f"Maximum:       {counts_series.max():,}"
)

print("\nPercentiles:")

for percentile in [25, 50, 75, 90, 95, 99]:

    value = counts_series.quantile(percentile / 100)

    print(
        f"{percentile:>3}th percentile: "
        f"{value:,.0f}"
    )

# ------------------------------------------------------------
# COMMON DUPLICATION SIZES
# ------------------------------------------------------------

print("\n")
print("Most common duplication counts:")
print("-" * 70)

frequency = counts_series.value_counts().head(15)

for rows_per_comment, number_of_comments in frequency.items():

    print(
        f"{rows_per_comment:>6} rows "
        f"-> {number_of_comments:>10,} comment IDs"
    )

print("\n")
print("=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)