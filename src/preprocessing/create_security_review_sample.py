import os
import pandas as pd


# ------------------------------------------------------------
# FILE PATHS
# ------------------------------------------------------------

INPUT_FILE = "data/processed/security_candidates.csv"
OUTPUT_FILE = "data/processed/security_review_sample.csv"


# ------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------

# Number of comments from each group
STRONG_SAMPLE_SIZE = 100
WEAK_SAMPLE_SIZE = 100
NON_CANDIDATE_SAMPLE_SIZE = 100

RANDOM_SEED = 42


# ------------------------------------------------------------
# LOAD SECURITY CANDIDATES
# ------------------------------------------------------------

print("=" * 70)
print("CREATING SECURITY MANUAL-REVIEW SAMPLE")
print("=" * 70)

print("\nLoading security_candidates.csv...")

candidates = pd.read_csv(INPUT_FILE)

print(f"Loaded {len(candidates):,} candidate comments.")


# ------------------------------------------------------------
# VALIDATE REQUIRED COLUMNS
# ------------------------------------------------------------

required_columns = [
    "comment_id",
    "comment",
    "repo",
    "language",
    "pr_id",
    "c_id",
    "matched_strong",
    "matched_weak",
    "security_categories",
    "candidate_score",
    "indicator_strength",
]

missing_columns = [
    column for column in required_columns
    if column not in candidates.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


# ------------------------------------------------------------
# SPLIT STRONG AND WEAK CANDIDATES
# ------------------------------------------------------------

strong_candidates = candidates[
    candidates["indicator_strength"].astype(str).str.lower() == "strong"
].copy()

weak_candidates = candidates[
    candidates["indicator_strength"].astype(str).str.lower() == "weak"
].copy()


print(f"\nStrong candidates available: {len(strong_candidates):,}")
print(f"Weak candidates available:   {len(weak_candidates):,}")


# ------------------------------------------------------------
# SAMPLE STRONG AND WEAK CANDIDATES
# ------------------------------------------------------------

strong_sample_size = min(
    STRONG_SAMPLE_SIZE,
    len(strong_candidates)
)

weak_sample_size = min(
    WEAK_SAMPLE_SIZE,
    len(weak_candidates)
)

strong_sample = strong_candidates.sample(
    n=strong_sample_size,
    random_state=RANDOM_SEED
).copy()

weak_sample = weak_candidates.sample(
    n=weak_sample_size,
    random_state=RANDOM_SEED
).copy()


strong_sample["review_group"] = "strong_candidate"
weak_sample["review_group"] = "weak_candidate"


# ------------------------------------------------------------
# LOAD A RANDOM SAMPLE OF NON-CANDIDATE COMMENTS
# ------------------------------------------------------------

print("\nLoading a random sample of non-candidate comments...")

# This reads the large unique-comments file in chunks.
# It does not load the entire 732 MB file into memory.

unique_comments_file = "data/processed/unique_comments.csv"

non_candidate_parts = []

for chunk in pd.read_csv(
    unique_comments_file,
    chunksize=50_000,
    low_memory=False
):
    # Remove comments that already appear in security_candidates.csv
    remaining = chunk[
        ~chunk["comment_id"].isin(candidates["comment_id"])
    ].copy()

    if not remaining.empty:
        non_candidate_parts.append(remaining)

    if sum(len(part) for part in non_candidate_parts) >= 5_000:
        break


if not non_candidate_parts:
    raise ValueError(
        "Could not find any non-candidate comments."
    )

non_candidates = pd.concat(
    non_candidate_parts,
    ignore_index=True
)

print(
    f"Collected {len(non_candidates):,} possible non-candidate comments."
)


# ------------------------------------------------------------
# SAMPLE NON-CANDIDATES
# ------------------------------------------------------------

non_candidate_sample_size = min(
    NON_CANDIDATE_SAMPLE_SIZE,
    len(non_candidates)
)

non_candidate_sample = non_candidates.sample(
    n=non_candidate_sample_size,
    random_state=RANDOM_SEED
).copy()

non_candidate_sample["matched_strong"] = ""
non_candidate_sample["matched_weak"] = ""
non_candidate_sample["security_categories"] = ""
non_candidate_sample["candidate_score"] = 0
non_candidate_sample["indicator_strength"] = "none"
non_candidate_sample["review_group"] = "non_candidate"


# ------------------------------------------------------------
# ADD MANUAL-REVIEW COLUMNS
# ------------------------------------------------------------

review_sample = pd.concat(
    [
        strong_sample,
        weak_sample,
        non_candidate_sample,
    ],
    ignore_index=True
)

review_sample["manual_label"] = ""
review_sample["review_notes"] = ""


# ------------------------------------------------------------
# SHUFFLE SAMPLE
# ------------------------------------------------------------

review_sample = review_sample.sample(
    frac=1,
    random_state=RANDOM_SEED
).reset_index(drop=True)


# ------------------------------------------------------------
# SAVE OUTPUT
# ------------------------------------------------------------

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

review_sample.to_csv(
    OUTPUT_FILE,
    index=False
)


# ------------------------------------------------------------
# DISPLAY RESULTS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("REVIEW SAMPLE CREATED")
print("=" * 70)

print(f"Total review comments: {len(review_sample):,}")
print(f"Strong candidates:     {len(strong_sample):,}")
print(f"Weak candidates:       {len(weak_sample):,}")
print(f"Non-candidates:        {len(non_candidate_sample):,}")

print(f"\nSaved to:")
print(OUTPUT_FILE)

print("\nNext step:")
print("Open the CSV and manually fill in:")
print("  manual_label")
print("  review_notes")

print("\nSuggested labels:")
print("  1 = Clearly security-related")
print("  2 = Possibly security-related")
print("  0 = Not security-related")

print("\n" + "=" * 70)