from django.db import models

class ThinkTank(models.Model):
    name = models.CharField(max_length=100, unique=True)
    url = models.URLField(max_length=255)
    description = models.TextField(blank=True, null=True)
    logo_path = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'thinktanks'