import csv
import json
import re
from pathlib import Path
from urllib.parse import urlparse, urlunparse


def normalize_url(url: str) -> str:
    """Normalize URLs for deduplication and cleaning."""
    if not url or not isinstance(url, str):
        return ""

    url = url.strip()
    url = re.sub(r"\[\.\]", ".", url)
    url = re.sub(r"\[dot\]", ".", url, flags=re.IGNORECASE)
    url = re.sub(r"\s+", "", url)

    parsed = urlparse(url)
    if not parsed.scheme:
        parsed = urlparse("http://" + url)

    if not parsed.netloc:
        return ""

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    if netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    path = parsed.path or "/"
    if path == "/":
        path = ""
    query = parsed.query
    fragment = ""

    cleaned = urlunparse((scheme, netloc, path, "", query, fragment))
    return cleaned


def clean_github_dataset1(input_path: Path, output_path: Path) -> None:
    """Clean github_dataset1.csv and save a normalized CSV copy."""
    with input_path.open("r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = ["url", "label"]
        rows = []
        seen = set()
        invalid_count = 0
        for row in reader:
            raw_url = row.get("url", "")
            url = normalize_url(raw_url)
            if not url:
                invalid_count += 1
                continue
            label = row.get("type", "").strip().lower()
            if label not in {"legitimate", "phishing"}:
                continue
            if url in seen:
                continue
            seen.add(url)
            rows.append({"url": url, "label": label})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as out_csv:
        writer = csv.DictWriter(out_csv, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Cleaned github_dataset1: {len(rows)} rows written, {invalid_count} invalid rows removed, {len(seen)} unique URLs.")


def clean_github_dataset_2(input_path: Path, output_path: Path) -> None:
    """Clean github_dataset_2.json and save a normalized JSON copy."""
    with input_path.open("r", encoding="utf-8") as infile:
        data = json.load(infile)

    cleaned_records = []
    seen = set()
    for record in data:
        raw_url = record.get("url", "")
        url = normalize_url(raw_url)
        if not url:
            continue
        if url in seen:
            continue
        seen.add(url)
        cleaned_records.append(
            {
                "url": url,
                "label": "phishing",
                "target": record.get("target", "Unknown"),
                "submission_time": record.get("submission_time", ""),
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as outfile:
        json.dump(cleaned_records, outfile, indent=2)

    print(
        f"Cleaned github_dataset_2: {len(cleaned_records)} records written, {len(data)-len(cleaned_records)} duplicate records removed.")


def main() -> None:
    base = Path(__file__).resolve().parent.parent
    raw_dir = base / "data" / "raw"
    out_dir = Path(__file__).resolve().parent

    clean_github_dataset1(
        raw_dir / "github_dataset1.csv",
        out_dir / "cleaned_github_dataset1.csv",
    )
    clean_github_dataset_2(
        raw_dir / "github_dataset_2.json",
        out_dir / "cleaned_github_dataset_2.json",
    )


if __name__ == "__main__":
    main()
