import base64
import csv
import json
import re
import time
from pathlib import Path
from urllib.parse import quote

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_CSV = PROJECT_ROOT / "data" / "gerrit" / "raw" / "couchbase-java-client.csv"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "gerrit"
    / "couchbase_java_client"
    / "collected"
    / "pilot"
)

GERRIT_BASE_URL = "https://review.couchbase.org"

# Test one review with multiple revisions and one abandoned review.
PILOT_REVIEW_NUMBERS = {"12050", "12027"}

REQUEST_DELAY_SECONDS = 0.5
REQUEST_TIMEOUT_SECONDS = 30

session = requests.Session()

session.headers.update({
    "Accept": "application/json",
    "User-Agent": "COMP4990B-Gerrit-Dataset-Research/1.0",
})

def normalize_key(value):
    """Normalize CSV column names for case-insensitive lookup."""
    return re.sub(r"[^a-z0-9]", "", value.lower())


def find_column(row, possible_names):
    """Find a CSV column using possible header names."""

    normalized = {
        normalize_key(key): key
        for key in row.keys()
        if key is not None
    }

    for name in possible_names:
        actual_key = normalized.get(normalize_key(name))

        if actual_key is not None:
            return row.get(actual_key, "").strip()

    raise KeyError(
        f"Could not find any of these CSV columns: {possible_names}"
    )


def load_pilot_records():
    """Load selected review revisions from the CROP CSV."""

    if not INPUT_CSV.exists():
        raise FileNotFoundError(
            f"Could not find input CSV: {INPUT_CSV}"
        )

    selected = []

    with INPUT_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        required_columns = {
            "review_number",
            "revision_number",
            "after_commit_id",
            "status",
        }

        actual_columns = {
            normalize_key(column)
            for column in (reader.fieldnames or [])
        }

        missing = {
            normalize_key(column)
            for column in required_columns
        } - actual_columns

        if missing:
            raise ValueError(
                f"CSV is missing required columns: {missing}. "
                f"Found: {reader.fieldnames}"
            )

        for row in reader:

            review_number = find_column(
                row, ["review_number"]
            )

            if review_number not in PILOT_REVIEW_NUMBERS:
                continue

            selected.append({
                "review_number": review_number,
                "revision_number": find_column(
                    row, ["revision_number"]
                ),
                "status": find_column(row, ["status"]),
                "change_id": find_column(row, ["change_id"]),
                "review_url": find_column(row, ["url"]),
                "before_commit_id": find_column(
                    row, ["before_commit_id"]
                ),
                "after_commit_id": find_column(
                    row, ["after_commit_id"]
                ),
            })

    return selected

def parse_response(response):
    """Parse JSON after removing Gerrit's XSSI prefix."""

    text = response.text

    if text.startswith(")]}'"):
        text = text.split("\n", 1)[1] if "\n" in text else ""

    if not text.strip():
        return None

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        return {
            "raw_response": text[:2000]
        }


def save_json(path, data):
    """Save data as formatted JSON."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )


def request_gerrit(endpoint, raw_text=False):
    """Make a public Gerrit API request."""

    url = f"{GERRIT_BASE_URL}{endpoint}"

    try:
        response = session.get(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS
        )

        result = {
            "url": url,
            "http_status": response.status_code,
            "success": response.ok,
        }

        if response.ok:

            if raw_text:
                result["data"] = response.text.strip()

            else:
                result["data"] = parse_response(response)

        else:
            result["error"] = response.text[:1000]

        return result

    except requests.RequestException as error:

        return {
            "url": url,
            "success": False,
            "error": str(error),
        }



# GERRIT API COLLECTION
def collect_review_revision(record):

    review_number = record["review_number"]
    revision_number = record["revision_number"]
    revision_hash = record["after_commit_id"]

    # Gerrit revision endpoints use the actual commit hash.
    if not re.fullmatch(r"[0-9a-fA-F]{40}", revision_hash):

        print(
            f"Skipping review {review_number}, "
            f"revision {revision_number}: invalid commit hash."
        )

        return None

    review_dir = OUTPUT_DIR / f"review_{review_number}"

    revision_dir = (
        review_dir / f"revision_{revision_number}"
    )

    print(
        f"\nTesting review {review_number}, "
        f"revision {revision_number}"
    )

    encoded_revision = quote(
        revision_hash,
        safe=""
    )

    detail = request_gerrit(
        f"/changes/{review_number}/detail"
        f"?o=MESSAGES&o=ALL_REVISIONS"
    )

    save_json(
        review_dir / "detail.json",
        detail
    )

    time.sleep(REQUEST_DELAY_SECONDS)

    comments = request_gerrit(
        f"/changes/{review_number}/revisions/"
        f"{encoded_revision}/comments"
    )

    save_json(
        revision_dir / "comments.json",
        comments
    )

    time.sleep(REQUEST_DELAY_SECONDS)

    changed_files = request_gerrit(
        f"/changes/{review_number}/revisions/"
        f"{encoded_revision}/files/"
    )

    save_json(
        revision_dir / "changed_files.json",
        changed_files
    )

    time.sleep(REQUEST_DELAY_SECONDS)
    patch = request_gerrit(
        f"/changes/{review_number}/revisions/"
        f"{encoded_revision}/patch",
        raw_text=True
    )

    if patch.get("success"):

        try:
            decoded_patch = base64.b64decode(
                patch["data"],
                validate=True
            ).decode(
                "utf-8",
                errors="replace"
            )

            patch_path = revision_dir / "patch.diff"

            patch_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            patch_path.write_text(
                decoded_patch,
                encoding="utf-8"
            )

        except Exception as error:

            patch["decode_error"] = str(error)

    save_json(
        revision_dir / "patch_response.json",
        patch
    )

    results = {
        "review_number": review_number,
        "revision_number": revision_number,
        "status_in_crop": record["status"],
        "after_commit_id": revision_hash,

        "detail_success": detail.get("success", False),
        "comments_success": comments.get("success", False),
        "changed_files_success": changed_files.get(
            "success", False
        ),
        "patch_success": patch.get("success", False),

        "detail_http_status": detail.get("http_status"),
        "comments_http_status": comments.get("http_status"),
        "changed_files_http_status": changed_files.get(
            "http_status"
        ),
        "patch_http_status": patch.get("http_status"),

        "patch_file_created": (
            revision_dir / "patch.diff"
        ).exists(),
    }

    print(json.dumps(results, indent=2))

    return results

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    records = load_pilot_records()

    if not records:
        print("No pilot records found.")
        return

    print("=" * 55)
    print("COUCHBASE GERRIT API PILOT")
    print("=" * 55)

    print(f"Input CSV: {INPUT_CSV}")
    print(f"Pilot revision records: {len(records)}")

    results = []

    for record in records:

        result = collect_review_revision(record)

        if result is not None:
            results.append(result)

    report_path = OUTPUT_DIR / "pilot_report.json"

    save_json(
        report_path,
        results
    )

    print("\n" + "=" * 55)
    print("GERRIT PILOT COMPLETE")
    print("=" * 55)

    print(f"Revision records tested: {len(results)}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Report: {report_path}")

    print("\nRequest success summary:")

    for field in [
        "detail_success",
        "comments_success",
        "changed_files_success",
        "patch_success",
    ]:

        successful = sum(
            1 for result in results
            if result.get(field)
        )

        print(
            f"{field}: {successful}/{len(results)}"
        )


if __name__ == "__main__":
    main()