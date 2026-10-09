from celery import shared_task

from apps.ai.services.indexing import index_card


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def embed_card(self, card_id):
    try:
        return index_card(card_id)
    except Exception as exc:
        raise self.retry(exc=exc)
