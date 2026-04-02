from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UsuarioViewSet,
    AdminCursoViewSet,
    AdminAvaliacaoViewSet,
    AdminCompraViewSet
)

# Router principal → rotas públicas da API
router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuarios')

# Router admin → rotas restritas (staff)
admin_router = DefaultRouter()
admin_router.register(r'cursos', AdminCursoViewSet, basename='admin-cursos')
admin_router.register(r'avaliacoes', AdminAvaliacaoViewSet, basename='admin-avaliacoes')
admin_router.register(r'compras', AdminCompraViewSet, basename='admin-compras')

urlpatterns = [
    # Inclui rotas públicas (ex: /api/usuarios/)
    path('', include(router.urls)),

    # Inclui rotas admin (ex: /api/admin/cursos/)
    path('admin/', include(admin_router.urls)),
]
'''
---------Usuários
/api/usuarios/
/api/usuarios/login/
/api/usuarios/cursos/
/api/usuarios/comprar/
/api/usuarios/avaliar/
/api/usuarios/reembolso/
---------Admin
/api/admin/cursos/
/api/admin/avaliacoes/
/api/admin/compras/
/api/admin/compras/{id}/rejeitar_reembolso/
'''