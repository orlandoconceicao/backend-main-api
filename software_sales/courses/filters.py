import django_filters
from .models import Curso, Compra, Avaliacao

# CURSO FILTER
class CursoFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains')
    preco_min = django_filters.NumberFilter(field_name='preco', lookup_expr='gte')
    preco_max = django_filters.NumberFilter(field_name='preco', lookup_expr='lte')
    criado_por = django_filters.NumberFilter(field_name='criado_por__id')

    class Meta:
        model = Curso
        fields = ['nome', 'preco_min', 'preco_max', 'criado_por']

# COMPRA FILTER
class CompraFilter(django_filters.FilterSet):
    status = django_filters.CharFilter()
    curso = django_filters.NumberFilter(field_name='curso__id')
    usuario = django_filters.NumberFilter(field_name='usuario__id')
    preco_min = django_filters.NumberFilter(field_name='preco', lookup_expr='gte')
    preco_max = django_filters.NumberFilter(field_name='preco', lookup_expr='lte')

    class Meta:
        model = Compra
        fields = ['status', 'curso', 'usuario', 'preco_min', 'preco_max']

# AVALIACAO FILTER
class AvaliacaoFilter(django_filters.FilterSet):
    curso = django_filters.NumberFilter(field_name='curso__id')
    usuario = django_filters.NumberFilter(field_name='usuario__id')
    nota_min = django_filters.NumberFilter(field_name='nota', lookup_expr='gte')
    nota_max = django_filters.NumberFilter(field_name='nota', lookup_expr='lte')

    class Meta:
        model = Avaliacao
        fields = ['curso', 'usuario', 'nota_min', 'nota_max']