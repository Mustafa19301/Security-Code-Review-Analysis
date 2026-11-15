import csv
import json
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import quote

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_CSV = (
    PROJECT_ROOT
    / "data/gerrit/raw/couchbase-java-client.csv"
)

REPO_DIR = (
    PROJECT_ROOT
    / "data/gerrit/repos/couchbase-java-client"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data/gerrit/couchbase_java_client/collected"
)

GERRIT_BASE_URL = "https://review.couchbase.org"

MAX_REVIEWS = 916

REQUEST_DELAY_SECONDS = 0.5
REQUEST_TIMEOUT_SECONDS = 30

REVIEWS_FILE = OUTPUT_DIR / "reviews.csv"
REVISIONS_FILE = OUTPUT_DIR / "revisions.csv"
MESSAGES_FILE = OUTPUT_DIR / "messages.csv"
PATCHES_FILE = OUTPUT_DIR / "patches.csv"
ERRORS_FILE = OUTPUT_DIR / "collection_errors.csv"


REVIEW_FIELDS = [
    "review_number",
    "change_id",
    "subject",
    "project",
    "branch",
    "status",
    "author",
    "created",
    "updated",
    "submitted",
    "insertions",
    "deletions",
    "total_comment_count",
    "review_url",
    "api_success",
]

REVISION_FIELDS = [
    "review_number",
    "revision_number",
    "commit_id",
    "gerrit_ref",
    "status",
    "previous_revision",
    "changed_files",
    "insertions",
    "deletions",
    "git_fetch_success",
    "comparison_success",
]

MESSAGE_FIELDS = [
    "review_number",
    "message_id",
    "revision_number",
    "author",
    "date",
    "tag",
    "message",
]

PATCH_FIELDS = [
    "review_number",
    "revision_number",
    "previous_revision",
    "file_path",
    "insertions",
    "deletions",
    "change_type",
]

ERROR_FIELDS = [
    "review_number",
    "revision_number",
    "stage",
    "error",
]

session = requests.Session()

session.headers.update({
    "Accept": "application/json",
    "User-Agent": "COMP4990B-Gerrit-Dataset-Research/1.0",
})

def normalize_key(value):
    return re.sub(r"[^a-z0-9]", "", value.lower())


def get_column(row, name):
    normalized = {
        normalize_key(key): key
        for key in row
        if key is not None
    }

    actual = normalized.get(normalize_key(name))

    if actual is None:
        raise KeyError(f"Missing CSV column: {name}")

    return (row.get(actual) or "").strip()


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fields,
            extrasaction="ignore"
        )

        writer.writeheader()
        writer.writerows(rows)


def add_error(errors, review, revision, stage, message):
    errors.append({
        "review_number": review,
        "revision_number": revision,
        "stage": stage,
        "error": str(message),
    })

    print(
        f"[ERROR] Review {review}, "
        f"revision {revision}, {stage}: {message}"
    )


def extract_name(person):
    if not isinstance(person, dict):
        return ""

    return (
        person.get("name")
        or person.get("username")
        or person.get("email")
        or ""
    )

def load_records():

    records = {}

    with INPUT_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            review = get_column(row, "review_number")
            revision = int(get_column(row, "revision_number"))

            record = {
                "review_number": review,
                "revision_number": revision,
                "status": get_column(row, "status"),
                "change_id": get_column(row, "change_id"),
                "review_url": get_column(row, "url"),
                "before_commit_id": get_column(
                    row, "before_commit_id"
                ),
                "after_commit_id": get_column(
                    row, "after_commit_id"
                ),
            }

            records.setdefault(review, {})[revision] = record

    selected_reviews = sorted(
        records.keys(),
        key=lambda value: int(value)
    )

    if MAX_REVIEWS is not None:
        selected_reviews = selected_reviews[:MAX_REVIEWS]

    return {
        review: records[review]
        for review in selected_reviews
    }



# GERRIT API
def parse_gerrit_response(response):

    text = response.text

    if text.startswith(")]}'"):
        text = text.split("\n", 1)[1]

    return json.loads(text)


def get_review_details(review_number):

    url = (
        f"{GERRIT_BASE_URL}/changes/"
        f"{quote(review_number, safe='')}/detail"
    )

    params = [
        ("o", "MESSAGES"),
        ("o", "ALL_REVISIONS"),
    ]

    response = session.get(
        url,
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS
    )

    response.raise_for_status()

    return parse_gerrit_response(response)

