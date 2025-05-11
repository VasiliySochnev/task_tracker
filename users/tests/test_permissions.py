# from django.test import TestCase
# from rest_framework.test import APIRequestFactory
#
# from users.models import Employee, Client
# from users.permissions import (
#     IsCladdingQuality, IsSalesManager, IsDepartmentOfPersonnel,
#     IsClient
# )
#
#
# class PermissionTestCase(TestCase):
#     """
#     Тесты для кастомных классов прав доступа.
#     """
#
#     def setUp(self):
#         self.factory = APIRequestFactory()
#
#         # Пользователи с различными ролями
#         self.quality = Employee.objects.create_user(
#             email="q@example.com", password="pass", position="инспектор по качеству"
#         )
#         self.clerk = Employee.objects.create_user(
#             email="w@example.com", password="pass", position="кладовщик"
#         )
#         self.sales = Employee.objects.create_user(
#             email="s@example.com", password="pass", position="менеджер по продажам"
#         )
#         self.hr = Employee.objects.create_user(
#             email="hr@example.com", password="pass", position="сотрудник отдела кадров"
#         )
#         self.client_user = Client.objects.create_user(
#             email="client@example.com", password="pass", client_type="B2C"
#         )
#
#     def test_is_cladding_quality(self):
#         """Права доступа для 'инспектор по качеству'."""
#         request = self.factory.get("/")
#         request.user = self.quality
#         self.assertTrue(IsCladdingQuality().has_permission(request, None))
#
#     def test_is_sales_manager(self):
#         """Права доступа для 'менеджер по продажам'."""
#         request = self.factory.get("/")
#         request.user = self.sales
#         self.assertTrue(IsSalesManager().has_permission(request, None))
#
#     def test_is_hr(self):
#         """Права доступа для 'сотрудник отдела кадров'."""
#         request = self.factory.get("/")
#         request.user = self.hr
#         self.assertTrue(IsDepartmentOfPersonnel().has_permission(request, None))
#
#     def test_is_client(self):
#         """Права доступа для клиента."""
#         request = self.factory.get("/")
#         request.user = self.client_user
#         self.assertTrue(IsClient().has_permission(request, None))
