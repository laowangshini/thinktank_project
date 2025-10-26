# webui/models.py
from django.db import models

class CrawlTaskProgress(models.Model):
    task_name = models.CharField(max_length=100, unique=True)  # 如 'run_all'
    status = models.CharField(max_length=200)
    progress = models.IntegerField(default=0)  # 0-100
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.task_name}: {self.progress}%"