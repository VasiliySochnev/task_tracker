from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tracker.models import Address, Order, OrderProduct, Product, ShippingZone
from users.models import Client, Department, User


class OrderCRUDTest(APITestCase):
    """
    Набор тестов для проверки операций CRUD над заказами (Order) через API.
    """

    def setUp(self):
        """
        Подготовка данных для тестов:
        - Создаёт клиента, адрес, зону доставки, департамент, поставщика и продукт.
        - Создаёт заказ напрямую через модель и связывает продукт с заказом.
        """
        # Создание пользователя-клиента
        self.client_user = Client.objects.create_user(
            email="client@example.com", password="pass123"
        )

        # Создание адреса доставки
        self.address = Address.objects.create(
            floor=3,
            apartment=45,
            house=12,
            street="Ленина",
            city="Москва",
            region="Московская область",
            postal_code=101000,
        )

        # Создание зоны доставки
        self.shipping_zone = ShippingZone.objects.create(
            name="city", description="Доставка по городу"
        )

        # Создание департамента и поставщика
        self.department = Department.objects.create(title="Электроника")
        self.supplier = User.objects.create_user(
            email="supplier@example.com", password="sup123"
        )

        # Создание товара
        self.product = Product.objects.create(
            title="Кабель HDMI",
            price="499.99",
            description="1.5 метра",
            department=self.department,
            amount_remains=30,
            amount_supplier=100,
            supplier=self.supplier,
        )

        # Данные для создания заказа через API
        self.order_data = {
            "client": self.client_user.id,
            "address": self.address.id,
            "total_amount": str(self.product.price),  # Цена как строка (для JSON)
            "status": "processing",
            "shipping_zone": self.shipping_zone.id,
            "products": [
                {
                    "product": self.product.pk,
                    "quantity": 1,  # Количество единиц товара в заказе
                }
            ],
        }

        # Создание заказа напрямую через ORM
        self.order = Order.objects.create(
            client=self.client_user,
            address=self.address,
            shipping_zone=self.shipping_zone,
            total_amount=self.product.price,
        )

        # Привязка продукта к заказу
        OrderProduct.objects.create(order=self.order, product=self.product, quantity=1)

    def test_create_order(self):
        """
        Тестирование создания заказа через POST-запрос.
        Проверяется увеличение количества заказов и наличие продукта в заказе.
        """
        orders_before = Order.objects.count()

        response = self.client.post(
            reverse("tracker:orders-list"), data=self.order_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверка, что заказ добавлен
        self.assertEqual(Order.objects.count(), orders_before + 1)

        # Проверка, что продукт прикреплён к заказу
        new_order = Order.objects.latest("order_id")
        self.assertEqual(OrderProduct.objects.filter(order=new_order).count(), 1)

    def test_read_order(self):
        """
        Тестирование получения заказа через GET-запрос.
        Проверяется корректность возвращаемых данных.
        """
        response = self.client.get(
            reverse("tracker:orders-detail", args=[self.order.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверка, что заказ принадлежит нужному клиенту
        self.assertEqual(response.data["client"], self.client_user.pk)

    def test_delete_order(self):
        """
        Тестирование удаления заказа через DELETE-запрос.
        Проверяется, что заказ действительно удалён.
        """
        response = self.client.delete(
            reverse("tracker:orders-detail", args=[self.order.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Убедимся, что заказ удалён из базы
        self.assertFalse(Order.objects.filter(pk=self.order.pk).exists())
