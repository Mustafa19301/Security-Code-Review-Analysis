import pandas as pd
from pathlib import Path


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_DIR = (
    PROJECT_ROOT
    / "data/gerrit/couchbase_java_client/collected"
)

REVIEWS_FILE = DATA_DIR / "reviews.csv"
REVISIONS_FILE = DATA_DIR / "revisions.csv"
MESSAGES_FILE = DATA_DIR / "messages.csv"
PATCHES_FILE = DATA_DIR / "patches.csv"
ERRORS_FILE = DATA_DIR / "collection_errors.csv"


# =========================================================
# LOAD DATASETS
# =========================================================

reviews = pd.read_csv(REVIEWS_FILE)
revisions = pd.read_csv(REVISIONS_FILE)
messages = pd.read_csv(MESSAGES_FILE)
patches = pd.read_csv(PATCHES_FILE)
errors = pd.read_csv(ERRORS_FILE)


# =========================================================
# GENERAL SUMMARY
# =========================================================

print("=" * 65)
print("GERRIT DATASET QUALITY VALIDATION")
print("=" * 65)

print("\n1. DATASET SIZES")
print("-" * 65)

print("Reviews:", len(reviews))
print("Revisions:", len(revisions))
print("Messages:", len(messages))
print("Patch records:", len(patches))
print("Errors:", len(errors))


# =========================================================
# REVIEW VALIDATION
# =========================================================

print("\n2. REVIEW VALIDATION")
print("-" * 65)

print(
    "Duplicate review numbers:",
    reviews["review_number"].duplicated().sum()
)

print(
    "API failures:",
    (~reviews["api_success"].astype(bool)).sum()
)

print("\nReview status distribution:")
print(reviews["status"].value_counts(dropna=False))


# =========================================================
# REVISION VALIDATION
# =========================================================

print("\n3. REVISION VALIDATION")
print("-" * 65)

print(
    "Duplicate review/revision pairs:",
    revisions.duplicated(
        subset=["review_number", "revision_number"]
    ).sum()
)

print(
    "Git fetch failures:",
    (~revisions["git_fetch_success"].astype(bool)).sum()
)

print(
    "Comparison failures:",
    (~revisions["comparison_success"].astype(bool)).sum()
)

print("\nFirst revision comparisons:")
print(
    revisions[
        revisions["revision_number"] == 1
    ][
        [
            "review_number",
            "previous_revision",
            "changed_files",
            "insertions",
            "deletions",
            "comparison_success"
        ]
    ].to_string(index=False)
)


# =========================================================
# PATCH VALIDATION
# =========================================================

print("\n4. PATCH VALIDATION")
print("-" * 65)

print(
    "Missing file paths:",
    patches["file_path"].isna().sum()
)

print("\nChange type distribution:")
print(patches["change_type"].value_counts(dropna=False))

patch_totals = (
    patches.groupby("review_number")
    [["insertions", "deletions"]]
    .sum()
)

print("\nLargest reviews by patch-file count:")
print(
    patches.groupby("review_number")
    .size()
    .sort_values(ascending=False)
    .head(5)
)

# Verify that each patch belongs to a fetched revision.
revision_keys = set(
    zip(
        revisions.loc[
            revisions["git_fetch_success"].astype(bool),
            "review_number"
        ],
        revisions.loc[
            revisions["git_fetch_success"].astype(bool),
            "revision_number"
        ]
    )
)

patch_keys = set(
    zip(
        patches["review_number"],
        patches["revision_number"]
    )
)

print(
    "\nPatch records without a fetched revision:",
    len(patch_keys - revision_keys)
)

# Separate successful comparisons with actual file changes
# from successful comparisons with zero changed files.

successful_revisions = revisions[
    revisions["comparison_success"].astype(bool)
]

revisions_with_changes = successful_revisions[
    successful_revisions["changed_files"] > 0
]

zero_change_revisions = successful_revisions[
    successful_revisions["changed_files"] == 0
]

revisions_with_changes_keys = set(
    zip(
        revisions_with_changes["review_number"],
        revisions_with_changes["revision_number"]
    )
)

zero_change_keys = set(
    zip(
        zero_change_revisions["review_number"],
        zero_change_revisions["revision_number"]
    )
)

print(
    "Successful revisions with actual changes:",
    len(revisions_with_changes)
)

print(
    "Successful zero-change revisions:",
    len(zero_change_revisions)
)

print(
    "Changed revisions without patch records:",
    len(revisions_with_changes_keys - patch_keys)
)

print(
    "Zero-change revisions without patch records:",
    len(zero_change_keys - patch_keys)
)


# =========================================================
# MESSAGE VALIDATION
# =========================================================

print("\n5. MESSAGE VALIDATION")
print("-" * 65)

print(
    "Duplicate message IDs:",
    messages["message_id"].duplicated().sum()
)

print(
    "Messages without revision attribution:",
    messages["revision_number"].isna().sum()
)

print("\nMessages per review:")
print(
    messages.groupby("review_number")
    .size()
    .sort_values(ascending=False)
)


# =========================================================
# ERROR SUMMARY
# =========================================================

print("\n6. COLLECTION ERRORS")
print("-" * 65)

if errors.empty:
    print("No collection errors recorded.")
else:
    print(errors.to_string(index=False))


# =========================================================
# FINAL CHECK
# =========================================================

print("\n" + "=" * 65)
print("VALIDATION FINISHED")
print("=" * 65)