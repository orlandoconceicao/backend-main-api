from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxLengthValidator, MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import F

class Base(models.Model):
    # Campos padrão reutilizáveis
    criacao = models.DateTimeField(auto_now_add=True)
    atualizacao = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        abstract = True

# Usuário
class Usuario(Base, AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True, db_index=True)  # login principal

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email  # mais limpo para logs/admin

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-criacao']
        indexes = [
            models.Index(fields=['criacao']),
            models.Index(fields=['email']),
        ]

# Curso
class Curso(Base):
    nome = models.CharField(max_length=120)
    descricao = models.TextField(validators=[MaxLengthValidator(500)])

    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('999.00'))
        ]
    )

    criado_por = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='cursos'
    )

    total_vendas = models.PositiveIntegerField(default=0)  # contador otimizado

    media_avaliacoes = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00')
    )

    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"

    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['-criacao']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['criado_por']),
        ]

# Avaliação
class Avaliacao(Base):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='avaliacoes'
    )

    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name='avaliacoes'
    )

    nota = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.00')),  # permite nota 0
            MaxValueValidator(Decimal('5.00'))
        ]
    )

    comentario = models.TextField(
        validators=[MaxLengthValidator(500)],
        blank=True
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Atualiza média do curso após nova avaliação
        media = self.curso.avaliacoes.aggregate(
            media=models.Avg('nota')
        )['media'] or Decimal('0.00')

        self.curso.media_avaliacoes = Decimal(media).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )
        self.curso.save(update_fields=['media_avaliacoes'])

    def __str__(self):
        return f"{self.usuario.email} avaliou {self.curso.nome} ({self.nota})"

    class Meta:
        verbose_name = 'Avaliacao'
        verbose_name_plural = 'Avaliacoes'
        ordering = ['-criacao']

        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'curso'],
                name='unique_avaliacao'  # evita duplicidade
            )
        ]

        indexes = [
            models.Index(fields=['curso']),
            models.Index(fields=['usuario']),
            models.Index(fields=['curso', 'usuario']),
        ]

# CompraStatus
class CompraStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    COMPLETED = "completed", "Concluído"
    REFUNDED = "refunded", "Reembolsado"

# Compra
class Compra(Base):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='compras'
    )

    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name='compras'
    )

    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    status = models.CharField(
        max_length=10,
        choices=CompraStatus.choices,
        default=CompraStatus.PENDING,
        db_index=True  # melhora filtro por status
    )

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        status_anterior = None

        # Busca status antigo apenas se já existir
        if not is_new:
            status_anterior = Compra.objects.get(pk=self.pk).status

        # Define preço automaticamente se não informado
        if not self.preco:
            self.preco = self.curso.preco

        # Garante precisão financeira
        self.preco = Decimal(self.preco).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        super().save(*args, **kwargs)

        # Incrementa vendas apenas na transição para concluído
        if (
            self.status == CompraStatus.COMPLETED and
            status_anterior != CompraStatus.COMPLETED
        ):
            Curso.objects.filter(pk=self.curso.pk).update(
                total_vendas=F('total_vendas') + 1
            )

        # Decrementa caso seja reembolsado
        if (
            self.status == CompraStatus.REFUNDED and
            status_anterior == CompraStatus.COMPLETED
        ):
            Curso.objects.filter(pk=self.curso.pk).update(
                total_vendas=F('total_vendas') - 1
            )

    def __str__(self):
        return f"{self.usuario.email} - {self.curso.nome} ({self.status})"

    class Meta:
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'
        ordering = ['-criacao']

        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'curso'],
                name='unique_compra'  # evita compra duplicada
            )
        ]

        indexes = [
            models.Index(fields=['usuario']),
            models.Index(fields=['curso']),
            models.Index(fields=['status']),
            models.Index(fields=['usuario', 'curso', 'status']),
        ]