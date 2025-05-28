from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tracker.models import Product
from users.models import Department, User


class ProductCRUDTest(APITestCase):
    """
    Набор тестов для проверки операций CRUD над продуктами (Product) через API.
    """

    def setUp(self):
        """
        Подготовка тестовых данных:
        - Создаёт департамент и пользователя-поставщика
        - Создаёт тестовый продукт
        """
        # Создание тестового департамента
        self.department = Department.objects.create(title="Инструменты")

        # Создание поставщика
        self.supplier = User.objects.create_user(
            email="supplier@test.com", password="test123"
        )

        # Данные продукта для тестирования
        self.product_data = {
            "title": "Отвертка",
            "price": "199.99",
            "description": "Крестовая отвертка",
            "department": self.department.id,
            "amount_remains": 20,
            "amount_supplier": 50,
            "supplier": self.supplier.id,
        }

        # Создание продукта напрямую через ORM
        self.product = Product.objects.create(
            title="Отвертка",
            price="199.99",
            description="Крестовая отвертка",
            department=self.department,
            amount_remains=20,
            amount_supplier=50,
            supplier=self.supplier,
        )

    def test_create_product(self):
        """
        Тестирование создания нового продукта через POST-запрос.
        Ожидается статус 201 CREATED.
        """
        response = self.client.post(
            reverse("tracker:products-list"), data=self.product_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_read_product(self):
        """
        Тестирование получения информации о продукте через GET-запрос.
        Проверяется корректность возвращаемого заголовка (title).
        """
        response = self.client.get(
            reverse("tracker:products-detail", args=[self.product.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.product.title)

    def test_update_product(self):
        """
        Тестирование обновления информации о продукте через PUT-запрос.
        Меняется поле title. Ожидается статус 200 OK и новое значение.
        """
        updated_data = self.product_data.copy()
        updated_data["title"] = "Отвертка мини"
        response = self.client.put(
            reverse("tracker:products-detail", args=[self.product.pk]),
            data=updated_data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Отвертка мини")

    def test_delete_product(self):
        """
        Тестирование удаления продукта через DELETE-запрос.
        Ожидается статус 204 NO CONTENT.
        """
        response = self.client.delete(
            reverse("tracker:products-detail", args=[self.product.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
