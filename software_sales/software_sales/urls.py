from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Painel administrativo padrão do Django
    path('admin/', admin.site.urls),

    # Todas as rotas da API (delegadas ao app courses)
    path('api/', include('courses.urls')),

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