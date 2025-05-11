from django.urls import path
from rest_framework.permissions import AllowAny
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from users.apps import UsersConfig
from users.views import (BusyEmployeesView, ClientViewSet, DepartmentViewSet,
                         EmployeeViewSet, UserViewSet)

app_name = UsersConfig.name

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"employees", EmployeeViewSet, basename="employee")
router.register(r"clients", ClientViewSet, basename="client")
router.register(r"departments", DepartmentViewSet, basename="department")

urlpatterns = [
    path(
        "login/",
        TokenObtainPairView.as_view(permission_classes=(AllowAny,)),
        name="login",
    ),
    path(
        "token/refresh/",
        TokenRefreshView.as_view(permission_classes=(AllowAny,)),
        name="token_refresh",
    ),
    path("busy-employees/", BusyEmployeesView.as_view(), name="busy_employee"),
]

urlpatterns += router.urls
