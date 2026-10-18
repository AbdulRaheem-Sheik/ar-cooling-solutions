import hashlib
import json
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect


BASE_DIR = Path(__file__).resolve().parent
# Settings and secrets come from the environment; locally they live in .env (never committed).
load_dotenv(BASE_DIR / ".env")
DATA_DIR = BASE_DIR / "data"
PRODUCT_DATA_DIR = DATA_DIR / "products"
SPARE_DATA_DIR = DATA_DIR / "spares"
SERVICE_DATA_DIR = DATA_DIR / "services"

# The live site is static (GitHub Pages), built by tools/build_static.py.
SITE_URL = os.environ.get("AR_SITE_URL", "https://arcooling.in").rstrip("/")
# Enquiries are emailed to you by Web3Forms (free). Get a key at https://web3forms.com.
# The key is designed to sit in public HTML: it can only send to your own inbox.
WEB3FORMS_ACCESS_KEY = os.environ.get("WEB3FORMS_ACCESS_KEY", "").strip()

# Each enquiry type is emailed to its own team. A Web3Forms key delivers only to the address
# that created it, so every team inbox has its own key. Until a team's key is set, its
# enquiries use WEB3FORMS_ACCESS_KEY.
ENQUIRY_TEAMS = {
    "product": {"team": "Sales", "email": "sales@arcooling.in", "key_env": "WEB3FORMS_KEY_SALES"},
    "spare": {"team": "Sales", "email": "sales@arcooling.in", "key_env": "WEB3FORMS_KEY_SALES"},
    "service": {"team": "Services", "email": "services@arcooling.in", "key_env": "WEB3FORMS_KEY_SERVICES"},
    "general": {"team": "Enquiry", "email": "enquiry@arcooling.in", "key_env": "WEB3FORMS_KEY_ENQUIRY"},
}


def get_enquiry_keys():
    """Web3Forms key for each enquiry type, falling back to the shared key."""
    return {
        kind: os.environ.get(team["key_env"], "").strip() or WEB3FORMS_ACCESS_KEY
        for kind, team in ENQUIRY_TEAMS.items()
    }
# Admin is a local editing tool (it is not part of the static site). It has no built-in
# default login: it stays disabled until both values are set in .env.
ADMIN_USERNAME = os.environ.get("AR_ADMIN_USERNAME", "").strip()
ADMIN_PASSWORD = os.environ.get("AR_ADMIN_PASSWORD", "")
ADMIN_MIN_PASSWORD_LENGTH = 12
ADMIN_ENABLED = bool(ADMIN_USERNAME) and len(ADMIN_PASSWORD) >= ADMIN_MIN_PASSWORD_LENGTH


def load_json_file(file_path):
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_json_records(folder_path, exclude_names=()):
    records = []
    for file_path in sorted(folder_path.glob("*.json")):
        if file_path.name in exclude_names:
            continue
        records.append(load_json_file(file_path))
    return tuple(records)


def get_product_types():
    return load_json_records(PRODUCT_DATA_DIR)


def get_product(slug):
    for product in get_product_types():
        if product.get("slug") == slug:
            return product
    return None


def get_spare_categories():
    return load_json_records(SPARE_DATA_DIR, exclude_names=("featured-spare.json",))


def get_services():
    return load_json_records(SERVICE_DATA_DIR)


def get_service(slug):
    for service in get_services():
        if service.get("slug") == slug:
            return service
    return None


def get_featured_spare():
    return load_json_file(SPARE_DATA_DIR / "featured-spare.json")


COLLECTION_DIRS = {
    "products": PRODUCT_DATA_DIR,
    "spares": SPARE_DATA_DIR,
    "services": SERVICE_DATA_DIR,
}


def resolve_data_file(collection, item_name):
    data_dir = COLLECTION_DIRS.get(collection)
    if data_dir is None:
        return None

    exact_path = data_dir / f"{item_name}.json"
    if exact_path.exists():
        return exact_path

    for file_path in sorted(data_dir.glob("*.json")):
        if file_path.name == "featured-spare.json":
            continue
        record = load_json_file(file_path)
        if record.get("slug") == item_name:
            return file_path
    return None


