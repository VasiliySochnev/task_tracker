from django.db.models import Count, Q
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Client, Department, Employee, User
from .permissions import IsDepartmentOfPersonnel, IsSalesManager
from .serializers import (BusyEmployeeSerializer, ClientSerializer,
                          DepartmentSerializer, EmployeeSerializer,
                          UserSerializer)


class UserViewSet(viewsets.ModelViewSet):
    """Сэт - контроллер для модели пользователя."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    lookup_field = "email"

    def perform_create(self, serializer):
        serializer.save(is_active=True)


class EmployeeViewSet(viewsets.ModelViewSet):
    """Сэт - контроллер для модели сотрудника."""

    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsDepartmentOfPersonnel]


class BusyEmployeesView(APIView):
    """Контроллер для отображения сотрудников, выполняющих задачи."""

    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        employees = (
            Employee.objects.annotate(
                active_tasks_count=Count("tasks", filter=Q(tasks__is_active=True))
            )
            .filter(active_tasks_count__gt=0)
            .order_by("-active_tasks_count")
        )
        serializer = BusyEmployeeSerializer(employees, many=True)
        return Response(serializer.data)


class ClientViewSet(viewsets.ModelViewSet):
    """Сэт - контроллер для модели клиента."""

    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsSalesManager]


class DepartmentViewSet(viewsets.ModelViewSet):
    """Сэт - контроллер для модели отдела."""

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsDepartmentOfPersonnel]
