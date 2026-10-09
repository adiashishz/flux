from django.core.management.base import BaseCommand

from apps.ai.services.indexing import EMBEDDED, index_card
from apps.workspace.models import Card


class Command(BaseCommand):
    help = "Embed every card that is missing an up to date embedding (runs in process)."

    def handle(self, *args, **options):
        counts = {}
        for card_id in Card.objects.values_list("id", flat=True):
            outcome = index_card(card_id)
            counts[outcome] = counts.get(outcome, 0) + 1
        self.stdout.write(self.style.SUCCESS(f"Embedded {counts.get(EMBEDDED, 0)} cards: {counts}"))
