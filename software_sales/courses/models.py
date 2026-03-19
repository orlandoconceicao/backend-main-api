from django.db import models
from django.core.validators import MaxLengthValidator, MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser
from django.db.models import Count
from decimal import Decimal, ROUND_HALF_UP

class Base(models.Model):
    criacao = models.DateTimeField(auto_now_add=True)
    atualizacao = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        abstract = True

# Usuário: username, email, password
class Usuario(Base, AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=False, null=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return f"{self.username} - {self.email}"
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-criacao', 'id']
        indexes = [models.Index(fields=['email'])]

# Curso: nome, descrição, preço, criado_em,
class Curso(Base):
    nome = models.CharField(null=False, blank=False, max_length=120)
    descricao = models.TextField(null=False, blank=False, validators=[MaxLengthValidator(500)])
    preco = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False, validators=[MinValueValidator(0.0), MaxValueValidator(999)])
    criado_por = models.ForeignKey("Usuario", on_delete=models.CASCADE, related_name='cursos')
    total_vendas = models.PositiveSmallIntegerField(default=0)


    def __str__(self):
        return f"{self.nome} - R$ {self.preco}" 
    
    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['-criacao']
        indexes = [models.Index(fields=['nome'])]
        
# Avaliação: usuário, curso, nota (1-5), comentário
class Avaliacao(Base):
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='avaliacoes')
    curso = models.ForeignKey('Curso', on_delete=models.CASCADE, related_name='avaliacoes')
    nota = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(5)])
    comentario = models.TextField(validators=[MaxLengthValidator(500)], blank=True)

    def __str__(self):
        return f"{self.usuario} avaliou {self.curso} com {self.nota}"
    
    class Meta: 
        verbose_name = 'Avaliacao'
        verbose_name_plural = 'Avaliacoes'
        ordering = ['-criacao']
        constraints = [models.UniqueConstraint(fields=['usuario', 'curso'], name='unique_avaliacao')]
        indexes = [
            models.Index(fields=['curso']),
            models.Index(fields=['usuario'])]

# Compra: usuário, curso, data e hora, preço, status (pending, completed, refunded)
class CompraStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    COMPLETED = "completed", "Concluído"
    REFUNDED = "refunded", "Reembolsado"

class Compra(Base):
    usuario = models.ForeignKey("Usuario", on_delete=models.CASCADE, related_name='compras')
    curso = models.ForeignKey("Curso", on_delete=models.CASCADE, related_name='compras')
    data = models.DateTimeField(auto_now_add=True)
    preco = models.DecimalField( max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=10, choices=CompraStatus.choices, default=CompraStatus.PENDING)

    def save(self, *args, **kwargs):
        # Define preço se não informado e garante arredondamento
        self.preco = self.preco or self.curso.preco
        self.preco = Decimal(self.preco).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        super().save(*args, **kwargs)  # salva a compra
        # Atualiza total de vendas do curso se a compra estiver COMPLETED
        total = self.curso.compras.filter(status=CompraStatus.COMPLETED).count()
        if self.curso.total_vendas != total:
            self.curso.total_vendas = total
            self.curso.save(update_fields=['total_vendas'])

    def __str__(self):
        return f"Compra do curso {self.curso} - Status {self.status}"
    
    class Meta:
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'
        ordering = ['-criacao']
        indexes = [models.Index(fields=['usuario', 'curso', 'status'])]
    