from django.core.paginator import EmptyPage
from django.db.models.query import QuerySet
from rest_framework import pagination
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


class StandardPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    # get_all=true devolve a lista inteira, sem paginar. Sem login, só
    # quando o total não passa deste limite. A página pública de
    # parlamentares usa get_all para legislaturas e parlamentares.
    get_all_max_anonimo = 500

    def paginate_queryset(self, queryset, request, view=None):
        if request.query_params.get('get_all', '').lower() == 'true':
            if not request.user.is_authenticated:
                self.verifica_limite_get_all(queryset)
            return None
        return super().paginate_queryset(queryset, request, view=view)

    def verifica_limite_get_all(self, queryset):
        limite = self.get_all_max_anonimo
        if isinstance(queryset, QuerySet):
            total = queryset[:limite + 1].count()
        else:
            total = len(queryset)

        if total > limite:
            raise ValidationError({'detail': (
                f'Sem autenticação, get_all=true só pode ser usado com até '
                f'{limite} registros. Use a paginação (page e page_size).')})

    def get_paginated_response_schema(self, schema):
        r = {
            'type': 'object',
            'properties': {
                'pagination': {
                    'type': 'object',
                    'properties': {
                        'links': {
                            'type': 'object',
                            'properties': {
                                'next': {
                                    'type': 'string',
                                    'nullable': True,
                                    'format': 'uri',
                                    'example': 'http://api.example.org/accounts/?{page_query_param}=4'.format(
                                        page_query_param=self.page_query_param)
                                },
                                'previous': {
                                    'type': 'string',
                                    'nullable': True,
                                    'format': 'uri',
                                    'example': 'http://api.example.org/accounts/?{page_query_param}=2'.format(
                                        page_query_param=self.page_query_param)
                                },
                            }
                        },
                        'previous_page': {
                            'type': 'integer',
                            'example': 123,
                        },
                        'next_page': {
                            'type': 'integer',
                            'example': 123,
                        },
                        'start_index': {
                            'type': 'integer',
                            'example': 123,
                        },
                        'end_index': {
                            'type': 'integer',
                            'example': 123,
                        },
                        'total_entries': {
                            'type': 'integer',
                            'example': 123,
                        },
                        'total_pages': {
                            'type': 'integer',
                            'example': 123,
                        },
                        'page': {
                            'type': 'integer',
                            'example': 123,
                        },
                    }
                },
                'results': schema,
            },
        }
        return r

    def get_paginated_response(self, data):
        try:
            previous_page_number = self.page.previous_page_number()
        except EmptyPage:
            previous_page_number = None

        try:
            next_page_number = self.page.next_page_number()
        except EmptyPage:
            next_page_number = None

        return Response({
            'pagination': {
                'links': {
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link(),
                },
                'previous_page': previous_page_number,
                'next_page': next_page_number,
                'start_index': self.page.start_index(),
                'end_index': self.page.end_index(),
                'total_entries': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'page': self.page.number,
            },
            'results': data,

        })
