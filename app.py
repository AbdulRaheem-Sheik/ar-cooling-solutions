import hashlib
import html
import json
import os
import secrets
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, abort, redirect, render_template, request, send_from_directory, session, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect


BASE_DIR = Path(__file__).resolve().parent
# Settings and secrets come from the environment; locally they live in .env (never committed).
load_dotenv(BASE_DIR / ".env")

# Content (products, services, spare parts, compressor models, home page items) lives in a
# SQLite database (store.py), first filled from the JSON files in data/.
import store  # noqa: E402  (after load_dotenv, so AR_DATABASE_PATH from .env applies)

# The live site is static (GitHub Pages), built by tools/build_static.py.
SITE_URL = os.environ.get("AR_SITE_URL", "https://arcooling.in").rstrip("/")
# Enquiries are delivered by FormSubmit (https://formsubmit.co, free): the visitor's browser
# sends the form to formsubmit.co, which emails it to the inbox below as a table. The very
# first submission makes FormSubmit email that inbox a one-time "Activate form" link.
# Each enquiry type can go to its own inbox; currently they all go to enquiry@arcooling.in.
ENQUIRY_INBOXES = {
    "product": "enquiry@arcooling.in",
    "spare": "enquiry@arcooling.in",
    "service": "enquiry@arcooling.in",
    "general": "enquiry@arcooling.in",
}
# Optional: after activation, FormSubmit's email offers a random-string alias for the inbox.
# Listing it here keeps the real address out of the page source (fewer spam bots).
FORMSUBMIT_ALIASES = {
    # "enquiry@arcooling.in": "the-random-string-from-formsubmit",
}


def formsubmit_endpoint(email, ajax=True):
    """FormSubmit URL for an inbox: /ajax/ for the browser script, plain for the no-JavaScript form."""
    target = FORMSUBMIT_ALIASES.get(email, email)
    return f"https://formsubmit.co/{'ajax/' if ajax else ''}{target}"


def get_enquiry_endpoints():
    """Where each enquiry type is sent."""
    return {kind: formsubmit_endpoint(email) for kind, email in ENQUIRY_INBOXES.items()}


# Admin edits the content database. It is not part of the static site, so it only works
# where the Flask app itself runs. It has no built-in default login: it stays disabled
# until both values are set in .env (or the host's environment settings).
ADMIN_USERNAME = os.environ.get("AR_ADMIN_USERNAME", "").strip()
ADMIN_PASSWORD = os.environ.get("AR_ADMIN_PASSWORD", "")
ADMIN_MIN_PASSWORD_LENGTH = 12
ADMIN_ENABLED = bool(ADMIN_USERNAME) and len(ADMIN_PASSWORD) >= ADMIN_MIN_PASSWORD_LENGTH


def get_product_types():
    return store.all_records("products")


def get_product(slug):
    for product in get_product_types():
        if product.get("slug") == slug:
            return product
    return None


def get_spare_categories():
    return store.all_records("spares")


def get_services():
    return store.all_records("services")


def get_service(slug):
    for service in get_services():
        if service.get("slug") == slug:
            return service
    return None


def get_featured_spare():
    return store.get_record("site", "featured-spare")


# Home page content: counters, reviews and FAQs (data/home/*.json).
# Entries marked "sample": true are stand-ins for real content. They show in the local
# preview (with a "Sample" badge) but never in the static build that goes live.
SHOW_SAMPLE_CONTENT = os.environ.get("AR_STATIC_BUILD") != "1"


def load_home_items(name):
    items = store.get_record("home", name)["items"]
    return [item for item in items if SHOW_SAMPLE_CONTENT or not item.get("sample")]


def slugify(text):
    return "-".join("".join(c if c.isalnum() else " " for c in text.lower()).split())


def get_compressor_brands():
    """Brands with their series and models. Each model gets its brand, series, slug and
    display name filled in, so templates and routes can use any model on its own."""
    brands = store.all_records("compressors")
    for brand in brands:
        for series in brand["series"]:
            for model in series["models"]:
                # Models with a maker's code get name/slug from it; generic ones set their own.
                if "model" in model:
                    model.setdefault("name", f"{brand['brand']} {model['model']}")
                    model.setdefault("slug", f"{brand['slug']}-{model['model'].lower()}")
                model["brand"], model["series"] = brand, series
                model["capacity"] = format_capacity(model.get("capacity_btuh"))
    return brands


def get_compressor_models():
    return [model for brand in get_compressor_brands() for series in brand["series"] for model in series["models"]]


