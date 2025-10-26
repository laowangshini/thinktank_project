# articles/admin.py

from django.contrib import admin
from .models import Article, Attachment, Digest
from thinktanks.models import ThinkTank  # ← ThinkTank 在 thinktanks 应用里！

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'url', 'publish_date', 'crawl_date', 'thinktank', 'is_processed']
    list_filter = ['publish_date', 'crawl_date', 'thinktank']
    search_fields = ['title', 'author', 'content']
    readonly_fields = ['crawl_date', 'view_count']

@admin.register(ThinkTank)
class ThinkTankAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Digest)
class DigestAdmin(admin.ModelAdmin):
    list_display = ['article', 'created_at', 'editor']
    search_fields = ['article__title']

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'article', 'file_type', 'download_status']
    search_fields = ['filename', 'article__title']