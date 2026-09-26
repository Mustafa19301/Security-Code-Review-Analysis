import pandas as pd
import re
from collections import Counter

# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = "data/processed/unique_comments.csv"
CHUNK_SIZE = 100_000


# ============================================================
# SECURITY KEYWORDS
# ============================================================

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
    "session",
    "csrf",
    "cross-site",
    "xss",
    "sql injection",
    "injection",
    "command injection",
    "code injection",
    "path traversal",
    "directory traversal",
    "buffer overflow",
    "memory corruption",
    "remote code execution",
    "rce",
    "arbitrary code",
    "arbitrary execution",
    "sandbox",
    "encryption",
    "decrypt",
    "cryptographic",
    "certificate",
    "tls",
    "ssl",
    "sanitiz",
    "sanitize",
    "validation",
    "validate input",
    "untrusted input",
    "unsafe input",
    "malicious",
    "privilege escalation",
    "denial of service",
    "dos",
    "cve"
]


# ============================================================
# HELPER FUNCTION
# ============================================================

def contains_security_keyword(text):
    """
    Returns True if a comment contains at least one
    security-related keyword.
    """

    if pd.isna(text):
        return False

    text = str(text).lower()

    for keyword in SECURITY_KEYWORDS:

        if keyword in text:
            return True

    return False


# ============================================================
# INITIALIZE COUNTERS
# ============================================================

total_comments = 0

empty_comments = 0
very_short_comments = 0
short_comments = 0

comments_with_urls = 0
comments_with_code = 0

security_candidates = 0

comment_lengths = []

word_frequency = Counter()

language_counts = Counter()

security_language_counts = Counter()

security_keyword_counts = Counter()


# ============================================================
# PROCESS DATASET
# ============================================================

print("=" * 70)
print("COMMENT ANALYSIS")
print("=" * 70)

print("\nInput file:")
print(INPUT_FILE)

print("\nReading processed dataset...")
print("-" * 70)


for chunk_number, chunk in enumerate(
    pd.read_csv(INPUT_FILE, chunksize=CHUNK_SIZE),
    start=1
):

    total_comments += len(chunk)

    # --------------------------------------------------------
    # Process each comment
    # --------------------------------------------------------

    for row in chunk.itertuples(index=False):

        comment = row.comment

        # ----------------------------------------------------
        # Missing / empty comments
        # ----------------------------------------------------

        if pd.isna(comment):

            empty_comments += 1
            continue

        comment = str(comment)

        stripped_comment = comment.strip()

        if len(stripped_comment) == 0:

            empty_comments += 1

        # ----------------------------------------------------
        # Comment length
        # ----------------------------------------------------

        length = len(comment)

        comment_lengths.append(length)

        # ----------------------------------------------------
        # Short comments
        # ----------------------------------------------------

        if length <= 10:

            very_short_comments += 1

        if length <= 30:

            short_comments += 1

        # ----------------------------------------------------
        # URLs
        # ----------------------------------------------------

        if re.search(
            r"https?://|www\.",
            comment,
            re.IGNORECASE
        ):

            comments_with_urls += 1

        # ----------------------------------------------------
        # Code indicators
        # ----------------------------------------------------

        code_indicators = [
            "```",
            "`",
            "();",
            "=>",
            "::",
            "#include",
            "def ",
            "class ",
            "function ",
            "public ",
            "private ",
            "protected ",
            "return ",
            "import ",
            "from ",
            "SELECT ",
            "INSERT ",
            "UPDATE ",
            "DELETE "
        ]

        has_code = False

        for indicator in code_indicators:

            if indicator.lower() in comment.lower():

                has_code = True
                break

        if has_code:

            comments_with_code += 1

        # ----------------------------------------------------
        # Word frequency
        # ----------------------------------------------------

        words = re.findall(
            r"\b[a-zA-Z][a-zA-Z0-9_'-]*\b",
            comment.lower()
        )

        word_frequency.update(words)

        # ----------------------------------------------------
        # Security keyword analysis
        # ----------------------------------------------------

        if contains_security_keyword(comment):

            security_candidates += 1

            # Count which security keywords were found

            comment_lower = comment.lower()

            for keyword in SECURITY_KEYWORDS:

                if keyword in comment_lower:

                    security_keyword_counts[keyword] += 1

            # Track security candidates by language

            language = row.language

            if pd.isna(language):

                language = "Unknown"

            security_language_counts[str(language)] += 1

        # ----------------------------------------------------
        # Overall language distribution
        # ----------------------------------------------------

        language = row.language

        if pd.isna(language):

            language = "Unknown"

        language_counts[str(language)] += 1

    # --------------------------------------------------------
    # Progress
    # --------------------------------------------------------

    if chunk_number % 10 == 0:

        print(
            f"Processed {total_comments:,} comments..."
        )


