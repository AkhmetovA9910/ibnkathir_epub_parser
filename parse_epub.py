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
OUTPUT_PATH = Path(__file__).parent / "tafsir_ibn_kathir.json"

VERSE_NUM_RE = re.compile(r"^\s*(\d+)\s*:\s*(\d+)\s*$")
ARABIC_RE = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")


def text_of(tag) -> str:
    """Return tag text with collapsed whitespace."""
    return re.sub(r"\s+", " ", tag.get_text(" ", strip=True)).strip()


def is_arabic(s: str) -> bool:
    """True if the string contains Arabic characters."""
    return bool(ARABIC_RE.search(s))


def parse_verse(div) -> dict | None:
    """Extract one verse: number, arabic text, list of tafsir paragraphs."""
    paragraphs = div.find_all("p", recursive=False)
    if not paragraphs:
        return None

    number_raw = None
    arabic = ""
    tafsir: list[str] = []

    for i, p in enumerate(paragraphs):
        text = text_of(p)
        if not text:
            continue

        if i == 0 and p.find("strong"):
            number_raw = text_of(p.find("strong"))
            continue

        if not arabic and is_arabic(text):
            arabic = text
            continue

        tafsir.append(text)

    if not number_raw:
        return None

    m = VERSE_NUM_RE.match(number_raw)
    surah_num = int(m.group(1)) if m else None
    ayah_num = int(m.group(2)) if m else None

    return {
        "reference": number_raw,
        "surah": surah_num,
        "ayah": ayah_num,
        "arabic": arabic,
        "tafsir": tafsir,
    }


def parse_surah(doc_item) -> dict | None:
    """Parse one surah document into a dict."""
    soup = BeautifulSoup(doc_item.get_content(), "xml")
    h1 = soup.find("h1")
    if not h1:
        return None
    title = text_of(h1)

    verses: list[dict] = []
    for vdiv in soup.find_all("div", class_="verse"):
        v = parse_verse(vdiv)
        if v:
            verses.append(v)

    if not verses:
        return None

    surah_number = verses[0]["surah"]
    name_ru, name_translit = title, None
    m = re.match(r"^(.*?)\s*\((.+)\)\s*$", title)
    if m:
        name_ru, name_translit = m.group(1).strip(), m.group(2).strip()

    return {
        "number": surah_number,
        "title": title,
        "name_ru": name_ru,
        "name_translit": name_translit,
        "verses_count": len(verses),
        "verses": verses,
    }


def main() -> None:
    book = epub.read_epub(str(EPUB_PATH))

    def meta(field: str) -> str | None:
        items = book.get_metadata("DC", field)
        return items[0][0] if items else None

    surahs: list[dict] = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        name = item.get_name()
        if not re.match(r"content/s\d+\.xhtml$", name):
            continue
        surah = parse_surah(item)
        if surah:
            surahs.append(surah)

    surahs.sort(key=lambda s: s["number"])

    result = {
        "title": meta("title"),
        "author": meta("creator"),
        "language": meta("language"),
        "surahs_count": len(surahs),
        "surahs": surahs,
    }

    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    total_verses = sum(s["verses_count"] for s in surahs)
    print(f"Surahs parsed: {len(surahs)}")
    print(f"Total verses:  {total_verses}")
    print(f"Output:        {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
