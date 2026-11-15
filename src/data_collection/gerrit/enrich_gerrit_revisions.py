
import json
import subprocess
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]

COLLECTED_DIR = (
    PROJECT_ROOT / "data/gerrit/couchbase_java_client/collected"
)

GIT_REPO = (
    PROJECT_ROOT / "data/gerrit/repos/couchbase-java-client"
)

OUTPUT_DIR = (
    PROJECT_ROOT / "data/gerrit/couchbase_java_client/processed"
)

REVISIONS_FILE = COLLECTED_DIR / "revisions.csv"
MESSAGES_FILE = COLLECTED_DIR / "messages.csv"

OUTPUT_FILE = OUTPUT_DIR / "revisions_enriched.csv"
ERRORS_FILE = OUTPUT_DIR / "enrichment_errors.csv"


def run_git(args):
    """Run a Git command in the local Gerrit repository."""
    return subprocess.run(
        ["git", "-C", str(GIT_REPO)] + args,
        capture_output=True,
        text=True
    )


def git_object_exists(commit_id):
    """Check whether a commit exists locally."""
    result = run_git([
        "cat-file",
        "-e",
        f"{commit_id}^{{commit}}"
    ])

    return result.returncode == 0


def get_parent_commit(commit_id):
    """Retrieve the actual Git parent of a commit."""
    result = run_git([
        "rev-parse",
        "--verify",
        f"{commit_id}^"
    ])

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return result.stdout.strip()


def get_code_diff(base_commit, commit_id):
    """Retrieve the code diff between two commits."""

    result = run_git([
        "diff",
        "--no-ext-diff",
        "--no-color",
        "--find-renames",
        "--full-index",
        "--binary",
        "--unified=3",
        base_commit,
        commit_id,
        "--"
    ])

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return result.stdout

def prepare_review_messages(messages):
    """
    Group general Gerrit review messages by
    review_number and revision_number.
    """

    grouped_messages = {}

    for row in messages.to_dict("records"):

        review_number = pd.to_numeric(
            row.get("review_number"),
            errors="coerce"
        )

        revision_number = pd.to_numeric(
            row.get("revision_number"),
            errors="coerce"
        )

        # Do not arbitrarily assign messages without
        # a review number or revision attribution.
        if pd.isna(review_number) or pd.isna(revision_number):
            continue

        key = (
            int(review_number),
            int(revision_number)
        )

        message_record = {
            "message_id": row.get("message_id"),
            "author": row.get("author"),
            "date": row.get("date"),
            "tag": row.get("tag"),
            "message": row.get("message")
        }

        grouped_messages.setdefault(key, []).append(
            message_record
        )

    return grouped_messages

def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading Gerrit datasets...")

    revisions = pd.read_csv(REVISIONS_FILE)
    messages = pd.read_csv(MESSAGES_FILE)

    original_count = len(revisions)

    print(f"Revisions loaded: {original_count}")
    print(f"Messages loaded: {len(messages)}")

    # Prepare messages grouped by review and revision.
    grouped_messages = prepare_review_messages(messages)

    # Build a lookup of commit IDs for each revision.
    commit_lookup = {}

    for row in revisions.itertuples():

        key = (
            int(row.review_number),
            int(row.revision_number)
        )

        commit_lookup[key] = str(row.commit_id)

    code_diffs = []
    review_messages = []
    error_records = []

    successful_diff_count = 0
    failed_diff_count = 0
    skipped_diff_count = 0

    total = len(revisions)

    print("\nStarting revision enrichment...\n")

    for index, row in enumerate(
        revisions.itertuples(),
        start=1
    ):

        review_number = int(row.review_number)
        revision_number = int(row.revision_number)
        commit_id = str(row.commit_id)

        key = (review_number, revision_number)

        print(
            f"[{index}/{total}] "
            f"Review {review_number}, revision {revision_number}"
        )

        associated_messages = grouped_messages.get(key, [])

        review_messages.append(
            json.dumps(
                associated_messages,
                ensure_ascii=False
            )
        )

        fetch_success = str(
            row.git_fetch_success
        ).strip().lower() == "true"

        comparison_success = str(
            row.comparison_success
        ).strip().lower() == "true"

        if not fetch_success or not comparison_success:

            code_diffs.append("")

            skipped_diff_count += 1

            error_records.append({
                "review_number": review_number,
                "revision_number": revision_number,
                "commit_id": commit_id,
                "error": (
                    "Skipped because original Git fetch "
                    "or comparison was unsuccessful."
                )
            })

            continue

        try:

            if not git_object_exists(commit_id):
                raise RuntimeError(
                    "Commit is unavailable in the local Git repository."
                )

            previous_revision = str(
                row.previous_revision
            ).strip()

            # First revision: compare against actual Git parent.
            if previous_revision.lower() == "parent":

                base_commit = get_parent_commit(commit_id)

            # Later revisions: compare against the preceding
            # revision belonging to the same Gerrit review.
            else:

                previous_number = int(float(previous_revision))

                previous_key = (
                    review_number,
                    previous_number
                )

                base_commit = commit_lookup.get(previous_key)

                if base_commit is None:
                    raise RuntimeError(
                        f"Previous revision {previous_number} "
                        "was not found."
                    )

            if not git_object_exists(base_commit):
                raise RuntimeError(
                    f"Base commit {base_commit} is unavailable locally."
                )

            diff = get_code_diff(
                base_commit,
                commit_id
            )

            code_diffs.append(diff)

            successful_diff_count += 1

        except Exception as error:

            code_diffs.append("")

            failed_diff_count += 1

            error_records.append({
                "review_number": review_number,
                "revision_number": revision_number,
                "commit_id": commit_id,
                "error": str(error)
            })

            print(f"  Diff extraction failed: {error}")

    revisions["code_diff"] = code_diffs
    revisions["review_messages"] = review_messages

    revisions.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    # Save extraction errors separately.
    errors_df = pd.DataFrame(
        error_records,
        columns=[
            "review_number",
            "revision_number",
            "commit_id",
            "error"
        ]
    )

    errors_df.to_csv(
        ERRORS_FILE,
        index=False,
        encoding="utf-8"
    )

    print("\n" + "=" * 65)
    print("GERRIT REVISION ENRICHMENT COMPLETE")
    print("=" * 65)

    print(f"Original revision records: {original_count}")
    print(f"Enriched revision records: {len(revisions)}")

    print(f"\nSuccessful diff extractions: {successful_diff_count}")
    print(f"Failed diff extractions: {failed_diff_count}")
    print(f"Skipped diff extractions: {skipped_diff_count}")

    print(
        "Revisions with associated messages:",
        sum(len(grouped_messages.get(
            (int(row.review_number), int(row.revision_number)),
            []
        )) > 0 for row in revisions.itertuples())
    )

    print(f"\nNew columns: code_diff, review_messages")
    print(f"Enriched dataset: {OUTPUT_FILE}")
    print(f"Enrichment errors: {ERRORS_FILE}")

    if len(revisions) != original_count:
        print("\nWARNING: Revision record count changed!")

    else:
        print("\nValidation: Original revision count preserved.")


if __name__ == "__main__":
    main()