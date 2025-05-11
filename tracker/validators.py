from rest_framework import serializers


class ProductСlientValidator:
    """Валидация от отсутствия товара в заказе."""

    def __init__(self, products_field, client_field):
        self.products_field = products_field
        self.client_field = client_field

    def __call__(self, value):
        products = value.get(self.products_field)
        client = value.get(self.client_field)

        if (
            (products and not client)
            or (client and not products)
            or (not products and not client)
        ):
            raise serializers.ValidationError(
                "Заказ не может быть без товара и клиента."
            )


class DepartmentProductValidator:
    """Валидация от отсутствия отдела для товара."""

    def __init__(self, department_field):
        self.department_field = department_field

    def __call__(self, value):
        department = value.get(self.department_field)

        if not department:
            raise serializers.ValidationError("Товар не может хранится без отдела.")
