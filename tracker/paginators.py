from rest_framework.pagination import PageNumberPagination


class ProductPaginator(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class OrderPaginator(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class TaskPaginator(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
