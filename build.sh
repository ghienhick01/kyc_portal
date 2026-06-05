#!/usr/bin/env bash
# build.sh — Used by Render/Railway for deployment

set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
