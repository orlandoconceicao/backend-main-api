from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Avg
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import Usuario, Curso, Compra, Avaliacao, CompraStatus

# RESPONSE PADRÃO
def response(success=True, data=None, error=None, status_code=status.HTTP_200_OK):
    # Padroniza todas as respostas da API
    return Response({
        "success": success,
        "data": data,
        "error": error
    }, status=status_code)

# PERMISSÕES
class IsAdmin(permissions.BasePermission):
    # Permite acesso apenas para admins
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

# USUÁRIO
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()

    def get_permissions(self):
        # Define permissões por ação
        permission_map = {
            'create': [permissions.AllowAny],
            'login': [permissions.AllowAny],
            'cursos': [permissions.AllowAny],
        }
        return [perm() for perm in permission_map.get(self.action, [permissions.IsAuthenticated])]

    # Cadastro de usuário
    def create(self, request):
        data = request.data

        # Valida campos obrigatórios
        if not data.get("username"):
            return response(False, error="Username é obrigatório", status_code=status.HTTP_400_BAD_REQUEST)

        if not data.get("email") or not data.get("password"):
            return response(False, error="Email e senha são obrigatórios", status_code=status.HTTP_400_BAD_REQUEST)

        # Evita email duplicado
        if Usuario.objects.filter(email=data.get("email")).exists():
            return response(False, error="Email já cadastrado", status_code=status.HTTP_400_BAD_REQUEST)

        # Criação segura do usuário
        Usuario.objects.create_user(
            username=data.get("username"),
            email=data.get("email"),
            password=data.get("password")
        )

        return response(True, data="Usuário criado com sucesso", status_code=status.HTTP_201_CREATED)

    # Login com JWT
    @action(detail=False, methods=['post'])
    def login(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return response(False, error="Email e senha são obrigatórios", status_code=status.HTTP_400_BAD_REQUEST)

        # Autenticação via email (USERNAME_FIELD)
        user = authenticate(request, username=email, password=password)

        if not user:
            return response(False, error="Credenciais inválidas", status_code=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)

        # Retorna tokens + dados básicos
        return response(True, data={
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username
            },
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        })

    # Lista cursos ativos com média
    @action(detail=False, methods=['get'])
    def cursos(self, request):
        cursos = Curso.objects.filter(ativo=True)\
            .annotate(media=Avg('avaliacoes__nota'))\
            .only('id', 'nome', 'preco')

        # Serialização manual leve
        data = [
            {
                "id": curso.id,
                "nome": curso.nome,
                "preco": curso.preco,
                "media": round(curso.media, 2) if curso.media else None
            }
            for curso in cursos
        ]

        return response(True, data=data)

    # Compra de curso
    @action(detail=False, methods=['post'])
    def comprar(self, request):
        curso_id = request.data.get("curso_id")

        if not curso_id:
            return response(False, error="curso_id é obrigatório", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            curso = Curso.objects.get(id=curso_id, ativo=True)
        except Curso.DoesNotExist:
            return response(False, error="Curso não encontrado", status_code=status.HTTP_404_NOT_FOUND)

        # Evita duplicação com transação
        with transaction.atomic():
            compra, created = Compra.objects.get_or_create(
                usuario=request.user,
                curso=curso,
                defaults={
                    "preco": curso.preco,
                    "status": CompraStatus.COMPLETED
                }
            )

            if not created:
                return response(False, error="Curso já foi comprado", status_code=status.HTTP_400_BAD_REQUEST)

        return response(True, data="Compra realizada com sucesso", status_code=status.HTTP_201_CREATED)

    # Avaliação de curso
    @action(detail=False, methods=['post'])
    def avaliar(self, request):
        data = request.data
        curso_id = data.get("curso_id")
        nota = data.get("nota")

        if not curso_id or nota is None:
            return response(False, error="curso_id e nota são obrigatórios", status_code=status.HTTP_400_BAD_REQUEST)

        # Validação de nota
        try:
            nota = float(nota)
        except (TypeError, ValueError):
            return response(False, error="Nota inválida", status_code=status.HTTP_400_BAD_REQUEST)

        if nota < 0 or nota > 5:
            return response(False, error="Nota deve estar entre 0 e 5", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            curso = Curso.objects.get(id=curso_id)
        except Curso.DoesNotExist:
            return response(False, error="Curso não encontrado", status_code=status.HTTP_404_NOT_FOUND)

        # Só pode avaliar se comprou
        if not Compra.objects.filter(
            usuario=request.user,
            curso=curso,
            status=CompraStatus.COMPLETED
        ).exists():
            return response(False, error="Você precisa comprar o curso antes de avaliar", status_code=status.HTTP_403_FORBIDDEN)

        # Atualiza ou cria avaliação
        Avaliacao.objects.update_or_create(
            usuario=request.user,
            curso=curso,
            defaults={
                "nota": nota,
                "comentario": data.get("comentario", "")
            }
        )

        return response(True, data="Avaliação salva com sucesso")

    # Reembolso de compra
    @action(detail=False, methods=['post'])
    def reembolso(self, request):
        compra_id = request.data.get("compra_id")

        if not compra_id:
            return response(False, error="compra_id é obrigatório", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            compra = Compra.objects.get(id=compra_id, usuario=request.user)
        except Compra.DoesNotExist:
            return response(False, error="Compra não encontrada", status_code=status.HTTP_404_NOT_FOUND)

        # Só permite reembolso se concluída
        if compra.status != CompraStatus.COMPLETED:
            return response(False, error="Compra não elegível para reembolso", status_code=status.HTTP_400_BAD_REQUEST)

        # Regra de 7 dias
        limite = compra.criacao + timedelta(days=7)

        if timezone.now() > limite:
            return response(False, error="Prazo de reembolso expirado", status_code=status.HTTP_400_BAD_REQUEST)

        compra.status = CompraStatus.REFUNDED
        compra.save(update_fields=['status'])

        return response(True, data="Reembolso realizado com sucesso")

# ADMIN
class AdminCursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdmin]


class AdminAvaliacaoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Avaliacao.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdmin]


class AdminCompraViewSet(viewsets.ModelViewSet):
    queryset = Compra.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    # Rejeitar reembolso
    @action(detail=True, methods=['post'])
    def rejeitar_reembolso(self, request, pk=None):
        compra = self.get_object()

        # Só pode rejeitar se estiver como reembolsado
        if compra.status != CompraStatus.REFUNDED:
            return response(False, error="Reembolso não está pendente", status_code=status.HTTP_400_BAD_REQUEST)

        compra.status = CompraStatus.COMPLETED
        compra.save(update_fields=['status'])
        return response(True, data="Reembolso rejeitado com sucesso")