import logging

from celery import shared_task

from apps.ai.models import AssistantRun
from apps.ai.services.indexing import index_card
from apps.ai.services.llm import LLMError
from apps.ai.services.planning import PlanError, execute_plan

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def embed_card(self, card_id):
    try:
        return index_card(card_id)
    except Exception as exc:
        raise self.retry(exc=exc)


def _finish(run_id, **fields):
    # Conditional update: a run that was already timed out is never overwritten.
    return AssistantRun.objects.filter(id=run_id, status=AssistantRun.RUNNING).update(**fields)


@shared_task
def run_plan_week(run_id):
    claimed = AssistantRun.objects.filter(id=run_id, status=AssistantRun.QUEUED).update(status=AssistantRun.RUNNING)
    if not claimed:
        return "skipped"

    run = AssistantRun.objects.get(id=run_id)
    try:
        execute_plan(run)
    except (PlanError, LLMError) as exc:
        _finish(run_id, status=AssistantRun.FAILED, error_message=str(exc)[:300], steps=run.steps,
                input_tokens=run.input_tokens, output_tokens=run.output_tokens)
        return "failed"
    except Exception:
        logger.exception("Plan run %s crashed", run_id)
        _finish(run_id, status=AssistantRun.FAILED, error_message="Planning failed unexpectedly.", steps=run.steps,
                input_tokens=run.input_tokens, output_tokens=run.output_tokens)
        return "crashed"

    _finish(run_id, status=AssistantRun.SUCCEEDED, result=run.result, steps=run.steps,
            input_tokens=run.input_tokens, output_tokens=run.output_tokens)
    return "succeeded"
