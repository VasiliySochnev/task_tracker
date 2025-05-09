from django.urls import path
from rest_framework.routers import DefaultRouter

from tracker.apps import TrackerConfig
from tracker.views import (AddressViewSet, ImportantTasksView,
                           LeastBusyEmployeesView, OrderEmployeeHistoryViewSet,
                           OrderStatusHistoryViewSet, OrderViewSet,
                           ProductViewSet, TaskSummaryView, TaskViewSet,
                           get_product_price, order_detail)

app_name = TrackerConfig.name


router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="products")
router.register(r"orders", OrderViewSet, basename="orders")
router.register(r"addresses", AddressViewSet, basename="addresses")
router.register(r"tasks", TaskViewSet, basename="tasks")
router.register(
    r"orders_statuses_stories",
    OrderStatusHistoryViewSet,
    basename="orders_statuses_stories",
)
router.register(
    r"orders_employees_stories",
    OrderEmployeeHistoryViewSet,
    basename="orders_employees_stories",
)

urlpatterns = [
    path("admin/get-product-price/", get_product_price, name="get_product_price"),
    path("order_detail/<int:order_id>/", order_detail, name="order_detail"),
    path("tasks/important/", ImportantTasksView.as_view(), name="important_tasks"),
    path(
        "tasks/summary/<int:order_id>/", TaskSummaryView.as_view(), name="task-summary"
    ),
    path(
        "least_busy_employees/",
        LeastBusyEmployeesView.as_view(),
        name="least_busy_employees",
    ),
] + router.urls
