# from django.test import TestCase
# from rest_framework.test import APIClient
# from rest_framework import status
# from django.urls import reverse
#
# from users.models import User, Employee, Client, Department
#
#
# class BaseTestCase(TestCase):
#     """
#     Базовый тестовый класс для инициализации клиентов и пользователей.
#     """
#     def setUp(self):
#         self.client = APIClient()
#
#         # Сотрудник отдела кадров (имеет права HR)
#         self.hr_employee = Employee.objects.create_user(
#             email="hr@example.com", password="test123",
#             position="сотрудник отдела кадров", is_staff=True
#         )
#
#         # Менеджер по продажам
#         self.sales_employee = Employee.objects.create_user(
#             email="sales@example.com", password="test123",
#             position="менеджер по продажам"
#         )
#
#         # Обычный пользователь без специальных прав
#         self.regular_user = User.objects.create_user(
#             email="user@example.com", password="test123"
#         )
#
#
# class UserViewSetTest(BaseTestCase):
#     """
#     Тесты для CRUD-операций над базовым пользователем.
#     """
#
#     def test_user_create(self):
#         """
#         Проверка успешного создания пользователя.
#         """
#         url = reverse("user:user-list")
#         response = self.client.post(url, {
#             "email": "new@example.com",
#             "password": "testpass123"
#         })
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertTrue(User.objects.filter(email="new@example.com").exists())
#
#     def test_user_list(self):
#         """
#         Проверка получения списка пользователей.
#         """
#         response = self.client.get(reverse("user:user-list"))
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#
# class EmployeeViewSetTest(BaseTestCase):
#
#     def test_employee_create_by_non_hr(self):
#         """
#         Проверка, что не-HR пользователь не может создать сотрудника.
#         """
#         self.client.force_authenticate(user=self.sales_employee)
#
#         response = self.client.post(reverse("user:employee-list"), {
#             "email": "employee2@example.com",
#             "password": "test123",
#             "position": "логист"
#         }, format="json")
#
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
#
#
# class ClientViewSetTest(BaseTestCase):
#
#     def test_client_create_by_non_sales(self):
#         """
#         Проверка, что не менеджер по продажам, не может создать клиента.
#         """
#         self.client.force_authenticate(user=self.hr_employee)
#         response = self.client.post(reverse("user:client-list"), {
#             "email": "client2@example.com",
#             "password": "test123",
#             "client_type": "B2B",
#             "organization_name": "OOO Example",
#             "o_g_r_n": "1234567890123",
#             "i_n_n": "123456789012",
#             "bank_account": "12345678901234567890"
#         }, format="json")
#
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
