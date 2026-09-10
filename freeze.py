"""Render the Flask app to static files that GitHub Pages can host.

    python freeze.py

Output goes to ./build — that directory is what the Pages workflow uploads.
Set SITE_BASE_URL when building for a different address (a custom domain, say),
so canonical links, Open Graph tags and sitemap.xml point at the right host:

    SITE_BASE_URL=https://www.royalbliss.lk python freeze.py
"""

import os
import shutil
import sys
from pathlib import Path

from flask_frozen import Freezer

from royalbliss import DEFAULT_BASE_URL, create_app

BUILD_DIR = Path(__file__).parent / "build"


def build() -> Path:
    base_url = os.environ.get("SITE_BASE_URL", DEFAULT_BASE_URL).rstrip("/") + "/"

    app = create_app(
        {
            "SITE_BASE_URL": base_url,
            "FREEZER_DESTINATION": str(BUILD_DIR),
            # Wipe stale pages from previous builds rather than leaving them behind.
            "FREEZER_REMOVE_EXTRA_FILES": True,
            # Makes url_for() emit the sub-path a project Pages site lives under.
            "FREEZER_BASE_URL": base_url,
            # Every page is reachable from the nav, so the crawler finds them all;
            # this just catches a page that is ever added without a link to it.
            "FREEZER_IGNORE_MIMETYPE_WARNINGS": True,
        }
    )

    freezer = Freezer(app)
    pages = [page for page in freezer.freeze()]

    # GitHub Pages runs Jekyll over the upload unless told not to, which would
    # drop any file or folder starting with an underscore.
    (BUILD_DIR / ".nojekyll").touch()

    # A custom domain needs a CNAME file next to the pages.
    domain = os.environ.get("SITE_DOMAIN", "").strip()
    if domain:
        (BUILD_DIR / "CNAME").write_text(domain + "\n")

    return pages


if __name__ == "__main__":
    if "--clean" in sys.argv and BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    urls = build()
    print(f"Froze {len(urls)} URLs into {BUILD_DIR}")
    for path in sorted(p for p in BUILD_DIR.rglob("*") if p.is_file()):
        print("  ", path.relative_to(BUILD_DIR))
