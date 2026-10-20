# AR Cooling Solutions website

Website for AR Cooling Solutions, Hyderabad: AC & HVAC products, services and spare parts.
Live at **https://arcooling.in** (GitHub Pages).

## How it works

- The pages are Flask/Jinja templates (`templates/`) filled from JSON data (`data/`).
- `tools/build_static.py` renders every public page to plain HTML in `_site/`.
- On every push to `main`, the GitHub Action (`.github/workflows/deploy.yml`) runs that
  build and publishes `_site/` to GitHub Pages. There is no server.
- The enquiry form is sent by the visitor's browser to [FormSubmit](https://formsubmit.co),
  which emails each enquiry as a table (with a reference like `AR-261016-4821`) to
  enquiry@arcooling.in. Change the inbox per enquiry type in `ENQUIRY_INBOXES` in `app.py`.
  The subject and the "Enquiry type" row say whether it is a product, service or spare part.

## Run it locally

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env        # then fill in the values (see comments in the file)
.venv\Scripts\python app.py   # preview at http://127.0.0.1:5000
```

The admin editor (`/admin`) runs only locally: edit products, services or spares there,
then commit and push; the live site rebuilds automatically.

To preview the exact static site that will be published:

```
.venv\Scripts\python tools\build_static.py --serve   # http://127.0.0.1:8000
```

## Editing content

| What | Where |
|---|---|
| Products, services, spare parts | `data/products/`, `data/services/`, `data/spares/` (or the local admin) |
| Business name, phone, email, city | `BUSINESS` in `app.py` |
| Product / service photos | put them in `static/images/products/` or `services/`, set `"image"` in the data file, then run `python tools/optimize_images.py` (needs `pip install pillow`) |
| Partner and client logos | add the image, run `python tools/process_logos.py` (needs `pip install pillow`), add it to `BRAND_LOGOS` / `CLIENT_LOGOS` in `app.py` |
| Colours, fonts, layout | `static/css/style.css` |

## Deploying (one-time setup)

1. **Activate the enquiry form** (once per inbox): send one enquiry from the live site.
   FormSubmit emails that inbox an "Activate form" link; click it. Until then enquiries are held.
2. *(no keys or repository variables are needed)*
3. **Enable Pages**: repo **Settings > Pages > Build and deployment > Source: GitHub Actions**.
   (Free GitHub accounts need a public repository for Pages.)
4. **Push to `main`.** The Actions tab shows the build; it fails loudly if a link is broken
   or the key is missing.
5. **Custom domain**: repo **Settings > Pages > Custom domain**: `arcooling.in`, then save.
6. **GoDaddy DNS** (My Products > arcooling.in > DNS). Remove any existing `A` record for `@`
   (GoDaddy's "Parked" record) and any `CNAME` for `www`, then add:

   | Type | Name | Value |
   |---|---|---|
   | A | @ | 185.199.108.153 |
   | A | @ | 185.199.109.153 |
   | A | @ | 185.199.110.153 |
   | A | @ | 185.199.111.153 |
   | CNAME | www | abdulraheem-sheik.github.io |

7. When GitHub shows the DNS check as successful (minutes to a few hours), tick
   **Enforce HTTPS** in Settings > Pages.
