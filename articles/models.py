from django.db import models

class Article(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('report', 'Report'),
        ('article', 'Article'),
        ('blog', 'Blog'),
        ('press_release', 'Press Release'),
    ]

    title = models.CharField(max_length=255)
    url = models.URLField(max_length=255, unique=True)
    content = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    author = models.CharField(max_length=100, blank=True, null=True)
    publish_date = models.DateField(blank=True, null=True)
    crawl_date = models.DateTimeField(blank=True, null=True)
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPE_CHOICES, blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, null=True)  # 可考虑用 Taggit
    view_count = models.IntegerField(default=0)
    is_processed = models.BooleanField(default=False)
    thinktank = models.ForeignKey('thinktanks.ThinkTank', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    @property
    def is_fully_processed(self):
        """
        判断文章是否真正被摘编。
        只有当关联的 Digest 存在，并且其摘要、关键要点、编辑备注中至少有一项非空时，
        才认为是已摘编。
        """
        try:
            digest = self.digest  # 假设 related_name='digest'
            # 检查三个字段是否都为空或 None
            if digest.digest_summary or digest.key_points or digest.editor_notes:
                return True
            else:
                return False
        except Digest.DoesNotExist:
            # 如果没有关联的 Digest，则未摘编
            return False

    class Meta:
        db_table = 'articles'




class Attachment(models.Model):
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('doc', 'DOC'),
        ('ppt', 'PPT'),
        ('xlsx', 'Excel'),
        ('image', 'Image'),
    ]

    DOWNLOAD_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    filename = models.CharField(max_length=255)
    original_url = models.URLField(max_length=500)
    local_path = models.CharField(max_length=500, blank=True, null=True)
    file_type = models.CharField(max_length=50, choices=FILE_TYPE_CHOICES)
    file_size = models.IntegerField(blank=True, null=True)  # 字节
    download_status = models.CharField(max_length=20, choices=DOWNLOAD_STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    downloaded_at = models.DateTimeField(blank=True, null=True)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)

    def __str__(self):
        return self.filename

    class Meta:
        db_table = 'attachments'

from django.contrib.auth.models import User

class Digest(models.Model):
    digest_summary = models.TextField()
    key_points = models.TextField(blank=True, null=True)
    editor_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    article = models.OneToOneField(
        Article, 
        on_delete=models.CASCADE, 
        related_name='digest'
    )
    editor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    @property
    def is_fully_filled(self):
        """判断摘编内容是否真正填写（非空且非空白）"""
        fields = [self.digest_summary, self.key_points, self.editor_notes]
        for field in fields:
            if field and field.strip():  # 检查字段是否存在且去除空白后非空
                return True
        return False
        
    def __str__(self):
        return f"Digest: {self.article.title}"

    class Meta:
        db_table = 'digests'