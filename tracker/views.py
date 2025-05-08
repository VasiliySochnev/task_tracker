from rest_framework import viewsets
from django.views.decorators.csrf import csrf_protect
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework import status
from rest_framework.views import APIView
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from users.permissions import (
    IsChangeStatusOrder,
    IsCladdingQuality,
    IsClient,
    IsSalesManager,
    IsViewTaskOfEmployee,
)

from .models import (
    Address,
    Order,
    OrderEmployeeHistory,
    OrderStatusHistory,
    Product, Task, OrderStatus,
)
from .serializers import (
    AddressSerializer,
    OrderEmployeeHistorySerializer,
    OrderSerializer,
    OrderStatusHistorySerializer,
    ProductSerializer, TaskSerializer,
    TaskSummarySerializer,
)
from .utils import complete_and_create_next
from django.urls import reverse
from django.http import HttpResponseRedirect
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response



def get_product_price(request):
    """Метод для получения цены товара по его ID."""
    product_id = request.GET.get('product_id')
    try:
        product = Product.objects.get(pk=product_id)
        return JsonResponse({'price': product.price})
    except Product.DoesNotExist:
        return JsonResponse({'price': 0}, status=404)


@csrf_protect
def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    tasks = Task.objects.filter(order=order)

    status_history = OrderStatusHistory.objects.filter(order=order).order_by('-timestamp')
    employees_history = OrderEmployeeHistory.objects.filter(order=order).order_by('assigned_at')

    if request.method == "POST" and 'complete_task' in request.POST:
        task_id = request.POST.get('complete_task')
        task = get_object_or_404(Task, pk=task_id)

        # Завершаем текущую задачу и создаем следующую
        complete_and_create_next(task)

        return redirect('tracker:order_detail', order_id=order_id)

    return render(request, 'order_detail.html', {
        'order': order,
        'tasks': tasks,
        'status_history': status_history,
        'employees_history': employees_history,
    })

class ImportantTasksView(APIView):
    def get(self, request):
        order_id = request.query_params.get("order_id")

        if not order_id:
            return Response({"detail": "order_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(order_id=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        all_statuses = [status_choice[0] for status_choice in OrderStatus.choices]
        all_statuses_excl_last = all_statuses[:-1]

        try:
            current_index = all_statuses_excl_last.index(order.status)
        except ValueError:
            return Response({"detail": "Неверный статус заказа или заказ выполнен."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        remaining_statuses = OrderStatus.choices[current_index:len(all_statuses) - 1]

        formatted = [{"key": key, "label": label} for key, label in remaining_statuses]

        return Response(formatted)


class TaskSummaryView(APIView):
    def get(self, request, order_id):
        try:
            Order.objects.get(order_id=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        tasks = Task.objects.filter(order_id=order_id, is_active=True).select_related(
            'employee__department', 'employee__shipping_zone', 'order'
        )

        serializer = TaskSummarySerializer(tasks, many=True)
        return Response(serializer.data)



class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsCladdingQuality, IsSalesManager]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsSalesManager, IsClient, IsChangeStatusOrder]


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsSalesManager, IsClient]


class OrderStatusHistoryViewSet(viewsets.ModelViewSet):
    queryset = OrderStatusHistory.objects.all()
    serializer_class = OrderStatusHistorySerializer
    permission_classes = [IsSalesManager, IsClient, IsChangeStatusOrder]


class OrderEmployeeHistoryViewSet(viewsets.ModelViewSet):
    queryset = OrderEmployeeHistory.objects.all()
    serializer_class = OrderEmployeeHistorySerializer
    permission_classes = [IsViewTaskOfEmployee]
