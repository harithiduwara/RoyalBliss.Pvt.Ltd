"""All site copy and data in one place.

Everything the website displays lives here, so the templates stay
presentational and non-developers only ever have to edit one file.

Placeholders marked "EDIT" are the company-specific facts still to be
supplied; see the table in README.md.
"""

# --------------------------------------------------------------------
# Company details
# --------------------------------------------------------------------

COMPANY = {
    "name": "Royal Bliss (Pvt) Ltd",
    "short_name": "Royal Bliss",
    "suffix": "(Pvt) Ltd",
    "tagline": "Food & Beverage Franchise Operator",
    "description": (
        "Royal Bliss (Pvt) Ltd is a food and beverage franchise operator running "
        "restaurant, café and beverage outlets to international brand standards."
    ),
    "registration": "Registered in Sri Lanka · Company No. PV 00000000",  # EDIT
    "country_code": "LK",
    "locality": "Colombo",
}

CONTACT = {
    "address_lines": ["No. 00, Example Avenue", "Colombo 00, Sri Lanka"],  # EDIT
    "street": "No. 00, Example Avenue",
    "phone_display": "+94 11 000 0000",  # EDIT
    "phone_href": "+94110000000",
    "email": "hello@royalbliss.lk",  # EDIT
    "email_partnerships": "partnerships@royalbliss.lk",
    "email_careers": "careers@royalbliss.lk",
    "office_hours": "Monday – Friday, 09:00 – 17:30",
}

SOCIALS = [  # EDIT: real profile URLs
    {"name": "Facebook", "url": "#", "icon": "facebook"},
    {"name": "Instagram", "url": "#", "icon": "instagram"},
    {"name": "LinkedIn", "url": "#", "icon": "linkedin"},
]

NAV = [
    {"endpoint": "site.index", "label": "Home"},
    {"endpoint": "site.about", "label": "About Us"},
    {"endpoint": "site.brands", "label": "Brands & Outlets"},
    {"endpoint": "site.franchise", "label": "Partner With Us"},
    {"endpoint": "site.contact", "label": "Contact"},
]

# --------------------------------------------------------------------
# Home page
# --------------------------------------------------------------------

HERO_PROMISES = [
    "Site selection, fit-out and launch, handled end to end",
    "Trained crews who follow brand recipes and service scripts",
    "Cold-chain, sourcing and food-safety discipline",
    "Transparent reporting against franchisor audits and KPIs",
]

STATS = [  # EDIT: real figures
    {"value": "00", "label": "Outlets Operated"},
    {"value": "00", "label": "Brands Franchised"},
    {"value": "000+", "label": "Team Members"},
    {"value": "0000", "label": "Year Established"},
]

SERVICES = [
    {
        "icon": "storefront",
        "title": "Outlet Development",
        "body": (
            "Location scouting, feasibility, lease negotiation, design approval and "
            "fit-out — delivered to the franchisor's specification and opened on schedule."
        ),
    },
    {
        "icon": "people",
        "title": "Operations & People",
        "body": (
            "Recruiting, brand-certified training, rostering and daily shift discipline. "
            "Our managers are accountable for guest experience scores, not just sales."
        ),
    },
    {
        "icon": "box",
        "title": "Supply & Quality",
        "body": (
            "Approved-supplier sourcing, cold-chain management, stock control and documented "
            "food-safety checks at every stage from delivery to counter."
        ),
    },
    {
        "icon": "chart",
        "title": "Commercial Management",
        "body": (
            "Menu pricing within brand guidelines, cost control, royalty and reporting "
            "obligations, and month-end packs that stand up to a franchisor review."
        ),
    },
    {
        "icon": "chat",
        "title": "Local Marketing",
        "body": (
            "Store-level activations, delivery-platform performance and community "
            "partnerships — always executed inside the brand's marketing playbook."
        ),
    },
    {
        "icon": "shield",
        "title": "Compliance",
        "body": (
            "Licensing, health authority inspections, HACCP-aligned documentation and staff "
            "medical clearances kept current across every outlet."
        ),
    },
]

FORMATS = [
    {
        "label": "Quick Service",
        "title": "Quick-Service Restaurants",
        "body": "High-volume kitchens built for speed, consistency and peak-hour throughput without letting quality slip.",
        "tags": ["Dine-in", "Takeaway", "Delivery"],
        "gradient": "linear-gradient(140deg,#6b1839,#4a0f27)",
    },
    {
        "label": "Café & Coffee",
        "title": "Specialty Coffee & Café",
        "body": "Barista-led counters where extraction standards, milk texture and dwell time are trained, tested and re-tested.",
        "tags": ["Espresso Bar", "All-day Menu"],
        "gradient": "linear-gradient(140deg,#8a5a2b,#4a2c12)",
    },
    {
        "label": "Beverages",
        "title": "Beverages & Desserts",
        "body": "Bubble tea, juices, frozen desserts and seasonal ranges — formats that live or die on recipe accuracy.",
        "tags": ["Kiosk", "Mall Retail"],
        "gradient": "linear-gradient(140deg,#2f5d50,#12352c)",
    },
]

