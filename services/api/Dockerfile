FROM python:3.13-slim

# Install system C-libraries required for GeoDjango and PostGIS
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    geos-bin \
    libgeos-dev \
    gettext \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy dependency definition files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Copy application source code
COPY . .

# Expose default port
EXPOSE 10000

# Start script: run migrations and launch gunicorn
CMD ["sh", "-c", "uv run python manage.py migrate && uv run gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 2 --threads 4"]
