# Image Fetcher

Find and download every image on a webpage. Flask backend, plain HTML/CSS/ES-module front end.

## Run locally (one click)
    python run.py
Installs missing packages, starts the server and opens your browser.

## Deploy
- **Render:** push this folder to GitHub, then New > Blueprint (uses `render.yaml`).
- **Railway / Koyeb / Heroku-style hosts:** uses `Procfile` (`gunicorn wsgi:app`).
- **PythonAnywhere:** in the WSGI file use
      import sys, os
      sys.path.insert(0, "/home/<user>/image-fetcher")
      os.environ["HOSTED"] = "1"
      from wsgi import application
  (free accounts can only reach whitelisted sites, so a paid plan is needed for general use)

Setting `PORT` or `HOSTED` switches on private-address blocking, rate limits and size caps.

## Layout
    run.py                     local launcher
    wsgi.py                    production entry point (gunicorn wsgi:app)
    imagefetcher/
      __init__.py              create_app() factory, security headers
      config.py                Settings (env-driven limits)
      routes.py                HTTP endpoints (blueprint)
      fetcher.py               all outgoing requests (redirect + size checks)
      security.py              SSRF guard, RateLimiter
      scraper.py               HTML parsing
      naming.py                file names / extensions
      archive.py               ZIP builder
      templates/               base.html, index.html, partials/
      static/css/              tokens.css, base.css, components.css
      static/js/               small ES modules (main.js is the entry)
    tests/test_app.py          python -m unittest discover -s tests -v
