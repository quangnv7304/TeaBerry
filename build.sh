#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python manage.py migrate

python manage.py shell <<'EOF'
import os
from django.contrib.auth import get_user_model

User = get_user_model()

email = os.environ["DJANGO_SUPERUSER_EMAIL"].strip().lower()
password = os.environ["DJANGO_SUPERUSER_PASSWORD"]

user = User.objects.filter(email__iexact=email).first()

if user:
    user.email = email
    user.is_active = True
    user.is_staff = True
    user.is_superuser = True
    user.role = "ADMIN"
    user.set_password(password)
    user.save(
        update_fields=[
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "role",
            "password",
        ]
    )
    print("SUPERUSER_UPDATED_SUCCESSFULLY")
else:
    User.objects.create_superuser(
        email=email,
        password=password,
    )
    print("SUPERUSER_CREATED_SUCCESSFULLY")
EOF

python manage.py collectstatic --noinput