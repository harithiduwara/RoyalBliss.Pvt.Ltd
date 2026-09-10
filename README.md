# Royal Bliss (Pvt) Ltd — Website

The official website for **Royal Bliss (Pvt) Ltd**, a food and beverage franchise operator.
It is a plain static site (HTML, CSS, a little JavaScript) with no build step, hosted free on
GitHub Pages.

**Live site:** https://harithiduwara.github.io/RoyalBliss.Pvt.Ltd/
*(available once Pages is switched on — see “Turning on hosting” below)*

---

## Pages

| File | Page | What it covers |
|---|---|---|
| `index.html` | Home | Positioning, what we do, portfolio preview, how we work |
| `about.html` | About Us | Story, values, quality & food safety, leadership |
| `brands.html` | Brands & Outlets | Franchised brands, outlet directory, delivery/corporate |
| `franchise.html` | Partner With Us | Brand owners, landlords, suppliers, careers, FAQ |
| `contact.html` | Contact | Enquiry form, head-office details, map slot |
| `404.html` | Not found | Friendly fallback for bad links |

Supporting files: `assets/css/styles.css`, `assets/js/main.js`, `assets/img/favicon.svg`,
`robots.txt`, `sitemap.xml`, `.nojekyll`, `.github/workflows/deploy-pages.yml`.

---

## Turning on hosting (one-time, ~2 minutes)

1. Merge this branch into `main`.
2. On GitHub, go to **Settings → Pages**.
3. Under **Build and deployment → Source**, choose **GitHub Actions**.
4. Push to `main` (or run the workflow manually from the **Actions** tab). The
   `Deploy site to GitHub Pages` workflow publishes the site.

The site is then live at `https://harithiduwara.github.io/RoyalBliss.Pvt.Ltd/`.

### Using your own domain (e.g. `royalbliss.lk`)

1. Add a file named `CNAME` at the repository root containing only your domain, e.g. `www.royalbliss.lk`.
2. At your DNS provider, point the domain at GitHub Pages:
   - `www` → CNAME record → `harithiduwara.github.io`
   - apex (`royalbliss.lk`) → A records → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
3. In **Settings → Pages**, enter the domain and tick **Enforce HTTPS**.
4. Update the `https://harithiduwara.github.io/RoyalBliss.Pvt.Ltd/` URLs in each page's
   `<link rel="canonical">` / Open Graph tags, in `robots.txt` and in `sitemap.xml`.

---

## Placeholders to replace

The structure and copy are complete; the company-specific facts are deliberately marked so
nothing invented ends up on a live page. Search the repo for `EDIT:` and `00` to find them all.

| Placeholder | Where | Replace with |
|---|---|---|
| `+94 11 000 0000` | all pages (footer), `contact.html`, `brands.html` | Real phone number (also update the `tel:` links) |
| `hello@royalbliss.lk`, `partnerships@…`, `careers@…` | footer, `contact.html`, `franchise.html`, `assets/js/main.js` | Real mailboxes |
| `No. 00, Example Avenue, Colombo 00, Sri Lanka` | footer, `contact.html` | Registered office address |
| `Company No. PV 00000000` | footer | Company registration number |
| `Registered in Sri Lanka` | footer | Correct country of registration |
| Stat band figures (`00`, `000+`, `0000`) | `index.html` | Outlet count, brand count, headcount, year founded |
| `Brand Name One / Two / Three` | `brands.html`, `index.html` | The brands you actually franchise (plus logos/colours) |
| Outlet table rows | `brands.html` | Real outlets, addresses, hours, phone numbers |
| Leadership cards (“Name to be added”) | `about.html` | Names and titles |
| Social links (`href="#"`) | footer of every page | Facebook / Instagram / LinkedIn URLs |
| Map placeholder box | `contact.html` | Google Maps embed `<iframe>` |

> **Note on the country:** the site assumes Sri Lanka (`.lk` addresses, `+94` dialling code,
> `PV` company number format), inferred from the “(Pvt) Ltd” company form. If Royal Bliss is
> registered elsewhere, update the footer, contact page and phone formats accordingly.

---

## Making the contact form actually send email

GitHub Pages serves static files only, so a form needs a third-party endpoint. The form already
supports one — no code changes needed beyond pasting a URL:

1. Create a free form endpoint at [Formspree](https://formspree.io), [Getform](https://getform.io)
   or [Basin](https://usebasin.com).
2. In `contact.html`, put the endpoint URL into the form's `data-endpoint` attribute:

   ```html
   <form class="form" data-form data-endpoint="https://formspree.io/f/xxxxxxxx" ...>
   ```

Until an endpoint is set, submitting the form opens the visitor's own email client with the
details pre-filled and addressed to the `data-mailto` address. A hidden honeypot field
(`company_website`) silently discards bot submissions either way.

---

## Editing the site

No tooling, no dependencies, no build. Edit the HTML directly and commit.

To preview locally:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

**Design tokens** — colours, fonts, spacing and shadows are CSS custom properties at the top of
`assets/css/styles.css` (`:root { … }`). Change `--royal`, `--gold` and `--cream` there and the
whole site follows.

**Adding a page** — copy an existing page, change the `<title>`, meta description and canonical
URL, add a `<li>` to the nav in *every* page's header, and add the URL to `sitemap.xml`.

**Adding photography** — drop images into `assets/img/` and swap them in for the gradient
placeholders (`.brand-card__visual`, `.split__media`). Use compressed JPEG/WebP under ~300 KB and
always set `alt` text.

---

## What's built in

- Responsive down to ~360 px, with a mobile navigation menu
- Accessible: skip link, semantic landmarks, labelled form fields, visible focus rings,
  `prefers-reduced-motion` support
- SEO: per-page titles and descriptions, canonical URLs, Open Graph tags, `sitemap.xml`,
  `robots.txt`, and Organization structured data on the home page
- No frameworks, no trackers, no cookies — one small JS file (~4 KB) and one stylesheet
- Fonts loaded from Google Fonts, with system-font fallbacks if they don't load

---

© Royal Bliss (Pvt) Ltd. Brand names shown on the Brands page remain the property of their
respective owners; Royal Bliss operates them as an authorised franchisee.