def get_compressor_model(slug):
    return next((model for model in get_compressor_models() if model["slug"] == slug), None)


def format_capacity(btuh):
    """'~6.75 TR' from BTU/h (1 TR = 12,000 BTU/h), or '' when unknown."""
    if not btuh:
        return ""
    return f"~{btuh / 12000:.2f}".rstrip("0").rstrip(".") + " TR"


def compressor_specs(model):
    """(label, value) rows for a compressor model page. A model's own "specs" list
    (label/value pairs) overrides or adds to the rows built from its series."""
    series, btuh = model["series"], model.get("capacity_btuh")
    specs = {
        "Brand": series.get("brands") or model["brand"]["brand"],
        "Series": series["name"],
        "Model": model.get("model") or "Matched to your unit",
        "Compressor type": series["type"],
        "Refrigerant": series["refrigerant"],
        "Nominal capacity": f"{btuh:,} BTU/h · {model['capacity']} · ~{btuh * 0.000293071:.1f} kW" if btuh else "Depends on refrigerant and operating conditions",
        "Application": series["application"],
        "Power supply": series.get("power_supply") or "On request",   # a list shows one per line
    }
    specs.update({spec["label"]: spec["value"] for spec in model.get("specs", [])})
    return list(specs.items())


# Collections the admin can edit.
EDITABLE_COLLECTIONS = ("products", "spares", "services", "compressors")


def resolve_record_name(collection, item_name):
    """The database name of an editable record, from its name or slug (None if not found)."""
    if collection not in EDITABLE_COLLECTIONS:
        return None
    return store.find_name(collection, item_name)


BUSINESS = {
    "name": "AR Cooling Solutions",
    "phone_display": "+91 88013 81405",
    "phone_e164": "+918801381405",
    # Second number, shown with the first in the contact section.
    "phone2_display": "+91 88010 31846",
    "phone2_e164": "+918801031846",
    "whatsapp_number": "918801381405",
    "email": "enquiry@arcooling.in",
    # Opening hours, shown across the site. Keep opening_days / opens / closes in step
    # (they are given to Google in the home page's structured data).
    "hours": "Mon – Sat, 9am – 7pm",
    "opening_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    "opens": "09:00",
    "closes": "19:00",
    # Social profiles, shown as buttons on the right edge of every page. Empty = hidden.
    "linkedin_url": "https://www.linkedin.com/company/arcooling/",
    "x_url": "https://x.com/arcooling_in",
    "facebook_url": "https://www.facebook.com/profile.php?id=61555687123321",
    "instagram_url": "https://www.instagram.com/arcooling_in/",
    "city": "Hyderabad",
    # The Google map in the contact section shows the shop's Google Maps listing: its exact
    # name there, its pin ("latitude,longitude"), the zoom (higher = closer; 17 shows the
    # street) and the listing's own link for "Open in Google Maps".
    "map_query": "AR Cooling Solutions - AC Spare Parts & Services",
    "map_center": "17.4904683,78.4507238",
    "map_zoom": 17,
    "map_url": "https://www.google.com/maps?cid=7070758302627232181",
}
SPARE_ENQUIRY_CATEGORIES = (
    "Copper coils",
    "Compressors",
    "Capacitors",
    "Fan motors",
    "PCBs",
    "Remote controls",
    "Filters",
    "Refrigerant gases",
    "Valves",
    "Filter driers & accumulators",
    "Coils",
    "Controllers",
)
PRODUCT_FAMILIES = (
    {
        "id": "room-products",
        "name": "Room air conditioning",
        "short_name": "Room systems",
        "icon": "home",
        "description": "Independent systems for bedrooms, living spaces, shops and other individual rooms.",
    },
    {
        "id": "light-commercial-products",
        "name": "Light commercial systems",
        "short_name": "Light commercial",
        "icon": "fan",
        "description": "Flexible ceiling, concealed and packaged systems for offices, retail, hospitality and larger rooms.",
    },
    {
        "id": "central-products",
        "name": "Central, multi-zone and critical cooling",
        "short_name": "Central HVAC",
        "icon": "building",
        "description": "Scalable plant, zoned and precision systems for buildings, facilities and continuous cooling loads.",
    },
)
SERVICE_GROUPS = (
    {
        "id": "installation-setup",
        "name": "Installation & setup",
        "icon": "install",
        "description": "New installations, concealed piping before interiors, and safe relocation of existing units.",
    },
    {
        "id": "repairs",
        "name": "Repairs & troubleshooting",
        "icon": "wrench",
        "description": "Root-cause diagnosis and repair: cooling faults, gas leaks, compressors and control boards.",
    },
    {
        "id": "cleaning-maintenance",
        "name": "Cleaning & maintenance",
        "icon": "calendar",
        "description": "AMC plans, deep cleaning and duct cleaning that keep systems efficient and air clean.",
    },
    {
        "id": "commercial",
        "name": "Commercial projects",
        "icon": "building",
        "description": "Design, supply, installation and upkeep of HVAC systems for businesses and facilities.",
    },
)
BRAND_LOGOS = {
    "Blue Star": "blue_star.png",
    "Carrier": "carrier.png",
    "Copeland": "copeland.png",
    "Daikin": "daikin.png",
    "Danfoss": "danfosss.png",
    "O General": "general.png",
    "Godrej": "godrej.png",
    "Haier": "haier.png",
    "Hitachi": "hitachi.png",
    "LG": "lg.png",
    "Lloyd": "llyod.png",
    "Mandev": "mandev.png",
    "Mitsubishi Electric": "mistubushi_electric.png",
    "Mitsubishi Heavy Industries": "mistubushi_heavy.png",
    "Panasonic": "panasonic.png",
    "Rajco": "rajco.png",
    "Samsung": "samsung.png",
    "Toshiba": "toshiba.png",
    "Totaline": "totaline.png",
    "Trane": "trane.png",
    "V-Guard": "vguard.png",
    "Voltas": "voltas.png",
}
CLIENT_LOGOS = {
    "Aizant": "aizant.png",
    "Aureole Pharma-Tech": "aurelo.png",
    "Azad Engineering": "azad.png",
    "Biophore": "biophore.png",
    "Charge Infra": "charge_infra.png",
    "Granules": "granules.png",
    "Hetero": "hetero.png",
    "Kreative Organics": "kreative.png",
    "LuLu": "lulu.png",
    "Mack Pharmatech": "mack.png",
    "Maithri": "maithri.png",
    "MEIL": "meil.png",
    "Metrochem API": "metrochem.png",
    "Resolute": "quad.png",
    "Urban Kisaan": "urban_kisaan.png",
    "Wow! Momo": "wow_momo.png",
}


def get_product_categories():
    return tuple(product["name"] for product in get_product_types())


def get_service_categories():
    return tuple(service["name"] for service in get_services())


def get_enquiry_type(category):
    if category in SPARE_ENQUIRY_CATEGORIES:
        return "spare"
    if category in get_service_categories():
        return "service"
    if category in get_product_categories():
        return "product"
    return "general"   # "Other" and anything unrecognised


def get_enquiry_items():
    """What each Enquire link can point at, for the form's "You're enquiring about" card.

    The static enquiry page reads its query string in the browser, so this lookup is
    embedded in the page as JSON. Keys match the link parameters: product=, service=, part=.
    """
    items = {}
    for product in get_product_types():
        items[f"product:{product['slug']}"] = {
            "name": product["name"], "image": item_image(product), "icon": product.get("icon") or "snow",
            "url": url_for("product_detail", slug=product["slug"]),
            "meta": " · ".join(filter(None, (product.get("capacity"), product.get("use_case")))),
            "kind": "product",
        }
    for service in get_services():
        items[f"service:{service['slug']}"] = {
            "name": service["name"], "image": item_image(service), "icon": service.get("icon") or "wrench",
            "url": url_for("service_detail", slug=service["slug"]),
            "meta": service.get("duration", ""), "kind": "service",
        }
    for category in get_spare_categories():
        for part in category.get("parts", []):
            items[f"part:{part['name']}"] = {
                "name": part["name"], "image": item_image(part), "icon": category.get("icon") or "spark",
                "url": spare_part_url(category, part),
                "meta": category["name"], "kind": "part",
            }
    for model in get_compressor_models():
        items[f"part:{model['name']}"] = {
            "name": model["name"], "image": item_image(model), "icon": "compressor",
            "url": url_for("compressor_detail", slug=model["slug"]),
            "meta": " · ".join(filter(None, (model["series"]["name"], model["capacity"]))), "kind": "part",
        }
    return items


TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = Flask(
    __name__,
    template_folder=str(TEMPLATE_DIR),
    static_folder=str(STATIC_DIR),
)


