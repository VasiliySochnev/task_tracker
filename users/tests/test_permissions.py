from django.test import TestCase
from rest_framework.test import APIRequestFactory

from users.models import Client, Employee
from users.permissions import (IsCladdingQuality, IsClient,
                               IsDepartmentOfPersonnel, IsSalesManager)


class PermissionTestCase(TestCase):
    """
    Тесты для проверки работы кастомных классов разрешений (permissions),
    основанных на должности пользователя или его типе.
    """

    def setUp(self):
        """
        Подготовка данных:
        - Создаются пользователи с различными должностями (инспектор, кладовщик, менеджер, HR)
        - Создаётся клиент.
        - Инициализируется фабрика запросов.
        """
        self.factory = APIRequestFactory()

        # Сотрудники с различными должностями
        self.quality = Employee.objects.create_user(
            email="q@example.com", password="pass", position="инспектор по качеству"
        )
        self.clerk = Employee.objects.create_user(
            email="w@example.com", password="pass", position="кладовщик"
        )
        self.sales = Employee.objects.create_user(
            email="s@example.com", password="pass", position="менеджер по продажам"
        )
        self.hr = Employee.objects.create_user(
            email="hr@example.com", password="pass", position="сотрудник отдела кадров"
        )

        # Клиент
        self.client_user = Client.objects.create_user(
            email="client@example.com", password="pass", client_type="B2C"
        )

    def test_is_cladding_quality(self):
        """
        Проверка разрешения IsCladdingQuality для пользователя с должностью 'инспектор по качеству'.
        Ожидается: разрешение предоставлено.
        """
        request = self.factory.get("/")
        request.user = self.quality
        self.assertTrue(IsCladdingQuality().has_permission(request, None))

    def test_is_sales_manager(self):
        """
        Проверка разрешения IsSalesManager для пользователя с должностью 'менеджер по продажам'.
        Ожидается: разрешение предоставлено.
        """
        request = self.factory.get("/")
        request.user = self.sales
        self.assertTrue(IsSalesManager().has_permission(request, None))

    def test_is_hr(self):
        """
        Проверка разрешения IsDepartmentOfPersonnel для пользователя с должностью 'сотрудник отдела кадров'.
        Ожидается: разрешение предоставлено.
        """
        request = self.factory.get("/")
        request.user = self.hr
        self.assertTrue(IsDepartmentOfPersonnel().has_permission(request, None))

    def test_is_client(self):
        """
        Проверка разрешения IsClient для пользователя, зарегистрированного как клиент.
        Ожидается: разрешение предоставлено.
        """
        request = self.factory.get("/")
        request.user = self.client_user
        self.assertTrue(IsClient().has_permission(request, None))
