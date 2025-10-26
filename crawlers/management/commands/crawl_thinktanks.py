# thinktank_project/crawlers/management/commands/crawl_thinktanks.py
from django.core.management.base import BaseCommand
# import sys
# import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from datetime import datetime
from django.conf import settings
from django.db import transaction
from django.utils import timezone


# 导入 Django 模型
from thinktanks.models import ThinkTank
from crawlers.models import CrawlTask
from articles.models import Article

from crawlers.utils.browser_renderer import ChromePageRender, Options

def clean_text(text):
    """清理文本内容，去除多余空白字符"""
    if text:
        # 去除多余的空白字符，保留段落结构
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    return ''
    
class Command(BaseCommand):
    help = '运行智库内容爬虫'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task-id',
            type=int,
            help='运行指定 ID 的爬虫任务',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='运行所有激活的爬虫任务 (默认行为)',
        )

    def handle(self, *args, **options):
        task_id = options.get('task_id')
        run_all = options.get('all') or (task_id is None)

        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        self.stdout.write("=" * 60)
        self.stdout.write("智库内容管理系统 - Django 爬虫")
        self.stdout.write(f"开始时间: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write("=" * 60)

        try:
            if task_id:
                task = CrawlTask.objects.filter(id=task_id).first()
                if not task:
                    self.stdout.write(self.style.ERROR(f"[错误] 未找到任务ID为 {task_id} 的任务"))
                    return
                if not task.is_active:
                    self.stdout.write(self.style.WARNING(f"[跳过] 任务 {task.task_name} 未激活，跳过"))
                    return
                self._crawl_single_task(task)
            elif run_all:
                active_tasks = CrawlTask.objects.filter(is_active=True)
                if not active_tasks.exists():
                    self.stdout.write(self.style.ERROR("[错误] 没有找到激活的爬取任务"))
                    return
                self.stdout.write(f"[信息] 找到 {active_tasks.count()} 个激活的爬取任务")

                success_count = 0
                failed_count = 0
                total_saved = 0

                for i, task in enumerate(active_tasks, 1):
                    self.stdout.write(f"\n{'='*40}")
                    self.stdout.write(f"进度: [{i}/{active_tasks.count()}]")
                    self.stdout.write(f"{'='*40}")

                    try:
                        saved_count = self._crawl_single_task(task)
                        success_count += 1
                        total_saved += saved_count
                        # 更新任务状态 (在 _crawl_single_task 内部已更新)
                    except Exception as e:
                        failed_count += 1
                        self.stdout.write(self.style.ERROR(f"[失败] 任务 {task.task_name} 执行失败: {e}"))
                        task.last_run = timezone.now()
                        task.last_run_status = 'failed'
                        task.last_run_message = f'执行失败: {str(e)}'
                        task.save(update_fields=['last_run', 'last_run_status', 'last_run_message'])

                self.stdout.write(f"\n{'='*60}")
                self.stdout.write("所有任务执行完毕")
                self.stdout.write(f"[成功] 成功: {success_count} 个任务")
                self.stdout.write(f"[失败] 失败: {failed_count} 个任务")
                self.stdout.write(f"[统计] 总共保存: {total_saved} 篇新文章")
                self.stdout.write(f"结束时间: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.stdout.write("=" * 60)
            else:
                self.stdout.write(self.style.ERROR("无效的参数组合"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[异常] 爬虫执行异常: {e}"))
            raise


    def _crawl_single_task(self, task):
        """爬取单个任务"""
        self.stdout.write(f"[执行] 执行任务: {task.task_name}")
        self.stdout.write(f"[智库] 智库: {task.thinktank.name}")
        self.stdout.write(f"[URL] URL: {task.start_url}")

        # 更新任务状态为运行中
        task.last_run = timezone.now()
        task.last_run_status = 'running'
        task.last_run_message = '任务正在执行中...'
        task.save(update_fields=['last_run', 'last_run_status', 'last_run_message'])

        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_driver_filepath = None
            use_undetected = True
            with ChromePageRender(
                chrome_driver_filepath=chrome_driver_filepath,
                options=chrome_options,
                use_undetected_chromedriver=use_undetected
            ) as browser:
                self.stdout.write("[网络] 正在获取页面内容 (使用浏览器)...")

                # --- 获取爬虫配置 ---
                import json
                try:
                    config_data = json.loads(task.crawler_config)
                    urls_to_crawl = config_data.get('urls', [task.start_url])
                    crawler_settings = config_data.get('config', {})
                    selectors_to_wait = crawler_settings.get('selectors', [])
                    waiting_timeout = crawler_settings.get('waiting_timeout', 10) # 默认10秒
                except (json.JSONDecodeError, TypeError):
                    self.stdout.write(self.style.WARNING("[警告] 无法解析 crawler_config，使用默认值"))
                    urls_to_crawl = [task.start_url]
                    selectors_to_wait = []
                    waiting_timeout = 10

                all_items = []
                for page_url in urls_to_crawl:
                    try:
                        # --- 导航到页面并等待元素 ---
                        is_timed_out = browser.goto_url_waiting_for_selectors(
                            url=page_url,
                            selector_types_rules=selectors_to_wait, # 等待配置中指定的元素
                            waiting_timeout_in_seconds=waiting_timeout,
                            print_error_log_to_console=True # 可选：打印超时日志
                        )
                        if is_timed_out:
                            self.stdout.write(self.style.WARNING(f"[警告] 等待元素超时: {page_url}"))

                        # --- 获取渲染后的页面源码 ---
                        html_content = browser.get_page_source()
                        self.stdout.write(f"[成功] 页面获取成功，大小: {len(html_content)} 字符")

                        # --- 根据爬虫类型解析内容 ---
                        items = []
                        crawler_method_name = f'_crawl_{task.crawler_type}'
                        crawler_method = getattr(self, crawler_method_name, None)
                        if crawler_method:
                            self.stdout.write(f"[解析] 使用 {task.crawler_type} 解析器...")
                            items = crawler_method(task, html_content)
                            all_items.extend(items)
                        else:
                            raise Exception(f"不支持的爬虫类型: {task.crawler_type}")

                        self.stdout.write(f"[数据] 从 {page_url} 解析到 {len(items)} 条数据")
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  处理页面 {page_url} 时出错: {e}"))
                        # 继续处理下一个 URL
                        continue

                # --- 保存所有解析到的数据 ---
                self.stdout.write(f"[总计] 所有页面共解析到 {len(all_items)} 条数据")
                if all_items:
                    saved_count, duplicate_count = self._save_articles(all_items, task.thinktank)
                    task.last_run = timezone.now()
                    task.last_run_status = 'success'
                    task.last_run_message = f'成功保存 {saved_count} 条新数据，跳过 {duplicate_count} 条重复数据'
                    task.save(update_fields=['last_run', 'last_run_status', 'last_run_message'])

                    self.stdout.write(self.style.SUCCESS(f"[保存] 成功保存 {saved_count} 条新数据"))
                    if duplicate_count > 0:
                        self.stdout.write(self.style.WARNING(f"[重复] 跳过 {duplicate_count} 条重复数据"))
                    return saved_count
                else:
                    task.last_run = timezone.now()
                    task.last_run_status = 'success'
                    task.last_run_message = '页面解析成功但未找到新数据'
                    task.save(update_fields=['last_run', 'last_run_status', 'last_run_message'])
                    self.stdout.write(self.style.WARNING("[警告] 未解析到任何数据"))
                    return 0
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[失败] 任务执行失败: {e}"))
            task.last_run = timezone.now()
            task.last_run_status = 'failed'
            task.last_run_message = f'执行失败: {str(e)}'
            task.save(update_fields=['last_run', 'last_run_status', 'last_run_message'])
            # 如果浏览器崩溃，可能需要特殊处理，但通常 __exit__ 会尝试关闭
            raise
            

    def _save_articles(self, items, thinktank):
        """保存文章到数据库 (使用 Django ORM)"""
        saved_count = 0
        duplicate_count = 0

        for item in items:
            try:
                # 检查是否已存在 (Django ORM)
                if Article.objects.filter(url=item['url']).exists():
                    duplicate_count += 1
                    continue

                # 解析日期
                publish_date = self._parse_date(item.get('publish_date_str', ''))

                # 创建新文章 (Django ORM)
                # 使用 transaction.atomic 确保单个文章创建的原子性
                with transaction.atomic():
                    new_article = Article(
                        title=item['title'][:255],
                        url=item['url'],
                        summary=item.get('summary', '')[:500],
                        author=item.get('author', '')[:100],
                        publish_date=publish_date,
                        content_type=item.get('content_type', ''),
                        tags=item.get('tags', ''),
                        thinktank=thinktank, # 直接关联对象
                        crawl_date=timezone.now(),
                        is_processed=False
                    )
                    new_article.save()
                saved_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  保存文章失败: {e}"))
                # 单篇文章保存失败不影响其他文章
                continue

        return saved_count, duplicate_count

    def _parse_date(self, date_str):
        """解析日期字符串"""
        if not date_str:
            return None

        # 常见日期格式 (与原脚本一致)
        date_patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{4})/(\d{1,2})/(\d{1,2})',
            r'(\d{4})\.(\d{1,2})\.(\d{1,2})',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    year = int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3))
                    return datetime(year, month, day).date()
                except (ValueError, IndexError):
                    continue
        return None

    # --- 爬虫解析方法 (与原脚本逻辑基本一致，但使用 Django 模型和 self.stdout) ---

    def _crawl_handler1(self, task, html_content):
        """处理handler1类型的网站（中国国际工程咨询有限公司）"""
        items = []
        soup = BeautifulSoup(html_content, 'html.parser')

        
        records = re.findall(r'<record><!\[CDATA\[(.*?)\]\]></record>', html_content, re.DOTALL)
        self.stdout.write(f"  找到 {len(records)} 个 CDATA 记录")

        if records:
             # 如果找到了 CDATA，沿用之前的逻辑
             for record_html in records:
                try:
                    # 解析每个record中的HTML内容
                    record_soup = BeautifulSoup(record_html, 'html.parser')

                    # 查找新闻列表容器 (根据 handler1 原逻辑)
                    news_list = record_soup.select_one('div.news-list')
                    if news_list is None:
                        continue

                    # 在每个新闻列表中查找内容 (根据 handler1 原逻辑)
                    old_newscontent = news_list.select_one('div.newscontent')
                    if old_newscontent is None:
                        continue

                    old_a = old_newscontent.select_one('a')
                    if old_a is None:
                        continue

                    a_href = urljoin(task.start_url, old_a.get('href', ''))
                    h3_element = old_a.select_one('h3')
                    if h3_element is None:
                        continue
                    h3_text = h3_element.get_text(strip=True)

                    # 查找日期信息 (根据 handler1 原逻辑)
                    span_element = news_list.select_one('span.newsdate')
                    span_text = span_element.get_text(strip=True) if span_element else ''

                    # 获取摘要信息 (根据 handler1 原逻辑)
                    summary_element = old_newscontent.select_one('p.newsinfo')
                    summary_text = summary_element.get_text(strip=True)[:300] if summary_element else ''

                    item = {
                        'title': h3_text,
                        'url': a_href,
                        'publish_date_str': span_text,
                        'content_type': task.task_name,
                        'summary': summary_text,
                        'author': '',
                        'tags': f"{task.thinktank.name},{task.task_name}"
                    }
                    items.append(item)
                except Exception as e:
                    self.stdout.write(f"  解析单个 CDATA 记录失败: {e}")
                    continue
        else:
            
            self.stdout.write("  未找到 CDATA 记录，尝试直接解析 HTML...")
            
            container = soup.select_one('div.default_pgContainer')
            if container:
                 
                 news_contents = container.select('div.newscontent')
                 self.stdout.write(f"  在 default_pgContainer 中找到 {len(news_contents)} 个 newscontent 元素")
                 for newscontent in news_contents:
                     try:
                         old_a = newscontent.select_one('a')
                         if old_a is None:
                             continue

                         a_href = urljoin(task.start_url, old_a.get('href', ''))
                         # 尝试获取标题，可能在 h3 或 a 标签文本中
                         h3_element = old_a.select_one('h3')
                         if h3_element:
                             h3_text = h3_element.get_text(strip=True)
                         else:
                             h3_text = old_a.get_text(strip=True) # 备选方案

                         if not h3_text:
                             continue

                         # 查找日期信息，可能在同级或父级元素中
                         # 根据网页示例，日期紧跟在标题后面，可能是纯文本或在 span 中
                         # 这里简化处理，尝试从父元素或附近查找
                         span_element = newscontent.select_one('span.newsdate') # 如果存在
                         span_text = span_element.get_text(strip=True) if span_element else ''

                         # 获取摘要信息
                         summary_element = newscontent.select_one('p.newsinfo') # 如果存在
                         summary_text = summary_element.get_text(strip=True)[:300] if summary_element else ''

                         item = {
                             'title': h3_text,
                             'url': a_href,
                             'publish_date_str': span_text,
                             'content_type': task.task_name,
                             'summary': summary_text,
                             'author': '',
                             'tags': f"{task.thinktank.name},{task.task_name}"
                         }
                         items.append(item)
                     except Exception as e:
                         self.stdout.write(f"  直接解析 HTML 时单个条目失败: {e}")
                         continue
            else:
                 self.stdout.write("  未找到 default_pgContainer 容器")

        return items

    def _crawl_handler2(self, task, html_content):
        """处理handler2类型的网站（中国人民大学国家发展与战略研究院）"""
        items = []
        soup = BeautifulSoup(html_content, 'html.parser')

        for old_briefItem in soup.select('div.briefItem'):
            try:
                old_a = old_briefItem.select_one('a')
                if old_a is None:
                    continue

                a_href = urljoin(task.start_url, old_a.get('href', ''))
                h3_element = old_a.select_one('h3')
                if h3_element is None:
                    continue
                h3_text = h3_element.get_text(strip=True)

                span_element = old_a.select_one('span')
                span_text = span_element.get_text(strip=True) if span_element else ''

                item = {
                    'title': h3_text,
                    'url': a_href,
                    'publish_date_str': span_text,
                    'content_type': task.task_name,
                    'summary': '',
                    'author': '',
                    'tags': f"{task.thinktank.name},{task.task_name}"
                }
                items.append(item)
            except Exception as e:
                self.stdout.write(f"  解析单个简报项失败: {e}")
                continue
        return items

    def _crawl_handler3(self, task, html_content):
        """处理handler3类型的网站（国务院发展研究中心）"""
        items = []
        soup = BeautifulSoup(html_content, 'html.parser')

        for re_box in soup.select('div.re_box'):
            try:
                old_a = re_box.select_one('a')
                if old_a is None:
                    continue

                a_href = urljoin(task.start_url, old_a.get('href', ''))
                h3_text = old_a.get('title', '')
                if not h3_text:
                    h3_text = old_a.get_text(strip=True)

                span_element = re_box.select_one('span')
                span_text = span_element.get_text(strip=True) if span_element else ''

                item = {
                    'title': h3_text,
                    'url': a_href,
                    'publish_date_str': span_text,
                    'content_type': task.task_name,
                    'summary': '',
                    'author': '',
                    'tags': f"{task.thinktank.name},{task.task_name}"
                }
                items.append(item)
            except Exception as e:
                self.stdout.write(f"  解析单个结果项失败: {e}")
                continue
        return items

    def _crawl_handler4(self, task, html_content):
        """处理handler4类型的网站（中国科学院）"""
        items = []
        soup = BeautifulSoup(html_content, 'html.parser')

        gl_list2 = soup.select_one('ul.gl_list2')
        if gl_list2 is None:
            return items

        for old_li in gl_list2.select('li'):
            try:
                old_a = old_li.select_one('a')
                if old_a is None:
                    continue

                a_href = urljoin(task.start_url, old_a.get('href', ''))
                h3_text = old_a.get('title', '')
                if not h3_text:
                    h3_text = old_a.get_text(strip=True)

                span_element = old_li.select_one('span')
                span_text = span_element.get_text(strip=True) if span_element else ''

                item = {
                    'title': h3_text,
                    'url': a_href,
                    'publish_date_str': span_text,
                    'content_type': task.task_name,
                    'summary': '',
                    'author': '',
                    'tags': f"{task.thinktank.name},{task.task_name}"
                }
                items.append(item)
            except Exception as e:
                self.stdout.write(f"  解析单个列表项失败: {e}")
                continue
        return items

    def _crawl_handler5(self, task, html_content):
        """处理handler5类型的网站（中国宏观经济研究院）"""
        items = []
        soup = BeautifulSoup(html_content, 'html.parser')

        u_list = soup.select_one('ul.u-list')
        if u_list is None:
            return items

        for old_li in u_list.select('li'):
            try:
                old_a = old_li.select_one('a')
                if old_a is None:
                    continue

                a_href = urljoin(task.start_url, old_a.get('href', ''))
                h3_text = old_a.get('title', '')
                if not h3_text:
                    h3_text = old_a.get_text(strip=True)

                span_element = old_li.select_one('span')
                span_text = span_element.get_text(strip=True) if span_element else ''

                item = {
                    'title': h3_text,
                    'url': a_href,
                    'publish_date_str': span_text,
                    'content_type': task.task_name,
                    'summary': '',
                    'author': '',
                    'tags': f"{task.thinktank.name},{task.task_name}"
                }
                items.append(item)
            except Exception as e:
                self.stdout.write(f"  解析单个列表项失败: {e}")
                continue
        return items

    def _crawl_handler6(self, task, html_content):
        """处理handler6类型的网站（CCiD赛迪研究院）"""
        items = []
        soup = BeautifulSoup(html_content, 'html.parser')

        new_list = soup.select_one('div.new_list.new0')
        if new_list is None:
            return items

        ul_container = new_list.select_one('ul')
        if ul_container is None:
            return items

        for old_li in ul_container.select('li'):
            try:
                old_a = old_li.select_one('a')
                if old_a is None:
                    continue

                a_href = urljoin(task.start_url, old_a.get('href', ''))
                h3_text = old_a.get_text(strip=True)
                if not h3_text:
                    continue

                span_element = old_li.select_one('span')
                span_text = span_element.get_text(strip=True) if span_element else ''

                item = {
                    'title': h3_text,
                    'url': a_href,
                    'publish_date_str': span_text,
                    'content_type': task.task_name,
                    'summary': '',
                    'author': '',
                    'tags': f"{task.thinktank.name},{task.task_name}"
                }
                items.append(item)
            except Exception as e:
                self.stdout.write(f"  解析单个列表项失败: {e}")
                continue
        return items

    def _crawl_handler7(self, task, html_content):
        """处理handler7类型的网站（上海社会科学院）"""
        items = []
        soup = BeautifulSoup(html_content, 'html.parser')

        cols_list = soup.select_one('ul.cols_list.clearfix')
        if cols_list is None:
            return items

        for old_li in cols_list.select('li'):
            try:
                old_a = old_li.select_one('a')
                if old_a is None:
                    continue

                a_href = urljoin(task.start_url, old_a.get('href', ''))
                h3_text = old_a.get_text(strip=True)
                if not h3_text:
                    continue

                span_element = old_li.select_one('span.cols_meta')
                span_text = span_element.get_text(strip=True) if span_element else ''

                item = {
                    'title': h3_text,
                    'url': a_href,
                    'publish_date_str': span_text,
                    'content_type': task.task_name,
                    'summary': '',
                    'author': '',
                    'tags': f"{task.thinktank.name},{task.task_name}"
                }
                items.append(item)
            except Exception as e:
                self.stdout.write(f"  解析单个列表项失败: {e}")
                continue
        return items
