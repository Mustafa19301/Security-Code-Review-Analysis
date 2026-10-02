import pandas as pd
import re
import os

INPUT_FILE = "data/processed/unique_comments.csv"
OUTPUT_FILE = "data/processed/security_candidates.csv"

# Number of rows processed at a time
CHUNK_SIZE = 100_000


# Strong indicators:
# These are terms/phrases that are much more likely to indicate
# an actual security-related discussion.
STRONG_INDICATORS = {
    "vulnerability": r"\bvulnerabilit(?:y|ies)\b",
    "vulnerable": r"\bvulnerable\b",
    "exploit": r"\bexploit(?:s|ed|ing)?\b",
    "security flaw": r"\bsecurity\s+flaw\b",
    "security vulnerability": r"\bsecurity\s+vulnerabilit(?:y|ies)\b",
    "security issue": r"\bsecurity\s+issue\b",
    "security bug": r"\bsecurity\s+bug\b",
    "cve": r"\bcve[-\s]?\d{4}[-\s]?\d+\b",
    "remote code execution": r"\bremote\s+code\s+execution\b",
    "arbitrary code execution": r"\barbitrary\s+code\s+execution\b",
    "arbitrary execution": r"\barbitrary\s+(?:code\s+)?execution\b",
    "rce": r"\brce\b",
    "sql injection": r"\bsql\s+injection\b",
    "command injection": r"\bcommand\s+injection\b",
    "code injection": r"\bcode\s+injection\b",
    "xss": r"\bxss\b",
    "cross-site scripting": r"\bcross[-\s]site\s+scripting\b",
    "csrf": r"\bcsrf\b",
    "cross-site request forgery": r"\bcross[-\s]site\s+request\s+forgery\b",
    "path traversal": r"\bpath\s+traversal\b",
    "directory traversal": r"\bdirectory\s+traversal\b",
    "buffer overflow": r"\bbuffer\s+overflow\b",
    "buffer overrun": r"\bbuffer\s+overrun\b",
    "memory corruption": r"\bmemory\s+corruption\b",
    "use-after-free": r"\buse[-\s]?after[-\s]?free\b",
    "privilege escalation": r"\bprivilege\s+escalation\b",
    "denial of service": r"\bdenial\s+of\s+service\b",
    "sandbox escape": r"\bsandbox\s+escape\b",
}


# Weaker indicators:
# These words can appear in normal software discussions.
# We therefore require at least TWO weak indicators before
# considering a comment a security candidate.
WEAK_INDICATORS = {
    "authentication": r"\bauthentication\b",
    "authenticate": r"\bauthenticate(?:s|d|ing)?\b",
    "authorization": r"\bauthorization\b",
    "authorize": r"\bauthoriz(?:e|es|ed|ing|ation)\b",
    "access control": r"\baccess\s+control\b",
    "permission": r"\bpermissions?\b",
    "privilege": r"\bprivileges?\b",
    "password": r"\bpasswords?\b",
    "credential": r"\bcredentials?\b",
    "secret": r"\bsecrets?\b",
    "api key": r"\bapi\s+keys?\b",
    "token": r"\btokens?\b",
    "session": r"\bsessions?\b",
    "tls": r"\btls\b",
    "ssl": r"\bssl\b",
    "certificate": r"\bcertificates?\b",
    "encryption": r"\bencrypt(?:ion|ed|ing)?\b",
    "decrypt": r"\bdecrypt(?:ion|ed|ing)?\b",
    "cryptographic": r"\bcryptograph(?:ic|y)\b",
    "sanitize": r"\bsanit(?:ize|izes|ized|izing|ization)\b",
    "validation": r"\bvalidation\b",
    "validate input": r"\bvalidat(?:e|ing)\s+input\b",
    "untrusted input": r"\buntrusted\s+input\b",
    "unsafe input": r"\bunsafe\s+input\b",
    "malicious": r"\bmalicious\b",
    "sandbox": r"\bsandbox\b",
    "security": r"\bsecurity\b",
}

STRONG_PATTERNS = {
    name: re.compile(pattern, re.IGNORECASE)
    for name, pattern in STRONG_INDICATORS.items()
}