def load_secret_key():
    """The key that signs the local admin login cookie.

    It must come from the environment (.env), never the code, which is public on GitHub.
    The static build generates a throwaway key, since the live site has no logins.
    """
    key = os.environ.get("SECRET_KEY", "")
    if len(key) < 32:
        raise RuntimeError(
            "SECRET_KEY is missing or shorter than 32 characters. Generate one with\n"
            '    python -c "import secrets; print(secrets.token_hex(32))"\n'
            "and set it in .env (local) or in your host's environment settings."
        )
    return key


app.config.update(
    SECRET_KEY=load_secret_key(),
    SESSION_COOKIE_HTTPONLY=True,        # page scripts can't read the cookie
    SESSION_COOKIE_SAMESITE="Lax",       # not sent with form posts from other sites
    # Form tokens last as long as the browser session, so a form left open isn't rejected.
    WTF_CSRF_TIME_LIMIT=None,
)

# On the server, Caddy handles HTTPS and passes requests on to the app (deploy/oracle/).
# AR_BEHIND_PROXY=1 makes the app trust Caddy's "the visitor used https" headers, and only
# send the admin login cookie over HTTPS. Leave it unset when running on your own PC.
if os.environ.get("AR_BEHIND_PROXY") == "1":
    from werkzeug.middleware.proxy_fix import ProxyFix

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    app.config["SESSION_COOKIE_SECURE"] = True

# Every admin POST form must carry a token from our own pages (blocks forged cross-site submissions).
csrf = CSRFProtect(app)

CSRF_RETRY_MESSAGE = "Your session expired before the form was sent. Please check the details and submit again."

_static_versions = {}


@app.url_defaults
def add_static_version(endpoint, values):
    """Add ?v=<content hash> to every static file URL, so browsers fetch a changed
    stylesheet, script or image right after a deploy instead of a cached copy."""
    if endpoint != "static" or "filename" not in values:
        return
    path = STATIC_DIR / values["filename"]
    if not path.is_file():
        return
    stamp = path.stat().st_mtime_ns
    cached = _static_versions.get(path)
    if not cached or cached[0] != stamp:
        cached = (stamp, hashlib.sha256(path.read_bytes()).hexdigest()[:10])
        _static_versions[path] = cached
    values["v"] = cached[1]


SNOW_EFFECT = True   # gentle falling snow in the background of every page; False turns it off

# Item photos without an "image" in the data file: drop static/images/<slug>.webp in and
# the card shows it. Until then the card keeps its icon placeholder.
OG_BANNER = "images/og-banner.jpg"   # 1200x630 share image, made by tools/make_og_banner.py


@app.template_global()
def faq_schema(faqs):
    """FAQPage structured data (schema.org) for Google, from question/answer pairs."""
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": faq["question"], "acceptedAnswer": {"@type": "Answer", "text": faq["answer"]}}
            for faq in faqs
        ],
    }


@app.template_global()
def item_image(item):
    """Photo URL for a product, service or part: its own "image", else /static/images/<slug>.webp
    when that file exists, else "" (the icon placeholder is shown)."""
    if item.get("image"):
        return item["image"]
    filename = f"images/{item.get('slug') or slugify(item['name'])}.webp"
    if (STATIC_DIR / filename).is_file():
        return url_for("static", filename=filename)
    return ""


def get_social_profiles():
    """(network, label, url) for each social profile that has a URL, in display order."""
    networks = [("linkedin", "LinkedIn"), ("x", "X"), ("facebook", "Facebook"), ("instagram", "Instagram")]
    return [(key, label, BUSINESS[f"{key}_url"]) for key, label in networks if BUSINESS.get(f"{key}_url")]


def get_nav_menus():
    """Dropdowns in the main menu, by nav key: (group name, group link, [(item name, item link)])."""
    products, services = get_product_types(), get_services()
    return {
        "products": [
            (family["short_name"], f"/products/#{family['id']}",
             [(p["name"], f"/products/{p['slug']}/") for p in products if p.get("family") == family["id"]])
            for family in PRODUCT_FAMILIES
        ],
        "services": [
            (group["name"], f"/services/#{group['id']}", items)
            for group in SERVICE_GROUPS
            if (items := [(s["name"], f"/services/{s['slug']}/") for s in services if s.get("group") == group["id"]])
        ],
        # Spare parts have no pages of their own, so the menu lists the categories.
        "parts": [
            ("Categories", "/parts/", [(c["name"], f"/parts/#{c['slug']}") for c in get_spare_categories()]),
            ("Compressor models", "/parts/compressors/",
             [(b["brand"], f"/parts/compressors/#{b['slug']}") for b in get_compressor_brands()]),
        ],
    }


