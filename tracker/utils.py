from django.db import transaction
from django.utils import timezone

from tracker.models import (OrderEmployeeHistory, OrderStatus,
                            OrderStatusHistory, Task)
from tracker.services import assign_task_to_employee  # Метод назначения задач


def complete_and_create_next(task: Task):
    """
    Завершает текущую задачу и создает следующую (если применимо), обновляя историю и статус заказа.

    :param task: Объект текущей задачи, подлежащей завершению.
    """
    # Сопоставление статусов с ключами для назначения задач
    status_to_position = {
        OrderStatus.PROCESSING: "processing",
        OrderStatus.ASSEMBLY: "assembly",
        OrderStatus.ITEM_PICKING: "item_picking",
        OrderStatus.TO_SHIPPING_AREA: "to_shipping",
        OrderStatus.AT_SHIPPING_AREA: "at_shipping",
        OrderStatus.DOC_PREPARATION: "docs",
        OrderStatus.DELIVERY: "delivery",
    }

    # Определение следующего статуса
    next_status_map = {
        OrderStatus.PROCESSING: OrderStatus.ASSEMBLY,
        OrderStatus.ASSEMBLY: OrderStatus.ITEM_PICKING,
        OrderStatus.ITEM_PICKING: OrderStatus.TO_SHIPPING_AREA,
        OrderStatus.TO_SHIPPING_AREA: OrderStatus.AT_SHIPPING_AREA,
        OrderStatus.AT_SHIPPING_AREA: OrderStatus.DOC_PREPARATION,
        OrderStatus.DOC_PREPARATION: OrderStatus.DELIVERY,
    }

    with transaction.atomic():
        # Завершаем задачу
        task.is_completed = True
        task.is_active = False
        task.due_date = timezone.now()
        task.save()

        # Записываем в историю, кто и когда выполнил задачу
        OrderEmployeeHistory.objects.create(
            order=task.order,
            employee=task.employee,
            assigned_at=task.created_at,
            completed_at=timezone.now(),
            task=task,
        )

        # Проверка, существует ли уже запись о текущем статусе
        existing_incomplete = OrderStatusHistory.objects.filter(
            order=task.order, status=task.status, completed=False
        ).first()

        # Если запись уже есть и все задачи по статусу завершены — отмечаем как завершённую
        unfinished_same_stage = task.order.tasks.filter(
            status=task.status, is_completed=False
        ).exists()

        if existing_incomplete:
            if not unfinished_same_stage:
                existing_incomplete.completed = True
                existing_incomplete.save()
        else:
            # Создаем новую запись о статусе
            OrderStatusHistory.objects.create(
                order=task.order,
                status=task.status,
                timestamp=timezone.now(),
                completed=not unfinished_same_stage,
            )

        # Получаем следующий статус
        next_status = next_status_map.get(task.status)

        # Проверка условий перед переходом к доставке
        if next_status == OrderStatus.DELIVERY:
            all_received = (
                task.order.tasks.filter(status=OrderStatus.AT_SHIPPING_AREA)
                .exclude(is_completed=True)
                .exists()
            )
            docs_prepared = (
                task.order.tasks.filter(status=OrderStatus.DOC_PREPARATION)
                .exclude(is_completed=True)
                .exists()
            )
            if all_received or docs_prepared:
                print(
                    "Нельзя переходить к доставке: приемка или документы не завершены."
                )
                return

        # Если следующего статуса нет — завершаем заказ
        if not next_status:
            task.order.status = OrderStatus.DELIVERED
            task.order.save()
            return

        # Обновляем статус заказа
        task.order.status = next_status
        task.order.save()

        # Получаем ключ для назначения следующей задачи
        next_position = status_to_position.get(next_status)
        if not next_position:
            raise Exception(f"Неизвестный статус: {next_status}")

        # Если есть незавершённые задачи предыдущего этапа — приостанавливаем переход
        if next_status == OrderStatus.AT_SHIPPING_AREA:
            incomplete_tasks = task.order.tasks.filter(
                status=OrderStatus.TO_SHIPPING_AREA, is_completed=False
            )
            if incomplete_tasks.exists():
                print(
                    f"Еще не все грузчики завершили задачи для заказа {task.order.pk}, приемщик пока не назначается."
                )
                return

        # Назначаем следующую задачу
        assign_task_to_employee(
            task.order,
            new_status=next_position,
            department=task.department,
            shipping_zone=task.shipping_zone,
        )

        # Финальная проверка завершенности всех задач
        if all_tasks_completed(task.order):
            print(
                f"Все задачи завершены для заказа {task.order.pk}. Статус заказа обновлен."
            )
        else:
            print(f"Некоторые задачи все еще не завершены для заказа {task.order.pk}.")


def all_tasks_completed(order) -> bool:
    """
    Проверяет, завершены ли все задачи по заказу.

    :param order: Объект заказа.
    :return: True, если все задачи завершены, иначе False.
    """
    tasks = order.tasks.all()
    for task in tasks:
        if not task.is_completed:
            return False
    return True
