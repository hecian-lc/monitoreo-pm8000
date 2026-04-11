FROM python:3.11-slim

WORKDIR /app

# System deps for WeasyPrint/matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
    libffi-dev shared-mime-info fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

RUN mkdir -p /app/data /app/reports-output

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
