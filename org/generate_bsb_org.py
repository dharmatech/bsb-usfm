#!/usr/bin/env python3
"""
Generate an Org Mode version of the Berean Standard Bible from the USFM source files.
"""
import argparse
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_USFM_DIR = PROJECT_ROOT / "usfm"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "bsb.org"

FOOTNOTE_RE = re.compile(r'\\f.*?\\f\*', re.DOTALL)
CROSS_REF_RE = re.compile(r'\\x.*?\\x\*', re.DOTALL)
INLINE_MARKER_RE = re.compile(r'\\(add|bd|bk|em|it|k|nd|pn|qac|sc|sig|tl|wj)\*?')

PARAGRAPH_RE = re.compile(r'\\(p|nb|b)(\s+|$)')

TITLE_RE = re.compile(r'\\(h|toc1|toc2|mt1)\s+(.*)')
SECTION_RE = re.compile(r'\\s(\d*)\s+(.*)')
VERSE_RE = re.compile(r'\\v\s+(\d+)\s+(.*)')
CHAPTER_RE = re.compile(r'\\c\s+(\d+)')
SECTION_REF_RE = re.compile(r'\\r\s+(.*)')
MAJOR_SECTION_RE = re.compile(r'\\m[rs]\s+(.*)')
CONTINUATION_RE = re.compile(r'\\(q\d+|qr|li\d+|pc|pmo|m)\s*(.*)')
ACROSTIC_RE = re.compile(r'\\qa\s+(.*)')
DESCRIPTION_RE = re.compile(r'\\d\s+(.*)')

def clean_text(text: str) -> str:
    """Strip USFM inline markup and footnotes down to readable text."""
    text = FOOTNOTE_RE.sub('', text)
    text = CROSS_REF_RE.sub('', text)
    text = INLINE_MARKER_RE.sub('', text)
    text = text.replace('\\*', '')
    text = text.replace('\\+', '')
    return re.sub(r'\s+', ' ', text).strip()

def append_fragment(fragment: str, prefer_newline: bool, items, current_verse):
    if not fragment:
        return current_verse
    if current_verse is not None:
        if current_verse[1]:
            separator = '\n' if prefer_newline else ' '
            current_verse[1] = f"{current_verse[1]}{separator}{fragment}"
        else:
            current_verse[1] = fragment
    elif items is not None:
        items.append(("paragraph", fragment))
    return current_verse

def parse_usfm(path: Path) -> dict:
    book_title = None
    chapters = []
    current_items = None
    current_verse = None

    def flush_verse():
        nonlocal current_verse
        if current_verse and current_items is not None:
            num, text = current_verse
            if text:
                current_items.append(("verse", num, text.strip()))
        current_verse = None

    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if (m := TITLE_RE.match(line)):
            if not book_title:
                book_title = clean_text(m.group(2))
            continue

        if (m := CHAPTER_RE.match(line)):
            flush_verse()
            current_items = []
            chapters.append({"number": int(m.group(1)), "items": current_items})
            continue

        if current_items is None:
            continue

        if (m := SECTION_RE.match(line)):
            flush_verse()
            level = int(m.group(1) or 1)
            title = clean_text(m.group(2))
            if title:
                current_items.append(("section", level, title))
            continue

        if (m := MAJOR_SECTION_RE.match(line)):
            flush_verse()
            title = clean_text(m.group(1))
            if title:
                current_items.append(("section", 1, title))
            continue

        if (m := PARAGRAPH_RE.match(line)):
            flush_verse()
            current_items.append(("paragraph_break",))
            continue

        if (m := SECTION_REF_RE.match(line)):
            ref = clean_text(m.group(1))
            if ref and current_items and current_items[-1][0] == "section":
                kind, lvl, title = current_items[-1]
                ref_text = ref[1:-1].strip() if ref.startswith("(") and ref.endswith(")") else ref
                current_items[-1] = (kind, lvl, f"{title} ({ref_text})")
            continue

        if (m := DESCRIPTION_RE.match(line)):
            desc = clean_text(m.group(1))
            if desc:
                current_items.append(("paragraph", desc))
            continue

        if (m := VERSE_RE.match(line)):
            flush_verse()
            current_verse = [m.group(1), clean_text(m.group(2))]
            continue

        if (m := ACROSTIC_RE.match(line)):
            frag = clean_text(m.group(1))
            current_verse = append_fragment(frag, True, current_items, current_verse)
            continue

        if (m := CONTINUATION_RE.match(line)):
            marker, frag = m.groups()
            frag = clean_text(frag)
            
            if not frag and marker in ('m', 'pmo', 'pc'):
                flush_verse()
                current_items.append(("paragraph_break",))
                continue

            prefer_newline = marker.startswith('q') or marker.startswith('li') or marker in ('qr', 'pc')
            current_verse = append_fragment(frag, prefer_newline, current_items, current_verse)
            continue

    flush_verse()
    if not book_title:
        book_title = path.stem
    return {"title": book_title, "chapters": chapters}

def render_org(books, output_path: Path) -> None:
    lines = [
        "#+title: Berean Standard Bible",
        "#+language: en",
        "#+creator: generate_bsb_org.py",
        "",
    ]

    for book in books:
        lines.append(f"* {book['title']}")
        for chapter in book["chapters"]:
            lines.append(f"** Chapter {chapter['number']}")
            
            verse_buffer = []
            def flush_buffer():
                if verse_buffer:
                    lines.append(" ".join(verse_buffer))
                    verse_buffer.clear()

            for item in chapter["items"]:
                kind = item[0]
                if kind == "verse":
                    _, num, text = item
                    verse_buffer.append(f"{num} {text}")
                else:
                    flush_buffer()
                    if kind == "section":
                        _, level, title = item
                        stars = "*" * (2 + level)
                        lines.append(f"{stars} {title}")
                    elif kind == "paragraph":
                        lines.append(item[1])
                    elif kind == "paragraph_break":
                        lines.append("")
            
            flush_buffer()
            lines.append("")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(lines).rstrip() + "\n"
    output_path.write_text(content, encoding="utf-8")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usfm-dir", type=Path, default=DEFAULT_USFM_DIR, help="Directory containing *.SFM files")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Where to write the Org file")
    return parser

def main() -> None:
    args = build_parser().parse_args()
    usfm_dir = args.usfm_dir
    if not usfm_dir.exists():
        raise SystemExit(f"USFM directory not found: {usfm_dir}")

    usfm_files = sorted(usfm_dir.glob("*.SFM"))
    if not usfm_files:
        raise SystemExit(f"No .SFM files found in {usfm_dir}")

    books = [parse_usfm(path) for path in usfm_files]
    render_org(books, args.output)
    print(f"Wrote {args.output} from {len(books)} books.")

if __name__ == "__main__":
    main()