# ============================================================
# CALCULATE STATISTICS
# ============================================================

comment_lengths_series = pd.Series(
    comment_lengths
)

average_length = comment_lengths_series.mean()
median_length = comment_lengths_series.median()

minimum_length = comment_lengths_series.min()
maximum_length = comment_lengths_series.max()


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n")
print("=" * 70)
print("COMMENT DATASET SUMMARY")
print("=" * 70)

print(
    f"\nTotal comments:              "
    f"{total_comments:,}"
)

print(
    f"Empty/missing comments:      "
    f"{empty_comments:,}"
)

print(
    f"Comments <= 10 characters:   "
    f"{very_short_comments:,}"
)

print(
    f"Comments <= 30 characters:   "
    f"{short_comments:,}"
)

print(
    f"Comments containing URLs:    "
    f"{comments_with_urls:,}"
)

print(
    f"Comments with code indicators:"
    f" {comments_with_code:,}"
)


# ============================================================
# COMMENT LENGTH
# ============================================================

print("\n")
print("=" * 70)
print("COMMENT LENGTH STATISTICS")
print("=" * 70)

print(
    f"\nAverage length:  "
    f"{average_length:.2f} characters"
)

print(
    f"Median length:   "
    f"{median_length:.2f} characters"
)

print(
    f"Minimum length:  "
    f"{minimum_length}"
)

print(
    f"Maximum length:  "
    f"{maximum_length}"
)


# ============================================================
# SECURITY CANDIDATES
# ============================================================

print("\n")
print("=" * 70)
print("SECURITY KEYWORD ANALYSIS")
print("=" * 70)

security_percentage = (
    security_candidates / total_comments * 100
)

print(
    f"\nSecurity keyword candidates: "
    f"{security_candidates:,}"
)

print(
    f"Percentage of comments:       "
    f"{security_percentage:.2f}%"
)


# ============================================================
# SECURITY KEYWORDS
# ============================================================

print("\n")
print("=" * 70)
print("MOST COMMON SECURITY KEYWORDS")
print("=" * 70)

for keyword, count in security_keyword_counts.most_common(30):

    percentage = (
        count / security_candidates * 100
    )

    print(
        f"{keyword:<25}"
        f"{count:>10,}"
        f" ({percentage:6.2f}%)"
    )


# ============================================================
# SECURITY CANDIDATES BY LANGUAGE
# ============================================================

print("\n")
print("=" * 70)
print("SECURITY CANDIDATES BY LANGUAGE")
print("=" * 70)

for language, count in security_language_counts.most_common(30):

    percentage = (
        count / security_candidates * 100
    )

    print(
        f"{language:<25}"
        f"{count:>10,}"
        f" ({percentage:6.2f}%)"
    )


# ============================================================
# LANGUAGE DISTRIBUTION
# ============================================================

print("\n")
print("=" * 70)
print("OVERALL LANGUAGE DISTRIBUTION")
print("=" * 70)

for language, count in language_counts.most_common(30):

    percentage = (
        count / total_comments * 100
    )

    print(
        f"{language:<25}"
        f"{count:>10,}"
        f" ({percentage:6.2f}%)"
    )


# ============================================================
# MOST COMMON WORDS
# ============================================================

print("\n")
print("=" * 70)
print("MOST COMMON WORDS")
print("=" * 70)

# Common English/code-review words that aren't useful
# for our initial analysis.

STOP_WORDS = {
    "the",
    "and",
    "this",
    "that",
    "with",
    "from",
    "have",
    "has",
    "for",
    "you",
    "your",
    "are",
    "was",
    "but",
    "not",
    "can",
    "will",
    "would",
    "should",
    "could",
    "about",
    "just",
    "like",
    "what",
    "when",
    "where",
    "which",
    "there",
    "they",
    "their",
    "then",
    "than",
    "also",
    "into",
    "been",
    "were",
    "here",
    "some",
    "more",
    "only",
    "one",
    "use",
    "used",
    "using",
    "make",
    "made",
    "need",
    "needs",
    "please",
    "think",
    "maybe",
    "looks",
    "look",
    "see",
    "get",
    "got",
    "how",
    "why"
}

filtered_words = Counter()

for word, count in word_frequency.items():

    if word not in STOP_WORDS and len(word) > 2:

        filtered_words[word] = count


print("\nTop 50 words:")

for word, count in filtered_words.most_common(50):

    print(
        f"{word:<25}"
        f"{count:>10,}"
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n")
print("=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)

print(
    f"\nAnalyzed {total_comments:,} unique comments."
)

print(
    f"Found {security_candidates:,} "
    f"potential security-related comments."
)

print(
    "\nIMPORTANT:"
)

print(
    "Security keyword candidates are NOT final security labels."
)

print(
    "They will be reviewed and refined before machine learning."
)

print("\n" + "=" * 70)