WEAK_PATTERNS = {
    name: re.compile(pattern, re.IGNORECASE)
    for name, pattern in WEAK_INDICATORS.items()
}

def detect_security_indicators(text):
    """
    Detect security-related indicators in a comment.

    Returns:
        matched_strong: list of strong indicators
        matched_weak: list of weak indicators
        categories: security categories
        candidate: True/False
        score: numeric candidate score
    """

    if pd.isna(text):
        return [], [], [], False, 0

    text = str(text)

    if not text.strip():
        return [], [], [], False, 0

    matched_strong = []
    matched_weak = []

    for name, pattern in STRONG_PATTERNS.items():
        if pattern.search(text):
            matched_strong.append(name)

    for name, pattern in WEAK_PATTERNS.items():
        if pattern.search(text):
            matched_weak.append(name)

    # --------------------------------------------------------
    # Candidate decision
    #
    # 1 strong indicator = candidate
    # OR
    # 2+ weak indicators = candidate
    # --------------------------------------------------------

    candidate = (
        len(matched_strong) >= 1
        or len(matched_weak) >= 2
    )

    # --------------------------------------------------------
    # Candidate score
    #
    # Strong indicator = 2 points
    # Weak indicator = 1 point
    # --------------------------------------------------------

    score = (len(matched_strong) * 2) + len(matched_weak)

    categories = set()

    all_matches = set(matched_strong + matched_weak)

    # Vulnerability / exploit
    if all_matches.intersection({
        "vulnerability",
        "vulnerable",
        "exploit",
        "security flaw",
        "security vulnerability",
        "security issue",
        "security bug",
        "cve"
    }):
        categories.add("vulnerability")

    # Authentication
    if all_matches.intersection({
        "authentication",
        "authenticate",
        "password",
        "credential",
        "session"
    }):
        categories.add("authentication")

    # Authorization / access control
    if all_matches.intersection({
        "authorization",
        "authorize",
        "access control",
        "permission",
        "privilege",
        "privilege escalation"
    }):
        categories.add("authorization")

    # Injection
    if all_matches.intersection({
        "sql injection",
        "command injection",
        "code injection",
        "xss",
        "cross-site scripting",
        "csrf",
        "cross-site request forgery"
    }):
        categories.add("injection")

    # Path traversal
    if all_matches.intersection({
        "path traversal",
        "directory traversal"
    }):
        categories.add("path_traversal")

    # Memory safety
    if all_matches.intersection({
        "buffer overflow",
        "buffer overrun",
        "memory corruption",
        "use-after-free"
    }):
        categories.add("memory_safety")

    # Code execution
    if all_matches.intersection({
        "remote code execution",
        "arbitrary code execution",
        "arbitrary execution",
        "rce"
    }):
        categories.add("code_execution")

    # Cryptography
    if all_matches.intersection({
        "tls",
        "ssl",
        "certificate",
        "encryption",
        "decrypt",
        "cryptographic"
    }):
        categories.add("cryptography")

    # Secrets
    if all_matches.intersection({
        "secret",
        "api key",
        "token",
        "credential"
    }):
        categories.add("secrets")

    # Input validation
    if all_matches.intersection({
        "sanitize",
        "validation",
        "validate input",
        "untrusted input",
        "unsafe input"
    }):
        categories.add("input_validation")

    # Denial of service
    if "denial of service" in all_matches:
        categories.add("denial_of_service")

    # Sandbox
    if all_matches.intersection({
        "sandbox",
        "sandbox escape"
    }):
        categories.add("sandbox")

    # General security
    if "security" in all_matches:
        categories.add("general_security")

    # Malicious activity
    if "malicious" in all_matches:
        categories.add("malicious_activity")

    return (
        matched_strong,
        matched_weak,
        sorted(categories),
        candidate,
        score
    )

