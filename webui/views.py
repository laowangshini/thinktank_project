# thinktank_project/webui/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseNotAllowed
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
from django.utils import timezone
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt 
from django.contrib.auth.decorators import login_required
from .models import CrawlTaskProgress
import subprocess
import threading
import os
import json

from articles.models import Article, Digest
from thinktanks.models import ThinkTank
from crawlers.models import CrawlTask
from users.models import User # 如果需要用户信息


def get_crawl_progress(request):
    progress_obj = CrawlTaskProgress.objects.filter(task_name='run_all').first()
    if progress_obj:
        return JsonResponse({
            'status': progress_obj.status,
            'progress': progress_obj.progress,
            'updated_at': progress_obj.updated_at.isoformat()
        })
    else:
        return JsonResponse({'status': 'idle', 'progress': 0})
    
def index_view(request):
    """首页 - 文章列表"""
    # 获取最新文章
    articles = Article.objects.select_related('thinktank').prefetch_related('digest').order_by('-crawl_date')[:50]
    # 获取统计信息
    total_articles = Article.objects.count()
    total_thinktanks = ThinkTank.objects.count()
    total_tasks = CrawlTask.objects.count()
    active_tasks = CrawlTask.objects.filter(is_active=True).count()

    stats = {
        'total_articles': total_articles,
        'total_thinktanks': total_thinktanks,
        'total_tasks': total_tasks,
        'active_tasks': active_tasks
    }

    return render(request, 'index.html', {'articles': articles, 'stats': stats})



def articles_view(request):
    page = request.GET.get('page', 1)
    per_page = 20

    # 获取筛选参数
    thinktank_id = request.GET.get('thinktank')

    # 基础查询集
    articles_list = Article.objects.select_related('thinktank').order_by('-crawl_date')

    # 如果有智库 ID，进行过滤
    if thinktank_id:
        try:
            thinktank_id = int(thinktank_id)
            articles_list = articles_list.filter(thinktank_id=thinktank_id)
        except (ValueError, TypeError):
            pass  # 忽略无效 ID

    paginator = Paginator(articles_list, per_page)

    try:
        articles_page = paginator.page(page)
    except PageNotAnInteger:
        articles_page = paginator.page(1)
    except EmptyPage:
        articles_page = paginator.page(paginator.num_pages)

    # 计算分页窗口 (例如，显示当前页前后各2页)
    current_page = articles_page.number
    total_pages = paginator.num_pages
    # page_range = list(range(max(1, current_page - 2), min(total_pages, current_page + 2) + 1))
    # 添加省略号逻辑 (可选，更复杂)
    # ... (省略具体实现，可在视图中处理)

    # 计算总数
    total_articles = articles_list.count() # 或 paginator.count

    context = {
        'articles': articles_page,
        # 'page_range_to_show': page_range, # 如果你计算了页码范围
        'pagination': {
            'total': total_articles,
            'total_pages': total_pages,
            # ... 其他需要的 pagination 信息
        }
    }
    return render(request, 'articles.html', context)


def article_detail_view(request, article_id):
    """文章详情页"""
    article = get_object_or_404(Article, id=article_id)
    
    # 增加浏览次数
    article.view_count = (article.view_count or 0) + 1
    article.save(update_fields=['view_count'])

    # 修改点4: 使用完整的模板路径
    return render(request, 'article_detail.html', {'article': article})
    

def thinktanks_view(request):
    """智库列表页"""
    # 获取所有智库
    thinktanks = ThinkTank.objects.order_by('name')

    # 为每个智库统计文章数量和任务数量
    # 使用 annotate 进行聚合查询，效率更高
    thinktank_stats = ThinkTank.objects.annotate(
        article_count=Count('article', distinct=True),
        task_count=Count('crawltask', distinct=True),
        active_task_count=Count('crawltask', filter=Q(crawltask__is_active=True))
    ).order_by('name')

    total_articles_agg = Article.objects.aggregate(total=Count('id'))
    # 计算所有任务总数和活跃任务总数
    total_tasks_agg = CrawlTask.objects.aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(is_active=True))
    )
    # 计算活跃智库数量
    active_thinktanks_count = ThinkTank.objects.filter(is_active=True).count()

    # 构造传递给模板的 stats_summary 字典
    stats_summary = {
        'total_articles': total_articles_agg['total'],
        'total_active_tasks': total_tasks_agg['active'],
        'total_tasks': total_tasks_agg['total'],
        'active_thinktanks_count': active_thinktanks_count,
    }

    # 将 stats_summary 也传递给模板上下文
    return render(request, 'thinktanks.html', {
        'thinktank_stats': thinktank_stats,
        'stats_summary': stats_summary 
    })


def thinktank_detail_view(request, thinktank_id):
    """智库详情页"""
    thinktank = get_object_or_404(ThinkTank, id=thinktank_id)
    
    # 获取该智库的文章 (最新20篇)
    articles = Article.objects.filter(thinktank=thinktank).select_related('thinktank').order_by('-crawl_date')[:20]
    
    # 获取该智库的任务
    tasks = CrawlTask.objects.filter(thinktank=thinktank)

    return render(request, 'thinktank_detail.html', {
        'thinktank': thinktank,
        'articles': articles,
        'tasks': tasks
    })


