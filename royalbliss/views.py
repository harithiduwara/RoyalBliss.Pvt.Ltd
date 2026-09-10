"""Page routes.

Every route is a plain GET that renders a template — anything else would not
survive the freeze to static files.
"""

from datetime import date
from urllib.parse import urljoin, urlsplit

from flask import Blueprint, Response, current_app, render_template, url_for

from . import content

site = Blueprint("site", __name__)

# Pages listed in sitemap.xml, in priority order.
SITEMAP_ENDPOINTS = [
    "site.index",
    "site.about",
    "site.brands",
    "site.franchise",
    "site.contact",
]


def absolute_url(endpoint: str) -> str:
    """Public URL for a page, for canonical links, Open Graph tags and the sitemap.

    ``url_for`` already carries the sub-path prefix while Frozen-Flask renders
    the site (a project Pages site lives under /<repo>/), so only the scheme and
    host are taken from SITE_BASE_URL — otherwise the prefix appears twice.
    """
    parts = urlsplit(current_app.config["SITE_BASE_URL"])
    origin = f"{parts.scheme}://{parts.netloc}"
    return urljoin(origin, url_for(endpoint))


@site.app_template_global()
def canonical_url(endpoint: str) -> str:
    return absolute_url(endpoint)


@site.app_context_processor
def inject_content():
    """Make company details and the nav available to every template."""
    return {
        "company": content.COMPANY,
        "contact": content.CONTACT,
        "socials": content.SOCIALS,
        "nav": content.NAV,
        "current_year": date.today().year,
    }


@site.route("/")
def index():
    return render_template(
        "index.html",
        page_title=f"{content.COMPANY['name']} | Food & Beverage Franchise Operator",
        meta_description=content.COMPANY["description"],
        hero_promises=content.HERO_PROMISES,
        stats=content.STATS,
        services=content.SERVICES,
        formats=content.FORMATS,
        why_us=content.WHY_US,
        steps=content.OPENING_STEPS,
    )


@site.route("/about/")
def about():
    return render_template(
        "about.html",
        page_title=f"About Us | {content.COMPANY['name']}",
        meta_description=(
            "Who we are: a food and beverage franchise operator focused on brand "
            "fidelity, food safety and well-run outlets."
        ),
        values=content.VALUES,
        quality_points=content.QUALITY_POINTS,
        leadership=content.LEADERSHIP,
    )


@site.route("/brands/")
def brands():
    return render_template(
        "brands.html",
        page_title=f"Brands & Outlets | {content.COMPANY['name']}",
        meta_description=(
            "The food and beverage brands Royal Bliss (Pvt) Ltd operates under "
            "franchise, and where to find our outlets."
        ),
        brands=content.BRANDS,
        outlets=content.OUTLETS,
        channels=content.CHANNELS,
    )


@site.route("/franchise/")
def franchise():
    return render_template(
        "franchise.html",
        page_title=f"Partner With Us | {content.COMPANY['name']}",
        meta_description=(
            "Franchise brand owners, landlords, suppliers and job seekers: how to "
            "work with Royal Bliss (Pvt) Ltd."
        ),
        tracks=content.PARTNER_TRACKS,
        brand_owner_steps=content.BRAND_OWNER_STEPS,
        supplier_requirements=content.SUPPLIER_REQUIREMENTS,
        roles=content.ROLES,
        faqs=content.FAQS,
    )


@site.route("/contact/")
def contact():
    return render_template(
        "contact.html",
        page_title=f"Contact | {content.COMPANY['name']}",
        meta_description=(
            "Contact Royal Bliss (Pvt) Ltd — franchise enquiries, site proposals, "
            "supplier registration and guest feedback."
        ),
        topics=content.ENQUIRY_TOPICS,
        form_endpoint=current_app.config["FORM_ENDPOINT"],
    )


@site.route("/404.html")
def not_found_page():
    """GitHub Pages serves /404.html for unknown URLs."""
    return render_template(
        "404.html",
        page_title=f"Page not found | {content.COMPANY['name']}",
        meta_description="The page you were looking for could not be found.",
    )


@site.app_errorhandler(404)
def handle_404(error):
    return not_found_page(), 404


@site.route("/robots.txt")
def robots():
    body = f"User-agent: *\nAllow: /\n\nSitemap: {absolute_url('site.sitemap')}\n"
    return Response(body, mimetype="text/plain")


@site.route("/sitemap.xml")
def sitemap():
    urls = "\n".join(
        f"  <url><loc>{absolute_url(endpoint)}</loc></url>" for endpoint in SITEMAP_ENDPOINTS
    )
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n"
        "</urlset>\n"
    )
    return Response(body, mimetype="application/xml")
