# thinktank_project/thinktanks/management/commands/view_data.py
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone
from thinktanks.models import ThinkTank
from crawlers.models import CrawlTask
from articles.models import Article
from users.models import User
from articles.models import Digest  # 假设 Digest 在 articles.models 中定义
import subprocess
import sys
import os

class Command(BaseCommand):
    help = '查看数据库中的数据内容'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("智库内容管理系统 - 数据库查看工具 (Django 版)")
        self.stdout.write("=" * 60)

        try:
            # 1. 查看智库信息
            self.stdout.write("\n📋 智库列表:")
            self.stdout.write("-" * 40)
            thinktanks = ThinkTank.objects.all()
            for i, thinktank in enumerate(thinktanks, 1):
                status = "✅ 激活" if thinktank.is_active else "⏸️ 暂停"
                self.stdout.write(f"{i}. {thinktank.name} [{status}]")
                self.stdout.write(f"   网址: {thinktank.url}")
                if thinktank.description:
                    self.stdout.write(f"   描述: {thinktank.description}")
                self.stdout.write("")

            # 2. 查看爬取任务
            self.stdout.write("\n🎯 爬取任务列表:")
            self.stdout.write("-" * 40)
            # 使用 select_related 优化查询，避免 N+1 问题
            tasks = CrawlTask.objects.select_related('thinktank').all()
            for i, task in enumerate(tasks, 1):
                status = "✅ 激活" if task.is_active else "⏸️ 禁用"
                last_status = ""
                if task.last_run_status:
                    if task.last_run_status == 'success':
                        last_status = "✅ 成功"
                    elif task.last_run_status == 'failed':
                        last_status = "❌ 失败"
                    elif task.last_run_status == 'running':
                        last_status = "🔄 运行中"
                    else:
                        last_status = f"❓ {task.last_run_status}"

                self.stdout.write(f"{i}. [{task.id}] {task.task_name} - {task.thinktank.name}")
                self.stdout.write(f"   状态: {status} | 爬虫类型: {task.crawler_type}")
                self.stdout.write(f"   起始URL: {task.start_url}")
                if task.last_run:
                    # Django 的 timezone.now() 是带时区的，确保输出时也处理时区
                    # 如果你的 settings.TIME_ZONE 设置正确，通常直接 strftime 就可以
                    self.stdout.write(f"   最后运行: {timezone.localtime(task.last_run).strftime('%Y-%m-%d %H:%M:%S')} {last_status}")
                else:
                    self.stdout.write(f"   最后运行: 从未运行")
                self.stdout.write("")

            # 3. 查看文章统计
            self.stdout.write("\n📰 文章统计:")
            self.stdout.write("-" * 40)
            total_articles = Article.objects.count()
            processed_articles = Article.objects.filter(is_processed=True).count()

            self.stdout.write(f"总文章数: {total_articles}")
            self.stdout.write(f"已摘编文章: {processed_articles}")
            self.stdout.write(f"待摘编文章: {total_articles - processed_articles}")

            if total_articles > 0:
                self.stdout.write("\n按智库分类:")
                # 使用 annotate 进行聚合查询，效率更高
                counts = ThinkTank.objects.annotate(article_count=Count('article')).filter(article_count__gt=0)
                for thinktank in counts:
                    self.stdout.write(f"  {thinktank.name}: {thinktank.article_count} 篇")

            # 4. 查看最新文章
            self.stdout.write("\n📄 最新文章 (前10篇):")
            self.stdout.write("-" * 40)
            # 使用 select_related 优化查询
            recent_articles = Article.objects.select_related('thinktank').order_by('-crawl_date')[:10]

            if recent_articles:
                for i, article in enumerate(recent_articles, 1):
                    digest_status = "✅ 已摘编" if article.is_processed else "⏳ 待摘编"
                    title_display = article.title[:60] + ('...' if len(article.title) > 60 else '')
                    self.stdout.write(f"{i}. {title_display}")
                    self.stdout.write(f"   来源: {article.thinktank.name} | {digest_status}")
                    if article.crawl_date:
                         self.stdout.write(f"   爬取时间: {timezone.localtime(article.crawl_date).strftime('%Y-%m-%d %H:%M:%S')}")
                    self.stdout.write("")
            else:
                self.stdout.write("暂无文章数据")

            # 5. 查看用户信息
            self.stdout.write("\n👥 用户列表:")
            self.stdout.write("-" * 40)
            users = User.objects.all()
            for i, user in enumerate(users, 1):
                status = "✅ 激活" if user.is_active else "⏸️ 禁用"
                self.stdout.write(f"{i}. {user.username} ({user.full_name}) - {user.role} [{status}]")
                self.stdout.write(f"   邮箱: {user.email}")
                if user.last_login:
                    self.stdout.write(f"   最后登录: {timezone.localtime(user.last_login).strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    self.stdout.write(f"   最后登录: 从未登录")
                self.stdout.write("")

            # 6. 查看摘编统计
            self.stdout.write("\n✏️ 摘编统计:")
            self.stdout.write("-" * 40)
            total_digests = Digest.objects.count()
            self.stdout.write(f"总摘编数: {total_digests}")

            if total_digests > 0:
                # 使用 select_related 优化查询
                recent_digests = Digest.objects.select_related('article').order_by('-created_at')[:5]
                self.stdout.write("\n最新摘编:")
                for i, digest in enumerate(recent_digests, 1):
                    title_display = digest.article.title[:50] + ('...' if len(digest.article.title) > 50 else '')
                    self.stdout.write(f"{i}. {title_display}")
                    self.stdout.write(f"   摘编时间: {timezone.localtime(digest.created_at).strftime('%Y-%m-%d %H:%M:%S')}")
                    self.stdout.write(f"   摘要长度: {len(digest.digest_summary)} 字符")
                    self.stdout.write("")

            self.stdout.write("=" * 60)
            self.stdout.write("数据库查看完毕！")
            # 注意：Django 项目通常没有 run_web.py 这样的独立脚本启动方式，
            # Web 服务是通过 runserver 管理命令启动的。
            # 这里可以提示用户如何启动 Django 开发服务器。
            self.stdout.write("💡 提示: 你可以通过运行 'python manage.py runserver' 启动 Web 服务")
            self.stdout.write("           然后在浏览器中访问: http://127.0.0.1:8000")
            # 如果你配置了 Admin 或特定的查看页面，可以在这里提示 URL。
            # 例如，如果配置了 Admin:
            self.stdout.write("           访问管理后台: http://127.0.0.1:8000/admin/")
            self.stdout.write("           (你需要先创建超级用户: python manage.py createsuperuser)")
            self.stdout.write("=" * 60)
            self.stdout.write("")

            # 询问用户是否启动 Web 服务 (可选功能)
            # 注意：subprocess 调用 runserver 会阻塞当前命令，直到 runserver 被手动停止。
            # 这与 Flask 的 run_web.py 不同。这里提供一个简单的交互。
            # try:
            #     choice = input("是否现在启动 Web 服务？(y/n): ").strip().lower()
            #     if choice in ['y', 'yes', '是', '']:
            #         self.stdout.write("正在启动 Web 服务...")
            #         self.stdout.write("🌐 Web 服务启动中...")
            #         self.stdout.write("📱 请在浏览器中访问: http://127.0.0.1:8000")
            #         self.stdout.write("⏹️  按 Ctrl+C 停止服务")
            #         self.stdout.write("")
            #         # 启动 Django 开发服务器
            #         # 注意：这会接管当前终端
            #         subprocess.run([sys.executable, 'manage.py', 'runserver'])
            # except KeyboardInterrupt:
            #     self.stdout.write("\nWeb 服务已停止。")
            # except Exception as e:
            #     self.stdout.write(self.style.ERROR(f"启动 Web 服务时出错: {e}"))
            #     self.stdout.write("你可以手动运行: python manage.py runserver")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"查看数据库时发生错误: {e}"))
            import traceback
            traceback.print_exc()
