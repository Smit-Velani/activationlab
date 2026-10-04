import pytest
from rest_framework.test import APIClient

from .models import Job
from .services import execute
from .tasks import run_job


@pytest.mark.django_db
def test_health():
    response = APIClient().get("/api/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.django_db
def test_idempotency(monkeypatch):
    monkeypatch.setattr("jobs.views.run_job.delay", lambda *_: None)

    client = APIClient()
    headers = {"HTTP_IDEMPOTENCY_KEY": "same-request"}

    first = client.post(
        "/api/jobs/",
        {"operation": "echo", "payload": {"x": 1}},
        format="json",
        **headers,
    )

    second = client.post(
        "/api/jobs/",
        {"operation": "echo", "payload": {"x": 999}},
        format="json",
        **headers,
    )

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["payload"] == {"x": 1}
    assert Job.objects.count() == 1


def test_execute_echo():
    result = execute("echo", {"message": "hello"})
    assert result == {"echo": {"message": "hello"}}


def test_execute_sum():
    result = execute("sum", {"values": [10, 20, 30]})
    assert result == {"sum": 60, "count": 3}


def test_execute_normalize():
    result = execute("normalize", {"text": "  HELLO    ActivationLab  "})
    assert result == {"text": "hello activationlab"}


def test_execute_sum_rejects_invalid_values():
    with pytest.raises(ValueError, match="numeric list"):
        execute("sum", {"values": [10, "invalid", 20]})


@pytest.mark.django_db(transaction=True)
def test_run_job_success():
    job = Job.objects.create(
        idempotency_key="task-success",
        operation="sum",
        payload={"values": [5, 10, 15]},
    )

    result = run_job.run(str(job.id))

    job.refresh_from_db()

    assert result == {"sum": 30, "count": 3}
    assert job.status == Job.Status.SUCCEEDED
    assert job.result == {"sum": 30, "count": 3}
    assert job.attempts == 1
    assert job.error == ""


@pytest.mark.django_db(transaction=True)
def test_run_job_permanent_failure():
    job = Job.objects.create(
        idempotency_key="task-failure",
        operation="sum",
        payload={"values": ["invalid", 10]},
    )

    result = run_job.run(str(job.id))

    job.refresh_from_db()

    assert job.status == Job.Status.FAILED
    assert job.attempts == 1
    assert job.error == "payload.values must be a numeric list"
    assert result == {"error": "payload.values must be a numeric list"}


@pytest.mark.django_db(transaction=True)
def test_transient_failure_requests_retry(monkeypatch):
    job = Job.objects.create(
        idempotency_key="task-retry",
        operation="echo",
        payload={"message": "retry-test"},
    )

    def transient_failure(*args, **kwargs):
        raise ConnectionError("temporary dependency failure")

    monkeypatch.setattr("jobs.tasks.execute", transient_failure)

    with pytest.raises(RuntimeError, match="temporary dependency failure"):
        run_job.run(str(job.id))

    job.refresh_from_db()

    assert job.status == Job.Status.QUEUED
    assert job.attempts == 1
    assert job.error == "temporary dependency failure"
