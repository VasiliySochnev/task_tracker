from django.db import models
from django.utils import timezone


class Address(models.Model):
    """Модель адреса."""

    floor = models.IntegerField(blank=True, null=True, verbose_name="этаж")
    apartment = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="номер квартиры"
    )
    house = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="номер дома"
    )
    street = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="улица"
    )
    city = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="населенный пункт"
    )
    region = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="область"
    )
    postal_code = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="почтовый индекс"
    )

    def __str__(self):
        return f"{self.apartment}, {self.house}, {self.street}, {self.city}, {self.region}, {self.postal_code}"

    class Meta:
        verbose_name = "Адрес"
        verbose_name_plural = "Адреса"
        ordering = ["city"]


class Product(models.Model):
    """Модель товара."""

    product_id = models.AutoField(primary_key=True)
    title = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Название товара"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Цена товара",
    )
    description = models.TextField(
        max_length=300, blank=True, null=True, verbose_name="Описание товара"
    )
    department = models.ForeignKey(
        "users.Department",
        on_delete=models.CASCADE,
        verbose_name="Отдел",
        blank=True,
        null=True,
    )
    amount_remains = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="Количество на складе"
    )
    amount_supplier = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="Количество у поставщика"
    )
    supplier = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, verbose_name="Поставщик"
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["title"]


class OrderStatus(models.TextChoices):
    """Модель для статуса заказа."""

    PROCESSING = "processing", "Обработка заказа"
    ASSEMBLY = "assembly", "Сборка заказа"
    ITEM_PICKING = "item_picking", "Сборка товара для заказа"
    TO_SHIPPING_AREA = "to_shipping", "Доставка в зону отгрузки"
    AT_SHIPPING_AREA = "at_shipping", "Приемка в зоне отгрузки"
    DOC_PREPARATION = "docs", "Подготовка документов"
    DELIVERY = "delivery", "Доставка заказа"
    DELIVERED = "delivered", "Заказ доставлен"

    @classmethod
    def from_position(cls, position: str) -> str:
        """Преобразует роль сотрудника в соответствующий статус заказа."""
        position = position.lower()
        position_status_map = {
            "менеджер склада": cls.PROCESSING,
            "складской оператор": cls.ASSEMBLY,
            "комплектовщик": cls.ITEM_PICKING,
            "грузчик": cls.TO_SHIPPING_AREA,
            "приемщик": cls.AT_SHIPPING_AREA,
            "логист": cls.DOC_PREPARATION,
            "курьер": cls.DELIVERY,
        }
        return position_status_map.get(position)


class ShippingZone(models.Model):
    """Модель зона отгрузки."""

    ZONE_CHOICES = [
        ("city", "Город"),
        ("district", "Район"),
        ("region", "Область"),
    ]

    name = models.CharField(
        max_length=20, choices=ZONE_CHOICES, unique=True, verbose_name="Название зоны"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Описание зоны")

    def __str__(self):
        return self.get_name_display()

    class Meta:
        verbose_name = "Зона отгрузки"
        verbose_name_plural = "Зоны отгрузки"


class Order(models.Model):
    """Модель заказа."""

    order_id = models.AutoField(primary_key=True)
    order_date = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата оформления заказа"
    )
    products = models.ManyToManyField(
        "Product", through="OrderProduct", verbose_name="Товары"
    )
    employee = models.ManyToManyField(
        "users.Employee", through="OrderEmployeeHistory", verbose_name="Сотрудник"
    )
    client = models.ForeignKey(
        "users.Client",
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Клиент",
    )
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Сумма заказа"
    )
    address = models.ForeignKey(
        "Address", on_delete=models.CASCADE, verbose_name="Адрес доставки"
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PROCESSING,
        verbose_name="Статус заказа",
    )
    shipping_zone = models.ForeignKey(
        "ShippingZone",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Зона отгрузки",
    )

    def change_status(self, new_status, completed=False):
        """Меняет статус заказа и записывает его в историю."""
        self.status = new_status
        self.current_step = new_status
        self.save()

        # Создаем запись в истории
        OrderStatusHistory.objects.create(
            order=self, status=new_status, completed=completed
        )
        # Назначаем задачу сотрудникам для текущего этапа
        from tracker.services import assign_task_to_employee

        assign_task_to_employee(self, new_status)

    def calculate_total(self, save=False):
        total = sum(
            item.product.price * item.quantity for item in self.orderproduct_set.all()
        )
        self.total_amount = total
        if save:
            self.save()

    def __str__(self):
        return f"Order {self.order_id} - {self.total_amount} by {self.client}"