@app.context_processor
def inject_site_settings():
    """Logos (shown above the footer on every page) and site-wide settings."""
    return {
        "brand_logos": BRAND_LOGOS,
        "client_logos": CLIENT_LOGOS,
        "site_url": SITE_URL,
        "snow_effect": SNOW_EFFECT,
        "og_banner": OG_BANNER,
        "social_profiles": get_social_profiles(),
        "nav_menus": get_nav_menus(),
        # The quick enquiry form in the contact section (see static/js/contact.js).
        "contact_endpoint": formsubmit_endpoint(ENQUIRY_INBOXES["general"]),
        "contact_fallback_action": formsubmit_endpoint(ENQUIRY_INBOXES["general"], ajax=False),
    }


@app.template_global()
def product_enquiry_url(product, variant=None):
    """Enquiry form link prefilled with a product (and optionally one capacity option)."""
    summary = product["name"]
    if variant:
        summary += f" – {variant['capacity']}"
        if variant.get("suits"):
            summary += f" ({variant['suits']})"
    elif product.get("capacity"):
        summary += f" – capacity range {product['capacity']}"
    details = [summary]
    if product.get("use_case"):
        details.append(f"Application: {product['use_case']}")
    details.append("Quantity: 1")
    return url_for(
        "product_enquiry",
        product=product["slug"],
        category=product["name"],
        product_description="\n".join(details),
        comments=f"Please share price, availability and installation details for {product['name']}.",
    )


@app.template_global()
def service_enquiry_url(service, option=None):
    """Enquiry form link prefilled with a service (and optionally one service option)."""
    summary = f"{service['name']} service"
    if option:
        summary += f" – {option['name']}"
    details = [summary, "AC brand / type: ", "Number of units: 1"]
    return url_for(
        "product_enquiry",
        service=service["slug"],
        category=service["name"],
        product_description="\n".join(details),
        comments="Please contact me to schedule a visit.",
    )


@app.template_global()
def spare_enquiry_url(category, part=None):
    """Enquiry form link prefilled with a spare-part category (and optionally one part)."""
    item_name = part["name"] if part else category["name"]
    details = [f"{item_name} ({category['name']})", "AC brand / model: ", "Quantity: 1"]
    params = {
        "category": category["enquiry_category"],
        "product_description": "\n".join(details),
        "comments": "Please confirm compatibility, price and availability.",
    }
    if part:
        params["part"] = part["name"]
    return url_for("product_enquiry", **params)


# Spare-part categories whose parts have a page of their own: category slug -> endpoint.
SPARE_DETAIL_ENDPOINTS = {"gases": "gas_detail", "copper-coils": "copper_detail"}
app.add_template_global(SPARE_DETAIL_ENDPOINTS, "spare_detail_endpoints")


@app.template_global()
def spare_part_url(category, part):
    """A part's own page if it has one, otherwise its category on the spare parts page."""
    endpoint = SPARE_DETAIL_ENDPOINTS.get(category["slug"])
    if endpoint and part.get("slug"):
        return url_for(endpoint, slug=part["slug"])
    if part.get("slug") and part.get("specs"):
        if category["slug"] == "compressors":  # shares /parts/compressors/ with the model pages
            return url_for("compressor_detail", slug=part["slug"])
        return url_for("part_detail", category_slug=category["slug"], slug=part["slug"])
    return url_for("spare_parts") + f"#{category['slug']}"


def get_spec_parts():
    """(category, part) for every spare part with its own specification page (part_detail.html)."""
    return [(c, p) for c in get_spare_categories() if c["slug"] not in SPARE_DETAIL_ENDPOINTS
            for p in c["parts"] if p.get("slug") and p.get("specs")]


def render_part_detail(category, item):
    return render_template("part_detail.html", business=BUSINESS, category=category, item=item)


def get_spare_category(slug):
    return next((c for c in get_spare_categories() if c["slug"] == slug), None)


def admin_required(view):
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    wrapped.__name__ = view.__name__
    return wrapped


@app.get("/")
def home():
    return render_template(
        "index.html",
        business=BUSINESS,
        services=get_services(),
        products=get_product_types(),
        stats=load_home_items("stats"),
        testimonials=load_home_items("testimonials"),
        faqs=load_home_items("faqs"),
    )


@app.get("/services/")
def services():
    return render_template(
        "services.html",
        business=BUSINESS,
        services=get_services(),
        groups=SERVICE_GROUPS,
    )


