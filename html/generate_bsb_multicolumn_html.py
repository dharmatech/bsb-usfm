#!/usr/bin/env python3
"""
Generate a multi-column HTML version of the Berean Standard Bible from the USFM source files.
"""
from __future__ import annotations

import argparse
import html as html_lib
from pathlib import Path

from generate_bsb_html import DEFAULT_USFM_DIR, parse_usfm

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "bsb-4col.html"


def render_multicolumn_html(books, output_path: Path, column_count: int) -> None:
    column_count = max(1, column_count)
    html_parts = []
    html_parts.append(
        f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<title>Berean Standard Bible - Multi Column</title>
<style>
@import url(\"https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Fraunces:wght@600&display=swap\");

:root {{
  --bg: #0b0f14;
  --bg-alt: #111827;
  --text: #e3e7ef;
  --muted: #9aa5b1;
  --accent: #7dd3fc;
  --accent-soft: rgba(125, 211, 252, 0.15);
  --rule: rgba(255, 255, 255, 0.08);
  --header-height: 72px;
  --column-count: {column_count};
  --column-gap: 2.5rem;
}}

* {{
  box-sizing: border-box;
}}

html, body {{
  height: 100%;
}}

body {{
  margin: 0;
  font-family: \"Space Mono\", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, \"Liberation Mono\", \"Courier New\", monospace;
  color: var(--text);
  background:
    radial-gradient(1100px 600px at 15% -10%, rgba(125, 211, 252, 0.18), transparent 60%),
    radial-gradient(900px 500px at 110% 5%, rgba(250, 204, 21, 0.08), transparent 55%),
    linear-gradient(160deg, #0b0f14 0%, #0a0e13 40%, #0b0d12 100%);
  overflow: hidden;
}}

body::before {{
  content: \"\";
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(120deg, rgba(255, 255, 255, 0.04) 0%, rgba(255, 255, 255, 0.0) 55%),
    repeating-linear-gradient(
      90deg,
      rgba(255, 255, 255, 0.025) 0,
      rgba(255, 255, 255, 0.025) 1px,
      transparent 1px,
      transparent 32px
    );
  opacity: 0.4;
  pointer-events: none;
}}

.topbar {{
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2.5rem;
  background: rgba(10, 12, 18, 0.88);
  border-bottom: 1px solid var(--rule);
  backdrop-filter: blur(8px);
  z-index: 2;
  animation: rise 0.6s ease-out;
}}

.topbar-title {{
  font-family: \"Fraunces\", \"Georgia\", serif;
  font-size: 1.25rem;
  letter-spacing: 0.02em;
  color: var(--accent);
}}

.topbar-subtitle {{
  margin-top: 0.2rem;
  font-size: 0.8rem;
  color: var(--muted);
}}

.topbar-left {{
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}}

.topbar-right {{
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.8rem;
  color: var(--muted);
}}

.topbar-chip {{
  border: 1px solid var(--rule);
  border-radius: 999px;
  padding: 0.25rem 0.75rem;
  background: rgba(12, 16, 24, 0.6);
}}

.reader {{
  height: calc(100vh - var(--header-height));
  margin-top: var(--header-height);
  padding: 1.6rem 2.5rem 3rem;
  overflow-y: auto;
  column-count: var(--column-count);
  column-gap: var(--column-gap);
  column-rule: 1px solid var(--rule);
  column-fill: auto;
  animation: fadeIn 0.8s ease-out;
}}

.book {{
  break-inside: auto;
}}

.book-title {{
  display: block;
  margin: 1.4rem 0 0.5rem;
  font-family: \"Fraunces\", \"Georgia\", serif;
  font-size: 1.6rem;
  letter-spacing: 0.03em;
  color: var(--accent);
  break-after: avoid;
}}

.chapter-title {{
  display: block;
  margin: 1.1rem 0 0.4rem;
  font-size: 0.95rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--muted);
  break-after: avoid;
}}

.section-title {{
  display: block;
  margin: 0.9rem 0 0.25rem;
  font-size: 1rem;
  color: #f8d477;
  break-after: avoid;
}}

.section-ref {{
  margin: 0 0 0.75rem;
  font-size: 0.8rem;
  color: var(--muted);
  font-style: italic;
}}

p {{
  margin: 0 0 0.85rem;
  line-height: 1.55;
}}

.verse {{
  display: inline;
}}

.verse-num {{
  font-size: 0.68em;
  vertical-align: text-top;
  color: #9fb6c8;
  margin-right: 0.25em;
  font-weight: 700;
  user-select: none;
}}

.instruction {{
  font-style: italic;
  color: var(--muted);
}}

details {{
  break-inside: auto;
}}

summary {{
  list-style: none;
  cursor: pointer;
  outline: none;
  break-inside: avoid;
}}

summary::-webkit-details-marker {{
  display: none;
}}

summary::before {{
  content: \">\";
  display: inline-block;
  margin-right: 0.6rem;
  color: var(--muted);
  transition: transform 0.2s ease, color 0.2s ease;
}}

details[open] > summary::before {{
  transform: rotate(90deg);
  color: var(--accent);
}}

summary:hover {{
  color: var(--accent);
}}

@keyframes rise {{
  from {{
    opacity: 0;
    transform: translateY(10px);
  }}
  to {{
    opacity: 1;
    transform: translateY(0);
  }}
}}

@keyframes fadeIn {{
  from {{
    opacity: 0;
  }}
  to {{
    opacity: 1;
  }}
}}

@media (max-width: 1500px) {{
  :root {{
    --column-count: 3;
  }}
}}

@media (max-width: 1200px) {{
  :root {{
    --column-count: 2;
  }}
}}

@media (max-width: 900px) {{
  :root {{
    --column-count: 1;
  }}

  .topbar {{
    height: auto;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 1rem 1.25rem;
  }}

  .reader {{
    margin-top: 0;
    height: calc(100vh - 110px);
    padding: 1.2rem 1.4rem 2rem;
  }}

  .topbar-right {{
    flex-wrap: wrap;
  }}
}}
</style>
</head>
<body>
<header class=\"topbar\">
  <div class=\"topbar-left\">
    <div class=\"topbar-title\">Berean Standard Bible</div>
    <div class=\"topbar-subtitle\">Multi-column reading view</div>
  </div>
  <div class=\"topbar-right\">
    <div class=\"topbar-chip\">Columns: {column_count}</div>
    <div class=\"topbar-chip\">Flow left-to-right across columns</div>
  </div>
</header>
<main id=\"reader\" class=\"reader\">
"""
    )

    for book in books:
        safe_id = book["id"]
        book_title = html_lib.escape(book["title"])
        html_parts.append(f'  <details class="book" id="{safe_id}">\n')
        html_parts.append(f'    <summary class="book-title">{book_title}</summary>\n')

        for chapter in book["chapters"]:
            chap_num = chapter["number"]
            html_parts.append('    <details class="chapter">\n')
            html_parts.append(f'      <summary class="chapter-title">Chapter {chap_num}</summary>\n')

            paragraph_buffer = []
            current_section_open = False

            def paragraph_indent() -> str:
                return "        " if current_section_open else "      "

            def flush_paragraph():
                if paragraph_buffer:
                    content = "".join(paragraph_buffer)
                    html_parts.append(f'{paragraph_indent()}<p>{content}</p>\n')
                    paragraph_buffer.clear()

            def close_current_section():
                nonlocal current_section_open
                if current_section_open:
                    flush_paragraph()
                    html_parts.append("      </details>\n")
                    current_section_open = False

            for item in chapter["items"]:
                kind = item[0]

                if kind == "section":
                    close_current_section()
                    _, _level, title, ref_text = item
                    safe_title = html_lib.escape(title)
                    html_parts.append('      <details class="section">\n')
                    html_parts.append(f'        <summary class="section-title">{safe_title}</summary>\n')
                    if ref_text:
                        safe_ref = html_lib.escape(ref_text)
                        html_parts.append(f'        <div class="section-ref">({safe_ref})</div>\n')
                    current_section_open = True
                elif kind == "verse":
                    _, num, text = item
                    text = html_lib.escape(text).replace("\n", "<br>")
                    paragraph_buffer.append(
                        f'<span class="verse"><sup class="verse-num">{num}</sup>{text}</span> '
                    )
                elif kind == "paragraph_break":
                    flush_paragraph()
                elif kind == "paragraph":
                    flush_paragraph()
                    text = html_lib.escape(item[1])
                    html_parts.append(f'{paragraph_indent()}<p class="instruction">{text}</p>\n')

            close_current_section()
            flush_paragraph()

            html_parts.append("    </details>\n")

        html_parts.append("  </details>\n")

    html_parts.append(
        """</main>
<script>
  const BOOK_STATE = {
    COLLAPSED: "collapsed",
    BOOK_ONLY: "book_only",
    BOOK_AND_CHAPTERS: "book_and_chapters",
  };

  function setBookState(book, state) {
    const chapters = book.querySelectorAll(":scope > details.chapter");
    if (state === BOOK_STATE.COLLAPSED) {
      book.open = false;
      chapters.forEach((chapter) => {
        chapter.open = false;
      });
      book.dataset.state = BOOK_STATE.COLLAPSED;
      return;
    }

    if (state === BOOK_STATE.BOOK_ONLY) {
      book.open = true;
      chapters.forEach((chapter) => {
        chapter.open = false;
      });
      book.dataset.state = BOOK_STATE.BOOK_ONLY;
      return;
    }

    book.open = true;
    chapters.forEach((chapter) => {
      chapter.open = true;
    });
    book.dataset.state = BOOK_STATE.BOOK_AND_CHAPTERS;
  }

  document.querySelectorAll("details.book").forEach((book) => {
    setBookState(book, BOOK_STATE.COLLAPSED);
    const summary = book.querySelector(":scope > summary");

    if (!summary) {
      return;
    }

    const advanceState = () => {
      const state = book.dataset.state || BOOK_STATE.COLLAPSED;
      if (state === BOOK_STATE.COLLAPSED) {
        setBookState(book, BOOK_STATE.BOOK_AND_CHAPTERS);
      } else if (state === BOOK_STATE.BOOK_AND_CHAPTERS) {
        setBookState(book, BOOK_STATE.BOOK_ONLY);
      } else {
        setBookState(book, BOOK_STATE.COLLAPSED);
      }
    };

    summary.addEventListener("click", (event) => {
      event.preventDefault();
      advanceState();
    });

    summary.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        advanceState();
      }
    });
  });
</script>
</body>
</html>
"""
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(html_parts), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usfm-dir", type=Path, default=DEFAULT_USFM_DIR, help="Directory containing *.SFM files")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Where to write the HTML file")
    parser.add_argument("--columns", type=int, default=4, help="Number of columns for the reader view")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    usfm_dir = args.usfm_dir
    if not usfm_dir.exists():
        raise SystemExit(f"USFM directory not found: {usfm_dir}")

    usfm_files = sorted(usfm_dir.glob("*.SFM"))
    if not usfm_files:
        raise SystemExit(f"No .SFM files found in {usfm_dir}")

    print(f"Parsing {len(usfm_files)} books...")
    books = [parse_usfm(path) for path in usfm_files]

    print(f"Rendering multi-column HTML to {args.output}...")
    render_multicolumn_html(books, args.output, args.columns)
    print("Done.")


if __name__ == "__main__":
    main()
