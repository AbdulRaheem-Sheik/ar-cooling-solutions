"""Run the website as a real (production) server with Waitress.

Waitress works on Windows and Linux, so this is exactly how the app runs on the Oracle
Cloud server, and also how to test that setup on your own PC:

    .venv\\Scripts\\python serve.py            # http://127.0.0.1:8080

On the server, Caddy (deploy/oracle/Caddyfile) sits in front of it, adds HTTPS for
arcooling.in and passes requests on; set AR_BEHIND_PROXY=1 there (see deploy/oracle/).

Settings (environment or .env): AR_HOST (default 127.0.0.1), AR_PORT (default 8080),
AR_THREADS (default 8). Use "python app.py" instead for development with auto-reload.
"""

import os

from waitress import serve

from app import app


def main():
    host = os.environ.get("AR_HOST", "127.0.0.1")
    port = int(os.environ.get("AR_PORT", "8080"))
    threads = int(os.environ.get("AR_THREADS", "8"))
    print(f"AR Cooling Solutions running at http://{host}:{port}  (Ctrl+C to stop)", flush=True)
    serve(app, host=host, port=port, threads=threads, ident="ar-cooling")


if __name__ == "__main__":
    main()
