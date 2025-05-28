from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import Employee, User


class BaseTestCase(TestCase):
    """
    Базовый тестовый класс для инициализации клиентов и тестовых пользователей с разными ролями.
    """

    def setUp(self):
        """
        Создаёт:
        - HR-сотрудника (имеет право создавать других сотрудников)
        - Менеджера по продажам (может создавать клиентов)
        - Обычного пользователя без спец. прав
        """
        self.client = APIClient()

        self.hr_employee = Employee.objects.create_user(
            email="hr@example.com",
            password="test123",
            position="сотрудник отдела кадров",
            is_staff=True,  # HR-сотрудник, потенциально с правами администратора
        )

        self.sales_employee = Employee.objects.create_user(
            email="sales@example.com",
            password="test123",
            position="менеджер по продажам",
        )

        self.regular_user = User.objects.create_user(
            email="user@example.com", password="test123"
        )


class UserViewSetTest(BaseTestCase):
    """
    Тесты CRUD-операций над объектами базовой модели User.
    """

    def test_user_create(self):
        """
        Проверка успешного создания нового пользователя через POST-запрос.
        Ожидается: статус 201 CREATED.
        """
        url = reverse("user:user-list")
        response = self.client.post(
            url, {"email": "new@example.com", "password": "testpass123"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

    def test_user_list(self):
        """
        Проверка получения списка всех пользователей.
        Ожидается: статус 200 OK.
        """
        response = self.client.get(reverse("user:user-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class EmployeeViewSetTest(BaseTestCase):
    """
    Тесты на создание сотрудников через эндпоинт EmployeeViewSet.
    """

    def test_employee_create_by_non_hr(self):
        """
        Проверка, что пользователь без HR-прав (менеджер по продажам)
        не может создать нового сотрудника.
        Ожидается: статус 403 FORBIDDEN.
        """
        self.client.force_authenticate(user=self.sales_employee)

        response = self.client.post(
            reverse("user:employee-list"),
            {
                "email": "employee2@example.com",
                "password": "test123",
                "position": "логист",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ClientViewSetTest(BaseTestCase):
    """
    Тесты на создание клиентов через эндпоинт ClientViewSet.
    """

    def test_client_create_by_non_sales(self):
        """
        Проверка, что сотрудник без роли 'менеджер по продажам' (в данном случае — HR)
        не может создать нового клиента.
        Ожидается: статус 403 FORBIDDEN.
        """
        self.client.force_authenticate(user=self.hr_employee)

        response = self.client.post(
            reverse("user:client-list"),
            {
                "email": "client2@example.com",
                "password": "test123",
                "client_type": "B2B",
                "organization_name": "OOO Example",
                "o_g_r_n": "1234567890123",
                "i_n_n": "123456789012",
                "bank_account": "12345678901234567890",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
