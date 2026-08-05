"""FastAPI application.

Local, single-company, no authentication — see the design doc's scope section. CORS
is open to the Vite dev server only.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .routers import compute, scenario

app = FastAPI(
    title="Payroll Tax Optimization",
    description=(
        "Implements the model documented in PAYROLL_MODEL.md. Where this service and "
        "that document disagree, the document is right and this service has a bug."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scenario.router)
app.include_router(compute.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index() -> str:
    """Signpost. This port serves the API; the app itself runs on the Vite server.

    Without this, hitting the backend root returns a bare {"detail":"Not Found"},
    which reads like a broken server rather than the wrong address.
    """
    return """<!doctype html>
<html><head><meta charset="utf-8"><title>Payroll API</title>
<style>
  body { font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
         max-width: 34rem; margin: 15vh auto; padding: 0 1.5rem; color: #16191d;
         line-height: 1.6; }
  h1 { font-size: 1.25rem; margin: 0 0 .5rem; }
  p { color: #6b7280; margin: 0 0 1.5rem; }
  a { display: block; padding: .75rem 1rem; margin-bottom: .5rem;
      border: 1px solid #e2e5ea; border-radius: 8px; text-decoration: none;
      color: #1f3864; font-weight: 500; }
  a:hover { background: #f6f7f9; }
  small { color: #8b929c; font-weight: 400; }
</style></head>
<body>
  <h1>This is the API, not the app.</h1>
  <p>Port 8000 serves JSON. The interface runs on the Vite dev server.</p>
  <a href="http://localhost:5173">Open the app <small>&mdash; localhost:5173</small></a>
  <a href="/docs">API documentation <small>&mdash; interactive</small></a>
  <a href="/api/health">Health check <small>&mdash; /api/health</small></a>
</body></html>"""
