import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "terra360.settings.base")  # adapte si besoin
app = Celery("terra360")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()