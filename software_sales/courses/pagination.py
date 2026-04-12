from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination, CursorPagination
from rest_framework.response import Response

# Padronizar respostas
class BasePagination:
    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "pagination": self.get_pagination_meta(),
            "data": data
        })

    def get_pagination_meta(self):
        raise NotImplementedError("Você precisa implementar get_pagination_meta()")

# Paginação padrão
class CustomPagination(PageNumberPagination, BasePagination):
    page_size = 10
    page_size_query_param = 'page_size'   # ?page_size=20
    max_page_size = 100
    page_query_param = 'page'             # ?page=2

    def get_pagination_meta(self):
        return {
            "total": self.page.paginator.count,  # pode ser pesado em tabelas grandes
            "page": self.page.number,
            "page_size": self.get_page_size(self.request),
            "total_pages": self.page.paginator.num_pages,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
        }

# Endpoints para listas grandes
class LargeResultsPagination(PageNumberPagination, BasePagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200

    def get_pagination_meta(self):
        return {
            "total": self.page.paginator.count,
            "page": self.page.number,
            "page_size": self.get_page_size(self.request),
            "total_pages": self.page.paginator.num_pages,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
        }

# Ideal para o front
class CustomLimitOffsetPagination(LimitOffsetPagination, BasePagination):
    default_limit = 10
    max_limit = 100

    def get_pagination_meta(self):
        return {
            "total": self.count,
            "limit": self.limit,
            "offset": self.offset,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
        }


# Performance alta em grandes volumes
class CustomCursorPagination(CursorPagination, BasePagination):
    page_size = 10
    ordering = '-criacao'  # precisa de index no campo!

    def get_pagination_meta(self):
        return {
            "page_size": self.page_size,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
        }