@app.get("/services/<slug>/")
def service_detail(slug):
    service = get_service(slug)
    if service is None:
        abort(404)
    all_services = get_services()
    related = [s for s in all_services if s.get("group") == service.get("group") and s["slug"] != slug]
    related += [s for s in all_services if s not in related and s["slug"] != slug]
    related = related[:3]
    return render_template(
        "service_detail.html",
        business=BUSINESS,
        service=service,
        related=related,
    )


@app.get("/about/")
def about():
    return render_template("about.html", business=BUSINESS)


@app.get("/clients/")
def clients():
    return render_template("clients.html", business=BUSINESS)


@app.get("/parts/")
def spare_parts():
    return render_template(
        "spare_parts.html",
        business=BUSINESS,
        categories=get_spare_categories(),
        featured_spare=get_featured_spare(),
        compressor_brands=get_compressor_brands(),
    )


def get_compressor_category():
    return get_spare_category("compressors")


@app.get("/parts/compressors/")
def compressors():
    return render_template(
        "compressors.html",
        business=BUSINESS,
        category=get_compressor_category(),
        brands=get_compressor_brands(),
    )


@app.get("/parts/compressors/<slug>/")
def compressor_detail(slug):
    model = get_compressor_model(slug)
    if model is None:
        # compressor types (rotary, scroll, ...) have spec pages at the same level as the models
        category = get_compressor_category()
        item = next((p for p in category["parts"] if p.get("slug") == slug and p.get("specs")), None)
        if item is None:
            abort(404)
        return render_part_detail(category, item)
    return render_template(
        "compressor_detail.html",
        business=BUSINESS,
        category=get_compressor_category(),
        model=model,
        specs=compressor_specs(model),
    )


@app.get("/parts/copper-coils/<slug>/")
def copper_detail(slug):
    category = get_spare_category("copper-coils")
    item = next((p for p in category["parts"] if p.get("slug") == slug), None)
    if item is None:
        abort(404)
    if not item.get("size_chart"):  # accessories without a size guide use the general spec page
        return render_part_detail(category, item)
    return render_template("copper_detail.html", business=BUSINESS, category=category, item=item)


@app.get("/parts/gases/<slug>/")
def gas_detail(slug):
    category = get_spare_category("gases")
    gas = next((g for g in category["parts"] if g.get("slug") == slug), None)
    if gas is None:
        abort(404)
    return render_template("gas_detail.html", business=BUSINESS, category=category, gas=gas)


@app.get("/parts/<category_slug>/<slug>/")
def part_detail(category_slug, slug):
    category = get_spare_category(category_slug)
    if category is None or category_slug in SPARE_DETAIL_ENDPOINTS:
        abort(404)
    item = next((p for p in category["parts"] if p.get("slug") == slug and p.get("specs")), None)
    if item is None:
        abort(404)
    return render_part_detail(category, item)


@app.get("/products/")
def products():
    return render_template(
        "products.html",
        business=BUSINESS,
        products=get_product_types(),
        families=PRODUCT_FAMILIES,
    )


@app.get("/products/<slug>/")
def product_detail(slug):
    product = get_product(slug)
    if product is None:
        abort(404)
    family = next((f for f in PRODUCT_FAMILIES if f["id"] == product.get("family")), None)
    related = [
        p for p in get_product_types()
        if p.get("family") == product.get("family") and p["slug"] != slug
    ]
    return render_template(
        "product_detail.html",
        business=BUSINESS,
        product=product,
        family=family,
        related=related,
    )


# Admin addresses also work with a trailing slash (/admin/, /admin/login/), as typed or
# autocompleted; public pages keep one address each, which search engines prefer.
@app.get("/admin", strict_slashes=False)
@admin_required
def admin_dashboard():
    product_entries = get_product_types()
    spare_entries = get_spare_categories()
    return render_template(
        "admin_dashboard.html",
        business=BUSINESS,
        products=product_entries,
        spares=spare_entries,
        compressor_brands=get_compressor_brands(),
        services=get_services(),
    )


ADMIN_DISABLED_MESSAGE = (
    "Admin login is not set up. Set AR_ADMIN_USERNAME and AR_ADMIN_PASSWORD "
    f"(at least {ADMIN_MIN_PASSWORD_LENGTH} characters) in the server environment."
)


