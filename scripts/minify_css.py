"""
minify_css.py
--------------
Minifies docs/assets/shared.css into dist/assets/shared.css (strips comments
and collapses whitespace). shared.css is loaded on every single page, so
minifying it is worth doing even without a real build pipeline.

Usage:
    python scripts/minify_css.py
    python scripts/minify_css.py --dist output
"""

import argparse
import re
from pathlib import Path


def minify_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{}:;,>])\s*", r"\1", css)
    css = re.sub(r";}", "}", css)
    return css.strip()


def main():
    parser = argparse.ArgumentParser(description="Minify shared.css into dist/")
    parser.add_argument("--dist", default="dist", help="Output directory (default: dist)")
    args = parser.parse_args()

    src = Path("docs/assets/shared.css")
    out_dir = Path(args.dist) / "assets"
    out_dir.mkdir(parents=True, exist_ok=True)

    css = src.read_text(encoding="utf-8")
    minified = minify_css(css)
    (out_dir / "shared.css").write_text(minified, encoding="utf-8")

    before, after = len(css), len(minified)
    print(f"✅  shared.css minified: {before:,} → {after:,} bytes ({100 - 100*after//before}% smaller)")


if __name__ == "__main__":
    main()
