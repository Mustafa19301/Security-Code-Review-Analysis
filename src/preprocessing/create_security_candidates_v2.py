import os
import re
import pandas as pd


INPUT_FILE = "data/processed/unique_comments.csv"
OUTPUT_FILE = "data/processed/security_candidates_v2.csv"

CHUNK_SIZE = 100_000

HIGH_CONFIDENCE_INDICATORS = [
    "security vulnerability",
    "security flaw",
    "security bug",
    "security issue",
    "remote code execution",
    "arbitrary code execution",
    "arbitrary execution",
    "sql injection",
    "command injection",
    "code injection",
    "cross-site scripting",
    "cross site scripting",
    "xss",
    "cross-site request forgery",
    "cross site request forgery",
    "csrf",
    "path traversal",
    "directory traversal",
    "buffer overflow",
    "buffer overrun",
    "memory corruption",
    "use-after-free",
    "use after free",
    "privilege escalation",
    "denial of service",
    "sandbox escape",
    "cve",
    "cwe",
]


CONTEXTUAL_INDICATORS = [
    "vulnerability",
    "vulnerable",
    "exploit",
    "exploited",
    "exploitable",
    "security",
    "attack",
    "attacker",
    "payload",
    "bypass",
    "unsafe",
    "risk",
    "flaw",
    "exposure",
    "impact",
    "malicious",
    "untrusted input",
    "security-sensitive",
    "security sensitive",
]


WEAK_INDICATORS = [
    "authentication",
    "authenticate",
    "authorization",
    "authorize",
    "access control",
    "permission",
    "privilege",
    "password",
    "credential",
    "secret",
    "api key",
    "token",
    "session",
    "tls",
    "ssl",
    "certificate",
    "encryption",
    "encrypt",
    "decrypt",
    "cryptographic",
    "cryptography",
    "sanitize",
    "sanitization",
    "validation",
    "validate input",
    "input validation",
    "unsafe input",
    "sandbox",
]


CATEGORY_PATTERNS = {
    "vulnerability": [
        "vulnerability",
        "vulnerable",
        "security flaw",
        "security bug",
        "security issue",
        "flaw",
        "cve",
        "cwe",
    ],
    "exploitation": [
        "exploit",
        "exploited",
        "exploitable",
        "attack",
        "attacker",
        "payload",
        "malicious",
    ],
    "injection": [
        "sql injection",
        "command injection",
        "code injection",
        "xss",
        "cross-site scripting",
        "cross site scripting",
        "csrf",
        "cross-site request forgery",
        "cross site request forgery",
    ],
    "path_traversal": [
        "path traversal",
        "directory traversal",
    ],
    "memory_safety": [
        "buffer overflow",
        "buffer overrun",
        "memory corruption",
        "use-after-free",
        "use after free",
    ],
    "code_execution": [
        "remote code execution",
        "arbitrary code execution",
        "arbitrary execution",
    ],
    "authorization": [
        "authorization",
        "authorize",
        "access control",
        "permission",
        "privilege",
        "privilege escalation",
        "bypass",
    ],
    "authentication": [
        "authentication",
        "authenticate",
        "password",
        "credential",
        "session",
    ],
    "secrets": [
        "secret",
        "api key",
        "credential",
        "password",
        "token",
    ],
    "cryptography": [
        "tls",
        "ssl",
        "certificate",
        "encryption",
        "encrypt",
        "decrypt",
        "cryptographic",
        "cryptography",
    ],
    "input_validation": [
        "sanitize",
        "sanitization",
        "validation",
        "validate input",
        "input validation",
        "untrusted input",
        "unsafe input",
    ],
    "availability": [
        "denial of service",
    ],
    "sandbox": [
        "sandbox",
        "sandbox escape",
    ],
}

HIGH_CONFIDENCE_PATTERNS = {
    indicator: re.compile(
        r"\b" + re.escape(indicator) + r"\b",
        re.IGNORECASE,
    )
    for indicator in HIGH_CONFIDENCE_INDICATORS
}

CONTEXTUAL_PATTERNS = {
    indicator: re.compile(
        r"\b" + re.escape(indicator) + r"\b",
        re.IGNORECASE,
    )
    for indicator in CONTEXTUAL_INDICATORS
}

WEAK_PATTERNS = {
    indicator: re.compile(
        r"\b" + re.escape(indicator) + r"\b",
        re.IGNORECASE,
    )
    for indicator in WEAK_INDICATORS
}

CATEGORY_COMPILED_PATTERNS = {
    category: [
        re.compile(
            r"\b" + re.escape(indicator) + r"\b",
            re.IGNORECASE,
        )
        for indicator in indicators
    ]
    for category, indicators in CATEGORY_PATTERNS.items()
}


def find_matches(text, compiled_patterns):
    """
    Return the indicator names that appear in the text.
    """

    matches = []

    for indicator, pattern in compiled_patterns.items():
        if pattern.search(text):
            matches.append(indicator)

    return matches


def find_categories(text):
    """
    Return security categories detected in the comment.
    """

    categories = []

    for category, patterns in CATEGORY_COMPILED_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(text):
                categories.append(category)
                break

    return categories


def has_contextual_security_term(text):
    """
    Determine whether a comment contains contextual
    language suggesting a possible security concern.
    """

    for pattern in CONTEXTUAL_PATTERNS.values():
        if pattern.search(text):
            return True

    return False


def detect_security_indicators(comment):
    """
    Classify a comment using more conservative rules.

    Candidate types:

    high_confidence:
        Contains an explicit vulnerability phrase or
        a known vulnerability class.

    contextual:
        Contains a contextual security term together
        with additional security-related evidence.

    weak:
        Contains at least three weak indicators,
        including at least one non-generic indicator.

    not_candidate:
        Does not meet the above conditions.
    """

    if pd.isna(comment):
        comment = ""

    text = str(comment).strip()

    if not text:
        return {
            "matched_high_confidence": "",
            "matched_contextual": "",
            "matched_weak": "",
            "security_categories": "",
            "candidate_score": 0,
            "indicator_strength": "none",
            "candidate_type": "not_candidate",
            "is_candidate": False,
        }

    high_confidence_matches = find_matches(
        text,
        HIGH_CONFIDENCE_PATTERNS,
    )

    contextual_matches = find_matches(
        text,
        CONTEXTUAL_PATTERNS,
    )

    weak_matches = find_matches(
        text,
        WEAK_PATTERNS,
    )

    categories = find_categories(text)

    if len(high_confidence_matches) > 0:
        candidate_type = "high_confidence"
        indicator_strength = "strong"
        is_candidate = True

    else:
        non_generic_weak_matches = [
            match
            for match in weak_matches
            if match not in {
                "security",
                "permission",
                "privilege",
                "token",
                "session",
                "validation",
            }
        ]

        contextual_candidate = (
            len(contextual_matches) > 0
            and len(non_generic_weak_matches) >= 1
            and len(categories) >= 1
        )

        if contextual_candidate:
            candidate_type = "contextual"
            indicator_strength = "moderate"
            is_candidate = True

        else:
            weak_candidate = len(weak_matches) >= 3

            if weak_candidate:
                candidate_type = "weak"
                indicator_strength = "weak"
                is_candidate = True
            else:
                candidate_type = "not_candidate"
                indicator_strength = "none"
                is_candidate = False

    candidate_score = (
        len(high_confidence_matches) * 5
        + len(contextual_matches) * 2
        + len(weak_matches)
    )

    if not is_candidate:
        candidate_score = 0

    return {
        "matched_high_confidence": "; ".join(high_confidence_matches),
        "matched_contextual": "; ".join(contextual_matches),
        "matched_weak": "; ".join(weak_matches),
        "security_categories": "; ".join(categories),
        "candidate_score": candidate_score,
        "indicator_strength": indicator_strength,
        "candidate_type": candidate_type,
        "is_candidate": is_candidate,
    }

def main():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Input file was not found: {INPUT_FILE}"
        )

    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
        print(f"Removed previous output file: {OUTPUT_FILE}")

    total_rows = 0
    total_candidates = 0
    first_write = True

    print("Starting security candidate detection v2...")
    print(f"Input file: {INPUT_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Chunk size: {CHUNK_SIZE:,}")
    print()

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            INPUT_FILE,
            chunksize=CHUNK_SIZE,
            dtype={
                "comment_id": "Int64",
                "comment": "string",
                "repo": "string",
                "language": "string",
                "pr_id": "Int64",
                "c_id": "Int64",
            },
            keep_default_na=True,
        ),
        start=1,
    ):
        total_rows += len(chunk)

        detection_results = chunk["comment"].apply(
            detect_security_indicators
        )

        detection_df = pd.DataFrame(
            detection_results.tolist(),
            index=chunk.index,
        )

        chunk_with_results = pd.concat(
            [chunk, detection_df],
            axis=1,
        )

        candidate_chunk = chunk_with_results[
            chunk_with_results["is_candidate"] == True
        ].copy()

        candidate_chunk.drop(
            columns=["is_candidate"],
            inplace=True,
        )

        if len(candidate_chunk) > 0:
            candidate_chunk.to_csv(
                OUTPUT_FILE,
                mode="w" if first_write else "a",
                header=first_write,
                index=False,
            )

            first_write = False
            total_candidates += len(candidate_chunk)

        print(
            f"Processed chunk {chunk_number:,} | "
            f"Rows processed: {total_rows:,} | "
            f"Candidates found: {total_candidates:,}"
        )

    print()
    print("Finished security candidate detection v2.")
    print(f"Total rows processed: {total_rows:,}")
    print(f"Total candidates written: {total_candidates:,}")

    if total_candidates == 0:
        print("No candidates were found.")
    else:
        print(f"Output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()