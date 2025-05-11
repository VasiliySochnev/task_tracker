from django.test import TestCase
from rest_framework.serializers import ValidationError

from users.validators import B2BValidator, DepartmentShippingValidator


class DepartmentShippingValidatorTest(TestCase):
    """
    Тесты для валидатора DepartmentShippingValidator.
    """

    def setUp(self):
        self.validator = DepartmentShippingValidator(
            department_field="department",
            shipping_zone_field="shipping_zone",
            position_field="position",
        )

    def test_valid_with_department(self):
        """
        Должно пройти: указана только department для грузчика.
        """
        data = {
            "position": "грузчик",
            "department": 1,
            "shipping_zone": None,
        }
        self.validator(data)  # Ожидаем отсутствие исключений

    def test_invalid_both_filled(self):
        """
        Ошибка: одновременно указаны department и shipping_zone.
        """
        data = {
            "position": "грузчик",
            "department": 1,
            "shipping_zone": 2,
        }
        with self.assertRaises(ValidationError):
            self.validator(data)

    def test_valid_exempt_position(self):
        """
        Должно пройти: должность, не требующая department/shipping_zone.
        """
        data = {
            "position": "менеджер по продажам",
            "department": None,
            "shipping_zone": None,
        }
        self.validator(data)


class B2BValidatorTest(TestCase):
    """
    Тесты для валидатора B2BValidator.
    """

    def setUp(self):
        self.validator = B2BValidator(
            client_type_field="client_type",
            organization_name_field="organization_name",
            o_g_r_n_field="o_g_r_n",
            i_n_n_field="i_n_n",
            bank_account_field="bank_account",
        )

    def test_valid_b2b_full(self):
        """
        Должно пройти: все поля для B2B клиента заполнены.
        """
        self.validator(
            {
                "client_type": "B2B",
                "organization_name": "ООО Тест",
                "o_g_r_n": "1234567890123",
                "i_n_n": "123456789012",
                "bank_account": "12345678901234567890",
            }
        )

    def test_invalid_b2b_missing_fields(self):
        """
        Ошибка: у B2B клиента отсутствуют обязательные поля.
        """
        with self.assertRaises(ValidationError):
            self.validator(
                {
                    "client_type": "B2B",
                    "organization_name": None,
                    "o_g_r_n": None,
                    "i_n_n": None,
                    "bank_account": None,
                }
            )

    def test_invalid_b2c_has_b2b_fields(self):
        """
        Ошибка: B2C клиент не должен иметь поля B2B.
        """
        with self.assertRaises(ValidationError):
            self.validator(
                {
                    "client_type": "B2C",
                    "organization_name": "ООО",
                    "o_g_r_n": "123",
                    "i_n_n": "123",
                    "bank_account": "456",
                }
            )
