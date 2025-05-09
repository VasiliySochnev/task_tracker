from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Модель пользователя."""

    username = None
    email = models.EmailField(unique=True, verbose_name="Email")
    first_name = models.CharField(
        max_length=50, verbose_name="Имя", blank=True, null=True
    )
    sur_name = models.CharField(
        max_length=50, verbose_name="Отчество", blank=True, null=True
    )
    last_name = models.CharField(
        max_length=50, verbose_name="Фамилия", blank=True, null=True
    )
    phone = models.CharField(
        max_length=35, verbose_name="телефон", blank=True, null=True
    )
    city = models.CharField(max_length=100, verbose_name="город", blank=True, null=True)
    avatar = models.ImageField(
        upload_to="photo/avatars/", verbose_name="Аватар", blank=True, null=True
    )
    tg_chat_id = models.CharField(
        max_length=100, verbose_name="Чат ID телеграмма", blank=True, null=True
    )
    is_staff = models.BooleanField(
        default=False, verbose_name="Администратор", blank=True, null=True
    )
    is_active = models.BooleanField(
        default=True, verbose_name="Активность", blank=True, null=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        full_name = f"{self.last_name or ''} {self.first_name or ''} {self.sur_name or ''}".strip()
        return full_name if full_name else self.email

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Department(models.Model):
    """Модель отдел."""

    DEPARTMENT_CHOICES = [
        ("инструмент", "Инструмент"),
        ("электрика", "Электрика"),
        ("сухие смеси", "Сухие смеси"),
        ("сантехника", "Сантехника"),
        ("метизы", "Метизы"),
        ("лкп и гсм", "ЛКП и ГСМ"),
    ]
    title = models.CharField(
        max_length=50,
        choices=DEPARTMENT_CHOICES,
        verbose_name="Отдел",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f" Отдел {self.title}"

    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"
        ordering = ["title"]


class Employee(User):
    """Модель сотрудника."""

    POSITION_CHOICES = [
        ("сотрудник отдела кадров", "Сотрудник отдела кадров"),
        ("менеджер по продажам", "Менеджер по продажам"),
        ("менеджер склада", "Менеджер склада"),
        ("складской оператор", "Складской оператор"),
        ("инспектор по качеству", "Инспектор по качеству"),
        ("товаровед", "Товаровед"),
        ("логист", "Логист"),
        ("кладовщик", "Кладовщик"),
        ("комплектовщик", "Комплектовщик"),
        ("грузчик", "Грузчик"),
        ("приемщик", "Приемщик"),
        ("курьер", "Курьер"),
    ]
    position = models.CharField(
        max_length=50,
        choices=POSITION_CHOICES,
        verbose_name="Должность",
        blank=True,
        null=True,
    )
    employee_id = models.AutoField(primary_key=True)
    department = models.ForeignKey(
        "Department",
        on_delete=models.CASCADE,
        verbose_name="Отдел",
        blank=True,
        null=True,
    )
    work_vacation = models.BooleanField(default=False, verbose_name="Рабочий отпуск")
    day_off = models.BooleanField(default=False, verbose_name="Выходные")
    shipping_zone = models.ForeignKey(
        "tracker.ShippingZone",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Зона отгрузки (для логистов, курьеров и приемщиков)",
    )

    def __str__(self):
        if self.department:
            return f"{self.position} {self.get_full_name()} {self.department}"
        elif self.shipping_zone:
            return f"{self.position} {self.get_full_name()} {self.shipping_zone}"
        else:
            return f"{self.position} {self.get_full_name()}"

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ["position"]


class Client(User):
    """Модель клиента."""

    CLIENT_TYPE_CHOICES = [
        ("B2B", "B2B"),
        ("B2C", "B2C"),
    ]
    client_id = models.AutoField(primary_key=True)
    client_type = models.CharField(max_length=3, choices=CLIENT_TYPE_CHOICES)
    organization_name = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Название организации"
    )
    o_g_r_n = models.CharField(
        max_length=15, blank=True, null=True, verbose_name="ОГРН"
    )
    i_n_n = models.CharField(max_length=12, blank=True, null=True, verbose_name="ИНН")
    bank_account = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Расчетный счет для B2B"
    )
    address = models.ManyToManyField(
        "tracker.Address", related_name="clients", verbose_name="Адреса клиента"
    )

    def __str__(self):
        base_info = f"{self.address}, {self.phone}"
        if self.client_type == "B2B":
            return f"{self.organization_name} | {base_info}"
        return f"{self.first_name} {self.last_name} | {base_info}"


    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ["first_name", "sur_name", "last_name", "phone"]
