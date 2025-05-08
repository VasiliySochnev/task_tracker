from django.core.management import BaseCommand

from users.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        user = User.objects.create(email="admin@mail.ru")
        user.set_password("admin")
        user.is_staff = True
        user.is_superuser = True
        user.save()
