from django.contrib import admin
from django.db.models import Field, ForeignKey, ManyToManyField
from django.urls import reverse
from django.utils.html import format_html

from tracker.models import (Address, Order, OrderEmployeeHistory, OrderProduct,
                            OrderStatusHistory, Product, ShippingZone, Task)

from .models import Client, Department, Employee, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Регистрация в панели для пользователя."""

    list_display = [
        field.name
        for field in User._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]

    search_fields = [
        field.name
        for field in User._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]
    list_filter = [
        field.name
        for field in User._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    """Регистрация в панели для зон отгрузки."""

    list_display = [
        "name",
        "description",
    ]
    search_fields = [
        "name",
        "description",
    ]
    list_filter = [
        "name",
        "description",
    ]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Регистрация в панели для сотрудника."""

    list_display = [
        "position",
        "employee_id",
        "department",
        "work_vacation",
        "day_off",
        "shipping_zone",
    ]

    def active_tasks(self, obj):
        return Task.objects.filter(
            employee=obj, status__in=["assigned", "in_progress"]
        ).count()

    search_fields = [
        "position",
        "department",
        "work_vacation",
        "day_off",
        "shipping_zone",
    ]
    list_filter = [
        "position",
        "department",
        "work_vacation",
        "day_off",
        "shipping_zone",
    ]


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Регистрация в панели для клиента."""

    list_display = [
        field.name
        for field in Client._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]

    search_fields = [
        field.name
        for field in Client._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]
    list_filter = [
        field.name
        for field in Client._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Регистрация в панели для отдела."""

    list_display = [
        field.name
        for field in Department._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]

    search_fields = [
        field.name
        for field in Department._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]
    list_filter = [
        field.name
        for field in Department._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Регистрация в панели для адреса."""

    list_display = [
        field.name
        for field in Address._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]

    search_fields = [
        field.name
        for field in Address._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]
    list_filter = [
        field.name
        for field in Address._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Регистрация в панели для товара."""

    list_display = [
        "pk",
        "title",
        "price",
        "description",
        "department",
        "amount_remains",
        "amount_supplier",
        "supplier",
    ]
    search_fields = [
        "title",
        "price",
        "department",
    ]
    list_filter = [
        "title",
        "price",
        "department",
    ]


class OrderProductInline(admin.TabularInline):
    """Регистрация в панели для промежуточной модели вычисления общей цены."""

    model = OrderProduct
    extra = 1
    autocomplete_fields = ["product"]
    fields = ["product", "quantity", "price"]
    readonly_fields = ["price"]

    def price(self, obj):
        if obj.product:
            return obj.product.price * obj.quantity
        return 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Регистрация в панели для заказа."""

    inlines = [OrderProductInline]

    def get_form(self, request, obj=None, **kwargs):
        request._obj_ = obj  # сохраняем текущий заказ для inlines
        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        print(f"[ADMIN] save_model: BEFORE save, obj.pk = {obj.pk}")
        super().save_model(request, obj, form, change)
        print(f"[ADMIN] save_model: AFTER save, obj.pk = {obj.pk}")

        # Только если заказ уже создан
        if not is_new:
            obj.calculate_total(save=True)

            # Меняем статус, если он не PROCESSING
            if obj.status != "PROCESSING":
                obj.change_status(new_status="PROCESSING")

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        order_id = getattr(form.instance, "pk", None)
        print(f"[ADMIN] save_related: order_id = {order_id!r}, change = {change}")

        if change is False and order_id:
            from tracker.tasks import create_order_task_chain

            print(
                f"[ADMIN] launching create_order_task_chain for order_id = {order_id}"
            )
            create_order_task_chain.apply_async(args=[order_id])
        else:
            print("[ADMIN] Not launching task — either not new or order_id is None")


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """Регистрация в панели для истории статусов заказа."""

    list_display = [
        field.name
        for field in OrderStatusHistory._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]

    search_fields = [
        field.name
        for field in OrderStatusHistory._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]
    list_filter = [
        field.name
        for field in OrderStatusHistory._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]


@admin.register(OrderEmployeeHistory)
class OrderEmployeeHistoryAdmin(admin.ModelAdmin):
    """Регистрация в панели для истории сотрудников, которые работали с заказом."""

    list_display = [
        field.name
        for field in OrderEmployeeHistory._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]

    search_fields = [
        field.name
        for field in OrderEmployeeHistory._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]
    list_filter = [
        field.name
        for field in OrderEmployeeHistory._meta.get_fields()
        if isinstance(field, Field)
        and not isinstance(field, (ForeignKey, ManyToManyField))
    ]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Регистрация в панели для задач."""

    list_display = (
        "status",
        "task_id",
        "order_link",
        "employee",
        "shipping_zone",
        "created_at",
        "due_date",
        "is_completed",
        "is_active",
    )
    list_filter = ("status", "employee", "order", "is_completed", "is_active")
    search_fields = ("status", "order__order_id", "employee__name", "is_active")
    ordering = ("-status",)
    date_hierarchy = "created_at"

    @admin.display(description="Заказ")
    def order_link(self, obj):
        if obj.order:
            url = reverse("admin:tracker_order_change", args=[obj.order.pk])
            return format_html('<a href="{}">Заказ #{}</a>', url, obj.order.pk)
        return "-"