WHY_US = [
    {"title": "Brand fidelity", "body": "Your specification is the specification. No local shortcuts, no unapproved substitutions."},
    {"title": "Capital readiness", "body": "Funded development plans, so agreed opening schedules are met rather than renegotiated."},
    {"title": "Open books", "body": "Sales, wastage, audit scores and guest feedback reported on your cycle, in your format."},
    {"title": "Local knowledge", "body": "Real insight into trade areas, landlords, labour markets and regulators in our territory."},
]

OPENING_STEPS = [
    {"title": "Territory & feasibility", "body": "We model the trade area, sales potential and cost base before committing to a site."},
    {"title": "Build to brand standard", "body": "Design approvals, equipment procurement and fit-out managed against the franchisor's manual."},
    {"title": "Certify the team", "body": "Managers and crew complete brand training and pass sign-off before the doors open."},
    {"title": "Operate and improve", "body": "Daily checks, weekly reviews and audit-ready records from the first trading day onward."},
]

# --------------------------------------------------------------------
# About page
# --------------------------------------------------------------------

VALUES = [
    {
        "icon": "shield",
        "title": "Safety first",
        "body": "If a food-safety check fails, the product does not leave the kitchen. There is no commercial argument that outranks this.",
    },
    {
        "icon": "storefront",
        "title": "Respect the brand",
        "body": "We operate someone else's name. Specifications, recipes and standards are followed, not reinterpreted.",
    },
    {
        "icon": "people",
        "title": "Grow our people",
        "body": "Crew members should be able to become shift leaders, and shift leaders should be able to become managers. We promote from within wherever we can.",
    },
    {
        "icon": "pulse",
        "title": "Tell the truth",
        "body": "Accurate numbers, honest audit results and early warning when something is going wrong. Franchisors and landlords get the real picture.",
    },
]

QUALITY_POINTS = [
    "Temperature logs for every chiller, freezer and hot-hold unit, recorded at set intervals",
    "Goods-received checks against approved supplier lists, with rejection authority at store level",
    "Colour-coded preparation, allergen separation and labelled shelf-life on all prepared items",
    "Cleaning schedules signed off by shift, not by memory",
    "Staff health screening and hygiene certification kept current and on file",
    "Internal audits between franchisor visits, with corrective actions tracked to closure",
]

LEADERSHIP = [  # EDIT: real names
    {"role": "Managing Director", "name": "Name to be added", "body": "Owns franchisor relationships, territory strategy and capital planning."},
    {"role": "Head of Operations", "name": "Name to be added", "body": "Owns outlet performance, staffing and the daily operating standard."},
    {"role": "Head of Quality & Supply", "name": "Name to be added", "body": "Owns sourcing, cold chain, food safety and compliance across all sites."},
]

# --------------------------------------------------------------------
# Brands & outlets
# --------------------------------------------------------------------

BRANDS = [  # EDIT: one entry per franchised brand
    {
        "label": "Brand One",
        "name": "Brand Name One",
        "body": "A short paragraph on the brand: what it serves, who it serves, and how long we have operated it in this territory.",
        "tags": ["Quick Service", "Dine-in", "Delivery"],
        "gradient": "linear-gradient(140deg,#6b1839,#4a0f27)",
    },
    {
        "label": "Brand Two",
        "name": "Brand Name Two",
        "body": "A short paragraph on the brand: what it serves, who it serves, and how long we have operated it in this territory.",
        "tags": ["Café", "Specialty Coffee"],
        "gradient": "linear-gradient(140deg,#8a5a2b,#4a2c12)",
    },
    {
        "label": "Brand Three",
        "name": "Brand Name Three",
        "body": "A short paragraph on the brand: what it serves, who it serves, and how long we have operated it in this territory.",
        "tags": ["Beverages", "Kiosk"],
        "gradient": "linear-gradient(140deg,#2f5d50,#12352c)",
    },
]

OUTLETS = [  # EDIT: one entry per outlet
    {
        "name": "Colombo Flagship",
        "brand": "Brand Name One",
        "address": "No. 00, Example Avenue, Colombo 00",
        "hours": "10:00 – 22:00 daily",
        "phone_display": "+94 11 000 0000",
        "phone_href": "+94110000000",
    },
    {
        "name": "Mall Kiosk",
        "brand": "Brand Name Three",
        "address": "Level 0, Example Mall, Colombo 00",
        "hours": "10:00 – 22:00 daily",
        "phone_display": "+94 11 000 0000",
        "phone_href": "+94110000000",
    },
    {
        "name": "Suburban Café",
        "brand": "Brand Name Two",
        "address": "No. 00, Example Road, Example City",
        "hours": "07:00 – 21:00 daily",
        "phone_display": "+94 11 000 0000",
        "phone_href": "+94110000000",
    },
]

