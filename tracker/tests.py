from django.test import TestCase

from tracker.models import Address, Order, OrderProduct, Product, ShippingZone
from users.models import Client, Department, Employee


class OrderWorkflowTest(TestCase):
    def setUp(self):
        # Создаем зоны отгрузки
        self.city_zone = ShippingZone.objects.create(name="city")
        self.district_zone = ShippingZone.objects.create(name="district")

        # Создаем отделы
        self.dept1 = Department.objects.create(title="инструмент")
        self.dept2 = Department.objects.create(title="электрика")

        # Создаем клиента и адрес
        self.address = Address.objects.create(city="Москва", street="Тестовая", house=1)
        self.client = Client.objects.create(
            email="client@test.com",
            password="test12345",
            first_name="Иван",
            last_name="Клиент",
            client_type="B2C",
        )
        self.client.address.add(self.address)

        # Создаем сотрудников
        self.sales_manager = Employee.objects.create(
            email="sales@test.com", position="менеджер по продажам"
        )
        self.warehouse_manager = Employee.objects.create(
            email="warehouse@test.com", position="менеджер склада"
        )

        # По одному комплектовщику и оператору на каждый отдел
        self.operator1 = Employee.objects.create(
            email="op1@test.com", position="складской оператор", department=self.dept1
        )
        self.operator2 = Employee.objects.create(
            email="op2@test.com", position="складской оператор", department=self.dept2
        )
        self.picker1 = Employee.objects.create(
            email="picker1@test.com", position="комплектовщик", department=self.dept1
        )
        self.picker2 = Employee.objects.create(
            email="picker2@test.com", position="комплектовщик", department=self.dept2
        )
        self.loader1 = Employee.objects.create(
            email="loader1@test.com", position="грузчик", department=self.dept1
        )
        self.loader2 = Employee.objects.create(
            email="loader2@test.com", position="грузчик", department=self.dept2
        )

        # Приемщики
        self.receiver_city = Employee.objects.create(
            email="rc@test.com", position="приемщик", shipping_zone=self.city_zone
        )
        self.receiver_district = Employee.objects.create(
            email="rd@test.com", position="приемщик", shipping_zone=self.district_zone
        )

        # Логисты
        self.logist_city = Employee.objects.create(
            email="lc@test.com", position="логист", shipping_zone=self.city_zone
        )
        self.logist_district = Employee.objects.create(
            email="ld@test.com", position="логист", shipping_zone=self.district_zone
        )

        # Курьеры
        self.courier_city = Employee.objects.create(
            email="cc@test.com", position="курьер", shipping_zone=self.city_zone
        )
        self.courier_district = Employee.objects.create(
            email="cd@test.com", position="курьер", shipping_zone=self.district_zone
        )

        # Создаем товары
        self.product1 = Product.objects.create(
            title="Молоток",
            price=500,
            department=self.dept1,
            supplier=self.sales_manager,
        )
        self.product2 = Product.objects.create(
            title="Провод",
            price=150,
            department=self.dept2,
            supplier=self.sales_manager,
        )

    def test_create_order_and_assign_tasks(self):
        # Создаем заказ
        order = Order.objects.create(
            client=self.client, address=self.address, shipping_zone=self.city_zone
        )

        # Добавляем товары
        OrderProduct.objects.create(order=order, product=self.product1, quantity=2)
        OrderProduct.objects.create(order=order, product=self.product2, quantity=3)

        # Рассчитываем сумму
        order.calculate_total(save=True)

        # Проверка: сумма заказа
        expected_total = (2 * self.product1.price) + (3 * self.product2.price)
        self.assertEqual(order.total_amount, expected_total)

        # Меняем статус -> должно создать задачи
        order.change_status("processing")

        # Проверяем, что задачи назначены
        assigned_tasks = order.tasks.all()
        self.assertGreater(len(assigned_tasks), 0)
        print("\nНазначенные задачи:")
        for task in assigned_tasks:
            print(f"{task.status} -> {task.employee.position} ({task.employee})")
