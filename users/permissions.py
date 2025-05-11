from rest_framework.permissions import BasePermission

from .models import Client, Employee


class IsCladdingQuality(BasePermission):
    """
    Разрешение, которое позволяет создавать, редактировать и удалять товар
    только кладовщику или инспектору по качеству.
    """

    allowed_positions = ["кладовщик", "инспектор по качеству"]

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return isinstance(request.user, Employee) and request.user.position in self.allowed_positions


class IsSalesManager(BasePermission):
    """
    Разрешение, которое позволяет создавать, редактировать и удалять заказы
    только менеджеру по продажам.
    """

    allowed_positions = ["менеджер по продажам"]

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return isinstance(request.user, Employee) and request.user.position in self.allowed_positions


class IsDepartmentOfPersonnel(BasePermission):
    """
    Разрешение, которое позволяет создавать, редактировать и удалять сотрудников
    только сотруднику из отдела кадров.
    """

    allowed_positions = ["сотрудник отдела кадров"]

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return isinstance(request.user, Employee) and request.user.position in self.allowed_positions


class IsChangeStatusOrder(BasePermission):
    """
    Разрешение, которое позволяет сотрудникам изменять статус заказа.
    """

    allowed_positions = [
        "менеджер по продажам",
        "менеджер склада",
        "складской оператор",
        "комплектовщик",
        "грузчик",
        "приемщик",
        "логист",
        "курьер",
    ]

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return isinstance(request.user, Employee) and request.user.position in self.allowed_positions


class IsViewTaskOfEmployee(BasePermission):
    """
    Разрешение, которое позволяет сотрудникам среднего звена
    иметь информацию о выполнении задач связанных с выполнением заказа.
    """

    allowed_positions = [
        "менеджер по продажам",
        "менеджер склада",
        "складской оператор",
    ]

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return isinstance(request.user, Employee) and request.user.position in self.allowed_positions


class IsClient(BasePermission):
    """
    Разрешение, которое позволяет клиенту редактировать свои данные,
    в том числе адреса.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return isinstance(request.user, Client)
