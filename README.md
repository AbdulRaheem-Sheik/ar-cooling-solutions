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

The admin editor (`/admin`) runs only locally for now. It edits the content database
(below); to publish an edit, export it to `data/`, then commit and push, and the live site
rebuilds automatically.

### Content database

The app reads products, services, spare parts, compressor models and home page items from
a SQLite database (`store.py`), a single file at `instance/ar_cooling.db` (not committed;
`AR_DATABASE_PATH` moves it). The first time the app runs, it fills the database from the
JSON files in `data/`. Every admin save keeps the previous version, so edits can be undone.

```
.venv\Scripts\python store.py export            # write admin edits back to data/ (then commit)
.venv\Scripts\python store.py import --replace  # reload the database from data/ (after a git pull; discards unexported admin edits)
.venv\Scripts\python store.py history spares 01-copper-coils
.venv\Scripts\python store.py restore spares 01-copper-coils <version-id>
```

The static build always starts from `data/`, never from your local database, so only
what is committed goes live.

To run it the way a live server does (Waitress, no auto-reload), at http://127.0.0.1:8080:

```
.venv\Scripts\python serve.py
```

To move the whole site (with a working `/admin`) onto a free Oracle Cloud server instead of
GitHub Pages, follow [deploy/oracle/README.md](deploy/oracle/README.md).

To preview the exact static site that will be published:

```
.venv\Scripts\python tools\build_static.py --serve   # http://127.0.0.1:8000
```

## Editing content

| What | Where |
|---|---|
| Products, services, spare parts | `data/products/`, `data/services/`, `data/spares/`, then `python store.py import --replace` to see them locally (or edit in the local admin and `python store.py export`) |
| Business name, phone, email, city | `BUSINESS` in `app.py` |
| Product / service photos | put them in `static/images/products/` or `services/`, set `"image"` in the data file, then run `python tools/optimize_images.py` (needs `pip install pillow`) |
| Partner and client logos | add the image, run `python tools/process_logos.py` (needs `pip install pillow`), add it to `BRAND_LOGOS` / `CLIENT_LOGOS` in `app.py` |
| Colours, fonts, layout | `static/css/style.css` |
| Social media posts | add the post to `data/social/posts.json`, run `python tools/make_social_posts.py` to draw its pictures; the build publishes a share page at `/go/<id>/` that shows the picture as a link card and sends visitors on to the post's page |

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
