from rest_framework import serializers

from .models import (
    Address,
    Order,
    OrderEmployeeHistory,
    OrderProduct,
    OrderStatusHistory,
    Product,Task
)

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"


class TaskSummarySerializer(serializers.ModelSerializer):
    order = serializers.StringRelatedField()
    task_status = serializers.CharField(source='status')
    task_created_at = serializers.DateTimeField(source='created_at')
    employee_full_name = serializers.SerializerMethodField()
    position = serializers.CharField(source='employee.position', default=None)
    department = serializers.SerializerMethodField()
    shipping_zone = serializers.SerializerMethodField()
    task_is_active = serializers.BooleanField(source='is_active')

    class Meta:
        model = Task
        fields = [
            'order',
            'task_status',
            'task_created_at',
            'employee_full_name',
            'position',
            'department',
            'shipping_zone',
            'task_is_active',
        ]

    def get_employee_full_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"

    def get_department(self, obj):
        return getattr(obj.employee.department, 'title', None)

    def get_shipping_zone(self, obj):
        return getattr(obj.employee.shipping_zone, 'name', None)



class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"



class OrderProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderProduct
        fields = "__all__"


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = "__all__"


class OrderEmployeeHistorySerializer(serializers.ModelSerializer):
    task_status = serializers.SerializerMethodField()

    class Meta:
        model = OrderEmployeeHistory
        fields = ["order", "employee", "assigned_at", "completed_at", "task", "task_status"]
        read_only_fields = ["task_status"]

    def get_task_status(self, obj):
        return obj.task_status
