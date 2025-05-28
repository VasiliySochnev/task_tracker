import logging

from django.db.models import Count, Q
from django.utils import timezone

from tracker.models import OrderEmployeeHistory, Task
from users.models import Department, Employee

logger = logging.getLogger(__name__)

# Сопоставление статусов заказа с должностями сотрудников и необходимостью учитывать зону отгрузки
STATUS_POSITION_MAPPING = {
    "processing": {"position": "менеджер склада", "use_shipping_zone": False},
    "assembly": {"position": "складской оператор", "use_shipping_zone": False},
    "item_picking": {"position": "комплектовщик", "use_shipping_zone": False},
    "to_shipping": {"position": "грузчик", "use_shipping_zone": False},
    "at_shipping": {"position": "приемщик", "use_shipping_zone": True},
    "docs": {"position": "логист", "use_shipping_zone": True},
    "delivery": {"position": "курьер", "use_shipping_zone": True},
}


def _create_task_and_history(
    order, status, employee, shipping_zone=None, department=None
):
    """
    Создаёт задачу и историю её назначения для конкретного сотрудника.

    :param order: Заказ, к которому относится задача.
    :param status: Текущий статус этапа заказа.
    :param employee: Сотрудник, которому назначается задача.
    :param shipping_zone: Зона отгрузки (если применяется).
    :param department: Отдел (если применяется).
    """
    # Проверка на дублирующие незавершённые задачи для того же сотрудника и статуса
    if Task.objects.filter(
        order=order, status=status, employee=employee, is_completed=False
    ).exists():
        print(
            f"Задача уже назначена для сотрудника {employee.get_full_name()} на статус {status}"
        )
        return

    # Создание задачи
    task = Task.objects.create(
        order=order,
        department=department,
        shipment_zone=shipping_zone,
        employee=employee,
        status=status,
        is_active=True,
    )

    # Создание записи в истории назначения
    OrderEmployeeHistory.objects.create(
        order=task.order,
        employee=task.employee,
        assigned_at=task.created_at,
        completed_at=timezone.now(),
        task=task,
    )

    print(
        f"Назначена задача: {employee.get_full_name()} ({status}) для заказа {order.pk}"
    )


def assign_task_to_employee(order, new_status, department=None, shipping_zone=None):
    """
    Назначает задачу соответствующему сотруднику, исходя из статуса заказа и его контекста.

    :param order: Заказ, по которому требуется назначение.
    :param new_status: Новый статус заказа.
    :param department: Отдел (опционально).
    :param shipping_zone: Зона отгрузки (опционально).
    """
    position_info = STATUS_POSITION_MAPPING.get(new_status)
    if not position_info:
        print(f"Статус {new_status} не найден в STATUS_POSITION_MAPPING")
        return

    position = position_info["position"]
    shipping_zone = position_info["use_shipping_zone"]

    # Фильтрация сотрудников по должности и активности
    employees = Employee.objects.filter(position=position, is_active=True)

    # Фильтрация по зоне отгрузки, если необходимо
    if shipping_zone and order.shipping_zone:
        employees = employees.filter(shipping_zone=order.shipping_zone)

    # Если задан отдел — фильтрация по нему
    elif department:
        employees = employees.filter(department=department)

    # Иначе — фильтрация по отделам товаров, входящих в заказ
    else:
        department_ids = order.products.values_list(
            "department_id", flat=True
        ).distinct()
        employees = employees.filter(department__in=department_ids)

    # Исключение сотрудников с более чем 2 активными заказами (не для грузчиков/приемщиков)
    if position not in ["грузчик", "приемщик"]:
        employees = employees.annotate(
            active_orders=Count(
                "tasks__order", filter=Q(tasks__is_completed=False), distinct=True
            )
        ).filter(active_orders__lt=3)

    # Специальная сортировка для грузчиков — по количеству задач в той же зоне
    if position == "грузчик":
        employees = employees.annotate(
            same_zone_tasks=Count(
                "tasks",
                filter=Q(
                    tasks__shipping_zone=order.shipping_zone, tasks__is_completed=False
                ),
            )
        ).order_by("same_zone_tasks")

    # Обработка "зоновых" позиций — просто назначаем первого подходящего
    if position in ["приемщик", "логист", "курьер"]:
        selected_employee = employees.first()
        if selected_employee:
            Task.objects.create(
                order=order,
                shipping_zone=order.shipping_zone,
                employee=selected_employee,
                status=new_status,
                is_active=True,
                department=None,
            )
            OrderEmployeeHistory.objects.create(
                order=order,
                employee=selected_employee,
            )
            print(
                f"Назначена задача: {selected_employee.get_full_name()} для зоны {order.shipping_zone}"
            )
        else:
            print(
                f"Нет сотрудников для позиции {position} в зоне {order.shipping_zone}"
            )
        return

    # Для остальных позиций — перебираем все отделы, задействованные в заказе
    department_ids = order.products.values_list("department_id", flat=True).distinct()

    for dept_id in department_ids:
        department = Department.objects.get(id=dept_id)

        # Ограничиваем выборку сотрудников заданным отделом
        dept_employees = employees.filter(department=department)

        # Для комплектовщиков — выбираем тех, у кого нет задач в этом отделе
        if position == "комплектовщик":
            dept_employees = dept_employees.annotate(
                dept_task_count=Count(
                    "tasks",
                    filter=Q(tasks__department=department, tasks__is_completed=False),
                )
            ).filter(dept_task_count=0)

        # Для грузчиков — аналогичная логика по отделу
        elif position == "грузчик":
            dept_employees = dept_employees.annotate(
                dept_task_count=Count(
                    "tasks",
                    filter=Q(tasks__department=department, tasks__is_completed=False),
                )
            ).filter(dept_task_count=0)

        # Назначение первого подходящего сотрудника
        selected_employee = dept_employees.first()

        if selected_employee:
            Task.objects.create(
                order=order,
                shipping_zone=order.shipping_zone if shipping_zone else None,
                employee=selected_employee,
                status=new_status,
                is_active=True,
                department=department,
            )
            OrderEmployeeHistory.objects.create(
                order=order,
                employee=selected_employee,
            )
            print(
                f"Назначена задача: {selected_employee.get_full_name()} для отдела {department.title}"
            )
        else:
            print(
                f"Нет подходящих сотрудников для статуса {new_status} и позиции {position} в отделе {department.title}"
            )