@app.get("/admin/login", strict_slashes=False)
def admin_login():
    error = None if ADMIN_ENABLED else ADMIN_DISABLED_MESSAGE
    return render_template("admin_login.html", business=BUSINESS, error=error)


@app.post("/admin/login")
def admin_login_submit():
    if not ADMIN_ENABLED:
        return render_template("admin_login.html", business=BUSINESS, error=ADMIN_DISABLED_MESSAGE), 503

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    # compare_digest takes the same time whether or not the start of the value matches.
    username_ok = secrets.compare_digest(username.encode(), ADMIN_USERNAME.encode())
    password_ok = secrets.compare_digest(password.encode(), ADMIN_PASSWORD.encode())
    if username_ok and password_ok:
        session.clear()
        session["admin_logged_in"] = True
        return redirect(url_for("admin_dashboard"))

    return render_template(
        "admin_login.html",
        business=BUSINESS,
        error="Invalid username or password.",
    ), 401


@app.post("/admin/logout")
def admin_logout():
    # POST (with a form token) so other sites can't log you out with a link.
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


@app.get("/admin/<collection>/<item_name>/edit")
@admin_required
def admin_edit(collection, item_name):
    name = resolve_record_name(collection, item_name)
    if name is None:
        return redirect(url_for("admin_dashboard"))

    record = store.get_record(collection, name)
    json_text = json.dumps(record, indent=2, ensure_ascii=False)
    return render_template(
        "admin_edit.html",
        business=BUSINESS,
        collection=collection,
        item_name=name,
        json_text=json_text,
    )


@app.post("/admin/<collection>/<item_name>/edit")
@admin_required
def admin_save(collection, item_name):
    name = resolve_record_name(collection, item_name)
    if name is None:
        return redirect(url_for("admin_dashboard"))

    raw_json = request.form.get("json_data", "")
    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError:
        parsed = None
    if not isinstance(parsed, dict):   # every record is a JSON object; anything else would break the pages
        return render_template(
            "admin_edit.html",
            business=BUSINESS,
            collection=collection,
            item_name=name,
            json_text=raw_json,
            error="Invalid JSON. Please correct the content and try again.",
        )

    store.save_record(collection, name, parsed)   # the previous version is kept in the edit history
    return redirect(url_for("admin_dashboard"))


@app.get("/enquiry/")
def product_enquiry():
    """The enquiry form. It is static: the browser fills it in from the link's query string
    and sends it to FormSubmit, which emails it to the enquiry inbox."""
    product_categories = get_product_categories()
    service_categories = get_service_categories()
    return render_template(
        "product_enquiry.html",
        business=BUSINESS,
        product_categories=product_categories,
        service_categories=service_categories,
        spare_categories=SPARE_ENQUIRY_CATEGORIES,
        category_types={c: get_enquiry_type(c) for c in product_categories + service_categories + SPARE_ENQUIRY_CATEGORIES},
        enquiry_items=get_enquiry_items(),
        enquiry_endpoints=get_enquiry_endpoints(),
        fallback_action=formsubmit_endpoint(ENQUIRY_INBOXES["general"], ajax=False),
    )


@app.get("/enquiry/thank-you/")
def enquiry_thanks():
    return render_template("enquiry_thanks.html", business=BUSINESS)


PRIVACY_UPDATED = "16 November 2026"   # change when the privacy policy text changes


@app.get("/privacy/")
def privacy():
    return render_template("privacy.html", business=BUSINESS, privacy_updated=PRIVACY_UPDATED)


# Social media posts (data/social/posts.json, pictures drawn by tools/make_social_posts.py).
# Each post gets a small share page at /go/<id>/: X, Facebook and LinkedIn read its tags to
# show the post's picture as a link card, and a visitor who clicks the card is sent straight
# on to the post's page on the site. Posts stay in the JSON file (not the content database),
# so a new post goes live as soon as it is pushed.
SOCIAL_POSTS_FILE = BASE_DIR / "data" / "social" / "posts.json"


def get_social_posts():
    if not SOCIAL_POSTS_FILE.is_file():
        return []
    return json.loads(SOCIAL_POSTS_FILE.read_text(encoding="utf-8"))


def social_post_image_exists(post):
    return (STATIC_DIR / "images" / "social" / post["image"]).is_file()