def admin_view(request):
    """管理后台首页"""
    # 获取所有任务，按智库和任务名排序
    tasks = CrawlTask.objects.select_related('thinktank').order_by('thinktank__name', 'task_name')
    return render(request, 'admin.html', {'tasks': tasks})


@require_http_methods(["POST"]) # 限制只接受 POST 请求
@csrf_exempt # 如果前端没有传递 CSRF token，需要豁免。更好的做法是在模板中包含 {% csrf_token %} 并通过 JS 传递
def toggle_task_view(request, task_id):
    """切换任务的激活状态"""
    task = get_object_or_404(CrawlTask, id=task_id)
    
    task.is_active = not task.is_active
    task.save(update_fields=['is_active']) # 只更新 is_active 字段

    status = "激活" if task.is_active else "禁用"
    messages.success(request, f'任务 "{task.task_name}" 已{status}')

    # 返回 JSON 响应
    return JsonResponse({'success': True, 'is_active': task.is_active})


def _run_crawler_subprocess(command_args):
    """在后台线程中运行爬虫子进程的辅助函数"""
    try:
        # 确保在项目根目录下运行命令
        project_root = settings.BASE_DIR
        result = subprocess.run(
            command_args,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )

        if result.returncode == 0:
            print(f"爬虫命令执行成功: {' '.join(command_args)}")
            print(result.stdout)
        else:
            print(f"爬虫命令执行失败: {' '.join(command_args)}")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print(f"爬虫命令执行超时: {' '.join(command_args)}")
    except Exception as e:
        print(f"爬虫命令执行异常: {' '.join(command_args)}, 错误: {e}")


@require_http_methods(["POST"])
def run_task_view(request, task_id):
    """手动运行单个任务 - 使用自定义爬虫脚本"""
    task = get_object_or_404(CrawlTask, id=task_id)
    
    # 构建调用你自定义爬虫脚本的命令
    # 假设你的脚本叫 custom_crawler.py，放在项目根目录
    script_path = os.path.join(settings.BASE_DIR, 'custom_crawler.py')
    
    # 可选：传递任务名称作为参数
    command_args = [
        sys.executable,  # 使用当前 Python 解释器
        script_path,
        '--thinktank', task.thinktank.name  # 只爬取该智库
    ]

    # 在后台线程中运行任务
    thread = threading.Thread(target=_run_custom_crawler_subprocess, args=(command_args,))
    thread.daemon = True
    thread.start()

    messages.info(request, f'任务 "{task.task_name}" 已提交后台执行（使用自定义爬虫）。')
    return JsonResponse({'success': True, 'message': '任务已提交执行'})


def _run_custom_crawler_subprocess(command_args):
    """在后台线程中运行自定义爬虫脚本的辅助函数"""
    try:
        # 确保在项目根目录下运行命令
        project_root = settings.BASE_DIR
        result = subprocess.run(
            command_args,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )

        if result.returncode == 0:
            print(f"自定义爬虫执行成功: {' '.join(command_args)}")
            print(result.stdout)
        else:
            print(f"自定义爬虫执行失败: {' '.join(command_args)}")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print(f"自定义爬虫执行超时: {' '.join(command_args)}")
    except Exception as e:
        print(f"自定义爬虫执行异常: {' '.join(command_args)}, 错误: {e}")

def _run_crawlers_in_background():
    try:
        # 步骤1: 运行 main.py
        CrawlTaskProgress.objects.update_or_create(
            task_name='run_all', defaults={'status': 'running ./proj released/main.py', 'progress': 10}
        )
        main_path = os.path.join(settings.BASE_DIR, './proj released/main.py')
        subprocess.run([sys.executable, main_path], cwd=settings.BASE_DIR, check=True)

        # 步骤2: 运行 内页爬取_完整版.py
        CrawlTaskProgress.objects.update_or_create(
            task_name='run_all', defaults={'status': 'running ./proj released/内页爬取', 'progress': 50}
        )
        crawler_path = os.path.join(settings.BASE_DIR, './proj released/内页爬取_完整版.py')
        subprocess.run([sys.executable, crawler_path], cwd=settings.BASE_DIR, check=True)

        # 完成
        CrawlTaskProgress.objects.update_or_create(
            task_name='run_all', defaults={'status': 'completed', 'progress': 100}
        )
    except Exception as e:
        CrawlTaskProgress.objects.update_or_create(
            task_name='run_all', defaults={'status': f'failed: {str(e)}', 'progress': 0}
        )

@require_http_methods(["POST"])
def run_all_tasks_view(request):
    # 启动后台线程
    print(">>> run_all_tasks_view 被调用了！")
    thread = threading.Thread(target=_run_crawlers_in_background)
    thread.daemon = True
    thread.start()

    return JsonResponse({'success': True, 'message': '任务已启动，请查看进度'})

