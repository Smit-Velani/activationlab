import logging
from celery import shared_task
from django.db import transaction
from .models import Job
from .services import execute
logger=logging.getLogger(__name__)
@shared_task(bind=True, autoretry_for=(RuntimeError,), retry_backoff=True, retry_jitter=True, max_retries=3)
def run_job(self, job_id):
    with transaction.atomic():
        job=Job.objects.select_for_update().get(id=job_id)
        if job.status == Job.Status.SUCCEEDED:
            return job.result
        job.status=Job.Status.RUNNING
        job.attempts += 1
        job.error=""
        job.save(update_fields=["status","attempts","error","updated_at"])
    try:
        result=execute(job.operation, job.payload)
        Job.objects.filter(id=job_id).update(status=Job.Status.SUCCEEDED, result=result, error="")
        logger.info("job_succeeded", extra={"job_id": str(job_id)})
        return result
    except ValueError as exc:
        Job.objects.filter(id=job_id).update(status=Job.Status.FAILED, error=str(exc))
        logger.warning("job_failed", extra={"job_id": str(job_id), "error": str(exc)})
        return {"error": str(exc)}
    except Exception as exc:
        Job.objects.filter(id=job_id).update(status=Job.Status.QUEUED, error=str(exc))
        raise RuntimeError(str(exc)) from exc
