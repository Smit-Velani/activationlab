from rest_framework import serializers
from .models import Job
class JobCreateSerializer(serializers.Serializer):
    operation=serializers.ChoiceField(choices=["sum","normalize","echo"])
    payload=serializers.JSONField()
class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model=Job
        fields=["id","idempotency_key","operation","payload","result","status","attempts","error","created_at","updated_at"]
