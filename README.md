# Royal Bliss (Pvt) Ltd — Website

The official website for **Royal Bliss (Pvt) Ltd**, a food and beverage franchise operator.

It is a **Flask** application (Jinja templates, all copy in one Python module) that is rendered
to static HTML by [Frozen-Flask](https://frozen-flask.readthedocs.io) and published on GitHub
Pages. Flask is the authoring layer; what visitors get is flat files.

**Live site:** https://harithiduwara.github.io/RoyalBliss.Pvt.Ltd/
*(available once Pages is switched on — see “Turning on hosting” below)*

> **Why the freeze step?** GitHub Pages serves static files only; it cannot run Python. So the
> site is built to HTML in CI and that output is what gets hosted. Everything in this repo is
> designed around that constraint — no server-side form handling, no database, no sessions.

---

## Layout

```
app.py                      dev server entry point
freeze.py                   renders the app to ./build for publishing
royalbliss/
  __init__.py               application factory + configuration
  views.py                  one route per page, plus robots.txt and sitemap.xml
  content.py                ← ALL SITE COPY AND DATA lives here
  templates/
    base.html               shared <head>, header, footer, scripts
    index.html  about.html  brands.html  franchise.html  contact.html  404.html
    partials/               header, footer, logo, page banner, icon + card macros
  static/css/styles.css     single stylesheet, CSS custom properties at the top
  static/js/main.js         mobile nav, scroll reveal, contact-form handling
  static/img/favicon.svg
tests/test_site.py          route + build smoke tests
.github/workflows/          test, freeze, deploy to Pages
```

| Route | Page | What it covers |
|---|---|---|
| `/` | Home | Positioning, what we do, portfolio preview, how we work |
| `/about/` | About Us | Story, values, quality & food safety, leadership |
| `/brands/` | Brands & Outlets | Franchised brands, outlet directory, delivery/corporate |
| `/franchise/` | Partner With Us | Brand owners, landlords, suppliers, careers, FAQ |
| `/contact/` | Contact | Enquiry form, head-office details, map slot |
| `/404.html` | Not found | GitHub Pages serves this for unknown URLs |

---

## Running it locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

python app.py            # http://127.0.0.1:5000
python -m pytest tests   # 16 smoke tests
```

To check exactly what will be published:

```bash
python freeze.py --clean
cd build && python -m http.server 8000
```

---

## Turning on hosting (one-time, ~2 minutes)

1. Merge this branch into `main`.
2. On GitHub, go to **Settings → Pages**.
3. Under **Build and deployment → Source**, choose **GitHub Actions**.
4. Push to `main` (or run the workflow manually from the **Actions** tab).

The workflow installs dependencies, runs the tests, freezes the app and deploys `build/`.
Pull requests build and test without deploying.

### Using your own domain (e.g. `royalbliss.lk`)

Page URLs are absolute, so the build needs to know where it will live.

1. In **Settings → Secrets and variables → Actions → Variables**, add:
   - `SITE_BASE_URL` = `https://www.royalbliss.lk/`
   - `SITE_DOMAIN` = `www.royalbliss.lk` — this writes the `CNAME` file into the build
2. At your DNS provider, point the domain at GitHub Pages:
   - `www` → CNAME record → `harithiduwara.github.io`
   - apex (`royalbliss.lk`) → A records → `185.199.108.153`, `185.199.109.153`,
     `185.199.110.153`, `185.199.111.153`
3. In **Settings → Pages**, enter the domain and tick **Enforce HTTPS**.

No code changes needed — canonical links, Open Graph tags, `sitemap.xml` and `robots.txt` all
follow `SITE_BASE_URL`.

---

## Editing the site

**Copy and data:** `royalbliss/content.py`. Adding an outlet, a brand, a job or an FAQ means
adding a dictionary to a list — the templates loop over them, so no HTML is involved:

```python
OUTLETS = [
    {
        "name": "Kandy City Centre",
        "brand": "Brand Name One",
        "address": "Level 2, Kandy City Centre",
        "hours": "10:00 – 22:00 daily",
        "phone_display": "+94 81 000 0000",
        "phone_href": "+94810000000",
    },
    ...
]
```

**Design tokens:** colours, fonts, spacing and shadows are CSS custom properties at the top of
`static/css/styles.css` (`:root { … }`). Change `--royal`, `--gold` and `--cream` there and the
whole site follows.

**A new page:** add a route in `royalbliss/views.py`, a template extending `base.html`, an entry
in `NAV` in `content.py`, and the endpoint in `SITEMAP_ENDPOINTS`. Frozen-Flask picks it up
automatically — no build config to touch.

**Photography:** drop images into `royalbliss/static/img/` and reference them with
`{{ url_for('static', filename='img/your-photo.jpg') }}`, replacing the gradient placeholders
(`.brand-card__visual`, `.split__media`). Compressed JPEG/WebP under ~300 KB, always with `alt` text.

---

## Placeholders to replace

The structure and copy are complete; the company-specific facts are deliberately marked so
nothing invented ends up on a live page. Almost all of them are in `royalbliss/content.py` —
search it for `EDIT`.

| Placeholder | Where in `content.py` | Replace with |
|---|---|---|
| `+94 11 000 0000` | `CONTACT`, `OUTLETS` | Real phone numbers (update `phone_href` too) |
| `hello@royalbliss.lk`, `partnerships@…`, `careers@…` | `CONTACT` | Real mailboxes |
| `No. 00, Example Avenue, Colombo 00` | `CONTACT` | Registered office address |
| `Company No. PV 00000000` | `COMPANY["registration"]` | Company registration number |
| `00`, `000+`, `0000` | `STATS` | Outlet count, brand count, headcount, year founded |
| `Brand Name One / Two / Three` | `BRANDS` | The brands you actually franchise |
| Outlet rows | `OUTLETS` | Real outlets, addresses, hours, phones |
| “Name to be added” | `LEADERSHIP` | Names and titles |
| `"url": "#"` | `SOCIALS` | Facebook / Instagram / LinkedIn URLs |
| Map placeholder box | `templates/contact.html` | Google Maps embed `<iframe>` |

> **Note on the country:** the site assumes Sri Lanka (`.lk` addresses, `+94` dialling code,
> `PV` company number format), inferred from the “(Pvt) Ltd” company form. If Royal Bliss is
> registered elsewhere, update `COMPANY` and `CONTACT` accordingly.

---

## Making the contact form deliver email

A static host cannot process a form POST, so submissions go to a form service instead:

1. Create a free endpoint at [Formspree](https://formspree.io), [Getform](https://getform.io)
   or [Basin](https://usebasin.com).
2. In **Settings → Secrets and variables → Actions → Variables**, add `FORM_ENDPOINT` with that
   URL, and add `FORM_ENDPOINT: ${{ vars.FORM_ENDPOINT }}` to the freeze step's `env:` block in
   `.github/workflows/deploy-pages.yml`.

Until an endpoint is set, submitting the form opens the visitor's own email client with the
details pre-filled and addressed to `CONTACT["email"]`. A hidden honeypot field
(`company_website`) silently discards bot submissions either way.

---

## What's built in

- Responsive down to ~360 px, with a mobile navigation menu
- Accessible: skip link, semantic landmarks, labelled form fields, visible focus rings,
  `prefers-reduced-motion` support
- SEO: per-page titles and descriptions, canonical URLs, Open Graph tags, generated
  `sitemap.xml` and `robots.txt`, Organization structured data on the home page
- No frontend frameworks, no trackers, no cookies — one small JS file and one stylesheet
- Fonts loaded from Google Fonts, with system-font fallbacks if they don't load

---

© Royal Bliss (Pvt) Ltd. Brand names shown on the Brands page remain the property of their
respective owners; Royal Bliss operates them as an authorised franchisee.
