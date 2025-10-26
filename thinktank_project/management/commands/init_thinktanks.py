#!/usr/bin/env python

from django.core.management.base import BaseCommand
from django.db import transaction
from thinktanks.models import ThinkTank
from crawlers.models import CrawlTask
from users.models import User
import json

# 智库与任务数据（来自原 Flask 脚本）
URL_DATA = {
    '中国国际工程咨询有限公司': {
        'tasks': [
            {
                'task_name': '智库建议',
                'urls': [
                    'https://www.ciecc.com.cn/col/col3963/index.html',
                    'https://www.ciecc.com.cn/col/col3963/index.html?uid=5248&pageNum=2',
                ],
                'crawler_type': 'handler1'
            },
            {
                'task_name': '中咨视界',
                'urls': [
                    'https://www.ciecc.com.cn/col/col2218/index.html',
                    'https://www.ciecc.com.cn/col/col2218/index.html?uid=5248&pageNum=2',
                ],
                'crawler_type': 'handler1'
            }
        ],
        'base_url': 'https://www.ciecc.com.cn',
        'logo_path': './Logos/handler1.jpg'
    },
    '中国人民大学国家发展与战略研究院': {
        'tasks': [
            {
                'task_name': '学者观点',
                'urls': [
                    'http://nads.ruc.edu.cn/zkdt/xzgd/index.htm',
                    'http://nads.ruc.edu.cn/zkdt/xzgd/index1.htm',
                ],
                'crawler_type': 'handler2'
            },
            {
                'task_name': '双周政策分析简报',
                'urls': [
                    'http://nads.ruc.edu.cn/zkcg/zcjb/szzcfxjb/index.htm',
                ],
                'crawler_type': 'handler2'
            }
        ],
        'base_url': 'http://nads.ruc.edu.cn',
        'logo_path': './Logos/handler2.png'
    },
    '国务院发展研究中心': {
        'tasks': [
            {
                'task_name': '中心动态',
                'urls': ['https://www.drc.gov.cn/Leaf.aspx?leafid=1346'],
                'crawler_type': 'handler3',
                'special_config': {
                    'pagination': True,
                    'pages_needed': 2
                }
            }
        ],
        'base_url': 'https://www.drc.gov.cn',
        'logo_path': './Logos/handler3.png'
    },
    '中国科学院': {
        'tasks': [
            {
                'task_name': '院内要闻',
                'urls': [
                    'https://www.cas.cn/yw/index.shtml',
                    'https://www.cas.cn/yw/index_1.shtml'
                ],
                'crawler_type': 'handler4'
            }
        ],
        'base_url': 'https://www.cas.cn',
        'logo_path': './Logos/handler4.png'
    },
    '中国宏观经济研究院': {
        'tasks': [
            {
                'task_name': '科研动态',
                'urls': [
                    'https://www.amr.org.cn/ghdt/kydt/index.html',
                    'https://www.amr.org.cn/ghdt/kydt/index_1.html'
                ],
                'crawler_type': 'handler5'
            }
        ],
        'base_url': 'https://www.amr.org.cn',
        'logo_path': './Logos/handler5.png'
    },
    'CCiD赛迪研究院': {
        'tasks': [
            {
                'task_name': '赛迪新闻',
                'urls': [
                    'https://www.ccidgroup.com/xwdt/sdxw.htm',
                    'https://www.ccidgroup.com/xwdt/sdxw/91.htm'
                ],
                'crawler_type': 'handler6'
            }
        ],
        'base_url': 'https://www.ccidgroup.com',
        'logo_path': './Logos/handler6.png'
    },
    '上海社会科学院': {
        'tasks': [
            {
                'task_name': '新闻',
                'urls': [
                    'https://www.sass.org.cn/1198/list1.htm',
                    'https://www.sass.org.cn/1198/list2.htm'
                ],
                'crawler_type': 'handler7'
            },
            {
                'task_name': '专家视点',
                'urls': [
                    'https://www.sass.org.cn/1201/list.htm',
                    'https://www.sass.org.cn/1201/list2.htm'
                ],
                'crawler_type': 'handler7'
            },
            {
                'task_name': '习近平文化思想最佳实践地建设',
                'urls': [
                    'https://www.sass.org.cn/5867/list.htm',
                    'https://www.sass.org.cn/5867/list2.htm'
                ],
                'crawler_type': 'handler7'
            }
        ],
        'base_url': 'https://www.sass.org.cn',
        'logo_path': './Logos/handler7.png'
    }
}

