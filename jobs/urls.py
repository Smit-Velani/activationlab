from django.urls import path
from . import views
urlpatterns=[path("health/",views.health),path("jobs/",views.create_job),path("jobs/<uuid:job_id>/",views.get_job)]
