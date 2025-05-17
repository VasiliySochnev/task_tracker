from rest_framework import serializers

from .models import (
    Address, Order, OrderEmployeeHistory, OrderProduct,
    OrderStatusHistory, Product, ShippingZone, Task
)
from .validators import DepartmentProductValidator, ProductСlientValidator


class ShippingZoneSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели ShippingZone (зона отгрузки).
    Используется для преобразования данных зоны отгрузки в JSON и обратно.
    """

    class Meta:
        model = ShippingZone
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Product (товар).
    Валидирует соответствие товара отделу через кастомный валидатор.
    """

    class Meta:
        model = Product
        fields = "__all__"
        validators = [DepartmentProductValidator(department_field="department")]


class TaskSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Task (задача).
    Используется для сериализации всех полей задачи.
    """

    class Meta:
        model = Task
        fields = "__all__"


class TaskSummarySerializer(serializers.ModelSerializer):
    """
    Сериализатор для краткого отображения активных задач по заказу.
    Позволяет получить расширенную информацию о задаче,
    включая имя сотрудника, отдел, должность и зону отгрузки.
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
        """
        Возвращает полное имя сотрудника.
        """
        return f"{obj.employee.first_name} {obj.employee.last_name}"

    def get_department(self, obj):
        """
        Возвращает название отдела сотрудника, если есть.
        """
        return getattr(obj.employee.department, "title", None)

    def get_shipping_zone(self, obj):
        """
        Возвращает название зоны отгрузки сотрудника, если есть.
        """
        return getattr(obj.employee.shipping_zone, "name", None)


class AddressSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Address (адрес).
    """

    class Meta:
        model = Address
        fields = "__all__"


class OrderProductSerializer(serializers.ModelSerializer):
    """
    Сериализатор для промежуточной модели OrderProduct (товар в заказе).
    Используется для отображения и обработки количества и товара.
    """

    class Meta:
        model = OrderProduct
        fields = ("product", "quantity")


class OrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Order (заказ).
    Обрабатывает вложенные продукты и включает дополнительное поле products_read
    для отображения продуктов в заказе (read-only).
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
        """
        Возвращает сериализованные данные о продуктах в заказе.
        """
        return OrderProductSerializer(obj.order_products.all(), many=True).data

    def create(self, validated_data):
        """
        Переопределяет метод создания заказа с вложенными товарами.
        """
        products_data = validated_data.pop("products")
        order = Order.objects.create(**validated_data)
        for item in products_data:
            OrderProduct.objects.create(order=order, **item)
        return order

    def update(self, instance, validated_data):
        """
        Переопределяет метод обновления заказа и связанных товаров.
        """
        products_data = validated_data.pop("products", None)

        # Обновляем основные поля заказа
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновляем товары, если они переданы
        if products_data:
            instance.products.all().delete()
            for item in products_data:
                OrderProduct.objects.create(order=instance, **item)

        return instance


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели OrderStatusHistory (история смены статуса заказа).
    """

    class Meta:
        model = OrderStatusHistory
        fields = "__all__"


class OrderEmployeeHistorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели OrderEmployeeHistory (история участия сотрудника в заказе).
    Добавляет поле task_status, возвращающее статус связанной задачи.
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
        """
        Получает статус задачи, связанной с историей.
        """
        return obj.task_status
