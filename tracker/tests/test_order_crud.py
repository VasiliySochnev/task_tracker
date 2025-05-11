from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tracker.models import Address, Order, OrderProduct, Product, ShippingZone
from users.models import Client, Department, User


class OrderCRUDTest(APITestCase):
    def setUp(self):
        # Создаем пользователя-клиента
        self.client_user = Client.objects.create_user(
            email="client@example.com", password="pass123"
        )

        # Создаем адрес
        self.address = Address.objects.create(
            floor=3,
            apartment=45,
            house=12,
            street="Ленина",
            city="Москва",
            region="Московская область",
            postal_code=101000,
        )

        # Создаем зону доставки
        self.shipping_zone = ShippingZone.objects.create(
            name="city", description="Доставка по городу"
        )

        # Создаем департамент и поставщика
        self.department = Department.objects.create(title="Электроника")
        self.supplier = User.objects.create_user(
            email="supplier@example.com", password="sup123"
        )

        # Создаем продукт
        self.product = Product.objects.create(
            title="Кабель HDMI",
            price="499.99",
            description="1.5 метра",
            department=self.department,
            amount_remains=30,
            amount_supplier=100,
            supplier=self.supplier,
        )

        # Данные для теста заказа
        self.order_data = {
            "client": self.client_user.id,
            "address": self.address.id,
            "total_amount": str(
                self.product.price
            ),  # Цена в строковом формате для JSON
            "status": "processing",
            "shipping_zone": self.shipping_zone.id,
            "products": [
                {
                    "product": self.product.pk,
                    "quantity": 1,  # Количество товара в заказе
                }
            ],
        }

        # Создаем заказ напрямую через модель (используем реальные объекты)
        self.order = Order.objects.create(
            client=self.client_user,
            address=self.address,
            shipping_zone=self.shipping_zone,
            total_amount=self.product.price,
        )
        OrderProduct.objects.create(order=self.order, product=self.product, quantity=1)

    def test_create_order(self):
        orders_before = Order.objects.count()
        response = self.client.post(
            reverse("tracker:orders-list"), data=self.order_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Order.objects.count(), orders_before + 1)

        new_order = Order.objects.latest("order_id")
        self.assertEqual(OrderProduct.objects.filter(order=new_order).count(), 1)

    def test_read_order(self):
        response = self.client.get(
            reverse("tracker:orders-detail", args=[self.order.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("RESPONSE:", response.data)

        self.assertEqual(response.data["client"], self.client_user.pk)

    # def test_update_order(self):
    #     # Изменим адрес
    #     new_address = Address.objects.create(
    #         floor=2,
    #         apartment=10,
    #         house=8,
    #         street="Советская",
    #         city="СПБ",
    #         region="ЛО",
    #         postal_code=190000
    #     )
    #
    #     updated_data = {
    #         "client": self.client_user.pk,
    #         "address": new_address.id,
    #         "shipping_zone": self.shipping_zone.id,
    #         "status": "processing",
    #         "total_amount": str(self.product.price),  # Цена в строковом формате для JSON
    #         "products": [
    #             {
    #                 "product": self.product.pk,
    #                 "quantity": 1  # Количество товара в заказе
    #             }
    #         ]
    #     }
    #
    #     related_order_products = OrderProduct.objects.filter(product_id=4)
    #     related_order_products.update(product=self.product.pk)  # Обновляем продукт в связанных записях
    #
    #     response = self.client.put(reverse("tracker:orders-detail", args=[self.order.pk]), data=updated_data, format="json")
    #     print("RESPONSE:", response.data)
    #
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(response.data["address"], new_address.id)

    def test_delete_order(self):
        response = self.client.delete(
            reverse("tracker:orders-detail", args=[self.order.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.filter(pk=self.order.pk).exists())
