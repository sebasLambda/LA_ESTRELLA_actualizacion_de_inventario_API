FROM python:3.12.5-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

ENV TZ=America/Bogota


WORKDIR /app

COPY . /app/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Configurar crontab
COPY mycron /etc/cron.d/mycron
RUN chmod 0644 /etc/cron.d/mycron && \
    crontab /etc/cron.d/mycron && \
    touch /var/log/cron.log

RUN chmod +x /app/entrypoint.sh

EXPOSE 9001

ENTRYPOINT ["./app/entrypoint.sh"]
