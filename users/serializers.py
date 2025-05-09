from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from users.models import Client, Department, Employee, User
from users.validators import B2BValidator, DepartmentShippingValidator


class UserSerializer(ModelSerializer):
    """Сериализатор для модели пользователя."""

    class Meta:
        model = User
        fields = "__all__"

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data["password"])  # Хешируем пароль
        user.save()
        return user


class DepartmentSerializer(ModelSerializer):
    """Сериализатор для модели отдела."""

    class Meta:
        model = Department
        fields = "__all__"


class EmployeeSerializer(ModelSerializer):
    """Сериализатор для модели сотрудника."""

    class Meta:
        model = Employee
        fields = "__all__"
        validators = DepartmentShippingValidator(
            department_field="department",
            shipping_zone_field="shipping_zone"
        )

    def create(self, validated_data):
        user = Employee(**validated_data)
        user.set_password(validated_data["password"])  # Хешируем пароль
        user.save()
        return user


class BusyEmployeeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения сотрудников, которые выполняют задачи."""

    active_tasks_count = serializers.IntegerField()
    active_task_names = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ["id", "position", "active_tasks_count", "active_task_names"]

    def get_active_task_names(self, obj):

        return list(obj.tasks.filter(is_active=True).values_list("status", flat=True))


class ClientSerializer(ModelSerializer):
    """Сериализатор для модели клиента."""

    class Meta:
        model = Client
        fields = "__all__"
        validators = B2BValidator(client_type_field="client_type",
                                  organization_name_field="organization_name",
                                  o_g_r_n_field="o_g_r_n",
                                  i_n_n_field="i_n_n",
                                  bank_account_field="bank_account"
                                  )

    def create(self, validated_data):
        user = Client(**validated_data)
        user.set_password(validated_data["password"])  # Хешируем пароль
        user.save()
        return user
