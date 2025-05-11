from rest_framework import serializers

from .models import (Address, Order, OrderEmployeeHistory, OrderProduct,
                     OrderStatusHistory, Product, Task)
from .validators import DepartmentProductValidator, ProductСlientValidator


class ProductSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели товара.
    """

    class Meta:
        model = Product
        fields = "__all__"
        validators = [DepartmentProductValidator(department_field="department")]


class TaskSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели задача.
    """

    class Meta:
        model = Task
        fields = "__all__"


class TaskSummarySerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения активных задач по конкретному заказу.
    """

    order = serializers.StringRelatedField()
    task_status = serializers.CharField(source="status")
    task_created_at = serializers.DateTimeField(source="created_at")
    employee_full_name = serializers.SerializerMethodField()
    position = serializers.CharField(source="employee.position", default=None)
    department = serializers.SerializerMethodField()
    shipping_zone = serializers.SerializerMethodField()
    task_is_active = serializers.BooleanField(source="is_active")

    class Meta:
        model = Task
        fields = [
            "order",
            "task_status",
            "task_created_at",
            "employee_full_name",
            "position",
            "department",
            "shipping_zone",
            "task_is_active",
        ]

    def get_employee_full_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"

    def get_department(self, obj):
        return getattr(obj.employee.department, "title", None)

    def get_shipping_zone(self, obj):
        return getattr(obj.employee.shipping_zone, "name", None)


class AddressSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели адреса.
    """

    class Meta:
        model = Address
        fields = "__all__"


class OrderProductSerializer(serializers.ModelSerializer):
    """
    Сериализатор для промежуточной модели
    товара и заказа.
    """

    class Meta:
        model = OrderProduct
        fields = ("product", "quantity")


class OrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели заказа.
    """

    products = OrderProductSerializer(many=True, write_only=True)
    products_read = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = "__all__"
        extra_fields = ["products_read"]
        validators = [
            ProductСlientValidator(products_field="products", client_field="client")
        ]

    def get_products_read(self, obj):
        return OrderProductSerializer(obj.order_products.all(), many=True).data

    def create(self, validated_data):
        products_data = validated_data.pop("products")
        order = Order.objects.create(**validated_data)
        for item in products_data:
            OrderProduct.objects.create(order=order, **item)
        return order

    def update(self, instance, validated_data):
        products_data = validated_data.pop("products", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if products_data:
            instance.products.all().delete()
            for item in products_data:
                OrderProduct.objects.create(order=instance, **item)

        return instance


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели история для
    статуса заказа.
    """

    class Meta:
        model = OrderStatusHistory
        fields = "__all__"


class OrderEmployeeHistorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели история для сотрудников,
    которые работали с заказом.
    """

    task_status = serializers.SerializerMethodField()

    class Meta:
        model = OrderEmployeeHistory
        fields = [
            "order",
            "employee",
            "assigned_at",
            "completed_at",
            "task",
            "task_status",
        ]
        read_only_fields = ["task_status"]

    def get_task_status(self, obj):
        return obj.task_status
