from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from tracker.models import Address
from users.models import Client


class AddressCRUDTest(APITestCase):
    def setUp(self):
        # Создайте клиента для тестов
        self.client_user = Client.objects.create_user(
            email="testuser@example.com", password="testpassword"
        )

        # Получаем токен для пользователя
        refresh = RefreshToken.for_user(self.client_user)
        self.access_token = str(refresh.access_token)

        self.address_data = {
            "floor": 2,
            "apartment": 15,
            "house": 7,
            "street": "Пушкина",
            "city": "Москва",
            "region": "Московская область",
            "postal_code": 123456,
        }
        self.address = Address.objects.create(**self.address_data)

        # Аутентификация клиента с помощью JWT
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)

    def test_create_address(self):
        response = self.client.post(
            reverse("tracker:addresses-list"), data=self.address_data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_read_address(self):
        response = self.client.get(
            reverse("tracker:addresses-detail", args=[self.address.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["city"], "Москва")

    def test_update_address(self):
        updated_data = self.address_data.copy()
        updated_data["city"] = "Санкт-Петербург"
        response = self.client.put(
            reverse("tracker:addresses-detail", args=[self.address.id]),
            data=updated_data,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["city"], "Санкт-Петербург")

    def test_delete_address(self):
        response = self.client.delete(
            reverse("tracker:addresses-detail", args=[self.address.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
