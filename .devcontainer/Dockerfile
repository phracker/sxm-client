FROM python:3.9.6-slim-buster

RUN apt-get update \
    && apt-get install -y git ffmpeg build-essential \
    # cleaning up unused files
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

COPY dev-requirements.txt /dev-requirements.txt
RUN pip install --no-cache-dir -r /dev-requirements.txt && rm /dev-requirements.txt

ENV PATH /workspaces/sxm-client/.bin:$PATH
