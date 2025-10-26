from django.db import models

class CrawlTask(models.Model):
    SCHEDULE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('manual', 'Manual'),
    ]

    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('running', 'Running'),
    ]

    task_name = models.CharField(max_length=100)
    start_url = models.URLField(max_length=500)
    crawler_type = models.CharField(max_length=50)
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_CHOICES, blank=True, null=True)
    schedule_time = models.CharField(max_length=10, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(blank=True, null=True)
    last_run_status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True, null=True)
    last_run_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    crawler_config = models.TextField(blank=True, null=True)  # JSON 格式
    thinktank = models.ForeignKey('thinktanks.ThinkTank', on_delete=models.CASCADE)

    def __str__(self):
        return self.task_name

    class Meta:
        db_table = 'crawl_tasks'