from celery import shared_task
from django.db.models import Count, Min, Q

from tracker.models import Order, OrderStatus, Task
from users.models import Employee


@shared_task
def create_order_task_chain(order_id):
    print(f"[CELERY] Starting chain for order {order_id}")
    order = Order.objects.get(pk=order_id)

    # первая задача – менеджер склада
    manager = Employee.objects.filter(position="менеджер склада").first()

    if manager:
        Task.objects.create(
            order=order,
            shipping_zone=order.shipping_zone,
            employee=manager,
            status=OrderStatus.PROCESSING,
            is_active=True,
        )
        order.status = OrderStatus.PROCESSING
        order.save()


@shared_task
def assign_least_busy_position_employees():
    """
    Назначает задачи наименее загруженным сотрудникам:
    комплектовщикам, грузчикам, приемщикам, логистам, курьерам.
    Учитывает отдел и зону отгрузки.
    """
    positions = ["комплектовщик", "грузчик", "приемщик", "логист", "курьер"]

    # Ищем активные заказы по статусу
    orders = Order.objects.filter(
        status__in=[
            OrderStatus.ITEM_PICKING,
            OrderStatus.TO_SHIPPING_AREA,
            OrderStatus.AT_SHIPPING_AREA,
            OrderStatus.DOC_PREPARATION,
            OrderStatus.DELIVERY,
        ]
    )

    for order in orders:
        for position in positions:
            # Пропускаем, если задача уже назначена
            if order.tasks.filter(
                status=OrderStatus.from_position(position), is_completed=False
            ).exists():
                continue

            employees = Employee.objects.filter(
                position=position, is_active=True
            ).annotate(task_count=Count("tasks", filter=Q(tasks__is_completed=False)))

            # Фильтрация по отделу (если задан)
            if order.products.exists():
                department_ids = order.products.values_list(
                    "department_id", flat=True
                ).distinct()
                employees = employees.filter(department_id__in=department_ids)

            # Фильтрация по зоне отгрузки
            if order.shipping_zone_id:
                employees = employees.filter(shipping_zone_id=order.shipping_zone_id)

            if not employees.exists():
                continue

            min_count = (
                employees.aggregate(min_count=Min("task_count"))["min_count"] or 0
            )
            least_busy = employees.filter(task_count=min_count).first()

            if least_busy:
                Task.objects.create(
                    order=order,
                    employee=least_busy,
                    status=OrderStatus.from_position(position),
                    is_active=True,
                    department=least_busy.department,
                    shipping_zone=least_busy.shipping_zone,
                )
                print(
                    f"Назначена задача для заказа {order.pk} сотруднику {least_busy.get_full_name()} ({position})"
                )