def extract_review(review_number, records, detail):

    first_record = next(iter(records.values()))

    owner = detail.get("owner", {})

    return {
        "review_number": review_number,
        "change_id": detail.get(
            "change_id",
            first_record["change_id"]
        ),
        "subject": detail.get("subject", ""),
        "project": detail.get("project", ""),
        "branch": detail.get("branch", ""),
        "status": detail.get(
            "status",
            first_record["status"]
        ),
        "author": extract_name(owner),
        "created": detail.get("created", ""),
        "updated": detail.get("updated", ""),
        "submitted": detail.get("submitted", ""),
        "insertions": detail.get("insertions", ""),
        "deletions": detail.get("deletions", ""),
        "total_comment_count": detail.get(
            "total_comment_count", ""
        ),
        "review_url": first_record["review_url"],
        "api_success": True,
    }

def extract_messages(review_number, detail):

    messages = []

    for item in detail.get("messages", []):

        messages.append({
            "review_number": review_number,
            "message_id": item.get("id", ""),
            "revision_number": item.get(
                "_revision_number", ""
            ),
            "author": extract_name(item.get("author", {})),
            "date": item.get("date", ""),
            "tag": item.get("tag", ""),
            "message": item.get("message", ""),
        })

    return messages

def run_git(arguments):

    result = subprocess.run(
        ["git", "-C", str(REPO_DIR)] + arguments,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or "Git command failed."
        )

    return result.stdout


def build_gerrit_ref(review_number, revision_number):

    last_two = str(review_number).zfill(2)[-2:]

    return (
        f"refs/changes/{last_two}/"
        f"{review_number}/{revision_number}"
    )


def fetch_revision(review_number, revision_number):

    gerrit_ref = build_gerrit_ref(
        review_number,
        revision_number
    )

    run_git([
        "fetch",
        "--depth=2",
        "origin",
        gerrit_ref
    ])

    commit_id = run_git([
        "rev-parse",
        "FETCH_HEAD"
    ]).strip()

    return commit_id, gerrit_ref


def get_first_parent(commit_id):
    """
    Return the first parent of a commit.

    Gerrit patch-set commits normally have one parent.
    If no parent exists, return an empty string.
    """

    output = run_git([
        "rev-list",
        "--parents",
        "-n",
        "1",
        commit_id
    ]).strip()

    parts = output.split()

    if len(parts) < 2:
        return ""

    return parts[1]

def compare_revisions(
    review_number,
    revision_number,
    previous_revision,
    previous_commit,
    current_commit
):

    numstat = run_git([
        "diff",
        "--numstat",
        "-M",
        previous_commit,
        current_commit
    ])

    name_status = run_git([
        "diff",
        "--name-status",
        "-M",
        previous_commit,
        current_commit
    ])

    change_types = {}

    for line in name_status.splitlines():

        parts = line.split("\t")

        if not parts:
            continue

        change_type = parts[0]

        if change_type.startswith("R") and len(parts) >= 3:
            # Git reports both old and new paths for renames.
            old_path = parts[1]
            new_path = parts[2]

            change_types[new_path] = "Renamed"
            change_types[old_path] = "Renamed"

        elif len(parts) >= 2:

            file_path = parts[1]

            if change_type == "A":
                change_types[file_path] = "Added"
            elif change_type == "D":
                change_types[file_path] = "Deleted"
            else:
                change_types[file_path] = "Modified"

    patch_rows = []

    total_insertions = 0
    total_deletions = 0

    for line in numstat.splitlines():

        parts = line.split("\t", 2)

        if len(parts) != 3:
            continue

        added, deleted, file_path = parts

        insertions = (
            int(added) if added.isdigit() else 0
        )

        deletions = (
            int(deleted) if deleted.isdigit() else 0
        )

        total_insertions += insertions
        total_deletions += deletions

        patch_rows.append({
            "review_number": review_number,
            "revision_number": revision_number,
            "previous_revision": previous_revision,
            "file_path": file_path,
            "insertions": insertions,
            "deletions": deletions,
            "change_type": change_types.get(
                file_path, "Modified"
            ),
        })

    return (
        patch_rows,
        len(patch_rows),
        total_insertions,
        total_deletions,
    )