class OrderProduct(models.Model):
    """Промежуточная модель для хранения количества каждого товара в заказе."""

    order = models.ForeignKey("Order", on_delete=models.CASCADE, verbose_name="Заказ")
    product = models.ForeignKey(
        "Product", on_delete=models.CASCADE, verbose_name="Товар"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    def __str__(self):
        return f"{self.quantity} x {self.product.title} в заказе {self.order.order_id}"


class OrderStatusHistory(models.Model):
    """Модель для хранения информации о каждом изменении статуса с временными метками."""

    order = models.ForeignKey(
        "Order",
        on_delete=models.CASCADE,
        related_name="order_status_history",
        verbose_name="Заказ",
    )
    status = models.CharField(
        max_length=20, choices=OrderStatus.choices, verbose_name="Статус заказа"
    )
    timestamp = models.DateTimeField(
        default=timezone.now, verbose_name="Время изменения статуса"
    )
    completed = models.BooleanField(default=False, verbose_name="Завершён ли этап?")

    def __str__(self):
        return f"Заказ {self.order.order_id}: {self.status} в {self.timestamp}"

    class Meta:
        verbose_name = "История статуса заказа"
        verbose_name_plural = "История статусов заказов"
        ordering = ["-timestamp"]  # последние изменения вверху


class OrderEmployeeHistory(models.Model):
    """Модель для отслеживания сотрудников, работающих с заказом, и их задач."""

    order = models.ForeignKey(
        "Order",
        on_delete=models.CASCADE,
        related_name="order_employee_history",
        verbose_name="Заказ",
    )
    employee = models.ForeignKey(
        "users.Employee", on_delete=models.CASCADE, verbose_name="Сотрудник"
    )
    assigned_at = models.DateTimeField(
        default=timezone.now, verbose_name="Время назначения"
    )
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Время завершения"
    )
    task = models.ForeignKey(
        "Task",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="employee_histories",
        verbose_name="Задача",
    )

    @property
    def task_status(self):
        if self.task and self.task.is_completed:
            return "завершена"
        elif self.task and self.task.is_active:
            return "назначена"
        return "не определено"

    def __str__(self):
        return f"Сотрудник {self.employee} для заказа {self.order.order_id} (назначен в {self.assigned_at})"

    class Meta:
        verbose_name = "История сотрудников заказа"
        verbose_name_plural = "История сотрудников заказов"
        ordering = ["assigned_at"]  # Сортировка по времени назначения


class Task(models.Model):
    """Модель задачи для отслеживания статуса выполнения."""

    task_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(
        "Order", on_delete=models.CASCADE, related_name="tasks", verbose_name="Заказ"
    )
    shipping_zone = models.ForeignKey(
        "ShippingZone",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Зона отгрузки",
    )
    department = models.ForeignKey(
        "users.Department",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Отдел",
    )
    employee = models.ForeignKey(
        "users.Employee",
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="Сотрудник",
    )
    description = models.TextField(
        blank=True, null=True, verbose_name="Описание задачи"
    )
    status = models.CharField(
        max_length=50, choices=OrderStatus.choices, verbose_name="Статус задачи"
    )
    created_at = models.DateTimeField(
        default=timezone.now, verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    due_date = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата завершения"
    )
    is_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    depends_on = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="dependent_tasks",
    )

    def __str__(self):
        return f" Заказ {self.order.order_id} - {self.status}"

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ["-status"]
