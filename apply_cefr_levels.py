#!/usr/bin/env python3
"""Add conservative, source-backed CEFR guidance to the local study deck.

Oxford aligns the American Oxford 3000 to A1-B2 and the additional Oxford
5000 entries to B2-C1. CEFR-J fills gaps at A1-B2, and the Octanove C1/C2
profile supplies explicit advanced labels. Unmatched words remain "Unrated"
instead of being falsely classified as beyond C1.
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
CEFRJ_URL = "https://raw.githubusercontent.com/openlanguageprofiles/olp-en-cefrj/master/cefrj-vocabulary-profile-1.5.csv"
OCTANOVE_URL = "https://raw.githubusercontent.com/openlanguageprofiles/olp-en-cefrj/master/octanove-vocabulary-profile-c1c2-1.0.csv"
LEVEL_ORDER = {"A1": 0, "A2": 1, "B1": 2, "B2": 3, "C1": 4, "Beyond C1": 5}
SOURCE_OXFORD = "Oxford 3000/5000"
SOURCE_CEFRJ = "CEFR-J Wordlist 1.5"
SOURCE_OCTANOVE = "Octanove C1/C2 1.0"
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


def parse_profile_csv(data: bytes, source: str) -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    for row in reader:
        raw_level = row.get("CEFR", "").strip().upper()
        level = "Beyond C1" if raw_level == "C2" else raw_level
        if level not in LEVEL_ORDER:
            continue
        headword = re.sub(r"\s*\([^)]*\)", "", row.get("headword", ""))
        for variant in re.split(r"\s*[/,]\s*", headword):
            word = variant.strip().casefold()
            if word:
                entries.append((word, level, source))
    return entries


def build_level_map() -> dict[str, tuple[str, str]]:
    mapping: dict[str, tuple[str, str]] = {}
    for url in PDF_URLS:
        for word, level in parse_pdf(download(url)):
            current = mapping.get(word)
            if current is None or LEVEL_ORDER[level] < LEVEL_ORDER[current[0]]:
                mapping[word] = (level, SOURCE_OXFORD)
    for url, source in ((CEFRJ_URL, SOURCE_CEFRJ), (OCTANOVE_URL, SOURCE_OCTANOVE)):
        for word, level, entry_source in parse_profile_csv(download(url), source):
            if word not in mapping:
                mapping[word] = (level, entry_source)
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
    if "level_source" not in fields:
        fields.insert(fields.index("level") + 1, "level_source")
    if "placement_eligible" not in fields:
        fields.insert(fields.index("level_source") + 1, "placement_eligible")

    counts = {level: 0 for level in (*LEVEL_ORDER, "Unrated")}
    matched = 0
    aliases = {"the": ("A1", SOURCE_OXFORD), "these": ("A1", SOURCE_OXFORD), "those": ("A1", SOURCE_OXFORD)}

    def inferred_level(row: dict[str, str]) -> tuple[str, str]:
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
        return "Unrated", "No match in Oxford, CEFR-J, or Octanove"

    for row in rows:
        level, source = inferred_level(row)
        row["level"] = level
        row["level_source"] = source
        row["placement_eligible"] = "true" if source in {SOURCE_OXFORD, SOURCE_OCTANOVE} else "false"
        counts[level] += 1
        matched += level != "Unrated"

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
    print(f"Wrote source-backed CEFR guidance for {total} words; classified: {matched}.")
    print("Level counts: " + ", ".join(f"{key}={value}" for key, value in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