def main():

    if not INPUT_CSV.exists():
        raise FileNotFoundError(INPUT_CSV)

    if not (REPO_DIR / ".git").exists():
        raise FileNotFoundError(
            f"Gerrit Git repository not found: {REPO_DIR}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_records = load_records()

    reviews = []
    revisions = []
    messages = []
    patches = []
    errors = []

    print("=" * 60)
    print("GERRIT DATASET COLLECTION")
    print("=" * 60)

    print(f"Input CSV: {INPUT_CSV}")
    print(f"Unique reviews selected: {len(all_records)}")

    for review_number, review_records in all_records.items():

        print(f"\nCollecting review {review_number}")

        try:

            detail = get_review_details(review_number)

            reviews.append(
                extract_review(
                    review_number,
                    review_records,
                    detail
                )
            )

            messages.extend(
                extract_messages(review_number, detail)
            )

        except Exception as error:

            detail = None

            add_error(
                errors,
                review_number,
                "",
                "review_details",
                error
            )

            reviews.append({
                "review_number": review_number,
                "change_id": next(
                    iter(review_records.values())
                )["change_id"],
                "review_url": next(
                    iter(review_records.values())
                )["review_url"],
                "api_success": False,
            })

        time.sleep(REQUEST_DELAY_SECONDS)

        previous_commit = None
        previous_revision = None
        previous_fetch_succeeded = True

        for revision_number, record in sorted(
            review_records.items()
        ):

            expected_commit = record["after_commit_id"]

            revision_result = {
                "review_number": review_number,
                "revision_number": revision_number,
                "commit_id": expected_commit,
                "gerrit_ref": "",
                "status": record["status"],
                "previous_revision": "",
                "changed_files": "",
                "insertions": "",
                "deletions": "",
                "git_fetch_success": False,
                "comparison_success": False,
            }

            try:

                if not re.fullmatch(
                    r"[0-9a-fA-F]{40}",
                    expected_commit
                ):
                    raise ValueError(
                        f"Invalid commit hash: {expected_commit}"
                    )

                fetched_commit, gerrit_ref = fetch_revision(
                    review_number,
                    revision_number
                )

                revision_result["commit_id"] = fetched_commit
                revision_result["gerrit_ref"] = gerrit_ref
                revision_result["git_fetch_success"] = True

                print(
                    f"  Revision {revision_number}: "
                    f"fetched {fetched_commit[:8]}"
                )

                # First revision: compare against its Git parent.
                if previous_commit is None:

                    parent_commit = get_first_parent(
                        fetched_commit
                    )

                    if parent_commit:

                        patch_rows, file_count, additions, deletions = (
                            compare_revisions(
                                review_number,
                                revision_number,
                                "parent",
                                parent_commit,
                                fetched_commit
                            )
                        )

                        patches.extend(patch_rows)

                        revision_result.update({
                            "previous_revision": "parent",
                            "changed_files": file_count,
                            "insertions": additions,
                            "deletions": deletions,
                            "comparison_success": True,
                        })

                        print(
                            f"    Compared with Git parent: "
                            f"{file_count} files, "
                            f"+{additions}/-{deletions}"
                        )

                    else:

                        add_error(
                            errors,
                            review_number,
                            revision_number,
                            "first_revision_comparison",
                            "Commit has no parent."
                        )

                # Subsequent revisions: compare with prior revision.
                elif previous_fetch_succeeded:

                    patch_rows, file_count, additions, deletions = (
                        compare_revisions(
                            review_number,
                            revision_number,
                            previous_revision,
                            previous_commit,
                            fetched_commit
                        )
                    )

                    patches.extend(patch_rows)

                    revision_result.update({
                        "previous_revision": previous_revision,
                        "changed_files": file_count,
                        "insertions": additions,
                        "deletions": deletions,
                        "comparison_success": True,
                    })

                    print(
                        f"    Compared with revision "
                        f"{previous_revision}: "
                        f"{file_count} files, "
                        f"+{additions}/-{deletions}"
                    )

                else:

                    add_error(
                        errors,
                        review_number,
                        revision_number,
                        "revision_comparison",
                        "Previous revision fetch failed; "
                        "comparison skipped to preserve continuity."
                    )

                previous_commit = fetched_commit
                previous_revision = revision_number
                previous_fetch_succeeded = True

            except Exception as error:

                add_error(
                    errors,
                    review_number,
                    revision_number,
                    "git_fetch_or_comparison",
                    error
                )

                previous_fetch_succeeded = False

            revisions.append(revision_result)

            time.sleep(REQUEST_DELAY_SECONDS)

    write_csv(REVIEWS_FILE, REVIEW_FIELDS, reviews)
    write_csv(REVISIONS_FILE, REVISION_FIELDS, revisions)
    write_csv(MESSAGES_FILE, MESSAGE_FIELDS, messages)
    write_csv(PATCHES_FILE, PATCH_FIELDS, patches)
    write_csv(ERRORS_FILE, ERROR_FIELDS, errors)

    print("\n" + "=" * 60)
    print("COLLECTION COMPLETE")
    print("=" * 60)

    print(f"Reviews collected: {len(reviews)}")
    print(f"Revisions processed: {len(revisions)}")
    print(f"Messages collected: {len(messages)}")
    print(f"Patch-file records: {len(patches)}")
    print(f"Errors recorded: {len(errors)}")

    print(f"\nOutput directory: {OUTPUT_DIR}")

    for path in [
        REVIEWS_FILE,
        REVISIONS_FILE,
        MESSAGES_FILE,
        PATCHES_FILE,
        ERRORS_FILE,
    ]:
        print(f"  {path.name}: {path.exists()}")


if __name__ == "__main__":
    main()