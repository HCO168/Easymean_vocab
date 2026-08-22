#!/usr/bin/env python3
"""Add concise, attributable English-Chinese examples from Tatoeba."""

from __future__ import annotations

import argparse
import csv
import io
import re
import urllib.request
import zipfile
from pathlib import Path


TATOEBA_ARCHIVE = "https://www.manythings.org/anki/cmn-eng.zip"
LICENSE = "CC BY 2.0 FR"
SOURCE_BASE = "https://tatoeba.org/en/sentences/show/"
TRADITIONAL_HINTS = set("這個們來說學國為時會裡見過對與實於從還沒樣點開關問讓體錯誤歡覺應該麼話書車買賣發現長間後無萬東專業進將種頭現動嗎")
UNSUITABLE = re.compile(r"\b(?:suicide|kill(?:ed|ing|s)?|murder(?:ed|ing|s)?|porn|rape(?:d|s)?|nazi|terrorist)\b", re.I)


def download_pairs(url: str) -> list[tuple[str, str, str]]:
    request = urllib.request.Request(url, headers={"User-Agent": "MeanEase-builder/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        archive = response.read()
    with zipfile.ZipFile(io.BytesIO(archive)) as package:
        filename = next(name for name in package.namelist() if name.endswith("cmn.txt"))
        lines = package.read(filename).decode("utf-8").splitlines()
    pairs = []
    for line in lines:
        parts = line.split("\t")
        if len(parts) >= 3:
            pairs.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))
    return pairs


def source_url(credit: str) -> str:
    match = re.search(r"tatoeba\.org\s+#(\d+)", credit, re.I)
    return SOURCE_BASE + match.group(1) if match else "https://tatoeba.org/"


def sentence_score(english: str, chinese: str, word: str) -> tuple[int, int, int, str]:
    tokens = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", english.casefold())
    traditional = sum(character in TRADITIONAL_HINTS for character in chinese)
    return traditional, abs(len(tokens) - 7), len(english), english


def enrich(input_path: Path, output_path: Path, url: str) -> tuple[int, int]:
    with input_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle); rows = list(reader); fields = list(reader.fieldnames or [])
    for field in ("example_source", "example_license"):
        if field not in fields:
            fields.append(field)
    targets = {row.get("word", "").strip().casefold() for row in rows if row.get("word", "").strip()}
    best: dict[str, tuple[tuple[int, int, int, str], str, str, str]] = {}
    for english, chinese, credit in download_pairs(url):
        tokens = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", english.casefold())
        if not 3 <= len(tokens) <= 16 or not re.search(r"[\u3400-\u9fff]", chinese) or UNSUITABLE.search(english):
            continue
        for word in set(tokens) & targets:
            score = sentence_score(english, chinese, word)
            if word not in best or score < best[word][0]:
                best[word] = (score, english, chinese, source_url(credit))
    matched = 0
    for row in rows:
        example = best.get(row.get("word", "").strip().casefold())
        if not example:
            row["example_en"] = row["example_zh"] = row["example_source"] = row["example_license"] = ""
            continue
        _, row["example_en"], row["example_zh"], row["example_source"] = example
        row["example_license"] = LICENSE; matched += 1
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    temporary.replace(output_path)
    return len(rows), matched


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("us_core_7000_authentic.csv"))
    parser.add_argument("--output", type=Path, default=Path("us_core_7000_authentic.csv"))
    parser.add_argument("--url", default=TATOEBA_ARCHIVE)
    args = parser.parse_args()
    total, matched = enrich(args.input, args.output, args.url)
    print(f"Wrote {total:,} rows; attributable bilingual examples: {matched:,} ({matched / total:.1%}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
