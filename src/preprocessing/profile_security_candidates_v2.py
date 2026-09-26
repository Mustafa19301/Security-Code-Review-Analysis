import os
import pandas as pd


INPUT_FILE = "data/processed/security_candidates_v2.csv"


def main():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"File not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print("Security Candidates v2 Profile")
    print("=" * 40)

    print(f"Total candidates: {len(df):,}")
    print(f"Total columns: {len(df.columns)}")

    print("\nColumns:")
    for column in df.columns:
        print(f"- {column}")

    if "candidate_type" in df.columns:
        print("\nCandidate types:")
        print(df["candidate_type"].value_counts(dropna=False))

    if "indicator_strength" in df.columns:
        print("\nIndicator strength:")
        print(df["indicator_strength"].value_counts(dropna=False))

    if "candidate_score" in df.columns:
        print("\nCandidate score:")
        print(df["candidate_score"].describe())

    if "security_categories" in df.columns:
        print("\nMost common security categories:")

        category_counts = {}

        for value in df["security_categories"].dropna():
            categories = str(value).split(";")

            for category in categories:
                category = category.strip()

                if category:
                    category_counts[category] = (
                        category_counts.get(category, 0) + 1
                    )

        sorted_categories = sorted(
            category_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        for category, count in sorted_categories[:20]:
            print(f"{category}: {count:,}")

    if "matched_high_confidence" in df.columns:
        print("\nMost common high-confidence indicators:")

        high_confidence_counts = {}

        for value in df["matched_high_confidence"].dropna():
            indicators = str(value).split(";")

            for indicator in indicators:
                indicator = indicator.strip()

                if indicator:
                    high_confidence_counts[indicator] = (
                        high_confidence_counts.get(indicator, 0) + 1
                    )

        sorted_indicators = sorted(
            high_confidence_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        for indicator, count in sorted_indicators[:20]:
            print(f"{indicator}: {count:,}")


if __name__ == "__main__":
    main()