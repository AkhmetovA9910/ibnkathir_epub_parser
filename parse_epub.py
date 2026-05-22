"""Parse 'Коран. Тафсир ибн Касира' EPUB into a structured JSON file."""

from __future__ import annotations

import json
import re
import warnings
from pathlib import Path

import ebooklib
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from ebooklib import epub

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

EPUB_PATH = Path(__file__).parent / "Коран. Тафсир ибн Касира.epub"
OUTPUT_DIR = Path(__file__).parent / "output"

VERSE_NUM_RE = re.compile(r"^\s*(\d+)\s*:\s*(\d+)\s*$")
ARABIC_RE = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")


def text_of(tag) -> str:
    """Return tag text with collapsed whitespace."""
    return re.sub(r"\s+", " ", tag.get_text(" ", strip=True)).strip()


def is_arabic(s: str) -> bool:
    """True if the string contains Arabic characters."""
    return bool(ARABIC_RE.search(s))


def parse_verse(div) -> dict | None:
    """Extract one verse: number and tafsir paragraphs joined by newline."""
    paragraphs = div.find_all("p", recursive=False)
    if not paragraphs:
        return None

    number_raw = None
    skip_arabic = True
    tafsir: list[str] = []

    for i, p in enumerate(paragraphs):
        text = text_of(p)
        if not text:
            continue

        if i == 0 and p.find("strong"):
            number_raw = text_of(p.find("strong"))
            continue

        if skip_arabic and is_arabic(text):
            skip_arabic = False
            continue

        tafsir.append(text)

    if not number_raw:
        return None

    m = VERSE_NUM_RE.match(number_raw)
    sura_num = int(m.group(1)) if m else None
    ayat_num = int(m.group(2)) if m else None

    return {
        "sura": sura_num,
        "ayat": ayat_num,
        "text": "\n".join(tafsir),
    }


def parse_surah(doc_item) -> list[dict]:
    """Parse one surah document into a list of verse dicts."""
    soup = BeautifulSoup(doc_item.get_content(), "xml")
    if not soup.find("h1"):
        return []

    verses: list[dict] = []
    for vdiv in soup.find_all("div", class_="verse"):
        v = parse_verse(vdiv)
        if v:
            verses.append(v)

    return verses


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    book = epub.read_epub(str(EPUB_PATH))

    surah_map: dict[int, list[dict]] = {}
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        name = item.get_name()
        if not re.match(r"content/s\d+\.xhtml$", name):
            continue
        verses = parse_surah(item)
        if verses:
            sura_num = verses[0]["sura"]
            surah_map.setdefault(sura_num, []).extend(verses)

    for sura_num in sorted(surah_map):
        verses = surah_map[sura_num]
        out_file = OUTPUT_DIR / f"{sura_num:03d}.json"
        out_file.write_text(
            json.dumps(verses, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    total_verses = sum(len(v) for v in surah_map.values())
    print(f"Surahs parsed: {len(surah_map)}")
    print(f"Total verses:  {total_verses}")
    print(f"Output dir:    {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
