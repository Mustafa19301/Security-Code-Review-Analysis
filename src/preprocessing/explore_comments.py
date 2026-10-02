import re
from collections import Counter

import pandas as pd


FILE_PATH = "data/processed/unique_comments.csv"
CHUNK_SIZE = 50_000

SECURITY_KEYWORDS = [
    "security",
    "secure",
    "vulnerability",
    "vulnerable",
    "exploit",
    "attack",
    "authentication",
    "authenticate",
    "authorization",
    "authorize",
    "permission",
    "privilege",
    "access control",
    "password",
    "credential",
    "secret",
    "token",
    "encryption",
    "encrypt",
    "decrypt",
    "cryptography",
    "injection",
    "sql injection",
    "xss",
    "cross-site scripting",
    "csrf",
    "sanitize",
    "sanitization",
    "validation",
    "input validation",
    "unsafe",
    "malicious",
    "cve",
    "cwe",
    "owasp",
    "ssl",
    "tls",
    "certificate",
    "cookie",
    "session",
    "jwt",
    "oauth"
]


def contains_security_keyword(comment):
    """
    Return True if the comment contains at least
    one security-related keyword.
    """

    if pd.isna(comment):
        return False

    comment = str(comment).lower()

    for keyword in SECURITY_KEYWORDS:
        if keyword in comment:
            return True

    return False


def extract_security_keywords(comment):
    """
    Return all security keywords found in a comment.
    """

    if pd.isna(comment):
        return []

    comment = str(comment).lower()

    found_keywords = []

    for keyword in SECURITY_KEYWORDS:
        if keyword in comment:
            found_keywords.append(keyword)

    return found_keywords


print("=" * 70)
print("EXPLORING UNIQUE COMMENTS")
print("=" * 70)

total_rows = 0
empty_comments = 0
short_comments = 0
security_candidate_count = 0

comment_length_sum = 0
comment_lengths = []

security_keyword_counts = Counter()
language_counts = Counter()

print("\nReading unique comments...")
print("-" * 70)

for chunk_number, chunk in enumerate(
    pd.read_csv(
        FILE_PATH,
        chunksize=CHUNK_SIZE,
        low_memory=True
    ),
    start=1
):

    total_rows += len(chunk)

    comments = chunk["comment"].fillna("").astype(str)

    lengths = comments.str.len()

    comment_length_sum += lengths.sum()
    comment_lengths.extend(lengths.tolist())

    empty_comments += int((lengths == 0).sum())
    short_comments += int((lengths <= 20).sum())

    for comment in comments:

        keywords = extract_security_keywords(comment)

        if keywords:
            security_candidate_count += 1
            security_keyword_counts.update(keywords)

    language_counts.update(
        chunk["language"].fillna("Unknown").astype(str)
    )

    if chunk_number % 20 == 0:
        print(f"Processed {total_rows:,} comments...")

length_series = pd.Series(comment_lengths)

print("\n")
print("=" * 70)
print("COMMENT EXPLORATION RESULTS")
print("=" * 70)

print(f"\nTotal comments:          {total_rows:,}")

print(
    f"Empty comments:         "
    f"{empty_comments:,} "
    f"({empty_comments / total_rows * 100:.2f}%)"
)

print(
    f"Comments <= 20 chars:   "
    f"{short_comments:,} "
    f"({short_comments / total_rows * 100:.2f}%)"
)

print(f"\nAverage length:         {length_series.mean():.2f}")
print(f"Median length:          {length_series.median():.2f}")
print(f"Minimum length:         {length_series.min():,}")
print(f"Maximum length:         {length_series.max():,}")

print("\n")
print("SECURITY KEYWORD CANDIDATES")
print("")

print(
    f"Comments containing at least one security keyword: "
    f"{security_candidate_count:,}"
)

print(
    f"Percentage of dataset: "
    f"{security_candidate_count / total_rows * 100:.2f}%"
)

print("\nKeyword frequencies:")

for keyword, count in security_keyword_counts.most_common():
    print(f"{keyword:<25} {count:>10,}")

print("\n")
print("TOP LANGUAGES")
print("")

for language, count in language_counts.most_common(20):
    print(f"{language:<25} {count:>10,}")

print("\n")
print("=" * 70)
print("EXPLORATION COMPLETE")
print("=" * 70)