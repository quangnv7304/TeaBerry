python manage.py shell <<'EOF'
import os
from django.contrib.auth import get_user_model

User = get_user_model()

email = os.environ["DJANGO_SUPERUSER_EMAIL"].strip().lower()
password = os.environ["DJANGO_SUPERUSER_PASSWORD"]

user = User.objects.filter(email__iexact=email).first()

if user:
    user.is_active = True
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
    print("Existing account updated to superuser.")
else:
    User.objects.create_superuser(
        email=email,
        password=password,
    )
    print("New superuser created.")
EOF