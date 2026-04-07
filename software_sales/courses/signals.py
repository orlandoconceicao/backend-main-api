from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.db.models import F
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Compra, Avaliacao, Curso, CompraStatus


# Guarda status antigo
@receiver(pre_save, sender=Compra)
def guardar_status_anterior(sender, instance, **kwargs):
    if instance.pk:
        instance._status_anterior = sender.objects.get(pk=instance.pk).status
    else:
        instance._status_anterior = None

# Atualiza vendas + email
@receiver(post_save, sender=Compra)
def compra_post_save(sender, instance, created, **kwargs):
    status_anterior = getattr(instance, '_status_anterior', None)

    if instance.status == CompraStatus.COMPLETED and status_anterior != CompraStatus.COMPLETED:
        Curso.objects.filter(pk=instance.curso.pk).update(
            total_vendas=F('total_vendas') + 1
        )

        send_mail(
            subject='Compra concluída!',
            message=f'Curso "{instance.curso.nome}" comprado com sucesso!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.usuario.email],
            fail_silently=True
        )

    if instance.status == CompraStatus.REFUNDED and status_anterior == CompraStatus.COMPLETED:
        Curso.objects.filter(pk=instance.curso.pk).update(
            total_vendas=F('total_vendas') - 1
        )

# média avaliações
@receiver(post_save, sender=Avaliacao)
@receiver(post_delete, sender=Avaliacao)
def atualizar_media(sender, instance, **kwargs):
    media = instance.curso.avaliacoes.aggregate(
        media=models.Avg('nota')
    )['media'] or Decimal('0.00')

    instance.curso.media_avaliacoes = Decimal(media).quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP
    )

    instance.curso.save(update_fields=['media_avaliacoes'])