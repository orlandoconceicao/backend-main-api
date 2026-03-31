from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Importa ViewSets do app
from .views import CursoViewSet, AvaliacaoViewSet

router = DefaultRouter()

# Rotas do domínio de cursos
router.register(r'cursos', CursoViewSet, basename='cursos')
router.register(r'avaliacoes', AvaliacaoViewSet, basename='avaliacoes')

urlpatterns = [
    path('', include(router.urls)),
]