import json
import re
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    PROJECT_ROOT
    / "data/gerrit/couchbase_java_client/processed/finalized_gerrit.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data/gerrit/couchbase_java_client/features"
)

OUTPUT_FILE = OUTPUT_DIR / "gerrit_structured_features.csv"

def safe_number(value):
    """Convert a value to a number, or return zero if unavailable."""
    return pd.to_numeric(value, errors="coerce")


def parse_review_messages(value):
    """Parse the JSON-formatted review message list."""
    if not isinstance(value, str) or not value.strip():
        return []

    try:
        messages = json.loads(value)
        return messages if isinstance(messages, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def get_changed_lines(diff_text):
    """
    Extract added and deleted lines from a unified Git diff.

    Excludes diff headers such as +++ and ---.
    """
    added = []
    deleted = []

    for line in diff_text.splitlines():
        if line.startswith("+++ ") or line.startswith("--- "):
            continue

        if line.startswith("+"):
            added.append(line[1:])

        elif line.startswith("-"):
            deleted.append(line[1:])

    return added, deleted


def get_changed_file_paths(diff_text):
    """Extract file paths from Git diff headers."""
    paths = []

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            match = re.match(
                r"diff --git a/(.*?) b/(.*)",
                line
            )

            if match:
                paths.append(match.group(2))

    return paths


def count_pattern(text, pattern):
    """Count occurrences of a regular expression."""
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def count_security_indicators(text):
    """Count broad security-related indicators in changed code."""
    patterns = {
        "authentication": (
            r"\bauthentication\b|\bauthenticator\b|\bauthenticate\b"
        ),
        "authorization": (
            r"\bauthorization\b|\bauthorize\b|\bpermission\b|\baccess control\b"
        ),
        "credentials": (
            r"\bpassword\b|\bcredential\b|\bsecret\b|\btoken\b"
        ),
        "cryptography": (
            r"\bssl\b|\btls\b|\bcertificate\b|\bcipher\b|\bcrypto\b"
        ),
        "input_validation": (
            r"\bvalidate\b|\bsanitize\b|\bvalidation\b|\bescape\b"
        ),
        "injection": (
            r"\bsql injection\b|\bcommand injection\b|\binjection\b"
        ),
    }

    return {
        f"security_{name}_count": count_pattern(text, pattern)
        for name, pattern in patterns.items()
    }


def extract_features(row):
    diff = row["code_diff"]

    if not isinstance(diff, str):
        diff = ""

    diff_available = bool(diff.strip())

    added_lines, deleted_lines = get_changed_lines(diff)

    added_text = "\n".join(added_lines)
    deleted_text = "\n".join(deleted_lines)
    changed_text = added_text + "\n" + deleted_text

    file_paths = get_changed_file_paths(diff)

    extensions = [
        Path(file_path).suffix.lower()
        for file_path in file_paths
        if Path(file_path).suffix
    ]

    review_messages = parse_review_messages(
        row["review_messages"]
    )

    message_texts = [
        str(message.get("message", ""))
        for message in review_messages
        if isinstance(message, dict)
    ]

    combined_messages = " ".join(message_texts)

    # Basic diff features
    features = {
        "diff_available": int(diff_available),
        "diff_character_count": len(diff),
        "diff_line_count": len(diff.splitlines()) if diff_available else 0,
        "added_line_count": len(added_lines),
        "deleted_line_count": len(deleted_lines),
        "changed_file_count_from_diff": len(file_paths),

        # File metadata
        "java_file_count": sum(ext == ".java" for ext in extensions),
        "test_file_count": sum(
            "test" in file_path.lower()
            for file_path in file_paths
        ),
        "unique_file_extension_count": len(set(extensions)),
        "java_file_indicator": int(".java" in extensions),

        # Code structure indicators
        "conditional_count": count_pattern(
            changed_text,
            r"\bif\b|\belse\b|\bswitch\b|\bcase\b"
        ),
        "loop_count": count_pattern(
            changed_text,
            r"\bfor\b|\bwhile\b|\bdo\b"
        ),
        "exception_count": count_pattern(
            changed_text,
            r"\btry\b|\bcatch\b|\bthrow\b|\bthrows\b"
        ),
        "method_declaration_count": count_pattern(
            added_text,
            r"\b(public|private|protected)\s+"
            r"[\w<>\[\], ?]+\s+\w+\s*\("
        ),

        # Review metadata
        "review_message_count": len(review_messages),
        "review_message_character_count": len(combined_messages),
    }

    # Existing patch metadata
    for column in ["changed_files", "insertions", "deletions"]:
        features[column] = safe_number(row[column])

    # Security-related indicators
    features.update(count_security_indicators(changed_text))

    # Separate added and deleted security indicators
    features["added_security_indicator_count"] = sum(
        count_security_indicators(added_text).values()
    )

    features["deleted_security_indicator_count"] = sum(
        count_security_indicators(deleted_text).values()
    )

    return pd.Series(features)

def main():
    print("Loading finalized Gerrit dataset...")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input dataset not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "review_number",
        "revision_number",
        "commit_id",
        "status",
        "changed_files",
        "insertions",
        "deletions",
        "git_fetch_success",
        "comparison_success",
        "code_diff",
        "review_messages",
        "security_label",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    print("Extracting structured features...")

    extracted = df.apply(extract_features, axis=1)

    # Preserve identifiers and the existing target label.
    identifiers = df[
        [
            "review_number",
            "revision_number",
            "commit_id",
            "security_label",
        ]
    ].copy()

    result = pd.concat(
        [identifiers, extracted],
        axis=1
    )

    # Preserve useful collection-quality metadata.
    result["git_fetch_success"] = df["git_fetch_success"]
    result["comparison_success"] = df["comparison_success"]
    result["status"] = df["status"]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    result.to_csv(OUTPUT_FILE, index=False)

    print("\nFEATURE EXTRACTION COMPLETE")
    print("-" * 45)

    print("Input revisions:", len(df))
    print("Output revisions:", len(result))
    print(
        "Non-empty diffs:",
        int(result["diff_available"].sum())
    )
    print(
        "Empty diffs:",
        int((result["diff_available"] == 0).sum())
    )

    print("\nSecurity label distribution:")
    print(result["security_label"].value_counts().sort_index())

    print("\nOutput feature count:", len(result.columns) - 4)
    print("Output file:", OUTPUT_FILE)

    print("\nFirst five records:")
    print(result.head().to_string(index=False))


if __name__ == "__main__":
    main()
