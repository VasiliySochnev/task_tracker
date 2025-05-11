from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tracker.models import Product
from users.models import Department, User


class ProductCRUDTest(APITestCase):
    def setUp(self):
        self.department = Department.objects.create(title="Инструменты")
        self.supplier = User.objects.create_user(
            email="supplier@test.com", password="test123"
        )

        self.product_data = {
            "title": "Отвертка",
            "price": "199.99",
            "description": "Крестовая отвертка",
            "department": self.department.id,
            "amount_remains": 20,
            "amount_supplier": 50,
            "supplier": self.supplier.id,
        }

        # Создаем продукт вручную
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
        response = self.client.post(
            reverse("tracker:products-list"), data=self.product_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_read_product(self):
        response = self.client.get(
            reverse("tracker:products-detail", args=[self.product.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.product.title)

    def test_update_product(self):
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
        response = self.client.delete(
            reverse("tracker:products-detail", args=[self.product.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
