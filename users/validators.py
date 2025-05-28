from rest_framework import serializers


class DepartmentShippingValidator:
    """Валидация для отделов и зон отгрузки."""

    def __init__(
        self, department_field, shipping_zone_field, position_field="position"
    ):
        self.department_field = department_field
        self.shipping_zone_field = shipping_zone_field
        self.position_field = position_field

        self.positions_without_department_or_zone = [
            "менеджер по продажам",
            "складской менеджер",
            "сотрудник отдела кадров",
        ]

    def __call__(self, value):
        position = value.get(self.position_field)
        department = value.get(self.department_field)
        shipping_zone = value.get(self.shipping_zone_field)

        if position in self.positions_without_department_or_zone:
            return

        if bool(department) == bool(shipping_zone):
            raise serializers.ValidationError(
                "Если сотрудник не менеджер по продажам, не складской менеджер и не из отдела кадров "
                "то он может работать либо в отделе либо в зоне отгрузки"
            )


class B2BValidator:
    """Валидация для проверки, что поля B2B заполнены только для B2B клиентов."""

    def __init__(
        self,
        client_type_field,
        organization_name_field,
        o_g_r_n_field,
        i_n_n_field,
        bank_account_field,
    ):
        self.client_type_field = client_type_field
        self.organization_name_field = organization_name_field
        self.o_g_r_n_field = o_g_r_n_field
        self.i_n_n_field = i_n_n_field
        self.bank_account_field = bank_account_field

    def __call__(self, value):
        client_type = value.get(self.client_type_field)
        organization_name = value.get(self.organization_name_field)
        o_g_r_n = value.get(self.o_g_r_n_field)
        i_n_n = value.get(self.i_n_n_field)
        bank_account = value.get(self.bank_account_field)

        def is_filled(val):
            return val not in [None, ""]

        fields_filled = all(
            map(is_filled, [organization_name, o_g_r_n, i_n_n, bank_account])
        )
        fields_empty = all(
            not is_filled(f) for f in [organization_name, o_g_r_n, i_n_n, bank_account]
        )

        if client_type == "B2B" and not fields_filled:
            raise serializers.ValidationError(
                "Все поля для B2B клиентов должны быть заполнены."
            )
        elif client_type == "B2C" and not fields_empty:
            raise serializers.ValidationError(
                "Поля организации не должны быть заполнены для B2C клиентов."
            )
