#!/usr/bin/env bash
# build.sh — Script de construcción para Render.com
set -o errexit  # Detiene el script si algún comando falla

# 1. Instalar dependencias de Python
pip install -r requirements.txt

# 2. Recopilar todos los archivos estáticos en STATIC_ROOT (staticfiles/)
python manage.py collectstatic --no-input

# 3. Aplicar migraciones pendientes
python manage.py migrate
