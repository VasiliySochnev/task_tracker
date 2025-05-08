from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from django.db.models import Count, Q
from rest_framework.views import APIView
from .models import Client, Department, Employee, User
from rest_framework.permissions import IsAdminUser
from .permissions import IsDepartmentOfPersonnel, IsSalesManager
from rest_framework.response import Response

from .serializers import (
    ClientSerializer,
    DepartmentSerializer,
    EmployeeSerializer,
    UserSerializer,
    BusyEmployeeSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    lookup_field = "email"

    def perform_create(self, serializer):
        serializer.save(is_active=True)


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsDepartmentOfPersonnel]

class BusyEmployeesView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        employees = (
            Employee.objects.annotate(
                active_tasks_count=Count('tasks', filter=Q(tasks__is_active=True))
            )
            .filter(active_tasks_count__gt=0)
            .order_by('-active_tasks_count')
        )
        serializer = BusyEmployeeSerializer(employees, many=True)
        return Response(serializer.data)


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsSalesManager]


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsDepartmentOfPersonnel]
