from django.db import IntegrityError, transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Job
from .serializers import JobCreateSerializer, JobSerializer
from .tasks import run_job
@api_view(["GET"])
def health(request):
    return Response({"status":"ok","service":"activationlab-api"})
@api_view(["POST"])
def create_job(request):
    serializer=JobCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    key=request.headers.get("Idempotency-Key")
    if not key:
        return Response({"detail":"Idempotency-Key header is required"}, status=400)
    try:
        with transaction.atomic():
            job, created=Job.objects.get_or_create(idempotency_key=key, defaults=serializer.validated_data)
    except IntegrityError:
        job=Job.objects.get(idempotency_key=key); created=False
    if created:
        run_job.delay(str(job.id))
    return Response(JobSerializer(job).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
@api_view(["GET"])
def get_job(request, job_id):
    try: job=Job.objects.get(id=job_id)
    except Job.DoesNotExist: return Response({"detail":"Not found"}, status=404)
    return Response(JobSerializer(job).data)
