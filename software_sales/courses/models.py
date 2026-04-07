from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxLengthValidator, MinValueValidator, MaxValueValidator
from django.db import models


class Base(models.Model):
    criacao = models.DateTimeField(auto_now_add=True)
    atualizacao = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        abstract = True


# Usuário
class Usuario(Base, AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True, db_index=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

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

    total_vendas = models.PositiveIntegerField(default=0)

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
            MinValueValidator(Decimal('1.00')),
            MaxValueValidator(Decimal('5.00'))
        ]
    )

    comentario = models.TextField(
        validators=[MaxLengthValidator(500)],
        blank=True
    )

    def save(self, *args, **kwargs):
        # 👇 agora só salva (média vai via SIGNAL)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.usuario.email} avaliou {self.curso.nome} ({self.nota})"

    class Meta:
        verbose_name = 'Avaliacao'
        verbose_name_plural = 'Avaliacoes'
        ordering = ['-criacao']

        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'curso'],
                name='unique_avaliacao'
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
        validators=[MinValueValidator(Decimal('1.00'))]
    )

    status = models.CharField(
        max_length=10,
        choices=CompraStatus.choices,
        default=CompraStatus.PENDING,
        db_index=True
    )

    def save(self, *args, **kwargs):
        # 👇 SEM lógica de vendas (isso agora é SIGNAL)

        if not self.preco:
            self.preco = self.curso.preco

        self.preco = Decimal(self.preco).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.usuario.email} - {self.curso.nome} ({self.status})"

    class Meta:
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'
        ordering = ['-criacao']

        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'curso'],
                name='unique_compra'
            )
        ]

        indexes = [
            models.Index(fields=['usuario']),
            models.Index(fields=['curso']),
            models.Index(fields=['status']),
            models.Index(fields=['usuario', 'curso', 'status']),
        ]