from rest_framework import serializers
from decimal import Decimal
from .models import Usuario, Curso, Avaliacao, Compra, CompraStatus

# Serializer => Usuario 
class UsuarioSerializer(serializers.ModelSerializer):
    # Senha so para escrita, não retorna na API
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        # Campo exposto
        fields = ['id', 'email', 'username', 'password', 'criacao']
        # Campos controlado pelo backend
        read_only_fields = ['id', 'criacao']

    def create(self, validated_data):
        # Cria usuario com senha criptografada
        return Usuario.objects.create_user(**validated_data)
    
    def validate_email(self, value):
        # Normaliza email
        return value.lower()


# Serializer => Curso
class CursoSerializer(serializers.ModelSerializer):
    # Nome do criador (campo relacionado)
    criado_por_nome = serializers.CharField(source='criado_por.username', read_only=True)
    # Campo calculado (usar annotate view)
    total_avaliacoes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Curso
        fields = [
            'id', 'nome', 'descricao', 'preco',
            'criado_por', 'criado_por_nome', 'total_vendas', 'total_avaliacoes',
            'criacao'
        ]
        # Impede manipulação de dados sensíveis
        read_only_fields = ['id', 'total_vendas', 'criacao', 'criado_por']

    def validate_preco(self, value):
        # Valida preço mínimo
        if value < Decimal('0.00'):
            raise serializers.ValidationError("Preço inválido.")
        return value 
    
    def create(self, validated_data):
        # Define automaticamente o criador
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Usuário não identificado.")
        
        validated_data['criado_por'] = request.user
        return super().create(validated_data)
    

# Serializer = Avaliacao
class AvaliacaoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Avaliacao
        fields = ['id', 'usuario', 'curso', 'nota', 'comentario', 'criacao']
        # Usuario vem de backend
        read_only_fields = ['id', 'criacao', 'usuario']

    def validate_nota(self, value):
        # Garante nota de 1 a 5
        if value < 1 or value > 5:
            raise serializers.ValidationError("Nota deve ser de 1 a 5")
        return value    
    
    def validate(self, data):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Usuário não identificado.")
        
        usuario = request.user
        curso = data.get('curso') or getattr(self.instance, 'curso', None)

        # Curso obrigatório
        if not curso:
            raise serializers.ValidationError("Curso é obrigatório.")
        
        # Verifica se comprou
        if not Compra.objects.filter(
            usuario=usuario, curso=curso, status=CompraStatus.COMPLETED
        ).exists():
            raise serializers.ValidationError("Você precisa comprar o curso antes de avaliar")
        
        # Impede duplicidade (create/update)
        if Avaliacao.objects.filter(
            usuario=usuario, 
            curso=curso
        ).exclude(
            id=self.instance.id if self.instance else None
        ).exists():
            raise serializers.ValidationError("Você ja avaliou esse curso.")
        
        # Define usuario automaticamente
        data['usuario'] = usuario
        return data
    
# Serializer => Compra
class CompraSerializer(serializers.ModelSerializer):

    class Meta:
        model = Compra
        fields = ['id', 'usuario', 'curso', 'preco', 'status']
        # Campos sensiveis controlados por backend
        read_only_fields = ['id', 'data', 'usuario', 'preco', 'status']

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Usuário não identificado.")
        
        usuario = request.user
        curso = validated_data['curso']

        # Cria compra com dados seguros
        return Compra.objects.create(
            usuario=usuario,
            curso=curso,
            preco=curso.preco
        )
    
# Serializer => CompraStatus (choices)
class CompraStatusSerializer(serializers.Serializer):
    # Retorna todos os status disponiveis
    status = serializers.ChoiceField(choices=CompraStatus.choices)