def digest_detail_view(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    
    try:
        digest = article.digest # 假设 related_name 是 'digest'
    except Digest.DoesNotExist:
        digest = None # 如果不存在，digest 为 None

    compression_ratio = 0.0

    if digest and article.content: 
        summary_len = len(digest.digest_summary) 
        content_len = len(article.content)
        if content_len > 0:
            compression_ratio = (summary_len / content_len) * 100
            
    return render(request, 'digest_detail.html', {
        'article': article,
        'digest': digest,
        'compression_ratio': compression_ratio
    })


def digest_edit_view(request, article_id):
    """编辑文章摘编"""
    article = get_object_or_404(Article, id=article_id)
    
    # ✅ 终极修复：用 editor_id 避免 SimpleLazyObject 问题
    digest, created = Digest.objects.get_or_create(article=article, defaults={
        'editor_id': request.user.pk if request.user.is_authenticated else None,  # ← 关键！用 _id
        'digest_summary': '',
        'key_points': '',
        'editor_notes': ''
    })

    if request.method == 'POST':
        digest_summary = request.POST.get('digest_summary', '').strip()
        key_points = request.POST.get('key_points', '').strip()
        editor_notes = request.POST.get('editor_notes', '').strip()

        if not digest_summary:
            messages.error(request, '摘要内容不能为空')
            return render(request, 'digest_edit.html', {'article': article, 'digest': digest})

        # 更新摘编内容
        digest.digest_summary = digest_summary
        digest.key_points = key_points
        digest.editor_notes = editor_notes
        digest.updated_at = timezone.now()
        
        if request.user.is_authenticated:
            # 从数据库获取真实 User 实例
            from django.contrib.auth import get_user_model
            User = get_user_model()
            digest.editor = User.objects.get(pk=request.user.pk)

        digest.save()

        # 标记文章为已处理
        article.is_processed = True
        article.save(update_fields=['is_processed'])

        messages.success(request, '摘编保存成功')
        return redirect('webui:digest_detail', article_id=article.id)

    # GET 请求：显示编辑表单
    return render(request, 'digest_edit.html', {'article': article, 'digest': digest})


def batch_select_view(request):
    """批量选择文章界面"""
    # 获取筛选参数
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    thinktank_id = request.GET.get('thinktank')

    # 基础查询
    articles_list = Article.objects.select_related('thinktank').order_by('-crawl_date')

    # 应用筛选
    if start_date:
        articles_list = articles_list.filter(publish_date__gte=start_date)
    if end_date:
        articles_list = articles_list.filter(publish_date__lte=end_date)
    if thinktank_id:
        try:
            thinktank_id = int(thinktank_id)
            articles_list = articles_list.filter(thinktank_id=thinktank_id)
        except (ValueError, TypeError):
            pass

    # 分页
    paginator = Paginator(articles_list, 20)
    page = request.GET.get('page', 1)
    try:
        articles_page = paginator.page(page)
    except PageNotAnInteger:
        articles_page = paginator.page(1)
    except EmptyPage:
        articles_page = paginator.page(paginator.num_pages)

    # 获取所有智库用于筛选
    thinktanks = ThinkTank.objects.all()

    context = {
        'articles': articles_page,
        'pagination': {
            'total': articles_list.count(),
            'total_pages': paginator.num_pages,
        },
        'thinktanks': thinktanks,
        'current_filters': {
            'start_date': start_date,
            'end_date': end_date,
            'thinktank_id': thinktank_id,
        }
    }
    return render(request, 'batch_select.html', context)


def batch_digest_view(request):
    """批量摘编界面"""
    article_ids = request.GET.get('article_ids', '')
    if not article_ids:
        messages.error(request, '未选择任何文章')
        return redirect('webui:batch_select')

    # 解析文章ID
    try:
        ids = [int(x) for x in article_ids.split(',') if x.isdigit()]
        articles = Article.objects.filter(id__in=ids).select_related('thinktank').order_by('id')
    except ValueError:
        messages.error(request, '文章ID格式错误')
        return redirect('webui:batch_select')

    # 获取对应的摘编对象
    digests = []
    for article in articles:
        digest, created = Digest.objects.get_or_create(
            article=article,
            defaults={
                'editor_id': request.user.pk if request.user.is_authenticated else None,
                'digest_summary': '',
                'key_points': '',
                'editor_notes': ''
            }
        )
        digests.append({
            'article': article,
            'digest': digest
        })

    context = {
        'digests': digests,
        'selected_count': len(articles)
    }
    return render(request, 'batch_digest.html', context)

    

def search_view(request):
    """搜索功能"""
    query = request.GET.get('q', '').strip()
    
    articles = []
    if query:
        # 在标题中搜索
        articles = Article.objects.filter(title__icontains=query).select_related('thinktank').order_by('-crawl_date')[:50]
        if not articles:
             messages.info(request, f'未找到标题包含 "{query}" 的文章。')

    return render(request, 'search.html', {'articles': articles, 'query': query})
