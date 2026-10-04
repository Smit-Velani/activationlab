import uuid
from django.db import migrations, models
class Migration(migrations.Migration):
    initial=True
    dependencies=[]
    operations=[migrations.CreateModel(name="Job",fields=[("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),("idempotency_key",models.CharField(max_length=128,unique=True)),("operation",models.CharField(max_length=64)),("payload",models.JSONField(default=dict)),("result",models.JSONField(blank=True,null=True)),("status",models.CharField(choices=[("queued","Queued"),("running","Running"),("succeeded","Succeeded"),("failed","Failed")],default="queued",max_length=16)),("attempts",models.PositiveIntegerField(default=0)),("error",models.TextField(blank=True)),("created_at",models.DateTimeField(auto_now_add=True)),("updated_at",models.DateTimeField(auto_now=True))])]
