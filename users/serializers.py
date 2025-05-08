from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from users.models import Client, Department, Employee, User


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data["password"])  # Хешируем пароль
        user.save()
        return user


class DepartmentSerializer(ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"


class EmployeeSerializer(ModelSerializer):
    class Meta:
        model = Employee
        fields = "__all__"

    def create(self, validated_data):
        user = Employee(**validated_data)
        user.set_password(validated_data["password"])  # Хешируем пароль
        user.save()
        return user


class BusyEmployeeSerializer(serializers.ModelSerializer):
    active_tasks_count = serializers.IntegerField()
    active_task_names = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ['id', 'position', 'active_tasks_count', 'active_task_names']

    def get_active_task_names(self, obj):
        # Предполагается, что у Task есть поле employee и название в name
        return list(obj.tasks.filter(is_active=True).values_list('status', flat=True))



class ClientSerializer(ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"

    def create(self, validated_data):
        user = Client(**validated_data)
        user.set_password(validated_data["password"])  # Хешируем пароль
        user.save()
        return user
