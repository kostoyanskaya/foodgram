from rest_framework.pagination import PageNumberPagination
from rest_framework.pagination import LimitOffsetPagination


class LimitPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'


class CustomLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 100