CHANNELS = [
    {
        "icon": "truck",
        "title": "Delivery & aggregators",
        "body": "Listed on the major delivery platforms in our territory, with dedicated packing stations so dine-in service is not slowed by online orders.",
    },
    {
        "icon": "storefront",
        "title": "Corporate & bulk orders",
        "body": "Office catering, event platters and recurring corporate accounts, quoted within brand pricing rules and invoiced properly.",
    },
    {
        "icon": "clock",
        "title": "New openings",
        "body": "Sites in our development pipeline are announced here first. Landlords with suitable space are welcome to approach us directly.",
    },
]

# --------------------------------------------------------------------
# Partner With Us
# --------------------------------------------------------------------

PARTNER_TRACKS = [
    {
        "icon": "star",
        "title": "Brand owners & franchisors",
        "body": "If you are looking for a master franchisee or a multi-unit developer in our territory, we can move quickly: feasibility modelling, a funded development schedule, and an operating team that has opened outlets before.",
        "link_text": "What we will send you",
        "anchor": "#brand-owners",
    },
    {
        "icon": "storefront",
        "title": "Landlords & developers",
        "body": "We take space in malls, high-street retail, transit hubs and highway locations. Send us the floor plate, frontage, footfall data and available services, and you will get a straight answer on fit.",
        "link_text": "Submit a location",
        "anchor": None,  # links to the contact form
    },
    {
        "icon": "box",
        "title": "Suppliers",
        "body": "Where a franchisor allows local sourcing, we buy locally. Suppliers must meet the brand's specification, pass our audit, and hold current food-safety certification.",
        "link_text": "Supplier requirements",
        "anchor": "#suppliers",
    },
    {
        "icon": "people",
        "title": "Careers",
        "body": "Crew, baristas, kitchen staff, shift leaders and outlet managers. Training is provided and paid; promotion from within is the norm rather than the exception.",
        "link_text": "Open roles",
        "anchor": "#careers",
    },
]

BRAND_OWNER_STEPS = [
    {"title": "Introduction", "body": "You tell us the brand, the territory on offer and the development expectations. We tell you honestly whether it fits our portfolio."},
    {"title": "Due diligence both ways", "body": "We share company profile, audited financials, existing brand references and outlet performance. We ask for your FDD or equivalent, fee structure and support model."},
    {"title": "Market study", "body": "A written feasibility: trade areas, competitor density, pricing sensitivity, labour costs and a five-year unit-economics model."},
    {"title": "Development plan", "body": "Site count, opening schedule, capital source and the operating team assigned to the brand."},
    {"title": "Agreement and launch", "body": "Contract, training, fit-out, certification, and a first opening we are both happy to put a photo of on the website."},
]

SUPPLIER_REQUIREMENTS = [
    {"title": "Certification", "body": "Valid business registration, food-handling licences and, for food items, current lab analysis or a recognised food-safety certification."},
    {"title": "Specification match", "body": "Product must meet the franchisor's written specification exactly — grade, size, packaging and shelf life included."},
    {"title": "Consistency & capacity", "body": "Reliable volumes, stable pricing over an agreed term, and a delivery schedule that fits our outlets' receiving windows."},
]

ROLES = [  # EDIT: keep current
    {"title": "Outlet Crew", "body": "Front counter, kitchen and barista roles. Full and part-time shifts. No prior experience required — brand training is provided."},
    {"title": "Shift Leaders", "body": "Run a trading shift end to end: people, product, cash and cleanliness. Typically promoted from crew."},
    {"title": "Outlet Managers", "body": "Own a P&L, a roster and an audit score. Prior multi-shift restaurant or café management experience expected."},
]

FAQS = [
    {
        "question": "Do you sell franchises of your own?",
        "answer": "No. Royal Bliss (Pvt) Ltd is a franchisee — we operate other companies' brands under licence. We do not sub-franchise unless a brand owner specifically authorises it in our territory.",
    },
    {
        "question": "Which territories do you operate in?",
        "answer": "Our current outlets and development pipeline are listed on the Brands & Outlets page. Territory rights vary by brand agreement, so it is best to ask us directly about a specific area.",
    },
    {
        "question": "How long does it take to open a new outlet?",
        "answer": "Typically three to six months from a signed lease, depending on the format, landlord handover condition and the franchisor's design approval cycle. Kiosks are faster; full-kitchen restaurants take longer.",
    },
    {
        "question": "Can we discuss an exclusive supply agreement?",
        "answer": "Yes, where the franchisor permits local sourcing for that item. Exclusivity is possible for suppliers who clear our audit and can hold price and quality over the term.",
    },
    {
        "question": "How do I report a problem with an order or an outlet?",
        "answer": "Please use the contact form and select “Guest feedback”, or call the outlet directly. Guest complaints are reviewed by the operations team, and anything food-safety related is escalated the same day.",
    },
]

# --------------------------------------------------------------------
# Contact form
# --------------------------------------------------------------------

ENQUIRY_TOPICS = [
    "Franchise opportunity (brand owner)",
    "Location / site proposal (landlord)",
    "Supplier registration",
    "Corporate or bulk order",
    "Careers",
    "Guest feedback",
    "Something else",
]
