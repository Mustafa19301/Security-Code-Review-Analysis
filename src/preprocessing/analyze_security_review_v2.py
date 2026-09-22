import os
import pandas as pd


INPUT_FILE = "data/processed/security_review_sample_v2.csv"


def calculate_percentage(numerator, denominator):
    if denominator == 0:
        return 0.0

    return (numerator / denominator) * 100


def main():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Input file was not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    df["manual_label"] = pd.to_numeric(
        df["manual_label"],
        errors="coerce",
    )

    if df["manual_label"].isna().any():
        raise ValueError(
            "Some rows do not have a valid manual_label."
        )

    print("Security Candidate v2 Validation Report")
    print("=" * 50)

    print(f"Total reviewed rows: {len(df):,}")

    print("\nOverall manual-label distribution:")
    overall_counts = (
        df["manual_label"]
        .value_counts()
        .sort_index()
    )

    for label, count in overall_counts.items():
        percentage = calculate_percentage(
            count,
            len(df),
        )

        if label == 0:
            description = "Not security-related"
        elif label == 1:
            description = "Clearly security-related"
        elif label == 2:
            description = "Possibly security-related"
        else:
            description = "Unknown"

        print(
            f"Label {int(label)} - {description}: "
            f"{count:,} ({percentage:.2f}%)"
        )

    print("\nManual labels by candidate type:")
    label_table = pd.crosstab(
        df["candidate_type"],
        df["manual_label"],
    )

    label_table = label_table.reindex(
        index=[
            "high_confidence",
            "contextual",
            "weak",
        ],
        columns=[0, 1, 2],
        fill_value=0,
    )

    print(label_table)

    print("\nCandidate-group precision:")
    print("-" * 50)

    for candidate_type in [
        "high_confidence",
        "contextual",
        "weak",
    ]:
        group = df[
            df["candidate_type"] == candidate_type
        ]

        clearly_security_related = len(
            group[group["manual_label"] == 1]
        )

        possibly_security_related = len(
            group[group["manual_label"] == 2]
        )

        total_group_rows = len(group)

        clear_precision = calculate_percentage(
            clearly_security_related,
            total_group_rows,
        )

        inclusive_precision = calculate_percentage(
            clearly_security_related
            + possibly_security_related,
            total_group_rows,
        )

        print(f"\nCandidate type: {candidate_type}")
        print(f"Reviewed rows: {total_group_rows:,}")
        print(
            "Clearly security-related: "
            f"{clearly_security_related:,}"
        )
        print(
            "Possibly security-related: "
            f"{possibly_security_related:,}"
        )
        print(
            "Clear precision: "
            f"{clear_precision:.2f}%"
        )
        print(
            "Clear + possible precision: "
            f"{inclusive_precision:.2f}%"
        )

    print("\nOverall precision:")
    clearly_security_related = len(
        df[df["manual_label"] == 1]
    )

    possibly_security_related = len(
        df[df["manual_label"] == 2]
    )

    overall_clear_precision = calculate_percentage(
        clearly_security_related,
        len(df),
    )

    overall_inclusive_precision = calculate_percentage(
        clearly_security_related
        + possibly_security_related,
        len(df),
    )

    print(
        "Clearly security-related: "
        f"{overall_clear_precision:.2f}%"
    )

    print(
        "Clearly or possibly security-related: "
        f"{overall_inclusive_precision:.2f}%"
    )

    print("\nReview-note examples for false positives:")
    false_positives = df[
        df["manual_label"] == 0
    ][
        [
            "candidate_type",
            "comment",
            "security_categories",
            "review_notes",
        ]
    ]

    for index, row in false_positives.head(10).iterrows():
        print("\n--- False-positive example ---")
        print(f"Candidate type: {row['candidate_type']}")
        print(f"Comment: {row['comment']}")
        print(
            "Categories: "
            f"{row['security_categories']}"
        )
        print(
            "Review notes: "
            f"{row['review_notes']}"
        )


if __name__ == "__main__":
    main()