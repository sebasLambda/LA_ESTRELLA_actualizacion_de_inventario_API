#!/bin/bash

echo "⏳ Esperando a PostgreSQL en $DB_HOST:$DB_PORT..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done

echo "✅ Base de datos lista. Ejecutando migraciones..."
python manage.py migrate --noinput

echo "👤 Verificando superusuario..."
python manage.py shell << EOF
import os
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(identification=os.environ.get("SUPERUSER_ID")).exists():
    User.objects.create_superuser(
        identification=os.environ.get("SUPERUSER_ID"),
        full_name=os.environ.get("SUPERUSER_NAME"),
        password=os.environ.get("SUPERUSER_PASSWORD")
    )
EOF



echo "📅 Iniciando cron..."
cron

echo "🚀 Iniciando servidor Django..."
exec "$@"
