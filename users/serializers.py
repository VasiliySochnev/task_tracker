from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from django.contrib.auth.models import Group
from users.models import Client, Department, Employee, User
from users.validators import B2BValidator, DepartmentShippingValidator

class UserSerializer(ModelSerializer):
    """Сериализатор для модели пользователя."""
    groups = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all(),
        required=False
    )

    class Meta:
        model = User
        fields = "__all__"

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        groups = validated_data.pop("groups", [])
        permissions = validated_data.pop("user_permissions", [])

        instance = self.Meta.model(**validated_data)

        if password:
            instance.set_password(password)

        instance.save()

        if permissions:
            instance.user_permissions.set(permissions)

        if groups:
            instance.groups.set(groups)

        return instance

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        groups = validated_data.pop("groups", None)
        permissions = validated_data.pop("user_permissions", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if permissions is not None:
            instance.user_permissions.set(permissions)
        if groups is not None:
            instance.groups.set(groups)
        return instance


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

    def validate(self, attrs):
        position = attrs.get("position")
        department = attrs.get("department")
        shipping_zone = attrs.get("shipping_zone")

        exempt_positions = [
            "менеджер по продажам",
            "складской менеджер",
            "сотрудник отдела кадров",
        ]

        if position not in exempt_positions:
            if bool(department) == bool(shipping_zone):
                raise serializers.ValidationError(
                    "Если сотрудник не менеджер по продажам, не складской менеджер и не из отдела кадров, "
                    "то он может работать либо в отделе, либо в зоне отгрузки (но не в обоих и не без них одновременно)."
                )

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = Employee(**validated_data)
        if password:
            user.set_password(password)
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
        validators = [B2BValidator(client_type_field="client_type",
                                  organization_name_field="organization_name",
                                  o_g_r_n_field="o_g_r_n",
                                  i_n_n_field="i_n_n",
                                  bank_account_field="bank_account"
                                  )]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = Client(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user