def render_share_page(post):
    """The share page for one social post, as HTML."""
    share_url = f"{SITE_URL}/go/{post['id']}/"
    image_url = f"{SITE_URL}/static/images/social/{post['image']}"
    title, description, target = (html.escape(post[k], quote=True) for k in ("title", "description", "target"))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} | AR Cooling Solutions</title>
  <meta name="description" content="{description}">
  <meta name="robots" content="noindex, follow">
  <link rel="canonical" href="{SITE_URL}{target}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="AR Cooling Solutions">
  <meta property="og:url" content="{share_url}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:image" content="{image_url}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{image_url}">
  <script>location.replace("{target}");</script>
</head>
<body style="font-family:system-ui,sans-serif;text-align:center;padding:3rem 1rem">
  <p><a href="{target}">Continue to AR Cooling Solutions</a></p>
</body>
</html>
"""


@app.get("/go/<post_id>/")
def share_page(post_id):
    post = next((p for p in get_social_posts() if p.get("id") == post_id), None)
    if post is None or not social_post_image_exists(post):
        abort(404)
    return render_share_page(post)


# Pages that render but should not be offered to search engines.
NOT_IN_SITEMAP = {"/enquiry/thank-you/"}


def public_page_paths():
    """Every public page; a new kind of page must be added here, which puts it in the static
    build, the site check and the sitemap at once.
    Uses url_for, so call it inside a request (a live request already is one)."""
    paths = [url_for(endpoint) for endpoint in
             ("home", "products", "services", "spare_parts", "clients", "about", "product_enquiry", "enquiry_thanks", "privacy")]
    paths += [url_for("product_detail", slug=p["slug"]) for p in get_product_types()]
    paths += [url_for("service_detail", slug=s["slug"]) for s in get_services()]
    paths.append(url_for("compressors"))
    paths += [url_for("compressor_detail", slug=m["slug"]) for m in get_compressor_models()]
    paths += [url_for("gas_detail", slug=g["slug"]) for g in get_spare_category("gases")["parts"]]
    paths += [url_for("copper_detail", slug=c["slug"])
              for c in get_spare_category("copper-coils")["parts"] if c.get("slug")]
    paths += [spare_part_url(c, p) for c, p in get_spec_parts()]
    # Two records with the same slug must not list the same address twice.
    return list(dict.fromkeys(paths))


def sitemap_paths():
    return [path for path in public_page_paths() if path not in NOT_IN_SITEMAP]


def render_sitemap():
    """sitemap.xml for search engines, built from the current content on every request,
    so pages added or renamed in admin are listed straight away.
    lastmod is today's date, as the GitHub Pages build always did."""
    today = date.today().isoformat()
    # Escaped so a slug typed in admin with "&" or "<" cannot break the XML.
    urls = "".join(
        f"  <url><loc>{html.escape(SITE_URL + path, quote=False)}</loc><lastmod>{today}</lastmod></url>\n"
        for path in sitemap_paths()
    )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")


def render_robots_txt():
    """robots.txt: everything may be crawled except admin (the login is still the real lock)."""
    return f"User-agent: *\nAllow: /\nDisallow: /admin\n\nSitemap: {SITE_URL}/sitemap.xml\n"


@app.get("/sitemap.xml")
def sitemap():
    return Response(render_sitemap(), mimetype="application/xml")


@app.get("/robots.txt")
def robots_txt():
    return Response(render_robots_txt(), mimetype="text/plain")


@app.get("/favicon.ico")
def favicon():
    # Some browsers and tools ask for /favicon.ico without reading the page's <link> tags.
    # The type is fixed so it does not depend on the server's own list of file types.
    return send_from_directory(STATIC_DIR, "favicon.ico", mimetype="image/vnd.microsoft.icon", max_age=86400)


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html", business=BUSINESS), 404


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    """An admin form arrived without a valid token: show it again without losing what was typed."""
    if request.endpoint == "admin_save" and session.get("admin_logged_in"):
        return render_template(
            "admin_edit.html",
            business=BUSINESS,
            collection=request.view_args["collection"],
            item_name=request.view_args["item_name"],
            json_text=request.form.get("json_data", ""),
            error=CSRF_RETRY_MESSAGE,
        ), 400
    if request.endpoint in ("admin_login_submit", "admin_save", "admin_logout"):
        return render_template("admin_login.html", business=BUSINESS, error=CSRF_RETRY_MESSAGE), 400
    return CSRF_RETRY_MESSAGE, 400


if __name__ == "__main__":
    # Local preview and admin editing. The live site runs serve.py on the Oracle server.
    # Debug mode (auto-reload, error console) is on only when AR_DEBUG=1 in your local .env.
    app.run(debug=os.environ.get("AR_DEBUG", "0") == "1")