BUSINESS = {
    "name": "AR Cooling Solutions",
    "phone_display": "+91 88013 81405",
    "phone_e164": "+918801381405",
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
    "city": "Hyderabad",
}
SPARE_ENQUIRY_CATEGORIES = (
    "Copper coils",
    "Compressors",
    "Capacitors",
    "Fan motors",
    "PCBs",
    "Remote controls",
    "Filters",
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
    "Mexflow": "mexflow.png",
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
    "Meil": "meil.png",
    "Azad Engineering": "azad.png",
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
            "name": product["name"], "image": product.get("image") or "", "icon": product.get("icon") or "snow",
            "url": url_for("product_detail", slug=product["slug"]),
            "meta": " · ".join(filter(None, (product.get("capacity"), product.get("use_case")))),
            "kind": "product",
        }
    for service in get_services():
        items[f"service:{service['slug']}"] = {
            "name": service["name"], "image": service.get("image") or "", "icon": service.get("icon") or "wrench",
            "url": url_for("service_detail", slug=service["slug"]),
            "meta": service.get("duration", ""), "kind": "service",
        }
    for category in get_spare_categories():
        for part in category.get("parts", []):
            items[f"part:{part['name']}"] = {
                "name": part["name"], "image": part.get("image") or "", "icon": category.get("icon") or "spark",
                "url": url_for("spare_parts") + f"#{category['slug']}",
                "meta": category["name"], "kind": "part",
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


@app.context_processor
def inject_site_settings():
    """Logos (shown above the footer on every page) and site-wide settings."""
    return {"brand_logos": BRAND_LOGOS, "client_logos": CLIENT_LOGOS, "site_url": SITE_URL}


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
    return render_template("about.html", business=BUSINESS, product_count=len(get_product_types()))


@app.get("/parts/")
def spare_parts():
    return render_template(
        "spare_parts.html",
        business=BUSINESS,
        categories=get_spare_categories(),
        featured_spare=get_featured_spare(),
    )


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


@app.get("/admin")
@admin_required
def admin_dashboard():
    product_entries = get_product_types()
    spare_entries = get_spare_categories()
    return render_template(
        "admin_dashboard.html",
        business=BUSINESS,
        products=product_entries,
        spares=spare_entries,
        services=get_services(),
    )


ADMIN_DISABLED_MESSAGE = (
    "Admin login is not set up. Set AR_ADMIN_USERNAME and AR_ADMIN_PASSWORD "
    f"(at least {ADMIN_MIN_PASSWORD_LENGTH} characters) in the server environment."
)


@app.get("/admin/login")
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
    file_path = resolve_data_file(collection, item_name)
    if file_path is None:
        return redirect(url_for("admin_dashboard"))

    record = load_json_file(file_path)
    json_text = json.dumps(record, indent=2, ensure_ascii=False)
    return render_template(
        "admin_edit.html",
        business=BUSINESS,
        collection=collection,
        item_name=file_path.stem,
        json_text=json_text,
    )


@app.post("/admin/<collection>/<item_name>/edit")
@admin_required
def admin_save(collection, item_name):
    file_path = resolve_data_file(collection, item_name)
    if file_path is None:
        return redirect(url_for("admin_dashboard"))

    raw_json = request.form.get("json_data", "")
    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError:
        return render_template(
            "admin_edit.html",
            business=BUSINESS,
            collection=collection,
            item_name=file_path.stem,
            json_text=raw_json,
            error="Invalid JSON. Please correct the content and try again.",
        )

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(parsed, file, indent=2, ensure_ascii=False)
        file.write("\n")

    return redirect(url_for("admin_dashboard"))


@app.get("/enquiry/")
def product_enquiry():
    """The enquiry form. It is static: the browser fills it in from the link's query string
    and sends it to Web3Forms, which emails it to you."""
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
        web3forms_access_key=WEB3FORMS_ACCESS_KEY,
        enquiry_keys=get_enquiry_keys(),
    )


@app.get("/enquiry/thank-you/")
def enquiry_thanks():
    return render_template("enquiry_thanks.html", business=BUSINESS)


PRIVACY_UPDATED = "16 October 2026"   # change when the privacy policy text changes


@app.get("/privacy/")
def privacy():
    return render_template("privacy.html", business=BUSINESS, privacy_updated=PRIVACY_UPDATED)


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
    # Local preview and admin editing. The live site is the static build (tools/build_static.py).
    # Debug mode (auto-reload, error console) is on only when AR_DEBUG=1 in your local .env.
    app.run(debug=os.environ.get("AR_DEBUG", "0") == "1")