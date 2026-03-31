from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Importa ViewSets principais
from courses.views import (
    UsuarioViewSet,
    AdminCursoViewSet,
    AdminAvaliacaoViewSet,
    AdminCompraViewSet
)

# Router principal da API
router = DefaultRouter()

# Rotas públicas e do usuário
router.register(r'usuarios', UsuarioViewSet, basename='usuarios')

# Rotas administrativas (separadas por organização)
router.register(r'admin/cursos', AdminCursoViewSet, basename='admin-cursos')
router.register(r'admin/avaliacoes', AdminAvaliacaoViewSet, basename='admin-avaliacoes')
router.register(r'admin/compras', AdminCompraViewSet, basename='admin-compras')

urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),

    # Rotas principais da API
    path('api/', include(router.urls)),

    # Rotas separadas por app (melhor organização)
    path('api/', include('courses.urls')),

    # Autenticação JWT
    path('api/auth/', include('rest_framework_simplejwt.urls')),
]