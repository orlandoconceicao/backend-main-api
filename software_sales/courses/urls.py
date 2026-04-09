from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UsuarioViewSet,
    CursoViewSet,
    AvaliacaoViewSet,
    AdminCursoViewSet,
    AdminAvaliacaoViewSet,
    AdminCompraViewSet
)

# ROTAS PÚBLICAS
public_router = DefaultRouter()
public_router.register(r'usuarios', UsuarioViewSet, basename='usuarios')
public_router.register(r'cursos', CursoViewSet, basename='cursos')
public_router.register(r'avaliacoes', AvaliacaoViewSet, basename='avaliacoes')

# ROTAS ADMIN
admin_router = DefaultRouter()
admin_router.register(r'cursos', AdminCursoViewSet, basename='admin-cursos')
admin_router.register(r'avaliacoes', AdminAvaliacaoViewSet, basename='admin-avaliacoes')
admin_router.register(r'compras', AdminCompraViewSet, basename='admin-compras')

urlpatterns = [
    path('', include(public_router.urls)),          # Public routes: /api/usuarios/, /api/cursos/, /api/avaliacoes/
    path('admin/', include(admin_router.urls)),     # Admin routes: /api/admin/cursos/, etc.
]