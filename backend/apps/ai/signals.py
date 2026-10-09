import logging

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.ai.tasks import embed_card
from apps.workspace.models import Card

logger = logging.getLogger(__name__)

TEXT_FIELDS = {"title", "description", "content_markdown"}


@receiver(post_save, sender=Card)
def enqueue_embedding(sender, instance, update_fields, **kwargs):
    if not settings.AI_EMBEDDINGS_ENABLED:
        return
    if update_fields is not None and not TEXT_FIELDS & set(update_fields):
        return

    card_id = str(instance.id)
    # robust=True: a down broker is logged and never fails the card save
    transaction.on_commit(lambda: embed_card.delay(card_id), robust=True)