# 爬虫配置模板
CRAWLER_CONFIGS = {
    'handler1': {
        'selectors': [
            ('css', 'div.main_comr.fr'),
            ('css', 'div.default_pgContainer'),
            ('css', 'div.news-list'),
            ('css', 'div.newscontent')
        ],
        'waiting_timeout': 30,
        'content_selector': 'div.newscontent'
    },
    'handler2': {
        'selectors': [
            ('css', 'div.commonRight'),
            ('css', 'div.commonRightTitle'),
            ('css', 'div.Brief'),
            ('css', 'div.briefItem')
        ],
        'waiting_timeout': 30,
        'content_selector': 'div.briefItem'
    },
    'handler3': {
        'selectors': [
            ('css', 'div.conright.fr'),
            ('css', 'div.containerbg'),
            ('css', 'div.document-box'),
            ('css', 'div.rr3'),
            ('css', 'div.re_box')
        ],
        'waiting_timeout': 30,
        'content_selector': 'div.re_box',
        'pagination': {
            'next_button': 'a.p-next.p-elem',
            'page_wait': 1
        }
    },
    'handler4': {
        'selectors': [
            ('css', 'div.container.boxcenter.main.pad_main'),
            ('css', 'div.xl.list_xl'),
            ('css', 'ul.gl_list2'),
            ('css', 'div#content')
        ],
        'waiting_timeout': 30,
        'content_selector': 'ul.gl_list2 li'
    },
    'handler5': {
        'selectors': [
            ('css', 'div.flex'),
            ('css', 'div.list'),
            ('css', 'ul.u-list')
        ],
        'waiting_timeout': 30,
        'content_selector': 'ul.u-list li'
    },
    'handler6': {
        'selectors': [
            ('css', 'div.layout_div1_list'),
            ('css', 'div.new_list.new0')
        ],
        'waiting_timeout': 30,
        'content_selector': 'div.new_list.new0 ul li'
    },
    'handler7': {
        'selectors': [
            ('css', 'div.column-news-con'),
            ('css', 'div.column-news-list.clearfix'),
            ('css', 'ul.cols_list.clearfix')
        ],
        'waiting_timeout': 30,
        'content_selector': 'ul.cols_list.clearfix li'
    }
}

# 简单密码哈希（仅用于开发）
def simple_hash(password):
    from django.contrib.auth.hashers import make_password
    return make_password(password)  # 推荐使用 Django 内置哈希
    # return f"hash_{password}"  # 原始方式，不安全


class Command(BaseCommand):
    help = '初始化智库、爬取任务和默认用户'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("智库内容管理系统 - 数据库初始化")
        self.stdout.write("=" * 60)

        try:
            with transaction.atomic():
                # 1. 创建默认用户
                self.create_users()

                # 2. 创建智库和爬取任务
                self.create_thinktanks_and_tasks()

            # 显示统计
            thinktank_count = ThinkTank.objects.count()
            task_count = CrawlTask.objects.count()
            user_count = User.objects.count()

            self.stdout.write(self.style.SUCCESS("\n数据库初始化完成！"))
            self.stdout.write(f"智库数量: {thinktank_count}")
            self.stdout.write(f"爬取任务数量: {task_count}")
            self.stdout.write(f"用户数量: {user_count}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"初始化失败: {e}"))
            raise

    def create_users(self):
        self.stdout.write("创建默认用户...")
        if User.objects.exists():
            self.stdout.write("用户已存在，跳过创建")
            return

        admin_user = User.objects.create(
            username='admin',
            email='admin@thinktank.com',
            password_hash=simple_hash('admin123'),
            full_name='系统管理员',
            role='admin',
            is_active=True
        )

        editor_user = User.objects.create(
            username='editor',
            email='editor@thinktank.com',
            password_hash=simple_hash('editor123'),
            full_name='内容编辑',
            role='editor',
            is_active=True
        )

        self.stdout.write(self.style.SUCCESS("✅ 默认用户创建完成"))
        self.stdout.write("  管理员: admin / admin123")
        self.stdout.write("  编辑: editor / editor123")

    def create_thinktanks_and_tasks(self):
        self.stdout.write("创建智库和爬取任务...")
        if ThinkTank.objects.exists():
            self.stdout.write("智库数据已存在，跳过创建")
            return

        for name, info in URL_DATA.items():
            # 创建智库
            thinktank = ThinkTank.objects.create(
                name=name,
                url=info['base_url'].strip(),
                description=f"{name}的内容爬取",
                logo_path=info['logo_path'].strip(),
                is_active=True
            )
            self.stdout.write(f"  🏢 创建智库: {name}")

            # 创建任务
            for task_info in info['tasks']:
                crawler_config = CRAWLER_CONFIGS.get(task_info['crawler_type'], {}).copy()
                if 'special_config' in task_info:
                    crawler_config.update(task_info['special_config'])

                full_config = {
                    'urls': [url.strip() for url in task_info['urls']],
                    'config': crawler_config
                }

                CrawlTask.objects.create(
                    task_name=task_info['task_name'],
                    start_url=task_info['urls'][0].strip(),
                    crawler_type=task_info['crawler_type'],
                    schedule_type='daily',
                    schedule_time='09:00',
                    is_active=True,
                    crawler_config=json.dumps(full_config, ensure_ascii=False, indent=2),
                    thinktank=thinktank
                )
                self.stdout.write(f"    📡 任务: {task_info['task_name']}")

        self.stdout.write(self.style.SUCCESS("✅ 智库和任务创建完成"))