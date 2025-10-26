from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import os
import json
import sys

class Command(BaseCommand):
    help = '运行自定义爬虫脚本'

    def add_arguments(self, parser):
        parser.add_argument('--task-name', type=str, help='指定任务名称（如: 北京大学国家发展研究院）')

    def handle(self, *args, **options):
        task_name = options.get('task_name')
        
        self.stdout.write(f"[开始] 运行自定义爬虫: {task_name or '所有'}")
        
        try:
            # 1. 运行前端爬虫脚本（生成 index.html）
            self.stdout.write("[步骤1] 运行前端链接爬虫...")
            frontend_script_path = os.path.join(settings.BASE_DIR, 'spider', 'main.py')  # 你的脚本路径
            
            result1 = subprocess.run([
                sys.executable, frontend_script_path
            ], capture_output=True, text=True, timeout=300)  # 5分钟超时
            
            if result1.returncode != 0:
                self.stdout.write(self.style.ERROR(f"[失败] 前端爬虫执行失败: {result1.stderr}"))
                return
            
            self.stdout.write(self.style.SUCCESS("[成功] 前端链接爬虫完成"))
            
            # 2. 运行正文爬虫脚本（从 index.html 生成 JSON）
            self.stdout.write("[步骤2] 运行正文内容爬虫...")
            content_script_path = os.path.join(settings.BASE_DIR, 'spider', '内页爬取_完整版.py')  # 你的正文爬虫脚本路径
            
            result2 = subprocess.run([
                sys.executable, content_script_path
            ], capture_output=True, text=True, timeout=600)  # 10分钟超时
            
            if result2.returncode != 0:
                self.stdout.write(self.style.ERROR(f"[失败] 正文爬虫执行失败: {result2.stderr}"))
                return
                
            self.stdout.write(self.style.SUCCESS("[成功] 正文内容爬虫完成"))
            
            # 3. 运行 Django 导入命令（JSON → 数据库）
            self.stdout.write("[步骤3] 导入数据到数据库...")
            
            from django.core.management import call_command
            call_command('import_articles')  # 你之前创建的导入命令
            
            self.stdout.write(self.style.SUCCESS("[成功] 数据导入完成"))
            
            self.stdout.write("="*50)
            self.stdout.write(self.style.SUCCESS("[完成] 自定义爬虫任务执行成功"))
            self.stdout.write("="*50)
            
        except subprocess.TimeoutExpired:
            self.stdout.write(self.style.ERROR("[超时] 爬虫执行超时"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[异常] {e}"))