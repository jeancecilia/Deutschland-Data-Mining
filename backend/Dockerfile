FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

COPY . /app
RUN pip install --no-cache-dir -e . \
    && python -m playwright install --with-deps chromium

EXPOSE 8000