def main():

    print("=" * 70)
    print("CREATING SECURITY CANDIDATE DATASET")
    print("=" * 70)

    print("\nInput:")
    print(INPUT_FILE)

    print("\nOutput:")
    print(OUTPUT_FILE)

    print("\nChunk size:")
    print(CHUNK_SIZE)

    if not os.path.exists(INPUT_FILE):
        print("\nERROR: Input file does not exist.")
        print("Expected:")
        print(INPUT_FILE)
        return

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
        print("\nRemoved previous output file.")

    total_rows = 0
    candidate_rows = 0

    strong_candidate_rows = 0
    weak_candidate_rows = 0

    category_counts = {}

    first_write = True

    for chunk_number, chunk in enumerate(
        pd.read_csv(
            INPUT_FILE,
            chunksize=CHUNK_SIZE
        ),
        start=1
    ):

        print(
            f"\nProcessing chunk {chunk_number}..."
        )

        total_rows += len(chunk)

        detection_results = (
            chunk["comment"]
            .apply(detect_security_indicators)
        )

        chunk["matched_strong"] = detection_results.apply(
            lambda x: "; ".join(x[0])
        )

        chunk["matched_weak"] = detection_results.apply(
            lambda x: "; ".join(x[1])
        )

        chunk["security_categories"] = detection_results.apply(
            lambda x: "; ".join(x[2])
        )

        chunk["candidate_score"] = detection_results.apply(
            lambda x: x[4]
        )

        chunk["indicator_strength"] = detection_results.apply(
            lambda x: (
                "strong"
                if len(x[0]) > 0
                else "weak"
                if len(x[1]) >= 2
                else ""
            )
        )

        candidate_mask = detection_results.apply(
            lambda x: x[3]
        )

        candidates = chunk[candidate_mask].copy()

        candidate_count = len(candidates)

        candidate_rows += candidate_count

        strong_count = (
            candidates["indicator_strength"]
            == "strong"
        ).sum()

        weak_count = (
            candidates["indicator_strength"]
            == "weak"
        ).sum()

        strong_candidate_rows += strong_count
        weak_candidate_rows += weak_count

        for categories in candidates["security_categories"]:

            if not categories:
                continue

            for category in categories.split("; "):

                category_counts[category] = (
                    category_counts.get(category, 0) + 1
                )

        candidates = candidates[
            [
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
                "indicator_strength"
            ]
        ]

        if len(candidates) > 0:

            candidates.to_csv(
                OUTPUT_FILE,
                mode="w" if first_write else "a",
                header=first_write,
                index=False
            )

            first_write = False

        print(
            f"Rows processed: {total_rows:,}"
        )

        print(
            f"Candidates found: {candidate_rows:,}"
        )

    print("\n" + "=" * 70)
    print("SECURITY CANDIDATE ANALYSIS COMPLETE")
    print("=" * 70)

    print(
        f"\nTotal comments processed: {total_rows:,}"
    )

    print(
        f"Security candidates:      {candidate_rows:,}"
    )

    if total_rows > 0:

        percentage = (
            candidate_rows / total_rows
        ) * 100

        print(
            f"Candidate percentage:     {percentage:.2f}%"
        )

    print(
        f"\nStrong candidates:        {strong_candidate_rows:,}"
    )

    print(
        f"Weak-only candidates:     {weak_candidate_rows:,}"
    )

    print("\nSecurity categories:")

    sorted_categories = sorted(
        category_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )

    for category, count in sorted_categories:

        percentage = (
            count / candidate_rows * 100
            if candidate_rows > 0
            else 0
        )

        print(
            f"{category:<25} "
            f"{count:>10,} "
            f"({percentage:>6.2f}%)"
        )

    print("\nOutput file:")
    print(OUTPUT_FILE)

    if os.path.exists(OUTPUT_FILE):

        file_size_mb = (
            os.path.getsize(OUTPUT_FILE)
            / (1024 * 1024)
        )

        print(
            f"Output size: {file_size_mb:.2f} MB"
        )

    print("\n" + "=" * 70)
    print("IMPORTANT")
    print("=" * 70)

    print(
        "\nThese are SECURITY CANDIDATES, not confirmed labels."
    )

    print(
        "We will manually inspect a sample before assigning"
    )

    print(
        "security_label = 1."
    )

if __name__ == "__main__":
    main()