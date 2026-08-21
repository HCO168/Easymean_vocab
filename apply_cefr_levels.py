#!/usr/bin/env python3
"""Add Oxford American 3000/5000 CEFR guidance to the local study deck.

Oxford aligns the American Oxford 3000 to A1-B2 and the additional Oxford
5000 entries to B2-C1. Words outside those lists are labeled "Beyond C1"
instead of being falsely classified as C2.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import urllib.request
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - user-facing dependency guidance
    print("Missing dependency: pypdf. Install it with: python3 -m pip install pypdf", file=sys.stderr)
    raise SystemExit(2)


PDF_URLS = (
    "https://www.oxfordlearnersdictionaries.com/external/pdf/wordlists/oxford-3000-5000/American_Oxford_3000_by_CEFR_level.pdf",
    "https://www.oxfordlearnersdictionaries.com/us/external/pdf/wordlists/oxford-3000-5000/American_Oxford_5000_by_CEFR_level.pdf",
)
LEVEL_ORDER = {"A1": 0, "A2": 1, "B1": 2, "B2": 3, "C1": 4}
POS_MARKER = re.compile(
    r"^(.+?)\s+(?:indefinite article|ordinal number|number|modal v\.|auxiliary v\.|"
    r"definite article|n\.|v[.,]|adj\.|adv\.|prep\.|conj\.|pron\.|det\.|exclam\.|art\.)",
    re.IGNORECASE,
)


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "vocab-coach-builder/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def parse_pdf(data: bytes) -> list[tuple[str, str]]:
    level = None
    entries: list[tuple[str, str]] = []
    for page in PdfReader(io.BytesIO(data)).pages:
        for raw_line in (page.extract_text() or "").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if re.fullmatch(r"[ABC][12]", line):
                level = line
                continue

            next_level = None
            trailing = re.search(r"\s([ABC][12])$", line)
            if trailing:
                next_level = trailing.group(1)
                line = line[: trailing.start()].strip()

            match = POS_MARKER.match(line)
            if match and level:
                head = re.sub(r"\s*\([^)]*\)", "", match.group(1).strip())
                head = re.sub(r"\d+$", "", head)
                for word in re.split(r"\s*,\s*", head):
                    if re.fullmatch(r"[A-Za-z]+(?:[-'][A-Za-z]+)?", word):
                        entries.append((word.casefold(), level))
            if next_level:
                level = next_level
    return entries


def build_level_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for url in PDF_URLS:
        for word, level in parse_pdf(download(url)):
            current = mapping.get(word)
            if current is None or LEVEL_ORDER[level] < LEVEL_ORDER[current]:
                mapping[word] = level
    return mapping


def apply_levels(input_path: Path, output_path: Path) -> tuple[int, int, dict[str, int]]:
    mapping = build_level_map()
    with input_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if "word" not in fields:
        raise ValueError("Input CSV has no word column")
    if "level" not in fields:
        meaning_index = fields.index("meaning") if "meaning" in fields else len(fields) - 1
        fields.insert(meaning_index + 1, "level")

    counts = {level: 0 for level in (*LEVEL_ORDER, "Beyond C1")}
    matched = 0
    aliases = {"the": "A1", "these": "A1", "those": "A1"}

    def inferred_level(row: dict[str, str]) -> str:
        word = row.get("word", "").strip().casefold()
        if word in mapping:
            return mapping[word]
        if word in aliases:
            return aliases[word]
        base_word = row.get("base_word", "").strip().casefold()
        if base_word in mapping:
            return mapping[base_word]
        candidates = []
        if word.endswith("ies"):
            candidates.append(word[:-3] + "y")
        if word.endswith("es"):
            candidates.extend((word[:-2], word[:-1]))
        if word.endswith("s"):
            candidates.append(word[:-1])
        if word.endswith("ied"):
            candidates.append(word[:-3] + "y")
        if word.endswith("ed"):
            candidates.extend((word[:-2], word[:-1]))
        if word.endswith("ing"):
            candidates.extend((word[:-3], word[:-3] + "e"))
        if word.endswith("est"):
            candidates.append(word[:-3])
        if word.endswith("er"):
            candidates.append(word[:-2])
        for candidate in candidates:
            if candidate in mapping:
                return mapping[candidate]
        return "Beyond C1"

    for row in rows:
        level = inferred_level(row)
        row["level"] = level
        counts[level] += 1
        matched += level != "Beyond C1"

    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(output_path)
    return len(rows), matched, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("us_core_7000_authentic.csv"))
    parser.add_argument("--output", type=Path, default=Path("us_core_7000_authentic.csv"))
    args = parser.parse_args()
    if not args.input.is_file():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 2
    try:
        total, matched, counts = apply_levels(args.input, args.output)
    except Exception as exc:
        print(f"Leveling failed: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote CEFR guidance for {total} words; Oxford list matches: {matched}.")
    print("Level counts: " + ", ".join(f"{key}={value}" for key, value in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
