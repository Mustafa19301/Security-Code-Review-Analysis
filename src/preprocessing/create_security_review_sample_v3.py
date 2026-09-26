import os
import pandas as pd


CANDIDATES_FILE = "data/processed/security_candidates_v2.csv"
ALL_COMMENTS_FILE = "data/processed/unique_comments.csv"
OUTPUT_FILE = "data/processed/security_review_sample_v3.csv"

RANDOM_STATE = 42

NON_CANDIDATE_SAMPLE_SIZE = 200
HIGH_CONFIDENCE_SAMPLE_SIZE = 200
CONTEXTUAL_SAMPLE_SIZE = 100
WEAK_SAMPLE_SIZE = 100


def load_candidate_data():
    if not os.path.exists(CANDIDATES_FILE):
        raise FileNotFoundError(
            f"Candidate file was not found: {CANDIDATES_FILE}"
        )

    candidates = pd.read_csv(CANDIDATES_FILE)

    print(f"Total v2 candidates available: {len(candidates):,}")

    return candidates


def load_non_candidate_sample(candidate_ids):
    if not os.path.exists(ALL_COMMENTS_FILE):
        raise FileNotFoundError(
            f"Comments file was not found: {ALL_COMMENTS_FILE}"
        )

    selected_parts = []
    rows_collected = 0

    print("\nSearching for non-candidate comments...")

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            ALL_COMMENTS_FILE,
            chunksize=100_000,
            dtype={
                "comment_id": "Int64",
                "comment": "string",
                "repo": "string",
                "language": "string",
                "pr_id": "Int64",
                "c_id": "Int64",
            },
        ),
        start=1,
    ):
        non_candidates = chunk[
            ~chunk["comment_id"].isin(candidate_ids)
        ].copy()

        if len(non_candidates) > 0:
            selected_parts.append(non_candidates)
            rows_collected += len(non_candidates)

        print(
            f"Processed chunk {chunk_number:,} | "
            f"Potential non-candidates collected: "
            f"{rows_collected:,}"
        )

        if rows_collected >= NON_CANDIDATE_SAMPLE_SIZE * 10:
            break

    if not selected_parts:
        raise ValueError(
            "No non-candidate comments were found."
        )

    non_candidates = pd.concat(
        selected_parts,
        ignore_index=True,
    )

    non_candidates = non_candidates.sample(
        n=min(
            NON_CANDIDATE_SAMPLE_SIZE,
            len(non_candidates),
        ),
        random_state=RANDOM_STATE,
    ).copy()

    non_candidates["review_group"] = "non_candidate"

    return non_candidates


def sample_candidate_group(
    candidates,
    candidate_type,
    sample_size,
):
    group = candidates[
        candidates["candidate_type"] == candidate_type
    ].copy()

    if len(group) == 0:
        raise ValueError(
            f"No candidates found for group: {candidate_type}"
        )

    sampled_group = group.sample(
        n=min(sample_size, len(group)),
        random_state=RANDOM_STATE,
    ).copy()

    sampled_group["review_group"] = candidate_type

    return sampled_group


def main():
    candidates = load_candidate_data()

    candidate_ids = set(
        candidates["comment_id"]
        .dropna()
        .astype("int64")
    )

    non_candidates = load_non_candidate_sample(
        candidate_ids
    )

    high_confidence = sample_candidate_group(
        candidates,
        "high_confidence",
        HIGH_CONFIDENCE_SAMPLE_SIZE,
    )

    contextual = sample_candidate_group(
        candidates,
        "contextual",
        CONTEXTUAL_SAMPLE_SIZE,
    )

    weak = sample_candidate_group(
        candidates,
        "weak",
        WEAK_SAMPLE_SIZE,
    )

    review_sample = pd.concat(
        [
            non_candidates,
            high_confidence,
            contextual,
            weak,
        ],
        ignore_index=True,
    )

    review_sample = review_sample.sample(
        frac=1,
        random_state=RANDOM_STATE,
    ).reset_index(drop=True)

    review_sample["manual_label"] = ""
    review_sample["review_notes"] = ""

    review_sample.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("\nSecurity review sample v3 created.")
    print(f"Rows written: {len(review_sample):,}")
    print(f"Output file: {OUTPUT_FILE}")

    print("\nReview-group distribution:")
    print(
        review_sample["review_group"]
        .value_counts()
    )


if __name__ == "__main__":
    main()