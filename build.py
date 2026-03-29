#!/usr/bin/env python3
"""Build script for generating multi-language static site."""

import json
import os
import shutil
from collections import OrderedDict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
TEMPLATES_DIR = ROOT / "templates"
TRANSLATIONS_DIR = ROOT / "translations"
DOCS_DIR = ROOT / "docs"

# Language configuration: code -> {native_name, rtl}
LANGUAGES = OrderedDict([
    ("en", {"native_name": "English", "rtl": False}),
    ("es", {"native_name": "Español", "rtl": False}),
    ("fr", {"native_name": "Français", "rtl": False}),
    ("pt", {"native_name": "Português", "rtl": False}),
    ("de", {"native_name": "Deutsch", "rtl": False}),
    ("nl", {"native_name": "Nederlands", "rtl": False}),
    ("zh", {"native_name": "中文", "rtl": False}),
    ("ja", {"native_name": "日本語", "rtl": False}),
    ("ko", {"native_name": "한국어", "rtl": False}),
    ("ar", {"native_name": "العربية", "rtl": True}),
    ("he", {"native_name": "עברית", "rtl": True}),
])

# Static assets to copy to dist root (shared across languages)
STATIC_ASSETS = [
    "logo.svg",
    "logo-dark.svg",
    "favicon.png",
    "icon-512.png",
]

STATIC_DIRS = [
    "downloads",
]


def load_translation(lang_code: str) -> dict:
    path = TRANSLATIONS_DIR / f"{lang_code}.json"
    if not path.exists():
        print(f"  WARNING: Translation file missing for '{lang_code}', falling back to English")
        path = TRANSLATIONS_DIR / "en.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_docs_content(lang_code: str) -> str:
    path = DOCS_DIR / f"{lang_code}.html"
    if not path.exists():
        print(f"  WARNING: Docs content missing for '{lang_code}', falling back to English")
        path = DOCS_DIR / "en.html"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def generate_root_redirect() -> str:
    lang_codes = list(LANGUAGES.keys())
    codes_js = json.dumps(lang_codes)
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mango — A fast, native MongoDB GUI</title>
  <meta name="description" content="Mango is a native MongoDB client built with Perry. No Electron, no JVM — just a fast, lightweight binary.">
  {"".join(f'  <link rel="alternate" hreflang="{lc}" href="https://mangoquery.com/{lc}/">' + chr(10) for lc in lang_codes)}  <link rel="alternate" hreflang="x-default" href="https://mangoquery.com/en/">
  <link rel="icon" type="image/png" href="/favicon.png">
  <script>
    (function() {{
      var supported = {codes_js};
      var langs = navigator.languages || [navigator.language || 'en'];
      var match = 'en';
      for (var i = 0; i < langs.length; i++) {{
        var code = langs[i].split('-')[0].toLowerCase();
        if (supported.indexOf(code) !== -1) {{
          match = code;
          break;
        }}
      }}
      window.location.replace('/' + match + '/');
    }})();
  </script>
  <noscript>
    <meta http-equiv="refresh" content="0;url=/en/">
  </noscript>
</head>
<body>
  <p>Redirecting... <a href="/en/">Click here</a> if not redirected.</p>
</body>
</html>"""


def build():
    print("Building multi-language site...")

    # Clean dist
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    # Set up Jinja2
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,
    )

    all_language_codes = list(LANGUAGES.keys())

    # Build each language
    for lang_code, lang_info in LANGUAGES.items():
        print(f"  Building {lang_code} ({lang_info['native_name']})...")

        translation = load_translation(lang_code)
        docs_content = load_docs_content(lang_code)
        is_rtl = lang_info["rtl"]

        common_ctx = {
            "lang_code": lang_code,
            "is_rtl": is_rtl,
            "t": translation,
            "all_languages": all_language_codes,
            "languages": LANGUAGES,
            "current_language_name": lang_info["native_name"],
        }

        # Build index page -> dist/{lang}/index.html
        lang_dir = DIST / lang_code
        lang_dir.mkdir(parents=True, exist_ok=True)

        index_template = env.get_template("index.html")
        index_html = index_template.render(**common_ctx, page_path="")
        (lang_dir / "index.html").write_text(index_html, encoding="utf-8")

        # Build docs page -> dist/{lang}/docs/index.html
        docs_dir = lang_dir / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        docs_template = env.get_template("docs.html")
        docs_html = docs_template.render(**common_ctx, page_path="docs", docs_content=docs_content)
        (docs_dir / "index.html").write_text(docs_html, encoding="utf-8")

    # Generate root redirect
    print("  Generating root language detector...")
    (DIST / "index.html").write_text(generate_root_redirect(), encoding="utf-8")

    # Copy static assets
    print("  Copying static assets...")
    for asset in STATIC_ASSETS:
        src = ROOT / asset
        if src.exists():
            shutil.copy2(src, DIST / asset)

    for dir_name in STATIC_DIRS:
        src = ROOT / dir_name
        if src.exists():
            shutil.copytree(src, DIST / dir_name)

    # Count output
    html_count = sum(1 for _ in DIST.rglob("*.html"))
    print(f"\nDone! Generated {html_count} HTML files in dist/")
    print(f"Languages: {', '.join(all_language_codes)}")


if __name__ == "__main__":
    build()
