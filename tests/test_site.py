"""Smoke tests: every page renders, and the static build contains what Pages needs."""

import pytest
from flask_frozen import Freezer

from royalbliss import create_app
from royalbliss.views import SITEMAP_ENDPOINTS

PAGES = ["/", "/about/", "/brands/", "/franchise/", "/contact/"]


@pytest.fixture
def app():
    return create_app({"TESTING": True, "SITE_BASE_URL": "https://example.test/"})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.mark.parametrize("path", PAGES)
def test_page_renders(client, path):
    response = client.get(path)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Royal Bliss" in body
    assert "</html>" in body


@pytest.mark.parametrize("path", PAGES)
def test_page_has_nav_and_canonical(client, path):
    body = client.get(path).get_data(as_text=True)
    assert 'id="nav-links"' in body
    assert '<link rel="canonical" href="https://example.test' in body


def test_unknown_url_renders_404_page(client):
    response = client.get("/no-such-page/")
    assert response.status_code == 404
    assert "That page has left the pass" in response.get_data(as_text=True)


def test_404_file_is_served_for_github_pages(client):
    assert client.get("/404.html").status_code == 200


def test_sitemap_lists_every_page(client):
    body = client.get("/sitemap.xml").get_data(as_text=True)
    assert body.count("<url>") == len(SITEMAP_ENDPOINTS)
    for path in PAGES:
        assert f"https://example.test{path}" in body


def test_robots_points_at_sitemap(client):
    assert "Sitemap: https://example.test/sitemap.xml" in client.get("/robots.txt").get_data(as_text=True)


def test_contact_form_uses_configured_endpoint():
    app = create_app({"TESTING": True, "FORM_ENDPOINT": "https://formspree.io/f/abc123"})
    body = app.test_client().get("/contact/").get_data(as_text=True)
    assert 'data-endpoint="https://formspree.io/f/abc123"' in body


def test_freeze_writes_the_files_pages_needs(tmp_path):
    base = "https://example.test/"
    app = create_app(
        {
            "SITE_BASE_URL": base,
            "FREEZER_DESTINATION": str(tmp_path),
            "FREEZER_BASE_URL": base,
            "FREEZER_REMOVE_EXTRA_FILES": True,
        }
    )
    Freezer(app).freeze()

    expected = [
        "index.html",
        "about/index.html",
        "brands/index.html",
        "franchise/index.html",
        "contact/index.html",
        "404.html",
        "robots.txt",
        "sitemap.xml",
        "static/css/styles.css",
        "static/js/main.js",
        "static/img/favicon.svg",
    ]
    for relative in expected:
        assert (tmp_path / relative).is_file(), f"missing from build: {relative}"


def test_frozen_site_contains_no_ledger_data(tmp_path):
    """The published site must never carry company bank data.

    ADR 002 keeps the tracker out of the Flask app so the freezer cannot reach
    it. This asserts that boundary holds, because the failure mode — publishing
    the company's bank account to a public URL — is not one to discover later.
    """
    base = "https://example.test/"
    app = create_app({
        "SITE_BASE_URL": base,
        "FREEZER_DESTINATION": str(tmp_path),
        "FREEZER_BASE_URL": base,
        "FREEZER_REMOVE_EXTRA_FILES": True,
    })
    Freezer(app).freeze()

    forbidden = ["011711004454", "sampath", "cash tracker", "reconcil", "ledger"]
    for path in tmp_path.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for needle in forbidden:
            assert needle not in text, f"{needle!r} leaked into the published site at {path}"


def test_finance_package_is_not_registered_on_the_app():
    """No finance route can exist, or the freezer would publish it."""
    app = create_app({"TESTING": True})
    for rule in app.url_map.iter_rules():
        assert "finance" not in rule.endpoint
        assert "ledger" not in str(rule)
