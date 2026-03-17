from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator

class Base(models.Model):
    criacao = models.DateTimeField(auto_now_add=True)
    atualizacao = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        abstract = True

# Usuário: username, email, password, is_admin, is_superuser
class Usuario(Base):
    username = models.CharField(unique=True, max_length=70, null=False, blank=False, error_messages={'blank': 'Deve conter nome para criar usuario'})
    email = models.EmailField(unique=True, blank=False, null=False, error_messages={'blank': 'Deve conter email para criar usuario'})
    password = models.CharField(blank=False, null=False, max_length=128, validators=[MinLengthValidator(8), RegexValidator(regex=r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', message="A senha deve conter letras maiúsculas, minúsculas, números e caracteres especiais.")])
    id_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.email})"
    class Meta:
        unique_together = ('username', 'email')

# Curso: nome, descrição, preço, criado_em, criado_por



# Avaliação: usuário, curso, nota (1-5), comentário



# Compra: usuário, curso, data, preço, status (pending, completed, refunded)