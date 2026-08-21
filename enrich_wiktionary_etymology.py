#!/usr/bin/env python3
"""Enrich a study CSV with English Wiktionary etymologies via Wiktextract.

The Kaikki/Wiktextract JSONL stream is processed without saving the multi-GB
source archive locally. Only target words from the input CSV are parsed and
written. Reused text remains under Wiktionary's CC BY-SA 4.0 license.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path


WIKTEXTRACT_URL = "https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl"
LICENSE = "CC BY-SA 4.0"
SOURCE_BASE = "https://en.wiktionary.org/wiki/"
MAX_TEXT_LENGTH = 700
WORD_PATTERN = re.compile(
    rb'"word"\s*:\s*"([^"\\]+)"\s*,\s*"lang"\s*:\s*"English"\s*,\s*"lang_code"\s*:\s*"en"'
)


def compact_text(text: str, word: str) -> str:
    text = text.strip()
    text = re.sub(
        rf"(?:PIE word[^\n]*(?:\n|\s+))?Etymology tree.*?English\s+{re.escape(word)}(?![A-Za-z'-])\s*",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(r"(?:PIE word[^\n]*(?:\n|\s+))?Etymology tree.*$", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(
        rf"^English\s+{re.escape(word)}\s*(?=(?:From|Inherited|Borrowed|Learned|Back|Calque|Clipping|Blend|Coined|②))",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\s+", " ", text).strip()
    text = text.removeprefix("② ").strip()
    normalized = text.casefold().rstrip(".")
    if normalized in {"", word.casefold(), f"from {word.casefold()}", f"see {word.casefold()}"}:
        return ""
    if re.fullmatch(r"from the (?:noun|verb|adjective|adverb).?", text, re.IGNORECASE):
        return ""
    if len(text) <= MAX_TEXT_LENGTH:
        return text
    shortened = text[: MAX_TEXT_LENGTH + 1].rsplit(" ", 1)[0].rstrip(" ,;:")
    return shortened + "…"


def stream_etymologies(url: str, targets: set[str]) -> tuple[dict[str, list[str]], str]:
    found: dict[str, list[str]] = defaultdict(list)
    request = urllib.request.Request(url, headers={"User-Agent": "Easymean_vocab-builder/1.0"})
    processed = 0
    next_report = 256 * 1024 * 1024
    with urllib.request.urlopen(request, timeout=120) as response:
        snapshot = response.headers.get("Last-Modified", "")
        for line in response:
            processed += len(line)
            if processed >= next_report:
                print(
                    f"Processed {processed / 1024 / 1024:.0f} MiB; "
                    f"matched {len(found):,}/{len(targets):,} target words...",
                    flush=True,
                )
                next_report += 256 * 1024 * 1024
            match = WORD_PATTERN.search(line)
            if not match:
                continue
            try:
                word = match.group(1).decode("utf-8").casefold()
            except UnicodeDecodeError:
                continue
            if word not in targets or b'"lang_code": "en"' not in line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(entry.get("word") or "").casefold() != word or entry.get("lang_code") != "en":
                continue
            text = compact_text(str(entry.get("etymology_text") or ""), str(entry.get("word") or word))
            if text and text not in found[word] and len(found[word]) < 2:
                found[word].append(text)
    return dict(found), snapshot


def enrich(input_path: Path, output_path: Path, url: str) -> tuple[int, int, str]:
    with input_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if "word" not in fields:
        raise ValueError("Input CSV has no word column")
    for field in ("etymology", "etymology_source", "etymology_license"):
        if field not in fields:
            fields.append(field)

    targets = {row.get("word", "").strip().casefold() for row in rows if row.get("word", "").strip()}
    etymologies, snapshot = stream_etymologies(url, targets)
    matched = 0
    for row in rows:
        word = row.get("word", "").strip()
        texts = etymologies.get(word.casefold(), [])
        if not texts:
            continue
        row["etymology"] = " ② ".join(texts) if len(texts) > 1 else texts[0]
        row["etymology_source"] = SOURCE_BASE + urllib.parse.quote(word.replace(" ", "_"), safe="-_()'")
        row["etymology_license"] = LICENSE
        matched += 1

    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(output_path)
    return len(rows), matched, snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("us_core_7000_authentic.csv"))
    parser.add_argument("--output", type=Path, default=Path("us_core_7000_authentic.csv"))
    parser.add_argument("--url", default=WIKTEXTRACT_URL)
    args = parser.parse_args()
    if not args.input.is_file():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 2
    try:
        total, matched, snapshot = enrich(args.input, args.output, args.url)
    except Exception as exc:
        print(f"Etymology enrichment failed: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {total:,} rows; Wiktionary etymology coverage: {matched:,} ({matched / total:.1%}).")
    if snapshot:
        print(f"Kaikki snapshot Last-Modified: {snapshot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
