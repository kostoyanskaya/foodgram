from rest_framework.pagination import PageNumberPagination
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class LimitPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'


class CustomLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 25  # Значение по умолчанию для limit
    max_limit = 50      # Максимально допустимое значение для limit

    def get_limit(self, request):
        """
        Возвращает значение limit, которое зависит от параметра recipes_limit.
        """
        try:
            recipes_limit = int(request.query_params.get('recipes_limit'))
        except (ValueError, TypeError):
            recipes_limit = None

        if recipes_limit is not None and recipes_limit > 0:
            return min(recipes_limit, self.max_limit)
        else:
            return super().get_limit(request)

    def get_paginated_response(self, data):
        """
        Перезапись метода для добавления информации о количестве рецептов.
        """
        return Response({
            'count': self.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })
