FROM python:3.11.7-slim


# Set environment variables.
# 1. Force Python stdout and stderr streams to be unbuffered.
ENV PYTHONUNBUFFERED=1
ENV LANG nb_NO.UTF-8
ENV LANGUAGE nb_NO:en
ENV LC_ALL nb_NO.UTF-8

# Install system packages required by Wagtail and Django.
RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends locales && sed -i '/nb_NO.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /db/sqlite

COPY requirements.txt /
RUN python -m venv /opt/venv && \
    /opt/venv/bin/python -m pip install pip --upgrade && \
    /opt/venv/bin/python -m pip install -r /requirements.txt

COPY . ./app
WORKDIR /app

CMD [ "python", "run.py" ]
