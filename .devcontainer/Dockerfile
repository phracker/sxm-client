FROM python:3.9.6-slim-buster

RUN apt-get update \
    && apt-get install -y git ffmpeg \
    # cleaning up unused files
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/pyproject.toml
RUN pip install "/app/[dev,test,doc]"
