    # articles/management/commands/import_articles.py

import json
from datetime import datetime, date
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date
from articles.models import Article
from thinktanks.models import ThinkTank  # 假设你的 ThinkTank 在 thinktanks 应用中

# 安全解析日期的辅助函数
def safe_parse_date(date_value):
    if not date_value:
        return None
    if isinstance(date_value, str):
        # 尝试多种常见格式
        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日', '%Y.%m.%d']:
            try:
                return datetime.strptime(date_value.strip(), fmt).date()
            except ValueError:
                continue
        # 最后尝试 Django 的 parse_date
        return parse_date(date_value.strip())
    elif isinstance(date_value, (datetime, date)):
        return date_value if isinstance(date_value, date) else date_value.date()
    return None
    
class Command(BaseCommand):
    help = '从 output_complete.json 导入文章到数据库'

    def handle(self, *args, **options):
        try:
            with open('C:/Users/DELL/proj released/test/test/thinktank_project/proj released/output_complete.json', 'r', encoding='utf-8') as f:
                data_list = json.load(f)

            imported_count = 0
            skipped_count = 0

            for item in data_list:
                # 获取或创建智库
                thinktank_name = item.get('thinkank_name', '').strip()
                if not thinktank_name:
                    self.stdout.write(self.style.WARNING(f'跳过：智库名称为空 - {item.get("title", "无标题")}'))
                    skipped_count += 1
                    continue

                thinktank, created = ThinkTank.objects.get_or_create(
                    name=thinktank_name,
                    defaults={'description': f'自动创建于 {datetime.now().strftime("%Y-%m-%d")}'}  # 可选默认描述
                )

                # 解析日期
                publish_date = safe_parse_date(item.get('publish_date'))
                crawl_date = safe_parse_date(item.get('crawl_date'))

                # 创建或更新文章（根据 URL 唯一性）
                article, created = Article.objects.update_or_create(
                    url=item['url'],  # 因为你的 Article.url 是 unique=True
                    defaults={
                        'title': item.get('title', '')[:255],
                        'content': item.get('content', ''),  # ← 正文内容
                        'summary': item.get('summary', ''),
                        'author': item.get('authors', '')[:100],
                        'publish_date': publish_date,
                        'crawl_date': crawl_date,
                        'content_type': 'article',  # 你可以根据来源设置不同类型
                        'tags': '',  # 你可以后续处理
                        'view_count': 0,
                        'is_processed': False,
                        'thinktank': thinktank,
                    }
                )

                if created:
                    imported_count += 1
                    self.stdout.write(self.style.SUCCESS(f'✅ 导入: {article.title[:50]}...'))
                else:
                    self.stdout.write(self.style.WARNING(f'🔄 更新: {article.title[:50]}...'))

            self.stdout.write(
                self.style.SUCCESS(f'导入完成！新增 {imported_count} 篇，跳过 {skipped_count} 篇。')
            )

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('❌ 找不到 output_complete.json 文件！'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 导入失败: {e}'))