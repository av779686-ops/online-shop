FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requierements.txt ./requierements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requierements.txt

COPY . .

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 3000 5432

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
