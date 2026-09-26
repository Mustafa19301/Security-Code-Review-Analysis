import os
import pandas as pd


INPUT_FILE = "data/processed/security_candidates_v2.csv"
OUTPUT_FILE = "data/processed/security_review_sample_v2.csv"

SAMPLE_SIZE_PER_GROUP = 100
RANDOM_STATE = 42


def main():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Input file was not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print(f"Total candidates available: {len(df):,}")

    required_columns = {
        "comment_id",
        "comment",
        "repo",
        "language",
        "pr_id",
        "c_id",
        "candidate_type",
        "candidate_score",
        "security_categories",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    review_parts = []

    # --------------------------------------------------
    # 1. Sample high-confidence candidates
    # --------------------------------------------------

    high_confidence = df[
        df["candidate_type"] == "high_confidence"
    ].sample(
        n=min(
            SAMPLE_SIZE_PER_GROUP,
            len(df[df["candidate_type"] == "high_confidence"]),
        ),
        random_state=RANDOM_STATE,
    ).copy()

    high_confidence["review_group"] = "high_confidence"

    review_parts.append(high_confidence)

    # --------------------------------------------------
    # 2. Sample contextual candidates
    # --------------------------------------------------

    contextual = df[
        df["candidate_type"] == "contextual"
    ].sample(
        n=min(
            SAMPLE_SIZE_PER_GROUP,
            len(df[df["candidate_type"] == "contextual"]),
        ),
        random_state=RANDOM_STATE,
    ).copy()

    contextual["review_group"] = "contextual"

    review_parts.append(contextual)

    # --------------------------------------------------
    # 3. Sample weak candidates
    # --------------------------------------------------

    weak = df[
        df["candidate_type"] == "weak"
    ].sample(
        n=min(
            SAMPLE_SIZE_PER_GROUP,
            len(df[df["candidate_type"] == "weak"]),
        ),
        random_state=RANDOM_STATE,
    ).copy()

    weak["review_group"] = "weak"

    review_parts.append(weak)

    # --------------------------------------------------
    # 4. Combine and shuffle
    # --------------------------------------------------

    review_sample = pd.concat(
        review_parts,
        ignore_index=True,
    )

    review_sample = review_sample.sample(
        frac=1,
        random_state=RANDOM_STATE,
    ).reset_index(drop=True)

    # --------------------------------------------------
    # 5. Add manual-review fields
    # --------------------------------------------------

    review_sample["manual_label"] = ""
    review_sample["review_notes"] = ""

    review_sample.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("Security review sample v2 created.")
    print(f"Rows written: {len(review_sample):,}")
    print(f"Output file: {OUTPUT_FILE}")

    print("\nReview-group distribution:")
    print(review_sample["review_group"].value_counts())


if __name__ == "__main__":
    main()