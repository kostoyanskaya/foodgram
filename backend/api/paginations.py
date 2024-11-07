from rest_framework.pagination import PageNumberPagination

class LimitPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'  # Параметр запроса для изменения количества объектов на странице
    max_page_size = 100