#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python manage.py migrate

python manage.py shell <<EOF
from django.contrib.auth import get_user_model

User = get_user_model()

email = "quangvoka732004@gmail.com"
password = "teaberry2026"

if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        username="admin",
        email=email,
        password=password,
    )
    print("Superuser created.")
else:
    print("Superuser already exists.")
EOF

python manage.py collectstatic --noinput