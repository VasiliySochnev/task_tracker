from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from tracker.models import Address
from users.models import Client


class AddressCRUDTest(APITestCase):
    """
    Набор тестов для проверки операций CRUD (создание, чтение, обновление, удаление)
    над моделью Address через API.
    """

    def setUp(self):
        """
        Настройка тестовой среды:
        - Создаёт тестового пользователя
        - Генерирует JWT токен
        - Создаёт тестовый адрес
        - Устанавливает токен в заголовки клиента
        """
        # Создание тестового клиента (пользователя)
        self.client_user = Client.objects.create_user(
            email="testuser@example.com", password="testpassword"
        )

        # Получение токена доступа для аутентификации
        refresh = RefreshToken.for_user(self.client_user)
        self.access_token = str(refresh.access_token)

        # Данные тестового адреса
        self.address_data = {
            "floor": 2,
            "apartment": 15,
            "house": 7,
            "street": "Пушкина",
            "city": "Москва",
            "region": "Московская область",
            "postal_code": 123456,
        }

        # Создание объекта Address в базе данных
        self.address = Address.objects.create(**self.address_data)

        # Установка заголовка авторизации для запросов
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)

    def test_create_address(self):
        """
        Тестирование создания нового адреса через POST-запрос.
        Ожидается статус 201 CREATED.
        """
        response = self.client.post(
            reverse("tracker:addresses-list"), data=self.address_data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_read_address(self):
        """
        Тестирование чтения существующего адреса через GET-запрос.
        Ожидается статус 200 OK и правильное значение поля city.
        """
        response = self.client.get(
            reverse("tracker:addresses-detail", args=[self.address.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["city"], "Москва")

    def test_update_address(self):
        """
        Тестирование обновления адреса через PUT-запрос.
        Изменяется поле city, ожидается статус 200 OK и обновлённое значение.
        """
        updated_data = self.address_data.copy()
        updated_data["city"] = "Санкт-Петербург"
        response = self.client.put(
            reverse("tracker:addresses-detail", args=[self.address.id]),
            data=updated_data,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["city"], "Санкт-Петербург")

    def test_delete_address(self):
        """
        Тестирование удаления адреса через DELETE-запрос.
        Ожидается статус 204 NO CONTENT.
        """
        response = self.client.delete(
            reverse("tracker:addresses-detail", args=[self.address.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
