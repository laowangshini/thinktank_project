# thinktank_project/webui/urls.py
from django.urls import path
from . import views

app_name = 'webui'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('articles/', views.articles_view, name='articles'),
    path('article/<int:article_id>/', views.article_detail_view, name='article_detail'),
    path('thinktanks/', views.thinktanks_view, name='thinktanks'),
    path('thinktank/<int:thinktank_id>/', views.thinktank_detail_view, name='thinktank_detail'),
    path('tasks/', views.admin_view, name='tasks'), 
    path('admin/task/<int:task_id>/toggle/', views.toggle_task_view, name='toggle_task'),
    path('admin/run_task/<int:task_id>/', views.run_task_view, name='run_task'),
    path('admin/run_all_tasks/', views.run_all_tasks_view, name='run_all_tasks'),
    path('digest/<int:article_id>/', views.digest_detail_view, name='digest_detail'),
    path('digest/<int:article_id>/edit/', views.digest_edit_view, name='digest_edit'),
    path('search/', views.search_view, name='search'),
    path('batch-select/', views.batch_select_view, name='batch_select'),
    path('batch-digest/', views.batch_digest_view, name='batch_digest'),
    path('admin/crawl-progress/', views.get_crawl_progress, name='crawl_progress'),
]