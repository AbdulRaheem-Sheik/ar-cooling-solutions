import json
import os
from pathlib import Path
from urllib.parse import quote

from flask import Flask, redirect, render_template, request, session, url_for


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PRODUCT_DATA_DIR = DATA_DIR / "products"
SPARE_DATA_DIR = DATA_DIR / "spares"
SERVICE_DATA_DIR = DATA_DIR / "services"
ADMIN_USERNAME = os.environ.get("AR_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("AR_ADMIN_PASSWORD", "admin123")


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


def get_spare_categories():
    return load_json_records(SPARE_DATA_DIR, exclude_names=("featured-spare.json",))


def get_services():
    return load_json_records(SERVICE_DATA_DIR)


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
    "email": "mailtoabdul1@gmail.com",
    "city": "Hyderabad",
}
PRODUCT_CATEGORIES = (
    "Copper coils",
    "Compressors",
    "Capacitors",
    "Fan motors",
    "PCBs",
    "Remote controls",
    "Filters",
    "Split AC units",
    "Cassette AC units",
    "Ductable AC units",
    "Tower AC units",
    "Package AC units",
    "Water chillers",
    "AHU units",
    "VRV & VRF units",
    "Other",
)
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = Flask(
    __name__,
    template_folder=str(TEMPLATE_DIR),
    static_folder=str(STATIC_DIR),
)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "ar-cooling-admin-secret")


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


@app.get("/services")
def services():
    return render_template("services.html", business=BUSINESS, services=get_services())


@app.get("/about")
def about():
    return render_template("about.html", business=BUSINESS)


@app.get("/parts")
def spare_parts():
    return render_template(
        "spare_parts.html",
        business=BUSINESS,
        categories=get_spare_categories(),
        featured_spare=get_featured_spare(),
    )


@app.get("/products")
def products():
    return render_template(
        "products.html",
        business=BUSINESS,
        products=get_product_types(),
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


@app.get("/admin/login")
def admin_login():
    return render_template("admin_login.html", business=BUSINESS, error=None)


@app.post("/admin/login")
def admin_login_submit():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session["admin_logged_in"] = True
        return redirect(url_for("admin_dashboard"))

    return render_template(
        "admin_login.html",
        business=BUSINESS,
        error="Invalid username or password.",
    )


@app.get("/admin/logout")
def admin_logout():
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


@app.route("/enquiry", methods=["GET", "POST"])
def product_enquiry():
    submitted_values = request.form if request.method == "POST" else request.args
    form = {
        field: submitted_values.get(field, "").strip()
        for field in ("name", "company_name", "email", "mobile", "category", "product_description", "comments")
    }
    errors = []

    if request.method == "POST":
        if not form["name"]:
            errors.append("Enter your name.")
        if not form["company_name"]:
            errors.append("Enter your company name.")
        if not form["email"] or "@" not in form["email"] or "." not in form["email"].rsplit("@", 1)[-1]:
            errors.append("Enter a valid email address.")
        if not form["mobile"] or len(form["mobile"]) > 24:
            errors.append("Enter a valid mobile number.")
        if form["category"] not in PRODUCT_CATEGORIES:
            errors.append("Choose a product category.")
        if not form["product_description"]:
            errors.append("Describe the product you need.")
        if len(form["name"]) > 120 or len(form["company_name"]) > 150 or len(form["email"]) > 254 or len(form["product_description"]) > 1000 or len(form["comments"]) > 1000:
            errors.append("One or more answers exceed the allowed length.")

        if not errors:
            message = "\n".join(
                (
                    "Product enquiry",
                    f"Name: {form['name']}",
                    f"Company: {form['company_name']}",
                    f"Email: {form['email']}",
                    f"Mobile: {form['mobile']}",
                    f"Category: {form['category']}",
                    f"Product description: {form['product_description']}",
                    f"Comments: {form['comments'] or 'None'}",
                )
            )
            return redirect(
                f"https://wa.me/{BUSINESS['whatsapp_number']}?text={quote(message)}"
            )

    return render_template(
        "product_enquiry.html",
        business=BUSINESS,
        categories=PRODUCT_CATEGORIES,
        form=form,
        errors=errors,
    ), (400 if errors else 200)


if __name__ == "__main__":
    app.run(debug=True)