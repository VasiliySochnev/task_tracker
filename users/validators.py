from rest_framework import serializers


class DepartmentShippingValidator:
    """Валидация для отделов и зон отгрузки."""
    def __init__(self, department_field, shipping_zone_field):
        self.department_field = department_field
        self.shipping_zone_field = shipping_zone_field

    def __call__(self, value):
        department_field = value.get(self.department_field)
        shipping_zone_field = value.get(self.shipping_zone_field)
        if (department_field is not None and shipping_zone_field) or (shipping_zone_field is None and department_field):
            raise serializers.ValidationError(
                'Если сотрудник не менеджер по продажам и не складской менеджер, то он может работать либо в отделе либо в зоне отгрузки'
            )


class B2BValidator:
    """Валидация для проверки, что поля B2B заполнены только для B2B клиентов."""
    def __init__(self, client_type_field, organization_name_field, o_g_r_n_field, i_n_n_field, bank_account_field):
        self.client_type_field = client_type_field
        self.organization_name_field = organization_name_field
        self.o_g_r_n_filed = o_g_r_n_field
        self.i_n_n_field = i_n_n_field
        self.bank_account_field = bank_account_field

    def __call__(self, value):
        client_type = value.get(self.client_type_field)
        organization_name = value.get(self.organization_name_field)
        o_g_r_n = value.get(self.o_g_r_n_filed)
        i_n_n = value.get(self.i_n_n_field)
        bank_account = value.get(self.bank_account_field)

        if client_type == "B2B":
            if not all(
                [organization_name, o_g_r_n, i_n_n, bank_account]
            ):
                raise serializers.ValidationError(
                    "Все поля для B2B клиентов должны быть заполнены."
                )
        else:
            if (
                organization_name
                or o_g_r_n
                or i_n_n
                or bank_account
            ):
                raise serializers.ValidationError(
                    "Поля организации не должны быть заполнены для B2C клиентов."
                )
