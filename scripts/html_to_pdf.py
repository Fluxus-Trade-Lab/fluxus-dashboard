#!/usr/bin/env python3
"""Convert the self-contained HTML performance reports to PDF via headless Chromium.

Chromium renders with print-media emulation, so the report's `@media print` rules
apply — forcing the clean light theme + light charts for paper. The HTML is
self-contained (base64 images, inline CSS/JS), so there are no network fetches.

Usage:
    python scripts/html_to_pdf.py                 # all monthly_*.html + h1_*.html
    python scripts/html_to_pdf.py path/to/one.html [more.html ...]
"""
import glob
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

REVIEWS = Path("data/portfolio/reviews")


def targets(argv):
    if argv:
        return [Path(a) for a in argv]
    files = sorted(glob.glob(str(REVIEWS / "monthly_*.html"))) + \
        sorted(glob.glob(str(REVIEWS / "h1_*.html")))
    return [Path(f) for f in files]


def main(argv):
    htmls = targets(argv)
    if not htmls:
        raise SystemExit("No HTML reports found. Generate them first.")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for html in htmls:
            pdf = html.with_suffix(".pdf")
            page.goto(html.resolve().as_uri(), wait_until="load")
            page.emulate_media(media="print")   # apply @media print (light theme)
            page.pdf(path=str(pdf), format="A4", print_background=True,
                     margin={"top": "12mm", "bottom": "12mm", "left": "10mm", "right": "10mm"})
            size_kb = pdf.stat().st_size // 1024
            print(f"  ✓ {pdf.name}  ({size_kb} KB)")
        browser.close()
    print(f"✓ {len(htmls)} PDFs written to {REVIEWS}")


if __name__ == "__main__":
    main(sys.argv[1:])
