# syntax=docker/dockerfile:1

# One image, one process. The Vite build is baked in beside the API, so uvicorn
# serves both and the frontend's relative /api calls stay same-origin — no nginx,
# no CORS, nothing to keep in sync between two containers.

FROM node:22-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PAYROLL_DATA_DIR=/data \
    FRONTEND_DIST=/app/static

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app/ ./app/
COPY --from=frontend /build/dist/ ./static/

# The scenario file is the only thing written at runtime, and it lives on the
# volume — the image itself stays read-only to the app user.
RUN useradd --create-home --uid 10001 payroll \
 && mkdir -p /data \
 && chown payroll:payroll /data
USER payroll

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health').read()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
