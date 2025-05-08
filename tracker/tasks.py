from celery import shared_task
from tracker.models import Order, Task, OrderStatus
from users.models import Employee

@shared_task
def create_order_task_chain(order_id):
    print(f"[CELERY] Starting chain for order {order_id}")
    order = Order.objects.get(pk=order_id)

    # первая задача – менеджер склада
    manager = Employee.objects.filter(position='менеджер склада').first()

    if manager:
        Task.objects.create(
            order=order,
            shipping_zone=order.shipping_zone,
            employee=manager,
            status=OrderStatus.PROCESSING,
            is_active=True
        )
        order.status = OrderStatus.PROCESSING
        order.save()



@shared_task
def assign_task_to_pending_orders():
    from tracker.services import assign_task_to_employee
    pending_orders = Order.objects.filter(status='processing')  # или другой статус, который тебя интересует
    for order in pending_orders:
        # Убедись, что заказ не назначен на сотрудников
        if order.tasks.filter(is_completed=False).exists():
            continue
        assign_task_to_employee(order, 'assembly')  # Пример: статус для сборки