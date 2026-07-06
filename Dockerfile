FROM python:3.14-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy app code
COPY . .

# Run migrations then start server
CMD set -e && uv run alembic upgrade head && exec uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers