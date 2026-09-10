"""Royal Bliss (Pvt) Ltd — Flask application factory.

Flask is used here as a templating layer, not a running server: the app is
rendered to static HTML by ``freeze.py`` and that output is what GitHub Pages
hosts. Everything in the app therefore has to survive being turned into flat
files — no request handling, no sessions, no database.
"""

import os

from flask import Flask

__version__ = "1.0.0"

DEFAULT_BASE_URL = "https://harithiduwara.github.io/RoyalBliss.Pvt.Ltd/"


def create_app(config: dict | None = None) -> Flask:
    """Build and configure the application.

    Environment variables (both optional):
        SITE_BASE_URL   public URL the site is served from; used for canonical
                        links, Open Graph tags and sitemap.xml
        FORM_ENDPOINT   third-party form endpoint (Formspree and the like) that
                        receives contact-form submissions
    """
    app = Flask(__name__)

    app.config.from_mapping(
        SITE_BASE_URL=os.environ.get("SITE_BASE_URL", DEFAULT_BASE_URL).rstrip("/") + "/",
        FORM_ENDPOINT=os.environ.get("FORM_ENDPOINT", ""),
    )
    if config:
        app.config.update(config)

    from .views import site

    app.register_blueprint(site)

    return app
