from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 10  # Количество объектов на странице по умолчанию
    page_size_query_param = 'limit'  # Параметр запроса для изменения количества на странице
    max_page_size = 100 