#!/usr/bin/env python3
"""
Generate an HTML version of the Berean Standard Bible from the USFM source files.
"""
import argparse
import re
import html
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_USFM_DIR = PROJECT_ROOT / "usfm"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "bsb.html"

# Regex patterns (Reused from existing parser)
FOOTNOTE_RE = re.compile(r'\\f.*?\\f*', re.DOTALL)
CROSS_REF_RE = re.compile(r'\\x.*?\\x*', re.DOTALL)
INLINE_MARKER_RE = re.compile(r'\\(add|bd|bk|em|it|k|nd|pn|qac|sc|sig|tl|wj)*?')

PARAGRAPH_RE = re.compile(r'\\(p|nb|b)(\s+|$)', re.DOTALL)

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

    content = path.read_text(encoding='utf-8')
    # Basic check for BOM or similar if needed, but utf-8 usually handles it.    
    for raw_line in content.splitlines():
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
    return {"id": path.stem, "title": book_title, "chapters": chapters}

def render_html(books, output_path: Path) -> None:
    # HTML Header
    html_parts = [
        """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Berean Standard Bible</title>
    <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
    <style>
        body {
            font-family: \"Georgia\", \"Times New Roman\", serif;
            line-height: 1.6;
            color: #333;
            padding-top: 56px; /* Space for fixed navbar on mobile */
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, \"Helvetica Neue\", Arial, sans-serif;
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
            color: #2c3e50;
        }
        .book-header {
            margin-top: 3rem;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #dee2e6;
            text-align: center;
        }
        .chapter-header {
            margin-top: 2rem;
            color: #6c757d;
        }
        .verse {
            position: relative;
        }
        .verse-num {
            font-size: 0.75em;
            vertical-align: text-top;
            color: #999;
            margin-right: 0.25em;
            font-weight: bold;
            user-select: none;
        }
        .section-title {
            color: #0d6efd;
            margin-top: 1.5em;
            font-size: 1.25rem;
        }
        .instruction {
            font-style: italic;
            color: #666;
            margin-bottom: 1rem;
        }
        /* Sidebar Navigation */
        .sidebar {
            position: fixed;
            top: 0;
            bottom: 0;
            left: 0;
            z-index: 100;
            padding: 48px 0 0;
            box-shadow: inset -1px 0 0 rgba(0, 0, 0, .1);
            background-color: #f8f9fa;
        }
        .sidebar-sticky {
            position: relative;
            top: 0;
            height: calc(100vh - 48px);
            padding-top: .5rem;
            overflow-x: hidden;
            overflow-y: auto; 
        }
        .sidebar .nav-link {
            font-weight: 500;
            color: #333;
            font-size: 0.9rem;
            padding: 0.25rem 1rem;
        }
        .sidebar .nav-link:hover {
            color: #0d6efd;
        }
        .sidebar .nav-link.active {
            color: #0d6efd;
        }
        
        /* Layout */
        @media (min-width: 992px) {
            body { padding-top: 0; }
            .sidebar { display: block !important; width: 250px; }
            main { margin-left: 250px; padding: 2rem 4rem; max-width: 900px; }
            .navbar-mobile { display: none; }
        }
        @media (max-width: 991.98px) {
            .sidebar { display: none; }
            main { padding: 1rem; }
            .navbar-mobile { position: fixed; top: 0; left: 0; right: 0; z-index: 1030; }
        }
    </style>
</head>
<body>

<!-- Mobile Navbar -->
<nav class="navbar navbar-expand-lg navbar-light bg-light navbar-mobile shadow-sm">
  <div class="container-fluid">
    <a class="navbar-brand" href="#">Berean Standard Bible</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#mobileMenu" aria-controls="mobileMenu" aria-expanded="false" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="mobileMenu">
      <ul class="navbar-nav me-auto mb-2 mb-lg-0" style="max-height: 50vh; overflow-y: auto;">

"""
    ]
    
    # Generate Nav Items
    nav_items = []
    for book in books:
        safe_id = book['id']
        title = html.escape(book['title'])
        nav_items.append(f'<li class="nav-item"><a class="nav-link" href="#{safe_id}">{title}</a></li>')

    html_parts.extend(nav_items)
    
    html_parts.append("""      </ul>
    </div>
  </div>
</nav>

<div class="container-fluid">
  <div class="row">
    <nav id="sidebarMenu" class="col-md-3 col-lg-2 d-md-block bg-light sidebar collapse">
      <div class="position-sticky pt-3 sidebar-sticky">
        <h5 class="px-3 pb-2 border-bottom">Books</h5>
        <ul class="nav flex-column">
"""    )
    
    html_parts.extend(nav_items)
    
    html_parts.append("""        </ul>
      </div>
    </nav>

    <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4">
"""    )

    # Render Books
    for book in books:
        safe_id = book['id']
        book_title = html.escape(book['title'])
        
        html_parts.append(f'<div id="{safe_id}" class="book-container">')
        html_parts.append(f'<h1 class="book-header">{book_title}</h1>')
        
        for chapter in book["chapters"]:
            chap_num = chapter['number']
            html_parts.append(f'<h2 class="chapter-header">Chapter {chap_num}</h2>')
            
            paragraph_buffer = []

            def flush_paragraph():
                if paragraph_buffer:
                    content = "".join(paragraph_buffer)
                    html_parts.append(f'<p>{content}</p>')
                    paragraph_buffer.clear()

            for item in chapter["items"]:
                kind = item[0]
                if kind == "verse":
                    _, num, text = item
                    text = html.escape(text).replace('\n', '<br>')
                    paragraph_buffer.append(f'<span class="verse"><sup class="verse-num">{num}</sup>{text}</span> ')
                elif kind == "section":
                    flush_paragraph()
                    _, level, title = item
                    safe_title = html.escape(title)
                    h_tag = f"h{min(6, level + 2)}" 
                    html_parts.append(f'<{h_tag} class="section-title">{safe_title}</{h_tag}>')
                elif kind == "paragraph_break":
                    flush_paragraph()
                elif kind == "paragraph":
                    flush_paragraph()
                    text = html.escape(item[1])
                    html_parts.append(f'<p class="instruction">{text}</p>')

            flush_paragraph()
        
        html_parts.append('</div>')

    html_parts.append("""    <footer class="my-5 pt-5 text-muted text-center text-small">
        <p class="mb-1">&copy; Berean Standard Bible</p>
    </footer>
    </main>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>""")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(html_parts), encoding="utf-8")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usfm-dir", type=Path, default=DEFAULT_USFM_DIR, help="Directory containing *.SFM files")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Where to write the HTML file")
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
    
    print(f"Rendering HTML to {args.output}...")
    render_html(books, args.output)
    print("Done.")

if __name__ == "__main__":
    main()