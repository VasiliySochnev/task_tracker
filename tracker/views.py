from django.db.models import Count, Min, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_protect
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from .paginators import ProductPaginator, OrderPaginator, TaskPaginator
from users.models import Employee
from users.permissions import (IsChangeStatusOrder, IsCladdingQuality,
                               IsClient, IsSalesManager, IsViewTaskOfEmployee)

from .models import (Address, Order, OrderEmployeeHistory, OrderStatus,
                     OrderStatusHistory, Product, Task)
from .serializers import (AddressSerializer, OrderEmployeeHistorySerializer,
                          OrderSerializer, OrderStatusHistorySerializer,
                          ProductSerializer, TaskSerializer,
                          TaskSummarySerializer)
from .utils import complete_and_create_next


def get_product_price(request):
    """
    Получение цены продукта по его ID (используется на фронте для автозаполнения).
    """
    product_id = request.GET.get("product_id")
    try:
        product = Product.objects.get(pk=product_id)
        return JsonResponse({"price": product.price})
    except Product.DoesNotExist:
        return JsonResponse({"price": 0}, status=404)


@csrf_protect
def order_detail(request, order_id):
    """
    Отображение детальной информации о заказе: список задач, история статусов и сотрудников.
    Также обрабатывает POST-запросы для завершения текущей задачи и создания следующей.
    """
    order = get_object_or_404(Order, pk=order_id)
    tasks = Task.objects.filter(order=order)

    status_history = OrderStatusHistory.objects.filter(order=order).order_by(
        "-timestamp"
    )
    employees_history = OrderEmployeeHistory.objects.filter(order=order).order_by(
        "assigned_at"
    )

    # Обработка кнопки "Завершить задачу"
    if request.method == "POST" and "complete_task" in request.POST:
        task_id = request.POST.get("complete_task")
        task = get_object_or_404(Task, pk=task_id)

        # Завершить текущую задачу и создать следующую по цепочке
        complete_and_create_next(task)

        return redirect("tracker:order_detail", order_id=order_id)

    return render(
        request,
        "order_detail.html",
        {
            "order": order,
            "tasks": tasks,
            "status_history": status_history,
            "employees_history": employees_history,
        },
    )


class ImportantTasksView(APIView):
    """
    API для получения оставшихся ключевых статусов заказа.
    Возвращает список статусов, начиная с текущего и до предпоследнего.
    """

    def get(self, request):
        order_id = request.query_params.get("order_id")

        if not order_id:
            return Response(
                {"detail": "order_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            order = Order.objects.get(order_id=order_id)
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Получаем все возможные статусы и отрезаем последний (завершённый)
        all_statuses = [status_choice[0] for status_choice in OrderStatus.choices]
        all_statuses_excl_last = all_statuses[:-1]

        try:
            current_index = all_statuses_excl_last.index(order.status)
        except ValueError:
            return Response(
                {"detail": "Неверный статус заказа или заказ уже завершён."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Формируем список оставшихся статусов
        remaining_statuses = OrderStatus.choices[current_index : len(all_statuses) - 1]
        formatted = [{"key": key, "label": label} for key, label in remaining_statuses]

        return Response(formatted)


class TaskSummaryView(APIView):
    """
    API для получения активных задач по конкретному заказу.
    Используется в интерфейсе сотрудника для просмотра текущих задач.
    """

    def get(self, request, order_id):
        try:
            Order.objects.get(order_id=order_id)
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Получаем только активные задачи и связанные данные для оптимизации
        tasks = Task.objects.filter(order_id=order_id, is_active=True).select_related(
            "employee__department", "employee__shipping_zone", "order"
        )

        serializer = TaskSummarySerializer(tasks, many=True)
        return Response(serializer.data)


class TaskViewSet(viewsets.ModelViewSet):
    """
    CRUD-интерфейс для задач (Task).
    """

    queryset = Task.objects.all()
    pagination_class = TaskPaginator
    serializer_class = TaskSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    CRUD-интерфейс для продуктов.
    Доступен только для менеджеров по продажам и сотрудников по контролю качества.
    """

    queryset = Product.objects.all()
    pagination_class = ProductPaginator
    serializer_class = ProductSerializer
    permission_classes = [IsCladdingQuality, IsSalesManager]


class OrderViewSet(viewsets.ModelViewSet):
    """
    CRUD-интерфейс для заказов.
    Доступен клиентам и менеджерам по продажам. Также разрешено менять статус.
    """

    queryset = Order.objects.all()
    pagination_class = OrderPaginator
    serializer_class = OrderSerializer
    permission_classes = [IsSalesManager, IsClient, IsChangeStatusOrder]


class AddressViewSet(viewsets.ModelViewSet):
    """
    CRUD-интерфейс для адресов доставки.
    Доступен клиентам и менеджерам по продажам.
    """

    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsSalesManager, IsClient]


class OrderStatusHistoryViewSet(viewsets.ModelViewSet):
    """
    CRUD-интерфейс для просмотра и управления историей изменения статусов заказа.
    """

    queryset = OrderStatusHistory.objects.all()
    serializer_class = OrderStatusHistorySerializer
    permission_classes = [IsSalesManager, IsClient, IsChangeStatusOrder]


class OrderEmployeeHistoryViewSet(viewsets.ModelViewSet):
    """
    CRUD-интерфейс для работы с историей назначения сотрудников на заказы.
    Только для просмотра задач сотрудниками.
    """

    queryset = OrderEmployeeHistory.objects.all()
    serializer_class = OrderEmployeeHistorySerializer
    permission_classes = [IsViewTaskOfEmployee]


class LeastBusyEmployeesView(APIView):
    """
    Возвращает наименее загруженных сотрудников по должностям:
    комплектовщики, грузчики, приемщики, логисты, курьеры.
    Учитывает отдел и зону отгрузки, если указаны.
    """

    def get(self, request):
        positions = ["комплектовщик", "грузчик", "приемщик", "логист", "курьер"]
        results = []

        for position in positions:
            employees = Employee.objects.filter(
                position=position, is_active=True
            ).annotate(task_count=Count("tasks", filter=Q(tasks__is_completed=False)))

            if not employees.exists():
                continue

            # Вычисляем минимальную загруженность (включая сотрудников с 0 задач)
            min_task_count = (
                employees.aggregate(min_count=Min("task_count"))["min_count"] or 0
            )
            least_busy = employees.filter(task_count=min_task_count)

            for emp in least_busy:
                results.append(
                    {
                        "id": emp.id,
                        "full_name": emp.get_full_name(),
                        "position": emp.position,
                        "department": emp.department.title if emp.department else None,
                        "shipping_zone": (
                            emp.shipping_zone.name if emp.shipping_zone else None
                        ),
                        "task_count": emp.task_count,
                    }
                )

        if not results:
            return Response(
                {"detail": "Нет подходящих сотрудников."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(results, status=status.HTTP_200_OK)
