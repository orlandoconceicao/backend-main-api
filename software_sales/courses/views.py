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
from .serializers import UsuarioSerializer, CursoSerializer, AvaliacaoSerializer, CompraSerializer
from .filters import CursoFilter, AvaliacaoFilter, CompraFilter

# RESPONSE PADRÃO
def response(success=True, data=None, error=None, status_code=status.HTTP_200_OK):
    return Response({
        "success": success,
        "data": data,
        "error": error
    }, status=status_code)

# PERMISSÃO ADMIN
class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

# USUÁRIO
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    def get_permissions(self):
        permission_map = {
            'create': [permissions.AllowAny],
            'login': [permissions.AllowAny],
            'cursos': [permissions.AllowAny],
            'comprar': [permissions.IsAuthenticated],
            'avaliar': [permissions.IsAuthenticated],
            'reembolso': [permissions.IsAuthenticated],
        }
        return [perm() for perm in permission_map.get(self.action, [permissions.IsAuthenticated])]

    # Cadastro
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response(True, data="Usuário criado com sucesso", status_code=201)

    # Login
    @action(detail=False, methods=['post'])
    def login(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        if not email or not password:
            return response(False, error="Email e senha são obrigatórios", status_code=400)

        user = authenticate(request, username=email, password=password)
        if not user:
            return response(False, error="Credenciais inválidas", status_code=401)

        refresh = RefreshToken.for_user(user)
        return response(True, data={
            "user": {"id": user.id, "email": user.email, "username": user.username},
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        })

    # Listar cursos públicos
    @action(detail=False, methods=['get'])
    def cursos(self, request):
        cursos = Curso.objects.filter(ativo=True).annotate(media=Avg('avaliacoes__nota'))
        data = [
            {"id": c.id, "nome": c.nome, "preco": c.preco, "media": round(c.media, 2) if c.media else None}
            for c in cursos
        ]
        return response(True, data=data)

    # Comprar curso
    @action(detail=False, methods=['post'])
    def comprar(self, request):
        curso_id = request.data.get("curso_id")
        if not curso_id:
            return response(False, error="curso_id é obrigatório", status_code=400)
        try:
            curso = Curso.objects.get(id=curso_id, ativo=True)
        except Curso.DoesNotExist:
            return response(False, error="Curso não encontrado", status_code=404)

        with transaction.atomic():
            compra, created = Compra.objects.get_or_create(
                usuario=request.user,
                curso=curso,
                defaults={"preco": curso.preco, "status": CompraStatus.COMPLETED}
            )
            if not created:
                return response(False, error="Curso já foi comprado", status_code=400)

        return response(True, data="Compra realizada com sucesso", status_code=201)

    # Avaliar curso
    @action(detail=False, methods=['post'])
    def avaliar(self, request):
        serializer = AvaliacaoSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response(True, data="Avaliação salva com sucesso")

    # Reembolso
    @action(detail=False, methods=['post'])
    def reembolso(self, request):
        compra_id = request.data.get("compra_id")
        if not compra_id:
            return response(False, error="compra_id é obrigatório", status_code=400)
        try:
            compra = Compra.objects.get(id=compra_id, usuario=request.user)
        except Compra.DoesNotExist:
            return response(False, error="Compra não encontrada", status_code=404)

        if compra.status != CompraStatus.COMPLETED:
            return response(False, error="Compra não elegível", status_code=400)

        if timezone.now() > compra.criacao + timedelta(days=7):
            return response(False, error="Prazo expirado", status_code=400)

        compra.status = CompraStatus.REFUNDED
        compra.save(update_fields=['status'])
        return response(True, data="Reembolso realizado com sucesso")


# ADMIN
class AdminCursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

class AdminAvaliacaoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Avaliacao.objects.all()
    serializer_class = AvaliacaoSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

class AdminCompraViewSet(viewsets.ModelViewSet):
    queryset = Compra.objects.all()
    serializer_class = CompraSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filterset_class = CompraFilter

    @action(detail=True, methods=['post'])
    def rejeitar_reembolso(self, request, pk=None):
        compra = self.get_object()
        if compra.status != CompraStatus.REFUNDED:
            return response(False, error="Reembolso não está pendente", status_code=400)

        compra.status = CompraStatus.COMPLETED
        compra.save(update_fields=['status'])
        return response(True, data="Reembolso rejeitado com sucesso")


# CURSOS PÚBLICOS
class CursoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Curso.objects.filter(ativo=True).annotate(media=Avg('avaliacoes__nota'))
    serializer_class = CursoSerializer
    permission_classes = [permissions.AllowAny]
    filterset_class = CursoFilter

# AVALIAÇÕES PÚBLICAS
class AvaliacaoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Avaliacao.objects.select_related('usuario', 'curso')
    serializer_class = AvaliacaoSerializer
    permission_classes = [permissions.AllowAny]
    filterset_class = AvaliacaoFilter