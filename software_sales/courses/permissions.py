from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import Compra, CompraStatus

# Permissão geral ao ADMIN
class IsAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True  # libera leitura para qualquer usuário

        # só permite escrita se for usuário autenticado e admin (is_staff)
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)

# Apenas dono pode modificar
class IsOwner(BasePermission):

    def has_object_permission(self, request, view, obj):
        # bloqueia se não estiver autenticado
        if not request.user or not request.user.is_authenticated:
            return False

        # permite apenas se o usuário for o dono do objeto
        return obj.usuario == request.user

# Só quem comprou pode avaliar/acessar conteúdo
class HasPurchasedCourse(BasePermission):
    message = "Você precisa comprar este curso."  # mensagem padrão de erro

    def has_permission(self, request, view):
        # garante que o usuário está logado
        if not request.user or not request.user.is_authenticated:
            return False

        # tenta obter curso_id de várias fontes (body, query ou URL)
        curso_id = (
            request.data.get('curso_id') or
            request.query_params.get('curso_id') or
            getattr(view, 'kwargs', {}).get('curso_id') or
            getattr(view, 'kwargs', {}).get('pk')
        )

        # se não encontrar o curso_id, bloqueia
        if not curso_id:
            self.message = "curso_id não informado."
            return False

        # verifica no banco se o usuário comprou o curso com status COMPLETED
        return Compra.objects.filter(
            usuario_id=request.user.id,  # usa id para otimizar
            curso_id=curso_id,
            status=CompraStatus.COMPLETED
        ).only('id').exists()  # consulta leve (só verifica existência)