from django.contrib import admin
from .models import Curso, Avaliacao, Compra, Usuario

# Inlines
class AvaliacaoInline(admin.TabularInline):
    model = Avaliacao
    extra = 0
    readonly_fields = ('usuario', 'nota', 'comentario', 'criacao', 'atualizacao')
    can_delete = False

class CompraInline(admin.TabularInline):
    model = Compra
    extra = 0
    readonly_fields = ('usuario', 'curso', 'preco', 'status', 'criacao', 'atualizacao')
    can_delete = False

class CursoInline(admin.TabularInline):
    model = Curso
    extra = 0
    readonly_fields = ('nome', 'preco', 'ativo', 'criacao')
    can_delete = False
    
# Ações customizadas
@admin.action(description='Marcar como Concluído')
def marcar_concluido(modeladmin, request, queryset):
    queryset.update(status='completed')

@admin.action(description='Marcar como Reembolsado')
def marcar_reembolsado(modeladmin, request, queryset):
    queryset.update(status='refunded')

# Admin Curso
@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'criado_por', 'preco', 'total_vendas', 'media_avaliacoes', 'qtd_avaliacoes', 'ativo', 'criacao')
    list_filter = ('ativo',)
    search_fields = ('nome', 'descricao', 'criado_por__email')
    ordering = ('-criacao',)
    readonly_fields = ('total_vendas', 'media_avaliacoes', 'criacao', 'atualizacao')
    inlines = [AvaliacaoInline]

    def qtd_avaliacoes(self, obj):
        return obj.avaliacoes.count()
    qtd_avaliacoes.short_description = 'Avaliações'

# Admin Avaliacao
@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'curso', 'nota', 'comentario', 'ativo', 'criacao')
    list_filter = ('nota', 'ativo')
    search_fields = ('usuario__email', 'curso__nome', 'comentario')
    ordering = ('-criacao',)
    readonly_fields = ('criacao', 'atualizacao')

# Admin Compra
@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'curso', 'preco', 'status', 'ativo', 'criacao')
    list_filter = ('status', 'ativo')
    search_fields = ('usuario__email', 'curso__nome')
    ordering = ('-criacao',)
    readonly_fields = ('criacao', 'atualizacao')
    actions = [marcar_concluido, marcar_reembolsado]

# Admin Usuario
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'is_staff', 'is_active', 'ativo', 'criacao')
    list_filter = ('is_staff', 'is_active', 'ativo')
    search_fields = ('username', 'email')
    ordering = ('-criacao',)
    readonly_fields = ('criacao', 'atualizacao')
    inlines = [CursoInline, CompraInline]